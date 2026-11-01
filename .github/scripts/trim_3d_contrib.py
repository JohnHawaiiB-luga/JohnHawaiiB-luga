"""Trim the 3D contribution graph: drop the language pie and the star/fork counters.

The README shows languages in their own card, and the counters add nothing on a profile page.
--transparent drops the background so the graph sits on the page's own colour; --light also darkens
the text for light themes.
Written against github-profile-3d-contrib v0.9.3; it fails loudly if that layout changes.
Usage: python3 trim_3d_contrib.py [--transparent] [--light] FILE.svg [FILE.svg ...]
"""
import re
import sys
import xml.etree.ElementTree as ET

SVG = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG)
NS = "{" + SVG + "}"
PIE_TRANSFORM = re.compile(r"translate\(\s*40\s*,\s*520\s*\)")
LIGHT_TEXT = {"fg": "#24292f", "weak": "#57606a"}


def texts(el):
    return [t.text.strip() for t in el.iter(NS + "text") if t.text and t.text.strip()]


def trim(path, transparent, light):
    tree = ET.parse(path)
    root = tree.getroot()
    groups = [c for c in root if c.tag == NS + "g"]

    pies = [g for g in groups if PIE_TRANSFORM.fullmatch(g.get("transform", ""))]
    if len(pies) != 1:
        sys.exit(f"{path}: expected one language pie group, found {len(pies)}")
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

    if transparent:
        backgrounds = [c for c in root if c.tag == NS + "rect" and c.get("class") == "fill-bg"
                       and c.get("width") == root.get("width") and c.get("height") == root.get("height")]
        if len(backgrounds) != 1:
            sys.exit(f"{path}: expected one full-size background, found {len(backgrounds)}")
        root.remove(backgrounds[0])

    if light:
        style = root.find(NS + "style")
        css = style.text
        for name, colour in LIGHT_TEXT.items():
            css, n = re.subn(rf"(\.(?:fill|stroke)-{name} \{{ (?:fill|stroke): )#[0-9a-fA-F]{{3,6}}", rf"\g<1>{colour}", css)
            if n != 2:
                sys.exit(f"{path}: expected the .{name} colour rules, found {n}")
        style.text = css

    tree.write(path, encoding="utf-8", xml_declaration=False)
    extras = [w for w, on in (("background", transparent), ("light text", light)) if on]
    print(f"{path}: pie and star/fork counters removed" + (f"; {', '.join(extras)}" if extras else ""))


if __name__ == "__main__":
    args = sys.argv[1:]
    flags = {a for a in args if a.startswith("--")}
    files = [a for a in args if not a.startswith("--")]
    if not files or flags - {"--transparent", "--light"}:
        sys.exit(__doc__)
    for p in files:
        trim(p, "--transparent" in flags, "--light" in flags)
