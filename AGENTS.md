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

## Logging Profiles System

The project supports multiple logging profiles that can be selected at build time without modifying any files.

### How It Works

**Architecture**: Using Nix Flake package outputs for profile selection
- `logging-config.nix`: Defines 4 logging profiles (debug, info, production, minimal)
- `flake.nix`: Creates 5 package outputs (one per profile + default)
- `build.py`: Selects the appropriate package output based on `--log-level` flag

**Key Files**:
- `logging-config.nix` (195 lines): Profile definitions with full documentation
- `flake.nix` (222 lines): Uses `mkBootISO` helper function to generate ISO for each profile
- `build.py`: Maps `--log-level` to flake package names (`.#bootDebugISO-{profile}`)
- `Makefile`: Convenient shortcuts (`make build-debug`, `make build-prod`, etc.)

### Profile Selection (No File Modifications)

The `--log-level` flag in `build.py` works by:

1. User calls: `./build.py build --log-level production`
2. build.py validates the level and maps it: `production` → `.#bootDebugISO-production`
3. build.py runs: `nix build .#bootDebugISO-production`
4. flake.nix has this output pre-defined: `bootDebugISO-production = mkBootISO "production";`
5. `mkBootISO` function uses `logging-config.nix` to get the profile settings
6. ISO is built with the selected profile

**Advantage**: No flake.nix modifications needed. Each profile is a separate, independently-cacheable Nix derivation.

### Adding New Profiles

To add a new logging profile:

1. Add to `logging-config.nix`:
   ```nix
   newprofile = {
     consoleLogLevel = 5;
     # ... other settings
   };
   ```

2. Add to `flake.nix` packages section:
   ```nix
   packages.${system} = {
     # ... existing profiles
     bootDebugISO-newprofile = mkBootISO "newprofile";
   };
   ```

3. Update `build.py` validation:
   ```python
   valid_levels = {"debug", "production", "info", "minimal", "newprofile"}
   ```

4. Update Makefile with new target (optional):
   ```makefile
   build-newprofile:
     @python3 build.py build --log-level newprofile
   ```

## Project Layout

```
./
├── flake.nix                  # Flakes configuration for ISO build (222 lines)
├── flake.lock                 # Lock file (auto-generated, commit to git)
├── logging-config.nix         # Logging profile definitions (195 lines)
├── build.py                   # Python build script with --log-level support
├── Makefile                   # Build automation with profile shortcuts
├── AGENTS.md                  # This file (developer guide)
├── README.md                  # User-facing instructions
└── docs/
    ├── build-script-implementation.md
    └── qemu-testing-guide.md
```

## Key NixOS Module References

These modules are imported automatically via `installation-cd-minimal.nix`:
- Stage-1 (initrd) config: `nixpkgs/nixos/modules/system/boot/stage-1.nix`
- Kernel params config: `nixpkgs/nixos/modules/system/boot/kernel.nix`
- ISO builder: `nixpkgs/nixos/modules/installer/cd-dvd/iso-image.nix`

See research notes in conversation history for detailed module exploration.

## Code Quality Standards: .nix File Documentation

### ⭐ REQUIRED: All .nix Files Must Have Extensive Comments

**This is a mandatory code quality requirement for all Nix configuration files.**

Every `.nix` file in this project must include comprehensive documentation explaining:

#### 1. **Configuration Options**
- **What it does**: Clear explanation of each setting's purpose
- **Valid ranges**: All acceptable values or value types
- **Value meanings**: Explanation of what each value produces
- **Current setting**: Clearly mark which value is currently set
- **Recommended settings**: Mark optimal values for debugging/production
- **When to change**: When and why someone would modify this setting

#### 2. **Structure Documentation**
- **Section headers**: Organize related settings with clear headers
- **Input explanations**: Document external inputs (inputs.nixpkgs, etc.)
- **Output explanations**: Explain what derivations are produced
- **Module descriptions**: Explain purpose of each imported module

#### 3. **Trade-Offs and Considerations**
- **Performance vs. quality**: Document speed/compression trade-offs
- **Security vs. debugging**: Note when debug mode reduces security
- **Size implications**: Explain how settings affect ISO/output size
- **Build time impact**: Note which settings affect build duration

#### 4. **Comment Format Standards**
```nix
# OPTION_NAME: Brief description (value type: range or options)
# Detailed explanation of what this option controls
# Valid values:
#   value1 - Description of this value
#   value2 - Description of this value (DEFAULT)
#   value3 - Description of this value
# Current: value2
# RECOMMENDED: value3 (for debugging)
# Note: Explain any special considerations or gotchas
OPTION_NAME = value2;
```

#### 5. **Documentation Checklist**
Before committing any .nix file:
- [ ] Every configuration option has a comment block
- [ ] Comment includes: what, why, valid values, current setting
- [ ] Sections are organized with clear headers (use `# ====...====`)
- [ ] Trade-offs are explained (performance, size, security)
- [ ] Current settings marked with "# Current: "
- [ ] Recommended settings marked with "# RECOMMENDED: "
- [ ] Special considerations noted in "# Note: " comments
- [ ] Syntax validation passes: braces/brackets balanced
- [ ] File is > 50% comments if it has > 20 lines of config

#### 6. **Why This Matters**
- **Nix Learning Curve**: Nix syntax is unfamiliar; comments help agents understand
- **NixOS Complexity**: Many options interact; documenting helps prevent mistakes
- **Future Maintenance**: Comments explain design decisions
- **Reproducibility**: Clear documentation ensures settings aren't changed accidentally
- **Debugging**: When something breaks, comments explain what each setting does

