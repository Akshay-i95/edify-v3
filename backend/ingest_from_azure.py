"""
Azure to Pinecone Ingestion Script
Fetch files from Azure Blob Storage and push to Pinecone
"""

import os
import sys
import logging
from typing import List, Dict
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
import requests
import json

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AzureToPineconeIngestion:
    def __init__(self):
        """Initialize Azure and API connections"""
        self.connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        self.container_name = os.getenv('AZURE_STORAGE_CONTAINER_NAME', 'edifydocumentcontainer')
        self.api_base_url = os.getenv('API_BASE_URL', 'http://localhost:5000')
        
        if not self.connection_string:
            raise ValueError("AZURE_STORAGE_CONNECTION_STRING not found in .env")
        
        # Initialize Azure Blob Service Client
        self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
        self.container_client = self.blob_service_client.get_container_client(self.container_name)
        
        logger.info(f"✅ Connected to Azure container: {self.container_name}")
    
    def list_files(self, prefix: str = "", file_extension: str = ".pdf") -> List[str]:
        """
        List files from Azure Blob Storage
        
        Args:
            prefix: Folder prefix to filter (e.g., 'kb/12/')
            file_extension: File extension to filter (e.g., '.pdf', '.docx')
        
        Returns:
            List of blob names
        """
        logger.info(f"📂 Listing files from Azure (prefix: '{prefix}', extension: '{file_extension}')")
        
        try:
            blobs = self.container_client.list_blobs(name_starts_with=prefix)
            
            file_list = []
            for blob in blobs:
                if file_extension:
                    if blob.name.lower().endswith(file_extension.lower()):
                        file_list.append(blob.name)
                else:
                    file_list.append(blob.name)
            
            logger.info(f"✅ Found {len(file_list)} files matching criteria")
            return file_list
            
        except Exception as e:
            logger.error(f"❌ Error listing files: {str(e)}")
            return []
    
    def ingest_files_batch(self, file_names: List[str], batch_size: int = 10) -> Dict:
        """
        Ingest files to Pinecone via API in batches
        
        Args:
            file_names: List of blob names to ingest
            batch_size: Number of files to process per batch
        
        Returns:
            Summary of ingestion results
        """
        if not file_names:
            logger.warning("⚠️ No files to ingest")
            return {'success': False, 'error': 'No files provided'}
        
        logger.info(f"🚀 Starting ingestion of {len(file_names)} files")
        
        results = {
            'total_files': len(file_names),
            'successful': 0,
            'failed': 0,
            'total_chunks': 0,
            'details': []
        }
        
        # Process in batches
        for i in range(0, len(file_names), batch_size):
            batch = file_names[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(file_names) + batch_size - 1) // batch_size
            
            logger.info(f"📦 Processing batch {batch_num}/{total_batches} ({len(batch)} files)")
            
            try:
                # Call the ingestion API
                response = requests.post(
                    f"{self.api_base_url}/api/kb/ingest",
                    json={
                        'fileNames': batch,
                        'container': self.container_name
                    },
                    timeout=300  # 5 minutes timeout per batch
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get('success'):
                        # Process results
                        for result in data.get('results', []):
                            if result.get('success'):
                                results['successful'] += 1
                                results['total_chunks'] += result.get('chunks', 0)
                                logger.info(f"  ✅ {result['fileName']}: {result.get('chunks', 0)} chunks")
                            else:
                                results['failed'] += 1
                                logger.error(f"  ❌ {result['fileName']}: {result.get('error', 'Unknown error')}")
                            
                            results['details'].append(result)
                    else:
                        logger.error(f"❌ Batch {batch_num} failed: {data.get('error')}")
                        results['failed'] += len(batch)
                else:
                    logger.error(f"❌ API request failed: {response.status_code} - {response.text}")
                    results['failed'] += len(batch)
                    
            except requests.exceptions.Timeout:
                logger.error(f"⏱️ Batch {batch_num} timed out")
                results['failed'] += len(batch)
            except Exception as e:
                logger.error(f"❌ Error processing batch {batch_num}: {str(e)}")
                results['failed'] += len(batch)
        
        # Print summary
        logger.info("\n" + "="*60)
        logger.info("📊 INGESTION SUMMARY")
        logger.info("="*60)
        logger.info(f"Total Files: {results['total_files']}")
        logger.info(f"✅ Successful: {results['successful']}")
        logger.info(f"❌ Failed: {results['failed']}")
        logger.info(f"📄 Total Chunks Created: {results['total_chunks']}")
        logger.info(f"Success Rate: {(results['successful']/results['total_files']*100):.1f}%")
        logger.info("="*60)
        
        return results
    
    def ingest_from_folder(self, folder_path: str = "kb/12/", file_extension: str = ".pdf", batch_size: int = 10):
        """
        Convenience method to list and ingest files from a folder
        
        Args:
            folder_path: Azure folder path (e.g., 'kb/12/', 'kb/12/grade1/')
            file_extension: File type to process (e.g., '.pdf', '.docx', '.pptx')
            batch_size: Number of files per batch
        """
        logger.info(f"🔍 Starting ingestion from folder: {folder_path}")
        
        # List files
        file_names = self.list_files(prefix=folder_path, file_extension=file_extension)
        
        if not file_names:
            logger.warning(f"⚠️ No {file_extension} files found in {folder_path}")
            return
        
        # Show preview
        logger.info(f"\n📋 Files to be ingested:")
        for i, fname in enumerate(file_names[:10], 1):
            logger.info(f"   {i}. {fname}")
        
        if len(file_names) > 10:
            logger.info(f"   ... and {len(file_names) - 10} more files")
        
        # Confirm
        print(f"\n⚠️  About to ingest {len(file_names)} files to Pinecone")
        confirm = input("Continue? (yes/no): ").strip().lower()
        
        if confirm not in ['yes', 'y']:
            logger.info("❌ Ingestion cancelled by user")
            return
        
        # Ingest
        results = self.ingest_files_batch(file_names, batch_size=batch_size)
        
        return results
    
    def get_pinecone_stats(self):
        """Get current Pinecone index statistics"""
        try:
            response = requests.get(f"{self.api_base_url}/api/kb/stats", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    stats = data.get('stats', {})
                    
                    logger.info("\n" + "="*60)
                    logger.info("📊 PINECONE INDEX STATISTICS")
                    logger.info("="*60)
                    logger.info(f"Total Vectors: {stats.get('total_vectors', 0):,}")
                    logger.info(f"Dimension: {stats.get('dimension', 384)}")
                    logger.info(f"Index Fullness: {stats.get('index_fullness', 0):.4f}")
                    
                    namespaces = stats.get('namespaces', {})
                    if namespaces:
                        logger.info(f"\nNamespaces:")
                        for ns, count in namespaces.items():
                            logger.info(f"   {ns}: {count:,} vectors")
                    
                    logger.info("="*60)
                    
                    return stats
            else:
                logger.error(f"❌ Failed to get stats: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error getting stats: {str(e)}")
        
        return None


def main():
    """Main execution function"""
    print("="*60)
    print("🚀 Azure to Pinecone Ingestion Tool")
    print("="*60)
    
    try:
        # Initialize
        ingestion = AzureToPineconeIngestion()
        
        # Show menu
        while True:
            print("\n📋 Select an option:")
            print("1. List files from a folder")
            print("2. Ingest files from a folder")
            print("3. Ingest specific files (manual input)")
            print("4. View Pinecone statistics")
            print("5. Exit")
            
            choice = input("\nEnter your choice (1-5): ").strip()
            
            if choice == '1':
                # List files
                folder = input("Enter folder path (e.g., 'kb/12/' or 'kb/12/grade1/'): ").strip()
                extension = input("Enter file extension (e.g., '.pdf', '.docx', or leave empty for all): ").strip()
                
                files = ingestion.list_files(prefix=folder, file_extension=extension)
                
                if files:
                    print(f"\n📁 Found {len(files)} files:")
                    for i, fname in enumerate(files, 1):
                        print(f"   {i}. {fname}")
                else:
                    print("⚠️ No files found")
            
            elif choice == '2':
                # Ingest from folder
                folder = input("Enter folder path (e.g., 'kb/12/grade1/'): ").strip()
                extension = input("Enter file extension (default: .pdf): ").strip() or ".pdf"
                batch_size = input("Enter batch size (default: 10): ").strip()
                batch_size = int(batch_size) if batch_size.isdigit() else 10
                
                ingestion.ingest_from_folder(folder, extension, batch_size)
            
            elif choice == '3':
                # Manual file input
                print("\nEnter file paths (one per line, empty line to finish):")
                file_names = []
                while True:
                    fname = input().strip()
                    if not fname:
                        break
                    file_names.append(fname)
                
                if file_names:
                    batch_size = input("Enter batch size (default: 10): ").strip()
                    batch_size = int(batch_size) if batch_size.isdigit() else 10
                    
                    ingestion.ingest_files_batch(file_names, batch_size)
                else:
                    print("⚠️ No files provided")
            
            elif choice == '4':
                # View stats
                ingestion.get_pinecone_stats()
            
            elif choice == '5':
                print("\n👋 Goodbye!")
                break
            
            else:
                print("❌ Invalid choice. Please enter 1-5.")
    
    except KeyboardInterrupt:
        print("\n\n⚠️ Process interrupted by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
