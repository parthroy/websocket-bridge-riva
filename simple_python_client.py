#!/usr/bin/env python3
"""
Simple Python Client for Riva WebSocket Bridge

Minimal example for quick integration into your Python codebase.
"""

import asyncio
import websockets
import json
import ssl
import logging

class SimpleRivaClient:
    def __init__(self, ws_url="wss://localhost:8009", verify_ssl=False):
        self.ws_url = ws_url
        self.verify_ssl = verify_ssl
        self.websocket = None
        
    async def connect_and_transcribe(self, 
                                   audio_data, 
                                   riva_host=None, 
                                   riva_port=None,
                                   language="en-US",
                                   sample_rate=16000,
                                   encoding="LINEAR16"):
        """
        Connect, send audio, and get transcription
        
        Args:
            audio_data: bytes - Raw audio data (16-bit mono PCM)
            riva_host: str - Custom Riva server host (optional)
            riva_port: int - Custom Riva server port (optional)
            language: str - Language code
            sample_rate: int - Audio sample rate
            encoding: str - Audio encoding format
            
        Returns:
            list: Final transcription results
        """
        
        # SSL context for self-signed certificates
        ssl_context = ssl.create_default_context()
        if not self.verify_ssl:
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
        
        transcripts = []
        
        try:
            # Connect
            async with websockets.connect(self.ws_url, ssl=ssl_context) as websocket:
                
                # 1. Send start message
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
                
                # 2. Wait for started confirmation
                response = await websocket.recv()
                data = json.loads(response)
                if data.get("type") != "started":
                    raise Exception(f"Failed to start ASR: {data}")
                
                # 3. Send audio data in chunks
                chunk_size = 4096
                for i in range(0, len(audio_data), chunk_size):
                    chunk = audio_data[i:i+chunk_size]
                    await websocket.send(chunk)
                    await asyncio.sleep(0.01)  # Small delay for real-time simulation
                
                # 4. Send stop message
                await websocket.send(json.dumps({"type": "stop"}))
                
                # 5. Collect results
                while True:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        data = json.loads(message)
                        
                        if data.get("type") == "recognition":
                            text = data.get("alternatives", [{}])[0].get("text", "")
                            transcripts.append(text)
                            
                        elif data.get("type") == "end":
                            break
                            
                    except asyncio.TimeoutError:
                        break
                        
        except Exception as e:
            logging.error(f"Error in transcription: {e}")
            
        return transcripts

# Example usage
async def example():
    client = SimpleRivaClient()
    
    # Example: Create dummy 16-bit mono audio (1 second of silence)
    sample_rate = 16000
    duration = 1.0
    samples = int(sample_rate * duration)
    audio_bytes = bytes([0] * (samples * 2))  # 2 bytes per 16-bit sample
    
    # Transcribe with default Riva
    results = await client.connect_and_transcribe(audio_bytes)
    print("Default Riva results:", results)
    
    # Transcribe with custom Riva server
    results = await client.connect_and_transcribe(
        audio_bytes,
        riva_host="custom-riva.example.com",
        riva_port=50052,
        language="es-ES"
    )
    print("Custom Riva results:", results)

if __name__ == "__main__":
    asyncio.run(example())
