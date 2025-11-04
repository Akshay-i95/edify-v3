"""
Enhanced PDF Processor - Phase 2 Implementation
Handles OCR, complex layouts, image extraction, and file validation

This module provides:
- OCR integration for scanned PDFs (Tesseract)
- Advanced PDF parsing for complex layouts
- Image-to-text extraction for diagram-heavy documents  
- File validation & repair mechanisms
- Chunk-level processing for AI chatbot foundation
"""

import io
import logging
import time
import os
import tempfile
from typing import List, Dict, Tuple, Optional, Any
from pathlib import Path
import numpy as np
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

# PDF Processing
import PyPDF2
import pdfplumber
import fitz  # PyMuPDF for advanced features

# OCR and Image Processing
try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

# File validation and repair
try:
    import pikepdf
    PIKEPDF_AVAILABLE = True
except ImportError:
    PIKEPDF_AVAILABLE = False

# Azure Blob Storage
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import AzureError

# Text Processing
import tiktoken
import re

class EnhancedPDFProcessor:
    def __init__(self, config: Dict):
        """Initialize the enhanced PDF processor with OCR and validation capabilities"""
        try:
            self.config = config
            
            # Configuration parameters
            self.max_workers = max(1, min(int(config.get('max_workers', 4)), 8))  # Reduced for OCR
            self.chunk_size = max(100, int(config.get('chunk_size', 1000)))
            self.chunk_overlap = max(0, min(int(config.get('chunk_overlap', 200)), self.chunk_size // 2))
            self.batch_size = max(1, int(config.get('batch_size', 20)))  # Reduced for OCR processing
            self.max_memory_mb = max(512, int(config.get('max_memory_mb', 2048)))
            self.min_chunk_length = max(50, int(config.get('min_chunk_length', 100)))
            self.max_chunk_length = max(self.chunk_size, int(config.get('max_chunk_length', 2000)))
            
            # OCR Configuration
            self.enable_ocr = config.get('enable_ocr', True) and OCR_AVAILABLE
            self.ocr_language = config.get('ocr_language', 'eng')
            self.ocr_dpi = int(config.get('ocr_dpi', 300))
            self.image_to_text = config.get('image_to_text', True)
            
            # File validation
            self.enable_repair = config.get('enable_repair', True) and PIKEPDF_AVAILABLE
            self.max_file_size_mb = int(config.get('max_file_size_mb', 100))
            
            # Setup logging
            self.logger = logging.getLogger(__name__)
            
            # Initialize tokenizer
            try:
                self.tokenizer = tiktoken.get_encoding("cl100k_base")
            except Exception as e:
                self.logger.warning(f"⚠️ Failed to load tiktoken: {str(e)}")
                self.tokenizer = None
            
            # Statistics tracking
            self.stats = {
                'total_files': 0,
                'successful_extractions': 0,
                'ocr_extractions': 0,
                'repair_attempts': 0,
                'failed_files': 0,
                'chunks_created': 0
            }
            
            self._validate_dependencies()
            self.logger.info(f"✅ Enhanced PDF Processor initialized with OCR: {self.enable_ocr}")
            
        except Exception as e:
            raise ValueError(f"Failed to initialize EnhancedPDFProcessor: {str(e)}")
    
    def _validate_dependencies(self):
        """Validate OCR and other dependencies"""
        if self.enable_ocr and not OCR_AVAILABLE:
            self.logger.warning("⚠️ OCR requested but dependencies not available. Install: pip install pytesseract pillow")
            self.enable_ocr = False
        
        if self.enable_ocr:
            try:
                # Test Tesseract installation
                version = pytesseract.get_tesseract_version()
                self.logger.info(f"✅ Tesseract OCR available: {version}")
            except Exception as e:
                self.logger.warning(f"⚠️ Tesseract not properly installed: {str(e)}")
                self.enable_ocr = False
        
        if self.enable_repair and not PIKEPDF_AVAILABLE:
            self.logger.warning("⚠️ PDF repair requested but pikepdf not available. Install: pip install pikepdf")
            self.enable_repair = False
    
    def validate_and_repair_pdf(self, pdf_stream: io.BytesIO, blob_name: str) -> Tuple[io.BytesIO, bool]:
        """Validate and attempt to repair corrupted PDF files"""
        repaired = False
        
        try:
            # First, try to read with PyPDF2 for basic validation
            pdf_stream.seek(0)
            reader = PyPDF2.PdfReader(pdf_stream)
            
            # Check if we can access pages
            num_pages = len(reader.pages)
            if num_pages == 0:
                raise Exception("PDF has no pages")
            
            # Try to read first page to validate - but handle warnings
            first_page = reader.pages[0]
            
            # Suppress common PDF warnings that don't affect processing
            import warnings
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=UserWarning)
                warnings.filterwarnings("ignore", message=".*Cannot set gray.*")
                warnings.filterwarnings("ignore", message=".*invalid float value.*")
                _ = first_page.extract_text()
            
            self.logger.debug(f"✅ PDF validation passed for {blob_name} ({num_pages} pages)")
            pdf_stream.seek(0)
            return pdf_stream, repaired
            
        except Exception as e:
            self.logger.warning(f"⚠️ PDF validation failed for {blob_name}: {str(e)}")
            
            if self.enable_repair:
                try:
                    self.stats['repair_attempts'] += 1
                    self.logger.info(f"🔧 Attempting to repair {blob_name}")
                    
                    # Save to temporary file for pikepdf
                    pdf_stream.seek(0)
                    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                        temp_file.write(pdf_stream.getvalue())
                        temp_path = temp_file.name
                    
                    try:
                        # Use pikepdf to repair
                        with pikepdf.open(temp_path, allow_overwriting_input=True) as pdf:
                            repaired_stream = io.BytesIO()
                            pdf.save(repaired_stream)
                            repaired_stream.seek(0)
                            repaired = True
                            
                            self.logger.info(f"✅ Successfully repaired {blob_name}")
                            return repaired_stream, repaired
                    finally:
                        # Clean up temp file
                        os.unlink(temp_path)
                        
                except Exception as repair_error:
                    self.logger.error(f"❌ Failed to repair {blob_name}: {str(repair_error)}")
            
            pdf_stream.seek(0)
            return pdf_stream, repaired
    
    def extract_text_with_ocr(self, pdf_stream: io.BytesIO, blob_name: str) -> Tuple[str, Dict]:
        """Extract text using multiple methods including OCR for scanned documents"""
        text_content = ""
        metadata = {
            'filename': blob_name,
            'pages': 0,
            'extraction_method': 'none',
            'processing_time': 0,
            'ocr_used': False,
            'images_processed': 0,
            'file_size_mb': 0
        }
        
        start_time = time.time()
        
        try:
            # First, validate and potentially repair the PDF
            pdf_stream, was_repaired = self.validate_and_repair_pdf(pdf_stream, blob_name)
            if was_repaired:
                metadata['repaired'] = True
            
            # Method 1: Try standard text extraction first
            text_content, basic_metadata = self._extract_standard_text(pdf_stream, blob_name)
            metadata.update(basic_metadata)
            
            # If standard extraction yields minimal text, try OCR
            if (len(text_content.strip()) < 100 and self.enable_ocr):
                self.logger.info(f"🔍 Standard extraction yielded minimal text for {blob_name}, trying OCR")
                ocr_text, ocr_metadata = self._extract_with_ocr(pdf_stream, blob_name)
                
                if len(ocr_text.strip()) > len(text_content.strip()):
                    text_content = ocr_text
                    metadata.update(ocr_metadata)
                    metadata['ocr_used'] = True
                    self.stats['ocr_extractions'] += 1
            
            # Extract images and convert to text if enabled
            if self.image_to_text and self.enable_ocr:
                image_text, image_count = self._extract_images_to_text(pdf_stream, blob_name)
                if image_text.strip():
                    text_content += "\n\n--- IMAGE CONTENT ---\n" + image_text
                    metadata['images_processed'] = image_count
            
        except Exception as e:
            self.logger.error(f"❌ Complete extraction failed for {blob_name}: {str(e)}")
        
        # Clean and normalize text
        if text_content:
            text_content = self.clean_text(text_content)
        
        metadata['processing_time'] = time.time() - start_time
        metadata['character_count'] = len(text_content)
        
        return text_content, metadata
    
    def _extract_standard_text(self, pdf_stream: io.BytesIO, blob_name: str) -> Tuple[str, Dict]:
        """Extract text using standard methods (pdfplumber, PyPDF2)"""
        text_content = ""
        metadata = {'extraction_method': 'none', 'pages': 0}
        
        # Method 1: pdfplumber (best for structured text) with warning suppression
        try:
            pdf_stream.seek(0)
            
            # Suppress common pdfminer warnings that don't affect extraction
            import warnings
            import logging
            
            # Temporarily reduce pdfminer logging level to avoid spam
            pdfminer_logger = logging.getLogger('pdfminer')
            original_level = pdfminer_logger.level
            pdfminer_logger.setLevel(logging.ERROR)
            
            try:
                with pdfplumber.open(pdf_stream) as pdf:
                    pages_text = []
                    for page_num, page in enumerate(pdf.pages):
                        try:
                            with warnings.catch_warnings():
                                warnings.filterwarnings("ignore")
                                page_text = page.extract_text()
                                if page_text and page_text.strip():
                                    pages_text.append(page_text)
                        except Exception as e:
                            self.logger.debug(f"⚠️ Page {page_num} extraction issue in {blob_name}: {str(e)}")
                    
                    if pages_text:
                        text_content = "\n\n".join(pages_text)
                        metadata['pages'] = len(pdf.pages)
                        metadata['extraction_method'] = 'pdfplumber'
                        return text_content, metadata
            finally:
                # Restore original logging level
                pdfminer_logger.setLevel(original_level)
        
        except Exception as e:
            self.logger.warning(f"⚠️ pdfplumber failed for {blob_name}: {str(e)}")
        
        # Method 2: PyMuPDF (better for complex layouts)
        try:
            pdf_stream.seek(0)
            pdf_doc = fitz.open(stream=pdf_stream.getvalue(), filetype="pdf")
            pages_text = []
            
            for page_num in range(pdf_doc.page_count):
                try:
                    page = pdf_doc[page_num]
                    page_text = page.get_text()
                    if page_text and page_text.strip():
                        pages_text.append(page_text)
                except Exception as e:
                    self.logger.warning(f"⚠️ Error extracting page {page_num} with PyMuPDF: {str(e)}")
            
            pdf_doc.close()
            
            if pages_text:
                text_content = "\n\n".join(pages_text)
                metadata['pages'] = pdf_doc.page_count
                metadata['extraction_method'] = 'PyMuPDF'
                return text_content, metadata
                
        except Exception as e:
            self.logger.warning(f"⚠️ PyMuPDF failed for {blob_name}: {str(e)}")
        
        # Method 3: PyPDF2 (fallback)
        try:
            pdf_stream.seek(0)
            pdf_reader = PyPDF2.PdfReader(pdf_stream)
            pages_text = []
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text and page_text.strip():
                        pages_text.append(page_text)
                except Exception as e:
                    self.logger.warning(f"⚠️ Error extracting page {page_num} with PyPDF2: {str(e)}")
            
            if pages_text:
                text_content = "\n\n".join(pages_text)
                metadata['pages'] = len(pdf_reader.pages)
                metadata['extraction_method'] = 'PyPDF2'
                
        except Exception as e:
            self.logger.warning(f"⚠️ PyPDF2 failed for {blob_name}: {str(e)}")
        
        return text_content, metadata
    
    def _extract_with_ocr(self, pdf_stream: io.BytesIO, blob_name: str) -> Tuple[str, Dict]:
        """Extract text using OCR for scanned documents"""
        if not self.enable_ocr:
            return "", {}
        
        text_content = ""
        metadata = {'extraction_method': 'OCR', 'pages': 0}
        
        try:
            pdf_stream.seek(0)
            pdf_doc = fitz.open(stream=pdf_stream.getvalue(), filetype="pdf")
            pages_text = []
            
            self.logger.info(f"🔍 Starting OCR processing for {blob_name} ({pdf_doc.page_count} pages)")
            
            for page_num in range(min(pdf_doc.page_count, 50)):  # Limit OCR to 50 pages
                try:
                    page = pdf_doc[page_num]
                    
                    # Convert page to image
                    pix = page.get_pixmap(matrix=fitz.Matrix(self.ocr_dpi/72, self.ocr_dpi/72))
                    img_data = pix.tobytes("png")
                    image = Image.open(io.BytesIO(img_data))
                    
                    # Apply OCR
                    page_text = pytesseract.image_to_string(
                        image, 
                        lang=self.ocr_language,
                        config='--psm 6'  # Assume uniform block of text
                    )
                    
                    if page_text and page_text.strip():
                        pages_text.append(page_text)
                    
                    # Memory cleanup
                    image.close()
                    pix = None
                    
                except Exception as e:
                    self.logger.warning(f"⚠️ OCR failed for page {page_num} in {blob_name}: {str(e)}")
                    continue
            
            pdf_doc.close()
            
            if pages_text:
                text_content = "\n\n".join(pages_text)
                metadata['pages'] = len(pages_text)
                
                self.logger.info(f"✅ OCR extracted {len(text_content)} characters from {blob_name}")
            
        except Exception as e:
            self.logger.error(f"❌ OCR processing failed for {blob_name}: {str(e)}")
        
        return text_content, metadata
    
    def _extract_images_to_text(self, pdf_stream: io.BytesIO, blob_name: str) -> Tuple[str, int]:
        """Extract images from PDF and convert to text using OCR"""
        if not self.enable_ocr:
            return "", 0
        
        image_text = ""
        image_count = 0
        
        try:
            pdf_stream.seek(0)
            pdf_doc = fitz.open(stream=pdf_stream.getvalue(), filetype="pdf")
            
            for page_num in range(min(pdf_doc.page_count, 20)):  # Limit to 20 pages for images
                page = pdf_doc[page_num]
                image_list = page.get_images()
                
                for img_index, img in enumerate(image_list):
                    try:
                        # Extract image
                        xref = img[0]
                        base_image = pdf_doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        
                        # Convert to PIL Image
                        image = Image.open(io.BytesIO(image_bytes))
                        
                        # Skip very small images (likely decorative)
                        if image.width < 100 or image.height < 100:
                            continue
                        
                        # Apply OCR to image
                        img_text = pytesseract.image_to_string(
                            image,
                            lang=self.ocr_language,
                            config='--psm 6'
                        )
                        
                        if img_text and len(img_text.strip()) > 20:  # Only meaningful text
                            image_text += f"\n--- Image {image_count + 1} (Page {page_num + 1}) ---\n"
                            image_text += img_text.strip() + "\n"
                            image_count += 1
                        
                        image.close()
                        
                    except Exception as e:
                        self.logger.warning(f"⚠️ Failed to process image {img_index} on page {page_num}: {str(e)}")
                        continue
            
            pdf_doc.close()
            
        except Exception as e:
            self.logger.error(f"❌ Image extraction failed for {blob_name}: {str(e)}")
        
        return image_text, image_count
    
    def clean_text(self, text: str) -> str:
        """Enhanced text cleaning for better chunking"""
        if not text:
            return ""
        
        # Remove excessive whitespace while preserving paragraph breaks
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Multiple line breaks to double
        text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces/tabs to single space
        
        # Remove page numbers and headers/footers (common patterns)
        text = re.sub(r'\n\d+\s*\n', '\n', text)  # Standalone page numbers
        text = re.sub(r'\n(?:Page \d+|P\.\d+)\n', '\n', text)  # Page markers
        
        # Fix common OCR errors
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)  # Missing spaces between words
        text = re.sub(r'\b(\w)\s+(\w)\b', r'\1\2', text)  # Extra spaces in words (OCR artifact)
        
        # Remove very short lines (likely formatting artifacts)
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if len(line) > 3:  # Keep lines with more than 3 characters
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines).strip()
    
    def create_smart_chunks(self, text: str, metadata: Dict) -> List[Dict]:
        """Create intelligent chunks optimized for AI retrieval (Phase 3)"""
        if not text or len(text.strip()) < self.min_chunk_length:
            return []
        
        chunks = []
        text = text.strip()
        
        try:
            # Split by sections first (headers, major breaks)
            sections = self._split_by_sections(text)
            
            for section_idx, section in enumerate(sections):
                if len(section.strip()) < self.min_chunk_length:
                    continue
                
                # Split section into semantic chunks
                section_chunks = self._create_semantic_chunks(section, metadata, section_idx)
                chunks.extend(section_chunks)
            
            # Add chunk relationships and context
            for i, chunk in enumerate(chunks):
                chunk['chunk_id'] = f"{metadata['filename']}_{i:03d}"
                chunk['total_chunks'] = len(chunks)
                chunk['chunk_index'] = i
                
                # Add context from neighboring chunks
                if i > 0:
                    chunk['previous_chunk_preview'] = chunks[i-1]['text'][:100] + "..."
                if i < len(chunks) - 1:
                    chunk['next_chunk_preview'] = chunks[i+1]['text'][:100] + "..."
            
            self.stats['chunks_created'] += len(chunks)
            return chunks
            
        except Exception as e:
            self.logger.error(f"❌ Error creating chunks: {str(e)}")
            return []
    
    def _split_by_sections(self, text: str) -> List[str]:
        """Split text into logical sections based on headers and content breaks"""
        # Look for section headers (various patterns)
        section_patterns = [
            r'\n\s*(?:[IVX]+\.|\d+\.)\s+[A-Z][^\n]{10,}\n',  # Numbered/Roman sections
            r'\n\s*[A-Z][A-Z\s]{5,}\n',  # ALL CAPS headers
            r'\n\s*Chapter\s+\d+[^\n]*\n',  # Chapter headers
            r'\n\s*Section\s+\d+[^\n]*\n',  # Section headers
        ]
        
        # Find section breaks
        section_breaks = [0]
        for pattern in section_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                section_breaks.append(match.start())
        
        # Add paragraph breaks as potential section breaks
        paragraph_breaks = [m.start() for m in re.finditer(r'\n\s*\n\s*[A-Z]', text)]
        section_breaks.extend(paragraph_breaks)
        
        # Remove duplicates and sort
        section_breaks = sorted(list(set(section_breaks)))
        section_breaks.append(len(text))
        
        # Create sections
        sections = []
        for i in range(len(section_breaks) - 1):
            start = section_breaks[i]
            end = section_breaks[i + 1]
            section = text[start:end].strip()
            if len(section) > 50:  # Only meaningful sections
                sections.append(section)
        
        return sections if sections else [text]
    
    def _create_semantic_chunks(self, section: str, metadata: Dict, section_idx: int) -> List[Dict]:
        """Create semantically meaningful chunks from a section"""
        chunks = []
        
        # Split by paragraphs
        paragraphs = [p.strip() for p in section.split('\n\n') if p.strip()]
        
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
                    chunk_data = self._create_chunk_with_metadata(
                        current_chunk, metadata, len(chunks), section_idx
                    )
                    chunks.append(chunk_data)
                
                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk)
                current_chunk = overlap_text + "\n\n" + para if overlap_text else para
                current_tokens = len(self.tokenizer.encode(current_chunk)) if self.tokenizer else len(current_chunk) // 4
            else:
                current_chunk += "\n\n" + para if current_chunk else para
                current_tokens += para_tokens
        
        # Add final chunk
        if current_chunk and len(current_chunk) >= self.min_chunk_length:
            chunk_data = self._create_chunk_with_metadata(
                current_chunk, metadata, len(chunks), section_idx
            )
            chunks.append(chunk_data)
        
        return chunks
    
    def _get_overlap_text(self, text: str) -> str:
        """Get overlap text from the end of current chunk"""
        if len(text) <= self.chunk_overlap:
            return text
        
        # Try to break at sentence boundary
        overlap_text = text[-self.chunk_overlap:]
        sentence_break = overlap_text.find('. ')
        if sentence_break > 0:
            return overlap_text[sentence_break + 2:]
        
        return overlap_text
    
    def _create_chunk_with_metadata(self, chunk_text: str, file_metadata: Dict, chunk_index: int, section_index: int) -> Dict:
        """Create comprehensive metadata for a chunk (Phase 3 optimization)"""
        # Extract key information for better retrieval
        chunk_preview = chunk_text[:200] + "..." if len(chunk_text) > 200 else chunk_text
        
        # Identify content type
        content_type = "general"
        if re.search(r'\b(?:table|figure|chart|graph)\b', chunk_text, re.IGNORECASE):
            content_type = "data_visualization"
        elif re.search(r'\b(?:definition|concept|theory)\b', chunk_text, re.IGNORECASE):
            content_type = "conceptual"
        elif re.search(r'\b(?:step|process|procedure|method)\b', chunk_text, re.IGNORECASE):
            content_type = "procedural"
        
        return {
            # Core content
            'text': chunk_text,
            'preview': chunk_preview,
            
            # Identification
            'chunk_id': f"{file_metadata['filename']}_{chunk_index:03d}",
            'chunk_index': chunk_index,
            'section_index': section_index,
            
            # Source metadata
            'filename': file_metadata['filename'],
            'file_pages': file_metadata.get('pages', 0),
            'extraction_method': file_metadata.get('extraction_method', 'unknown'),
            'ocr_used': file_metadata.get('ocr_used', False),
            'images_processed': file_metadata.get('images_processed', 0),
            
            # Content metadata
            'content_type': content_type,
            'chunk_length': len(chunk_text),
            'chunk_tokens': len(self.tokenizer.encode(chunk_text)) if self.tokenizer else len(chunk_text) // 4,
            
            # Processing metadata
            'processing_time': file_metadata.get('processing_time', 0),
            'created_at': time.time()
        }
    
    def process_single_pdf_enhanced(self, container_client, blob_name: str) -> List[Dict]:
        """Process a single PDF with enhanced capabilities"""
        try:
            self.stats['total_files'] += 1
            
            # Stream PDF from blob
            pdf_stream, blob_properties = self.stream_pdf_from_blob(container_client, blob_name)
            if not pdf_stream:
                self.stats['failed_files'] += 1
                return []
            
            # Enhanced text extraction with OCR and validation
            text_content, metadata = self.extract_text_with_ocr(pdf_stream, blob_name)
            if not text_content or len(text_content.strip()) < 50:
                self.logger.warning(f"⚠️ Minimal text extracted from {blob_name}")
                self.stats['failed_files'] += 1
                return []
            
            # Add blob properties to metadata
            metadata['file_size_mb'] = blob_properties.size / (1024 * 1024)
            metadata['last_modified'] = blob_properties.last_modified
            
            # Create smart chunks optimized for AI retrieval
            chunks = self.create_smart_chunks(text_content, metadata)
            
            if chunks:
                self.stats['successful_extractions'] += 1
                self.logger.info(f"✅ Enhanced processing of {blob_name}: {len(chunks)} chunks, "
                               f"{metadata['pages']} pages, OCR: {metadata.get('ocr_used', False)}")
            else:
                self.stats['failed_files'] += 1
            
            return chunks
            
        except Exception as e:
            self.logger.error(f"❌ Enhanced processing failed for {blob_name}: {str(e)}")
            self.stats['failed_files'] += 1
            return []
    
    def stream_pdf_from_blob(self, container_client, blob_name: str) -> Tuple[Optional[io.BytesIO], Optional[Dict]]:
        """Stream PDF content from Azure Blob Storage (enhanced with better error handling)"""
        if not blob_name or not blob_name.lower().endswith('.pdf'):
            self.logger.error(f"❌ Invalid PDF file name: {blob_name}")
            return None, None
            
        try:
            blob_client = container_client.get_blob_client(blob_name)
            
            # Get blob properties with retry
            properties = None
            for attempt in range(3):
                try:
                    properties = blob_client.get_blob_properties()
                    break
                except Exception as e:
                    if attempt == 2:
                        self.logger.error(f"❌ Failed to get properties for {blob_name}: {str(e)}")
                        return None, None
                    time.sleep(1)
            
            file_size_mb = properties.size / (1024 * 1024)
            
            # Enhanced file size validation
            if properties.size == 0:
                self.logger.warning(f"⚠️ File {blob_name} is empty")
                return None, None
            
            if file_size_mb > self.max_file_size_mb:
                self.logger.warning(f"⚠️ File {blob_name} ({file_size_mb:.1f}MB) exceeds size limit")
                return None, None
            
            # Stream with enhanced error handling
            blob_data = blob_client.download_blob()
            pdf_stream = io.BytesIO()
            
            # Stream in chunks
            for chunk in blob_data.chunks():
                if chunk:
                    pdf_stream.write(chunk)
            
            pdf_stream.seek(0)
            
            # Verify PDF header
            header = pdf_stream.read(4)
            if header != b'%PDF':
                self.logger.error(f"❌ {blob_name} is not a valid PDF file")
                return None, None
            
            pdf_stream.seek(0)
            return pdf_stream, properties
            
        except Exception as e:
            self.logger.error(f"❌ Error streaming {blob_name}: {str(e)}")
            return None, None
    
    def process_pdf_batch_enhanced(self, container_client, pdf_files: List[str]) -> List[Dict]:
        """Process a batch of PDFs with enhanced capabilities"""
        all_chunks = []
        
        # Reduced workers for OCR processing
        max_workers = min(self.max_workers, 4)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {
                executor.submit(self.process_single_pdf_enhanced, container_client, pdf_file): pdf_file 
                for pdf_file in pdf_files
            }
            
            with tqdm(total=len(pdf_files), desc="Processing PDFs (Enhanced)") as pbar:
                for future in as_completed(future_to_file):
                    pdf_file = future_to_file[future]
                    try:
                        chunks = future.result()
                        all_chunks.extend(chunks)
                        pbar.set_postfix({
                            'chunks': len(all_chunks),
                            'success_rate': f"{(self.stats['successful_extractions']/max(1, self.stats['total_files']))*100:.1f}%"
                        })
                    except Exception as e:
                        self.logger.error(f"❌ Batch processing error for {pdf_file}: {str(e)}")
                        self.stats['failed_files'] += 1
                    finally:
                        pbar.update(1)
        
        return all_chunks
    
    def get_processing_stats(self) -> Dict:
        """Get detailed processing statistics"""
        total = max(1, self.stats['total_files'])
        return {
            'total_files_processed': self.stats['total_files'],
            'successful_extractions': self.stats['successful_extractions'],
            'failed_extractions': self.stats['failed_files'],
            'success_rate_percent': (self.stats['successful_extractions'] / total) * 100,
            'ocr_extractions': self.stats['ocr_extractions'],
            'repair_attempts': self.stats['repair_attempts'],
            'total_chunks_created': self.stats['chunks_created'],
            'average_chunks_per_file': self.stats['chunks_created'] / max(1, self.stats['successful_extractions'])
        }
