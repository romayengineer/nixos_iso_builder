# AGENTS.md: Custom NixOS Minimal ISO with Debug Logging

## Project Goal
Build a custom NixOS minimal ISO image with debug/verbose logging enabled by default, for troubleshooting failed boot installations. The ISO will output all kernel, initrd, and systemd debug messages to console and systemd journal.

## Critical Build Information

### Build Method: Flakes (Modern NixOS)
- **Build command**: `nix build --extra-experimental-features "nix-command flakes" .#bootDebugISO`
- **Output path**: `result/iso/nixos-*.iso`
- **Prerequisites**: Nix package manager must be installed on the build machine
- **Note**: The `--extra-experimental-features "nix-command flakes"` flag is required for flakes to work

### Flake Configuration (`flake.nix`)
- **Minimal imports**: Only `installation-cd-minimal.nix` base (no GUI, no graphical modules)
- **Key config options**:
  - `boot.consoleLogLevel = 7` (max kernel debug messages)
  - `boot.initrd.verbose = true` (early boot verbosity)
  - `boot.kernelParams = ["loglevel=7" "systemd.log_level=debug" "systemd.log_target=console"]`
- **Compression**: Use `lz4` for faster builds during development
- **NixOS version**: Pin to `nixos-26.05` or stable branch for reproducibility

### Build Time & Disk Space
- **First build**: 15-30 minutes (downloads/compiles dependencies)
- **Subsequent builds**: 5-10 minutes (cached)
- **Disk space required**: ~15GB working space, final ISO ~900MB

## Log Capture Strategy

### During Boot Failure
If the ISO partially boots:
1. From interactive shell: `journalctl --boot --all` → shows complete boot log
2. Export to file: `journalctl --boot --all > /tmp/boot_log.txt`
3. Copy log file to USB or network storage for analysis

### Early Boot (Stage-1) Failures
- All console output is printed to TTY (capture via screenshot/photo)
- Logs stored in systemd journal if initrd stage-1 completes
- No post-boot file writing possible for early failures (USB drivers not loaded)

## Project Layout

```
./
├── flake.nix              # Flakes configuration for ISO build
├── flake.lock             # Lock file (auto-generated, commit to git)
├── AGENTS.md              # This file
└── README.md              # User-facing build/burn instructions (optional)
```

## Key NixOS Module References

These modules are imported automatically via `installation-cd-minimal.nix`:
- Stage-1 (initrd) config: `nixpkgs/nixos/modules/system/boot/stage-1.nix`
- Kernel params config: `nixpkgs/nixos/modules/system/boot/kernel.nix`
- ISO builder: `nixpkgs/nixos/modules/installer/cd-dvd/iso-image.nix`

See research notes in conversation history for detailed module exploration.

## Common Pitfalls for Agents

### Mistake: Writing logs directly to USB during early boot
- **Reality**: USB drivers not available in stage-1 (initrd)
- **Solution**: Logs go to console/journal; capture them post-boot via `journalctl`

### Mistake: Using legacy `nixos-generators`
- **Reality**: Deprecated in NixOS 25.05+, replaced by `nixos-rebuild build-image`
- **Current approach**: Use Flakes with `nix build` (modern standard)

### Mistake: Forgetting `flake.lock` is required
- **Reality**: Lock file must exist and be committed for reproducible builds
- **Action**: After `nix flake init` or first `nix build`, commit `flake.lock` to git

### Mistake: Using `nix-build` instead of `nix build`
- **Reality**: `nix build` is the modern Flakes syntax; `nix-build` is legacy
- **Correct command**: `nix build .#bootDebugISO`

## Testing the Built ISO

```bash
# Boot in QEMU for quick iteration
qemu-system-x86_64 -enable-kvm -m 512 -cdrom result/iso/nixos-*.iso

# Mount ISO to inspect contents (verify nix-store.squashfs exists)
mkdir -p mnt
sudo mount -o loop result/iso/nixos-*.iso mnt
ls -la mnt  # Should show: boot EFI isolinux nix-store.squashfs version.txt
sudo umount mnt
```

## Nix Development Environment Expectations

- Build requires internet access (downloads nixpkgs, dependencies)
- Parallel builds: `nix build` uses all available cores by default
- Cache invalidation: Changes to `flake.nix` force full rebuild of affected derivations
- Garbage collection: Keep `result/` symlink to prevent intermediate files from being cleaned

## Success Criteria

✅ ISO builds without errors (`nix build` exits 0)
✅ ISO file exists at `result/iso/nixos-*.iso` (~900MB)
✅ ISO boots to NixOS live environment
✅ `journalctl --boot --all` shows debug-level kernel/systemd messages
✅ Boot log captures all failed initialization steps for debugging

## References

- **NixOS Manual**: https://nixos.org/manual/nixos/stable/
- **Flakes Guide**: https://nixos.wiki/wiki/Flakes
- **Boot Configuration**: https://mynixos.com/nixpkgs/option/boot
- **Kernel Netconsole (alternative logging)**: https://docs.kernel.org/6.16/networking/netconsole.html
