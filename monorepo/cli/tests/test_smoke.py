from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SHARED = ROOT / "shared"
if str(SHARED) not in sys.path:
	sys.path.insert(0, str(SHARED))

from langextract.schemas import ensure_extraction_shape  # type: ignore


def test_ensure_extraction_shape_handles_invalid():
	assert ensure_extraction_shape({}) == {"entities": [], "relationships": []}
	assert ensure_extraction_shape({"entities": [{"name": "X", "type": "PERSON"}]})["entities"][0]["name"] == "X"
