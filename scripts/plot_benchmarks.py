#!/usr/bin/env python3
"""Figures of the CP2K Noctua 2 benchmarks from the CP2K timing reports in results/runs/<case>/<n>n/output.out.

fig_scaling.pdf/png: wall time against the number of cores (strong scaling) for all cases.
fig_steps.pdf/png:   wall time split into the main steps of each calculation, per node count.
Width 16 cm, Liberation Sans 10 pt (same metrics as Helvetica/Arial used in the report text).
"""
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, MultipleLocator, NullFormatter, NullLocator

ROOT = sys.argv[1]  # folder with runs/
OUT = sys.argv[2]   # folder for the figures
CM = 1 / 2.54
plt.rcParams.update({"font.family": "Liberation Sans", "font.size": 10, "mathtext.fontset": "custom",
                     "mathtext.rm": "Liberation Sans", "mathtext.it": "Liberation Sans:italic",
                     "axes.linewidth": 0.8, "pdf.fonttype": 42})
LEGEND = dict(frameon=True, fancybox=False, edgecolor="black", facecolor="white", framealpha=1)

CASES = [  # folder, label, colour, marker
    ("water_64_PBE_TZV2P", "64 H$_2$O, PBE, TZV2P-MOLOPT-GTH", "#1f77b4", "o"),
    ("Si_GW_aug-TZ2", "Si, $G_0W_0$ + SOC, aug-TZVP-MOLOPT-GTH tier 2, 12$\\times$12$\\times$12 $k$", "#ff7f0e", "s"),
    ("WSe2_monolayer_GW_aug-TZ2", "WSe$_2$ monolayer, $G_0W_0$ + SOC, aug-TZVP-MOLOPT-GTH tier 2, 16$\\times$16$\\times$1 $k$", "#9467bd", "D"),
    ("nanographene_L5_GW_aug-SZ2", "nanographene 98 atoms, $G_0W_0$, aug-SZV-MOLOPT-GTH tier 2, AUTO_RI", "#d62728", "v"),
    ("nanographene_L16_GW_aug-SZ2_autoRI", "nanographene 296 atoms, $G_0W_0$, aug-SZV-MOLOPT-GTH tier 2, AUTO_RI", "#2ca02c", "^"),
    ("nanographene_L16_GW_aug-SZ2", "nanographene 296 atoms, $G_0W_0$, aug-SZV-MOLOPT-GTH tier 2, RI basis from file", "#8c564b", "<"),
]
NODES = ["0.5", "1", "2"]
STEP_TITLES = {  # short panel titles of fig_steps (basis sets and k-meshes are in the caption and the table)
    "water_64_PBE_TZV2P": "64 H$_2$O, PBE", "Si_GW_aug-TZ2": "Si, $G_0W_0$ + SOC",
    "WSe2_monolayer_GW_aug-TZ2": "WSe$_2$ monolayer, $G_0W_0$ + SOC",
    "nanographene_L5_GW_aug-SZ2": "nanographene 98 atoms, $G_0W_0$, AUTO_RI",
    "nanographene_L16_GW_aug-SZ2_autoRI": "nanographene 296 atoms, $G_0W_0$, AUTO_RI",
    "nanographene_L16_GW_aug-SZ2": "nanographene 296 atoms, $G_0W_0$, RI basis from file"}
CORES_PER_NODE = 128

# main steps: label -> timer names whose inclusive times are added (step "other" = total - sum)
STEPS = {
    "molecular GW": [("SCF", ["scf_env_do_scf"]), ("RI-RS grid optimization", ["optimize_ri_rs_grid"]),
                     ("$\\chi$", ["get_mat_chi_Gamma_tau"]), ("$W$", ["compute_W"]),
                     ("$\\mathit{\\Sigma}$ and QP energies", ["compute_Sigma_c_and_QP_energie"])],
    "periodic GW": [("SCF", ["scf_env_do_scf"]), ("RI-RS grid optimization", ["optimize_ri_rs_grid"]),
                    ("RI-RS matrix $Z_{lP}$", ["prepare_ri_rs", "-optimize_ri_rs_grid"]),
                    ("$\\chi$", ["compute_chi"]), ("$W$", ["compute_W0"]),
                    ("$\\mathit{\\Sigma}$ and QP energies", ["compute_Sigma_x", "compute_Sigma_c_and_QP"]),
                    ("SOC and band output", ["soc", "eval_bandstructure_properties"])],
    "Gamma DFT": [("KS matrix build", ["qs_ks_update_qs_env"]), ("OT minimization", ["scf_env_do_scf", "-qs_ks_update_qs_env"])],
}
KIND = {"water_64_PBE_TZV2P": "Gamma DFT", "Si_GW_aug-TZ2": "periodic GW", "WSe2_monolayer_GW_aug-TZ2": "periodic GW",
        "nanographene_L5_GW_aug-SZ2": "molecular GW", "nanographene_L16_GW_aug-SZ2_autoRI": "molecular GW",
        "nanographene_L16_GW_aug-SZ2": "molecular GW"}
STEP_COLOURS = ["#4e79a7", "#f28e2b", "#edc948", "#59a14f", "#e15759", "#b07aa1", "#76b7b2", "#bab0ac"]


