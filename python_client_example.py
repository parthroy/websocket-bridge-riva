#!/usr/bin/env python3
"""
WebSocket Bridge Python Client Example

This example demonstrates how to connect to the NVIDIA Riva WebSocket Bridge
and perform real-time speech recognition using the AudioCodes protocol.

Requirements:
    pip install websockets asyncio wave numpy

Usage:
    python python_client_example.py [audio_file.wav]
"""

import asyncio
import websockets
import json
import wave
import time
import sys
import ssl
from typing import Optional, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RivaWebSocketClient:
    """
    Python client for NVIDIA Riva WebSocket Bridge
    Implements the AudioCodes VoiceAI Connect protocol
    """
    
    def __init__(self, 
                 ws_url: str = "wss://localhost:8009",
                 riva_host: Optional[str] = None,
                 riva_port: Optional[int] = None,
                 language: str = "en-US",
                 sample_rate: int = 16000,
                 encoding: str = "LINEAR16",
                 verify_ssl: bool = False):
        """
        Initialize the WebSocket client
        
        Args:
            ws_url: WebSocket bridge URL
            riva_host: Custom Riva server host (optional)
            riva_port: Custom Riva server port (optional)
            language: Language code (e.g., 'en-US', 'es-ES', 'hi-IN')
            sample_rate: Audio sample rate in Hz
            encoding: Audio encoding format
            verify_ssl: Whether to verify SSL certificates
        """
        self.ws_url = ws_url
        self.riva_host = riva_host
        self.riva_port = riva_port
        self.language = language
        self.sample_rate = sample_rate
        self.encoding = encoding
        self.verify_ssl = verify_ssl
        
        self.websocket = None
        self.is_connected = False
        self.is_recording = False
        self.transcripts = []
        
    async def connect(self):
        """Establish WebSocket connection"""
        try:
            # Configure SSL context
            ssl_context = ssl.create_default_context()
            if not self.verify_ssl:
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
            
            logger.info(f"🔌 Connecting to WebSocket: {self.ws_url}")
            self.websocket = await websockets.connect(
                self.ws_url, 
                ssl=ssl_context,
                ping_interval=20,
                ping_timeout=10
            )
            self.is_connected = True
            logger.info("✅ WebSocket connection established")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect: {e}")
            raise
    
    async def start_asr_session(self) -> bool:
        """
        Start ASR session by sending start message
        
        Returns:
            bool: True if session started successfully
        """
        if not self.is_connected:
            raise ConnectionError("WebSocket not connected")
        
        # Build start message
        start_message = {
            "type": "start",
            "language": self.language,
            "format": "raw",
            "encoding": self.encoding,
            "sampleRateHz": self.sample_rate
        }
        
        # Add dynamic Riva connection parameters if provided
        if self.riva_host:
            start_message["rivaHost"] = self.riva_host
            logger.info(f"🎯 Using custom Riva host: {self.riva_host}")
            
        if self.riva_port:
            start_message["rivaPort"] = self.riva_port
            logger.info(f"🎯 Using custom Riva port: {self.riva_port}")
        
        try:
            logger.info(f"📤 Sending start message: {json.dumps(start_message, indent=2)}")
            await self.websocket.send(json.dumps(start_message))
            
            # Wait for confirmation
            response = await self.websocket.recv()
            response_data = json.loads(response)
            
            if response_data.get("type") == "started":
                logger.info("✅ ASR session started successfully")
                self.is_recording = True
                return True
            else:
                logger.error(f"❌ Failed to start session: {response_data}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error starting ASR session: {e}")
            return False
    
    async def stop_asr_session(self):
        """Stop ASR session"""
        if not self.is_recording:
            return
        
        try:
            stop_message = {"type": "stop"}
            logger.info("🛑 Stopping ASR session")
            await self.websocket.send(json.dumps(stop_message))
            
            # Wait for end confirmation
            response = await self.websocket.recv()
            response_data = json.loads(response)
            
            if response_data.get("type") == "end":
                logger.info(f"✅ ASR session ended: {response_data.get('reason', 'Unknown')}")
                self.is_recording = False
            
        except Exception as e:
            logger.error(f"❌ Error stopping ASR session: {e}")
    
    async def send_audio_chunk(self, audio_data: bytes):
        """
        Send binary audio data to the bridge
        
        Args:
            audio_data: Raw audio bytes
        """
        if not self.is_recording:
            logger.warning("⚠️ Cannot send audio - ASR session not active")
            return
        
        try:
            await self.websocket.send(audio_data)
            logger.debug(f"📡 Sent audio chunk: {len(audio_data)} bytes")
            
        except Exception as e:
            logger.error(f"❌ Error sending audio: {e}")
    
    async def listen_for_results(self):
        """
        Listen for transcription results from the bridge
        """
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    await self._handle_message(data)
                    
                except json.JSONDecodeError:
                    logger.warning(f"⚠️ Received non-JSON message: {message}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info("🔌 WebSocket connection closed")
            self.is_connected = False
            self.is_recording = False
            
        except Exception as e:
            logger.error(f"❌ Error listening for results: {e}")
    
    async def _handle_message(self, data: Dict[str, Any]):
        """Handle incoming messages from the bridge"""
        message_type = data.get("type")
        
        if message_type == "started":
            logger.info("🎬 ASR streaming started")
            
        elif message_type == "hypothesis":
            # Interim result
            text = data.get("alternatives", [{}])[0].get("text", "")
            logger.info(f"💭 Interim: {text}")
            
        elif message_type == "recognition":
            # Final result
            text = data.get("alternatives", [{}])[0].get("text", "")
            logger.info(f"✅ Final: {text}")
            self.transcripts.append(text)
            
        elif message_type == "end":
            reason = data.get("reason", "Unknown")
            logger.info(f"🏁 Session ended: {reason}")
            self.is_recording = False
            
        elif message_type == "error":
            error_msg = data.get("message", "Unknown error")
            logger.error(f"❌ Error from server: {error_msg}")
            
        else:
            logger.warning(f"⚠️ Unknown message type: {message_type}")
    
    async def disconnect(self):
        """Close WebSocket connection"""
        if self.websocket:
            await self.websocket.close()
            self.is_connected = False
            self.is_recording = False
            logger.info("🔌 WebSocket disconnected")

async def stream_audio_file(client: RivaWebSocketClient, audio_file_path: str, chunk_size: int = 4096):
    """
    Stream audio file to the WebSocket bridge
    
    Args:
        client: RivaWebSocketClient instance
        audio_file_path: Path to WAV audio file
        chunk_size: Size of audio chunks to send
    """
    try:
        with wave.open(audio_file_path, 'rb') as wav_file:
            # Verify audio format
            channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            framerate = wav_file.getframerate()
            
            logger.info(f"📁 Audio file info:")
            logger.info(f"   - Channels: {channels}")
            logger.info(f"   - Sample width: {sample_width} bytes")
            logger.info(f"   - Frame rate: {framerate} Hz")
            logger.info(f"   - Duration: {wav_file.getnframes() / framerate:.2f} seconds")
            
            if channels != 1:
                logger.warning("⚠️ Audio should be mono (1 channel)")
            if sample_width != 2:
                logger.warning("⚠️ Audio should be 16-bit (2 bytes per sample)")
            if framerate != client.sample_rate:
                logger.warning(f"⚠️ Audio sample rate ({framerate}) differs from client setting ({client.sample_rate})")
            
            # Stream audio data
            frames_per_chunk = chunk_size // sample_width
            total_chunks = wav_file.getnframes() // frames_per_chunk
            
            logger.info(f"🎵 Streaming audio in {total_chunks} chunks...")
            
            for i in range(total_chunks):
                if not client.is_recording:
                    break
                    
                audio_data = wav_file.readframes(frames_per_chunk)
                if not audio_data:
                    break
                
                await client.send_audio_chunk(audio_data)
                
                # Simulate real-time streaming
                await asyncio.sleep(frames_per_chunk / framerate)
                
                if (i + 1) % 10 == 0:
                    logger.info(f"📊 Progress: {i + 1}/{total_chunks} chunks sent")
            
            logger.info("🎵 Audio streaming completed")
            
    except FileNotFoundError:
        logger.error(f"❌ Audio file not found: {audio_file_path}")
    except Exception as e:
        logger.error(f"❌ Error streaming audio: {e}")

async def microphone_simulation():
    """
    Simulate microphone input with dummy audio data
    """
    logger.info("🎤 Simulating microphone input (sending silence)")
    
    # Generate 16-bit mono silence at 16kHz
    sample_rate = 16000
    chunk_duration = 0.1  # 100ms chunks
    samples_per_chunk = int(sample_rate * chunk_duration)
    
    # Create silence (zeros)
    silence_chunk = bytes([0] * (samples_per_chunk * 2))  # 2 bytes per 16-bit sample
    
    return silence_chunk

async def main():
    """Main example function"""
    
    # Configuration
    config = {
        "ws_url": "wss://localhost:8009",
        "riva_host": None,  # Set to custom host if needed
        "riva_port": None,  # Set to custom port if needed
        "language": "en-US",
        "sample_rate": 16000,
        "encoding": "LINEAR16",
        "verify_ssl": False
    }
    
    # Check for audio file argument
    audio_file = sys.argv[1] if len(sys.argv) > 1 else None
    
    if audio_file:
        logger.info(f"🎵 Using audio file: {audio_file}")
    else:
        logger.info("🎤 No audio file provided, will use microphone simulation")
    
    # Create client
    client = RivaWebSocketClient(**config)
    
    try:
        # Connect to WebSocket
        await client.connect()
        
        # Start ASR session
        success = await client.start_asr_session()
        if not success:
            return
        
        # Start listening for results in background
        listen_task = asyncio.create_task(client.listen_for_results())
        
        # Stream audio
        if audio_file:
            await stream_audio_file(client, audio_file)
        else:
            # Simulate microphone for 10 seconds
            logger.info("🎤 Simulating 10 seconds of microphone input...")
            silence_chunk = await microphone_simulation()
            
            for i in range(100):  # 10 seconds of 100ms chunks
                await client.send_audio_chunk(silence_chunk)
                await asyncio.sleep(0.1)
                if not client.is_recording:
                    break
        
        # Wait a bit for final results
        await asyncio.sleep(2)
        
        # Stop ASR session
        await client.stop_asr_session()
        
        # Cancel listening task
        listen_task.cancel()
        
        # Show results
        logger.info("📋 Transcription Results:")
        for i, transcript in enumerate(client.transcripts, 1):
            logger.info(f"   {i}. {transcript}")
        
        if not client.transcripts:
            logger.info("   No transcriptions received")
        
    except KeyboardInterrupt:
        logger.info("⏹️ Interrupted by user")
        
    except Exception as e:
        logger.error(f"❌ Error in main: {e}")
        
    finally:
        await client.disconnect()

if __name__ == "__main__":
    # Example usage with different configurations
    
    print("🚀 NVIDIA Riva WebSocket Bridge - Python Client Example")
    print("=" * 60)
    print()
    print("Usage examples:")
    print("1. Default configuration:")
    print("   python python_client_example.py")
    print()
    print("2. With audio file:")
    print("   python python_client_example.py audio.wav")
    print()
    print("3. Custom configuration (modify config dict in main()):")
    print("   - Set riva_host/riva_port for custom Riva server")
    print("   - Change language, sample_rate, encoding as needed")
    print()
    
    # Run the example
    asyncio.run(main())
