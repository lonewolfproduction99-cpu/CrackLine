# Single source of truth for Phase 1 hand-designed obstacle chunks.
# Each chunk is 640 px tall; y is local (0 = top of chunk, 640 = bottom), x is screen x (0..720).
LANE_W = 720 / 7
def lane(i): return round(LANE_W * (i + 0.5), 1)
S, M = 'RockSmall', 'RockMedium'
CHUNK_HEIGHT = 640
CHUNKS = [
    # Chunk0: empty warm-up
    [],
    # Chunk1: single rock dead centre (teaches the first dodge)
    [(M, lane(3), 320)],
    # Chunk2: two separated rocks
    [(M, lane(0), 320), (M, lane(4), 320)],
    # Chunk3: small debris cluster on the right + a lone pebble on the left
    [(S, lane(4), 240), (S, lane(5), 280), (S, lane(5) + 40, 220), (S, lane(1), 520)],
    # Chunk4: wall with a 2-lane gap in the middle-right
    [(M, lane(0), 300), (M, lane(1), 300), (M, lane(2), 300), (M, lane(5), 300), (M, lane(6), 300)],
    # Chunk5: alternating left/right hazards
    [(S, lane(1), 80), (S, lane(5), 280), (S, lane(2), 480)],
    # Chunk6: wall, gap on the left
    [(M, lane(2), 420), (M, lane(3), 420), (M, lane(4), 420), (M, lane(5), 420), (M, lane(6), 420)],
    # Chunk7: wall, gap on the right (forces a long traverse from chunk6)
    [(M, lane(0), 180), (M, lane(1), 180), (M, lane(2), 180), (M, lane(3), 180), (M, lane(4), 180)],
    # Chunk8: mixed scatter
    [(M, lane(3), 150), (S, lane(0), 430), (S, lane(6), 430), (S, lane(3), 600)],
]
HIT_RADIUS = {S: 28, M: 44}
IMAGE_SIZE = {S: 76, M: 116}   # radius of the collision polygon used in game.json
