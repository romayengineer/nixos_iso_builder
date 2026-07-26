# QEMU Testing Guide for Windows WSL

How to test the custom NixOS minimal ISO with debug logging in QEMU on Windows/WSL.

## Quick Start

### If you're on WSL (Linux command line):
```bash
./build.sh test
```

### If you're on Windows (Command Prompt/PowerShell):
Copy the ISO path from WSL and run QEMU natively on Windows.

---

## Option 1: QEMU in WSL (Linux - Recommended)

Best for: Quick testing, terminal-based debugging, no display server setup needed.

### Setup

```bash
# Install QEMU in WSL
sudo apt update
sudo apt install qemu-system-x86

# Verify installation
qemu-system-x86_64 --version
```

### Run the Test

**Method A: Using the build script**
```bash
./build.sh test
```

**Method B: Direct QEMU command (without KVM - works on WSL)**
```bash
cd /mnt/c/Users/Admin/Documents/Projects/nixos
# Run WITHOUT -enable-kvm (KVM not available in WSL)
qemu-system-x86_64 -m 512 -cdrom result/iso/nixos-*.iso
```

**Note on KVM:** WSL doesn't support KVM (Kernel-based Virtual Machine). The `-enable-kvm` flag will fail with "Permission denied". QEMU will automatically fall back to TCG (Tiny Code Generator) which is slower but still works fine for testing.

### What to Expect

You'll see kernel boot messages in the terminal:
```
[    0.000000] Linux version 6.18.39 (nixbld@...) (gcc (GCC) 15.2.0, GNU ld ...)
[    0.000000] Command line: ... loglevel=7 systemd.log_level=debug ...
[    0.000000] KERNEL supported cpus:
...
```

