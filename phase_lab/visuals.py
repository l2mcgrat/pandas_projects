"""Headless, publication-friendly figures and an offline browser trajectory viewer."""

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import shutil
import zipfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
from scipy.interpolate import PchipInterpolator

from .engine import read_csv
from .documentation import build_theory
from .model import POTENTIALS
from .publishing import viewer_html, link_experiments
from .references import empirical_comparison

METRICS = {
    "o6": ("multipolar_order", "Multipolar O₆", "order"),
    "fcc": ("fcc_order", "FCC reference order", "fcc"),
    "polar": ("polar_order", "Polar order", "polar"),
    "nematic": ("nematic_order", "Nematic order", "nematic"),
    "q6": ("local_q6", "Local structural q₆ (12 neighbors)", "q6"),
    "density": ("density_g_cm3", "Density / g cm⁻³", "density"),
    "energy": ("potential_kJ_mol_molecule", "Potential / kJ mol⁻¹ molecule", "energy"),
    "msd": ("msd_final_nm2", "Nonaffine MSD / nm²", "msd"),
    "c2": ("rotation_c2", "Rotational C₂ (single origin)", "c2"),
}


def smooth_grid(group, key, resolution=45):
    """Shape-preserving T then log(P) interpolation; no extrapolation/new evidence."""
    temperatures = sorted({number(r, "temperature_K") for r in group})
    pressures = sorted({number(r, "pressure_kPa") for r in group if r["pressure_kPa"]})
    lookup = {(number(r, "temperature_K"), number(r, "pressure_kPa")): number(r, key)
              for r in group if r["pressure_kPa"] and r.get(key, "") != ""}
    if len(temperatures) < 2 or len(pressures) < 2 or len(lookup) != len(temperatures)*len(pressures):
        return None
    zz = np.array([[lookup[t, p] for t in temperatures] for p in pressures])
    tx, py = np.linspace(temperatures[0], temperatures[-1], resolution), np.geomspace(pressures[0], pressures[-1], resolution)
    zt = PchipInterpolator(temperatures, zz, axis=1)(tx)
    smooth = PchipInterpolator(np.log(pressures), zt, axis=0)(np.log(py))
    return {"t": tx.tolist(), "p": py.tolist(), "z": np.round(smooth, 6).tolist(),
            "samples": [[t, p, lookup[t, p]] for p in pressures for t in temperatures]}


COLORS = ["#5eead4", "#fbbf24", "#c4b5fd", "#fb7185"]
STYLE = {"figure.facecolor": "#0a1020", "axes.facecolor": "#101b30", "text.color": "#e2e8f0",
         "axes.labelcolor": "#b9c8df", "xtick.color": "#91a5c2", "ytick.color": "#91a5c2",
         "axes.edgecolor": "#334155", "grid.color": "#30425a", "font.family": "DejaVu Sans",
         "font.size": 10, "savefig.facecolor": "#0a1020"}


def number(row, key):
    return float(row[key])


def emit(fig, target, pdf):
    # Reserve space for the provenance footer, outside all axis labels.
    if fig.get_layout_engine() is not None:
        fig.get_layout_engine().set(rect=(.02, .055, .96, .945))
    fig.text(.02, .01, "DIPOLE ATLAS  /  qualitative surrogates · finite, short trajectories · not measured phase boundaries",
             color="#91a5c2", fontsize=8)
    fig.savefig(target, dpi=180, bbox_inches="tight")
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def plot_fingerprint(rows, reports, pdf):
    fig, axes = plt.subplots(2, 3, figsize=(15, 9), layout="constrained")
    keys = [("multipolar_order", "Multipolar order $O_6$"), ("fcc_order", "FCC reference order"),
            ("density_g_cm3", "Density / g cm$^{-3}$"), ("potential_kJ_mol_molecule", "Potential energy / kJ mol$^{-1}$ molecule"),
            ("msd_final_nm2", "End-of-plateau nonaffine MSD / nm$^2$"), ("angular_kl_nats", "Angular KL divergence / nats")]
    names = list(dict.fromkeys(row["molecule"] for row in rows))
    for mi, name in enumerate(names):
        pressures = list(dict.fromkeys(row["pressure_kPa"] for row in rows if row["molecule"] == name))
        for pi, pressure in enumerate(pressures):
            group = [row for row in rows if row["molecule"] == name and row["pressure_kPa"] == pressure]
            # Keep supplied protocol order; heating/cooling arrows are not thermodynamic boundaries.
            x = [number(row, "temperature_K") for row in group]
            label = group[0]["label"] + (f" · {float(pressure):g} kPa" if pressure else " · NVT")
            for ax, (key, title) in zip(axes.flat, keys):
                errors = [number(row, key + "_block_se") for row in group] if key + "_block_se" in group[0] else None
                ax.errorbar(x, [number(row, key) for row in group], yerr=errors, color=COLORS[mi % len(COLORS)],
                            linestyle=["-", "--", ":", "-."][pi % 4], marker="o", capsize=3, label=label)
                ax.set(xlabel="Target temperature / K", ylabel=title)
                ax.grid(alpha=.3)
    axes.flat[0].legend(fontsize=7, loc="best")
    fig.suptitle("ORDER / DISORDER\nTemperature-path fingerprints", fontsize=23, fontweight="bold")
    emit(fig, reports / "order_fingerprint.png", pdf)


