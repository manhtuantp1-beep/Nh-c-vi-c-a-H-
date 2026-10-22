"""Windows desktop entry point; source and frozen builds share the same CLI."""
from nhacviec.__main__ import main

if __name__ == "__main__":
    raise SystemExit(main())
