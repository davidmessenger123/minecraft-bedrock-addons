"""
Download reference photographs for the NZ animal models from Wikimedia Commons.

Scientific names give the best matches. For extinct species Commons usually
holds the museum paintings and scientific reconstructions, which is exactly
what is wanted for a model.

Usage: python3 tools/fetch_refs.py [out_dir]
"""

from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request
import time

UA = "NZAnimalsAddOn/1.0 (local add-on build; contact: local)"

# species id -> (search terms, extra fallback terms)
TERMS = {
    "kiwi": ["Apteryx mantelli", "great spotted kiwi"],
    "kakapo": ["Strigops habroptilus", "kakapo"],
    "kea": ["Nestor notabilis", "kea parrot"],
    "kaka": ["Nestor meridionalis", "New Zealand kaka"],
    "tui": ['Meliphagus novaeseelandiae', 'tui Prosthemadera bird perched', 'tui New Zealand honeyeater'],
    "hihi": ['Notiomystis cincta perched', 'hihi stitchbird', 'Notiomystis cincta'],
    "kereru": ["Columba novaeseelandiae", "New Zealand pigeon"],
    "pukeko": ["Porphyrio melanotus", "pukeko"],
    "morepork": ['Ninox novaeseelandiae perched', 'ruru owl', 'Ninox novaeseelandiae'],
    "kotare": ["Todiramphus sanctus", "kingfisher New Zealand"],
    "tieke": ["Philesturnus rufusater", "North Island saddleback"],
    "whio": ["Hymenolaimus malacorhynchos", "blue duck whio"],
    "huia": ['Heteralochaus acutirostris illustration', 'huia Heteralochaus', 'huia bird drawing'],
    "haasts_eagle": ['Hieraaetus moorei reconstruction', 'Haast eagle painting', "Haast's eagle"],
    "moa": ["Dinornis robustus", "giant moa"],
    "rockhopper_penguin": ['Eudyptes fileri', 'rockhopper penguin Eudyptes', 'Eudyptes pachyrhynchus'],
    "yellow_eyed_penguin": ["Megadyptes antipodes", "yellow-eyed penguin"],
    "little_penguin": ["Eudyptula minor", "little penguin blue"],
    "tuatara": ["Sphenodon punctatus", "tuatara"],
    "powelliphanta": ["Powelliphanta", "giant land snail New Zealand"],
    "weta": ["Deinacrida heteracantha", "giant weta"],
    "huhu": ['Prionoplus reticularis beetle photo', 'Prionoplus reticularis', ' huhu beetle New Zealand'],
    "nz_sea_lion": ["Phocarctos hookeri", "New Zealand sea lion"],
    "nz_fur_seal": ["Arctocephalus forsteri", "New Zealand fur seal"],
    "hectors_dolphin": ["Cephorhynchus hectori", "Hector's dolphin"],
    "dusky_dolphin": ["Cephalorhynchus commersonii", "dusky dolphin"],
    "orca": ['Orcinus orca portrait', 'killer whale Orcinus orca swimming', 'Orcinus orca'],
    "sperm_whale": ["Physeter macrocephalus", "sperm whale"],
    "blue_shark": ["Prionace glauca", "blue shark"],
}

BAD = ("map", "logo", "icon", "distribution", "range", "skull", "skeleton of",
       "diagram", "chart", "graph", "coin", "stamp", "banknote", "sign", "flag",
       "plaque", "statue", "monument", "coat of arms", "svg")


def api_search(term: str, limit: int = 8) -> list[tuple[str, str]]:
    q = {
        "action": "query", "format": "json", "generator": "search",
        "gsrsearch": f"filetype:bitmap {term}", "gsrnamespace": "6",
        "gsrlimit": str(limit), "prop": "imageinfo", "iiprop": "url|size",
        "iiurlwidth": "800",
    }
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(q)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    data = None
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                data = json.load(r)
            break
        except urllib.error.HTTPError as exc:
            if exc.code not in (429, 503):
                raise
            wait = 6 * (attempt + 1)
            print(f"    rate limited, waiting {wait}s")
            time.sleep(wait)
    if data is None:
        return []
    out = []
    for p in (data.get("query", {}).get("pages", {}) or {}).values():
        title = p.get("title", "")
        if any(b in title.lower() for b in BAD):
            continue
        ii = (p.get("imageinfo") or [{}])[0]
        u = ii.get("thumburl")
        if u and (ii.get("width") or 0) >= 500:
            out.append((title, u))
    return out


def fetch(url: str, path: str) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
        if len(data) < 8000:
            return False
        with open(path, "wb") as fh:
            fh.write(data)
        return True
    except Exception as exc:  # noqa: BLE001
        print("    download failed:", exc)
        return False


def main() -> int:
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "refs")
    out = os.path.normpath(out)
    os.makedirs(out, exist_ok=True)

    index = {}
    for sid, terms in TERMS.items():
        dest = os.path.join(out, f"{sid}.jpg")
        if os.path.exists(dest) and os.path.getsize(dest) > 8000:
            print(f"  {sid}: cached")
            continue
        got = False
        for term in terms:
            time.sleep(2.5)
            for title, url in api_search(term):
                if fetch(url, dest):
                    print(f"  {sid}: {title}")
                    index[sid] = title
                    got = True
                    break
            if got:
                break
        if not got:
            print(f"  {sid}: NOT FOUND")
    with open(os.path.join(out, "index.json"), "w", encoding="utf-8") as fh:
        json.dump(index, fh, indent=2)
    print(f"\n{len(os.listdir(out)) - 1} reference images in {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
