"""
Audio processing service for validation, conversion, and optimization.
Handles various audio formats and provides preprocessing capabilities.
"""

import io
from typing import Dict, Any
import soundfile as sf
import numpy as np
from pydub import AudioSegment
import imageio_ffmpeg as ffmpeg

from .base import BaseService, AudioProcessorInterface
from ..core.exceptions import AudioProcessingError
from ..core.config import settings


class AudioProcessorService(BaseService, AudioProcessorInterface):
    """Service for audio processing and validation."""
    
    def __init__(self):
        super().__init__()
        self.audio_settings = settings.audio_settings
        # Configure pydub to use imageio-ffmpeg
        self._setup_ffmpeg()
    
    def _setup_ffmpeg(self):
        """Configure pydub to use imageio-ffmpeg binaries."""
        try:
            # Get FFmpeg executable path from imageio-ffmpeg
            ffmpeg_path = ffmpeg.get_ffmpeg_exe()
            AudioSegment.converter = ffmpeg_path
            AudioSegment.ffmpeg = ffmpeg_path
            AudioSegment.ffprobe = ffmpeg_path.replace('ffmpeg', 'ffprobe')
            self.logger.info("FFmpeg configured successfully", path=ffmpeg_path)
        except Exception as e:
            self.logger.warning("Failed to configure FFmpeg", error=str(e))
    
    async def validate_audio(self, audio_data: bytes, format: str) -> bool:
        """
        Validate audio data and format.
        
        Args:
            audio_data: Raw audio bytes
            format: Audio format (wav, mp3, etc.)
            
        Returns:
            True if audio is valid
            
        Raises:
            AudioProcessingError: If audio validation fails
        """
        try:
            self.logger.info("Validating audio", format=format)
            # Check format support
            if format.lower() not in self.audio_settings.supported_formats:
                raise AudioProcessingError(
                    f"Unsupported audio format: {format}",
                    error_code="UNSUPPORTED_FORMAT"
                )
            
            self.logger.info("Audio format supported", format=format)
            # Check file size
            size_mb = len(audio_data) / (1024 * 1024)
            if size_mb > self.audio_settings.max_size_mb:
                raise AudioProcessingError(
                    f"Audio file too large: {size_mb:.2f}MB (max: {self.audio_settings.max_size_mb}MB)",
                    error_code="FILE_TOO_LARGE"
                )
            
            self.logger.info("Audio file size is within the limit", size_mb=size_mb)
            # Try to load the audio to validate format
            audio_segment = AudioSegment.from_file(
                io.BytesIO(audio_data), 
                format=format.lower()
            )
            
            self.logger.info("Audio loaded successfully", format=format)
            # Check duration (optional: add max duration limit)
            duration_seconds = len(audio_segment) / 1000
            if duration_seconds > 300:  # 5 minutes max
                raise AudioProcessingError(
                    f"Audio too long: {duration_seconds:.1f}s (max: 300s)",
                    error_code="AUDIO_TOO_LONG"
                )
            
            self.logger.info("Audio duration is within the limit", duration_seconds=duration_seconds)
            self.logger.info(
                "Audio validation successful",
                format=format,
                size_mb=size_mb,
                duration_seconds=duration_seconds
            )
            
            return True
            
        except AudioProcessingError:
            raise
        except Exception as e:
            self.logger.error("Audio validation failed", error=str(e))
            raise AudioProcessingError(
                f"Audio validation failed: {str(e)}",
                error_code="VALIDATION_ERROR"
            )
    
    async def convert_audio_format(
        self, 
        audio_data: bytes, 
        source_format: str, 
        target_format: str
    ) -> bytes:
        """
        Convert audio from one format to another.
        
        Args:
            audio_data: Source audio bytes
            source_format: Source format (wav, mp3, etc.)
            target_format: Target format
            
        Returns:
            Converted audio bytes
            
        Raises:
            AudioProcessingError: If conversion fails
        """
        try:
            # Load audio
            audio_segment = AudioSegment.from_file(
                io.BytesIO(audio_data),
                format=source_format.lower()
            )
            
            # Optimize audio for speech recognition if converting to wav
            if target_format.lower() == "wav":
                # Resample to optimal rate for speech recognition
                audio_segment = audio_segment.set_frame_rate(self.audio_settings.sample_rate)
                # Convert to mono for better recognition
                audio_segment = audio_segment.set_channels(1)
                # Normalize audio levels
                audio_segment = audio_segment.normalize()
            
            # Export to target format
            output_buffer = io.BytesIO()
            audio_segment.export(output_buffer, format=target_format.lower())
            
            converted_data = output_buffer.getvalue()
            
            self.logger.info(
                "Audio conversion successful",
                source_format=source_format,
                target_format=target_format,
                original_size=len(audio_data),
                converted_size=len(converted_data)
            )
            
            return converted_data
            
        except Exception as e:
            self.logger.error("Audio conversion failed", error=str(e))
            raise AudioProcessingError(
                f"Audio conversion failed: {str(e)}",
                error_code="CONVERSION_ERROR"
            )
    
    async def extract_audio_features(self, audio_data: bytes, format: str) -> Dict[str, Any]:
        """
        Extract features from audio for analysis.
        
        Args:
            audio_data: Audio bytes
            format: Audio format
            
        Returns:
            Dictionary with audio features
        """
        try:
            audio_segment = AudioSegment.from_file(
                io.BytesIO(audio_data),
                format=format.lower()
            )
            
            # Convert to numpy array for analysis
            samples = np.array(audio_segment.get_array_of_samples())
            if audio_segment.channels == 2:
                samples = samples.reshape((-1, 2))
                samples = samples.mean(axis=1)  # Convert to mono
            
            # Extract basic features
            features = {
                "duration_seconds": len(audio_segment) / 1000,
                "sample_rate": audio_segment.frame_rate,
                "channels": audio_segment.channels,
                "bit_depth": audio_segment.sample_width * 8,
                "rms_energy": float(np.sqrt(np.mean(samples ** 2))),
                "zero_crossing_rate": float(np.mean(np.diff(np.sign(samples)) != 0)),
                "max_amplitude": float(np.max(np.abs(samples))),
                "silence_ratio": float(np.sum(np.abs(samples) < 0.01) / len(samples))
            }
            
            self.logger.info("Audio features extracted", features=features)
            return features
            
        except Exception as e:
            self.logger.error("Feature extraction failed", error=str(e))
            raise AudioProcessingError(
                f"Feature extraction failed: {str(e)}",
                error_code="FEATURE_EXTRACTION_ERROR"
            )
    
    async def preprocess_for_speech_recognition(
        self, 
        audio_data: bytes, 
        format: str
    ) -> bytes:
        """
        Preprocess audio for optimal speech recognition.
        
        Args:
            audio_data: Raw audio bytes
            format: Audio format
            
        Returns:
            Preprocessed audio bytes in WAV format
        """
        try:
            # Load audio
            audio_segment = AudioSegment.from_file(
                io.BytesIO(audio_data),
                format=format.lower()
            )
            
            # Apply preprocessing steps
            # 1. Convert to mono
            if audio_segment.channels > 1:
                audio_segment = audio_segment.set_channels(1)
            
            # 2. Resample to optimal rate
            audio_segment = audio_segment.set_frame_rate(self.audio_settings.sample_rate)
            
            # 3. Normalize volume
            audio_segment = audio_segment.normalize()
            
            # 4. Apply noise reduction (simple high-pass filter)
            # Remove very low frequencies that are typically noise
            audio_segment = audio_segment.high_pass_filter(80)
            
            # 5. Apply compression to reduce dynamic range
            audio_segment = audio_segment.compress_dynamic_range(threshold=-20.0, ratio=4.0)
            
            # Export as WAV
            output_buffer = io.BytesIO()
            audio_segment.export(output_buffer, format="wav")
            
            preprocessed_data = output_buffer.getvalue()
            
            self.logger.info(
                "Audio preprocessing completed",
                original_size=len(audio_data),
                preprocessed_size=len(preprocessed_data)
            )
            
            return preprocessed_data
            
        except Exception as e:
            self.logger.error("Audio preprocessing failed", error=str(e))
            raise AudioProcessingError(
                f"Audio preprocessing failed: {str(e)}",
                error_code="PREPROCESSING_ERROR"
            )
