import json, os, re, sys, zipfile
from urllib.request import Request, urlopen
from html.parser import HTMLParser

APKCOMBO_URL = "https://apkcombo.com/spotify-music/com.spotify.music/download/apk"

class LinkFinder(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and "href" in attrs:
            self.links.append(attrs["href"])

def find_apkcombo_dl(version=None):
    url = APKCOMBO_URL
    if version:
        url = f"https://apkcombo.com/spotify-music/com.spotify.music/download/apk?version={version}"

    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    data = urlopen(req, timeout=30).read().decode()
    parser = LinkFinder()
    parser.feed(data)

    for link in parser.links:
        if "apkcombo.com" in link and link.endswith(".apk"):
            return link

    match = re.search(r'https://[^"]+\.apk[^"]*', data)
    if match:
        return match.group()

    ver_match = re.search(r'version=([\d.]+)', data)
    if ver_match:
        return f"https://apkcombo.com/spotify-music/com.spotify.music/download/apk?version={ver_match.group(1)}"

    return None

def download_apk(url, filename=None):
    if not filename:
        filename = url.split("/")[-1].split("?")[0]
        if not filename.endswith(".apk"):
            filename = "spotify.apk"

    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    print(f"Downloading {url}")
    data = urlopen(req, timeout=120).read()
    with open(filename, "wb") as f:
        f.write(data)
    print(f"Saved {filename} ({len(data)} bytes)")
    return filename

def extract_apk_version(apk_path):
    try:
        with zipfile.ZipFile(apk_path) as z:
            with z.open("AndroidManifest.xml") as f:
                content = f.read()
                m = re.search(rb'versionName[=:]["\']([\d.]+)["\']', content)
                if m:
                    return m.group(1).decode()
    except Exception:
        pass
    return None

if __name__ == "__main__":
    version = sys.argv[1] if len(sys.argv) > 1 else None
    url = find_apkcombo_dl(version)
    if not url:
        raise SystemExit("Could not find Spotify APK download URL")

    apk = download_apk(url)
    ver = extract_apk_version(apk) or version or "unknown"
    print(f"Spotify version: {ver}")

    os.rename(apk, f"spotify-{ver}.apk")
    with open(os.environ.get("GITHUB_ENV", "NUL"), "a") as env_file:
        if env_file.name != "NUL":
            env_file.write(f"SPOTIFY_VERSION={ver}\n")
