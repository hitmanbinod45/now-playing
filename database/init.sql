-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Songs table
CREATE TABLE songs (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    artist VARCHAR(255) NOT NULL,
    album VARCHAR(255),
    duration INTEGER,
    fingerprint_hash VARCHAR(64) UNIQUE NOT NULL,
    audio_features JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Search history
CREATE TABLE search_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    song_id INTEGER REFERENCES songs(id),
    confidence_score FLOAT,
    search_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Usage statistics
CREATE TABLE usage_stats (
    id SERIAL PRIMARY KEY,
    date DATE DEFAULT CURRENT_DATE,
    total_searches INTEGER DEFAULT 0,
    successful_matches INTEGER DEFAULT 0,
    unique_users INTEGER DEFAULT 0
);

-- Insert sample songs for testing
INSERT INTO songs (title, artist, album, fingerprint_hash, audio_features) VALUES 
('Shape of You', 'Ed Sheeran', '÷ (Divide)', 'sample_hash_1', '{}'),
('Blinding Lights', 'The Weeknd', 'After Hours', 'sample_hash_2', '{}'),
('Dance Monkey', 'Tones and I', 'The Kids Are Coming', 'sample_hash_3', '{}');