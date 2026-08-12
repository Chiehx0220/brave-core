#!/usr/bin/env python3
"""Patches decompiled Brave APK resources to restore stock Chrome MD3 colors.

Covers only the two fixes that don't require Chromium's original literal
color constants:
  - NTP toolbar/omnibox background colors: static hex -> MD3 attr tokens.
  - Home surface background color: colorSurface -> colorSurfaceContainerHigh.

See CLAUDE.md / commit history for the full (source-level) set of fixes;
this script intentionally does not attempt the baseline/gm3_baseline
palette remap, since that needs Chromium's actual stock values, which
this repackage path has no trusted way to obtain.
"""

import glob
import os
import sys
import xml.etree.ElementTree as ET

ANDROID_NS = "http://schemas.android.com/apk/res/android"
ET.register_namespace("android", ANDROID_NS)

DECODE_DIR = sys.argv[1] if len(sys.argv) > 1 else "decoded"

COLOR_REPLACEMENTS = {
    "location_bar_background_color_for_ntp": "?attr/colorSurfaceContainerLow",
    "toolbar_background_color_for_ntp": "?attr/colorSurface",
}


def patch_colors():
    found = set()
    for path in glob.glob(os.path.join(DECODE_DIR, "res", "values*", "colors.xml")):
        tree = ET.parse(path)
        root = tree.getroot()
        changed = False
        for color in root.findall("color"):
            name = color.get("name")
            if name in COLOR_REPLACEMENTS:
                color.text = COLOR_REPLACEMENTS[name]
                changed = True
                found.add(name)
        if changed:
            tree.write(path, encoding="utf-8", xml_declaration=True)
            print(f"patched {path}")
    missing = set(COLOR_REPLACEMENTS) - found
    if missing:
        print(f"ERROR: color resources not found in any values*/colors.xml: {missing}",
              file=sys.stderr)
        sys.exit(1)


def patch_home_surface():
    path = os.path.join(DECODE_DIR, "res", "color", "home_surface_background_color.xml")
    if not os.path.exists(path):
        print(f"ERROR: {path} not found", file=sys.stderr)
        sys.exit(1)
    tree = ET.parse(path)
    root = tree.getroot()
    changed = False
    color_attr = f"{{{ANDROID_NS}}}color"
    for item in root.findall("item"):
        if item.get(color_attr) == "?attr/colorSurface":
            item.set(color_attr, "?attr/colorSurfaceContainerHigh")
            changed = True
    if not changed:
        print(f"ERROR: no '?attr/colorSurface' item found in {path}", file=sys.stderr)
        sys.exit(1)
    tree.write(path, encoding="utf-8", xml_declaration=True)
    print(f"patched {path}")


if __name__ == "__main__":
    patch_colors()
    patch_home_surface()
    print("All MD3 resource patches applied.")
