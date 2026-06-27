#!/bin/bash
set -e

MODULE_ID="${MODULE_ID:-ronspotipy}"
MODULE_NAME="${MODULE_NAME:-Ronspotipy}"
MODULE_AUTHOR="${MODULE_AUTHOR:-ronspotipy}"
OUT_DIR="out"
TEMPLATE="module-template"
MODDED_APK="modded.apk"

if [ ! -f "$MODDED_APK" ]; then
    echo "Error: modded.apk not found. Run patch step first." >&2
    exit 1
fi

mkdir -p "$OUT_DIR"

# Build numeric version from current date
VERCODE=$(date +%Y%m%d%H%M)

# Extract APK version (prefer env var, fallback to APK manifest)
if [ -n "$SPOTIFY_VERSION" ]; then
  VER="$SPOTIFY_VERSION"
else
  VER=$(python3 -c "
import zipfile, re
with zipfile.ZipFile('$MODDED_APK') as z:
    with z.open('AndroidManifest.xml') as f:
        c = f.read()
        m = re.search(rb'versionName[=:][\"\\x27]([\d.]+)[\"\\x27]', c)
        print(m.group(1).decode() if m else 'unknown')
")
fi

MODULE_DIR="$OUT_DIR/$MODULE_ID"

# Clean and create fresh module dir
rm -rf "$MODULE_DIR"
mkdir -p "$MODULE_DIR"

# Copy module template
cp -r "$TEMPLATE/META-INF" "$MODULE_DIR/"
cp -r "$TEMPLATE/bin" "$MODULE_DIR/"
cp "$TEMPLATE/customize.sh" "$MODULE_DIR/"
cp "$TEMPLATE/service.sh" "$MODULE_DIR/"
cp "$TEMPLATE/uninstall.sh" "$MODULE_DIR/"

# Create config
cat > "$MODULE_DIR/config" <<EOF
PKG_NAME=com.spotify.music
PKG_VER=$VER
MODULE_ARCH=arm64
EOF

# Create module.prop
cat > "$MODULE_DIR/module.prop" <<EOF
id=$MODULE_ID
name=$MODULE_NAME
version=v$VER
versionCode=$VERCODE
author=$MODULE_AUTHOR
description=Modded Spotify with premium unlocked
updateJson=https://raw.githubusercontent.com/${GITHUB_REPOSITORY}/main/update.json
EOF

# Copy the modded APK (used by customize.sh to install)
cp "$MODDED_APK" "$MODULE_DIR/com.spotify.music.apk"

# Create a dummy base.apk (will be generated from the stock APK during flash)
# Actually, we need a real base.apk for the mount mechanism. Create a placeholder.
cp "$MODDED_APK" "$MODULE_DIR/base.apk"

# Set permissions
chmod -R 755 "$MODULE_DIR/bin"
chmod 644 "$MODULE_DIR/module.prop"
chmod 644 "$MODULE_DIR/config"
chmod 755 "$MODULE_DIR/customize.sh"
chmod 755 "$MODULE_DIR/service.sh"
chmod 755 "$MODULE_DIR/uninstall.sh"

# Build zip
ZIP_NAME="${MODULE_ID}-v${VER}.zip"
cd "$OUT_DIR"
rm -f "$ZIP_NAME"
(
    cd "$MODULE_ID"
    zip -r9 "../$ZIP_NAME" .
)
cd ..

echo "Module built: $OUT_DIR/$ZIP_NAME"
echo "Version: $VER (code $VERCODE)"

# Set output for GitHub Actions
if [ -n "$GITHUB_ENV" ]; then
    echo "MODULE_ZIP=$OUT_DIR/$ZIP_NAME" >> "$GITHUB_ENV"
    echo "MODULE_VERSION=v$VER" >> "$GITHUB_ENV"
fi
