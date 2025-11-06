"""
Improved Metadata Service with Multi-Strategy UUID Matching
This service implements intelligent document matching across different UUID systems.
"""
import json
import logging
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import requests
from difflib import SequenceMatcher
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImprovedMetadataService:
    def __init__(self):
        self.edify_metadata_cache = {}
        self.filename_similarity_cache = {}
        self.uuid_mapping_cache = {}
        self.last_cache_update = None
        
        # Edify API configuration
        self.edify_api_url = "https://api.edify.ac.in/api/sop"
        self.edify_headers = {
            'accept': 'application/json',
            'authorization': 'bearer 9b1b2da2-a6f8-4636-b13a-4b4e9ff82bd9'
        }
        
        logger.info("Improved Metadata Service initialized")
    
    def _extract_uuid_from_path(self, path: str) -> Optional[str]:
        """Extract UUID from file path using regex"""
        uuid_pattern = r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})'
        match = re.search(uuid_pattern, path, re.IGNORECASE)
        return match.group(1) if match else None
    
    def _calculate_filename_similarity(self, filename1: str, filename2: str) -> float:
        """Calculate similarity between two filenames"""
        # Normalize filenames for comparison
        name1 = filename1.lower().replace('.pdf', '').replace('-', ' ').replace('_', ' ')
        name2 = filename2.lower().replace('.pdf', '').replace('-', ' ').replace('_', ' ')
        
        # Remove common prefixes/numbers
        name1 = re.sub(r'^\d+\.?\s*', '', name1)
        name2 = re.sub(r'^\d+\.?\s*', '', name2)
        
        return SequenceMatcher(None, name1, name2).ratio()
    
    def _generate_content_fingerprint(self, text: str) -> str:
        """Generate a content fingerprint for fallback matching"""
        # Take first 500 chars, normalize, and hash
        normalized_text = re.sub(r'\s+', ' ', text[:500]).strip().lower()
        return hashlib.md5(normalized_text.encode()).hexdigest()[:16]
    
    def _fetch_edify_metadata(self) -> Dict:
        """Fetch metadata from Edify API with caching"""
        try:
            # Check cache freshness (refresh every hour)
            if (self.last_cache_update and 
                (datetime.now() - self.last_cache_update).seconds < 3600 and 
                self.edify_metadata_cache):
                logger.info("Using cached Edify metadata")
                return self.edify_metadata_cache
            
            logger.info("Fetching fresh metadata from Edify API...")
            response = requests.get(self.edify_api_url, headers=self.edify_headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if not data.get('success', False):
                logger.error(f"Edify API returned error: {data}")
                return {}
            
            # Process and cache the metadata
            processed_metadata = self._process_edify_metadata(data.get('sops', []))
            self.edify_metadata_cache = processed_metadata
            self.last_cache_update = datetime.now()
            
            logger.info(f"Successfully cached {len(processed_metadata)} Edify documents")
            return processed_metadata
            
        except Exception as e:
            logger.error(f"Error fetching Edify metadata: {e}")
            return self.edify_metadata_cache or {}
    
    def _process_edify_metadata(self, sops: List[Dict]) -> Dict:
        """Process raw Edify metadata into usable format"""
        processed = {}
        
        for sop in sops:
            doc_id = sop.get('_id')
            if not doc_id:
                continue
            
            # Extract metadata
            sop_title = sop.get('sopTitle', 'Unknown Document')
            department_name = sop.get('departmentName', 'Unknown Department')
            school_types = sop.get('schoolTypeNames', [])
            
            # Extract filename from sopFile
            filename = 'Unknown Filename'
            if sop.get('sopFile') and sop['sopFile'].get('name'):
                filename = sop['sopFile']['name']
            
            processed[doc_id] = {
                'title': sop_title,
                'filename': filename,
                'department': department_name,
                'school_types': school_types,
                'display_name': filename if filename != 'Unknown Filename' else sop_title,
                'download_url': sop.get('sopFile', {}).get('url', ''),
                'metadata_source': 'edify_api'
            }
        
        return processed
    
    def _build_filename_similarity_index(self, edify_metadata: Dict) -> Dict:
        """Build filename similarity index for fallback matching"""
        if self.filename_similarity_cache:
            return self.filename_similarity_cache
        
        similarity_index = {}
        
        for doc_id, metadata in edify_metadata.items():
            edify_filename = metadata['filename']
            if edify_filename and edify_filename != 'Unknown Filename':
                similarity_index[doc_id] = {
                    'filename': edify_filename,
                    'normalized_filename': self._normalize_filename_for_matching(edify_filename),
                    'title': metadata['title']
                }
        
        self.filename_similarity_cache = similarity_index
        return similarity_index
    
    def _normalize_filename_for_matching(self, filename: str) -> str:
        """Normalize filename for better matching"""
        # Remove file extension
        name = filename.replace('.pdf', '').replace('.PDF', '')
        # Remove numbers and dots at the beginning
        name = re.sub(r'^\d+\.?\s*', '', name)
        # Replace special characters with spaces
        name = re.sub(r'[_\-&]+', ' ', name)
        # Normalize whitespace
        name = re.sub(r'\s+', ' ', name).strip().lower()
        return name
    
    def match_document_by_strategies(self, vector_uuid: str, chunk_text: str = "", vector_metadata: Dict = None) -> Tuple[Optional[str], Dict, float]:
        """
        Multi-strategy document matching:
        1. Direct UUID match
        2. Filename similarity matching
        3. Content fingerprint matching (future implementation)
        
        Returns: (matched_doc_id, metadata, confidence_score)
        """
        edify_metadata = self._fetch_edify_metadata()
        
        if not edify_metadata:
            return None, {}, 0.0
        
        # Strategy 1: Direct UUID match
        if vector_uuid in edify_metadata:
            logger.info(f"Direct UUID match found for {vector_uuid}")
            return vector_uuid, edify_metadata[vector_uuid], 1.0
        
        # Strategy 2: Filename similarity matching
        if vector_metadata and vector_metadata.get('filename'):
            vector_filename = vector_metadata['filename']
            best_match_id, best_score = self._find_best_filename_match(vector_filename, edify_metadata)
            
            if best_match_id and best_score > 0.7:  # High confidence threshold
                logger.info(f"Filename similarity match found: {vector_filename} -> {edify_metadata[best_match_id]['filename']} (score: {best_score:.3f})")
                return best_match_id, edify_metadata[best_match_id], best_score
        
        # Strategy 3: Content fingerprinting (placeholder for future implementation)
        # if chunk_text:
        #     content_fingerprint = self._generate_content_fingerprint(chunk_text)
        #     # Would compare against precomputed content fingerprints
        
        # No match found
        return None, {}, 0.0
    
    def _find_best_filename_match(self, vector_filename: str, edify_metadata: Dict) -> Tuple[Optional[str], float]:
        """Find best filename match using similarity scoring without UUID processing"""
        best_match_id = None
        best_score = 0.0
        
        # Extract base filename for comparison
        base_filename = vector_filename.replace('.pdf', '').replace('.PDF', '')
        # Remove path if present
        if '/' in base_filename:
            base_filename = base_filename.split('/')[-1]
        
        for doc_id, metadata in edify_metadata.items():
            edify_filename = metadata['filename']
            if edify_filename == 'Unknown Filename':
                continue
            
            # Calculate similarity
            similarity = self._calculate_filename_similarity(base_filename, edify_filename)
            
            if similarity > best_score:
                best_score = similarity
                best_match_id = doc_id
        
        return best_match_id, best_score
    
    def enhance_chunk_metadata(self, chunk_metadata: Dict) -> Dict:
        """Enhanced metadata enhancement using only metadata, no UUID processing"""
        enhanced = chunk_metadata.copy()
        
        # Use filename-based matching without UUID extraction
        filename = chunk_metadata.get('filename', '')
        
        if filename:
            # Try to match with Edify metadata using filename similarity
            edify_metadata = self._fetch_edify_metadata()
            if edify_metadata:
                best_match_id, best_score = self._find_best_filename_match(filename, edify_metadata)
                
                if best_match_id and best_score > 0.5:  # Minimum confidence threshold
                    matched_metadata = edify_metadata[best_match_id]
                    # Enhance with matched metadata
                    enhanced.update({
                        'display_name': matched_metadata['display_name'],
                        'original_filename': matched_metadata['filename'],
                        'document_title': matched_metadata['title'],
                        'department': matched_metadata['department'],
                        'school_types': matched_metadata['school_types'],
                        'download_url': matched_metadata['download_url'],
                        'metadata_source': 'edify_api',
                        'match_confidence': best_score,
                        'match_strategy': 'filename_similarity',
                        'edify_doc_id': best_match_id
                    })
                    logger.info(f"Enhanced metadata for {filename} with confidence {best_score:.3f}")
                    return enhanced
        
        # Fallback to intelligent display name using only metadata
        fallback_name = self._generate_fallback_display_name(chunk_metadata)
        enhanced.update({
            'display_name': fallback_name,
            'original_filename': chunk_metadata.get('filename', 'Unknown'),
            'document_title': fallback_name,
            'metadata_source': 'fallback',
            'match_confidence': 0.0,
            'match_strategy': 'fallback'
        })
        logger.info(f"Using fallback display name for {filename}: {fallback_name}")
        
        return enhanced
    
    def _generate_fallback_display_name(self, chunk_metadata: Dict) -> str:
        """Generate intelligent fallback display name using only metadata"""
        # Try to use filename if available
        if 'filename' in chunk_metadata:
            filename = chunk_metadata['filename']
            
            # Extract meaningful name from path structure
            if '/' in filename:
                path_parts = filename.split('/')
                # Determine document type from path
                if 'k12' in filename.lower():
                    return "K12 Document"
                elif 'preschool' in filename.lower():
                    return "Preschool Document"
                elif 'edifyho' in filename.lower() or 'administrative' in filename.lower():
                    return "Administrative Document"
                else:
                    return "Educational Document"
            else:
                # Use the actual filename, cleaned up
                display_name = filename.replace('.pdf', '').replace('_', ' ').replace('-', ' ').title()
                # If filename is too short or seems like random chars, use generic name
                if len(display_name) < 3 or display_name.replace(' ', '').isalnum() and len(display_name) < 10:
                    return "Educational Document"
                return display_name
        
        # Fallback to generic name
        return "Educational Document"
    
    def get_document_download_info(self, chunk_metadata: Dict) -> Dict:
        """Get download information for a document"""
        enhanced_metadata = self.enhance_chunk_metadata(chunk_metadata)
        
        return {
            'display_name': enhanced_metadata.get('display_name', 'Unknown Document'),
            'download_url': enhanced_metadata.get('download_url', ''),
            'filename': enhanced_metadata.get('original_filename', 'document.pdf'),
            'can_download': bool(enhanced_metadata.get('download_url')),
            'metadata_source': enhanced_metadata.get('metadata_source', 'unknown')
        }
    
    def get_statistics(self) -> Dict:
        """Get service statistics"""
        edify_metadata = self._fetch_edify_metadata()
        
        return {
            'edify_documents_cached': len(edify_metadata),
            'last_cache_update': self.last_cache_update.isoformat() if self.last_cache_update else None,
            'cache_size_mb': len(str(self.edify_metadata_cache)) / (1024 * 1024),
            'similarity_index_size': len(self.filename_similarity_cache)
        }

# Global instance
improved_metadata_service = ImprovedMetadataService()

def enhance_chunk_metadata(chunk_metadata: Dict) -> Dict:
    """Global function for easy import"""
    return improved_metadata_service.enhance_chunk_metadata(chunk_metadata)

def get_document_download_info(chunk_metadata: Dict) -> Dict:
    """Global function for download info"""
    return improved_metadata_service.get_document_download_info(chunk_metadata)

if __name__ == "__main__":
    # Test the improved service
    service = ImprovedMetadataService()
    
    # Test with sample metadata
    sample_metadata = {
        'filename': 'edipedia/2025-2026/k12/3c6174ed-e425-47b6-9e12-b0a93b6ee8ec.pdf',
        'chunk_id': 'edipedia/2025-2026/k12/3c6174ed-e425-47b6-9e12-b0a93b6ee8ec.pdf_001'
    }
    
    enhanced = service.enhance_chunk_metadata(sample_metadata)
    print(f"Enhanced metadata: {json.dumps(enhanced, indent=2)}")
    
    # Print statistics
    stats = service.get_statistics()
    print(f"Service statistics: {json.dumps(stats, indent=2)}")
