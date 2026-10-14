"""Entry point para ``python -m autocomplete``."""

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from autocomplete.interfaces.cli import main
else:
    from .interfaces.cli import main


if __name__ == "__main__":
    sys.exit(main())