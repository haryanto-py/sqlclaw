"""
Shared configuration for the skillhub backend.
Resolves all file paths relative to the project root.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Project root is two levels up from skillhub/backend/
PROJECT_ROOT = Path(__file__).parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env", override=True)

# Log file paths
QUERY_LOG = PROJECT_ROOT / "openclaw" / "logs" / "queries.log"
OPENCLAW_LOG = PROJECT_ROOT / "openclaw" / "logs" / "openclaw.log"

# Skills directory
SKILLS_DIR = PROJECT_ROOT / "openclaw" / "skills"

# Database URLs
DATABASE_URL = os.environ.get("DATABASE_URL", "")
READONLY_DB_URL = os.environ.get("READONLY_DB_URL", "")
