"""Development entry point for NeoEng-D-Trace."""

from src.launcher import build_parser, main, run_headless

__all__ = ["build_parser", "main", "run_headless"]

if __name__ == "__main__":
    raise SystemExit(main())
