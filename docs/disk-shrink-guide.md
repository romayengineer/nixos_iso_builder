# How to Shrink Disk with Reserved MFT Space

The reserved MFT (Master File Table) space at the end of the partition is likely **the main culprit** preventing you from shrinking the disk. Here's what's happening and how to fix it:

## Why MFT Space Blocks Shrinking

Windows reserves space at the end of NTFS partitions for the Master File Table to grow. The `diskmgmt.msc` shrink function can only shrink a partition up to the last immovable file on the disk. If the MFT extension zone is at the end, it acts as a hard barrier.

## Solutions to Shrink Your Disk

### Option 1: Use a Third-Party Tool (Easiest)
Use **AOMEI Partition Assistant** or **EaseUS Partition Master** - these tools can move the MFT zone and other immovable files, allowing you to shrink further than Windows allows.

### Option 2: Defragment & Optimize (Free)
1. **In Defraggler** (which you're already using):
   - Run full defragmentation
   - Use the "Optimize" feature to move files towards the beginning of the partition
   - This may push the MFT reservation towards the usable space

2. **Disable MFT Growth Reserve**:
   - Open Command Prompt as Administrator
   - Run: `fsutil behavior set disabledeletenotify 0` (for SSDs)
   - For HDDs: Consider running `Optimize-Volume -DriveLetter X -Defrag` (PowerShell as admin)

### Option 3: Use Windows Built-in Tools
1. Run **Disk Cleanup** (`cleanmgr`) - remove temp files
2. Run **Storage Sense** (Settings > System > Storage) to clean up
3. Try shrinking again in `diskmgmt.msc`

### Option 4: Command Line (Advanced)
```
diskpart
list volume
select volume X
shrink desired=XXXX minimum=XXXX
```
(Replace X with your volume number and desired size)

## My Recommendation

**Start with Option 2** (Defraggler optimization) since you already have it. If that doesn't work, **Option 1** (AOMEI or EaseUS) is the most reliable and will definitely solve the problem - both have free versions.

The 400GB of free space is real, but Windows can only shrink to where the unmovable files end, not to where the actual data ends.
