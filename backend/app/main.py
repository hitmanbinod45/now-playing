from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import identify, songs

app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(identify.router, prefix="/identify")
app.include_router(songs.router, prefix="/songs")

@app.get("/")
def health_check():
    return {"status": "running"}