#### 7. **Example: Well-Documented .nix File**
See `flake.nix` in this project (227 lines, 159 comment lines, 70% documentation ratio):
- Each boot option documented with 8-12 lines of explanation
- Valid ranges shown explicitly
- Current and recommended settings marked
- Trade-offs (e.g., compression algorithms) fully explained

#### 8. **Enforcement**
- Any .nix file modifications must include comment updates
- Pull requests without adequate .nix comments will be requested for revision
- New .nix files must follow this standard from creation

## Testing Standards: ALL TESTS MUST PASS

### ⭐ HARD RULE: NEVER SKIP TESTS - ALL INTEGRATION TESTS MUST PASS

**This is a non-negotiable requirement. Tests represent the contract of the system.**

#### 1. **No Skipped Tests**
- **NEVER** use `@pytest.mark.skip()` on any test
- **NEVER** use `pytest.xfail()` to mark expected failures
- **NEVER** use conditional skip logic to avoid failing tests
- Every test in the repo must pass 100% of the time
- If a test fails, FIX THE CODE - don't skip the test

#### 2. **Integration Tests Are Critical**
- Integration tests (`tests/integration/`) verify real behavior, not mocked behavior
- They must pass after ANY change to flake.nix, build.py, or nixos_iso_builder package
- They validate the entire build pipeline end-to-end
- Skipping integration tests means the build system is untested

#### 3. **Test Failure Resolution Process**
When a test fails:
1. **Analyze the failure**: Understand what the test expects vs. what actually happens
2. **Fix the root cause**: Modify flake.nix, nixos_iso_builder code, or build.py to make the test pass
3. **Verify the fix**: Run `make test-integration` until all tests pass
4. **Document the fix**: Explain in code comments why the change was needed
5. **Never ship a failure**: Always commit working code with passing tests

#### 4. **Specific Rule for Integration Tests**
- `make test-integration` must exit with code 0 (all tests pass)
- Before committing, run: `python3 -m pytest tests/integration/test_build.py -v`
- All assertions must pass; no "expected failures" allowed
- If the flake.nix produces invalid output, FIX THE FLAKE - don't skip the test

#### 5. **Why This Matters**
- **Trust**: Tests are the only guarantee that code works as intended
- **Regression Prevention**: Skipping tests allows bugs to hide and resurface
- **Integration Tests Especially**: They test the actual nix build, not mocked behavior
- **User Confidence**: Users depend on the ISO actually being built
- **Project Quality**: This project is about providing a working debug ISO - no shortcuts

#### 6. **Enforcement**
- Any commit that skips tests will be rejected
- Any PR with `@pytest.mark.skip()` will be requested for revision
- Integration test failures must be fixed before proceeding with other work
- Use `make test-all` frequently during development to catch issues early

### Common Pitfalls for Agents

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

### Mistake: Creating .nix files without extensive comments
- **Reality**: Nix syntax is unfamiliar; configuration options lack self-documentation
- **Solution**: Follow the .nix File Documentation standard above
- **Requirement**: Every configuration option must have comprehensive comments explaining what, why, valid values, and recommendations

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

## Root Cause Analysis: ISO Build Failure (RESOLVED)

### Problem Statement
Integration tests were failing because `nix build .#bootDebugISO-minimal` produced no ISO file.
The flake.nix returned a directory structure with an empty `iso/` subdirectory instead of the actual ISO binary.

### Root Cause (Identified via test_nix_eval.py)

**The mkDerivation wrapper was not declaring isoImage as a buildInput.**

When `nix build` executes, it only builds derivations that are explicitly listed as `buildInputs` or referenced in phases.
Simply setting `iso = isoImage;` as a custom attribute does NOT trigger a build.

**Evidence from test_nix_eval.py:**
```
test_bootdebugiso_minimal_buildInputs FAILED
AssertionError: bootDebugISO-minimal should have buildInputs: 0
```

The mkDerivation had:
- `iso = isoImage;` (custom attribute, NOT a buildInput)
- `buildInputs = [];` (empty - isoImage never gets built!)
- `installPhase` tries to copy from `$iso` but `$iso` is NOT in the build environment

### Why This Matters

In Nix:
1. **Attributes in stdenv.mkDerivation can be:**
   - `buildInputs`: Derivations that WILL be built and available in `$PATH` and environment
   - `propagatedBuildInputs`: Like buildInputs but propagate to dependent derivations
   - Custom attributes (e.g., `iso = ...`): Just variables, NOT built unless referenced in phases
   
2. **Reference syntax:**
   - `${isoImage}` or `$iso` in shell phases only works if the derivation is in buildInputs
   - Setting `iso = isoImage;` just makes it available as a Nix variable, not a build dependency
   
3. **The fix:**
   - Either: `buildInputs = [ isoImage ];` to make it a build dependency
   - Or: Use `postUnpack` or other phases to properly reference the derivation
   - Or: Return `isoImage` directly instead of wrapping it

### How Tests Revealed This

Created `tests/integration/test_nix_eval.py` with 9 tests to understand Nix behavior:
1. Confirmed bootDebugISO-minimal evaluates to a derivation ✓
2. Confirmed it has all required derivation attributes ✓
3. Confirmed drvPath exists and is valid ✓
4. **Discovered buildInputs is empty** ✗ <- ROOT CAUSE
5. Discovered iso attribute exists but isn't a proper buildInput

### Lesson: Always Test Nix Evaluation

When flake.nix modifications don't work:
1. Use `nix eval` to check what the flake produces
2. Test intermediate values with `--apply` transformations
3. Don't assume custom attributes trigger builds - check buildInputs
4. Write tests to validate assumptions (test_nix_eval.py approach)

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