The ISO will boot to a graphical console (no display window on Windows, but you'll see text output in WSL terminal).

**To exit QEMU:**
- Press `Ctrl+A` then `X` (or `Ctrl+C`)
- Or close the console window if one appears

### Pros & Cons

| Pros | Cons |
|------|------|
| Native Linux, best performance | Requires QEMU installed in WSL |
| ISO already on WSL filesystem | No graphical window (terminal only) |
| Works with `./build.sh test` | Display setup needed for GUI |
| Simple command | May need X11 forwarding for graphical mode |

---

## Option 2: QEMU on Windows (Native)

Best for: Graphical testing, if you prefer Windows-based tools, side-by-side development.

### Setup

**Method A: Download from qemu.org**
1. Download QEMU installer from https://www.qemu.org/download/#windows
2. Install to default location (usually `C:\Program Files\qemu`)
3. Add QEMU to PATH (installer should do this)

**Method B: Using Chocolatey (if installed)**
```powershell
choco install qemu
```

**Method C: Using WinGet (Windows 11+)**
```powershell
winget install QEMU.QEMU
```

### Find ISO Path

In WSL, get the absolute path to the ISO:
```bash
wslpath -w /mnt/c/Users/Admin/Documents/Projects/nixos/result/iso/nixos-*.iso
```

This converts the WSL path to a Windows path like:
```
C:\Users\Admin\Documents\Projects\nixos\result\iso\nixos-minimal-26.05.20260724.597283a-x86_64-linux.iso
```

### Run QEMU

**From Windows Command Prompt (cmd.exe):**
```cmd
qemu-system-x86_64.exe -enable-kvm -m 512 -cdrom "C:\Users\Admin\Documents\Projects\nixos\result\iso\nixos-minimal-26.05.20260724.597283a-x86_64-linux.iso"
```

**From Windows PowerShell:**
```powershell
& 'C:\Program Files\qemu\qemu-system-x86_64.exe' -enable-kvm -m 512 -cdrom "C:\Users\Admin\Documents\Projects\nixos\result\iso\nixos-minimal-26.05.20260724.597283a-x86_64-linux.iso"
```

**Create a batch file for easy reuse:**

Save this as `test-iso.bat` in your project folder:
```batch
@echo off
REM Test NixOS debug ISO in QEMU
cd /D "%~dp0"
for /f %%i in ('wsl wslpath -w "$(wsl pwd)/result/iso/nixos-*.iso"') do (
    "C:\Program Files\qemu\qemu-system-x86_64.exe" -enable-kvm -m 512 -cdrom "%%i"
)
```

Then just double-click `test-iso.bat` to run it.

### What to Expect

A QEMU window will open showing:
- Boot loader menu
- Kernel boot messages scrolling down
- NixOS logo and system messages
- Interactive shell prompt (if boot succeeds)

**To exit QEMU:**
- Close the QEMU window, or
- Press `Alt+F4`

### Pros & Cons

| Pros | Cons |
|------|------|
| Graphical window on Windows | Separate QEMU install needed |
| No WSL terminal overhead | ISO path conversion required |
| Familiar Windows interface | Slightly slower (Windows emulation layer) |
| Easy to use for GUI testing | `-enable-kvm` may not work (warning is OK) |

---

## Option 3: QEMU in WSL with Display Forwarding (Advanced)

Best for: Full graphical boot testing with QEMU running natively in Linux.

### Requirements

- **Windows 11 with WSLg installed**, OR
- **Windows 10/11 with VcXsrv X11 server**

### Method A: Using WSLg (Windows 11+, Easiest)

WSL 2 on Windows 11 includes automatic X11 display forwarding. Just run:

```bash
# Install QEMU in WSL
sudo apt install qemu-system-x86

# Run with display (will open in Windows)
./build.sh test
```

QEMU will automatically display in a Windows window using WSLg.

### Method B: Using VcXsrv (Windows 10 / Manual)

1. **Download & install VcXsrv** from https://sourceforge.net/projects/vcxsrv/

2. **Start VcXsrv** (XLaunch):
   - Choose "Multiple windows"
   - Display number: `:0` (or `-1`)
   - Uncheck "Native OpenGL" if you get issues
   - Check "Disable access control"
   - Finish

3. **In WSL, set display variable:**
   ```bash
   export DISPLAY=:0
   ```

4. **Run QEMU:**
   ```bash
   ./build.sh test
   ```

### What to Expect

A QEMU graphical window will appear on your Windows desktop showing the ISO booting with full graphics.

### Pros & Cons

| Pros | Cons |
|------|------|
| Native Linux performance | Complex setup (VcXsrv) |
| Full graphical boot | Requires WSLg or X11 server |
| ISO on WSL filesystem | Potential display lag |
| Automatic with WSLg on Win11 | More dependencies |

---

## Debugging Tips

### View Boot Messages in QEMU

When QEMU boots, watch the console for:

```
[    0.000000] Linux version 6.18.39
[    0.000000] Command line: ... loglevel=7 systemd.log_level=debug systemd.log_target=console
[    0.X] systemd[1]: Started System Logging Service.
```

Debug messages should scroll by automatically. If boot fails, look for error messages.

### Capture Output to File

**In WSL:**
```bash
qemu-system-x86_64 -enable-kvm -m 512 -cdrom result/iso/nixos-*.iso 2>&1 | tee qemu-boot.log
```

Then check `qemu-boot.log` for error details.

### Common Issues

**Issue: `Could not access KVM kernel module: Permission denied` in WSL (⚠️ Common)**
- **Why:** WSL doesn't have access to the host's KVM hardware virtualization module. KVM is only available on native Linux with hardware support.
- **Solution:** Remove the `-enable-kvm` flag and let QEMU use TCG (Tiny Code Generator) instead:
  ```bash
  # DON'T use -enable-kvm in WSL
  qemu-system-x86_64 -m 512 -cdrom result/iso/nixos-*.iso
  ```
- **Performance:** TCG is slower than KVM (slower CPU emulation), but still boots and works fine for testing. Boot will take 1-2 minutes instead of seconds.
- **Updated:** The `build.sh test` command has been updated to handle this automatically.

**Issue: QEMU window is very small or unreadable**
- **Solution:** Add `serial -mon chardev=mon0` to redirect console to terminal:
  ```bash
  qemu-system-x86_64 -m 512 -cdrom result/iso/nixos-*.iso -serial stdio
  ```

**Issue: QEMU hangs or is very slow**
- **Solution:** Increase RAM and disable KVM:
  ```bash
  qemu-system-x86_64 -m 1024 -cdrom result/iso/nixos-*.iso
  ```

**Issue: "qemu-system-x86_64: command not found" in WSL**
- **Solution:** Install QEMU:
  ```bash
  sudo apt install qemu-system-x86
  ```

**Issue: Can't find ISO path on Windows**
- **Solution:** Run in WSL to get Windows path:
  ```bash
  ls -lh result/iso/nixos-*.iso  # Verify ISO exists
  wslpath -w "$(pwd)/result/iso/nixos-*.iso"  # Convert to Windows path
  ```

---

## Performance Comparison

| Method | Performance | Setup Difficulty | Graphical |
|--------|-------------|------------------|-----------|
| **WSL (Option 1)** | ⭐⭐⭐⭐⭐ Native | ⭐ Easy | Text output |
| **Windows Native (Option 2)** | ⭐⭐⭐⭐ Good | ⭐⭐ Medium | Yes |
| **WSL + Display (Option 3)** | ⭐⭐⭐⭐⭐ Native | ⭐⭐⭐ Hard | Yes |

---

## Recommended Path

### For Quick Testing (Recommended for Debug Logging):
```bash
# In WSL terminal
sudo apt install qemu-system-x86
./build.sh test
```

Console output is perfect for debugging kernel and systemd messages. No extra setup needed.

### For Full Graphical Testing:
- **Windows 11:** Just run `./build.sh test` - WSLg handles display
- **Windows 10:** Install VcXsrv, then run `./build.sh test`
- **Alternative:** Use Windows QEMU installer instead of WSL

---

## References

- QEMU Documentation: https://www.qemu.org/docs/
- WSLg (Windows 11): https://github.com/microsoft/wslg
- VcXsrv: https://sourceforge.net/projects/vcxsrv/
- NixOS Manual: https://nixos.org/manual/nixos/stable/
