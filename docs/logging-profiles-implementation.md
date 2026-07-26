# Logging Profiles Implementation Guide

## Overview

This document explains how the logging profile system works, including the architecture, design decisions, and technical implementation.

## Architecture

### Three-Component System

The logging profiles system consists of three integrated components:

```
┌─────────────────────────────────────────────────────────────────┐
│ User Interface: build.py                                        │
│ - Accepts: ./build.py build --log-level {debug|prod|...}       │
│ - Validates log level                                            │
│ - Maps to flake output: .#bootDebugISO-{level}                  │
│ - Runs: nix build .#bootDebugISO-{level}                        │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│ Profile Selection: flake.nix                                    │
│ - Imports logging-config.nix                                     │
│ - Uses mkBootISO helper function                                 │
│ - Creates package outputs for each profile:                      │
│   - .#bootDebugISO-debug                                         │
│   - .#bootDebugISO-info                                          │
│   - .#bootDebugISO-production                                    │
│   - .#bootDebugISO-minimal                                       │
│ - Default: .#bootDebugISO → debug profile                        │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│ Profile Definitions: logging-config.nix                         │
│ - Attribute set with 4 profiles                                  │
│ - Each profile defines:                                          │
│   - consoleLogLevel (0-7)                                        │
│   - initrdVerbose (true/false)                                   │
│   - kernelLogLevel (0-7)                                         │
│   - systemdLogLevel (string: debug|info|err|crit)               │
│   - systemdLogTarget (string: console|journal)                  │
│   - journaldForwardConsole (yes/no)                             │
│   - emergencyAccess (true/false)                                 │
│ - description field for user feedback                            │
└─────────────────────────────────────────────────────────────────┘
```

### Why This Approach?

**Why not use `--arg logLevel "debug"`?**

Nix Flakes do not support `--arg` directly. The design options were:

1. **Modify flake.nix on each build** - Anti-pattern: modifies source files, no way to build multiple profiles in parallel, clutters git history
2. **Create separate package outputs** - Current approach: clean, cacheable, no file modifications, allows parallel builds
3. **Use a non-flake default.nix** - Would require different project structure, loses flakes benefits

**Current approach advantages:**
- ✅ No file modifications needed
- ✅ Each profile is independently cacheable
- ✅ Can build multiple profiles in parallel
- ✅ Clean flake.nix structure
- ✅ Simple to add new profiles

## Implementation Details

### 1. logging-config.nix

Defines all available logging profiles as an attribute set.

**File structure:**
```nix
{
  # Profile 1: debug
  debug = {
    consoleLogLevel = 7;
    initrdVerbose = true;
    kernelLogLevel = 7;
    systemdLogLevel = "debug";
    systemdLogTarget = "console";
    journaldForwardConsole = "yes";
    emergencyAccess = true;
    description = "Debug: Maximum verbosity (troubleshooting)";
  };
  
  # Profile 2: info
  info = { ... };
  
  # Profile 3: production
  production = { ... };
  
  # Profile 4: minimal
  minimal = { ... };
}
```

**Key design points:**
- Each profile is self-contained and documented
- Includes `description` field for user feedback
- All 4 profiles defined in single file for easy comparison
- Changes to a profile affect all ISOs built with that profile

### 2. flake.nix Package Generation

Uses a helper function to generate package outputs for each profile:

**Relevant sections:**

```nix
# Helper function to create a boot ISO with a specific logging profile
mkBootISO = (profileName:
  let
    logs = loggingConfig.${profileName};
  in
  (nixpkgs.lib.nixosSystem {
    # ... configuration using logs.* variables ...
  }).config.system.build.isoImage
);

# Create package outputs for each profile
packages.${system} = {
  bootDebugISO-debug = mkBootISO "debug";
  bootDebugISO-info = mkBootISO "info";
  bootDebugISO-production = mkBootISO "production";
  bootDebugISO-minimal = mkBootISO "minimal";
  bootDebugISO = mkBootISO "debug";  # Default
};
```

**Key design points:**
- `mkBootISO` is a function that takes a profile name
- Each package output calls `mkBootISO` with a different profile
- Default `bootDebugISO` uses "debug" profile
- `lib.mkForce` used to override conflicting settings from iso-image.nix

**Why mkBootISO function?**
- Eliminates code duplication (configuration used for all profiles)
- Profile selection happens at package level, not configuration level
- Easier to add new profiles (just add one line to packages)

### 3. build.py Command-Line Interface

Maps `--log-level` flag to flake package outputs:

```python
def cmd_build(args: argparse.Namespace) -> int:
    log_level = getattr(args, "log_level", "debug")
    
    # Validate the log level
    if not validate_log_level(log_level):
        return 1
    
    # Map log level to flake output name
    flake_output = f".#bootDebugISO-{log_level}"
    
    # Run nix build with selected output
    process = subprocess.Popen(
        [
            "nix",
            "build",
            "--extra-experimental-features",
            "nix-command flakes",
            flake_output,  # e.g., .#bootDebugISO-minimal
        ],
        ...
    )
```

**Key design points:**
- Simple string interpolation: `.#bootDebugISO-{log_level}`
- Validation ensures only valid profiles are used
- No file modifications - just passes different flake output
- Type-safe with proper annotations and error handling

