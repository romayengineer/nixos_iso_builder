╔═══════════════════════════════════════════════════════════════════════════╗
║                      USB BURNING INSTRUCTIONS                             ║
╚═══════════════════════════════════════════════════════════════════════════╝

1. IDENTIFY YOUR USB DEVICE
   ━━━━━━━━━━━━━━━━━━━━━━━━━
   List all devices:
     lsblk
   
   Or use:
     sudo fdisk -l
   
   ⚠  Look for your USB device (usually /dev/sdX where X is a letter)
   ⚠  DO NOT confuse with your main hard drive!

2. UNMOUNT USB (if already mounted)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   sudo umount /dev/sdX*

3. BURN ISO TO USB
   ━━━━━━━━━━━━━━━━━
   
   METHOD A: Command Line (dd)
   ───────────────────────────
   sudo dd if={iso_display} of=/dev/sdX bs=4M status=progress conv=fsync
   sudo sync
   
   METHOD B: GUI Tools
   ──────────────────
   Use one of these applications:
     - GNOME Disks (gnome-disk-utility)
     - Balena Etcher (balena-etcher)
     - Popsicle
     - UNetbootin
   
   Steps:
     1. Open the application
     2. Select your ISO file from result/iso/
     3. Select your USB device
     4. Click Write/Burn/Start

4. EJECT USB SAFELY
   ━━━━━━━━━━━━━━━━
   sudo eject /dev/sdX

╔═══════════════════════════════════════════════════════════════════════════╗
║                              ⚠  WARNING  ⚠                               ║
║                                                                           ║
║  Replace /dev/sdX with YOUR ACTUAL USB DEVICE!                            ║
║  Using the wrong device will overwrite your data permanently!             ║
║                                                                           ║
║  Double-check lsblk output before running dd command.                     ║
╚═══════════════════════════════════════════════════════════════════════════╝