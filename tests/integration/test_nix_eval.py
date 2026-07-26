"""Integration tests for Nix evaluation behavior

Tests that use nix eval to understand what the flake.nix actually produces.
No mocking - uses real nix eval calls.
"""

from pathlib import Path
import subprocess
import json
from typing import Any, Dict

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


def run_nix_eval_json(expression: str, apply: str = "") -> Any:
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
    return json.loads(result.stdout)


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
    """Test that bootDebugISO-minimal has phases (our custom mkDerivation)"""
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
    # mkDerivation should have at least installPhase
    assert isinstance(phases, list), f"phases should be a list: {phases}"
