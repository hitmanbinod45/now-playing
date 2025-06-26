from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import asyncio
import numpy as np
import librosa
from typing import List, Dict
import redis
import hashlib
import time

app = FastAPI(title="What's This Song API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # SvelteKit dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis connection for audio fingerprints
redis_client = redis.Redis(host='localhost', port=6379, db=0)

class AudioProcessor:
    def __init__(self):
        self.sample_rate = 22050
        self.hop_length = 512
        
    def extract_features(self, audio_data: np.ndarray) -> Dict:
        """Extract audio features for fingerprinting"""
        # Compute spectral features
        mfccs = librosa.feature.mfcc(y=audio_data, sr=self.sample_rate, n_mfcc=13)
        chroma = librosa.feature.chroma(y=audio_data, sr=self.sample_rate)
        spectral_centroid = librosa.feature.spectral_centroid(y=audio_data, sr=self.sample_rate)
        
        # Create fingerprint hash
        features = np.concatenate([
            np.mean(mfccs, axis=1),
            np.mean(chroma, axis=1),
            np.mean(spectral_centroid, axis=1)
        ])
        
        return {
            'fingerprint': hashlib.md5(features.tobytes()).hexdigest(),
            'mfccs': mfccs.tolist(),
            'chroma': chroma.tolist(),
            'spectral_centroid': spectral_centroid.tolist()
        }
    
    def match_song(self, fingerprint: str) -> Dict:
        """Match fingerprint against database"""
        # Check Redis for existing fingerprints
        stored_songs = redis_client.keys('song:*')
        
        best_match = None
        best_score = 0
        
        for song_key in stored_songs:
            song_data = json.loads(redis_client.get(song_key))
            stored_fingerprint = song_data.get('fingerprint')
            
            # Simple similarity check (in production, use more sophisticated matching)
            similarity = self.calculate_similarity(fingerprint, stored_fingerprint)
            
            if similarity > best_score:
                best_score = similarity
                best_match = song_data
        
        return best_match if best_score > 0.7 else None
    
    def calculate_similarity(self, fp1: str, fp2: str) -> float:
        """Calculate similarity between two fingerprints"""
        # Simple Hamming distance for demo
        if len(fp1) != len(fp2):
            return 0.0
        
        matches = sum(c1 == c2 for c1, c2 in zip(fp1, fp2))
        return matches / len(fp1)

audio_processor = AudioProcessor()

# WebSocket connections manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

manager = ConnectionManager()

@app.get("/")
async def root():
    return {"message": "What's This Song API is running!"}

@app.post("/identify-song")
async def identify_song(file: UploadFile = File(...)):
    """Identify song from uploaded audio file"""
    try:
        # Read audio file
        audio_bytes = await file.read()
        
        # Convert to numpy array (simplified - in production, handle different formats)
        audio_data = np.frombuffer(audio_bytes, dtype=np.float32)
        
        # Extract features and fingerprint
        features = audio_processor.extract_features(audio_data)
        
        # Try to match the song
        match = audio_processor.match_song(features['fingerprint'])
        
        if match:
            return {
                "success": True,
                "song": match,
                "confidence": 0.85  # Mock confidence score
            }
        else:
            return {
                "success": False,
                "message": "Song not found in database",
                "confidence": 0.0
            }
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.websocket("/ws/listen")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time audio streaming"""
    await manager.connect(websocket)
    
    try:
        while True:
            # Receive audio data from client
            data = await websocket.receive_bytes()
            
            # Process audio data
            audio_data = np.frombuffer(data, dtype=np.float32)
            
            if len(audio_data) > 0:
                # Extract features
                features = audio_processor.extract_features(audio_data)
                
                # Try to match
                match = audio_processor.match_song(features['fingerprint'])
                
                if match:
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "match_found",
                            "song": match,
                            "timestamp": time.time()
                        }),
                        websocket
                    )
                else:
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "listening",
                            "message": "Listening..."
                        }),
                        websocket
                    )
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.post("/add-song")
async def add_song(file: UploadFile = File(...), title: str = "", artist: str = ""):
    """Add a song to the database for recognition"""
    try:
        audio_bytes = await file.read()
        audio_data = np.frombuffer(audio_bytes, dtype=np.float32)
        
        # Extract features
        features = audio_processor.extract_features(audio_data)
        
        # Store in Redis
        song_data = {
            "title": title,
            "artist": artist,
            "fingerprint": features['fingerprint'],
            "features": features,
            "added_at": time.time()
        }
        
        song_key = f"song:{features['fingerprint']}"
        redis_client.set(song_key, json.dumps(song_data))
        
        return {
            "success": True,
            "message": f"Song '{title}' by {artist} added successfully",
            "fingerprint": features['fingerprint']
        }
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)