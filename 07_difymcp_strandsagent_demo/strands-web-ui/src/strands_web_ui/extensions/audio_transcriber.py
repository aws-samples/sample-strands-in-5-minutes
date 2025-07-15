"""
Audio transcription utility for MP3 files using AWS Transcribe.

This module provides functionality to:
- Process MP3 files and convert them to the required format for AWS Transcribe
- Automatically detect language (Indonesian/English)
- Handle both streaming and batch transcription
"""

import asyncio
import io
import logging
import tempfile
import os
from typing import Optional, Dict, Any, List
import boto3
from botocore.exceptions import ClientError

try:
    from pydub import AudioSegment
    from pydub.utils import which
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    logging.warning("pydub not available. Audio conversion features will be limited.")

try:
    from amazon_transcribe.client import TranscribeStreamingClient
    from amazon_transcribe.handlers import TranscriptResultStreamHandler
    from amazon_transcribe.model import TranscriptEvent
    TRANSCRIBE_STREAMING_AVAILABLE = True
except ImportError:
    TRANSCRIBE_STREAMING_AVAILABLE = False
    logging.warning("amazon-transcribe not available. Using batch transcription only.")

logger = logging.getLogger(__name__)

class TranscriptionResult:
    """Container for transcription results."""
    
    def __init__(self):
        self.transcript = ""
        self.language_code = None
        self.confidence = None
        self.segments = []
        self.is_complete = False