### 4. Makefile Convenience Shortcuts

Provides easy-to-remember build targets:

```makefile
build-debug:
	@python3 build.py build --log-level debug

build-info:
	@python3 build.py build --log-level info

build-prod:
	@python3 build.py build --log-level production

build-minimal:
	@python3 build.py build --log-level minimal
```

## Profile Specifications

### Debug Profile
- **Kernel console**: 7 (KERN_DEBUG)
- **Systemd logging**: debug
- **Initrd**: verbose
- **Emergency shell**: enabled
- **Use case**: Troubleshooting boot failures

### Info Profile
- **Kernel console**: 6 (KERN_INFO)
- **Systemd logging**: info
- **Initrd**: verbose
- **Emergency shell**: enabled
- **Use case**: General testing, understanding boot process

### Production Profile
- **Kernel console**: 3 (KERN_ERR)
- **Systemd logging**: err
- **Initrd**: minimal
- **Emergency shell**: disabled
- **Use case**: Deployment, catching real errors

### Minimal Profile
- **Kernel console**: 2 (KERN_CRIT)
- **Systemd logging**: crit
- **Initrd**: minimal
- **Emergency shell**: disabled
- **Use case**: CI/CD, silent operation

## How Profiles Are Used During Boot

1. **Kernel loads with loglevel parameter**
   - `loglevel=7` tells kernel to print messages >= KERN_DEBUG level
   - Set via `boot.kernelParams` from profile

2. **Systemd starts with log_level parameter**
   - `systemd.log_level=debug` tells systemd to log all messages
   - Set via `boot.kernelParams` from profile

3. **Messages sent to console**
   - `systemd.log_target=console` directs logs to /dev/console
   - Visible during boot
   - Also forwarded to journal via `journalctl.forward_to_console`

4. **Emergency shell availability**
   - `boot.initrd.systemd.emergencyAccess=true/false` from profile
   - If boot fails, emergency shell is available (if enabled)
   - Allows interactive troubleshooting

## Adding a New Profile

### Step 1: Add to logging-config.nix

```nix
newprofile = {
  consoleLogLevel = 5;
  initrdVerbose = false;
  kernelLogLevel = 5;
  systemdLogLevel = "notice";
  systemdLogTarget = "console";
  journaldForwardConsole = "no";
  emergencyAccess = false;
  description = "Custom profile";
};
```

### Step 2: Add to flake.nix packages

```nix
packages.${system} = {
  # ... existing profiles ...
  bootDebugISO-newprofile = mkBootISO "newprofile";
};
```

### Step 3: Update build.py validation

```python
def validate_log_level(log_level: str) -> bool:
    valid_levels = {"debug", "production", "info", "minimal", "newprofile"}
    if log_level not in valid_levels:
        log_error(f"Invalid log level: {log_level}")
        return False
    return True
```

### Step 4: Add Makefile target (optional)

```makefile
build-newprofile:
	@python3 build.py build --log-level newprofile
```

### Step 5: Update help text

- Update README.md profile table
- Update Makefile help text
- Update build.py help message

## Performance Considerations

### Cache Behavior

Each profile output is independently cacheable:
- Building `bootDebugISO-debug` doesn't affect cache for `bootDebugISO-production`
- Subsequent builds of the same profile reuse cache
- Parallel builds of different profiles use independent caches

### Build Times

- **First build** (any profile): 15-30 minutes (downloads all dependencies)
- **Same profile again**: 5-10 minutes (reuses cache)
- **Different profile**: 5-10 minutes (configuration differences are small, most cache shared)

### Disk Space

- Working space needed: ~15GB
- Final ISO size: ~900MB per profile
- Only current `result/` symlink kept; others removed

## Testing the Implementation

### Unit Testing

```bash
# Verify all profiles can be selected
./build.py build --log-level debug
./build.py build --log-level info
./build.py build --log-level production
./build.py build --log-level minimal
```

### Integration Testing

```bash
# Verify flake outputs exist
nix flake show .

# Verify Makefile targets work
make build-debug
make build-prod
```

### Validation Testing

```bash
# Check that ISOs boot with correct logging
# (requires actual booting or QEMU)
qemu-system-x86_64 -cdrom result/iso/nixos-*.iso
```

## Troubleshooting

### Error: "dynamic attribute already defined"

This error means `packages.${system}` was defined multiple times. Fix:
- Ensure all package definitions are inside a single attribute set block
- Use `packages.${system} = { ... };` not `packages.${system}.foo = ...;`

### Error: "logLevel" not found in logging-config.nix

The profile name doesn't exist. Fix:
- Check spelling in `logging-config.nix`
- Add new profile if needed
- Update build.py validation list

### Flake caching issues

If builds seem to use stale configuration:
```bash
rm -rf .git/nix/flake-cache  # Clear flake cache
nix flake update             # Update flake.lock
nix build .#bootDebugISO     # Rebuild
```

## References

- **Nix Flakes**: https://nixos.wiki/wiki/Flakes
- **NixOS Options**: https://mynixos.com/nixpkgs/option/boot
- **Package Outputs**: https://nixos.org/manual/nix/stable/command-ref/new-cli/nix3-flake.html