def plot_angles(rows, records, reports, pdf):
    for name in dict.fromkeys(row["molecule"] for row in rows):
        subset = [row for row in rows if row["molecule"] == name]
        pressure = subset[0]["pressure_kPa"]
        group = sorted([row for row in subset if row["pressure_kPa"] == pressure], key=lambda row: number(row, "temperature_K"))
        chosen = [group[i] for i in sorted(set(np.linspace(0, len(group) - 1, min(3, len(group)), dtype=int)))]
        fig, axes = plt.subplots(2, len(chosen), figsize=(5 * len(chosen), 8), squeeze=False, layout="constrained")
        for column, row in enumerate(chosen):
            values = read_csv(records / row["condition"] / "orientation_histogram.csv")
            density = np.array([number(value, "relative_to_isotropic") for value in values]).reshape(10, 16)
            image = axes[0, column].imshow(density, origin="lower", aspect="auto", extent=[-180, 180, -1, 1],
                                           cmap="magma", vmin=0, vmax=max(3, float(density.max())))
            axes[0, column].set(xlabel="Azimuth φ / degrees", ylabel="cos(θ) — equal solid angle",
                                title=f'{number(row, "temperature_K"):g} K')
            fig.colorbar(image, ax=axes[0, column], label="Probability / isotropic probability", shrink=.75)
            degrees = np.arange(1, 7)
            axes[1, column].bar(degrees, [number(row, f"a{d}_squared") for d in degrees], color=COLORS[column % 4])
            axes[1, column].axhline(0, color="#91a5c2", linewidth=.8)
            axes[1, column].set(xlabel="Spherical harmonic degree ℓ", ylabel="Self-pair-corrected $A_ℓ^2$", xticks=degrees)
            axes[1, column].grid(axis="y", alpha=.2)
        pressure_label = f"{float(pressure):g} kPa" if pressure else "fixed volume"
        fig.suptitle(f"ANGULAR ATLAS / {group[0]['label']}\n{pressure_label} · pooled maps and instantaneous multipole spectrum", fontsize=17)
        emit(fig, reports / f"{name}_angles.png", pdf)


def plot_surfaces(rows, reports, pdf):
    for name in dict.fromkeys(row["molecule"] for row in rows):
        group = [row for row in rows if row["molecule"] == name and row["pressure_kPa"]]
        temperatures = sorted({number(row, "temperature_K") for row in group})
        pressures = sorted({number(row, "pressure_kPa") for row in group})
        if len(temperatures) < 2 or len(pressures) < 2:
            continue
        xx, yy = np.meshgrid(temperatures, pressures)
        fig = plt.figure(figsize=(15, 8))
        fig.subplots_adjust(left=.03, right=.93, bottom=.15, top=.82, wspace=.18)
        for index, (key, title) in enumerate((("multipolar_order", "$O_6$ multipolar order"), ("fcc_order", "FCC reference order")), 1):
            lookup = {(number(row, "temperature_K"), number(row, "pressure_kPa")): number(row, key) for row in group}
            zz = np.array([[lookup[(t, p)] for t in temperatures] for p in pressures])
            ax = fig.add_subplot(1, 2, index, projection="3d")
            grid = smooth_grid(group, key, 80)
            if grid is None:
                continue
            sx, sy = np.meshgrid(grid["t"], np.log10(grid["p"]))
            surface = ax.plot_surface(sx, sy, np.array(grid["z"]), cmap="viridis", alpha=.9,
                                      linewidth=0, antialiased=True, rcount=80, ccount=80,
                                      vmin=float(zz.min()), vmax=float(zz.max()))
            ax.scatter(xx.ravel(), np.log10(yy.ravel()), zz.ravel(), color="#fbbf24", s=26, depthshade=False)
            ax.set(xlabel="Temperature / K", ylabel="Pressure / kPa (log)", zlabel=title, title=title,
                   yticks=np.log10(pressures), yticklabels=[f"{p:g}" for p in pressures])
            ax.set_box_aspect((1, 1, .8), zoom=.82)
            for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
                axis.set_pane_color((.07, .12, .21, 1))
            ax.view_init(elev=28, azim=-130)
            fig.colorbar(surface, ax=ax, shrink=.5, pad=.12)
        fig.suptitle(f"{group[0]['label']} / {POTENTIALS.get(group[0].get('potential', 'coulomb_lj'))}\nPCHIP in T, log(P) · gold = simulated samples · NOT a phase boundary", fontsize=14)
        emit(fig, reports / f"{name}_surface.png", pdf)


