#!/usr/bin/env python3
"""
Enhanced KB Processing Script - Robust version with resource monitoring
Handles memory management, error recovery, and system resource constraints
"""

import os
import sys
import json
import time
import gc
import psutil
import logging
import traceback
import tempfile
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import signal
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Import processing modules
from enhanced_kb_processor import EnhancedKBProcessor as KBProcessor

class ResourceMonitor:
    """Monitor system resources to prevent crashes"""
    
    def __init__(self, max_memory_percent=85, max_cpu_percent=90, min_disk_gb=2):
        self.max_memory_percent = max_memory_percent
        self.max_cpu_percent = max_cpu_percent
        self.min_disk_gb = min_disk_gb
        self.logger = logging.getLogger(__name__)
    
    def check_resources(self) -> Tuple[bool, str]:
        """Check if system resources are available for processing"""
        try:
            # Check memory
            memory = psutil.virtual_memory()
            if memory.percent > self.max_memory_percent:
                return False, f"Memory usage too high: {memory.percent:.1f}% > {self.max_memory_percent}%"
            
            # Check CPU (average over 1 second)
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > self.max_cpu_percent:
                return False, f"CPU usage too high: {cpu_percent:.1f}% > {self.max_cpu_percent}%"
            
            # Check disk space for /tmp
            disk = psutil.disk_usage('/tmp')
            free_gb = disk.free / (1024**3)
            if free_gb < self.min_disk_gb:
                return False, f"Disk space too low: {free_gb:.1f}GB < {self.min_disk_gb}GB"
            
            return True, f"Resources OK - Memory: {memory.percent:.1f}%, CPU: {cpu_percent:.1f}%, Disk: {free_gb:.1f}GB"
        
        except Exception as e:
            self.logger.warning(f"Resource check failed: {e}")
            return True, "Resource check failed, assuming OK"
    
    def log_system_status(self):
        """Log detailed system status"""
        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            disk = psutil.disk_usage('/')
            tmp_disk = psutil.disk_usage('/tmp')
            
            self.logger.info(f"💻 System Status:")
            self.logger.info(f"   Memory: {memory.percent:.1f}% used ({memory.used/1024**3:.1f}GB/{memory.total/1024**3:.1f}GB)")
            self.logger.info(f"   Swap: {swap.percent:.1f}% used ({swap.used/1024**3:.1f}GB/{swap.total/1024**3:.1f}GB)")
            self.logger.info(f"   Disk /: {disk.percent:.1f}% used ({disk.free/1024**3:.1f}GB free)")
            self.logger.info(f"   Disk /tmp: {tmp_disk.percent:.1f}% used ({tmp_disk.free/1024**3:.1f}GB free)")
            self.logger.info(f"   CPU: {psutil.cpu_percent(interval=1):.1f}%")
            
        except Exception as e:
            self.logger.warning(f"Failed to log system status: {e}")

class EnhancedProgressTracker:
    """Enhanced progress tracking with better persistence and recovery"""
    
    def __init__(self, progress_file="processing_progress.json"):
        self.progress_file = progress_file
        self.backup_file = f"{progress_file}.backup"
        self.processed_files = set()
        self.total_processed = 0
        self.last_save_time = time.time()
        self.save_interval = 5  # Save every 5 files
        self.logger = logging.getLogger(__name__)
        
        # Load existing progress
        self.load_progress()
    
    def load_progress(self):
        """Load progress with backup recovery"""
        for file_path in [self.progress_file, self.backup_file]:
            if not os.path.exists(file_path):
                continue
                
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                self.processed_files = set(data.get("processed_files", []))
                self.total_processed = len(self.processed_files)
                
                self.logger.info(f"📄 Loaded progress: {self.total_processed} files from {file_path}")
                
                # If we loaded from backup, restore main file
                if file_path == self.backup_file:
                    self.save_progress(force=True)
                    self.logger.info(f"🔄 Restored progress file from backup")
                
                return
                
            except Exception as e:
                self.logger.warning(f"Failed to load progress from {file_path}: {e}")
        
        self.logger.info("📄 Starting with empty progress")
    
    def is_processed(self, file_path: str) -> bool:
        """Check if file has been processed"""
        return file_path in self.processed_files
    
    def mark_processed(self, file_path: str):
        """Mark file as processed and save if needed"""
        if file_path not in self.processed_files:
            self.processed_files.add(file_path)
            self.total_processed += 1
            
            # Save progress periodically
            if (self.total_processed % self.save_interval == 0 or 
                time.time() - self.last_save_time > 30):  # Save every 30 seconds
                self.save_progress()
    
    def save_progress(self, force=False):
        """Save progress with atomic write and backup"""
        if not force and time.time() - self.last_save_time < 10:
            return  # Don't save too frequently
        
        try:
            data = {
                "processed_files": sorted(list(self.processed_files)),
                "total_processed": self.total_processed,
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "version": "enhanced"
            }
            
            # Create backup of current file
            if os.path.exists(self.progress_file):
                shutil.copy2(self.progress_file, self.backup_file)
            
            # Atomic write using temporary file
            temp_file = f"{self.progress_file}.tmp"
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Atomic rename
            os.rename(temp_file, self.progress_file)
            self.last_save_time = time.time()
            
        except Exception as e:
            self.logger.error(f"Failed to save progress: {e}")

