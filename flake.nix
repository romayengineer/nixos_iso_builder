{
  description = "Custom NixOS Minimal ISO with Debug Logging";

  inputs = {
    # Pin to a stable NixOS version for reproducibility
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05";
  };

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
    in
    {
      # Build with: nix build .#bootDebugISO
      packages.${system}.bootDebugISO = (nixpkgs.lib.nixosSystem {
        inherit system;
        modules = [
          # Import minimal installation ISO base (no GUI, no graphical modules)
          "${nixpkgs}/nixos/modules/installer/cd-dvd/installation-cd-minimal.nix"

          # Custom configuration for debug logging
          ({ config, pkgs, modulesPath, ... }: {
            # ========================================
            # KERNEL LOGGING CONFIGURATION
            # ========================================
            
            # Set kernel console log level to maximum (7 = KERN_DEBUG)
            # This ensures all kernel debug messages are printed to console
            # Default is 4, which hides debug messages
            boot.consoleLogLevel = 7;

            # Enable verbose initrd output during early boot (stage-1)
            # Default is true, but explicitly set for clarity
            boot.initrd.verbose = true;

            # Kernel command-line parameters for logging
            boot.kernelParams = [
              # Maximum kernel logging verbosity
              "loglevel=2"
              
              # Systemd debug-level logging
              "systemd.log_level=debug"
              
              # Send systemd logs to console (not journal-only)
              "systemd.log_target=console"
              
              # Forward console messages to systemd journal as well
              "systemd.journald.forward_to_console=yes"
            ];

            # ========================================
            # EMERGENCY ACCESS & DEBUGGING
            # ========================================
            
            # Enable emergency shell access during initrd if boot fails
            # Allows interactive troubleshooting before stage-2
            boot.initrd.systemd.emergencyAccess = true;

            # ========================================
            # ISO IMAGE OPTIMIZATION
            # ========================================
            
            # Use lz4 compression for faster builds during development
            # Production builds could use better compression (gzip, xz)
            # but lz4 is sufficient and rebuilds much faster
            isoImage.squashfsCompression = "lz4";

            # ========================================
            # OPTIONAL: USEFUL DEBUGGING PACKAGES
            # ========================================
            
            # Add commonly needed tools for troubleshooting
            environment.systemPackages = with pkgs; [
              # System inspection
              htop
              iotop
              
              # Networking
              curl
              wget
              netcat
              
              # Text editors
              vim
              nano
              
              # Utilities
              tmux
              screen
              file
            ];


          })
        ];
      }).config.system.build.isoImage;

      # Default package for 'nix build'
      defaultPackage.${system} = self.packages.${system}.bootDebugISO;
    };
}
