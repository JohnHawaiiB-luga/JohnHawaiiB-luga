"""Trim the 3D contribution graph: drop the star/fork counters and, unless --keep-pie, the language pie.

The counters add nothing on a profile page. The website's GitHub tile drops the pie; the README keeps it
as its languages chart.
Written against github-profile-3d-contrib v0.9.3; it fails loudly if that layout changes.
Usage: python3 trim_3d_contrib.py [--keep-pie] FILE.svg [FILE.svg ...]
"""
import re
import sys
import xml.etree.ElementTree as ET

SVG = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG)
NS = "{" + SVG + "}"
PIE_TRANSFORM = re.compile(r"translate\(\s*40\s*,\s*520\s*\)")


def texts(el):
    return [t.text.strip() for t in el.iter(NS + "text") if t.text and t.text.strip()]


def trim(path, keep_pie):
    tree = ET.parse(path)
    root = tree.getroot()
    groups = [c for c in root if c.tag == NS + "g"]

    pies = [g for g in groups if PIE_TRANSFORM.fullmatch(g.get("transform", ""))]
    if len(pies) != 1:
        sys.exit(f"{path}: expected one language pie group, found {len(pies)}")
    if not keep_pie:
        root.remove(pies[0])

    totals = [g for g in groups if "contributions" in texts(g)]
    if len(totals) != 1:
        sys.exit(f"{path}: expected one totals group, found {len(totals)}")
    counters = [c for c in totals[0]
                if c.tag == NS + "g"
                or (c.tag == NS + "text" and c.get("class") == "fill-fg" and re.fullmatch(r"[\d.,]+[KkMm]?", (c.text or "").strip()))]
    if len(counters) != 4:
        sys.exit(f"{path}: expected 4 star/fork elements, found {len(counters)}")
    for c in counters:
        totals[0].remove(c)

    tree.write(path, encoding="utf-8", xml_declaration=False)
    print(f"{path}: {'star/fork counters' if keep_pie else 'pie and star/fork counters'} removed")


if __name__ == "__main__":
    args = sys.argv[1:]
    keep_pie = "--keep-pie" in args
    files = [a for a in args if a != "--keep-pie"]
    if not files:
        sys.exit(__doc__)
    for p in files:
        trim(p, keep_pie)
