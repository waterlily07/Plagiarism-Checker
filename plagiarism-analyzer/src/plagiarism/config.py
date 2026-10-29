"""Central configuration. Change defaults here, not in modules."""
from pathlib import Path

# --- Algorithm defaults ---
K = 5              # words per k-gram (the "five-word fingerprint")
WINNOW_W = 4       # winnowing window size

# --- Hashing ---
HASH_DIGEST_BYTES = 8   # blake2b digest size -> 64-bit ints

# --- Paths (relative to project root) ---
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "plagiarism.db"
CORPUS_DIR = PROJECT_ROOT / "data" / "corpus"

# --- Text ---
# Shown in every report and in the README so the tool's scope is explicit.
DISCLAIMER = (
    "This tool measures textual similarity against an indexed corpus. "
    "It does NOT determine plagiarism, intent, or originality. "
    "Results are evidence for human review."
)