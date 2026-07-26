# USB Burning Instructions

## Steps

### 1. Insert USB drive

Insert your USB drive into a USB port.

### 2. Identify device

Run:
```bash
sudo lsblk
```

Look for your device (e.g., `/dev/sdb`, `/dev/sdc`). Note the full device path.

### 3. Unmount USB (if auto-mounted)

If your system auto-mounts the USB:
```bash
sudo umount /dev/sdX*
```

Replace `sdX` with your actual device identifier (e.g., `sdb`).

### 4. Write ISO to USB

```bash
sudo dd if={ISO_PATH} of=/dev/sdX bs=4M status=progress
```

Replace:
- `{ISO_PATH}` with the full path to your NixOS ISO file
- `sdX` with your actual device (e.g., `sdb`, `sdc`)

### 5. Sync and eject

```bash
sudo sync && sudo eject /dev/sdX
```

## ⚠️ WARNING

**`dd` will overwrite the ENTIRE USB drive!**

- **Triple-check your device identifier before running `dd`**
- Using the wrong device could delete important data
- Make sure you're targeting the USB drive, not your system drive

## Examples

If your ISO is at `/home/user/nixos.iso` and USB is `/dev/sdb`:

```bash
sudo dd if=/home/user/nixos.iso of=/dev/sdb bs=4M status=progress
sudo sync && sudo eject /dev/sdb
```

## Verify Success

After ejecting, the USB drive should no longer appear in `lsblk`.
