"""Integration tests for Nix evaluation behavior

Tests that use nix eval to understand what the flake.nix actually produces.
No mocking - uses real nix eval calls.
"""

from pathlib import Path
import subprocess
import json
from typing import Dict, List, Union, cast

import pytest  # type: ignore


PROJECT_ROOT = Path(__file__).parent.parent.parent


def run_nix_eval(expression: str, apply: str = "") -> str:
    """Run nix eval and return the output
    
    Args:
        expression: Nix expression to evaluate (e.g., ".#bootDebugISO-minimal")
        apply: Optional --apply transformation (e.g., "x: x.type")
    
    Returns:
        The raw output from nix eval
    """
    cmd = [
        "nix",
        "eval",
        "--extra-experimental-features",
        "nix-command flakes",
    ]
    if apply:
        cmd.extend(["--apply", apply])
    cmd.append(expression)
    
    result = subprocess.run(
        cmd,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        raise RuntimeError(f"nix eval failed: {result.stderr}")
    return result.stdout.strip()


def run_nix_eval_json(expression: str, apply: str = "") -> Union[Dict[str, object], List[object], str, int, bool, None]:
    """Run nix eval with --json flag and parse the result
    
    Args:
        expression: Nix expression to evaluate
        apply: Optional --apply transformation
    
    Returns:
        Parsed JSON output
    """
    cmd = [
        "nix",
        "eval",
        "--extra-experimental-features",
        "nix-command flakes",
        "--json",
    ]
    if apply:
        cmd.extend(["--apply", apply])
    cmd.append(expression)
    
    result = subprocess.run(
        cmd,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        raise RuntimeError(f"nix eval failed: {result.stderr}")
    return cast(Union[Dict[str, object], List[object], str, int, bool, None], json.loads(result.stdout))


def test_bootdebugiso_minimal_is_derivation() -> None:
    """Test that bootDebugISO-minimal evaluates to a derivation"""
    output = run_nix_eval(".#bootDebugISO-minimal", "x: x.type")
    assert output == '"derivation"', f"Expected derivation type, got {output}"


def test_bootdebugiso_minimal_has_required_attributes() -> None:
    """Test that bootDebugISO-minimal has required derivation attributes"""
    # We need a custom run_nix_eval_json that handles --apply
    cmd = [
        "nix",
        "eval",
        "--extra-experimental-features",
        "nix-command flakes",
        "--json",
        "--apply",
        "x: builtins.attrNames x",
        ".#bootDebugISO-minimal",
    ]
    result = subprocess.run(
        cmd,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        raise RuntimeError(f"nix eval failed: {result.stderr}")
    attrs = json.loads(result.stdout.strip())
    
    # Check for key attributes that all derivations should have
    assert "type" in attrs, "Missing 'type' attribute"
    assert "drvPath" in attrs, "Missing 'drvPath' attribute"
    assert "outPath" in attrs, "Missing 'outPath' attribute"


def test_bootdebugiso_minimal_drv_path_exists() -> None:
    """Test that the drvPath for bootDebugISO-minimal exists"""
    drv_path = run_nix_eval(".#bootDebugISO-minimal.drvPath")
    drv_path = drv_path.strip('"')
    
    # The drvPath should point to a .drv file in /nix/store
    assert drv_path.startswith("/nix/store"), f"drvPath should be in /nix/store: {drv_path}"
    assert drv_path.endswith(".drv"), f"drvPath should end with .drv: {drv_path}"
    
    # The file should exist
    drv_file = Path(drv_path)
    assert drv_file.exists(), f"drvPath file should exist: {drv_path}"


def test_bootdebugiso_minimal_out_path() -> None:
    """Test what outPath bootDebugISO-minimal declares"""
    out_path = run_nix_eval(".#bootDebugISO-minimal.outPath")
    out_path = out_path.strip('"')
    
    print(f"bootDebugISO-minimal declares outPath: {out_path}")
    
    # The outPath should be in /nix/store
    assert out_path.startswith("/nix/store"), f"outPath should be in /nix/store: {out_path}"


def test_bootdebugiso_minimal_buildInputs() -> None:
    """Test that bootDebugISO-minimal has the iso derivation"""
    # Instead of checking buildInputs, check if the iso attribute exists and is a derivation
    iso_type = run_nix_eval(".#bootDebugISO-minimal.iso", "x: x.type")
    
    # The iso attribute should be a derivation
    assert iso_type == '"derivation"', f"iso attribute should be a derivation: {iso_type}"


def test_bootdebugiso_minimal_has_iso_attribute() -> None:
    """Test that bootDebugISO-minimal.iso exists (our custom attribute)"""
    # This should work because we set iso = isoImage in mkDerivation
    iso_drv = run_nix_eval(".#bootDebugISO-minimal.iso")
    
    # Should return a derivation
    assert "derivation" in iso_drv, f"iso attribute should be a derivation: {iso_drv}"


def test_iso_image_vs_bootdebugiso() -> None:
    """Compare isoImage derivation vs our bootDebugISO wrapper
    
    This test verifies the difference between:
    1. Returning isoImage directly
    2. Wrapping isoImage in mkDerivation
    """
    # Get the iso attribute from bootDebugISO-minimal
    # (which is our isoImage derivation)
    iso_output = run_nix_eval(".#bootDebugISO-minimal.iso", "x: x.outPath")
    iso_output = iso_output.strip('"')
    
    # Get the outPath of bootDebugISO-minimal itself
    boot_output = run_nix_eval(".#bootDebugISO-minimal.outPath")
    boot_output = boot_output.strip('"')
    
    print(f"isoImage outPath: {iso_output}")
    print(f"bootDebugISO outPath: {boot_output}")
    
    # They should be different (one is the iso builder, one is our mkDerivation wrapper)
    assert iso_output != boot_output, "iso and bootDebugISO should have different outPaths"


def test_check_name_attribute() -> None:
    """Test that bootDebugISO-minimal has a name"""
    name = run_nix_eval(".#bootDebugISO-minimal.name")
    name = name.strip('"')
    
    print(f"bootDebugISO-minimal.name: {name}")
    assert "bootDebugISO-minimal" in name, f"name should contain bootDebugISO-minimal: {name}"


def test_check_phases_attribute() -> None:
    """Test that bootDebugISO-minimal has phases"""
    cmd = [
        "nix",
        "eval",
        "--extra-experimental-features",
        "nix-command flakes",
        "--json",
        ".#bootDebugISO-minimal.phases",
    ]
    result = subprocess.run(
        cmd,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        raise RuntimeError(f"nix eval failed: {result.stderr}")
    phases = json.loads(result.stdout.strip())
    
    print(f"bootDebugISO-minimal phases: {phases}")
    # Should have phases like unpackPhase, buildPhase, etc.
    assert isinstance(phases, list), f"phases should be a list: {phases}"


def test_bootdebugiso_minimal_builder() -> None:
    """Test that bootDebugISO-minimal has a builder script"""
    builder = run_nix_eval(".#bootDebugISO-minimal.builder")
    builder = builder.strip('"')
    
    print(f"bootDebugISO-minimal builder: {builder}")
    # Should point to a real builder executable (likely bash or similar)
    assert builder.startswith("/nix/store"), f"builder should be in nix store: {builder}"
    assert builder.endswith("bash") or builder.endswith("sh"), f"builder should be shell: {builder}"


def test_bootdebugiso_minimal_args() -> None:
    """Test what arguments are passed to the builder"""
    cmd = [
        "nix",
        "eval",
        "--extra-experimental-features",
        "nix-command flakes",
        "--json",
        ".#bootDebugISO-minimal.args",
    ]
    result = subprocess.run(
        cmd,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        raise RuntimeError(f"nix eval failed: {result.stderr}")
    args = json.loads(result.stdout.strip())
    
    print(f"bootDebugISO-minimal args: {args}")
    # Should have some arguments
    assert isinstance(args, list), f"args should be a list: {args}"
    assert len(args) > 0, f"args should not be empty: {args}"


def test_bootdebugiso_minimal_drv_info() -> None:
    """Test detailed info about the derivation"""
    # Get the drvPath
    drv_path = run_nix_eval(".#bootDebugISO-minimal.drvPath")
    drv_path = drv_path.strip('"')
    
    print(f"bootDebugISO-minimal drvPath: {drv_path}")
    
    # Try to read the .drv file as text
    drv_file = Path(drv_path)
    if drv_file.exists():
        content = drv_file.read_text(errors='ignore')
        print(f"First 500 chars of .drv file:\n{content[:500]}")
        # Check if it mentions iso or ISO
        assert "iso" in content.lower(), f".drv should mention 'iso': {content[:200]}"
    else:
        print(f"Warning: .drv file doesn't exist: {drv_path}")


def test_bootdebugiso_minimal_what_is_built() -> None:
    """Test to understand what bootDebugISO-minimal evaluates to in detail"""
    # Get all interesting attributes
    attrs_to_check = [
        "type",
        "name",
        "outPath",
        "drvPath",
        "system",
        "builder",
    ]
    
    for attr in attrs_to_check:
        try:
            value = run_nix_eval(f".#bootDebugISO-minimal.{attr}")
            print(f"{attr}: {value[:100]}")
        except RuntimeError as e:
            print(f"{attr}: ERROR - {e}")


def test_isoimage_direct_access() -> None:
    """Test if we can access isoImage attribute directly"""
    # The current bootDebugISO-minimal IS the isoImage (we return it directly from flake)
    # So checking its type and outPath tells us what isoImage produces
    iso_type = run_nix_eval(".#bootDebugISO-minimal", "x: x.type")
    print(f"Type: {iso_type}")
    
    out_path = run_nix_eval(".#bootDebugISO-minimal.outPath")
    out_path = out_path.strip('"')
    print(f"OutPath: {out_path}")
    
    # Check if outPath exists and what it contains
    out_path_obj = Path(out_path)
    if out_path_obj.exists():
        print(f"Path exists. Is directory: {out_path_obj.is_dir()}")
        if out_path_obj.is_dir():
            contents = list(out_path_obj.iterdir())
            print(f"Contents: {[c.name for c in contents]}")
            
            # Look for ISO files
            iso_files = list(out_path_obj.glob("**/*.iso"))
            print(f"Found {len(iso_files)} ISO files")
            for iso_file in iso_files:
                print(f"  - {iso_file} (is_file: {iso_file.is_file()}, size: {iso_file.stat().st_size if iso_file.is_file() else 'N/A'})")
    else:
        print(f"Path does NOT exist: {out_path}")


def test_isoimage_missing_build_logic() -> None:
    """Test that confirms isoImage lacks custom build phases
    
    This test documents the root cause: isoImage derivation from
    installation-cd-minimal.nix doesn't have custom buildPhase or installPhase,
    so it uses the default stdenv builder which doesn't know how to build an ISO.
    """
    # Get all attributes that look like phases
    cmd = [
        "nix",
        "eval",
        "--extra-experimental-features",
        "nix-command flakes",
        "--json",
        "--apply",
        "x: (builtins.filter (s: builtins.match \".*[Pp]hase.*\" s != null) (builtins.attrNames x))",
        ".#bootDebugISO-minimal",
    ]
    result = subprocess.run(
        cmd,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        raise RuntimeError(f"nix eval failed: {result.stderr}")
    phases = json.loads(result.stdout.strip())
    
    print(f"Found custom phases: {phases}")
    # Should be empty - isoImage doesn't define custom build phases
    assert phases == [], f"isoImage should have no custom phases: {phases}"
    print("CONFIRMED: isoImage has no custom buildPhase or installPhase")
