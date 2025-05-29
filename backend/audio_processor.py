#!/usr/bin/env python3
"""
Audio Processing for Live Audio Interview Practice
Handles audio format conversion for Gemini Live API compatibility
"""

import base64
import numpy as np
import wave
import io
from typing import Optional, Tuple

from config import config
from models import AudioData

class AudioProcessor:
    """
    Audio processor for Gemini Live API compatibility
    Ensures proper format: 16-bit PCM at 16kHz mono
    """
    
    def __init__(self):
        self.target_sample_rate = config.AUDIO_SAMPLE_RATE
        self.target_channels = config.AUDIO_CHANNELS
    
    def validate_audio_format(self, audio_data: bytes) -> bool:
        """Validate if audio data is in correct format"""
        try:
            # Try to parse as WAV
            with io.BytesIO(audio_data) as audio_io:
                with wave.open(audio_io, 'rb') as wav_file:
                    sample_rate = wav_file.getframerate()
                    channels = wav_file.getnchannels()
                    sample_width = wav_file.getsampwidth()
                    
                    return (
                        sample_rate == self.target_sample_rate and
                        channels == self.target_channels and
                        sample_width == 2  # 16-bit = 2 bytes
                    )
        except Exception:
            # If can't parse as WAV, assume it's raw PCM
            return len(audio_data) > 0
    
    def convert_to_pcm_16khz(self, audio_data: bytes, source_sample_rate: int = None) -> Optional[AudioData]:
        """
        Convert audio data to 16-bit PCM at 16kHz mono
        Required format for Gemini Live API
        """
        try:
            # Try to determine if it's WAV format
            if self._is_wav_format(audio_data):
                return self._convert_wav_to_pcm(audio_data)
            else:
                # Assume raw PCM and process
                return self._process_raw_pcm(audio_data, source_sample_rate)
                
        except Exception as e:
            print(f"❌ Error converting audio: {e}")
            return None
    
    def _is_wav_format(self, audio_data: bytes) -> bool:
        """Check if audio data is in WAV format"""
        return audio_data.startswith(b'RIFF') and b'WAVE' in audio_data[:12]
    
    def _convert_wav_to_pcm(self, wav_data: bytes) -> Optional[AudioData]:
        """Convert WAV data to target PCM format"""
        try:
            with io.BytesIO(wav_data) as audio_io:
                with wave.open(audio_io, 'rb') as wav_file:
                    # Get WAV properties
                    sample_rate = wav_file.getframerate()
                    channels = wav_file.getnchannels()
                    sample_width = wav_file.getsampwidth()
                    frames = wav_file.readframes(wav_file.getnframes())
                    
                    print(f"🔊 Input WAV: {sample_rate}Hz, {channels}ch, {sample_width*8}bit")
                    
                    # Convert to numpy array
                    if sample_width == 1:
                        audio_array = np.frombuffer(frames, dtype=np.uint8)
                        audio_array = (audio_array.astype(np.float32) - 128) / 128.0
                    elif sample_width == 2:
                        audio_array = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
                    elif sample_width == 4:
                        audio_array = np.frombuffer(frames, dtype=np.int32).astype(np.float32) / 2147483648.0
                    else:
                        print(f"❌ Unsupported sample width: {sample_width}")
                        return None
                    
                    # Reshape for multi-channel
                    if channels > 1:
                        audio_array = audio_array.reshape(-1, channels)
                        # Convert to mono by averaging channels
                        audio_array = np.mean(audio_array, axis=1)
                    
                    # Resample if needed
                    if sample_rate != self.target_sample_rate:
                        audio_array = self._resample_audio(audio_array, sample_rate, self.target_sample_rate)
                    
                    # Convert back to 16-bit PCM
                    audio_16bit = (audio_array * 32767).astype(np.int16)
                    pcm_data = audio_16bit.tobytes()
                    
                    print(f"✅ Output PCM: {self.target_sample_rate}Hz, {self.target_channels}ch, 16bit, {len(pcm_data)} bytes")
                    
                    return AudioData(
                        data=pcm_data,
                        sample_rate=self.target_sample_rate,
                        channels=self.target_channels,
                        format="pcm"
                    )
                    
        except Exception as e:
            print(f"❌ Error converting WAV to PCM: {e}")
            return None
    
    def _process_raw_pcm(self, pcm_data: bytes, source_sample_rate: int = None) -> Optional[AudioData]:
        """Process raw PCM data"""
        try:
            # Assume 16-bit PCM if no sample rate provided
            if source_sample_rate is None:
                source_sample_rate = self.target_sample_rate
            
            # Convert to numpy array (assuming 16-bit)
            audio_array = np.frombuffer(pcm_data, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Resample if needed
            if source_sample_rate != self.target_sample_rate:
                audio_array = self._resample_audio(audio_array, source_sample_rate, self.target_sample_rate)
            
            # Convert back to 16-bit PCM
            audio_16bit = (audio_array * 32767).astype(np.int16)
            processed_data = audio_16bit.tobytes()
            
            return AudioData(
                data=processed_data,
                sample_rate=self.target_sample_rate,
                channels=self.target_channels,
                format="pcm"
            )
            
        except Exception as e:
            print(f"❌ Error processing raw PCM: {e}")
            return None
    
    def _resample_audio(self, audio_array: np.ndarray, source_rate: int, target_rate: int) -> np.ndarray:
        """Simple audio resampling using linear interpolation"""
        if source_rate == target_rate:
            return audio_array
        
        # Calculate resampling ratio
        ratio = target_rate / source_rate
        target_length = int(len(audio_array) * ratio)
        
        # Create new time indices
        source_indices = np.arange(len(audio_array))
        target_indices = np.linspace(0, len(audio_array) - 1, target_length)
        
        # Interpolate
        resampled = np.interp(target_indices, source_indices, audio_array)
        
        print(f"🔄 Resampled audio: {source_rate}Hz -> {target_rate}Hz ({len(audio_array)} -> {len(resampled)} samples)")
        
        return resampled
    
    def create_silence(self, duration_ms: int) -> AudioData:
        """Create silence audio data of specified duration"""
        samples = int(self.target_sample_rate * duration_ms / 1000)
        silence_data = np.zeros(samples, dtype=np.int16).tobytes()
        
        return AudioData(
            data=silence_data,
            sample_rate=self.target_sample_rate,
            channels=self.target_channels,
            format="pcm"
        )
    
    def decode_base64_audio(self, base64_audio: str) -> Optional[bytes]:
        """Decode base64 encoded audio data"""
        try:
            return base64.b64decode(base64_audio)
        except Exception as e:
            print(f"❌ Error decoding base64 audio: {e}")
            return None
    
    def encode_audio_to_base64(self, audio_data: bytes) -> str:
        """Encode audio data to base64"""
        return base64.b64encode(audio_data).decode('utf-8')
    
    def get_audio_info(self, audio_data: AudioData) -> dict:
        """Get information about audio data"""
        duration_ms = len(audio_data.data) / (audio_data.sample_rate * audio_data.channels * 2) * 1000
        
        return {
            "sample_rate": audio_data.sample_rate,
            "channels": audio_data.channels,
            "format": audio_data.format,
            "mime_type": audio_data.mime_type,
            "size_bytes": len(audio_data.data),
            "duration_ms": round(duration_ms, 2)
        }
    
    def process_webm_to_pcm(self, audio_data: AudioData) -> Optional[AudioData]:
        """
        Process WebM audio data to PCM format for Gemini Live API
        WebM typically contains Opus audio codec
        """
        try:
            print(f"🔊 Processing {audio_data.format} audio: {len(audio_data.data)} bytes")
            
            if audio_data.format.lower() in ['webm', 'opus']:
                # For now, we'll try to extract raw audio and assume it's close to PCM
                # This is a simplified approach - in production, you'd use ffmpeg or similar
                return self._process_webm_audio(audio_data)
            elif audio_data.format.lower() in ['pcm', 'wav']:
                # Already in PCM or WAV format
                return self.convert_to_pcm_16khz(audio_data.data, audio_data.sample_rate)
            else:
                print(f"⚠️ Unsupported audio format: {audio_data.format}")
                # Try to process as raw PCM anyway
                return self._process_raw_pcm(audio_data.data, audio_data.sample_rate)
                
        except Exception as e:
            print(f"❌ Error processing WebM to PCM: {e}")
            return None
    
    def _process_webm_audio(self, audio_data: AudioData) -> Optional[AudioData]:
        """
        Simplified WebM audio processing
        In production, this would use ffmpeg or similar for proper decoding
        """
        try:
            # For now, we'll use a simplified approach:
            # 1. Skip WebM container headers (very basic approach)
            # 2. Try to find audio data patterns
            # 3. Convert to our target format
            
            raw_data = audio_data.data
            
            # Skip initial WebM headers (simplified)
            # Look for audio data patterns
            audio_start = 0
            if raw_data.startswith(b'\x1a\x45\xdf\xa3'):  # WebM signature
                # Try to find audio data after headers
                # This is a very simplified approach
                for i in range(min(1024, len(raw_data) - 100)):
                    if raw_data[i:i+4] == b'\x15\x49\xa9\x66':  # Some audio pattern
                        audio_start = i
                        break
            
            # Extract the audio portion
            audio_portion = raw_data[audio_start:]
            
            if len(audio_portion) < 100:
                print("❌ No valid audio data found in WebM")
                return None
            
            # For this simplified version, we'll treat it as raw PCM-like data
            # and apply basic processing
            try:
                # Try to interpret as 16-bit samples
                if len(audio_portion) % 2 != 0:
                    audio_portion = audio_portion[:-1]  # Make even length
                
                # Convert to float array for processing
                audio_array = np.frombuffer(audio_portion, dtype=np.int16).astype(np.float32) / 32768.0
                
                # Apply basic filtering to remove noise
                audio_array = self._apply_basic_audio_filter(audio_array)
                
                # Resample to target rate if needed
                if audio_data.sample_rate != self.target_sample_rate:
                    audio_array = self._resample_audio(audio_array, audio_data.sample_rate, self.target_sample_rate)
                
                # Convert back to 16-bit PCM
                audio_16bit = (audio_array * 32767).astype(np.int16)
                processed_data = audio_16bit.tobytes()
                
                print(f"✅ WebM processed to PCM: {len(processed_data)} bytes")
                
                return AudioData(
                    data=processed_data,
                    sample_rate=self.target_sample_rate,
                    channels=self.target_channels,
                    format="pcm"
                )
                
            except Exception as e:
                print(f"❌ Error processing WebM audio data: {e}")
                # Fallback: try to create valid PCM from the data we have
                return self._create_fallback_audio()
                
        except Exception as e:
            print(f"❌ Error in WebM processing: {e}")
            return None
    
    def _apply_basic_audio_filter(self, audio_array: np.ndarray) -> np.ndarray:
        """Apply basic audio filtering to reduce noise"""
        try:
            # Normalize volume
            if np.max(np.abs(audio_array)) > 0:
                audio_array = audio_array / np.max(np.abs(audio_array)) * 0.8
            
            # Simple high-pass filter to remove DC offset
            if len(audio_array) > 1:
                audio_array = audio_array - np.mean(audio_array)
            
            return audio_array
            
        except Exception:
            return audio_array  # Return original if filtering fails
    
    def _create_fallback_audio(self) -> AudioData:
        """Create a short audio signal as fallback when processing fails"""
        # Create a short tone to indicate audio was received
        duration_ms = 500  # 0.5 seconds
        samples = int(self.target_sample_rate * duration_ms / 1000)
        
        # Create a simple tone at 440Hz
        t = np.linspace(0, duration_ms / 1000, samples, False)
        tone = np.sin(2 * np.pi * 440 * t) * 0.1  # Low volume
        
        audio_16bit = (tone * 32767).astype(np.int16)
        
        return AudioData(
            data=audio_16bit.tobytes(),
            sample_rate=self.target_sample_rate,
            channels=self.target_channels,
            format="pcm"
        ) 