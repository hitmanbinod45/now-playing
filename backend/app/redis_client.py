import redis

class ValkeyClient:
    def __init__(self):
        self.client = redis.Redis(host='localhost', port=6379, db=0)
    
    def store_fingerprints(self, song_id: int, fingerprints: list):
        pipe = self.client.pipeline()
        for hash_val, offset in fingerprints:
            # Store as sorted set with time offset as score
            pipe.zadd(f"fp:{hash_val}", {f"{song_id}:{offset}": offset})
        pipe.execute()
    
    def find_matches(self, query_prints: list) -> dict:
        matches = {}
        for hash_val, offset in query_prints:
            # Find similar fingerprints within time tolerance
            results = self.client.zrangebyscore(
                f"fp:{hash_val}", 
                offset - 2, 
                offset + 2,
                withscores=True
            )
            for result in results:
                song_id, db_offset = result[0].decode().split(':')
                time_diff = offset - float(db_offset)
                if song_id not in matches:
                    matches[song_id] = {}
                matches[song_id][time_diff] = matches[song_id].get(time_diff, 0) + 1
        return matches