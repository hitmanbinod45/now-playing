import librosa
import numpy as np
from scipy.signal import find_peaks
import io
import sqlalchemy as sa

SAMPLE_RATE = 44100
N_FFT = 4096
HOP_LENGTH = 2048

def generate_fingerprint(audio_data: bytes) -> list:
    # Load audio from bytes
    audio, sr = librosa.load(io.BytesIO(audio_data), sr=SAMPLE_RATE, mono=True)
    
    # Compute spectrogram
    stft = librosa.stft(audio, n_fft=N_FFT, hop_length=HOP_LENGTH)
    spectrogram = np.abs(stft)
    db_spec = librosa.amplitude_to_db(spectrogram, ref=np.max)
    
    # Find spectral peaks
    peaks = []
    for time_idx in range(db_spec.shape[1]):
        freqs = db_spec[:, time_idx]
        peak_indices, _ = find_peaks(freqs, distance=10, prominence=5)
        peaks.extend([(freq_idx, time_idx) for freq_idx in peak_indices])
    
    # Generate hashes
    hashes = set()
    for i, (freq1, time1) in enumerate(peaks):
        for freq2, time2 in peaks[i+1:i+50]:
            time_delta = time2 - time1
            if 1 <= time_delta <= 5:
                hash_val = hash((freq1, freq2, time_delta)) & 0xFFFFFFFF
                hashes.add((hash_val, time1))
    
    return list(hashes)

# Database model would be defined in database.py
# class Fingerprint(Base):
#     __tablename__ = "fingerprints"
#     hash = sa.Column(sa.BigInteger, primary_key=True)
#     time_offset = sa.Column(sa.Integer)
#     song_id = sa.Column(sa.Integer, sa.ForeignKey("songs.id"))