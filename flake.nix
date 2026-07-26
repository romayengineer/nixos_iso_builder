################################################################################
# ⚠️  IMPORTANT: KEEP EXTENSIVE COMMENTS IN THIS FILE
################################################################################
#
# This file serves as a TEMPLATE for all .nix files in this project.
# Every configuration option MUST include comprehensive documentation:
#
#   • What it does (purpose and function)
#   • Valid ranges (acceptable values or value types)
#   • Value meanings (what each value produces)
#   • Current setting (clearly marked)
#   • Recommended settings (marked for debugging/production)
#   • When to change (reasons to modify this setting)
#
# WHY THIS MATTERS:
#   • Nix syntax is unfamiliar; comments bridge understanding
#   • NixOS options interact; documentation prevents mistakes
#   • Future maintainers depend on clear explanations
#   • Reproducibility requires documenting design decisions
#
# ENFORCEMENT:
#   • All modifications must update comments alongside code
#   • New .nix files must follow this standard from creation
#   • PRs without adequate documentation will be rejected
#
# REFERENCE: See AGENTS.md section "Code Quality Standards: .nix File Documentation"
#
# This file: 227 lines total, 159 comment lines (70% documentation)
# Goal: Make every setting self-documenting and easy to modify
#
################################################################################

{
  # Flake description: Brief summary of what this flake builds
  # Used by 'nix flake show' and package managers
  description = "Custom NixOS Minimal ISO with Debug Logging";

  # inputs: External dependencies and packages used by this flake
  # These are fetched from GitHub/channels and pinned to specific versions
  inputs = {
    # nixpkgs: The official NixOS package collection and modules
    # url format: github:OWNER/REPO/REF
    # REF options:
    #   nixos-26.05  - Latest stable branch (2026 May release) - RECOMMENDED
    #   nixos-unstable - Rolling release (bleeding edge, may have issues)
    #   nixos-25.11  - Previous stable release
    #   main         - Latest development branch
    # Pinning to a specific branch ensures reproducible builds across time
    # All machines using this flake will get the same versions
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05";
  };

  # outputs: What this flake produces (build outputs)
  # Takes inputs as arguments and produces derivations (build recipes)
  outputs = { self, nixpkgs }:
    let
      # system: Target architecture for the build
      # Range: "x86_64-linux", "aarch64-linux", "x86_64-darwin", "aarch64-darwin"
      # "x86_64-linux" = 64-bit Intel/AMD Linux (most common for server/desktop)
      # "aarch64-linux" = ARM 64-bit Linux (Raspberry Pi, embedded systems)
      system = "x86_64-linux";
      
      # pkgs: Pre-packaged software available for this system
      # nixpkgs.legacyPackages.${system} provides all nixpkgs packages
      # used in environment.systemPackages list below
      pkgs = nixpkgs.legacyPackages.${system};
    in
    {
      # packages: Derivations (buildable things) this flake provides
      # Access with: nix build .#bootDebugISO
      # packages.${system}.PACKAGE_NAME = definition
      # This creates a package called "bootDebugISO" for x86_64-linux
      packages.${system}.bootDebugISO = (nixpkgs.lib.nixosSystem {
        # Build for the system defined above
        inherit system;
        
        # modules: NixOS configuration modules to merge
        # Modules are composable configuration files that set options
        # They are evaluated left-to-right with later ones overriding earlier
        modules = [
          # installation-cd-minimal.nix: Base NixOS ISO configuration
          # Provided by nixpkgs, sets up:
          #   - Minimal (no GUI) ISO filesystem
          #   - Boot loader (GRUB/UEFI)
          #   - Installer (nixos-install script)
          #   - Basic system packages
          # We import this as the base and then add our debug logging on top
          "${nixpkgs}/nixos/modules/installer/cd-dvd/installation-cd-minimal.nix"

           # Custom configuration for debug logging
           ({ config, pkgs, modulesPath, ... }: {
             # ========================================
             # KERNEL LOGGING CONFIGURATION
             # ========================================
             
             # boot.consoleLogLevel: Kernel console log level
             # Range: 0-7 (integer)
             # Levels (KERN_* kernel log levels):
             #   0 = KERN_EMERG     - System is unusable (emergency only)
             #   1 = KERN_ALERT     - Action must be taken immediately
             #   2 = KERN_CRIT      - Critical conditions
             #   3 = KERN_ERR       - Error conditions
             #   4 = KERN_WARNING   - Warning conditions (DEFAULT)
             #   5 = KERN_NOTICE    - Normal but significant conditions
             #   6 = KERN_INFO      - Informational messages
             #   7 = KERN_DEBUG     - Debug-level messages (MAXIMUM VERBOSITY)
             # Set to 7 for maximum kernel debug output to console
             boot.consoleLogLevel = 7;

             # boot.initrd.verbose: Enable verbose output during early boot (stage-1)
             # Range: true | false (boolean)
             # true  = Show all initrd initialization messages
             # false = Minimal output during boot
             # Default: true
             # Set to true to capture all early-boot debugging information
             boot.initrd.verbose = true;

             # boot.kernelParams: Kernel command-line parameters passed at boot
             # These are appended to the kernel command line and control runtime behavior
             boot.kernelParams = [
               # loglevel: Kernel logging level for runtime messages
               # Range: 0-7 (integer)
               # Same levels as boot.consoleLogLevel above
               # Values:
               #   0 = EMERG  - Only show emergencies
               #   1 = ALERT  - Show alerts and emergencies
               #   2 = CRIT   - Show critical messages and above (many use this for boot)
               #   3 = ERR    - Show errors and above
               #   4 = WARN   - Show warnings and above (DEFAULT kernel behavior)
               #   5 = NOTICE - Show notices and above
               #   6 = INFO   - Show info messages and above
               #   7 = DEBUG  - Show all messages including debug (MAXIMUM)
               # Set to 7 for maximum verbosity, but 2-3 captures most boot failures
               "loglevel=7"
               
               # systemd.log_level: Systemd (init system) logging level
               # Range: emerg, alert, crit, err, warning, notice, info, debug
               # Levels (in order of verbosity):
               #   emerg   - System is unusable
               #   alert   - Action must be taken immediately
               #   crit    - Critical conditions only
               #   err     - Error conditions and above
               #   warning - Warnings and above (DEFAULT)
               #   notice  - Normal but significant messages and above
               #   info    - Informational messages and above
               #   debug   - All messages including debug details (MAXIMUM)
               # Set to "debug" to capture all systemd/service startup messages
               "systemd.log_level=debug"
               
               # systemd.log_target: Where systemd logs are sent
               # Range: console, journal, kmsg, syslog, null, auto
               # Options:
               #   console  - Send to /dev/console (appears on screen during boot)
               #   journal  - Send to systemd journal only (readable via journalctl post-boot)
               #   kmsg     - Send to kernel log buffer (captured by dmesg)
               #   syslog   - Send to syslog daemon (if available)
               #   null     - Discard all logs (not useful for debugging)
               #   auto     - Auto-detect best target (DEFAULT)
               # Set to "console" to see logs on screen during early boot failures
               "systemd.log_target=console"
               
               # systemd.journald.forward_to_console: Forward journal logs to console
               # Range: 0 or 1 (yes/no, true/false)
               # 0/no/false   - Don't forward journal messages to console
               # 1/yes/true   - Forward all journal messages to /dev/console
               # DEFAULT: Depends on whether systemd-journald is configured
               # Set to "yes" so console sees both early and late-boot messages
               "systemd.journald.forward_to_console=yes"
             ];

             # ========================================
             # EMERGENCY ACCESS & DEBUGGING
             # ========================================
             
             # boot.initrd.systemd.emergencyAccess: Enable emergency shell in initrd
             # Range: true | false (boolean)
             # true  = Drop to emergency shell if initrd fails during boot
             #         Allows manual troubleshooting of early-boot issues
             #         Type "exit" to resume boot or reboot
             # false = Continue to panic without shell access
             # DEFAULT: false (emergency shell usually disabled for security)
             # Set to true for interactive debugging during failed boot
             boot.initrd.systemd.emergencyAccess = true;

             # ========================================
             # ISO IMAGE OPTIMIZATION
             # ========================================
             
             # isoImage.squashfsCompression: Compression algorithm for SquashFS ISO
             # SquashFS is the read-only filesystem used in NixOS ISOs to pack
             # the entire nix store into a compressed image
             # Range: lz4, zstd, gzip, xz, lzma (string)
             # Compression vs. Speed tradeoffs:
             #   lz4    - FAST (fastest decompression, 60-90MB/s)
             #            Compression: ~40% ratio
             #            Use: Development/testing, fastest ISO boot
             #   zstd   - BALANCED (good speed, good compression)
             #            Compression: ~35% ratio, medium speed
             #            Use: Balanced production builds
             #   gzip   - GOOD compression (slower than zstd)
             #            Compression: ~33% ratio
             #            Use: Production, slower boot acceptable
             #   xz     - EXCELLENT compression (very slow decompression)
             #            Compression: ~25% ratio
             #            Use: Download size critical, boot speed not critical
             #   lzma   - Similar to xz, older format
             # Set to "lz4" for development (fast rebuilds)
             # Set to "zstd" or "xz" for production distributions
             isoImage.squashfsCompression = "lz4";

             # ========================================
             # OPTIONAL: USEFUL DEBUGGING PACKAGES
             # ========================================
             
             # environment.systemPackages: Additional packages included in the ISO
             # These tools are included in the live environment for troubleshooting
             # larger package list = larger ISO size (trade-off)
             # Range: List of nix package names (from nixpkgs)
             environment.systemPackages = with pkgs; [
               # System inspection tools
               htop              # Interactive process monitor (like top but better)
               iotop             # I/O performance monitoring by process
               
               # Networking tools
               curl              # Command-line HTTP/HTTPS client
               wget              # Download files from network
               netcat            # Network debugging (read/write TCP/UDP)
               
               # Text editors (choose based on preference)
               vim               # Advanced text editor
               nano              # Simple terminal text editor
               
               # Terminal utilities
               tmux              # Terminal multiplexer (split windows, sessions)
               screen            # Terminal multiplexer (alternative to tmux)
               file              # Identify file types by content
             ];


           })
         ];
       
       # .config.system.build.isoImage: Extract the ISO image builder
       # nixosSystem returns a full system evaluation with many outputs
       # .config.system.build.isoImage = the ISO binary (bootable image file)
       # Alternative outputs available:
       #   .config.system.build.kernel     - Just the kernel
       #   .config.system.build.initrd     - Just the initrd (early boot)
       #   .config.system.build.toplevel   - Full system closure (everything)
       # We only need the ISO image for this build
       }).config.system.build.isoImage;

       # defaultPackage: Package used when user runs 'nix build' without #attribute
       # Range: Any package in packages.${system}
       # Alternative: Could remove this line and user would need 'nix build .#bootDebugISO'
       # With this line, 'nix build' alone is sufficient (convenience)
       defaultPackage.${system} = self.packages.${system}.bootDebugISO;
     };
 }