def compact_trajectory(records, row):
    """Bound browser payloads without reducing the canonical CSV trajectory."""
    folder = records / row["condition"]
    thermo = read_csv(folder / "thermodynamics.csv")
    frames = sorted(set(np.linspace(0, len(thermo) - 1, min(120, len(thermo)), dtype=int).tolist()))
    count = int(row["molecules"])
    ids = set(np.linspace(0, count - 1, min(256, count), dtype=int).tolist())
    selected = {frame: [] for frame in frames}
    with (folder / "trajectory.csv").open(newline="", encoding="utf-8") as stream:
        for sample in csv.DictReader(stream):
            frame = int(sample["frame"])
            if frame in selected and int(sample["molecule_id"]) in ids:
                selected[frame].append([round(float(sample[key]), 5) for key in
                                        ("x_nm", "y_nm", "z_nm", "dipole_ux", "dipole_uy", "dipole_uz")])
    return {
        "summary": row,
        "empirical": empirical_comparison(row["molecule"], row["temperature_K"], row["pressure_kPa"]),
        "frames": [{"points": selected[i], "time": number(thermo[i], "time_ps"),
                    "box": number(thermo[i], "box_nm"), "order": number(thermo[i], "multipolar_order"),
                    "fcc": number(thermo[i], "fcc_order"), "density": number(thermo[i], "density_g_cm3"),
                    "energy": number(thermo[i], "potential_kJ_mol_molecule"),
                    **{alias: float(thermo[i][key]) if thermo[i].get(key, "") != "" else None
                       for alias, key in (("polar", "polar_order"), ("nematic", "nematic_order"),
                                          ("q6", "local_q6"), ("msd", "msd_nonaffine_nm2"),
                                          ("c2", "rotation_c2"), ("wall", "wall_kJ_mol_molecule"))},
                    "temperature": number(thermo[i], "measured_temperature_K")} for i in frames],
    }


def render_run(root, run_id):
    records = root / "records" / "phase_simulations" / run_id
    metadata = json.loads((records / "metadata.json").read_text(encoding="utf-8"))
    if metadata["status"] != "complete":
        raise ValueError("Only completed simulation runs can be rendered or published.")
    rows = read_csv(records / "summary.csv")
    for row in rows:
        row.setdefault("potential", "coulomb_lj")
        row.setdefault("boundary", "periodic")
        row.setdefault("density_mode", "legacy")
    reports = root / "reports" / "phase_simulations" / run_id
    media = root / "media" / "phase_simulations" / run_id
    reports.mkdir(parents=True, exist_ok=True)
    media.mkdir(parents=True, exist_ok=True)
    provenance = build_theory(reports)
    for name in ("theory.html", "theory.pdf", "theory.tex", "theory-source.json"):
        shutil.copy2(reports / name, media / name)
    provenance.update({"rendered_utc": datetime.now(timezone.utc).isoformat(), "run_id": run_id,
                       "renderer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                       "reference_sha256": hashlib.sha256((Path(__file__).parent / "references.py").read_bytes()).hexdigest()})
    (media / "render_metadata.json").write_text(json.dumps(provenance, indent=2), encoding="utf-8")
    with plt.rc_context(STYLE), PdfPages(reports / "dipole_atlas.pdf") as pdf:
        potentials = list(dict.fromkeys(row["potential"] for row in rows))
        for potential in potentials:
            group = [r for r in rows if r["potential"] == potential]
            output = reports / potential if len(potentials) > 1 else reports
            output.mkdir(exist_ok=True)
            plot_fingerprint(group, output, pdf)
            plot_angles(group, records, output, pdf)
            plot_surfaces(group, output, pdf)
    surfaces = {}
    for potential in potentials:
        for name in dict.fromkeys(row["molecule"] for row in rows):
            group = [r for r in rows if r["molecule"] == name and r["potential"] == potential and r["pressure_kPa"]]
            surfaces[f"{potential}/{name}"] = {metric: smooth_grid(group, key) for metric, (key, _, _) in METRICS.items()}
    payload = {"runId": run_id, "notice": metadata["notice"],
               "potentials": POTENTIALS, "metrics": METRICS, "surfaces": surfaces,
               "conditions": [compact_trajectory(records, row) for row in rows]}
    (media / "trajectory.js").write_text("window.DIPOLE_ATLAS=" + json.dumps(payload, separators=(",", ":"), allow_nan=False) + ";\n", encoding="utf-8")
    for name in ("viewer.css", "viewer.js"):
        shutil.copy2(Path(__file__).parent / "web" / name, media / name)
    figures = [p.relative_to(reports).as_posix() for p in sorted(reports.rglob("*.png"))]
    (media / "index.html").write_text(viewer_html(run_id, metadata["notice"], figures,
                                                f"../../../reports/phase_simulations/{run_id}/"), encoding="utf-8")
    shutil.copy2(records / "summary.csv", media / "summary.csv")
    shutil.copy2(records / "metadata.json", media / "metadata.json")
    link_experiments(media.parent)
    with zipfile.ZipFile(media / "records.zip", "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(records.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(records).as_posix())
    for path in [*records.rglob("*.csv"), *media.glob("*"), *reports.glob("*")]:
        if path.is_file() and path.stat().st_size > 50 * 1024 ** 2:
            print(f"Large Git asset (>50 MiB): {path}. Split runs before committing; GitHub blocks ordinary files >100 MiB.")