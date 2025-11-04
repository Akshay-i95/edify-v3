"""
Enhanced Video Processor for KB Ingestion
Extracts audio content from MP4 videos and transcribes speech to text
Integrates with existing KB processing pipeline
"""

import os
import logging
import tempfile
import time
from typing import Dict, Tuple, List, Optional
from pathlib import Path
import traceback
from datetime import datetime

# Video/Audio processing
try:
    import ffmpeg
    import speech_recognition as sr
    from pydub import AudioSegment
    import whisper
    AUDIO_LIBS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Audio processing libraries not available: {e}")
    AUDIO_LIBS_AVAILABLE = False

class EnhancedVideoProcessor:
    """Enhanced video processor with full audio transcription"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.recognizer = sr.Recognizer() if AUDIO_LIBS_AVAILABLE else None
        self.whisper_model = None
        self.temp_dir = tempfile.mkdtemp(prefix="video_processing_")
        
        # Initialize Whisper model (small model for speed/memory balance)
        if AUDIO_LIBS_AVAILABLE:
            try:
                self.whisper_model = whisper.load_model("base")
                self.logger.info("✅ Whisper model loaded successfully")
            except Exception as e:
                self.logger.warning(f"⚠️ Whisper model loading failed: {e}")

        self.logger.info(f"📁 Video processing temp directory: {self.temp_dir}")

    def process_mp4_full(self, video_content: bytes, file_info: Dict) -> Tuple[str, Dict]:
        """
        Process MP4 file with full audio transcription
        
        Args:
            video_content: Raw video file bytes
            file_info: File information dictionary
            
        Returns:
            Tuple of (extracted_text, metadata)
        """
        start_time = time.time()
        temp_video_path = None
        temp_audio_path = None
        
        try:
            # Create temporary file for video
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_video:
                temp_video.write(video_content)
                temp_video_path = temp_video.name
            
            self.logger.info(f"🎥 Processing MP4: {file_info.get('filename', 'unknown')}")
            
            # Extract basic metadata
            metadata = self._extract_video_metadata(temp_video_path, file_info)
            
            # Add video URL for chatbot access
            metadata['video_url'] = self._generate_video_url(file_info)
            metadata['media_type'] = 'video'
            metadata['has_video_content'] = True
            
            # Extract and transcribe audio
            transcribed_text = self._extract_and_transcribe_audio(temp_video_path)
            
            if transcribed_text:
                metadata['transcription_available'] = True
                metadata['transcription_method'] = 'whisper' if self.whisper_model else 'speech_recognition'
                self.logger.info(f"✅ Transcription successful using {metadata['transcription_method']}")
            else:
                metadata['transcription_available'] = False
                metadata['transcription_method'] = 'none'
                self.logger.warning(f"⚠️ No transcription available for {file_info.get('filename')}")
            
            # Combine all text content
            combined_text = self._combine_text_content(transcribed_text, metadata)
            
            # Update processing metadata
            processing_time = time.time() - start_time
            metadata.update({
                'processing_time': round(processing_time, 2),
                'processing_method': 'enhanced_full_extraction',
                'content_length': len(combined_text) if combined_text else 0,
                'processed_timestamp': datetime.now().isoformat()
            })
            
            self.logger.info(f"🎬 Video processing completed in {processing_time:.2f}s")
            return combined_text, metadata
            
        except Exception as e:
            self.logger.error(f"❌ MP4 processing failed: {e}")
            self.logger.error(traceback.format_exc())
            
            # Return basic metadata even on failure
            basic_metadata = {
                'error': str(e),
                'transcription_available': False,
                'processing_method': 'failed',
                'processed_timestamp': datetime.now().isoformat(),
                'video_url': self._generate_video_url(file_info),
                'media_type': 'video',
                'has_video_content': True
            }
            
            return "", basic_metadata
            
        finally:
            # Cleanup temporary files
            self._cleanup_temp_files([temp_video_path, temp_audio_path])

    def _extract_and_transcribe_audio(self, video_path: str) -> str:
        """Extract audio from video and transcribe to text using ffmpeg"""
        if not AUDIO_LIBS_AVAILABLE:
            self.logger.warning("⚠️ Audio processing libraries not available, skipping transcription")
            return ""
            
        audio_path = None
        try:
            # Check if video has audio stream
            probe = ffmpeg.probe(video_path)
            audio_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
            
            if not audio_stream:
                self.logger.warning("⚠️ No audio track found in video")
                return ""
            
            # Extract audio using ffmpeg
            self.logger.info("🔊 Extracting audio from video using ffmpeg...")
            audio_path = video_path.replace('.mp4', '_audio.wav')
            
            (
                ffmpeg
                .input(video_path)
                .output(audio_path, acodec='pcm_s16le', ac=1, ar='16000')
                .overwrite_output()
                .run(quiet=True)
            )
            
            if not os.path.exists(audio_path):
                self.logger.warning("⚠️ Audio extraction failed")
                return ""
            
            # Transcribe using Whisper (primary method)
            if self.whisper_model:
                try:
                    self.logger.info("🤖 Transcribing with Whisper...")
                    result = self.whisper_model.transcribe(audio_path)
                    transcription = result["text"].strip()
                    
                    if transcription:
                        self.logger.info(f"✅ Whisper transcription successful ({len(transcription)} chars)")
                        return transcription
                    else:
                        self.logger.warning("⚠️ Whisper returned empty transcription")
                        
                except Exception as e:
                    self.logger.warning(f"⚠️ Whisper transcription failed: {e}")
            
            # Fallback to SpeechRecognition
            return self._transcribe_with_speech_recognition(audio_path)
            
        except Exception as e:
            self.logger.error(f"❌ Audio extraction/transcription failed: {e}")
            return ""
            
        finally:
            # Clean up audio file
            if audio_path and os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                except:
                    pass

    def _transcribe_with_speech_recognition(self, audio_path: str) -> str:
        """Fallback transcription using SpeechRecognition library"""
        try:
            self.logger.info("🔄 Trying SpeechRecognition fallback...")
            
            # Convert to format suitable for speech recognition
            audio_segment = AudioSegment.from_wav(audio_path)
            
            # Convert to mono and appropriate sample rate
            audio_segment = audio_segment.set_channels(1).set_frame_rate(16000)
            
            # Split into chunks (SpeechRecognition works better with shorter segments)
            chunk_length = 30000  # 30 seconds
            chunks = [audio_segment[i:i + chunk_length] 
                     for i in range(0, len(audio_segment), chunk_length)]
            
            transcriptions = []
            
            for i, chunk in enumerate(chunks[:10]):  # Limit to first 10 chunks (5 minutes)
                try:
                    # Save chunk to temporary file
                    chunk_path = audio_path.replace('.wav', f'_chunk_{i}.wav')
                    chunk.export(chunk_path, format="wav")
                    
                    # Transcribe chunk
                    with sr.AudioFile(chunk_path) as source:
                        audio_data = self.recognizer.record(source)
                        text = self.recognizer.recognize_google(audio_data)
                        if text.strip():
                            transcriptions.append(text.strip())
                    
                    # Clean up chunk file
                    if os.path.exists(chunk_path):
                        os.remove(chunk_path)
                        
                except Exception as e:
                    self.logger.debug(f"Chunk {i} transcription failed: {e}")
                    continue
            
            final_transcription = " ".join(transcriptions)
            
            if final_transcription:
                self.logger.info(f"✅ SpeechRecognition transcription successful ({len(final_transcription)} chars)")
            else:
                self.logger.warning("⚠️ SpeechRecognition returned empty transcription")
                
            return final_transcription
            
        except Exception as e:
            self.logger.warning(f"⚠️ SpeechRecognition fallback failed: {e}")
            return ""

    def _fallback_metadata_only(self, content: bytes, file_info: Dict) -> Tuple[str, Dict]:
        """Fallback to metadata-only processing if audio processing fails"""
        filename = file_info['filename']
        size_mb = len(content) / (1024 * 1024)
        
        text_content = f"""
        Video File: {filename}
        File Type: MP4 Video
        Size: {size_mb:.2f} MB
        Grade: {file_info.get('grade', 'Unknown')}
        
        This is a video educational resource. Audio transcription was not available
        during processing, but the video contains educational content.
        """
        
        metadata = {
            'file_type': 'video_metadata_only',
            'size_mb': size_mb,
            'extraction_method': 'metadata_fallback',
            'transcription_available': False
        }
        
        return text_content.strip(), metadata

    def _extract_video_metadata(self, video_path: str, file_info: Dict) -> Dict:
        """Extract basic metadata from video file using ffmpeg"""
        try:
            if not AUDIO_LIBS_AVAILABLE:
                self.logger.warning("⚠️ Video processing libraries not available, using basic metadata")
                return {
                    'filename': file_info.get('filename', ''),
                    'grade': file_info.get('grade', 'unknown'),
                    'subject': file_info.get('subject', 'general'),
                    'has_audio': False,
                    'duration_seconds': 0,
                    'fps': 0,
                    'size': [0, 0]
                }
                
            # Use ffmpeg to probe video metadata
            probe = ffmpeg.probe(video_path)
            
            # Extract video stream info
            video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
            audio_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
            
            duration = float(probe['format'].get('duration', 0))
            
            # Calculate FPS safely
            fps = 0
            if video_stream and 'r_frame_rate' in video_stream:
                fps_str = video_stream['r_frame_rate']
                if '/' in fps_str:
                    try:
                        num, den = fps_str.split('/')
                        fps = float(num) / float(den) if float(den) != 0 else 0
                    except:
                        fps = 0
                        
            metadata = {
                'duration_seconds': duration,
                'fps': fps,
                'size': [int(video_stream.get('width', 0)), int(video_stream.get('height', 0))] if video_stream else [0, 0],
                'has_audio': audio_stream is not None,
                'filename': file_info.get('filename', ''),
                'grade': file_info.get('grade', 'unknown'),
                'subject': file_info.get('subject', 'general')
            }
            return metadata
        except Exception as e:
            self.logger.warning(f"⚠️ Could not extract video metadata: {e}")
            return {
                'filename': file_info.get('filename', ''),
                'grade': file_info.get('grade', 'unknown'),
                'subject': file_info.get('subject', 'general'),
                'has_audio': False,
                'duration_seconds': 0,
                'fps': 0,
                'size': [0, 0]
            }

    def _combine_text_content(self, transcribed_text: str, metadata: Dict) -> str:
        """Combine transcribed text with metadata for comprehensive content"""
        content_parts = []
        
        # Add file information
        filename = metadata.get('filename', 'unknown')
        grade = metadata.get('grade', 'unknown')
        duration = metadata.get('duration_seconds', 0)
        
        content_parts.append(f"Video File: {filename}")
        content_parts.append(f"Grade Level: {grade}")
        content_parts.append(f"Duration: {duration:.1f} seconds")
        content_parts.append(f"Media Type: Educational Video")
        
        if metadata.get('has_audio'):
            content_parts.append("Audio Content: Available")
        else:
            content_parts.append("Audio Content: Not available")
        
        # Add transcribed content if available
        if transcribed_text and transcribed_text.strip():
            content_parts.append("\n--- Video Transcript ---")
            content_parts.append(transcribed_text.strip())
        else:
            content_parts.append("\n--- No Transcript Available ---")
            content_parts.append("This video file could not be transcribed automatically.")
        
        return "\n".join(content_parts)

    def _generate_video_url(self, file_info: Dict) -> str:
        """
        Generate video URL for chatbot access
        
        Args:
            file_info: File information dictionary
            
        Returns:
            Video URL string
        """
        # Get Azure storage account info
        storage_account = os.getenv('AZURE_STORAGE_ACCOUNT_NAME', 'your-storage-account')
        container_name = os.getenv('AZURE_CONTAINER_NAME', 'edifydocumentcontainer')
        file_path = file_info.get('file_path', '')
        
        # Generate Azure Blob Storage URL
        # Format: https://{account}.blob.core.windows.net/{container}/{blob-path}
        video_url = f"https://{storage_account}.blob.core.windows.net/{container_name}/{file_path}"
        
        return video_url

    def _cleanup_temp_files(self, file_paths: List[str]):
        """Clean up temporary files"""
        for file_path in file_paths:
            if file_path and os.path.exists(file_path):
                try:
                    os.unlink(file_path)
                    self.logger.debug(f"🗑️ Cleaned up: {file_path}")
                except Exception as e:
                    self.logger.warning(f"⚠️ Failed to cleanup {file_path}: {e}")

    def __del__(self):
        """Clean up temporary directory"""
        try:
            import shutil
            if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
        except:
            pass