import os
import sys
from pathlib import Path

os.environ["COMICCRAFT_MOCK"] = "1"  # offline: no API keys, no GPU
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
