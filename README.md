# Custom NixOS Minimal ISO with Debug Logging

A reproducible NixOS ISO image configured for maximum boot-time verbosity and debug logging. Designed to capture all kernel, initrd, and systemd debug messages to help troubleshoot failed NixOS installations.

## Quick Start

### Prerequisites

1. **Nix package manager** installed on your build machine
   - Install: https://nixos.org/download/
   - Verify: `nix --version`

2. **Disk space**: ~15GB working space for first build, ~900MB for final ISO
3. **Internet**: Required to download dependencies
4. **USB pendrive**: For burning the final ISO

### Build the ISO

```bash
# Navigate to project directory
cd /path/to/nixos

# Build the ISO (first build takes 15-30 minutes)
nix build .#bootDebugISO.config.system.build.isoImage

# Find the ISO file
ls -lh result/iso/nixos-*.iso

# Expected output: ISO file ~900MB
```

The build output will be a symlink `result/` pointing to the built ISO.

### Burn to USB Pendrive

Replace `/dev/sdX` with your actual USB device (use `lsblk` or `fdisk -l` to identify it).

**WARNING**: Be absolutely sure of the device name. Using the wrong device will overwrite your data.

```bash
# 1. Identify your USB device
lsblk
# or
sudo fdisk -l

# 2. Unmount if already mounted
sudo umount /dev/sdX*

# 3. Burn ISO to USB (method 1: dd)
sudo dd if=result/iso/nixos-*.iso of=/dev/sdX bs=4M status=progress conv=fsync
sudo sync

# 3. Burn ISO to USB (method 2: GNOME Disks, Etcher, or similar GUI)
# - Open your preferred USB burner
# - Select result/iso/nixos-*.iso
# - Select USB device
# - Write/Burn

# 4. Eject safely
sudo eject /dev/sdX
```

## Capturing Boot Logs

### If ISO boots partially (reaches interactive shell):

```bash
# View all boot logs from last boot
journalctl --boot --all

# Save to file for analysis
journalctl --boot --all > /tmp/boot_log.txt

# Copy to USB or transfer out for analysis
```

### If boot fails early (stuck in stage-1 initrd):

- **Capture console output**: Take a screenshot or photo of the error messages
- **The logs are printed to console** even if USB drivers aren't loaded yet
- Try to reach an emergency shell by pressing `Ctrl+D` or waiting
- If emergency shell appears, use `journalctl --boot --all` as above

### Additional debugging commands:

```bash
# See kernel ring buffer (last 100 lines)
dmesg | tail -100

# View systemd units that failed
systemctl --failed

# Check detailed systemd logs for a specific unit
journalctl --unit=systemd-networkd --all

# See what happened during stage-1 (initrd)
journalctl -b -x  # with explanations
```

## Configuration Details

All debug logging is configured in `flake.nix`:

- **Kernel logging**: `boot.consoleLogLevel = 7` (max verbosity)
- **Initrd verbosity**: `boot.initrd.verbose = true`
- **Systemd debug**: `systemd.log_level=debug` via kernel params
- **Console output**: `systemd.log_target=console` for direct visibility
- **Compression**: `lz4` for faster rebuild cycles

See `AGENTS.md` for architecture notes and common pitfalls.

## Rebuilding After Changes

If you modify `flake.nix`:

```bash
# Clean previous build (optional but recommended)
rm -rf result/

# Rebuild (subsequent builds are much faster due to caching)
nix build .#bootDebugISO.config.system.build.isoImage
```

## Testing Without Burning to USB

### QEMU (fast iteration):

```bash
# Install QEMU if needed
# On Ubuntu: sudo apt install qemu-system-x86

# Boot ISO in QEMU (verify boot behavior)
qemu-system-x86_64 -enable-kvm -m 512 -cdrom result/iso/nixos-*.iso

# Watch for kernel output and systemd messages
```

### Inspect ISO contents:

```bash
# Verify nix-store.squashfs exists (required for booting)
mkdir -p mnt
sudo mount -o loop result/iso/nixos-*.iso mnt
ls -la mnt/

# Expected: boot/ EFI/ isolinux/ nix-store.squashfs version.txt
sudo umount mnt
```

## Troubleshooting

### Build fails with "hash mismatch"

```bash
# Flake inputs may have changed; update lock file
nix flake update
nix build .#bootDebugISO.config.system.build.isoImage
```

### Build is very slow

- First build downloads all dependencies (~several GB)
- Keep the `result/` symlink to avoid garbage collection
- Subsequent builds reuse cache (~5-10 minutes)

### ISO won't boot

1. Verify burned correctly: `sudo md5sum /dev/sdX` should match ISO checksum
2. Try different USB device or pendrive
3. Check BIOS settings: boot from USB, disable Secure Boot if needed
4. Try UEFI mode vs. Legacy BIOS mode

### Can't capture boot logs

- If stuck at kernel panic: take a photo of the error
- If you reach emergency shell: `journalctl --boot --all`
- If silent failure: add `rd.debug` to kernel params (edit at boot menu)

## References

- **NixOS Manual**: https://nixos.org/manual/nixos/stable/
- **Flakes Guide**: https://nixos.wiki/wiki/Flakes
- **Boot Options**: https://mynixos.com/nixpkgs/option/boot
- **Kernel Netconsole** (for remote logging): https://docs.kernel.org/6.16/networking/netconsole.html

## Project Files

- `flake.nix` - ISO build configuration with debug logging
- `flake.lock` - Reproducible dependency lock (auto-generated, commit to git)
- `AGENTS.md` - Agent-focused documentation for development
- `README.md` - This file
