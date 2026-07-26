╔═══════════════════════════════════════════════════════════════════════════╗
║           NixOS Debug ISO Build Script - Help                             ║
╚═══════════════════════════════════════════════════════════════════════════╝

USAGE
━━━━━
  ./build.py <command> [args]

COMMANDS
━━━━━━━━
  build           Build the custom NixOS ISO with debug logging
  clean           Remove build artifacts (result/, mnt/)
  test            Boot ISO in QEMU for testing (requires QEMU)
  inspect         Mount and inspect ISO contents
  burn-help       Show detailed USB burning instructions
  help            Display this help message

EXAMPLES
━━━━━━━━
  # Build the ISO (first: 15-30 min, subsequent: 5-10 min)
  ./build.py build

  # Test the ISO in QEMU
  ./build.py test

  # Inspect what's inside the ISO
  ./build.py inspect

  # Get USB burning instructions
  ./build.py burn-help

  # Remove build artifacts to start fresh
  ./build.py clean

WORKFLOW
━━━━━━━
  1. Build:      ./build.py build
  2. Inspect:    ./build.py inspect
  3. Test:       ./build.py test
  4. Burn:       ./build.py burn-help    (then follow instructions)
  5. Boot & Debug: Boot from USB, run 'journalctl --boot --all'

NOTES
━━━━━
  • First build requires internet (downloads nixpkgs dependencies)
  • Subsequent builds are much faster (uses cache)
  • ISO size: ~900MB
  • Build space needed: ~15GB
  • Nix must be installed: https://nixos.org/download/
