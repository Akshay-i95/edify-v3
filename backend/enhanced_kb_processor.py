"""
Enhanced KB Multi-Format Processor
Handles PDF, PPTX, DOCX, MP4, and other formats from KB module
Organizes data into Pinecone namespaces: kb-esp, kb-psp, kb-msp, kb-ssp
"""

import io
import logging
import time
import os
import tempfile
from typing import List, Dict, Tuple, Optional, Any
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import json
from datetime import datetime

# File format processors
import PyPDF2
import pdfplumber
import fitz  # PyMuPDF
from pptx import Presentation
from docx import Document
import zipfile
import xml.etree.ElementTree as ET

# OCR and Image Processing
try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

# Azure and Vector DB
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import AzureError
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer

# Text processing
import tiktoken
import re

class EnhancedKBProcessor:
    def __init__(self, config: Dict):
        """Initialize the enhanced KB processor for multiple file formats"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize tokenizer
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to load tokenizer: {str(e)}")
            self.tokenizer = None
        
        # Initialize embedding model
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            self.logger.info("✅ Embedding model loaded")
        except Exception as e:
            self.logger.error(f"❌ Failed to load embedding model: {str(e)}")
            raise
        
        # Configure processing parameters
        self.chunk_size = int(config.get('chunk_size', 600))
        self.chunk_overlap = int(config.get('chunk_overlap', 120))
        self.min_chunk_length = int(config.get('min_chunk_length', 100))
        self.max_chunk_length = int(config.get('max_chunk_length', 1200))
        self.batch_size = int(config.get('batch_size', 15))
        self.max_workers = int(config.get('max_workers', 4))
        
        # Namespace mapping
        self.namespace_mapping = {
            'kb-esp': ['playgroup', 'ik1', 'ik2', 'ik3'],  # Early Stage Program
            'kb-psp': ['grade1', 'grade2', 'grade3', 'grade4', 'grade5'],  # Primary Stage Program
            'kb-msp': ['grade6', 'grade7', 'grade8', 'grade9', 'grade10'],  # Middle Stage Program
            'kb-ssp': ['grade11', 'grade12']  # Senior Stage Program
        }
        
        # File type handlers
        self.file_handlers = {
            '.pdf': self._process_pdf,
            '.pptx': self._process_pptx,
            '.docx': self._process_docx,
            '.mp4': self._process_mp4,
            '.ppt': self._process_ppt,
            '.xlsx': self._process_xlsx,
            '.doc': self._process_doc,
            '.html': self._process_html,
            '.pptm': self._process_pptx  # Same as pptx
        }
        
        # Statistics tracking
        self.stats = {
            'total_files': 0,
            'processed_files': 0,
            'failed_files': 0,
            'chunks_created': 0,
            'files_by_type': {},
            'files_by_namespace': {},
            'processing_times': {},
            'start_time': time.time(),
            'current_file': '',
            'completion_percentage': 0.0
        }
        
        # Initialize Azure and Pinecone
        self._initialize_connections()
        
    def _initialize_connections(self):
        """Initialize Azure Blob Storage and Pinecone connections"""
        try:
            # Azure Blob Storage
            connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
            if not connection_string:
                raise ValueError("AZURE_STORAGE_CONNECTION_STRING not found")
            
            self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
            self.container_name = 'edifydocumentcontainer'
            self.container_client = self.blob_service_client.get_container_client(self.container_name)
            
            # Pinecone
            pinecone_api_key = os.getenv('PINECONE_API_KEY')
            if not pinecone_api_key:
                raise ValueError("PINECONE_API_KEY not found")
            
            self.pc = Pinecone(api_key=pinecone_api_key)
            
            self.index_name = os.getenv('PINECONE_INDEX_NAME', 'edify-edicenter')
            self.index = self.pc.Index(self.index_name)
            
            self.logger.info("✅ Azure and Pinecone connections initialized")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize connections: {str(e)}")
            raise
    
    def get_namespace_for_grade(self, grade: str) -> str:
        """Determine the Pinecone namespace for a given grade"""
        grade_lower = grade.lower()
        
        for namespace, grades in self.namespace_mapping.items():
            if grade_lower in grades:
                return namespace
        
        # Default fallback
        if 'common' in grade_lower:
            return 'kb-psp'  # Common files go to primary
        
        return 'kb-msp'  # Default to middle stage
    
    async def process_kb_directory(self, target_year: str = '12'):
        """Process all files in the specified KB directory year"""
        self.logger.info(f"🚀 Starting KB processing for year: {target_year}")
        
        try:
            # Get all files from the target directory
            files = list(self.container_client.list_blobs(name_starts_with=f'kb/{target_year}/'))
            
            if not files:
                self.logger.warning(f"⚠️ No files found in kb/{target_year}/")
                return
            
            # Organize files by grade and type
            organized_files = self._organize_files(files, target_year)
            
            # Process each namespace separately
            for namespace, file_data in organized_files.items():
                self.logger.info(f"📚 Processing namespace: {namespace} ({len(file_data)} files)")
                await self._process_namespace(namespace, file_data)
            
            # Final statistics
            self._print_final_statistics()
            
        except Exception as e:
            self.logger.error(f"❌ Error processing KB directory: {str(e)}")
            raise
    
    def _organize_files(self, files, target_year: str) -> Dict[str, List]:
        """Organize files by namespace and collect metadata"""
        organized = {
            'kb-esp': [],
            'kb-psp': [],
            'kb-msp': [],
            'kb-ssp': []
        }
        
        for blob in files:
            try:
                path_parts = blob.name.split('/')
                if len(path_parts) < 3:
                    continue
                
                year = path_parts[1]
                grade = path_parts[2]
                filename = path_parts[-1]
                
                # Skip if not target year
                if year != target_year:
                    continue
                
                # Get file extension
                file_ext = Path(filename).suffix.lower()
                
                # Skip unsupported file types
                if file_ext not in self.file_handlers:
                    self.logger.debug(f"⚠️ Unsupported file type: {filename}")
                    continue
                
                # Determine namespace
                namespace = self.get_namespace_for_grade(grade)
                
                # Add to organized structure
                file_info = {
                    'blob_name': blob.name,
                    'filename': filename,
                    'grade': grade,
                    'file_type': file_ext,
                    'size': blob.size,
                    'last_modified': blob.last_modified
                }
                
                organized[namespace].append(file_info)
                
                # Update statistics
                if file_ext not in self.stats['files_by_type']:
                    self.stats['files_by_type'][file_ext] = 0
                self.stats['files_by_type'][file_ext] += 1
                
                if namespace not in self.stats['files_by_namespace']:
                    self.stats['files_by_namespace'][namespace] = 0
                self.stats['files_by_namespace'][namespace] += 1
                
            except Exception as e:
                self.logger.warning(f"⚠️ Error organizing file {blob.name}: {str(e)}")
                continue
        
        self.stats['total_files'] = sum(len(files) for files in organized.values())
        
        self.logger.info(f"📊 File organization complete:")
        for namespace, files in organized.items():
            self.logger.info(f"   {namespace}: {len(files)} files")
        
        return organized
    
    async def _process_namespace(self, namespace: str, files: List[Dict]):
        """Process all files for a specific namespace"""
        self.logger.info(f"🔄 Processing {len(files)} files for namespace: {namespace}")
        
        # Process files in batches
        for i in range(0, len(files), self.batch_size):
            batch = files[i:i + self.batch_size]
            
            self.logger.info(f"📦 Processing batch {i//self.batch_size + 1}/{(len(files)-1)//self.batch_size + 1}")
            
            # Process batch
            batch_chunks = self._process_file_batch(batch, namespace)
            
            # Upload to Pinecone
            if batch_chunks:
                await self._upload_to_pinecone(batch_chunks, namespace)
            
            # Update progress
            self.stats['completion_percentage'] = ((i + len(batch)) / self.stats['total_files']) * 100
            
            # Live statistics
            self._print_live_statistics()
    
    def _process_file_batch(self, files: List[Dict], namespace: str) -> List[Dict]:
        """Process a batch of files with reduced memory usage"""
        all_chunks = []
        
        # Reduce concurrent workers to prevent memory exhaustion
        max_workers = min(2, self.max_workers)  # Max 2 workers
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Process files in smaller sub-batches to manage memory
            batch_size = 2  # Process 2 files at a time
            
            for i in range(0, len(files), batch_size):
                sub_batch = files[i:i + batch_size]
                
                future_to_file = {
                    executor.submit(self._process_single_file, file_info, namespace): file_info
                    for file_info in sub_batch
                }
                
                for future in as_completed(future_to_file):
                    file_info = future_to_file[future]
                    try:
                        chunks = future.result()
                        if chunks:
                            all_chunks.extend(chunks)
                            self.stats['processed_files'] += 1
                        else:
                            self.stats['failed_files'] += 1
                        
                        # Clear chunk data immediately after processing
                        del chunks
                        
                    except Exception as e:
                        self.logger.error(f"❌ Error processing {file_info['filename']}: {str(e)}")
                        self.stats['failed_files'] += 1
                
                # Force garbage collection after each sub-batch
                import gc
                gc.collect()
        
        return all_chunks
    
    def _process_single_file(self, file_info: Dict, namespace: str) -> List[Dict]:
        """Process a single file based on its type"""
        try:
            self.stats['current_file'] = file_info['filename']
            start_time = time.time()
            
            blob_name = file_info['blob_name']
            file_type = file_info['file_type']
            
            # Get the appropriate handler
            handler = self.file_handlers.get(file_type)
            if not handler:
                self.logger.warning(f"⚠️ No handler for file type: {file_type}")
                return []
            
            # Download file content
            blob_client = self.container_client.get_blob_client(blob_name)
            file_content = blob_client.download_blob().readall()
            
            # Process with appropriate handler
            text_content, metadata = handler(file_content, file_info)
            
            if not text_content or len(text_content.strip()) < 50:
                self.logger.warning(f"⚠️ Minimal content extracted from {file_info['filename']}")
                return []
            
            # Create chunks
            chunks = self._create_chunks(text_content, file_info, metadata, namespace)
            
            # Update processing time
            processing_time = time.time() - start_time
            self.stats['processing_times'][file_type] = self.stats['processing_times'].get(file_type, [])
            self.stats['processing_times'][file_type].append(processing_time)
            
            self.logger.info(f"✅ Processed {file_info['filename']}: {len(chunks)} chunks in {processing_time:.2f}s")
            
            return chunks
            
        except Exception as e:
            self.logger.error(f"❌ Error processing {file_info['filename']}: {str(e)}")
            return []
    
    def _process_pdf(self, content: bytes, file_info: Dict) -> Tuple[str, Dict]:
        """Process PDF files"""
        try:
            pdf_stream = io.BytesIO(content)
            text_content = ""
            metadata = {'pages': 0, 'extraction_method': 'pdf'}
            
            # Try pdfplumber first
            try:
                import pdfplumber
                with pdfplumber.open(pdf_stream) as pdf:
                    pages_text = []
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text and page_text.strip():
                            pages_text.append(page_text)
                    
                    if pages_text:
                        text_content = "\n\n".join(pages_text)
                        metadata['pages'] = len(pdf.pages)
                        metadata['extraction_method'] = 'pdfplumber'
            except Exception as e:
                self.logger.debug(f"pdfplumber failed for {file_info['filename']}: {str(e)}")
            
            # Fallback to PyMuPDF
            if not text_content:
                try:
                    pdf_stream.seek(0)
                    pdf_doc = fitz.open(stream=content, filetype="pdf")
                    pages_text = []
                    
                    for page_num in range(pdf_doc.page_count):
                        page = pdf_doc[page_num]
                        page_text = page.get_text()
                        if page_text and page_text.strip():
                            pages_text.append(page_text)
                    
                    if pages_text:
                        text_content = "\n\n".join(pages_text)
                        metadata['pages'] = pdf_doc.page_count
                        metadata['extraction_method'] = 'PyMuPDF'
                    
                    pdf_doc.close()
                except Exception as e:
                    self.logger.debug(f"PyMuPDF failed for {file_info['filename']}: {str(e)}")
            
            return text_content, metadata
            
        except Exception as e:
            self.logger.error(f"❌ PDF processing failed: {str(e)}")
            return "", {}
    
    def _process_pptx(self, content: bytes, file_info: Dict) -> Tuple[str, Dict]:
        """Process PowerPoint files (.pptx)"""
        try:
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix='.pptx', delete=False) as temp_file:
                temp_file.write(content)
                temp_path = temp_file.name
            
            try:
                prs = Presentation(temp_path)
                slides_text = []
                
                for slide_num, slide in enumerate(prs.slides):
                    slide_text = []
                    
                    # Extract text from shapes
                    for shape in slide.shapes:
                        if hasattr(shape, "text") and shape.text.strip():
                            slide_text.append(shape.text.strip())
                    
                    if slide_text:
                        slides_text.append(f"--- Slide {slide_num + 1} ---\n" + "\n".join(slide_text))
                
                text_content = "\n\n".join(slides_text)
                metadata = {
                    'slides': len(prs.slides),
                    'extraction_method': 'python-pptx'
                }
                
                return text_content, metadata
                
            finally:
                os.unlink(temp_path)
                
        except Exception as e:
            self.logger.error(f"❌ PPTX processing failed: {str(e)}")
            return "", {}
    
    def _process_docx(self, content: bytes, file_info: Dict) -> Tuple[str, Dict]:
        """Process Word documents (.docx)"""
        try:
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as temp_file:
                temp_file.write(content)
                temp_path = temp_file.name
            
            try:
                doc = Document(temp_path)
                paragraphs = []
                
                for paragraph in doc.paragraphs:
                    if paragraph.text.strip():
                        paragraphs.append(paragraph.text.strip())
                
                # Extract text from tables
                for table in doc.tables:
                    for row in table.rows:
                        row_text = []
                        for cell in row.cells:
                            if cell.text.strip():
                                row_text.append(cell.text.strip())
                        if row_text:
                            paragraphs.append(" | ".join(row_text))
                
                text_content = "\n\n".join(paragraphs)
                metadata = {
                    'paragraphs': len(doc.paragraphs),
                    'tables': len(doc.tables),
                    'extraction_method': 'python-docx'
                }
                
                return text_content, metadata
                
            finally:
                os.unlink(temp_path)
                
        except Exception as e:
            self.logger.error(f"❌ DOCX processing failed: {str(e)}")
            return "", {}
    
    def _process_mp4(self, content: bytes, file_info: Dict) -> Tuple[str, Dict]:
        """Process MP4 video files (extract metadata only for now)"""
        try:
            # For now, we'll just create a placeholder with metadata
            # In future, we could add video transcription capabilities
            filename = file_info['filename']
            size_mb = len(content) / (1024 * 1024)
            
            text_content = f"""
            Video File: {filename}
            File Type: MP4 Video
            Size: {size_mb:.2f} MB
            Grade: {file_info['grade']}
            
            This is a video educational resource. Video content analysis and transcription 
            capabilities can be added in future iterations.
            """
            
            metadata = {
                'file_type': 'video',
                'size_mb': size_mb,
                'extraction_method': 'metadata_only'
            }
            
            return text_content.strip(), metadata
            
        except Exception as e:
            self.logger.error(f"❌ MP4 processing failed: {str(e)}")
            return "", {}
    
    def _process_ppt(self, content: bytes, file_info: Dict) -> Tuple[str, Dict]:
        """Process legacy PowerPoint files (.ppt)"""
        try:
            # For .ppt files, we'll extract what we can or provide metadata
            filename = file_info['filename']
            size_mb = len(content) / (1024 * 1024)
            
            text_content = f"""
            PowerPoint File: {filename}
            File Type: Legacy PowerPoint (.ppt)
            Size: {size_mb:.2f} MB
            Grade: {file_info['grade']}
            
            This is a legacy PowerPoint presentation. For full text extraction,
            consider converting to .pptx format.
            """
            
            metadata = {
                'file_type': 'presentation',
                'size_mb': size_mb,
                'extraction_method': 'metadata_only'
            }
            
            return text_content.strip(), metadata
            
        except Exception as e:
            self.logger.error(f"❌ PPT processing failed: {str(e)}")
            return "", {}
    
    def _process_xlsx(self, content: bytes, file_info: Dict) -> Tuple[str, Dict]:
        """Process Excel files (.xlsx)"""
        try:
            import pandas as pd
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
                temp_file.write(content)
                temp_path = temp_file.name
            
            try:
                # Read all sheets
                excel_file = pd.ExcelFile(temp_path)
                sheets_text = []
                
                for sheet_name in excel_file.sheet_names:
                    df = pd.read_excel(temp_path, sheet_name=sheet_name)
                    
                    # Convert to text representation
                    if not df.empty:
                        sheet_text = f"--- Sheet: {sheet_name} ---\n"
                        sheet_text += df.to_string(index=False)
                        sheets_text.append(sheet_text)
                
                text_content = "\n\n".join(sheets_text)
                metadata = {
                    'sheets': len(excel_file.sheet_names),
                    'extraction_method': 'pandas'
                }
                
                return text_content, metadata
                
            finally:
                os.unlink(temp_path)
                
        except ImportError:
            # Fallback if pandas not available
            filename = file_info['filename']
            text_content = f"Excel File: {filename}\nRequires pandas for full text extraction."
            metadata = {'extraction_method': 'metadata_only'}
            return text_content, metadata
        except Exception as e:
            self.logger.error(f"❌ XLSX processing failed: {str(e)}")
            return "", {}
    
    def _process_doc(self, content: bytes, file_info: Dict) -> Tuple[str, Dict]:
        """Process legacy Word documents (.doc)"""
        try:
            # For now, provide metadata only
            # Full .doc processing would require additional libraries like python-docx2txt
            filename = file_info['filename']
            size_mb = len(content) / (1024 * 1024)
            
            text_content = f"""
            Word Document: {filename}
            File Type: Legacy Word Document (.doc)
            Size: {size_mb:.2f} MB
            Grade: {file_info['grade']}
            
            This is a legacy Word document. For full text extraction,
            consider converting to .docx format.
            """
            
            metadata = {
                'file_type': 'document',
                'size_mb': size_mb,
                'extraction_method': 'metadata_only'
            }
            
            return text_content.strip(), metadata
            
        except Exception as e:
            self.logger.error(f"❌ DOC processing failed: {str(e)}")
            return "", {}
    
    def _process_html(self, content: bytes, file_info: Dict) -> Tuple[str, Dict]:
        """Process HTML files"""
        try:
            from bs4 import BeautifulSoup
            
            # Parse HTML
            soup = BeautifulSoup(content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text
            text_content = soup.get_text()
            
            # Clean up text
            lines = (line.strip() for line in text_content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text_content = '\n'.join(chunk for chunk in chunks if chunk)
            
            metadata = {
                'extraction_method': 'beautifulsoup'
            }
            
            return text_content, metadata
            
        except ImportError:
            # Fallback without BeautifulSoup
            text_content = content.decode('utf-8', errors='ignore')
            # Basic HTML tag removal
            text_content = re.sub(r'<[^>]+>', '', text_content)
            metadata = {'extraction_method': 'basic_html'}
            return text_content, metadata
        except Exception as e:
            self.logger.error(f"❌ HTML processing failed: {str(e)}")
            return "", {}
    
    def _create_chunks(self, text: str, file_info: Dict, metadata: Dict, namespace: str) -> List[Dict]:
        """Create chunks from extracted text"""
        if not text or len(text.strip()) < self.min_chunk_length:
            return []
        
        chunks = []
        text = text.strip()
        
        # Split text into chunks
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        current_chunk = ""
        current_tokens = 0
        
        for para in paragraphs:
            # Calculate tokens
            if self.tokenizer:
                para_tokens = len(self.tokenizer.encode(para))
            else:
                para_tokens = len(para) // 4
            
            # Check if adding this paragraph would exceed chunk size
            if current_tokens + para_tokens > self.chunk_size and current_chunk:
                # Create chunk
                if len(current_chunk) >= self.min_chunk_length:
                    chunk = self._create_chunk_metadata(
                        current_chunk, file_info, metadata, namespace, len(chunks)
                    )
                    chunks.append(chunk)
                
                # Start new chunk with overlap
                overlap = self._get_overlap(current_chunk)
                current_chunk = overlap + "\n\n" + para if overlap else para
                current_tokens = len(self.tokenizer.encode(current_chunk)) if self.tokenizer else len(current_chunk) // 4
            else:
                current_chunk += "\n\n" + para if current_chunk else para
                current_tokens += para_tokens
        
        # Add final chunk
        if current_chunk and len(current_chunk) >= self.min_chunk_length:
            chunk = self._create_chunk_metadata(
                current_chunk, file_info, metadata, namespace, len(chunks)
            )
            chunks.append(chunk)
        
        self.stats['chunks_created'] += len(chunks)
        return chunks
    
    def _get_overlap(self, text: str) -> str:
        """Get overlap text from the end of current chunk"""
        if len(text) <= self.chunk_overlap:
            return text
        
        overlap_text = text[-self.chunk_overlap:]
        # Try to break at sentence boundary
        sentence_break = overlap_text.find('. ')
        if sentence_break > 0:
            return overlap_text[sentence_break + 2:]
        
        return overlap_text
    
    def _create_chunk_metadata(self, chunk_text: str, file_info: Dict, file_metadata: Dict, namespace: str, chunk_index: int) -> Dict:
        """Create comprehensive metadata for a chunk"""
        metadata = {
            'id': f"{file_info['filename']}_{chunk_index:03d}",
            'text': chunk_text,
            'namespace': namespace,
            'filename': file_info['filename'],
            'grade': file_info['grade'],
            'file_type': file_info['file_type'],
            'chunk_index': chunk_index,
            'chunk_length': len(chunk_text),
            'source_path': file_info['blob_name'],
            'extraction_method': file_metadata.get('extraction_method', 'unknown'),
            'created_at': datetime.now().isoformat(),
            'file_size': file_info['size'],
            'last_modified': file_info['last_modified'].isoformat() if file_info['last_modified'] else None
        }
        
        # Add video-specific metadata if available
        if file_metadata.get('video_url'):
            metadata['video_url'] = file_metadata['video_url']
            metadata['media_type'] = file_metadata.get('media_type', 'video')
            metadata['has_video_content'] = file_metadata.get('has_video_content', True)
            metadata['transcription_available'] = file_metadata.get('transcription_available', False)
            metadata['video_duration'] = file_metadata.get('duration_seconds', 0)
            
        return metadata
    
    async def _upload_to_pinecone(self, chunks: List[Dict], namespace: str):
        """Upload chunks to Pinecone with embeddings"""
        try:
            if not chunks:
                return
            
            self.logger.info(f"🔄 Generating embeddings for {len(chunks)} chunks...")
            
            # Generate embeddings
            texts = [chunk['text'] for chunk in chunks]
            embeddings = self.embedding_model.encode(texts, convert_to_tensor=False)
            
            # Prepare vectors for Pinecone
            vectors = []
            for chunk, embedding in zip(chunks, embeddings):
                vector = {
                    'id': chunk['id'],
                    'values': embedding.tolist(),
                    'metadata': {k: v for k, v in chunk.items() if k != 'text'}
                }
                vectors.append(vector)
            
            # Upload to Pinecone in batches
            batch_size = 100
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                self.index.upsert(vectors=batch, namespace=namespace)
                
                self.logger.info(f"✅ Uploaded batch {i//batch_size + 1}/{(len(vectors)-1)//batch_size + 1} to {namespace}")
            
            self.logger.info(f"✅ Uploaded {len(chunks)} chunks to namespace: {namespace}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error uploading to Pinecone: {str(e)}")
            return False
    
    def _print_live_statistics(self):
        """Print live processing statistics"""
        elapsed_time = time.time() - self.stats['start_time']
        processed = self.stats['processed_files']
        failed = self.stats['failed_files']
        total = self.stats['total_files']
        
        if total > 0:
            success_rate = (processed / (processed + failed)) * 100 if (processed + failed) > 0 else 0
            completion = self.stats['completion_percentage']
            
            print(f"\n📊 LIVE STATISTICS")
            print(f"═══════════════════════════════════════")
            print(f"📁 Current File: {self.stats['current_file'][:50]}...")
            print(f"⏱️  Elapsed Time: {elapsed_time:.1f}s")
            print(f"📈 Progress: {completion:.1f}% ({processed + failed}/{total})")
            print(f"✅ Success Rate: {success_rate:.1f}%")
            print(f"📄 Chunks Created: {self.stats['chunks_created']:,}")
            print(f"═══════════════════════════════════════")
    
    def _print_final_statistics(self):
        """Print final processing statistics"""
        elapsed_time = time.time() - self.stats['start_time']
        processed = self.stats['processed_files']
        failed = self.stats['failed_files']
        total = self.stats['total_files']
        
        print(f"\n🎉 FINAL PROCESSING STATISTICS")
        print(f"═══════════════════════════════════════════════")
        print(f"⏱️  Total Processing Time: {elapsed_time:.1f}s")
        print(f"📁 Total Files: {total:,}")
        print(f"✅ Successfully Processed: {processed:,}")
        print(f"❌ Failed: {failed:,}")
        print(f"📈 Success Rate: {(processed/total)*100:.1f}%")
        print(f"📄 Total Chunks Created: {self.stats['chunks_created']:,}")
        print(f"⚡ Average Processing Speed: {processed/(elapsed_time/60):.1f} files/minute")
        
        print(f"\n📊 FILES BY TYPE:")
        for file_type, count in self.stats['files_by_type'].items():
            print(f"   {file_type}: {count:,} files")
        
        print(f"\n🎯 FILES BY NAMESPACE:")
        for namespace, count in self.stats['files_by_namespace'].items():
            print(f"   {namespace}: {count:,} files")
        
        print(f"\n⏱️  AVERAGE PROCESSING TIMES BY TYPE:")
        for file_type, times in self.stats['processing_times'].items():
            avg_time = sum(times) / len(times)
            print(f"   {file_type}: {avg_time:.2f}s")
        
        print(f"═══════════════════════════════════════════════")

# Async wrapper for the main processing
async def main():
    """Main processing function"""
    import os
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Configuration
    config = {
        'chunk_size': int(os.getenv('CHUNK_SIZE', 600)),
        'chunk_overlap': int(os.getenv('CHUNK_OVERLAP', 120)),
        'min_chunk_length': int(os.getenv('MIN_CHUNK_LENGTH', 100)),
        'max_chunk_length': int(os.getenv('MAX_CHUNK_LENGTH', 1200)),
        'batch_size': int(os.getenv('BATCH_SIZE', 15)),
        'max_workers': int(os.getenv('MAX_WORKERS', 4))
    }
    
    # Initialize processor
    processor = EnhancedKBProcessor(config)
    
    # Process KB directory (12/ only as specified)
    await processor.process_kb_directory(target_year='12')

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())