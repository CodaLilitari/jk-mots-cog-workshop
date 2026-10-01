#!/usr/bin/env python3
"""Portable entry point for the public JK/MotS COG Workshop."""
import sys
sys.dont_write_bytecode = True
from tools.workshop import main

if __name__ == "__main__":
    raise SystemExit(main())
