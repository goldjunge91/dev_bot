#!/bin/bash

# Define paths
SOURCE_CONFIG="$HOME/dev_bot/src/gubot_one/cycloneDDS/raspi_cyclonedds.xml"
DEST_CONFIG="/var/tmp/cyclonedds.xml"

echo "Setting up CycloneDDS..."

# Check if source exists
if [ ! -f "$SOURCE_CONFIG" ]; then
    echo "❌ Error: Source config not found at $SOURCE_CONFIG"
    exit 1
fi

# Copy the file
echo "Copying config from repo to $DEST_CONFIG..."
cp "$SOURCE_CONFIG" "$DEST_CONFIG"

# Verify
if [ -f "$DEST_CONFIG" ]; then
    echo "✅ Success! Config installed to $DEST_CONFIG."
    echo "Tailscale Peers configured:"
    grep "Peer Address" "$DEST_CONFIG"
else
    echo "❌ Error: Copy failed."
    exit 1
fi
