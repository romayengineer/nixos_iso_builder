#!/usr/bin/env python3
"""
NixOS Debug ISO Build Script - Wrapper for nixos_iso_builder package

This is a backward-compatible entry point that delegates to the modularized
nixos_iso_builder package.

Usage: ./build.py <command> [args]
Commands: build, clean, test, inspect, burn-help, help
"""

import sys

from nixos_iso_builder import main

if __name__ == "__main__":
    sys.exit(main())
