"""
Enhanced Vector Database Manager - Phase 3 Impleme            self.top_k_default = config.get('top_k_default', 5)  # Reduced for focused student responsestation
Optimized for chunk-level retrieval and AI chatbot foundation

This module provides:
- Chunk-level vector storage with comprehensive metadata
- Top-K retrieval algorithm for precise context
- Source attribution system
- Multiple vector database backends with enhanced querying
- Similarity search optimization for AI responses
"""

import os
import logging
import time
import uuid
import json
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
import numpy as np
from sentence_transformers import SentenceTransformer

# Vector Databases
try:
    import chromadb
    from chromadb.config import Settings
    from chromadb.utils import embedding_functions
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

try:
    from pinecone import Pinecone, ServerlessSpec
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False

class EnhancedVectorDBManager:
    def __init__(self, config: Dict):
        """Initialize enhanced vector database for chunk-level retrieval"""
        try:
            self.config = config
            self.db_type = config.get('vector_db_type', 'chromadb').lower()
            self.db_path = config.get('vector_db_path', './vector_store')
            self.collection_name = config.get('collection_name', 'pdf_chunks')  # Changed to chunks
            self.embedding_model_name = config.get('embedding_model', 'all-MiniLM-L6-v2')
            
            # Enhanced configuration for AI chatbot
            self.max_chunk_length = config.get('max_chunk_length', 2000)
            self.top_k_default = config.get('top_k_default', 25)  # Increase default retrieval count for better context
            self.similarity_threshold = config.get('similarity_threshold', 0.7)
            self.enable_reranking = config.get('enable_reranking', True)
            
            # Setup logging
            self.logger = logging.getLogger(__name__)
            
            # Initialize embedding model
            self.embedding_model = None
            self.embedding_dim = None
            self._initialize_embedding_model()
            
            # Initialize vector database
            self.db_client = None
            self.collection = None
            self._initialize_database()
            
            # Statistics
            self.stats = {
                'chunks_stored': 0,
                'queries_processed': 0,
                'average_query_time': 0,
                'last_update': None
            }
            
            self.logger.info(f"Enhanced Vector DB Manager initialized: {self.db_type}, chunks collection")
            
        except Exception as e:
            self.logger.error(f"ERROR: Failed to initialize EnhancedVectorDBManager: {str(e)}")
            raise
    
    def _initialize_embedding_model(self):
        """Initialize embedding model optimized for semantic search"""
        try:
            self.logger.info(f"Loading embedding model: {self.embedding_model_name}")
            
            self.embedding_model = SentenceTransformer(self.embedding_model_name)
            self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
            
            # Test the model
            test_embedding = self.embedding_model.encode(["test chunk for AI retrieval"], convert_to_numpy=True)
            if test_embedding.shape[1] != self.embedding_dim:
                raise ValueError("Model dimension mismatch")
            
            self.logger.info(f"Embedding model loaded. Dimension: {self.embedding_dim}")
            
        except Exception as e:
            self.logger.error(f"ERROR: Failed to load embedding model: {str(e)}")
            raise
    
    def _initialize_database(self):
        """Initialize vector database with chunk-optimized settings"""
        try:
            if self.db_type == 'chromadb':
                self._initialize_chromadb()
            elif self.db_type == 'faiss':
                self._initialize_faiss()
            elif self.db_type == 'pinecone':
                self._initialize_pinecone()
            else:
                raise ValueError(f"Unsupported database type: {self.db_type}")
                
        except Exception as e:
            self.logger.error(f"ERROR: Failed to initialize {self.db_type} database: {str(e)}")
            raise
    
    def _initialize_chromadb(self):
        """Initialize ChromaDB with enhanced settings for chunks"""
        if not CHROMADB_AVAILABLE:
            raise ImportError("ChromaDB not available. Install with: pip install chromadb")
        
        try:
            # Ensure directory exists
            os.makedirs(self.db_path, exist_ok=True)
            
            # Initialize ChromaDB client with persistence
            self.db_client = chromadb.PersistentClient(
                path=self.db_path,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Create or get collection with enhanced metadata
            try:
                self.collection = self.db_client.get_collection(
                    name=self.collection_name,
                    embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(
                        model_name=self.embedding_model_name
                    )
                )
                self.logger.info(f"SUCCESS: Connected to existing ChromaDB collection: {self.collection_name}")
            except:
                self.collection = self.db_client.create_collection(
                    name=self.collection_name,
                    embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(
                        model_name=self.embedding_model_name
                    ),
                    metadata={"description": "Enhanced PDF chunks for AI chatbot retrieval"}
                )
                self.logger.info(f"SUCCESS: Created new ChromaDB collection: {self.collection_name}")
            
        except Exception as e:
            self.logger.error(f"ERROR: ChromaDB initialization failed: {str(e)}")
            raise
    
    def _initialize_faiss(self):
        """Initialize FAISS with enhanced indexing for semantic search"""
        if not FAISS_AVAILABLE:
            raise ImportError("FAISS not available. Install with: pip install faiss-cpu")
        
        try:
            # Create enhanced FAISS index (HNSW for better semantic search)
            self.faiss_index = faiss.IndexHNSWFlat(self.embedding_dim, 32)
            self.faiss_index.hnsw.efConstruction = 200
            self.faiss_index.hnsw.efSearch = 100
            
            # Metadata storage for FAISS
            self.faiss_metadata = {}
            self.faiss_id_counter = 0
            
            # Try to load existing index
            index_path = os.path.join(self.db_path, "enhanced_chunks.index")
            metadata_path = os.path.join(self.db_path, "enhanced_metadata.json")
            
            if os.path.exists(index_path) and os.path.exists(metadata_path):
                self.faiss_index = faiss.read_index(index_path)
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    saved_data = json.load(f)
                    self.faiss_metadata = saved_data.get('metadata', {})
                    self.faiss_id_counter = saved_data.get('id_counter', 0)
                self.logger.info(f"SUCCESS: Loaded existing FAISS index with {self.faiss_index.ntotal} chunks")
            else:
                os.makedirs(self.db_path, exist_ok=True)
                self.logger.info("SUCCESS: Created new FAISS index for enhanced chunks")
            
        except Exception as e:
            self.logger.error(f"ERROR: FAISS initialization failed: {str(e)}")
            raise
    
    def _initialize_pinecone(self):
        """Initialize Pinecone with enhanced indexing for semantic search"""
        if not PINECONE_AVAILABLE:
            raise ImportError("Pinecone not available. Install with: pip install pinecone-client")
        
        try:
            # Get Pinecone configuration from config
            api_key = self.config.get('pinecone_api_key') or os.getenv('PINECONE_API_KEY')
            environment = self.config.get('pinecone_environment', 'us-east-1-aws')
            index_name = self.config.get('pinecone_index_name', self.collection_name)
            
            if not api_key:
                raise ValueError("Pinecone API key not found. Set PINECONE_API_KEY environment variable or add to config.")
            
            # Initialize Pinecone client
            self.pinecone_client = Pinecone(api_key=api_key)
            
            # Check if index exists, create if not
            existing_indexes = [index.name for index in self.pinecone_client.list_indexes()]
            
            if index_name not in existing_indexes:
                self.logger.info(f"Creating new Pinecone index: {index_name}")
                self.pinecone_client.create_index(
                    name=index_name,
                    dimension=self.embedding_dim,
                    metric='cosine',
                    spec=ServerlessSpec(
                        cloud='aws',
                        region=environment
                    )
                )
                # Wait for index to be ready
                import time
                time.sleep(10)
            
            # Connect to index
            self.pinecone_index = self.pinecone_client.Index(index_name)
            self.pinecone_index_name = index_name
            
            # Get index stats
            stats = self.pinecone_index.describe_index_stats()
            total_vectors = stats.get('total_vector_count', 0)
            
            self.logger.info(f"Connected to Pinecone index '{index_name}' with {total_vectors} vectors")
            
        except Exception as e:
            self.logger.error(f"ERROR: Pinecone initialization failed: {str(e)}")
            raise
    
    def store_chunks_batch(self, chunks: List[Dict]) -> bool:
        """Store chunks in batch with enhanced metadata for AI retrieval"""
        if not chunks:
            return True
        
        try:
            start_time = time.time()
            
            # Prepare data for batch storage
            texts = []
            metadatas = []
            ids = []
            
            for chunk in chunks:
                # Generate unique ID for chunk
                chunk_id = chunk.get('chunk_id') or f"chunk_{uuid.uuid4().hex[:8]}"
                
                # Prepare text for embedding (combine content with context)
                chunk_text = chunk['text']
                if len(chunk_text) > self.max_chunk_length:
                    chunk_text = chunk_text[:self.max_chunk_length]
                
                # Enhanced metadata for better retrieval
                enhanced_metadata = {
                    # Core identification
                    'chunk_id': chunk_id,
                    'filename': chunk['filename'],
                    'chunk_index': chunk.get('chunk_index', 0),
                    'section_index': chunk.get('section_index', 0),
                    
                    # Content metadata
                    'content_type': chunk.get('content_type', 'general'),
                    'chunk_length': len(chunk_text),
                    'chunk_tokens': chunk.get('chunk_tokens', 0),
                    'preview': chunk.get('preview', chunk_text[:200]),
                    
                    # Source metadata for attribution
                    'file_pages': chunk.get('file_pages', 0),
                    'extraction_method': chunk.get('extraction_method', 'unknown'),
                    'ocr_used': chunk.get('ocr_used', False),
                    'images_processed': chunk.get('images_processed', 0),
                    
                    # Context for better retrieval
                    'previous_chunk_preview': chunk.get('previous_chunk_preview', ''),
                    'next_chunk_preview': chunk.get('next_chunk_preview', ''),
                    
                    # Processing metadata
                    'created_at': chunk.get('created_at', time.time()),
                    'stored_at': time.time()
                }
                
                texts.append(chunk_text)
                metadatas.append(enhanced_metadata)
                ids.append(chunk_id)
            
            # Store based on database type
            if self.db_type == 'chromadb':
                self._store_chunks_chromadb(texts, metadatas, ids)
            elif self.db_type == 'faiss':
                self._store_chunks_faiss(texts, metadatas, ids)
            elif self.db_type == 'pinecone':
                self._store_chunks_pinecone(texts, metadatas, ids)
            
            # Update statistics
            self.stats['chunks_stored'] += len(chunks)
            self.stats['last_update'] = datetime.now().isoformat()
            
            processing_time = time.time() - start_time
            self.logger.info(f"SUCCESS: Stored {len(chunks)} chunks in {processing_time:.2f}s")
            
            return True
            
        except Exception as e:
            self.logger.error(f"ERROR: Failed to store chunks batch: {str(e)}")
            return False
    
    def _store_chunks_chromadb(self, texts: List[str], metadatas: List[Dict], ids: List[str]):
        """Store chunks in ChromaDB"""
        try:
            # Convert metadata to ChromaDB format (strings only)
            chroma_metadatas = []
            for metadata in metadatas:
                chroma_metadata = {}
                for key, value in metadata.items():
                    if isinstance(value, (str, int, float, bool)):
                        chroma_metadata[key] = str(value)
                    elif value is not None:
                        chroma_metadata[key] = str(value)
                chroma_metadatas.append(chroma_metadata)
            
            # Store in collection
            self.collection.add(
                documents=texts,
                metadatas=chroma_metadatas,
                ids=ids
            )
            
        except Exception as e:
            self.logger.error(f"ERROR: ChromaDB storage error: {str(e)}")
            raise
    
    def _store_chunks_faiss(self, texts: List[str], metadatas: List[Dict], ids: List[str]):
        """Store chunks in FAISS"""
        try:
            # Generate embeddings
            embeddings = self.embedding_model.encode(texts, convert_to_numpy=True)
            
            # Add to FAISS index
            faiss_ids = []
            for i, (text, metadata, chunk_id) in enumerate(zip(texts, metadatas, ids)):
                faiss_id = self.faiss_id_counter
                self.faiss_id_counter += 1
                
                # Store metadata
                self.faiss_metadata[faiss_id] = {
                    'text': text,
                    'chunk_id': chunk_id,
                    **metadata
                }
                faiss_ids.append(faiss_id)
            
            # Add embeddings to index
            self.faiss_index.add_with_ids(embeddings, np.array(faiss_ids))
            
            # Save index and metadata
            self._save_faiss_index()
            
        except Exception as e:
            self.logger.error(f"ERROR: FAISS storage error: {str(e)}")
            raise
    
    def _save_faiss_index(self):
        """Save FAISS index and metadata to disk"""
        try:
            index_path = os.path.join(self.db_path, "enhanced_chunks.index")
            metadata_path = os.path.join(self.db_path, "enhanced_metadata.json")
            
            # Save FAISS index
            faiss.write_index(self.faiss_index, index_path)
            
            # Save metadata
            save_data = {
                'metadata': self.faiss_metadata,
                'id_counter': self.faiss_id_counter,
                'updated_at': time.time()
            }
            
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            self.logger.error(f"ERROR: Failed to save FAISS index: {str(e)}")
    
    def _store_chunks_pinecone(self, texts: List[str], metadatas: List[Dict], ids: List[str]):
        """Store chunks in Pinecone"""
        try:
            # Generate embeddings
            embeddings = self.embedding_model.encode(texts, convert_to_numpy=True)
            
            # Prepare vectors for Pinecone
            vectors_to_upsert = []
            for i, (text, metadata, chunk_id) in enumerate(zip(texts, metadatas, ids)):
                # Pinecone metadata must be flat key-value pairs with simple types
                pinecone_metadata = {
                    'text': text[:40000],  # Pinecone has metadata size limits
                    'chunk_id': chunk_id,
                    'filename': str(metadata.get('filename', '')),
                    'chunk_index': int(metadata.get('chunk_index', 0)),
                    'section_index': int(metadata.get('section_index', 0)),
                    'content_type': str(metadata.get('content_type', 'general')),
                    'chunk_length': int(metadata.get('chunk_length', 0)),
                    'chunk_tokens': int(metadata.get('chunk_tokens', 0)),
                    'preview': str(metadata.get('preview', ''))[:1000],  # Limit preview size
                    'file_pages': int(metadata.get('file_pages', 0)),
                    'extraction_method': str(metadata.get('extraction_method', 'unknown')),
                    'ocr_used': str(metadata.get('ocr_used', False)),
                    'images_processed': int(metadata.get('images_processed', 0)),
                    'created_at': float(metadata.get('created_at', time.time())),
                    'stored_at': float(metadata.get('stored_at', time.time()))
                }
                
                vectors_to_upsert.append({
                    'id': chunk_id,
                    'values': embeddings[i].tolist(),
                    'metadata': pinecone_metadata
                })
            
            # Upsert vectors in batches (Pinecone recommends batches of 100-1000)
            batch_size = 100
            for i in range(0, len(vectors_to_upsert), batch_size):
                batch = vectors_to_upsert[i:i + batch_size]
                self.pinecone_index.upsert(vectors=batch)
            
            self.logger.info(f"SUCCESS: Stored {len(vectors_to_upsert)} vectors in Pinecone")
            
        except Exception as e:
            self.logger.error(f"ERROR: Pinecone storage error: {str(e)}")
            raise
    
    def search_similar_chunks(self, query: str, top_k: int = None, filters: Dict = None, namespace: str = None) -> List[Dict]:
        """Advanced educational content search with multiple retrieval strategies"""
        if top_k is None:
            top_k = self.top_k_default
        
        try:
            start_time = time.time()
            all_results = []
            
            self.logger.info(f"SEARCH: ADVANCED SEARCH: '{query[:60]}...' in namespace: {namespace}")
            
            # STRATEGY 1: Primary semantic search
            if self.db_type == 'pinecone':
                primary_results = self._search_pinecone_advanced(query, top_k, filters, namespace)
            elif self.db_type == 'chromadb':
                primary_results = self._search_chromadb(query, top_k, filters)
            elif self.db_type == 'faiss':
                primary_results = self._search_faiss(query, top_k, filters)
            else:
                primary_results = []
            
            all_results.extend(primary_results)
            self.logger.info(f"CHART: Primary search: {len(primary_results)} results")
            
            # STRATEGY 2: Educational keyword expansion
            if len(primary_results) < top_k * 0.7:  # If we don't have enough high-quality results
                expanded_results = self._educational_keyword_search(query, top_k//2, filters, namespace)
                all_results.extend(expanded_results)
                self.logger.info(f"📚 Keyword expansion: {len(expanded_results)} additional results")
            
            # STRATEGY 3: Cross-namespace search for comprehensive coverage
            if namespace and len(all_results) < top_k:
                cross_namespace_results = self._cross_namespace_search(query, top_k//3, filters, namespace)
                all_results.extend(cross_namespace_results)
                self.logger.info(f"REFRESH: Cross-namespace: {len(cross_namespace_results)} additional results")
            
            # STRATEGY 4: Fuzzy matching for typos and variations
            if len(all_results) < top_k * 0.8:
                fuzzy_results = self._fuzzy_educational_search(query, top_k//3, filters, namespace)
                all_results.extend(fuzzy_results)
                self.logger.info(f"TARGET: Fuzzy matching: {len(fuzzy_results)} additional results")
            
            # Remove duplicates and enhance results
            unique_results = self._deduplicate_and_enhance_results(all_results)
            
            # Apply educational content scoring
            scored_results = self._apply_educational_scoring(unique_results, query)
            
            # Sort by enhanced relevance score and limit
            final_results = sorted(scored_results, key=lambda x: x.get('enhanced_score', 0), reverse=True)[:top_k]
            
            # Post-process results for AI optimization
            enhanced_results = self._enhance_search_results(final_results, query)
            
            # Apply reranking if enabled
            if self.enable_reranking and len(enhanced_results) > 1:
                enhanced_results = self._rerank_results(enhanced_results, query)
            
            # Update statistics
            query_time = time.time() - start_time
            self.stats['queries_processed'] += 1
            current_avg = self.stats['average_query_time']
            self.stats['average_query_time'] = (current_avg * (self.stats['queries_processed'] - 1) + query_time) / self.stats['queries_processed']
            
            self.logger.info(f"SUCCESS: SEARCH COMPLETE: {len(enhanced_results)} high-quality chunks in {query_time:.3f}s")
            
            return enhanced_results
            
        except Exception as e:
            self.logger.error(f"ERROR: Advanced search failed: {str(e)}")
            return []
    
    def _search_chromadb(self, query: str, top_k: int, filters: Dict = None) -> List[Dict]:
        """Search ChromaDB for similar chunks"""
        try:
            # Prepare where clause for filtering
            where_clause = {}
            if filters:
                for key, value in filters.items():
                    where_clause[key] = str(value)
            
            # Perform search
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                where=where_clause if where_clause else None
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i, (doc, metadata, distance) in enumerate(zip(
                    results['documents'][0],
                    results['metadatas'][0],
                    results['distances'][0]
                )):
                    formatted_results.append({
                        'text': doc,
                        'metadata': metadata,
                        'similarity_score': 1 - distance,  # Convert distance to similarity
                        'rank': i + 1
                    })
            
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"ERROR: ChromaDB search error: {str(e)}")
            return []
    
    def _search_faiss(self, query: str, top_k: int, filters: Dict = None) -> List[Dict]:
        """Search FAISS for similar chunks"""
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query], convert_to_numpy=True)
            
            # Search FAISS index
            similarities, indices = self.faiss_index.search(query_embedding, min(top_k, self.faiss_index.ntotal))
            
            # Format results
            formatted_results = []
            for i, (similarity, idx) in enumerate(zip(similarities[0], indices[0])):
                if idx == -1:  # No more results
                    break
                
                # Convert index to string key for metadata lookup
                metadata = self.faiss_metadata.get(str(idx), {})
                
                # Apply filters if specified
                if filters:
                    skip = False
                    for key, value in filters.items():
                        if metadata.get(key) != str(value):
                            skip = True
                            break
                    if skip:
                        continue
                
                formatted_results.append({
                    'text': metadata.get('text', ''),
                    'metadata': metadata,
                    'similarity_score': float(similarity),
                    'rank': i + 1
                })
            
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"ERROR: FAISS search error: {str(e)}")
            return []
    
    def _search_pinecone_advanced(self, query: str, top_k: int, filters: Dict = None, namespace: str = None) -> List[Dict]:
        """Advanced Pinecone search with enhanced educational content retrieval"""
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query], convert_to_numpy=True)
            
            # Determine namespace to search
            if namespace is None:
                namespace = self._determine_search_namespace(query)
            
            # Prepare filter for Pinecone
            pinecone_filter = {}
            if filters:
                for key, value in filters.items():
                    if key in ['chunk_index', 'section_index', 'chunk_length', 'chunk_tokens', 'file_pages']:
                        pinecone_filter[key] = {"$eq": int(value)}
                    elif key in ['created_at', 'stored_at']:
                        pinecone_filter[key] = {"$eq": float(value)}
                    else:
                        pinecone_filter[key] = {"$eq": str(value)}
            
            # Perform search with enhanced top_k for better recall
            search_response = self.pinecone_index.query(
                vector=query_embedding[0].tolist(),
                top_k=min(top_k * 2, 50),  # Get more results for better filtering
                include_metadata=True,
                filter=pinecone_filter if pinecone_filter else None,
                namespace=namespace
            )
            
            self.logger.info(f"TARGET: Pinecone search in namespace '{namespace}': {len(search_response.matches)} matches")
            
            # Format and enhance results
            formatted_results = []
            for i, match in enumerate(search_response.matches):
                metadata = match.metadata or {}
                
                # Extract text content with multiple fallbacks
                text_content = self._extract_text_from_metadata(metadata)
                
                if text_content and len(text_content.strip()) > 20:  # Ensure meaningful content
                    result = {
                        'text': text_content,
                        'metadata': metadata,
                        'similarity_score': float(match.score),
                        'rank': i + 1,
                        'namespace': namespace,
                        'search_method': 'pinecone_advanced'
                    }
                    formatted_results.append(result)
            
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"ERROR: Advanced Pinecone search error: {str(e)}")
            return []
    
    def _educational_keyword_search(self, query: str, top_k: int, filters: Dict = None, namespace: str = None) -> List[Dict]:
        """Search using educational keyword expansion and synonyms"""
        try:
            # Educational term expansions
            educational_expansions = {
                'assessment': ['evaluation', 'testing', 'grading', 'measurement', 'appraisal'],
                'formative': ['ongoing', 'continuous', 'developmental', 'progressive'],
                'summative': ['final', 'conclusive', 'terminal', 'end'],
                'learning': ['education', 'instruction', 'study', 'training', 'development'],
                'teaching': ['instruction', 'pedagogy', 'education', 'training'],
                'student': ['learner', 'pupil', 'scholar', 'apprentice'],
                'curriculum': ['syllabus', 'program', 'course', 'academic program'],
                'objective': ['goal', 'aim', 'target', 'outcome', 'purpose'],
                'strategy': ['method', 'approach', 'technique', 'way', 'procedure'],
                'skill': ['ability', 'competency', 'proficiency', 'capability'],
                'knowledge': ['understanding', 'information', 'learning', 'awareness'],
                'performance': ['achievement', 'accomplishment', 'results', 'outcomes'],
                'feedback': ['response', 'comment', 'evaluation', 'review'],
                'engagement': ['participation', 'involvement', 'interaction', 'activity']
            }
            
            results = []
            query_lower = query.lower()
            
            # Find applicable expansions
            for term, synonyms in educational_expansions.items():
                if term in query_lower:
                    for synonym in synonyms[:2]:  # Use top 2 synonyms
                        expanded_query = query_lower.replace(term, synonym)
                        try:
                            expanded_results = self._search_pinecone_advanced(expanded_query, top_k//3, filters, namespace)
                            for result in expanded_results:
                                result['search_method'] = f'keyword_expansion_{term}_{synonym}'
                                result['similarity_score'] *= 0.9  # Slight penalty for expanded terms
                            results.extend(expanded_results)
                        except Exception as e:
                            self.logger.debug(f"Keyword expansion failed for {synonym}: {str(e)}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"ERROR: Educational keyword search failed: {str(e)}")
            return []
    
    def _cross_namespace_search(self, query: str, top_k: int, filters: Dict = None, current_namespace: str = None) -> List[Dict]:
        """Search across different namespaces for comprehensive coverage"""
        try:
            results = []
            # Include both kb-* and edipedia-* namespaces for comprehensive search
            all_namespaces = [
                'kb-psp', 'kb-msp', 'kb-ssp', 'kb-esp',  # KB curriculum namespaces
                'edipedia-k12', 'edipedia-preschools', 'edipedia-edifyho'  # General content namespaces
            ]
            
            # Remove current namespace from search list
            if current_namespace in all_namespaces:
                all_namespaces.remove(current_namespace)
            
            # Prioritize related namespaces based on current namespace
            priority_namespaces = []
            if current_namespace and current_namespace.startswith('kb-'):
                # If searching from kb namespace, prioritize other kb namespaces
                priority_namespaces = [ns for ns in all_namespaces if ns.startswith('kb-')]
                priority_namespaces.extend([ns for ns in all_namespaces if not ns.startswith('kb-')])
            elif current_namespace and current_namespace.startswith('edipedia-'):
                # If searching from edipedia namespace, prioritize other edipedia namespaces
                priority_namespaces = [ns for ns in all_namespaces if ns.startswith('edipedia-')]
                priority_namespaces.extend([ns for ns in all_namespaces if not ns.startswith('edipedia-')])
            else:
                priority_namespaces = all_namespaces
            
            # Search in priority order, limiting total results
            for i, namespace in enumerate(priority_namespaces[:6]):  # Limit to top 6 namespaces
                try:
                    # Reduce search count for lower priority namespaces
                    search_count = max(1, top_k // (3 + i))
                    cross_results = self._search_pinecone_advanced(query, search_count, filters, namespace)
                    
                    for result in cross_results:
                        result['search_method'] = f'cross_namespace_{namespace}'
                        # Apply different penalties based on namespace relationship
                        if namespace.startswith('kb-') and current_namespace and current_namespace.startswith('kb-'):
                            result['similarity_score'] *= 0.92  # Small penalty for related kb namespaces
                        elif namespace.startswith('edipedia-') and current_namespace and current_namespace.startswith('edipedia-'):
                            result['similarity_score'] *= 0.92  # Small penalty for related edipedia namespaces
                        else:
                            result['similarity_score'] *= 0.85  # Larger penalty for cross-type namespaces
                        result['namespace'] = namespace
                    results.extend(cross_results)
                except Exception as e:
                    self.logger.debug(f"Cross-namespace search failed for {namespace}: {str(e)}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"ERROR: Cross-namespace search failed: {str(e)}")
            return []
    
    def _fuzzy_educational_search(self, query: str, top_k: int, filters: Dict = None, namespace: str = None) -> List[Dict]:
        """Fuzzy matching for handling typos and variations in educational terms"""
        try:
            results = []
            
            # Common educational term variations and typos
            fuzzy_corrections = {
                'assesment': 'assessment',
                'evalution': 'evaluation', 
                'learing': 'learning',
                'teching': 'teaching',
                'studens': 'students',
                'objetive': 'objective',
                'stragety': 'strategy',
                'knowlege': 'knowledge',
                'performace': 'performance',
                'engagment': 'engagement',
                'curriculm': 'curriculum',
                'instraction': 'instruction'
            }
            
            # Check for typos and correct them
            corrected_query = query.lower()
            corrections_made = []
            
            for typo, correction in fuzzy_corrections.items():
                if typo in corrected_query:
                    corrected_query = corrected_query.replace(typo, correction)
                    corrections_made.append(f"{typo}->{correction}")
            
            # If corrections were made, search with corrected query
            if corrections_made:
                self.logger.info(f"🔤 Fuzzy corrections applied: {', '.join(corrections_made)}")
                corrected_results = self._search_pinecone_advanced(corrected_query, top_k, filters, namespace)
                for result in corrected_results:
                    result['search_method'] = f'fuzzy_correction'
                    result['similarity_score'] *= 0.95  # Small penalty for fuzzy matching
                results.extend(corrected_results)
            
            return results
            
        except Exception as e:
            self.logger.error(f"ERROR: Fuzzy search failed: {str(e)}")
            return []
    
    def _extract_text_from_metadata(self, metadata: Dict) -> str:
        """Extract text content from metadata with multiple fallbacks"""
        text_keys = ['text', 'content', 'document_content', 'chunk_text', 'chunk_content', 'preview']
        
        for key in text_keys:
            if key in metadata and metadata[key]:
                text = str(metadata[key]).strip()
                if len(text) > 10:  # Ensure meaningful content
                    return text
        
        return ""
    
    def _deduplicate_and_enhance_results(self, results: List[Dict]) -> List[Dict]:
        """Remove duplicates and enhance result metadata"""
        seen_texts = set()
        unique_results = []
        
        for result in results:
            # Create a fingerprint for deduplication
            text = result.get('text', '')
            fingerprint = text[:100].strip().lower() if text else ''
            
            if fingerprint and fingerprint not in seen_texts and len(fingerprint) > 20:
                seen_texts.add(fingerprint)
                
                # Enhance metadata
                metadata = result.get('metadata', {})
                result['chunk_length'] = len(text)
                result['has_educational_terms'] = self._count_educational_terms(text)
                result['content_quality'] = self._assess_content_quality(text, metadata)
                
                unique_results.append(result)
        
        return unique_results
    
    def _apply_educational_scoring(self, results: List[Dict], query: str) -> List[Dict]:
        """Apply educational content-specific scoring for better ranking"""
        try:
            query_words = set(query.lower().split())
            
            for result in results:
                base_score = result.get('similarity_score', 0)
                text = result.get('text', '').lower()
                metadata = result.get('metadata', {})
                
                # Educational content bonus
                educational_bonus = 0
                educational_terms = ['learning', 'teaching', 'education', 'student', 'assessment', 'curriculum']
                educational_bonus += sum(0.02 for term in educational_terms if term in text)
                
                # Query term overlap bonus
                text_words = set(text.split())
                overlap = len(query_words.intersection(text_words))
                overlap_bonus = min(0.1, overlap * 0.02)
                
                # Content quality bonus
                quality_bonus = result.get('content_quality', 0) * 0.05
                
                # Length penalty for very short chunks
                length_penalty = 0
                if result.get('chunk_length', 0) < 100:
                    length_penalty = 0.05
                
                # Namespace bonus (prefer exact namespace matches)
                namespace_bonus = 0.02 if 'cross_namespace' not in result.get('search_method', '') else 0
                
                # Calculate enhanced score
                enhanced_score = base_score + educational_bonus + overlap_bonus + quality_bonus + namespace_bonus - length_penalty
                result['enhanced_score'] = max(0, min(1, enhanced_score))
                
                # Store scoring details for debugging
                result['scoring_details'] = {
                    'base_score': base_score,
                    'educational_bonus': educational_bonus,
                    'overlap_bonus': overlap_bonus,
                    'quality_bonus': quality_bonus,
                    'namespace_bonus': namespace_bonus,
                    'length_penalty': length_penalty
                }
            
            return results
            
        except Exception as e:
            self.logger.error(f"ERROR: Educational scoring failed: {str(e)}")
            return results
    
    def _count_educational_terms(self, text: str) -> int:
        """Count educational terms in text"""
        educational_terms = [
            'assessment', 'evaluation', 'learning', 'teaching', 'education', 'student', 'curriculum',
            'objective', 'strategy', 'skill', 'knowledge', 'performance', 'feedback', 'engagement',
            'instruction', 'pedagogy', 'formative', 'summative', 'rubric', 'standard', 'outcome'
        ]
        
        text_lower = text.lower()
        return sum(1 for term in educational_terms if term in text_lower)
    
    def _assess_content_quality(self, text: str, metadata: Dict) -> float:
        """Assess the quality of educational content"""
        score = 0.5  # Base score
        
        # Length quality
        text_length = len(text)
        if 200 <= text_length <= 1500:
            score += 0.2
        elif text_length < 100:
            score -= 0.2
        
        # Sentence structure
        sentences = text.split('.')
        if len(sentences) >= 2:
            score += 0.1
        
        # Educational terminology density
        educational_term_count = self._count_educational_terms(text)
        if educational_term_count >= 3:
            score += 0.2
        elif educational_term_count >= 1:
            score += 0.1
        
        # Metadata quality indicators
        if metadata.get('section_title'):
            score += 0.1
        if metadata.get('document_title'):
            score += 0.1
        
        return max(0, min(1, score))
    
    def _determine_search_namespace(self, query: str) -> str:
        """Automatically determine the best namespace to search based on query content"""
        query_lower = query.lower()
        
        # Preschool indicators
        preschool_keywords = [
            'preschool', 'pre-school', 'daycare', 'nursery', 'toddler', 
            'early childhood', 'kindergarten prep', 'play-based learning'
        ]
        
        # Grade-specific curriculum indicators (for kb-* namespaces)
        primary_keywords = [
            'grade 1', 'grade 2', 'grade 3', 'grade 4', 'grade 5', 'primary',
            'elementary', 'basic math', 'reading', 'phonics', 'counting'
        ]
        
        middle_keywords = [
            'grade 6', 'grade 7', 'grade 8', 'middle school', 'pre-algebra',
            'earth science', 'life science', 'middle grade'
        ]
        
        secondary_keywords = [
            'grade 9', 'grade 10', 'grade 11', 'grade 12', 'high school',
            'algebra', 'geometry', 'chemistry', 'physics', 'biology', 'calculus'
        ]
        
        early_keywords = [
            'early years', 'foundation', 'pre-primary', 'playgroup', 'nursery'
        ]
        
        # K12 academic indicators (for edipedia-* general content)
        k12_academic_keywords = [
            'curriculum overview', 'educational policy', 'teaching standards',
            'assessment framework', 'academic guidelines', 'learning objectives'
        ]
        
        # Administrative indicators
        admin_keywords = [
            'policy', 'procedure', 'admin', 'management', 'staff', 'employee',
            'hr', 'human resources', 'finance', 'budget', 'compliance', 'audit',
            'legal', 'contract', 'agreement', 'governance'
        ]
        
        # Check for specific grade-level curriculum content (prioritize kb-* namespaces)
        if any(keyword in query_lower for keyword in primary_keywords):
            return 'kb-psp'  # Primary School Programs
        
        if any(keyword in query_lower for keyword in middle_keywords):
            return 'kb-msp'  # Middle School Programs
        
        if any(keyword in query_lower for keyword in secondary_keywords):
            return 'kb-ssp'  # Secondary School Programs
        
        if any(keyword in query_lower for keyword in early_keywords):
            return 'kb-esp'  # Early School Programs
        
        # Check for preschool content
        if any(keyword in query_lower for keyword in preschool_keywords):
            return 'edipedia-preschools'
        
        # Check for administrative content
        if any(keyword in query_lower for keyword in admin_keywords):
            return 'edipedia-edifyho'
        
        # Check for general K12 academic content
        if any(keyword in query_lower for keyword in k12_academic_keywords):
            return 'edipedia-k12'
        
        # Default to enhanced middle school curriculum for general education queries
        return 'kb-msp'
    
    def _enhance_search_results(self, results: List[Dict], query: str) -> List[Dict]:
        """Enhance search results with additional context for AI"""
        enhanced_results = []
        
        for result in results:
            try:
                metadata = result['metadata']
                
                # Add source attribution
                source_info = {
                    'source_file': metadata.get('filename', 'unknown'),
                    'chunk_location': f"Chunk {int(metadata.get('chunk_index', 0)) + 1}",
                    'extraction_method': metadata.get('extraction_method', 'unknown'),
                    'content_type': metadata.get('content_type', 'general')
                }
                
                # Add context from neighboring chunks
                context_info = {
                    'previous_context': metadata.get('previous_chunk_preview', ''),
                    'next_context': metadata.get('next_chunk_preview', ''),
                    'section_index': metadata.get('section_index', 0)
                }
                
                # Calculate relevance score
                relevance_score = self._calculate_relevance_score(result, query)
                
                enhanced_result = {
                    'text': result['text'],
                    'similarity_score': result['similarity_score'],
                    'relevance_score': relevance_score,
                    'source_attribution': source_info,
                    'context': context_info,
                    'metadata': metadata,
                    'rank': result['rank']
                }
                
                enhanced_results.append(enhanced_result)
                
            except Exception as e:
                self.logger.warning(f"WARNING: Failed to enhance result: {str(e)}")
                enhanced_results.append(result)
        
        return enhanced_results
    
    def _calculate_relevance_score(self, result: Dict, query: str) -> float:
        """Calculate a relevance score combining similarity and content factors"""
        try:
            # Base similarity score
            base_score = result['similarity_score']
            
            # Content type bonus
            content_type = result['metadata'].get('content_type', 'general')
            content_bonus = 0.1 if content_type in ['conceptual', 'procedural'] else 0.0
            
            # Length penalty for very short or very long chunks
            chunk_length = int(result['metadata'].get('chunk_length', 0))
            if chunk_length < 100:
                length_penalty = 0.1
            elif chunk_length > 1500:
                length_penalty = 0.05
            else:
                length_penalty = 0.0
            
            # OCR penalty (OCR text may be less accurate)
            ocr_penalty = 0.05 if result['metadata'].get('ocr_used') == 'True' else 0.0
            
            # Calculate final score
            relevance_score = base_score + content_bonus - length_penalty - ocr_penalty
            
            return max(0.0, min(1.0, relevance_score))
            
        except Exception:
            return result['similarity_score']
    
    def _rerank_results(self, results: List[Dict], query: str) -> List[Dict]:
        """Rerank results using relevance score"""
        try:
            # Sort by relevance score (combination of similarity and relevance factors)
            reranked = sorted(
                results,
                key=lambda x: (x.get('relevance_score', 0), x.get('similarity_score', 0)),
                reverse=True
            )
            
            # Update ranks
            for i, result in enumerate(reranked):
                result['rank'] = i + 1
            
            return reranked
            
        except Exception as e:
            self.logger.warning(f"WARNING: Reranking failed: {str(e)}")
            return results
    
    def _enhanced_search_with_fallbacks(self, query: str, top_k: int, filters: Dict, namespace: str, initial_results: List[Dict]) -> List[Dict]:
        """Enhanced search with multiple fallback strategies for better educational content retrieval"""
        try:
            all_results = list(initial_results)  # Start with initial results
            used_ids = set(r.get('metadata', {}).get('chunk_id', '') for r in initial_results)
            
            # Strategy 1: Keyword-based relaxed search
            query_words = query.lower().split()
            if len(query_words) > 1:
                for keyword in query_words:
                    if len(keyword) > 3:  # Only use meaningful words
                        try:
                            if self.db_type == 'pinecone':
                                keyword_results = self._search_pinecone(keyword, top_k//2, filters, namespace)
                            else:
                                keyword_results = []
                            
                            for result in keyword_results:
                                chunk_id = result.get('metadata', {}).get('chunk_id', '')
                                if chunk_id and chunk_id not in used_ids:
                                    # Reduce similarity score slightly for keyword matches
                                    result['similarity_score'] = result.get('similarity_score', 0) * 0.9
                                    all_results.append(result)
                                    used_ids.add(chunk_id)
                        except Exception as e:
                            self.logger.debug(f"Keyword search failed for '{keyword}': {str(e)}")
            
            # Strategy 2: Broader namespace search if we have namespaces
            if namespace and self.db_type == 'pinecone':
                try:
                    # Try searching in the general namespace as fallback
                    if namespace != 'general':
                        general_results = self._search_pinecone(query, top_k//2, filters, 'general')
                        for result in general_results:
                            chunk_id = result.get('metadata', {}).get('chunk_id', '')
                            if chunk_id and chunk_id not in used_ids:
                                # Reduce similarity score for cross-namespace matches
                                result['similarity_score'] = result.get('similarity_score', 0) * 0.85
                                result['namespace'] = 'general'
                                all_results.append(result)
                                used_ids.add(chunk_id)
                except Exception as e:
                    self.logger.debug(f"Cross-namespace search failed: {str(e)}")
            
            # Strategy 3: Expanded educational terms search
            educational_expansions = {
                'assessment': ['evaluation', 'testing', 'grading', 'measurement'],
                'learning': ['education', 'instruction', 'teaching', 'study'],
                'student': ['learner', 'pupil', 'child'],
                'teaching': ['instruction', 'education', 'pedagogy'],
                'classroom': ['class', 'learning environment', 'educational setting']
            }
            
            for term, expansions in educational_expansions.items():
                if term in query.lower():
                    for expansion in expansions:
                        try:
                            if self.db_type == 'pinecone':
                                expanded_results = self._search_pinecone(
                                    query.replace(term, expansion), top_k//3, filters, namespace
                                )
                            else:
                                expanded_results = []
                            
                            for result in expanded_results:
                                chunk_id = result.get('metadata', {}).get('chunk_id', '')
                                if chunk_id and chunk_id not in used_ids:
                                    # Reduce similarity score for expanded term matches
                                    result['similarity_score'] = result.get('similarity_score', 0) * 0.8
                                    all_results.append(result)
                                    used_ids.add(chunk_id)
                        except Exception as e:
                            self.logger.debug(f"Expanded search failed for '{expansion}': {str(e)}")
            
            # Remove duplicates and sort by similarity
            unique_results = []
            seen_texts = set()
            for result in all_results:
                text_snippet = result.get('text', '')[:100]  # Use first 100 chars as fingerprint
                if text_snippet and text_snippet not in seen_texts:
                    unique_results.append(result)
                    seen_texts.add(text_snippet)
            
            # Sort by similarity score and limit to top_k
            unique_results.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)
            return unique_results[:top_k]
            
        except Exception as e:
            self.logger.error(f"Enhanced search fallback failed: {str(e)}")
            return initial_results
    
    def get_chunk_by_id(self, chunk_id: str) -> Optional[Dict]:
        """Retrieve a specific chunk by its ID"""
        try:
            if self.db_type == 'chromadb':
                results = self.collection.get(ids=[chunk_id])
                if results['documents'] and results['documents'][0]:
                    return {
                        'text': results['documents'][0],
                        'metadata': results['metadatas'][0]
                    }
            elif self.db_type == 'faiss':
                for metadata in self.faiss_metadata.values():
                    if metadata.get('chunk_id') == chunk_id:
                        return {
                            'text': metadata.get('text', ''),
                            'metadata': metadata
                        }
            
            return None
            
        except Exception as e:
            self.logger.error(f"ERROR: Failed to retrieve chunk {chunk_id}: {str(e)}")
            return None
    
    def get_context_chunks(self, chunk_id: str, context_size: int = 2) -> List[Dict]:
        """Get neighboring chunks for additional context"""
        try:
            # Find the target chunk
            target_chunk = self.get_chunk_by_id(chunk_id)
            if not target_chunk:
                return []
            
            filename = target_chunk['metadata'].get('filename')
            chunk_index = int(target_chunk['metadata'].get('chunk_index', 0))
            
            # Search for neighboring chunks
            context_chunks = []
            
            if self.db_type == 'chromadb':
                # Search for chunks from same file with nearby indices
                for i in range(max(0, chunk_index - context_size), chunk_index + context_size + 1):
                    if i != chunk_index:  # Skip the target chunk itself
                        neighbor_id = f"{filename}_{i:03d}"
                        neighbor = self.get_chunk_by_id(neighbor_id)
                        if neighbor:
                            context_chunks.append(neighbor)
            
            elif self.db_type == 'faiss':
                # Search through metadata for neighboring chunks
                for metadata in self.faiss_metadata.values():
                    if (metadata.get('filename') == filename and
                        abs(int(metadata.get('chunk_index', 0)) - chunk_index) <= context_size and
                        metadata.get('chunk_id') != chunk_id):
                        context_chunks.append({
                            'text': metadata.get('text', ''),
                            'metadata': metadata
                        })
            
            # Sort by chunk index
            context_chunks.sort(key=lambda x: int(x['metadata'].get('chunk_index', 0)))
            
            return context_chunks
            
        except Exception as e:
            self.logger.error(f"ERROR: Failed to get context for chunk {chunk_id}: {str(e)}")
            return []
    
    def get_collection_stats(self) -> Dict:
        """Get detailed statistics about the vector database"""
        try:
            total_chunks = 0
            
            if self.db_type == 'chromadb':
                total_chunks = self.collection.count()
            elif self.db_type == 'faiss':
                total_chunks = self.faiss_index.ntotal
            elif self.db_type == 'pinecone':
                stats = self.pinecone_index.describe_index_stats()
                total_chunks = stats.get('total_vector_count', 0)
            
            return {
                'database_type': self.db_type,
                'total_chunks': total_chunks,
                'embedding_dimension': self.embedding_dim,
                'embedding_model': self.embedding_model_name,
                'chunks_stored': self.stats['chunks_stored'],
                'queries_processed': self.stats['queries_processed'],
                'average_query_time_ms': self.stats['average_query_time'] * 1000,
                'last_update': self.stats['last_update']
            }
            
        except Exception as e:
            self.logger.error(f"ERROR: Failed to get collection stats: {str(e)}")
            return {}
    
    def create_search_index(self) -> bool:
        """Create optimized search index for faster retrieval"""
        try:
            if self.db_type == 'faiss' and hasattr(self, 'faiss_index'):
                # Train the index for better performance
                if self.faiss_index.ntotal > 100:
                    self.logger.info("🔧 Optimizing FAISS index for faster search...")
                    # For HNSW index, we can adjust search parameters
                    self.faiss_index.hnsw.efSearch = min(200, self.faiss_index.ntotal)
                    self._save_faiss_index()
                    self.logger.info("SUCCESS: FAISS index optimized")
                    return True
            
            elif self.db_type == 'chromadb':
                # ChromaDB handles indexing automatically
                self.logger.info("SUCCESS: ChromaDB indexing is automatic")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"ERROR: Failed to create search index: {str(e)}")
            return False
    
    def clear_collection(self) -> bool:
        """Clear all data from the vector database"""
        try:
            if self.db_type == 'chromadb':
                # Delete and recreate collection
                self.db_client.delete_collection(self.collection_name)
                self.collection = self.db_client.create_collection(
                    name=self.collection_name,
                    embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(
                        model_name=self.embedding_model_name
                    ),
                    metadata={"description": "Enhanced PDF chunks for AI chatbot retrieval"}
                )
                
            elif self.db_type == 'faiss':
                # Reset FAISS index
                self.faiss_index = faiss.IndexHNSWFlat(self.embedding_dim, 32)
                self.faiss_index.hnsw.efConstruction = 200
                self.faiss_index.hnsw.efSearch = 100
                self.faiss_metadata = {}
                self.faiss_id_counter = 0
                self._save_faiss_index()
                
            elif self.db_type == 'pinecone':
                # Delete all vectors from Pinecone index
                self.pinecone_index.delete(delete_all=True)
            
            # Reset statistics
            self.stats['chunks_stored'] = 0
            self.stats['last_update'] = None
            
            self.logger.info(f"SUCCESS: Cleared all data from {self.db_type} collection")
            return True
            
        except Exception as e:
            self.logger.error(f"ERROR: Failed to clear collection: {str(e)}")
            return False
    
    def delete_chunks_by_filename(self, filename: str) -> bool:
        """Delete all chunks from a specific file"""
        try:
            if self.db_type == 'pinecone':
                # Pinecone supports filtering for deletion
                self.pinecone_index.delete(filter={"filename": {"$eq": filename}})
                self.logger.info(f"SUCCESS: Deleted chunks for file: {filename}")
                return True
                
            elif self.db_type == 'chromadb':
                # ChromaDB delete with where clause
                try:
                    self.collection.delete(where={"filename": filename})
                    self.logger.info(f"SUCCESS: Deleted chunks for file: {filename}")
                    return True
                except Exception as e:
                    self.logger.warning(f"WARNING: Could not delete from ChromaDB: {str(e)}")
                    return False
                    
            elif self.db_type == 'faiss':
                # FAISS requires rebuilding without the deleted items
                self.logger.warning("WARNING: FAISS requires full rebuild to delete specific files")
                return False
            
        except Exception as e:
            self.logger.error(f"ERROR: Failed to delete chunks for file {filename}: {str(e)}")
            return False
