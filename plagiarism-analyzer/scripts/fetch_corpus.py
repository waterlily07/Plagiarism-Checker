"""Download Project Gutenberg books using Windows curl."""
from pathlib import Path
import subprocess
import time

BOOK_IDS = [
    # Original 10
    1342, 84, 11, 1661, 2701, 98, 1232, 2600, 174, 345,
    # Classic literature
    5200, 2554, 1399, 28054, 1080, 16328, 205, 45, 76, 158,
    1400, 145, 120, 219, 1260, 244, 768, 834, 829, 514,
    # Science and philosophy
    2009, 4217, 4280, 5827, 3207, 3600, 3777, 3800, 4000, 4010,
    # History and biography
    2448, 2475, 3398, 3490, 3500, 3600, 4000, 5000, 6000, 7000,
    # More classics
    1184, 1998, 2021, 2028, 2538, 2814, 3010, 3535, 4300, 5410,
    # Shakespeare, Dickens, etc.
    1513, 1535, 2246, 23042, 2449, 2518, 2539, 2620, 2795, 2852,
    # Add 30 more from browsing gutenberg.org
    3020, 3200, 3300, 3500, 4000, 4200, 4400, 4600, 4800, 5000,
    5100, 5200, 5300, 5400, 5500, 5600, 5700, 5800, 5900, 6000,
    6100, 6200, 6300, 6400, 6500, 6600, 6700, 6800, 6900, 7000,
]

DEST = Path("data/corpus")
DEST.mkdir(parents=True, exist_ok=True)

print(f"Fetching {len(BOOK_IDS)} books via curl...")
ok = 0
for bid in BOOK_IDS:
    out = DEST / f"gutenberg_{bid}.txt"
    if out.exists() and out.stat().st_size > 1000:
        print(f"[skip] {out.name} already exists")
        ok += 1
        continue

    url = f"https://www.gutenberg.org/cache/epub/{bid}/pg{bid}.txt"
    try:
        result = subprocess.run(
            ["curl", "-L", "-s", "-o", str(out), url],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0 and out.exists() and out.stat().st_size > 1000:
            print(f"[ok]   {out.name}  ({out.stat().st_size:,} bytes)")
            ok += 1
        else:
            print(f"[fail] {bid}: curl returned {result.returncode}")
    except Exception as e:
        print(f"[fail] {bid}: {e}")
    time.sleep(2)

print(f"Done. {ok}/{len(BOOK_IDS)} books saved to {DEST}")