class EnhancedKBProcessor:
    """Enhanced KB processor with robust error handling and resource management"""
    
    def __init__(self):
        self.setup_logging()
        self.resource_monitor = ResourceMonitor()
        self.progress_tracker = EnhancedProgressTracker()
        self.processor = None
        self.running = True
        self.processed_count = 0
        self.failed_count = 0
        self.start_time = time.time()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        self.logger = logging.getLogger(__name__)
    
    def setup_logging(self):
        """Setup enhanced logging"""
        log_file = f"logs/kb_processing_enhanced_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        os.makedirs("logs", exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f"🛑 Received signal {signum}, shutting down gracefully...")
        self.running = False
        self.progress_tracker.save_progress(force=True)
        sys.exit(0)
    
    def cleanup_temp_files(self):
        """Clean up temporary files to free disk space"""
        try:
            temp_dir = tempfile.gettempdir()
            cleaned_count = 0
            for file_path in Path(temp_dir).glob("tmp*"):
                try:
                    if file_path.is_file() and time.time() - file_path.stat().st_mtime > 3600:  # 1 hour old
                        file_path.unlink()
                        cleaned_count += 1
                except:
                    pass
            
            if cleaned_count > 0:
                self.logger.info(f"🧹 Cleaned {cleaned_count} temporary files")
                
        except Exception as e:
            self.logger.warning(f"Failed to clean temp files: {e}")
    
    def force_garbage_collection(self):
        """Force garbage collection to free memory"""
        try:
            collected = gc.collect()
            if collected > 0:
                self.logger.debug(f"🗑️ Garbage collected {collected} objects")
        except Exception as e:
            self.logger.warning(f"Garbage collection failed: {e}")
    
    def wait_for_resources(self, max_wait_time=300):
        """Wait for system resources to become available"""
        wait_start = time.time()
        
        while time.time() - wait_start < max_wait_time:
            if not self.running:
                return False
                
            resource_ok, message = self.resource_monitor.check_resources()
            if resource_ok:
                return True
            
            self.logger.warning(f"⏳ {message} - waiting 30 seconds...")
            time.sleep(30)
            
            # Try to free up resources
            self.force_garbage_collection()
            self.cleanup_temp_files()
        
        self.logger.error(f"❌ Resources not available after {max_wait_time} seconds")
        return False
    
    def process_file_safely(self, file_info: dict) -> bool:
        """Process a single file with comprehensive error handling"""
        file_path = file_info['path']
        file_size_mb = file_info['size'] / (1024 * 1024)
        
        try:
            self.logger.info(f"🔄 Processing {self.processed_count + 1}: {os.path.basename(file_path)} ({file_size_mb:.1f}MB)")
            
            # Check resources before processing
            if not self.wait_for_resources():
                return False
            
            # Process the file using the actual processor methods
            try:
                # Get the blob and file info
                blob = file_info['blob']
                blob_name = file_info['path']
                
                # Create file info dict that processor expects
                processor_file_info = {
                    'blob_name': blob_name,
                    'filename': blob_name.split('/')[-1],
                    'grade': blob_name.split('/')[2] if len(blob_name.split('/')) > 2 else 'common',
                    'file_type': f".{blob_name.split('.')[-1].lower()}",
                    'size': file_size_mb,
                    'last_modified': blob.last_modified
                }
                
                # Determine namespace
                namespace = self.processor.get_namespace_for_grade(processor_file_info['grade'])
                
                # Use the processor's internal method
                chunks = self.processor._process_single_file(processor_file_info, namespace)
                
                # Convert result to expected format
                if chunks:
                    result = {'success': True, 'chunks': len(chunks), 'processing_time': 0}
                else:
                    result = {'success': False, 'error': 'No chunks generated'}
                    
            except Exception as e:
                result = {'success': False, 'error': str(e)}
            
            if result and result.get('success', False):
                chunks = result.get('chunks', 0)
                processing_time = result.get('processing_time', 0)
                self.logger.info(f"✅ Completed {os.path.basename(file_path)}: {chunks} chunks in {processing_time:.1f}s")
                
                # Mark as processed
                self.progress_tracker.mark_processed(file_path)
                self.processed_count += 1
                
                # Cleanup after successful processing
                self.force_garbage_collection()
                
                return True
            else:
                error = result.get('error', 'Unknown error') if result else 'No result returned'
                self.logger.warning(f"⚠️ Failed to process {os.path.basename(file_path)}: {error}")
                self.failed_count += 1
                
                # Still mark as processed to avoid infinite retries
                self.progress_tracker.mark_processed(file_path)
                return True  # Continue processing other files
                
        except Exception as e:
            self.logger.error(f"❌ Exception processing {os.path.basename(file_path)}: {e}")
            self.logger.debug(traceback.format_exc())
            self.failed_count += 1
            
            # Mark as processed to avoid infinite retries
            self.progress_tracker.mark_processed(file_path)
            
            # Force cleanup after errors
            self.force_garbage_collection()
            self.cleanup_temp_files()
            
            return True  # Continue processing other files
    
    def log_progress_summary(self):
        """Log processing progress summary"""
        elapsed_time = time.time() - self.start_time
        processed_total = self.progress_tracker.total_processed
        
        if self.processed_count > 0:
            avg_time_per_file = elapsed_time / self.processed_count
            self.logger.info(f"📊 Progress Summary:")
            self.logger.info(f"   Total processed: {processed_total}")
            self.logger.info(f"   This session: {self.processed_count} processed, {self.failed_count} failed")
            self.logger.info(f"   Session time: {elapsed_time/60:.1f} minutes")
            self.logger.info(f"   Average: {avg_time_per_file:.1f}s per file")
    
    def run(self):
        """Main processing loop with enhanced error handling"""
        self.logger.info("🚀 Starting Enhanced Large File KB Processing...")
        self.logger.info("📋 This version includes resource monitoring and robust error handling!")
        self.logger.info(f"📅 Started at: {datetime.now()}")
        
        try:
            # Log initial system status
            self.resource_monitor.log_system_status()
            
            # Initialize processor
            self.logger.info("🔧 Initializing processor...")
            config = {
                'batch_size': 2,  # Very small batches for stability
                'max_workers': 1,  # Single worker to control memory
                'embedding_batch_size': 20,  # Smaller embedding batches
                'pinecone_batch_size': 30,  # Smaller Pinecone batches
                'memory_limit_mb': 2048,  # 2GB memory limit
                'gc_frequency': 1  # Aggressive garbage collection
            }
            self.processor = KBProcessor(config)
            
            # Get list of files to process
            self.logger.info("🔍 Scanning for files to process...")
            
            # Get container client
            container_client = self.processor.container_client
            
            # Get all files from kb/12/
            all_blobs = list(container_client.list_blobs(name_starts_with='kb/12/'))
            
            # Filter out already processed files and get file info
            files_to_process = []
            large_files_count = 0
            for blob in all_blobs:
                if not self.progress_tracker.is_processed(blob.name):
                    # Check if it's a supported file type
                    file_ext = blob.name.split('.')[-1].lower()
                    if f'.{file_ext}' in self.processor.file_handlers:
                        files_to_process.append({
                            'path': blob.name,
                            'size': blob.size,
                            'blob': blob
                        })
                        
                        # Count large files
                        if blob.size > 10 * 1024 * 1024:  # >10MB
                            large_files_count += 1
            
            self.logger.info(f"📊 Total files found: {len(all_blobs)}")
            self.logger.info(f"📁 Already processed: {self.progress_tracker.total_processed}")
            self.logger.info(f"🎯 Files to process: {len(files_to_process)}")
            self.logger.info(f"🎯 Large files (>10MB) to process: {large_files_count}")
            
            if not files_to_process:
                self.logger.info("🎉 All files have been processed!")
                return
            
            # Sort by size (process smaller files first to build momentum)
            files_to_process.sort(key=lambda x: x['size'])
            
            # Process files
            for i, file_info in enumerate(files_to_process):
                if not self.running:
                    self.logger.info("🛑 Processing stopped by signal")
                    break
                
                # Log progress every 10 files
                if i % 10 == 0:
                    self.log_progress_summary()
                    self.resource_monitor.log_system_status()
                
                # Process the file
                success = self.process_file_safely(file_info)
                if not success:
                    self.logger.error("❌ Processing failed due to resource constraints")
                    break
                
                # Brief pause between files to prevent overwhelming the system
                time.sleep(0.5)
            
            # Final summary
            self.log_progress_summary()
            self.resource_monitor.log_system_status()
            
            if self.processed_count > 0:
                self.logger.info(f"🎉 Session completed! Processed {self.processed_count} files, {self.failed_count} failures")
            else:
                self.logger.info("ℹ️ No files were processed in this session")
                
        except Exception as e:
            self.logger.error(f"❌ Fatal error in main processing loop: {e}")
            self.logger.debug(traceback.format_exc())
        
        finally:
            # Cleanup
            self.progress_tracker.save_progress(force=True)
            self.logger.info("🏁 Enhanced KB Processing completed")

if __name__ == "__main__":
    processor = EnhancedKBProcessor()
    processor.run()