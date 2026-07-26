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

      # loggingConfig: Import logging profiles from logging-config.nix
      # This provides multiple logging profiles (debug, production, info, minimal)
      # that can be selected at build time via build.py --log-level flag
      # Default profile is "debug" for maximum verbosity during troubleshooting
      loggingConfig = import ./logging-config.nix;
      
      # Helper function to create a boot ISO with a specific logging profile
      # Usage: mkBootISO "debug" or mkBootISO "production"
      mkBootISO = (profileName:
        let
          logs = loggingConfig.${profileName};
        in
        (nixpkgs.lib.nixosSystem {
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

              # Custom configuration using logging profile
              # This section uses variables from the logging-config.nix file
              # The selected profile (logs) determines all logging behavior
              ({ config, pkgs, modulesPath, ... }: {
              # ========================================
              # KERNEL & SYSTEMD LOGGING CONFIGURATION
              # ========================================
              # All settings below come from the selected logging profile
              # See logging-config.nix for profile definitions
              
              # boot.consoleLogLevel: Kernel console log level (from logs)
              # Uses: logs.consoleLogLevel
              boot.consoleLogLevel = logs.consoleLogLevel;

              # boot.initrd.verbose: Enable verbose early boot output (from logs)
              # Uses: logs.initrdVerbose
              boot.initrd.verbose = logs.initrdVerbose;

              # boot.kernelParams: Kernel command-line parameters (from logs)
              # Constructed from logging profile values
              boot.kernelParams = [
                "loglevel=${builtins.toString logs.kernelLogLevel}"
                "systemd.log_level=${logs.systemdLogLevel}"
                "systemd.log_target=${logs.systemdLogTarget}"
                "systemd.journald.forward_to_console=${logs.journaldForwardConsole}"
              ];

              # ========================================
              # EMERGENCY ACCESS & DEBUGGING
              # ========================================
              
               # boot.initrd.systemd.emergencyAccess: Emergency shell on boot failure
               # Uses: logs.emergencyAccess
               # true  = Interactive shell if initrd fails (for debugging)
               # false = Panic without shell (for production/security)
               # Use lib.mkForce to override the default from iso-image.nix
               boot.initrd.systemd.emergencyAccess = nixpkgs.lib.mkForce logs.emergencyAccess;

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
         }).config.system.build.isoImage
       );
    in
    {
      # packages: Derivations (buildable things) this flake provides
      # Create separate package outputs for each logging profile
      # Usage: nix build .#bootDebugISO-debug     (max verbosity)
      #        nix build .#bootDebugISO-info      (balanced)
      #        nix build .#bootDebugISO-production (minimal)
      #        nix build .#bootDebugISO-minimal    (quiet)
      packages.${system} = {
        bootDebugISO-debug = mkBootISO "debug";
        bootDebugISO-info = mkBootISO "info";
        bootDebugISO-production = mkBootISO "production";
        bootDebugISO-minimal = mkBootISO "minimal";
        bootDebugISO = mkBootISO "debug";  # Default: debug profile
      };

      # defaultPackage: Package used when user runs 'nix build' without #attribute
      # Range: Any package in packages.${system}
      # Defaults to debug profile (maximum verbosity for troubleshooting)
      defaultPackage.${system} = self.packages.${system}.bootDebugISO;
    };
  }
