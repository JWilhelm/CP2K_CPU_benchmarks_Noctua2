#!/usr/bin/env python3
"""Collect wall times, step times and peak memory of all benchmark runs into timings.json.

Reads runs/<case>/<n>n/{output.out,slurm-*.out,cp2k.stderr} below the directory given as argument 1
and writes timings.json next to this script's parent folder (argument 2).
"""
import glob
import json
import os
import re
import sys

ROOT, OUT = sys.argv[1], sys.argv[2]

# CP2K timer names whose inclusive time (last column of the timing report) is shown per step
STEP_TIMERS = {
    "SCF": "qs_energies",
    "GW total": "gw_calc_small_cell_full_kp",
    "GW (molecule)": "gw_calc_large_cell_Gamma",
}


def timing_report(text):
    """Return {routine: (calls, max inclusive time)} from the last CP2K timing report."""
    start = text.rfind("SUBROUTINE                       CALLS")
    table = {}
    if start < 0:
        return table
    for line in text[start:].splitlines()[2:]:
        cols = line.split()
        if len(cols) == 7 and re.match(r"^[0-9.]+$", cols[6]):
            table.setdefault(cols[0], (cols[1], float(cols[6])))
        elif line.startswith(" ---") and table:
            break
    return table


def classify_failure(run_dir):
    text = ""
    for f in glob.glob(os.path.join(run_dir, "cp2k.stderr")) + glob.glob(os.path.join(run_dir, "slurm-*.out")):
        text += open(f, errors="replace").read()
    out = os.path.join(run_dir, "output.out")
    if os.path.exists(out):
        text += open(out, errors="replace").read()[-20000:]
    if re.search(r"Insufficient memory|not enough memory", text):
        return "memory check abort"
    if re.search(r"oom_kill|Out Of Memory", text):
        return "out of memory (killed)"
    if re.search(r"DUE TO TIME LIMIT", text):
        return "time limit"
    if re.search(r"\[ABORT\]|SIGSEGV|Segmentation", text):
        return "abort"
    if re.search(r"CANCELLED AT", text):
        return "cancelled"
    if not re.search(r"^end \d+", text, re.M):
        return "running"
    return "unknown"


results = {}
for run_dir in sorted(glob.glob(os.path.join(ROOT, "runs", "*", "*n"))):
    case, nodes = run_dir.split(os.sep)[-2], run_dir.split(os.sep)[-1][:-1]
    entry = {"nodes": float(nodes)}
    out = os.path.join(run_dir, "output.out")
    text = open(out, errors="replace").read() if os.path.exists(out) else ""
    report = timing_report(text)
    if "PROGRAM ENDED AT" in text and "CP2K" in report:
        entry["status"] = "completed"
        entry["wall_s"] = report["CP2K"][1]
        entry["steps_s"] = {k: report[v][1] for k, v in STEP_TIMERS.items() if v in report}
        mem = re.findall(r"Estimated peak process memory \[MiB\]\s+(\d+)", text)
        if mem:
            entry["peak_mem_per_rank_MiB"] = max(int(m) for m in mem)
        entry["top_routines"] = sorted(
            ((k, v[1]) for k, v in report.items() if v[1] > 0.05 * report["CP2K"][1] and k != "CP2K"),
            key=lambda kv: -kv[1])[:15]
        gaps = re.findall(r"G0W0 indirect band gap \(eV\):\s+([-0-9.]+)", text) or \
            re.findall(r"GW HOMO-LUMO gap \(eV\):\s+([-0-9.]+)", text)
        if gaps:
            entry["gw_gap_eV"] = float(gaps[-1])
        etot = re.findall(r"ENERGY\| Total FORCE_EVAL \( QS \) energy \[(?:a\.u\.|hartree)\]:\s+([-0-9.]+)", text)
        if etot:
            entry["E_total_Ha"] = float(etot[-1])
    else:
        entry["status"] = classify_failure(run_dir)
    results.setdefault(case, {})[nodes] = entry

json.dump(results, open(OUT, "w"), indent=1)
for case, runs in results.items():
    print(case, {n: (r["status"], r.get("wall_s")) for n, r in sorted(runs.items(), key=lambda x: float(x[0]))})
