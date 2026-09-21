from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RESUME_DIR = DATA_DIR / "resumes"
JOB_DESCRIPTION_DIR = DATA_DIR / "job_descriptions"

DEFAULT_ROOT_DIR = os.getenv("ROOT_DIR", str(RESUME_DIR))
DEFAULT_JOB_DESCRIPTION = os.getenv(
    "JOB_DESCRIPTION",
    "Python backend engineer with Flask and SQL",
)

KEYWORDS = ["python", "flask", "sql", "backend", "engineer", "developer"]
