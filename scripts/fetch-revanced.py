import sys, re, urllib.request


def fetch_latest_download(repo, pattern, output):
    """Fetch the latest release page, find expanded_assets, and download."""
    # Get the latest release tag
    latest_url = f"https://github.com/{repo}/releases/latest"
    try:
        r = urllib.request.urlopen(latest_url, timeout=15)
        tag_url = r.url  # e.g. https://github.com/.../releases/tag/v5.14.1
        tag = tag_url.rstrip("/").rsplit("/", 1)[-1]
    except Exception as e:
        print(f"ERROR: could not fetch latest release from {latest_url}: {e}", file=sys.stderr)
        sys.exit(1)

    # Fetch the expanded assets page
    assets_url = f"https://github.com/{repo}/releases/expanded_assets/{tag}"
    try:
        r = urllib.request.urlopen(assets_url, timeout=15)
        html = r.read().decode()
    except Exception as e:
        print(f"ERROR: could not fetch assets from {assets_url}: {e}", file=sys.stderr)
        sys.exit(1)

    # Find download link matching the pattern
    for m in re.finditer(rf'href="(/{repo}/releases/download/{re.escape(tag)}/{pattern})"', html):
        dl_url = "https://github.com" + m.group(1)
        print(f"Downloading {dl_url}")
        urllib.request.urlretrieve(dl_url, output)
        return

    print(f"ERROR: could not find download URL matching '{pattern}' in {assets_url}", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: fetch-revanced.py [cli|patches]", file=sys.stderr)
        sys.exit(1)

    if sys.argv[1] == "cli":
        fetch_latest_download(
            "inotia00/revanced-cli",
            r"revanced-cli-[\d.]+-all\.jar",
            "revanced-cli.jar",
        )
    elif sys.argv[1] == "patches":
        fetch_latest_download(
            "inotia00/revanced-patches",
            r"patches-[\d.]+\.rvp",
            "patches.rvp",
        )
    else:
        print(f"Unknown target: {sys.argv[1]}", file=sys.stderr)
        sys.exit(1)
