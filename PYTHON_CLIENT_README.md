# Python Client Examples for Riva WebSocket Bridge

This directory contains Python client examples for connecting to the NVIDIA Riva WebSocket Bridge.

## 📋 Requirements

Install the required dependencies:

```bash
pip install websockets asyncio wave numpy
```

Or use the provided requirements file:

```bash
pip install -r requirements_client.txt
```

## 🚀 Quick Start

### 1. Simple Async Client (`simple_python_client.py`)

**Best for:** Quick integration, minimal code

```python
from simple_python_client import SimpleRivaClient
import asyncio

async def main():
    client = SimpleRivaClient()
    
    # Your 16-bit mono PCM audio data
    audio_data = load_your_audio()  # bytes
    
    # Basic transcription
    results = await client.connect_and_transcribe(audio_data)
    print("Transcription:", results)
    
    # With custom Riva server
    results = await client.connect_and_transcribe(
        audio_data,
        riva_url="your-riva-server.com:50052",
        language="es-ES"
    )

asyncio.run(main())
```

### 2. Synchronous Client (`sync_python_client.py`)

**Best for:** Integration into existing synchronous codebases

```python
from sync_python_client import SyncRivaClient

# Create client
client = SyncRivaClient()

# Transcribe audio (blocking call)
results = client.transcribe_audio(
    audio_data,
    riva_url="your-riva-server.com:50052",  # URL format
    language="en-US",
    sample_rate=16000,
    encoding="LINEAR16"
)

print("Transcription results:", results)
```

### 3. Full-Featured Client (`python_client_example.py`)

**Best for:** Production use, streaming, advanced features

```python
from python_client_example import RivaWebSocketClient
import asyncio

async def main():
    client = RivaWebSocketClient(
        ws_url="wss://your-bridge.com:8009",
        riva_url="your-riva-server.com:50052",  # URL format
        language="en-US",
        sample_rate=16000,
        encoding="LINEAR16"
    )
    
    await client.connect()
    await client.start_asr_session()
    
    # Stream audio chunks
    for chunk in audio_chunks:
        await client.send_audio_chunk(chunk)
        await asyncio.sleep(0.1)  # Real-time simulation
    
    await client.stop_asr_session()
    print("Final transcripts:", client.transcripts)

asyncio.run(main())
```

## 🎯 Configuration Options

### WebSocket Bridge Settings

```python
client = SomeClient(
    ws_url="wss://localhost:8009",    # Bridge URL
    verify_ssl=False                  # SSL verification
)
```

### Dynamic Riva Connection

```python
# URL format examples
results = client.transcribe_audio(
    audio_data,
    riva_url="riva-server.example.com:50052",  # Complete URL with port
    language="en-US",
    sample_rate=16000,
    encoding="LINEAR16"
)

# Supported URL formats:
# riva_url="localhost:50051"           # Host with port
# riva_url="riva.company.com:50052"    # Domain with custom port  
# riva_url="10.0.1.100:50051"          # IP address with port
# riva_url="riva-server.example.com"   # Domain only (uses default port 50051)
```

### Supported Languages

```python
language_options = [
    "en-US",  # English (US)
    "en-GB",  # English (UK) 
    "es-ES",  # Spanish
    "fr-FR",  # French
    "de-DE",  # German
    "hi-IN",  # Hindi
    "ja-JP",  # Japanese
    "ko-KR",  # Korean
    # ... and more
]
```

### Supported Audio Formats

```python
encoding_options = [
    "LINEAR16",  # 16-bit PCM (default)
    "MULAW",     # μ-law encoding
    "ALAW",      # A-law encoding
    "FLAC"       # FLAC compression
]

sample_rate_options = [
    8000,   # 8 kHz (telephony)
    16000,  # 16 kHz (default)
    22050,  # 22.05 kHz
    44100   # 44.1 kHz (CD quality)
]
```

## 📡 Message Protocol

### Start Message Format

```json
{
  "type": "start",
  "language": "en-US",
  "format": "raw",
  "encoding": "LINEAR16", 
  "sampleRateHz": 16000,
  "rivaHost": "custom-riva.example.com",  // Optional
  "rivaPort": 50052                       // Optional
}
```

### Response Messages

