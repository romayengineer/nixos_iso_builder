################################################################################
# ⚠️  IMPORTANT: KEEP EXTENSIVE COMMENTS IN THIS FILE
################################################################################
#
# Logging configuration profiles for NixOS debug ISO builds
# This file defines multiple logging profiles that can be selected at build time
# by using the --log-level flag in build.py
#
# Usage in build.py:
#   ./build.py build --log-level debug      (maximum verbosity for troubleshooting)
#   ./build.py build --log-level production (minimal logs for deployment)
#   ./build.py build --log-level minimal    (quiet mode, errors only)
#
# Usage in flake.nix:
#   loggingConfig = import ./logging-config.nix;
#   logs = loggingConfig.${profileName};  # profileName = "debug", "production", etc
#
# Each profile returns an attribute set with logging configuration options
# that can be directly used in boot.* and kernel parameters
#
################################################################################

{
  # ============================================================================
  # DEBUG PROFILE: Maximum verbosity for troubleshooting failed boots
  # ============================================================================
  # Use this profile when investigating boot failures and system issues
  # Output will be very verbose with all kernel/systemd debug messages
  debug = {
    # boot.consoleLogLevel: Kernel console log level
    # 7 = KERN_DEBUG - show ALL kernel messages including debug
    consoleLogLevel = 7;

    # boot.initrd.verbose: Enable verbose early boot output
    # true = show all initrd (stage-1) initialization messages
    initrdVerbose = true;

    # loglevel: Kernel command-line logging level
    # 7 = DEBUG - all kernel messages at runtime
    kernelLogLevel = 7;

    # systemd.log_level: Systemd (init system) logging level
    # "debug" = all systemd messages including debug details
    systemdLogLevel = "debug";

    # systemd.log_target: Where systemd logs are sent
    # "console" = visible on screen during boot (useful for debugging)
    systemdLogTarget = "console";

    # systemd.journald.forward_to_console: Forward journal to console
    # "yes" = console sees both early and late-boot messages
    journaldForwardConsole = "yes";

    # boot.initrd.systemd.emergencyAccess: Emergency shell on initrd failure
    # true = drop to interactive shell if early boot fails (for manual debugging)
    emergencyAccess = true;

    # Short description for user feedback
    description = "Debug: Maximum verbosity (troubleshooting)";
  };

  # ============================================================================
  # PRODUCTION PROFILE: Minimal useful logging for deployment
  # ============================================================================
  # Use this profile for production deployments where you want to catch real issues
  # without flooding logs with debug noise
  production = {
    # boot.consoleLogLevel: Kernel console log level
    # 3 = KERN_ERR - show errors and above
    # This captures real problems without debug spam
    consoleLogLevel = 3;

    # boot.initrd.verbose: Enable verbose early boot output
    # false = minimal initrd output (faster boot)
    initrdVerbose = false;

    # loglevel: Kernel command-line logging level
    # 3 = ERR - only show errors and above at runtime
    kernelLogLevel = 3;

    # systemd.log_level: Systemd (init system) logging level
    # "err" = only show errors (filters out info/debug spam)
    systemdLogLevel = "err";

    # systemd.log_target: Where systemd logs are sent
    # "console" = still show errors on screen (safety net)
    systemdLogTarget = "console";

    # systemd.journald.forward_to_console: Forward journal to console
    # "no" - don't forward (logs go to journal only, readable via journalctl)
    journaldForwardConsole = "no";

    # boot.initrd.systemd.emergencyAccess: Emergency shell on initrd failure
    # false = panic on failure (security: no interactive shell)
    emergencyAccess = false;

    # Short description for user feedback
    description = "Production: Minimal logging (errors only)";
  };

  # ============================================================================
  # MINIMAL PROFILE: Quiet mode - only emergencies
  # ============================================================================
  # Use this profile for silent operation where you only care about critical failures
  # Useful for automated deployments and CI/CD pipelines
  minimal = {
    # boot.consoleLogLevel: Kernel console log level
    # 2 = KERN_CRIT - show critical conditions only
    consoleLogLevel = 2;

    # boot.initrd.verbose: Enable verbose early boot output
    # false = minimal initrd output
    initrdVerbose = false;

    # loglevel: Kernel command-line logging level
    # 2 = CRIT - only critical messages
    kernelLogLevel = 2;

    # systemd.log_level: Systemd (init system) logging level
    # "crit" = only critical conditions
    systemdLogLevel = "crit";

    # systemd.log_target: Where systemd logs are sent
    # "journal" - minimal console output (logs go to journal only)
    systemdLogTarget = "journal";

    # systemd.journald.forward_to_console: Forward journal to console
    # "no" - no console clutter
    journaldForwardConsole = "no";

    # boot.initrd.systemd.emergencyAccess: Emergency shell on initrd failure
    # false = panic without shell (minimal interaction)
    emergencyAccess = false;

    # Short description for user feedback
    description = "Minimal: Quiet mode (critical only)";
  };

  # ============================================================================
  # INFO PROFILE: Balanced logging for general use
  # ============================================================================
  # Use this profile for normal operation with useful information without debug spam
  # Good for initial testing and general troubleshooting
  info = {
    # boot.consoleLogLevel: Kernel console log level
    # 6 = KERN_INFO - show info messages and above
    consoleLogLevel = 6;

    # boot.initrd.verbose: Enable verbose early boot output
    # true = show initialization messages (useful for understanding boot process)
    initrdVerbose = true;

    # loglevel: Kernel command-line logging level
    # 6 = INFO - informational messages at runtime
    kernelLogLevel = 6;

    # systemd.log_level: Systemd (init system) logging level
    # "info" = informational messages and above (no debug spam)
    systemdLogLevel = "info";

    # systemd.log_target: Where systemd logs are sent
    # "console" = visible on screen (helpful during boot)
    systemdLogTarget = "console";

    # systemd.journald.forward_to_console: Forward journal to console
    # "yes" - see all messages
    journaldForwardConsole = "yes";

    # boot.initrd.systemd.emergencyAccess: Emergency shell on initrd failure
    # true = drop to shell if something fails (interactive troubleshooting)
    emergencyAccess = true;

    # Short description for user feedback
    description = "Info: Balanced logging (troubleshooting)";
  };

  # ============================================================================
  # PROFILE REFERENCE TABLE
  # ============================================================================
  #
  # Profile     | Console | Initrd | Systemd    | Target  | Emergency | Use Case
  # ──────────────────────────────────────────────────────────────────────────
  # debug       | 7       | true   | debug      | console | true      | Troubleshooting boot failures
  # info        | 6       | true   | info       | console | true      | Initial testing
  # production  | 3       | false  | err        | console | false     | Deployment (catch errors)
  # minimal     | 2       | false  | crit       | journal | false     | CI/CD (silent operation)
  #
  # Legend:
  #   Console   = boot.consoleLogLevel (0-7 scale)
  #   Initrd    = boot.initrd.verbose (true/false)
  #   Systemd   = systemd.log_level
  #   Target    = systemd.log_target
  #   Emergency = boot.initrd.systemd.emergencyAccess
  #
}
