#!/usr/bin/env python3
"""
Synchronous Python Client for Riva WebSocket Bridge

This version uses threading to provide a synchronous interface
that's easier to integrate into existing Python codebases.
"""

import json
import ssl
import threading
import time
import queue
import logging
from typing import Optional, List, Dict, Any

try:
    import websockets
    import asyncio
except ImportError:
    print("❌ Missing dependencies. Install with:")
    print("pip install websockets asyncio")
    exit(1)

class SyncRivaClient:
    """
    Synchronous wrapper for the Riva WebSocket Bridge client
    """
    
    def __init__(self, ws_url: str = "wss://localhost:8009", verify_ssl: bool = False):
        self.ws_url = ws_url
        self.verify_ssl = verify_ssl
        self.loop = None
        self.thread = None
        self.result_queue = queue.Queue()
        self.error_queue = queue.Queue()
        
    def transcribe_audio(self,
                        audio_data: bytes,
                        riva_host: Optional[str] = None,
                        riva_port: Optional[int] = None,
                        language: str = "en-US",
                        sample_rate: int = 16000,
                        encoding: str = "LINEAR16",
                        timeout: float = 30.0) -> List[str]:
        """
        Synchronous method to transcribe audio
        
        Args:
            audio_data: Raw audio bytes (16-bit mono PCM)
            riva_host: Custom Riva server host
            riva_port: Custom Riva server port
            language: Language code
            sample_rate: Audio sample rate
            encoding: Audio encoding format
            timeout: Maximum time to wait for results
            
        Returns:
            List of transcription results
        """
        
        # Clear previous results
        while not self.result_queue.empty():
            self.result_queue.get()
        while not self.error_queue.empty():
            self.error_queue.get()
        
        # Start async processing in thread
        self.thread = threading.Thread(
            target=self._run_async_transcription,
            args=(audio_data, riva_host, riva_port, language, sample_rate, encoding)
        )
        self.thread.start()
        
        # Wait for results
        try:
            result = self.result_queue.get(timeout=timeout)
            self.thread.join(timeout=1.0)
            return result
            
        except queue.Empty:
            logging.error("Timeout waiting for transcription results")
            return []
            
        except Exception as e:
            try:
                error = self.error_queue.get_nowait()
                logging.error(f"Transcription error: {error}")
            except queue.Empty:
                logging.error(f"Unknown transcription error: {e}")
            return []
    
    def _run_async_transcription(self, audio_data, riva_host, riva_port, language, sample_rate, encoding):
        """Run async transcription in thread"""
        try:
            # Create new event loop for this thread
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            
            # Run transcription
            result = self.loop.run_until_complete(
                self._async_transcribe(audio_data, riva_host, riva_port, language, sample_rate, encoding)
            )
            
            self.result_queue.put(result)
            
        except Exception as e:
            self.error_queue.put(str(e))
            
        finally:
            if self.loop:
                self.loop.close()
    
    async def _async_transcribe(self, audio_data, riva_host, riva_port, language, sample_rate, encoding):
        """Async transcription implementation"""
        
        ssl_context = ssl.create_default_context()
        if not self.verify_ssl:
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
        
        transcripts = []
        
        try:
            async with websockets.connect(self.ws_url, ssl=ssl_context) as websocket:
                
                # Send start message
                start_msg = {
                    "type": "start",
                    "language": language,
                    "format": "raw",
                    "encoding": encoding,
                    "sampleRateHz": sample_rate
                }
                
                if riva_host:
                    start_msg["rivaHost"] = riva_host
                if riva_port:
                    start_msg["rivaPort"] = riva_port
                
                await websocket.send(json.dumps(start_msg))
                
                # Wait for started confirmation
                response = await websocket.recv()
                data = json.loads(response)
                if data.get("type") != "started":
                    raise Exception(f"Failed to start ASR: {data}")
                
                # Send audio in chunks
                chunk_size = 4096
                for i in range(0, len(audio_data), chunk_size):
                    chunk = audio_data[i:i+chunk_size]
                    await websocket.send(chunk)
                    await asyncio.sleep(0.01)
                
                # Send stop message
                await websocket.send(json.dumps({"type": "stop"}))
                
                # Collect results
                while True:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        data = json.loads(message)
                        
                        if data.get("type") == "recognition":
                            text = data.get("alternatives", [{}])[0].get("text", "")
                            if text:
                                transcripts.append(text)
                                
                        elif data.get("type") == "end":
                            break
                            
                    except asyncio.TimeoutError:
                        break
                        
        except Exception as e:
            raise Exception(f"WebSocket transcription failed: {e}")
            
        return transcripts

def create_test_audio(duration_seconds: float = 1.0, sample_rate: int = 16000) -> bytes:
    """
    Create test audio data (silence) for demonstration
    
    Args:
        duration_seconds: Duration of audio
        sample_rate: Sample rate in Hz
        
    Returns:
        Raw audio bytes (16-bit mono PCM)
    """
    samples = int(sample_rate * duration_seconds)
    # Create silence (zeros) - 2 bytes per 16-bit sample
    return bytes([0] * (samples * 2))

def main():
    """Example usage of the synchronous client"""
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    print("🚀 Riva WebSocket Bridge - Synchronous Python Client")
    print("=" * 55)
    
    # Create client
    client = SyncRivaClient(
        ws_url="wss://localhost:8009",
        verify_ssl=False
    )
    
    # Create test audio (1 second of silence)
    audio_data = create_test_audio(duration_seconds=1.0)
    print(f"📊 Generated {len(audio_data)} bytes of test audio")
    
    # Example 1: Basic transcription
    print("\n1️⃣ Basic transcription (default Riva):")
    try:
        results = client.transcribe_audio(audio_data)
        print(f"   Results: {results}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Example 2: Custom Riva server
    print("\n2️⃣ Custom Riva server:")
    try:
        results = client.transcribe_audio(
            audio_data,
            riva_host="custom-riva.example.com",
            riva_port=50052,
            language="es-ES"
        )
        print(f"   Results: {results}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Example 3: Different audio settings
    print("\n3️⃣ Different audio settings:")
    try:
        # Create 8kHz audio
        audio_8k = create_test_audio(duration_seconds=2.0, sample_rate=8000)
        results = client.transcribe_audio(
            audio_8k,
            language="hi-IN",
            sample_rate=8000,
            encoding="LINEAR16"
        )
        print(f"   Results: {results}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n✅ Examples completed!")

if __name__ == "__main__":
    main()
