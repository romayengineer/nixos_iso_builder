# NixOS Debug ISO Build Script - Python Edition

## Usage

```
./build.py <command> [options]
```

## Commands

- **build [--log-level LEVEL]** - Build ISO with debug logging (default: debug)
- **clean** - Remove build artifacts
- **test** - Boot ISO in QEMU for testing
- **inspect** - Mount and inspect ISO contents
- **burn-help** - Show USB burning instructions
- **help** - Show this help message

## Log Levels

- **debug** - Maximum verbosity (for troubleshooting)
- **info** - Balanced logging (default)
- **production** - Minimal logs (for deployment)
- **minimal** - Quiet mode (for CI/CD)

## Examples

```bash
./build.py build                      # Build with debug logging
./build.py build --log-level minimal  # Build with minimal logging
./build.py test                       # Test in QEMU
./build.py clean                      # Clean artifacts
```
