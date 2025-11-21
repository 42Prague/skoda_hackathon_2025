import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent

DATA_DIR = Path(os.getenv("DATA_DIR", PROJECT_ROOT / "data")).resolve()
DB_DIR = Path(os.getenv("DB_DIR", PROJECT_ROOT / "volumes" / "talent-db")).resolve()
DB_PATH = Path(os.getenv("DATABASE_PATH", DB_DIR / "talent_matching.db")).resolve()
EMPLOYEES_CSV = Path(os.getenv("EMPLOYEES_CSV", DATA_DIR / "employees_dataset.csv")).resolve()
JOBS_CSV = Path(os.getenv("JOBS_CSV", DATA_DIR / "jobs_dataset.csv")).resolve()
COURSES_CSV = Path(os.getenv("COURSES_CSV", DATA_DIR / "courses_dataset.csv")).resolve()
SENTENCE_TRANSFORMER_MODEL = os.getenv("SENTENCE_TRANSFORMER_MODEL", "all-MiniLM-L6-v2")

DB_DIR.mkdir(parents=True, exist_ok=True)
