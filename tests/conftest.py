import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Load .env at collection time so pytest.mark.skipif markers that gate on
# environment variables (e.g. ANTHROPIC_API_KEY) see them.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")
