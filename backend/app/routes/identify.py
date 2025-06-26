from fastapi import APIRouter, UploadFile, File
from app.fingerprint import generate_fingerprint
from app.redis_client import ValkeyClient
from app.database import SessionLocal
from app.schemas import IdentificationResult
import io

router = APIRouter()
valkey = ValkeyClient()

@router.post("/", response_model=IdentificationResult)
async def identify_song(file: UploadFile = File(...)):
    # Read audio file
    audio_data = await file.read()
    
    # Generate fingerprints
    query_prints = generate_fingerprint(audio_data)
    
    # Find matches in Valkey
    matches = valkey.find_matches(query_prints)
    
    # Find best matching song
    best_song_id = None
    best_score = 0
    for song_id, offsets in matches.items():
        max_count = max(offsets.values(), default=0)
        if max_count > best_score:
            best_score = max_count
            best_song_id = song_id
    
    # Get song details from PostgreSQL
    db = SessionLocal()
    song = db.execute(
        sa.select(Song).where(Song.id == best_song_id)
    ).scalar_one_or_none()
    
    return {
        "match": bool(song),
        "song": {
            "title": song.title,
            "artist": song.artist,
            "spotify_id": song.spotify_id,
            "confidence": best_score / len(query_prints)
        } if song else None
    }