def timing_report(path):
    """{routine: maximum inclusive time} of the timing report at the end of a completed CP2K output."""
    if not os.path.exists(path):
        return None
    text = open(path, errors="replace").read()
    if "PROGRAM ENDED AT" not in text:
        return None
    table = {}
    for line in text[text.rfind("SUBROUTINE                       CALLS"):].splitlines()[2:]:
        cols = line.split()
        if len(cols) == 7:
            try:
                table.setdefault(cols[0], float(cols[6]))
            except ValueError:
                pass
    return table


def memory_failure(run_dir):
    """True if the run was killed for memory or stopped by a CP2K memory check."""
    text = ""
    if not os.path.isdir(run_dir):
        return False
    for name in ("output.out", "cp2k.stderr") + tuple(f for f in os.listdir(run_dir) if f.startswith("slurm-")):
        path = os.path.join(run_dir, name)
        if os.path.exists(path):
            text += open(path, errors="replace").read()[-50000:]
    return "Out Of Memory" in text or "oom_kill" in text or "Insufficient memory" in text


def tick_step(span):
    """Tick spacing 1, 2 or 5 times a power of ten giving 3 to 7 ticks on [0, span]."""
    for exponent in range(0, 6):
        for mantissa in (1, 2, 5):
            step = mantissa * 10 ** exponent
            if span / step <= 7:
                return step
    return 10 ** 6


ALL_CASES = [c[0] for c in CASES]
reports = {c: {n: timing_report(os.path.join(ROOT, "runs", c, n + "n", "output.out")) for n in NODES}
           for c in ALL_CASES}

# ---------------------------------------------------------------- strong scaling
fig, ax = plt.subplots(figsize=(16 * CM, 14 * CM))
for case, label, colour, marker in CASES:
    pts = [(float(n) * CORES_PER_NODE, r["CP2K"]) for n, r in reports[case].items() if r]
    if not pts:
        continue
    x, y = zip(*pts)
    ax.plot(x, y, marker=marker, color=colour, label=label, lw=1.5, ms=5)
    ax.plot([x[0], x[-1]], [y[0], y[0] * x[0] / x[-1]], color=colour, lw=0.8, ls=":")
ax.set_xscale("log")
ax.set_yscale("log")
ax.xaxis.set_major_locator(FixedLocator([64, 128, 256]))
ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: "%d" % v))
ax.xaxis.set_minor_locator(NullLocator())
yt = [20, 50, 100, 200, 500, 1000, 2000, 5000, 10000]
ax.yaxis.set_major_locator(FixedLocator(yt))
ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: "%d" % v))
ax.yaxis.set_minor_formatter(NullFormatter())
ax.set_xlim(55, 300)
ax.set_ylim(40, 6000)
ax.set_xlabel("Number of cores (128 cores per Noctua 2 node)")
ax.set_ylabel("Wall time (s)")
ax.grid(True, which="major", color="0.85", lw=0.6)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.17), ncol=1, fontsize=8, **LEGEND)
fig.tight_layout()
for ext in ("pdf", "png"):
    fig.savefig(os.path.join(OUT, "fig_scaling." + ext), dpi=200)
plt.close(fig)

# ---------------------------------------------------------------- step breakdown
fig, axes = plt.subplots(len(CASES), 1, figsize=(16 * CM, 23 * CM))
for ax, (case, label, _, _), letter in zip(axes, CASES, "abcdefg"):
    steps = STEPS[KIND[case]]
    nodes = NODES
    xpos = range(len(nodes))
    tmax = max([r["CP2K"] for r in reports[case].values() if r] or [1])
    for i, n in zip(xpos, nodes):
        r = reports[case][n]
        if not r:
            if memory_failure(os.path.join(ROOT, "runs", case, n + "n")):
                ax.text(i, 0.03 * tmax, "does not fit\ninto memory", ha="center", va="bottom", fontsize=8)
            continue
        bottom = 0.0
        for j, (slabel, timers) in enumerate(steps):
            t = sum(-r.get(k[1:], 0.0) if k.startswith("-") else r.get(k, 0.0) for k in timers)
            ax.bar(i, t, bottom=bottom, color=STEP_COLOURS[j], width=0.6, label=slabel)
            bottom += t
        ax.bar(i, r["CP2K"] - bottom, bottom=bottom, color=STEP_COLOURS[-1], width=0.6, label="other")
    handles, labels = ax.get_legend_handles_labels()
    uniq = dict(zip(labels, handles))
    ax.legend(uniq.values(), uniq.keys(), loc="upper left", bbox_to_anchor=(1.02, 1.12), fontsize=8, labelspacing=0.15,
              handlelength=1.2, borderpad=0.3, **LEGEND)
    ax.set_xticks(list(xpos))
    ax.set_xticklabels(["%d" % (float(n) * CORES_PER_NODE) for n in nodes])
    ax.set_xlim(-0.6, len(nodes) - 0.4)
    ax.set_ylim(0, 1.3 * tmax)
    ax.yaxis.set_major_locator(MultipleLocator(tick_step(1.3 * tmax)))
    ax.yaxis.set_minor_locator(MultipleLocator(tick_step(1.3 * tmax) / 5))
    ax.set_ylabel("Wall time (s)")
    ax.text(0.01, 0.95, "(%s)" % letter, transform=ax.transAxes, va="top", ha="left")
    ax.set_title(STEP_TITLES[case], fontsize=10, loc="left")
axes[-1].set_xlabel("Number of cores (128 cores per Noctua 2 node)")
fig.tight_layout()
for ext in ("pdf", "png"):
    fig.savefig(os.path.join(OUT, "fig_steps." + ext), dpi=200)
plt.close(fig)
print("figures written to", OUT)
