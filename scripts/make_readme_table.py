#!/usr/bin/env python3
"""Markdown timing table (wall time in s per node count) from timings.json written by collect_timings.py."""
import json
import sys

timings = json.load(open(sys.argv[1]))
CASES = [
    ("water_64_PBE_TZV2P", "64 H₂O (192 atoms), PBE, TZV2P-MOLOPT-GTH, Γ point"),
    ("Si_GW_aug-TZ2", "Si (2 atoms), G₀W₀@PBE + SOC, aug-TZVP-MOLOPT-GTH tier 2, 12×12×12 k"),
    ("WSe2_monolayer_GW_aug-TZ2", "WSe₂ monolayer (3 atoms), G₀W₀@PBE + SOC, aug-TZVP-MOLOPT-GTH tier 2, 16×16×1 k"),
    ("nanographene_L5_GW_aug-SZ2", "nanographene (98 atoms), G₀W₀@PBE, aug-SZV-MOLOPT-GTH tier 2, AUTO_RI"),
    ("nanographene_L16_GW_aug-SZ2_autoRI", "nanographene (296 atoms), G₀W₀@PBE, aug-SZV-MOLOPT-GTH tier 2, AUTO_RI"),
    ("nanographene_L16_GW_aug-SZ2", "nanographene (296 atoms), G₀W₀@PBE, aug-SZV-MOLOPT-GTH tier 2, RI basis from file"),
]
NODES = ["0.5", "1", "2"]
print("| Test | " + " | ".join(f"{n} node{'s' if n not in ('0.5', '1') else ''} ({int(float(n) * 128)} cores)"
                             for n in NODES) + " |")
print("|:---|" + "---:|" * len(NODES))
for case, label in CASES:
    cells = []
    for n in NODES:
        r = timings.get(case, {}).get(n)
        if r is None:
            cells.append("")
        elif r["status"] == "completed":
            cells.append(f"[{r['wall_s']:.0f}](outputs/{case}/{n}n/output.out)")
        elif r["status"] in ("memory check abort", "out of memory (killed)", "cancelled"):
            cells.append(f"[–](outputs/{case}/{n}n/)")
        else:
            cells.append(r["status"])
    print(f"| [{label}](inputs/{case}/) | " + " | ".join(cells) + " |")
