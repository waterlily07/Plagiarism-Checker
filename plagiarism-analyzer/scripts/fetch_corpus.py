"""Download Project Gutenberg books using Windows curl."""
from pathlib import Path
import subprocess
import time

BOOK_IDS = [1342, 84, 11, 1661, 2701, 98, 1232, 2600, 174, 345]

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