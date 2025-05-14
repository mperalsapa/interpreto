# Interpreto
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/mperalsapa/interpreto)

Interpreto is a system for transcribing audio and video files. It provides an easy-to-use web interface for uploading media files and automatically generates transcriptions with timestamps. The modular architecture of the project, makes easy to add more functionality, like another interface (for example, a Telegram bot).

## Features
- Upload audio and video files for transcription
- Real-time transcription updates via server-sent events
- Display of transcription alongside media player
- Automatic subtitle generation in WebVTT format
- Language detection for transcripts
- Efficient audio processing with voice activity detection

## Architecture
Interpreto is built using a microservices architecture:

1. Frontend: React-based web interface for uploading files and viewing transcriptions
2. Backend API: FastAPI service that handles file uploads and job management
3. Worker Service: Processes media files using Whisper models and voice detection
4. Storage:
    - MongoDB for storing file metadata and transcriptions
    - MinIO for storing media files
    - Redis for real-time communication between services

## Installation
### Prerequisites
- Docker and Docker Compose
- Python 3.8+
- Node.js 14+
- CUDA-capable GPU (optional, for faster transcription)
## Setup
1. Clone the repository:
```bash
git clone https://github.com/mperalsapa/interpreto.git  
cd interpreto
```
2. Set up the environment variables (or use the defaults in the code):

```# MongoDB config  
MONGO_HOST=localhost  
MONGO_PORT=27017  
MONGO_USER=frontend-service  
MONGO_PASS=frontend-service  
MONGO_DB=media_service  

# MinIO config  
MINIO_HOST=localhost  
MINIO_PORT=9000  
MINIO_ACCESS_KEY=minioadmin  
MINIO_SECRET_KEY=minioadmin  

# Redis config  
REDIS_HOST=localhost  
REDIS_PORT=6379
```

3. Start the services using Docker Compose:
```bash
docker-compose up -d
```

## Usage
1. Open the web application in your browser at http://localhost:8080
2. Upload an audio or video file using the upload form
3. Wait for the transcription to process - you'll see real-time updates
4. View the transcription alongside the media player
5. The transcription will be automatically displayed as subtitles

## Technologies
- Frontend: React
- Backend: FastAPI (Python)
- Speech Recognition: Whisper, faster-whisper
- Voice Activity Detection: Silero VAD
- Storage: MongoDB, MinIO, Redis
- Processing: PyTorch, torchaudio