class StreamingTranscriptHandler(TranscriptResultStreamHandler):
    """Custom handler for streaming transcription events."""
    
    def __init__(self, stream, result_container: TranscriptionResult):
        super().__init__(stream)
        self.result_container = result_container
        self.last_partial_transcript = ""  # Track the last partial result
        
    async def handle_transcript_event(self, transcript_event: TranscriptEvent):
        """Handle transcript events and update the result container."""
        try:
            results = transcript_event.transcript.results
            logger.info(f"=== TRANSCRIPT EVENT DEBUG ===")
            logger.info(f"Number of results: {len(results)}")
            
            for i, result in enumerate(results):
                logger.info(f"Result {i}: is_partial={result.is_partial}")
                logger.info(f"Result {i}: alternatives count={len(result.alternatives) if result.alternatives else 0}")
                
                if result.alternatives:
                    for j, alt in enumerate(result.alternatives):
                        transcript_text = alt.transcript if hasattr(alt, 'transcript') else ""
                        confidence = getattr(alt, 'confidence', None)
                        logger.info(f"  Alternative {j}: transcript='{transcript_text}', confidence={confidence}")
                        
                        # For the first alternative, process it
                        if j == 0:
                            # Update language code if available
                            if hasattr(result, 'language_code') and result.language_code:
                                self.result_container.language_code = result.language_code
                                logger.info(f"Language from result: {result.language_code}")
                            
                            # Handle both partial and final results
                            if transcript_text and transcript_text.strip():
                                if result.is_partial:
                                    logger.info(f"PARTIAL: '{transcript_text}'")
                                    # Store the latest partial result
                                    self.last_partial_transcript = transcript_text
                                else:
                                    logger.info(f"FINAL: '{transcript_text}' - ADDING TO TRANSCRIPT")
                                    self.result_container.transcript += transcript_text + " "
                                    self.result_container.confidence = confidence
                                    
                                    # Store segment information
                                    segment = {
                                        'transcript': transcript_text,
                                        'confidence': confidence,
                                        'start_time': getattr(result, 'start_time', None),
                                        'end_time': getattr(result, 'end_time', None)
                                    }
                                    self.result_container.segments.append(segment)
                                    
                                    # Clear partial transcript since we got a final one
                                    self.last_partial_transcript = ""
                else:
                    logger.warning(f"Result {i}: No alternatives found")
            
            # Check for language identification at transcript level
            if hasattr(transcript_event.transcript, 'language_identification'):
                lang_id = transcript_event.transcript.language_identification
                if hasattr(lang_id, 'language_code') and lang_id.language_code:
                    self.result_container.language_code = lang_id.language_code
                    logger.info(f"Language from transcript level: {lang_id.language_code}")
            
            logger.info(f"Current transcript state: '{self.result_container.transcript}'")
            logger.info(f"Last partial transcript: '{self.last_partial_transcript}'")
            logger.info(f"=== END TRANSCRIPT EVENT DEBUG ===")
                    
        except Exception as e:
            logger.error(f"Error handling transcript event: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            
    def finalize_transcript(self):
        """Finalize transcript by using the last partial result if no final result was received."""
        if not self.result_container.transcript.strip() and self.last_partial_transcript.strip():
            logger.info(f"No final transcript received, using last partial result: '{self.last_partial_transcript}'")
            self.result_container.transcript = self.last_partial_transcript
            
            # Create a segment for the partial result
            segment = {
                'transcript': self.last_partial_transcript,
                'confidence': self.result_container.confidence,
                'start_time': None,
                'end_time': None
            }
            self.result_container.segments.append(segment)
            
    async def handle_language_identification_event(self, language_identification_event):
        """Handle language identification events."""
        try:
            logger.info(f"=== LANGUAGE IDENTIFICATION EVENT ===")
            logger.info(f"Event: {language_identification_event}")
            
            if hasattr(language_identification_event, 'language_code'):
                self.result_container.language_code = language_identification_event.language_code
                logger.info(f"Language identification: {language_identification_event.language_code}")
            
            # Check for other language identification attributes
            for attr in dir(language_identification_event):
                if not attr.startswith('_'):
                    value = getattr(language_identification_event, attr)
                    logger.info(f"  {attr}: {value}")
                    
            logger.info(f"=== END LANGUAGE IDENTIFICATION EVENT ===")
        except Exception as e:
            logger.error(f"Error handling language identification event: {str(e)}")
            
    async def handle_events(self):
        """Override to add more comprehensive event handling."""
        try:
            logger.info("Starting event handling...")
            await super().handle_events()
            logger.info("Event handling completed")
        except Exception as e:
            logger.error(f"Error in event handling: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

class AudioTranscriber:
    """Main class for handling audio transcription."""
    
    def __init__(self, region: str = "ap-southeast-1"):
        """
        Initialize the audio transcriber.
        
        Args:
            region: AWS region for Transcribe service
        """
        self.region = region
        self.transcribe_client = boto3.client('transcribe', region_name=region)
        
        # Check if streaming client is available
        if TRANSCRIBE_STREAMING_AVAILABLE:
            self.streaming_client = TranscribeStreamingClient(region=region)
        else:
            self.streaming_client = None
            logger.warning("Streaming transcription not available. Using batch mode only.")
    
    def _convert_mp3_to_wav(self, mp3_data: bytes) -> bytes:
        """
        Convert MP3 data to WAV format suitable for transcription.
        
        Args:
            mp3_data: MP3 file data as bytes
            
        Returns:
            WAV file data as bytes
        """
        if not PYDUB_AVAILABLE:
            raise RuntimeError("pydub is required for audio conversion. Please install it with: pip install pydub")
        
        # Load MP3 from bytes
        audio = AudioSegment.from_mp3(io.BytesIO(mp3_data))
        
        # Convert to the format required by Transcribe
        # 16kHz, mono, 16-bit PCM
        audio = audio.set_frame_rate(16000)
        audio = audio.set_channels(1)
        audio = audio.set_sample_width(2)  # 16-bit
        
        # Export to WAV format
        wav_buffer = io.BytesIO()
        audio.export(wav_buffer, format="wav")
        wav_buffer.seek(0)
        
        return wav_buffer.read()
    
    async def transcribe_streaming(self, audio_data: bytes, 
                                 language_options: List[str] = None) -> TranscriptionResult:
        """
        Transcribe audio using streaming API.
        
        Args:
            audio_data: Audio data in bytes (WAV format, 16kHz, mono)
            language_options: List of language codes to consider
            
        Returns:
            TranscriptionResult object
        """
        if not self.streaming_client:
            raise RuntimeError("Streaming transcription not available")
        
        if language_options is None:
            language_options = ["en-US", "id-ID"]  # English and Indonesian
        
        result_container = TranscriptionResult()
        logger.info(f"Starting transcription with language options: {language_options}")
        logger.info(f"Audio data size: {len(audio_data)} bytes")
        
        try:
            # Start transcription stream
            stream = await self.streaming_client.start_stream_transcription(
                language_code=None,  # Auto-detect
                identify_language=True,
                language_options=language_options,
                media_sample_rate_hz=16000,
                media_encoding="pcm",
                identify_multiple_languages=False,  # Set to True if you want to detect multiple languages
            )
            
            logger.info("Transcription stream started successfully")
            
            # Create handler
            handler = StreamingTranscriptHandler(stream.output_stream, result_container)
            
            # Send audio data
            async def send_audio():
                try:
                    # Use smaller chunks for better streaming performance
                    chunk_size = 1024 * 4  # 4KB chunks (reduced from 8KB)
                    total_chunks = (len(audio_data) + chunk_size - 1) // chunk_size
                    logger.info(f"Sending {total_chunks} audio chunks of {chunk_size} bytes each")
                    
                    for i in range(0, len(audio_data), chunk_size):
                        chunk = audio_data[i:i + chunk_size]
                        await stream.input_stream.send_audio_event(audio_chunk=chunk)
                        # Slightly longer delay for better processing
                        await asyncio.sleep(0.05)  # 50ms delay
                        
                        if (i // chunk_size) % 10 == 0:  # Log every 10th chunk
                            logger.debug(f"Sent chunk {i // chunk_size + 1}/{total_chunks}")
                    
                    logger.info("All audio chunks sent, ending stream")
                    await stream.input_stream.end_stream()
                    
                    # Give some time for final processing
                    await asyncio.sleep(1.0)
                    
                except Exception as e:
                    logger.error(f"Error sending audio: {str(e)}")
                    raise
            
            # Process transcription with timeout
            logger.info("Starting audio processing and event handling")
            try:
                # Add timeout to prevent hanging
                await asyncio.wait_for(
                    asyncio.gather(send_audio(), handler.handle_events()),
                    timeout=60.0  # 60 second timeout
                )
            except asyncio.TimeoutError:
                logger.error("Transcription timed out after 60 seconds")
                raise RuntimeError("Transcription timed out")
            
            # Finalize transcript - use partial result if no final result was received
            handler.finalize_transcript()
            
            result_container.is_complete = True
            result_container.transcript = result_container.transcript.strip()
            
            logger.info(f"Transcription completed. Final transcript: '{result_container.transcript}'")
            logger.info(f"Language detected: {result_container.language_code}")
            logger.info(f"Number of segments: {len(result_container.segments)}")
            
            # If transcript is empty but language was detected, there might be an issue
            if not result_container.transcript and result_container.language_code:
                logger.warning("Language was detected but transcript is empty. This might indicate:")
                logger.warning("1. Audio contains no speech")
                logger.warning("2. Audio quality is too poor")
                logger.warning("3. Audio format compatibility issue")
                logger.warning("4. Streaming API processing issue")
                
                # Set a helpful message
                result_container.transcript = f"[No speech detected in {result_container.language_code} audio]"
            
        except Exception as e:
            logger.error(f"Streaming transcription failed: {str(e)}")
            logger.error(f"Result container state: transcript='{result_container.transcript}', language={result_container.language_code}")
            raise
        
        return result_container
    
    def transcribe_batch(self, audio_data: bytes, 
                        language_options: List[str] = None) -> TranscriptionResult:
        """
        Transcribe audio using batch API (upload to S3 first).
        
        Args:
            audio_data: Audio data in bytes
            language_options: List of language codes to consider
            
        Returns:
            TranscriptionResult object
        """
        if language_options is None:
            language_options = ["en-US", "id-ID"]
        
        result_container = TranscriptionResult()
        
        # This would require S3 upload and is more complex
        # For now, we'll focus on the streaming approach
        raise NotImplementedError("Batch transcription requires S3 setup. Use streaming instead.")
    
    async def transcribe_mp3_file(self, mp3_data: bytes, 
                                language_options: List[str] = None) -> TranscriptionResult:
        """
        Transcribe an MP3 file with automatic language detection.
        
        Args:
            mp3_data: MP3 file data as bytes
            language_options: List of language codes to consider (default: en-US, id-ID)
            
        Returns:
            TranscriptionResult object with transcript and detected language
        """
        try:
            # Convert MP3 to WAV format
            logger.info("Converting MP3 to WAV format...")
            wav_data = self._convert_mp3_to_wav(mp3_data)
            
            # Use streaming transcription if available
            if self.streaming_client:
                logger.info("Starting streaming transcription...")
                result = await self.transcribe_streaming(wav_data, language_options)
            else:
                logger.info("Streaming not available, using batch transcription...")
                result = self.transcribe_batch(wav_data, language_options)
            
            logger.info(f"Transcription completed. Language: {result.language_code}")
            return result
            
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            raise
    
    async def transcribe_wav_file(self, wav_data: bytes, 
                                language_options: List[str] = None) -> TranscriptionResult:
        """
        Transcribe a WAV file with automatic language detection.
        
        Args:
            wav_data: WAV file data as bytes
            language_options: List of language codes to consider (default: en-US, id-ID)
            
        Returns:
            TranscriptionResult object with transcript and detected language
        """
        try:
            # Process WAV data to ensure it's in the correct format
            logger.info("Processing WAV file format...")
            processed_wav_data = self._process_wav_format(wav_data)
            
            # Use streaming transcription if available
            if self.streaming_client:
                logger.info("Starting streaming transcription...")
                result = await self.transcribe_streaming(processed_wav_data, language_options)
            else:
                logger.info("Streaming not available, using batch transcription...")
                result = self.transcribe_batch(processed_wav_data, language_options)
            
            logger.info(f"Transcription completed. Language: {result.language_code}")
            return result
            
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            raise
    
    def _process_wav_format(self, wav_data: bytes) -> bytes:
        """
        Process WAV data to ensure it's in the correct format for transcription.
        
        Args:
            wav_data: WAV file data as bytes
            
        Returns:
            Processed WAV file data as bytes (16kHz, mono, 16-bit PCM)
        """
        if not PYDUB_AVAILABLE:
            logger.warning("pydub not available. Using WAV file as-is (may cause issues if format is incorrect)")
            return wav_data
        
        try:
            logger.info("Processing WAV file format for streaming transcription...")
            
            # Load WAV from bytes
            audio = AudioSegment.from_wav(io.BytesIO(wav_data))
            
            # Log original format
            logger.info(f"Original audio format: {audio.frame_rate}Hz, {audio.channels} channels, {audio.sample_width*8}-bit")
            
            # Convert to the exact format required by AWS Transcribe streaming
            # 16kHz, mono, 16-bit PCM
            audio = audio.set_frame_rate(16000)
            audio = audio.set_channels(1)  # Mono
            audio = audio.set_sample_width(2)  # 16-bit (2 bytes)
            
            # Ensure it's in PCM format
            audio = audio.normalize()  # Normalize audio levels
            
            logger.info(f"Converted audio format: {audio.frame_rate}Hz, {audio.channels} channels, {audio.sample_width*8}-bit")
            logger.info(f"Audio duration: {len(audio)/1000:.2f} seconds")
            
            # Export to WAV format with specific parameters for streaming
            wav_buffer = io.BytesIO()
            audio.export(
                wav_buffer, 
                format="wav",
                parameters=[
                    "-acodec", "pcm_s16le",  # 16-bit PCM little-endian
                    "-ar", "16000",          # 16kHz sample rate
                    "-ac", "1"               # Mono
                ]
            )
            wav_buffer.seek(0)
            
            processed_data = wav_buffer.read()
            logger.info(f"Processed WAV data size: {len(processed_data)} bytes")
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Failed to process WAV format: {str(e)}")
            logger.error("This might cause transcription issues. Consider using a different audio file.")
            # Return original data as fallback
            return wav_data

def create_transcriber(region: str = "ap-southeast-1") -> AudioTranscriber:
    """
    Factory function to create an AudioTranscriber instance.
    
    Args:
        region: AWS region for Transcribe service
        
    Returns:
        AudioTranscriber instance
    """
    return AudioTranscriber(region=region)

# Example usage
async def example_usage():
    """Example of how to use the AudioTranscriber."""
    transcriber = create_transcriber()
    
    # Read MP3 file
    with open("example.mp3", "rb") as f:
        mp3_data = f.read()
    
    # Transcribe
    result = await transcriber.transcribe_mp3_file(mp3_data)
    
    print(f"Transcript: {result.transcript}")
    print(f"Language: {result.language_code}")
    print(f"Confidence: {result.confidence}")

# Convenience functions for app integration
def transcribe_audio_file_sync(file_path: str, language_options: list = None, region: str = "ap-southeast-1"):
    """
    Synchronous audio transcription using extensions.
    """
    try:
        # Set default language options
        if language_options is None:
            language_options = ["en-US", "id-ID"]
        
        # Create transcriber
        transcriber = create_transcriber(region=region)
        
        # Read the audio file
        with open(file_path, "rb") as f:
            audio_data = f.read()
        
        # Determine file type and transcribe
        file_extension = file_path.lower().split('.')[-1]
        
        # Run async transcription
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        if file_extension == 'mp3':
            result = loop.run_until_complete(transcriber.transcribe_mp3_file(audio_data, language_options))
        elif file_extension == 'wav':
            result = loop.run_until_complete(transcriber.transcribe_wav_file(audio_data, language_options))
        else:
            return {
                "status": "error",
                "message": f"Unsupported file format: {file_extension}",
                "transcript": "",
                "language_code": None,
                "confidence": None,
                "segments": []
            }
        
        loop.close()
        
        return {
            "status": "success",
            "message": f"Successfully transcribed {file_extension.upper()} audio file. Detected language: {result.language_code}",
            "transcript": result.transcript,
            "language_code": result.language_code,
            "confidence": result.confidence,
            "segments": result.segments
        }
        
    except FileNotFoundError:
        return {
            "status": "error",
            "message": f"Audio file not found: {file_path}",
            "transcript": "",
            "language_code": None,
            "confidence": None,
            "segments": []
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Transcription failed: {str(e)}",
            "transcript": "",
            "language_code": None,
            "confidence": None,
            "segments": []
        }

def get_supported_languages():
    """
    Get supported languages for audio transcription.
    """
    return {
        "status": "success",
        "supported_languages": {
            "en-US": "English (United States)",
            "id-ID": "Indonesian (Indonesia)",
            "zh-CN": "Chinese (Simplified)",
            "ja-JP": "Japanese",
            "ko-KR": "Korean",
            "th-TH": "Thai",
            "vi-VN": "Vietnamese"
        },
        "supported_formats": ["mp3", "wav"],
        "default_options": ["en-US", "id-ID"],
        "message": "These are the supported languages and formats for audio transcription"
    }

if __name__ == "__main__":
    asyncio.run(example_usage())