```json
// Session started
{"type": "started"}

// Interim result
{
  "type": "hypothesis",
  "alternatives": [{"text": "hello wor..."}]
}

// Final result
{
  "type": "recognition", 
  "alternatives": [{"text": "hello world"}]
}

// Session ended
{"type": "end", "reason": "Recognition complete"}

// Stop message
{"type": "stop"}
```

## 🎵 Audio Data Requirements

Your audio data must be:

- **Format**: Raw PCM bytes
- **Channels**: Mono (1 channel)
- **Bit depth**: 16-bit for LINEAR16 encoding
- **Sample rate**: Match the `sampleRateHz` parameter
- **Byte order**: Little-endian

### Converting Audio Files

```python
import wave
import numpy as np

def convert_wav_to_pcm(wav_file_path):
    """Convert WAV file to raw PCM bytes"""
    with wave.open(wav_file_path, 'rb') as wav:
        # Read all frames
        frames = wav.readframes(wav.getnframes())
        
        # Convert to numpy array
        audio_data = np.frombuffer(frames, dtype=np.int16)
        
        # Convert to mono if stereo
        if wav.getnchannels() == 2:
            audio_data = audio_data[::2]  # Take left channel
        
        # Resample if needed (you may need scipy.signal.resample)
        # target_rate = 16000
        # if wav.getframerate() != target_rate:
        #     audio_data = resample(audio_data, target_rate)
        
        return audio_data.tobytes()
```

## 🚀 Running the Examples

### With Default Configuration

```bash
# Async example
python simple_python_client.py

# Sync example  
python sync_python_client.py

# Full example
python python_client_example.py
```

### With Audio File

```bash
python python_client_example.py your_audio.wav
```

### With Custom Bridge URL

```python
# Modify the ws_url in the script
client = SomeClient(ws_url="wss://your-bridge-server.com:8009")
```

## 🔧 Integration into Your Codebase

### For Async Applications

```python
# Add this to your existing async application
from simple_python_client import SimpleRivaClient

class YourApp:
    def __init__(self):
        self.riva_client = SimpleRivaClient()
    
    async def process_audio(self, audio_bytes):
        transcripts = await self.riva_client.connect_and_transcribe(
            audio_bytes,
            riva_url=self.config.riva_url,  # e.g., "riva-server.com:50051"
            language=self.config.language
        )
        return transcripts
```

### For Sync Applications

```python
# Add this to your existing sync application
from sync_python_client import SyncRivaClient

class YourApp:
    def __init__(self):
        self.riva_client = SyncRivaClient()
    
    def process_audio(self, audio_bytes):
        transcripts = self.riva_client.transcribe_audio(
            audio_bytes,
            riva_url=self.config.riva_url,  # e.g., "riva-server.com:50051"
            language=self.config.language
        )
        return transcripts
```

## ⚠️ Important Notes

1. **SSL Certificates**: The bridge uses self-signed certificates by default. Set `verify_ssl=False` for development.

2. **Audio Format**: Ensure your audio is in the correct format (16-bit mono PCM) to avoid transcription issues.

3. **Connection Persistence**: Each transcription creates a new WebSocket connection. For high-frequency usage, consider connection pooling.

4. **Error Handling**: Always wrap calls in try-catch blocks for production use.

5. **Timeouts**: Set appropriate timeouts for your use case to avoid hanging connections.

## 🐛 Troubleshooting

### Connection Issues
```bash
# Test bridge connectivity
curl -k https://localhost:8009

# Check bridge logs
docker logs <bridge-container>
```

### Audio Issues
```python
# Verify audio format
import wave
with wave.open("your_audio.wav", 'rb') as w:
    print(f"Channels: {w.getnchannels()}")      # Should be 1
    print(f"Sample width: {w.getsampwidth()}")  # Should be 2 
    print(f"Frame rate: {w.getframerate()}")    # Should match sampleRateHz
```

### Riva Server Issues
```python
### Riva Server Issues

```python
# Test with default Riva (don't set riva_url)
results = client.transcribe_audio(audio_data)

# Test with custom Riva
results = client.transcribe_audio(
    audio_data, 
    riva_url="your-riva-server:50051"
)
```
```

## 📞 Support

For issues with:
- **WebSocket Bridge**: Check the bridge server logs
- **Riva Connection**: Verify Riva server is running and accessible
- **Audio Processing**: Ensure audio format compliance
- **Python Client**: Check dependencies and error logs
