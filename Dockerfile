FROM nixos/nix:latest

# Install build dependencies via Nix
RUN nix-env -iA nixpkgs.python3 nixpkgs.gnumake

# Pre-configure Nix for flakes
RUN mkdir -p /root/.config/nix && \
    echo "experimental-features = nix-command flakes" > /root/.config/nix/nix.conf

WORKDIR /build

# Copy only the files needed for Nix input fetching first (for layer caching)
COPY flake.nix flake.lock logging-config.nix ./

# Pre-fetch nixpkgs with submodules so it's cached in the image layer
# Subsequent builds reuse this cached source instead of cloning from scratch
RUN nix flake lock --update-input nixpkgs --extra-experimental-features "nix-command flakes"

# git safe directory for mounted volumes
RUN git config --global safe.directory '*'

# Copy the rest of the project files
COPY . .

# Default command: build with debug logging
CMD ["python3", "./build.py", "build"]
