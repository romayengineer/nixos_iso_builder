#!/bin/bash
# NixOS Debug ISO Build Script
# Usage: ./build.sh <command> [args]
# Commands: build, clean, test, inspect, burn-help, help

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

log_info() {
    echo -e "${BLUE}ℹ${NC} $*"
}

log_success() {
    echo -e "${GREEN}✅${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}⚠${NC}  $*"
}

log_error() {
    echo -e "${RED}✗${NC}  $*"
}

iso_path() {
    ls -1 "$SCRIPT_DIR/result/iso/nixos-"*.iso 2>/dev/null | head -1 || echo ""
}

# ============================================================================
# BUILD FUNCTIONS
# ============================================================================

build() {
    log_info "Building NixOS ISO with debug logging..."
    log_info "First build: 15-30 minutes | Subsequent builds: 5-10 minutes"
    echo ""
    
    if ! command -v nix &> /dev/null; then
        log_error "Nix not found in PATH"
        log_info "Install Nix: https://nixos.org/download/"
        return 1
    fi
    
    cd "$SCRIPT_DIR"
    nix build --extra-experimental-features "nix-command flakes" .#bootDebugISO.config.system.build.isoImage
    
    echo ""
    local iso=$(iso_path)
    if [[ -n "$iso" ]]; then
        log_success "Build complete!"
        log_info "ISO location: $iso"
        ls -lh "$iso"
    else
        log_error "ISO file not found after build"
        return 1
    fi
}

clean() {
    log_info "Cleaning build artifacts..."
    cd "$SCRIPT_DIR"
    
    rm -rf result result-* mnt/ 2>/dev/null || true
    
    log_success "Cleanup complete"
}

test_qemu() {
    log_info "Testing ISO in QEMU..."
    
    if ! command -v qemu-system-x86_64 &> /dev/null; then
        log_error "QEMU not found"
        log_info "Install QEMU: sudo apt install qemu-system-x86"
        return 1
    fi
    
    local iso=$(iso_path)
    if [[ -z "$iso" ]]; then
        log_info "ISO not found, building first..."
        build
        iso=$(iso_path)
    fi
    
    log_info "Starting QEMU (Ctrl+C to exit)..."
    echo ""
    
    qemu-system-x86_64 -enable-kvm -m 512 -cdrom "$iso"
}

inspect() {
    log_info "Inspecting ISO contents..."
    
    local iso=$(iso_path)
    if [[ -z "$iso" ]]; then
        log_info "ISO not found, building first..."
        build
        iso=$(iso_path)
    fi
    
    cd "$SCRIPT_DIR"
    mkdir -p mnt
    
    log_info "Mounting ISO..."
    sudo mount -o loop "$iso" mnt
    
    echo ""
    log_info "ISO contents:"
    ls -lah mnt/
    
    echo ""
    log_info "Unmounting ISO..."
    sudo umount mnt
    rmdir mnt
    
    log_success "Inspection complete"
}

burn_help() {
    local iso=$(iso_path)
    iso_display="${iso:-<build the ISO first with: ./build.sh build>}"
    
    cat << 'EOF'

╔═══════════════════════════════════════════════════════════════════════════╗
║                      USB BURNING INSTRUCTIONS                             ║
╚═══════════════════════════════════════════════════════════════════════════╝

1. IDENTIFY YOUR USB DEVICE
   ━━━━━━━━━━━━━━━━━━━━━━━━━
   List all devices:
     lsblk
   
   Or use:
     sudo fdisk -l
   
   ⚠  Look for your USB device (usually /dev/sdX where X is a letter)
   ⚠  DO NOT confuse with your main hard drive!

2. UNMOUNT USB (if already mounted)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   sudo umount /dev/sdX*

3. BURN ISO TO USB
   ━━━━━━━━━━━━━━━━━
   
   METHOD A: Command Line (dd)
   ───────────────────────────
EOF
    
    if [[ -n "$iso" ]]; then
        echo "   sudo dd if=$iso of=/dev/sdX bs=4M status=progress conv=fsync"
    else
        echo "   sudo dd if=result/iso/nixos-*.iso of=/dev/sdX bs=4M status=progress conv=fsync"
    fi
    
    cat << 'EOF'
   sudo sync
   
   METHOD B: GUI Tools
   ──────────────────
   Use one of these applications:
     - GNOME Disks (gnome-disk-utility)
     - Balena Etcher (balena-etcher)
     - Popsicle
     - UNetbootin
   
   Steps:
     1. Open the application
     2. Select your ISO file from result/iso/
     3. Select your USB device
     4. Click Write/Burn/Start

4. EJECT USB SAFELY
   ━━━━━━━━━━━━━━━━
   sudo eject /dev/sdX

╔═══════════════════════════════════════════════════════════════════════════╗
║                              ⚠  WARNING  ⚠                                ║
║                                                                            ║
║  Replace /dev/sdX with YOUR ACTUAL USB DEVICE!                            ║
║  Using the wrong device will overwrite your data permanently!             ║
║                                                                            ║
║  Double-check lsblk output before running dd command.                     ║
╚═══════════════════════════════════════════════════════════════════════════╝

EOF
}

help() {
    cat << 'EOF'

╔═══════════════════════════════════════════════════════════════════════════╗
║           NixOS Debug ISO Build Script - Help                             ║
╚═══════════════════════════════════════════════════════════════════════════╝

USAGE
━━━━━
  ./build.sh <command> [args]

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
  ./build.sh build

  # Test the ISO in QEMU
  ./build.sh test

  # Inspect what's inside the ISO
  ./build.sh inspect

  # Get USB burning instructions
  ./build.sh burn-help

  # Remove build artifacts to start fresh
  ./build.sh clean

WORKFLOW
━━━━━━━
  1. Build:      ./build.sh build
  2. Inspect:    ./build.sh inspect
  3. Test:       ./build.sh test
  4. Burn:       ./build.sh burn-help    (then follow instructions)
  5. Boot & Debug: Boot from USB, run 'journalctl --boot --all'

NOTES
━━━━━
  • First build requires internet (downloads nixpkgs dependencies)
  • Subsequent builds are much faster (uses cache)
  • ISO size: ~900MB
  • Build space needed: ~15GB
  • Nix must be installed: https://nixos.org/download/

EOF
}

# ============================================================================
# MAIN DISPATCH
# ============================================================================

main() {
    if [[ $# -eq 0 ]]; then
        help
        return 0
    fi
    
    local command="$1"
    shift || true
    
    case "$command" in
        build)
            build "$@"
            ;;
        clean)
            clean "$@"
            ;;
        test)
            test_qemu "$@"
            ;;
        inspect)
            inspect "$@"
            ;;
        burn-help)
            burn_help "$@"
            ;;
        help|-h|--help)
            help "$@"
            ;;
        *)
            log_error "Unknown command: $command"
            echo ""
            help
            return 1
            ;;
    esac
}

main "$@"
