#!/usr/bin/env python3
"""Figures of the CP2K Noctua 2 benchmarks from the CP2K timing reports in results/runs/<case>/<n>n/output.out.

fig_scaling.pdf/png: wall time against the number of cores (strong scaling) for all cases.
fig_steps.pdf/png:   wall time split into the main steps of each calculation, per node count.
fig_kp_transform.pdf/png: RSKP_TRANSFORM GEMM (default) against FFT for TiO2 anatase PBE and G0W0.
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
    ("water_64_PBE_TZV2P", "64 H$_2$O, PBE, TZV2P-MOLOPT", "#1f77b4", "o"),
    ("anatase_DFT_aug-TZ2_FFT", "TiO$_2$ anatase, PBE, aug-TZVP tier 2", "#ff7f0e", "s"),
    ("nanographene_L16_GW_aug-SZ2", "nanographene 296 atoms, $G_0W_0$, aug-SZV tier 2", "#2ca02c", "^"),
    ("nanographene_L56_GW_aug-SZ2", "nanographene 1016 atoms, $G_0W_0$, aug-SZV tier 2", "#d62728", "v"),
    ("anatase_GW_aug-SZ2", "TiO$_2$ anatase, $G_0W_0$, aug-SZV tier 2", "#9467bd", "D"),
]
NODES = ["0.5", "1", "2", "4", "8"]
CORES_PER_NODE = 128

# main steps: label -> timer names whose inclusive times are added (step "other" = total - sum)
STEPS = {
    "molecular GW": [("SCF", ["scf_env_do_scf"]), ("RI-RS grid optimization", ["optimize_ri_rs_grid"]),
                     ("$\\chi$", ["get_mat_chi_Gamma_tau"]), ("$W$", ["compute_W"]),
                     ("$\\mathit{\\Sigma}$ and QP energies", ["compute_Sigma_c_and_QP_energie"])],
    "periodic GW": [("SCF", ["scf_env_do_scf"]), ("RI-RS setup and $Z$", ["prepare_ri_rs", "compute_Z_lP_q"]),
                    ("$\\chi$", ["compute_chi"]), ("$W$", ["compute_W0"]),
                    ("$\\mathit{\\Sigma}$ and QP energies", ["compute_Sigma_x", "compute_Sigma_c_and_QP"]),
                    ("SOC and band output", ["eval_bandstructure_properties"])],
    "k-point DFT": [("diagonalization", ["cp_cfm_geeig_local"]),
                    ("density matrix $k\\to R$", ["kpoint_density_transform"]),
                    ("KS and overlap $R\\to k$", ["kpoint_operator_evaluate_batch"]),
                    ("KS matrix build", ["qs_ks_update_qs_env"])],
    "Gamma DFT": [("KS matrix build", ["qs_ks_update_qs_env"]), ("OT minimization", ["scf_env_do_scf", "-qs_ks_update_qs_env"])],
}
KIND = {"water_64_PBE_TZV2P": "Gamma DFT", "anatase_DFT_aug-TZ2": "k-point DFT", "anatase_DFT_aug-TZ2_FFT": "k-point DFT",
        "anatase_GW_aug-SZ2_FFT": "periodic GW",
        "nanographene_L16_GW_aug-SZ2": "molecular GW", "nanographene_L56_GW_aug-SZ2": "molecular GW",
        "anatase_GW_aug-SZ2": "periodic GW"}
STEP_COLOURS = ["#4e79a7", "#f28e2b", "#59a14f", "#e15759", "#b07aa1", "#76b7b2", "#bab0ac"]


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


ALL_CASES = [c[0] for c in CASES] + ["anatase_DFT_aug-TZ2", "anatase_GW_aug-SZ2_FFT"]
reports = {c: {n: timing_report(os.path.join(ROOT, "runs", c, n + "n", "output.out")) for n in NODES}
           for c in ALL_CASES}

# ---------------------------------------------------------------- strong scaling
fig, ax = plt.subplots(figsize=(16 * CM, 12 * CM))
for case, label, colour, marker in CASES:
    pts = [(float(n) * CORES_PER_NODE, r["CP2K"]) for n, r in reports[case].items() if r]
    if not pts:
        continue
    x, y = zip(*pts)
    ax.plot(x, y, marker=marker, color=colour, label=label, lw=1.5, ms=5)
    ax.plot([x[0], x[-1]], [y[0], y[0] * x[0] / x[-1]], color=colour, lw=0.8, ls=":")
ax.set_xscale("log")
ax.set_yscale("log")
ax.xaxis.set_major_locator(FixedLocator([64, 128, 256, 512, 1024]))
ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: "%d" % v))
ax.xaxis.set_minor_locator(NullLocator())
yt = [20, 50, 100, 200, 500, 1000, 2000, 5000, 10000]
ax.yaxis.set_major_locator(FixedLocator(yt))
ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: "%d" % v))
ax.yaxis.set_minor_formatter(NullFormatter())
ax.set_xlim(55, 1200)
ax.set_ylim(20, 10000)
ax.set_xlabel("Number of cores (128 cores per Noctua 2 node)")
ax.set_ylabel("Wall time (s)")
ax.grid(True, which="major", color="0.85", lw=0.6)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.17), ncol=2, fontsize=8, **LEGEND)
fig.tight_layout()
for ext in ("pdf", "png"):
    fig.savefig(os.path.join(OUT, "fig_scaling." + ext), dpi=200)
plt.close(fig)

# ---------------------------------------------------------------- step breakdown
fig, axes = plt.subplots(len(CASES), 1, figsize=(16 * CM, 23 * CM))
for ax, (case, label, _, _), letter in zip(axes, CASES, "abcdefg"):
    steps = STEPS[KIND[case]]
    nodes = [n for n in NODES if n != "8" or reports[case]["8"]]
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
    ax.legend(uniq.values(), uniq.keys(), loc="upper left", bbox_to_anchor=(1.02, 1.0), fontsize=8, **LEGEND)
    ax.set_xticks(list(xpos))
    ax.set_xticklabels(["%d" % (float(n) * CORES_PER_NODE) for n in nodes])
    ax.set_xlim(-0.6, len(nodes) - 0.4)
    ax.set_ylim(0, 1.3 * tmax)
    ax.yaxis.set_major_locator(MultipleLocator(tick_step(1.3 * tmax)))
    ax.yaxis.set_minor_locator(MultipleLocator(tick_step(1.3 * tmax) / 5))
    ax.set_ylabel("Wall time (s)")
    ax.text(0.01, 0.95, "(%s)" % letter, transform=ax.transAxes, va="top", ha="left")
    ax.set_title(label, fontsize=10, loc="left")
axes[-1].set_xlabel("Number of cores (128 cores per Noctua 2 node)")
fig.tight_layout()
for ext in ("pdf", "png"):
    fig.savefig(os.path.join(OUT, "fig_steps." + ext), dpi=200)
plt.close(fig)
# ---------------------------------------------------------------- GEMM against FFT
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16 * CM, 11 * CM), gridspec_kw={"width_ratios": [1.25, 1]})
for case, backend, ls in (("anatase_DFT_aug-TZ2", "GEMM (default)", "-"), ("anatase_DFT_aug-TZ2_FFT", "FFT", "--")):
    pts = [(float(n) * CORES_PER_NODE, r["CP2K"], r["kpoint_density_transform"])
           for n, r in reports[case].items() if r]
    x, total, dens = zip(*pts)
    ax1.plot(x, total, ls=ls, marker="s", color="#ff7f0e", label="total, " + backend)
    ax1.plot(x, dens, ls=ls, marker="o", color="#4e79a7", label="density matrix $k\\to R$, " + backend)
ax1.set_xscale("log")
ax1.set_yscale("log")
ax1.xaxis.set_major_locator(FixedLocator([64, 128, 256, 512]))
ax1.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: "%d" % v))
ax1.xaxis.set_minor_locator(NullLocator())
ax1.yaxis.set_major_locator(FixedLocator([10, 20, 50, 100, 200, 500, 1000, 2000]))
ax1.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: "%d" % v))
ax1.yaxis.set_minor_formatter(NullFormatter())
ax1.set_ylim(10, 5000)
ax1.set_xlim(55, 600)
ax1.set_xlabel("Number of cores")
ax1.set_ylabel("Wall time (s)")
ax1.grid(True, which="major", color="0.85", lw=0.6)
ax1.legend(loc="upper center", bbox_to_anchor=(0.5, -0.2), fontsize=8, **LEGEND)
ax1.text(0.03, 0.97, "(a)", transform=ax1.transAxes, va="top", ha="left")
ax1.set_title("PBE, aug-TZVP tier 2", fontsize=10, loc="left")
steps = STEPS["periodic GW"]
for i, case in enumerate(("anatase_GW_aug-SZ2", "anatase_GW_aug-SZ2_FFT")):
    r = reports[case]["8"]
    bottom = 0.0
    for j, (slabel, timers) in enumerate(steps):
        t = sum(r.get(k, 0.0) for k in timers)
        ax2.bar(i, t, bottom=bottom, color=STEP_COLOURS[j], width=0.6, label=slabel if i == 0 else None)
        bottom += t
    ax2.bar(i, r["CP2K"] - bottom, bottom=bottom, color=STEP_COLOURS[-1], width=0.6, label="other" if i == 0 else None)
ax2.set_xticks([0, 1])
ax2.set_xticklabels(["GEMM\n(default)", "FFT"])
ax2.set_xlim(-0.6, 1.6)
ax2.set_ylim(0, 1400)
ax2.yaxis.set_major_locator(MultipleLocator(200))
ax2.yaxis.set_minor_locator(MultipleLocator(50))
ax2.set_ylabel("Wall time (s)")
ax2.legend(loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=2, fontsize=8, **LEGEND)
ax2.text(0.03, 0.97, "(b)", transform=ax2.transAxes, va="top", ha="left")
ax2.set_title("$G_0W_0$, aug-SZV tier 2, 1024 cores", fontsize=10, loc="left")
fig.tight_layout()
for ext in ("pdf", "png"):
    fig.savefig(os.path.join(OUT, "fig_kp_transform." + ext), dpi=200)
plt.close(fig)
print("figures written to", OUT)
