#!/bin/bash

# Take hex response as command line argument
input=$1

# Check if input was provided
if [ -z "$input" ]; then
    echo "Usage: ./decode.sh <hex_response>"
    echo "Example: ./decode.sh 0x000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000a0..."
    exit 1
fi

# Remove 0x prefix from input
HEX_DATA=${input#0x}

# --- Decoding based on character positions in the hex string ---

# Password hash (Chars 193-256)
PASSWORD_HASH="0x$(echo "$HEX_DATA" | cut -c 193-256)"

# Download value (Chars 257-320)
DOWNLOAD_DEC=$(printf "%d" "0x$(echo "$HEX_DATA" | cut -c 257-320)")

# Upload value (Chars 321-384)
UPLOAD_DEC=$(printf "%d" "0x$(echo "$HEX_DATA" | cut -c 321-384)")

# Username length in bytes (Chars 385-448)
USERNAME_LEN=$(printf "%d" "0x$(echo "$HEX_DATA" | cut -c 385-448)")

# Username hex data, located in the block at Chars 449-512
USERNAME_HEX=$(echo "$HEX_DATA" | cut -c 449-$((449 + USERNAME_LEN * 2 - 1)))
USERNAME_STR=$(echo "$USERNAME_HEX" | xxd -r -p)

# Salt length in bytes (Chars 513-576)
SALT_LEN=$(printf "%d" "0x$(echo "$HEX_DATA" | cut -c 513-576)")

# Salt hex data, located in the block at Chars 577-640
SALT_HEX=$(echo "$HEX_DATA" | cut -c 577-$((577 + SALT_LEN * 2 - 1)))
SALT_STR=$(echo "$SALT_HEX" | xxd -r -p)

# --- Output the results ---
echo "=== Decoded UserData ==="
echo "Username:      '$USERNAME_STR'"
echo "Salt:          '$SALT_STR'"
echo "Password Hash: $PASSWORD_HASH"
echo "Download:      $DOWNLOAD_DEC"
echo "Upload:        $UPLOAD_DEC"