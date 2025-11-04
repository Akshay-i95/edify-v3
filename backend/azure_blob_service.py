"""
Azure Blob Storage Service for PDF Download Management
Provides secure download URLs for source PDFs with time-limited SAS tokens
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from urllib.parse import urljoin

try:
    from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False
    # Create dummy classes for type hints when Azure is not available
    class BlobServiceClient:
        pass
    class BlobSasPermissions:
        pass
    def generate_blob_sas(*args, **kwargs):
        return None

class AzureBlobDownloadService:
    """Service for generating secure download URLs for PDF files in Azure Blob Storage"""
    
    def __init__(self, config: Dict):
        """Initialize Azure Blob Storage service with configuration"""
        self.logger = logging.getLogger(__name__)
        
        if not AZURE_AVAILABLE:
            self.logger.error("ERROR: Azure Storage SDK not available. Install with: pip install azure-storage-blob")
            raise ImportError("Azure Storage SDK not installed")
        
        # Load Azure configuration
        self.connection_string = config.get('azure_connection_string', os.getenv('AZURE_STORAGE_CONNECTION_STRING'))
        self.account_name = config.get('azure_account_name', os.getenv('AZURE_STORAGE_ACCOUNT_NAME'))
        self.account_key = config.get('azure_account_key', os.getenv('AZURE_STORAGE_ACCOUNT_KEY'))
        self.container_name = config.get('azure_container_name', os.getenv('AZURE_STORAGE_CONTAINER_NAME'))
        self.folder_path = config.get('azure_folder_path', os.getenv('AZURE_BLOB_FOLDER_PATH', ''))
        
        # Validate configuration
        if not self.connection_string and not (self.account_name and self.account_key):
            raise ValueError("Azure connection string or account name/key required")
        
        if not self.container_name:
            raise ValueError("Azure container name required")
        
        # Initialize blob service client
        try:
            if self.connection_string:
                self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
            else:
                account_url = f"https://{self.account_name}.blob.core.windows.net"
                self.blob_service_client = BlobServiceClient(
                    account_url=account_url,
                    credential=self.account_key
                )
            
            # Test connection
            self._test_connection()
            
            self.logger.info("Azure Blob Storage service initialized successfully")
            
        except Exception as e:
            self.logger.error(f"ERROR: Failed to initialize Azure Blob Storage: {str(e)}")
            raise
    
    def _test_connection(self):
        """Test Azure Blob Storage connection"""
        try:
            # Try to get container properties
            container_client = self.blob_service_client.get_container_client(self.container_name)
            container_client.get_container_properties()
            self.logger.info(f"Successfully connected to container: {self.container_name}")
            self.logger.info(f"Using folder path: {self.folder_path}")
            return True
        except Exception as e:
            self.logger.warning(f"WARNING: Connection test failed: {str(e)}")
            # Don't raise here - connection might still work for other operations
            return False

    def generate_download_url(self, filename: str, expiry_hours: int = 1) -> Optional[str]:
        """
        Generate a secure download URL with SAS token for a PDF file
        
        Args:
            filename: Name of the PDF file in blob storage
            expiry_hours: Hours until the download URL expires (default: 1 hour)
            
        Returns:
            Secure download URL or None if file not found
        """
        try:
            self.logger.info(f"Generating download URL for: {filename}")
            
            # Find the correct blob path
            blob_name = self._find_blob_path(filename)
            
            if not blob_name:
                self.logger.warning(f"WARNING: Blob not found for filename: {filename}")
                return None
            
            # Generate SAS token
            sas_token = self._generate_sas_token(blob_name, expiry_hours)
            
            if not sas_token:
                self.logger.error(f"ERROR: Failed to generate SAS token for: {blob_name}")
                return None
            
            # Construct download URL
            blob_url = f"https://{self.account_name}.blob.core.windows.net/{self.container_name}/{blob_name}"
            download_url = f"{blob_url}?{sas_token}"
            
            self.logger.info(f"[SUCCESS] Generated download URL for: {filename} -> {blob_name} (expires in {expiry_hours}h)")
            
            return download_url
            
        except Exception as e:
            self.logger.error(f"ERROR: Failed to generate download URL for {filename}: {str(e)}")
            return None
    
    def _construct_blob_name(self, filename: str) -> str:
        """Construct full blob name with folder path"""
        # Check if filename already contains the folder path
        if self.folder_path and filename.startswith(self.folder_path):
            # Filename already includes the full path
            return filename
        
        # If filename already starts with the folder path without trailing slash
        folder_without_slash = self.folder_path.rstrip('/') if self.folder_path else ''
        if folder_without_slash and filename.startswith(folder_without_slash):
            return filename
        
        # Check if it's already a full path (contains forward slashes)
        if '/' in filename and not filename.startswith('./'):
            # This might already be a full blob path, try it as-is first
            return filename
        
        # Otherwise, construct the full path
        if self.folder_path:
            # Ensure folder path ends with /
            folder = self.folder_path.rstrip('/') + '/'
            return f"{folder}{filename}"
        
        return filename
    
    def _blob_exists(self, blob_name: str) -> bool:
        """Check if blob exists in container"""
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            blob_client.get_blob_properties()
            return True
        except Exception:
            return False
    
    def _find_blob_path(self, filename: str) -> Optional[str]:
        """Find the correct blob path for a filename by trying different variations"""
        try:
            # Log the filename and folder path for debugging
            self.logger.info(f"Finding blob path for filename: {filename}, folder path: {self.folder_path}")
            
            # Try different path variations
            possible_paths = [
                filename,  # As-is
                self._construct_blob_name(filename),  # With folder path
            ]
            
            # If filename contains path separators, try just the basename
            if '/' in filename:
                basename = filename.split('/')[-1]
                possible_paths.extend([
                    basename,
                    self._construct_blob_name(basename)
                ])
            
            # If filename has extension, try without extension
            base, ext = os.path.splitext(filename)
            if ext:
                possible_paths.extend([
                    base,
                    self._construct_blob_name(base)
                ])
            
            # If no extension, try with common extensions
            else:
                possible_paths.extend([
                    f"{filename}.pdf",
                    self._construct_blob_name(f"{filename}.pdf"),
                    f"{filename}.docx",
                    self._construct_blob_name(f"{filename}.docx")
                ])
            
            # Remove duplicates while preserving order
            seen = set()
            unique_paths = []
            for path in possible_paths:
                if path not in seen:
                    seen.add(path)
                    unique_paths.append(path)
            
            self.logger.info(f"Trying paths: {unique_paths}")
            
            # Try each path
            for path in unique_paths:
                if self._blob_exists(path):
                    self.logger.info(f"Found blob at path: {path}")
                    return path
            
            # Try listing blobs with a name containing the filename (fallback for partial match)
            try:
                container_client = self.blob_service_client.get_container_client(self.container_name)
                prefix = self.folder_path.rstrip('/') + '/' if self.folder_path else None
                
                blobs = list(container_client.list_blobs(name_starts_with=prefix))
                self.logger.info(f"Found {len(blobs)} blobs with prefix: {prefix}")
                
                # Try a fuzzy match on filename
                for blob in blobs:
                    if filename.lower() in blob.name.lower():
                        self.logger.info(f"Found fuzzy match: {blob.name}")
                        return blob.name
            except Exception as e:
                self.logger.warning(f"Fuzzy match search failed: {str(e)}")
            
            self.logger.warning(f"No matching blob found for {filename}")
            return None
        except Exception as e:
            self.logger.error(f"Error finding blob path: {str(e)}")
            return None
    
    def _generate_sas_token(self, blob_name: str, expiry_hours: int) -> Optional[str]:
        """Generate SAS token for blob download"""
        try:
            # Set permissions for download only
            permissions = BlobSasPermissions(read=True)
            
            # Set expiry time
            expiry_time = datetime.utcnow() + timedelta(hours=expiry_hours)
            
            # Generate SAS token
            sas_token = generate_blob_sas(
                account_name=self.account_name,
                container_name=self.container_name,
                blob_name=blob_name,
                account_key=self.account_key,
                permission=permissions,
                expiry=expiry_time
            )
            
            return sas_token
            
        except Exception as e:
            self.logger.error(f"ERROR: SAS token generation failed: {str(e)}")
            return None
    
    def get_blob_info(self, filename: str) -> Optional[Dict]:
        """Get blob information including size and last modified date"""
        try:
            # Find the correct blob path
            blob_name = self._find_blob_path(filename)
            
            if not blob_name:
                return {
                    'filename': filename,
                    'exists': False,
                    'error': 'File not found in storage'
                }
            
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            properties = blob_client.get_blob_properties()
            
            return {
                'filename': filename,
                'blob_name': blob_name,
                'size_bytes': properties.size,
                'size_mb': round(properties.size / (1024 * 1024), 2),
                'last_modified': properties.last_modified.isoformat() if properties.last_modified else None,
                'content_type': properties.content_settings.content_type if properties.content_settings else 'application/pdf',
                'exists': True
            }
            
        except Exception as e:
            self.logger.warning(f"WARNING: Failed to get blob info for {filename}: {str(e)}")
            return {
                'filename': filename,
                'exists': False,
                'error': str(e)
            }
    
    def list_available_pdfs(self) -> List[Dict]:
        """List all available PDF files in the container/folder"""
        try:
            container_client = self.blob_service_client.get_container_client(self.container_name)
            
            # Set prefix for folder if specified
            prefix = self.folder_path.rstrip('/') + '/' if self.folder_path else None
            
            pdf_files = []
            blobs = container_client.list_blobs(name_starts_with=prefix)
            
            for blob in blobs:
                if blob.name.lower().endswith('.pdf'):
                    # Extract filename from full blob path
                    filename = blob.name.split('/')[-1] if '/' in blob.name else blob.name
                    
                    pdf_files.append({
                        'filename': filename,
                        'blob_name': blob.name,
                        'size_mb': round(blob.size / (1024 * 1024), 2),
                        'last_modified': blob.last_modified.isoformat() if blob.last_modified else None
                    })
            
            self.logger.info(f"Found {len(pdf_files)} PDF files in Azure storage")
            return pdf_files
            
        except Exception as e:
            self.logger.error(f"ERROR: Failed to list PDF files: {str(e)}")
            return []
    
    def batch_generate_download_urls(self, filenames: List[str], expiry_hours: int = 1) -> Dict[str, Optional[str]]:
        """Generate download URLs for multiple files at once"""
        download_urls = {}
        
        for filename in filenames:
            download_urls[filename] = self.generate_download_url(filename, expiry_hours)
        
        successful = sum(1 for url in download_urls.values() if url is not None)
        self.logger.info(f"Generated {successful}/{len(filenames)} download URLs")
        
        return download_urls
    
    def get_blob_info(self, filename: str) -> Optional[Dict]:
        """Get blob information including size and last modified date"""
        try:
            # Find the correct blob path
            blob_name = self._find_blob_path(filename)
            
            if not blob_name:
                return {
                    'filename': filename,
                    'exists': False,
                    'error': 'File not found in storage'
                }
            
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            properties = blob_client.get_blob_properties()
            
            return {
                'filename': filename,
                'blob_name': blob_name,
                'size_bytes': properties.size,
                'size_mb': round(properties.size / (1024 * 1024), 2),
                'last_modified': properties.last_modified.isoformat() if properties.last_modified else None,
                'content_type': properties.content_settings.content_type if properties.content_settings else 'application/pdf',
                'exists': True
            }
            
        except Exception as e:
            self.logger.warning(f"WARNING: Failed to get blob info for {filename}: {str(e)}")
            return {
                'filename': filename,
                'exists': False,
                'error': str(e)
            }
    
    def list_available_pdfs(self) -> List[Dict]:
        """List all available PDF files in the container/folder"""
        try:
            container_client = self.blob_service_client.get_container_client(self.container_name)
            
            # Set prefix for folder if specified
            prefix = self.folder_path.rstrip('/') + '/' if self.folder_path else None
            
            pdf_files = []
            blobs = container_client.list_blobs(name_starts_with=prefix)
            
            for blob in blobs:
                if blob.name.lower().endswith('.pdf'):
                    # Extract filename from full blob path
                    filename = blob.name.split('/')[-1] if '/' in blob.name else blob.name
                    
                    pdf_files.append({
                        'filename': filename,
                        'blob_name': blob.name,
                        'size_mb': round(blob.size / (1024 * 1024), 2),
                        'last_modified': blob.last_modified.isoformat() if blob.last_modified else None
                    })
            
            self.logger.info(f"Found {len(pdf_files)} PDF files in Azure storage")
            return pdf_files
            
        except Exception as e:
            self.logger.error(f"ERROR: Failed to list PDF files: {str(e)}")
            return []
    
    def batch_generate_download_urls(self, filenames: List[str], expiry_hours: int = 1) -> Dict[str, Optional[str]]:
        """Generate download URLs for multiple files at once"""
        download_urls = {}
        
        for filename in filenames:
            download_urls[filename] = self.generate_download_url(filename, expiry_hours)
        
        successful = sum(1 for url in download_urls.values() if url is not None)
        self.logger.info(f"Generated {successful}/{len(filenames)} download URLs")
        
        return download_urls
    
    def get_download_stats(self) -> Dict:
        """Get service statistics"""
        try:
            # Check connection without calling list_containers with max_results
            # This works with the latest Azure SDK
            if self.connection_string:
                service_client = BlobServiceClient.from_connection_string(self.connection_string)
                # Just get the account name to verify connection
                _ = service_client.account_name
            else:
                # Use account name and key
                service_client = BlobServiceClient(
                    account_url=f"https://{self.account_name}.blob.core.windows.net",
                    credential=self.account_key
                )
                # Just get the account name to verify connection
                _ = service_client.account_name
                
            self.logger.info(f"Connection test successful: {service_client.account_name}")
            
            # Now list PDFs
            pdf_files = self.list_available_pdfs()
            total_size_mb = sum(pdf.get('size_mb', 0) for pdf in pdf_files)
            
            return {
                'total_pdf_files': len(pdf_files),
                'total_size_mb': round(total_size_mb, 2),
                'container_name': self.container_name,
                'folder_path': self.folder_path or 'root',
                'service_available': True
            }
        except Exception as e:
            return {
                'service_available': False,
                'error': str(e)
            }

# Factory function for easy initialization
def create_azure_download_service(config: Dict = None) -> Optional[AzureBlobDownloadService]:
    """
    Factory function to create Azure download service
    
    Args:
        config: Configuration dictionary (optional)
        
    Returns:
        AzureBlobDownloadService instance or None if Azure not available
    """
    if not AZURE_AVAILABLE:
        logging.getLogger(__name__).warning("WARNING: Azure Storage SDK not available")
        return None
    
    try:
        if config is None:
            config = {}
        
        return AzureBlobDownloadService(config)
    except Exception as e:
        logging.getLogger(__name__).error(f"ERROR: Failed to create Azure download service: {str(e)}")
        return None

