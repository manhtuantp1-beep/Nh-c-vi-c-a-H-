"""Run the packaged UI verification from a source checkout.

For the Windows release, the build workflow invokes the frozen executable's
--capture-ui command so its DPI manifest and embedded runtime are exercised.
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nhacviec.ui_preview import main


if __name__ == "__main__":
    raise SystemExit(main())
