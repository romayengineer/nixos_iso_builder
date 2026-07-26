# Integration Tests for NixOS ISO Builder

## Overview

This directory contains integration tests that **actually build NixOS ISOs** using the real `nix build` command. Tests are not mocked - they create real files and verify them.

## Test Structure

```
tests/
├── conftest.py              - Pytest configuration
├── integration/
│   ├── __init__.py
│   └── test_build.py        - Integration tests for build functionality
└── README.md                - This file
```

## Running Tests

### Prerequisites

Install test dependencies:
```bash
make install-dev
# or
pip install -r requirements-test.txt
```

### Run All Tests

```bash
make test-all
```

### Run Integration Tests Only

```bash
make test-integration
```

These tests will:
1. Clean up old ISO files
2. Run actual `nix build` command
3. Verify new ISO file is created
4. Validate ISO properties

### Run Specific Test

```bash
pytest tests/integration/test_build.py::test_build_minimal_creates_iso -v
```

## Test Coverage

The integration tests verify:

✅ **Build Operations**
- `test_build_minimal_creates_iso` - Minimal profile creates valid ISO
- `test_build_debug_creates_iso` - Debug profile creates valid ISO
- `test_build_log_is_created` - Build process creates build.log

✅ **File Discovery**
- `test_find_iso_returns_none_when_no_iso_exists` - Correctly returns None
- `test_find_iso_finds_built_iso` - Correctly finds built ISO

✅ **File Validation**
- `test_validate_iso_is_file_rejects_directories` - Rejects non-files
- `test_validate_iso_is_file_accepts_valid_iso` - Accepts valid ISOs
- `test_iso_file_is_valid_nixos_iso` - Verifies ISO properties

✅ **Cleanup Operations**
- `test_cleanup_result_symlinks_removes_old_links` - Cleanup works correctly

## Important Notes

### Real File Operations

These tests:
- ✅ Actually call `nix build`
- ✅ Create real ISO files in `/nix/store`
- ✅ Write real `build.log` file
- ✅ Remove real files and symlinks

### No Mocking

Tests do NOT use:
- unittest.mock
- pytest-mock
- Any stubbing or patching

This means:
- Tests are true integration tests
- They verify the actual build process works
- They catch real-world issues
- They run slower (15-30 minutes first run)

### Cleanup

Tests automatically:
1. Clean up old ISO files before building
2. Remove result symlinks
3. Create fresh builds

## Test Markers

Run tests with specific markers:

```bash
# Run slow tests only
pytest -m slow

# Run integration tests only
pytest -m integration
```

## Debugging Failed Tests

If a test fails:

1. **Check build.log** - Contains full `nix build` output
   ```bash
   cat build.log | tail -100
   ```

2. **Check result symlink** - Points to ISO directory
   ```bash
   ls -la result
   ```

3. **Verify ISO exists** - Check /nix/store
   ```bash
   ls -la /nix/store/*nixos*.iso/iso/
   ```

4. **Run test with verbose output**
   ```bash
   pytest tests/integration/test_build.py -vvs
   ```

## Expected Test Duration

- First test run: 15-30 minutes (downloads dependencies, compiles)
- Subsequent runs: 5-10 minutes (uses cache)

## Continuous Integration

These tests are suitable for CI/CD:

```yaml
test:
  stage: test
  script:
    - make install-dev
    - make test-integration
  timeout: 1 hour
```

## Adding New Tests

To add a new integration test:

1. Open `tests/integration/test_build.py`
2. Add a new function starting with `test_`
3. Use `cleanup_iso_files()` to start fresh
4. Call real functions from `nixos_iso_builder`
5. Use assertions to verify results

Example:

```python
def test_my_new_feature() -> None:
    """Description of what you're testing"""
    # Arrange: Clean up and prepare
    cleanup_iso_files(PROJECT_ROOT)
    
    # Act: Do something
    result = some_operation()
    
    # Assert: Verify result
    assert result is not None
```

## References

- [pytest documentation](https://docs.pytest.org/)
- [NixOS Build Guide](../AGENTS.md)
- [Module Documentation](../nixos_iso_builder/README.md)
