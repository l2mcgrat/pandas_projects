"""Original, deterministic study illustrations; no publisher or document edits.

Run ``python -B -m site_content.diagrams`` from any working directory. The
optional ``--root`` chooses the repository/output root. Only the study asset
directory is written. Reproducibility is byte-for-byte within the same installed
NumPy/Matplotlib/font environment, not a promise across renderer versions.
"""

from __future__ import annotations

import argparse
from collections.abc import Iterator
from itertools import permutations
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np
from matplotlib.axes import Axes
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.patches import Circle, Polygon, Rectangle


BLUE = "#145da0"
ORANGE = "#b94b00"
GREEN = "#00776c"
PURPLE = "#7044a2"
INK = "#192d3e"
PALE = "#e5eef6"
COLORS = (BLUE, ORANGE, GREEN, PURPLE)
ASSET_DIRECTORY = Path("tex_images/mental_map/study")


def _figure(title: str, panels: int = 1) -> tuple[Figure, list[Axes]]:
    fig = Figure(figsize=(10, 4.6), layout="constrained")
    FigureCanvasAgg(fig)
    axes = list(fig.subplots(1, panels, squeeze=False)[0])
    fig.suptitle(title, fontsize=15, fontweight="bold", color=INK)
    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(alpha=0.2)
        ax.set_axisbelow(True)
    return fig, axes


def _diagram(ax: Axes, xmax: float = 10, ymax: float = 5) -> None:
    ax.set(xlim=(0, xmax), ylim=(0, ymax))
    ax.set_aspect("equal")
    ax.axis("off")


def _box(ax: Axes, x: float, y: float, text: str, width: float = 1.2,
         height: float = 0.65, color: str = PALE) -> None:
    ax.add_patch(Rectangle((x, y), width, height, facecolor=color, edgecolor=INK, lw=1.5))
    ax.text(x + width / 2, y + height / 2, text, ha="center", va="center", color=INK, fontsize=10)


def _arrow(ax: Axes, start: tuple[float, float], end: tuple[float, float],
           color: str = INK, label: str = "") -> None:
    ax.annotate("", xy=end, xytext=start,
                arrowprops={"arrowstyle": "->", "color": color, "lw": 1.8})
    if label:
        ax.text((start[0] + end[0]) / 2, (start[1] + end[1]) / 2 + 0.16,
                label, ha="center", fontsize=10, color=color)


def euler_decay(step: float, steps: int) -> tuple[np.ndarray, np.ndarray]:
    """Forward Euler for y'=-2y, y(0)=1; illustrates its stability limit."""
    if step <= 0 or steps < 0:
        raise ValueError("step must be positive and steps nonnegative")
    t = np.arange(steps + 1) * step
    return t, (1 - 2 * step) ** np.arange(steps + 1)


def closed_loop_poles(gains: np.ndarray) -> np.ndarray:
    """Track roots of s^3+3s^2+2s+K by minimum-distance branch matching."""
    previous = np.array([-2, -1, 0], dtype=complex)
    rows = []
    for gain in gains:
        roots = np.roots([1, 3, 2, float(gain)])
        matched = min(permutations(roots), key=lambda p: float(np.sum(np.abs(p - previous) ** 2)))
        previous = np.array(matched, dtype=complex)
        rows.append(previous)
    return np.asarray(rows).reshape((-1, 3))


def grid_path_counts(rows: int, columns: int) -> np.ndarray:
    """Count right/down paths with one way to reach each boundary cell."""
    if rows < 1 or columns < 1:
        raise ValueError("grid dimensions must be positive")
    counts = np.ones((rows, columns), dtype=object)
    for row in range(1, rows):
        for col in range(1, columns):
            counts[row, col] = counts[row - 1, col] + counts[row, col - 1]
    return counts


def _math_figures() -> Iterator[tuple[str, Figure]]:
    fig, (ax, bx) = _figure("Linear maps: singular directions and eigenvectors", 2)
    theta = np.linspace(0, 2 * np.pi, 361)
    circle = np.array([np.cos(theta), np.sin(theta)])
    matrix = np.array([[2.0, 1.0], [1.0, 2.0]])
    ellipse = matrix @ circle
    for panel, curve, title in ((ax, circle, "Input unit circle"), (bx, ellipse, "A = [[2,1],[1,2]]")):
        panel.plot(*curve, color=BLUE)
        panel.set(xlabel="x", ylabel="y", title=title, xlim=(-3.3, 3.3), ylim=(-3.3, 3.3))
        panel.set_aspect("equal")
    for vector, scale, color in ((np.array([1, 1]) / np.sqrt(2), 3, ORANGE),
                                 (np.array([-1, 1]) / np.sqrt(2), 1, GREEN)):
        _arrow(ax, (0, 0), tuple(vector), color)
        _arrow(bx, (0, 0), tuple(scale * vector), color, f"σ = {scale}")
    yield "math_svd", fig

    fig, (ax, bx) = _figure("Least squares: data residuals and orthogonal projection", 2)
    x = np.arange(6, dtype=float)
    y = np.array([1.2, 1.7, 3.1, 3.7, 5.2, 5.5])
    design = np.column_stack((np.ones_like(x), x))
    fit = design @ np.linalg.lstsq(design, y, rcond=None)[0]
    ax.scatter(x, y, color=INK, label="synthetic observations")
    ax.plot(x, fit, color=BLUE, label="least-squares line")
    ax.vlines(x, fit, y, color=ORANGE, label="vertical residuals")
    ax.set(xlabel="predictor x", ylabel="response y")
    ax.legend(fontsize=9)
    bx.plot([0, 4], [0, 2], color=BLUE, label="column-space slice")
    _arrow(bx, (0, 0), (1, 3), INK, "b")
    _arrow(bx, (0, 0), (2, 1), BLUE, "projection")
    _arrow(bx, (2, 1), (1, 3), ORANGE, "residual")
    bx.set(xlim=(-0.3, 4), ylim=(-0.3, 3.7), xlabel="observation-space coordinate 1",
           ylabel="observation-space coordinate 2", title="Geometry schematic (not the six data points)")
    bx.set_aspect("equal")
    yield "math_least_squares", fig

    fig, (ax, bx) = _figure("Local approximations: Newton iteration and Taylor error", 2)
    x = np.linspace(0, 2.4, 250)
    ax.plot(x, x * x - 2, label="f(x) = x² − 2", color=BLUE)
    ax.axhline(0, color=INK, lw=1)
    for point, color in ((2.0, ORANGE), (1.5, GREEN)):
        nxt = point - (point * point - 2) / (2 * point)
        ax.plot([nxt, point], [0, point * point - 2], "--o", color=color,
                label=f"tangent at {point:g}; next {nxt:.3f}")
    ax.set(xlabel="x", ylabel="f(x)")
    ax.legend(fontsize=9)
    h = np.logspace(-4, -0.2, 160)
    bx.loglog(h, np.abs(np.expm1(h) - h), color=BLUE, label="|exp(h) − 1 − h|")
    bx.loglog(h, h * h / 2, "--", color=ORANGE, label="h²/2 reference")
    bx.set(xlabel="expansion step h", ylabel="absolute error")
    bx.legend()
    yield "math_newton", fig

    fig, (ax, bx) = _figure("Numerical ODEs: accuracy is not the same as stability", 2)
    for panel in (ax, bx):
        t = np.linspace(0, 6, 300)
        panel.plot(t, np.exp(-2 * t), color=INK, label="exact exp(−2t)")
        panel.set(xlabel="time t", ylabel="y")
    for step, panel, color in ((0.1, ax, BLUE), (0.8, ax, ORANGE), (1.1, bx, PURPLE)):
        t, y = euler_decay(step, int(6 / step))
        panel.plot(t, y, "o--", color=color, label=f"Euler h={step}", markersize=4)
    ax.legend(fontsize=9)
    bx.legend(fontsize=9)
    yield "math_ode", fig

    fig, (ax, bx) = _figure("Uncertainty: repeated measurements versus the estimated mean", 2)
    x = np.linspace(-4, 4, 450)
    for sigma, label, color in ((1, "individual σ = 1", BLUE), (0.2, "mean: n = 25, SE = 0.2", ORANGE)):
        ax.plot(x, np.exp(-x * x / (2 * sigma * sigma)) / (sigma * np.sqrt(2 * np.pi)),
                label=label, color=color)
    ax.set(xlabel="error (independent, normal model)", ylabel="probability density")
    ax.legend(fontsize=9)
    n = np.arange(1, 101)
    bx.plot(n, 1 / np.sqrt(n), label="random standard error", color=BLUE)
    bx.plot(n, np.sqrt(1 / n + 0.25 ** 2), label="including independent calibration uncertainty 0.25", color=ORANGE)
    bx.axhline(0.25, color=INK, ls=":", label="calibration floor")
    bx.set(xlabel="sample count n", ylabel="combined standard uncertainty")
    bx.legend(fontsize=8)
    yield "math_uncertainty", fig

    fig, axes = _figure("Vector fields: flux and circulation measure different structure", 2)
    x, y = np.meshgrid(np.linspace(-1, 1, 9), np.linspace(-1, 1, 9))
    for ax, u, v, title in ((axes[0], x, y, "F=(x,y): div F=2, curl F=0"),
                           (axes[1], -y, x, "F=(−y,x): div F=0, curl F=2ẑ")):
        ax.quiver(x, y, u, v, color=BLUE)
        ax.add_patch(Circle((0, 0), 0.8, fill=False, ec=ORANGE, lw=2))
        ax.set(xlabel="x", ylabel="y", title=title, xlim=(-1.3, 1.3), ylim=(-1.3, 1.3))
        ax.set_aspect("equal")
    yield "math_fields", fig

    fig, (ax, bx) = _figure("Fourier representations: harmonics and spectral amplitudes", 2)
    x = np.linspace(-np.pi, np.pi, 1400)
    ax.plot(x, np.where(x < 0, -1, 1), color=INK, lw=1, label="periodic square wave")
    for maximum, color in ((3, BLUE), (15, ORANGE)):
        wave = sum(4 / (np.pi * k) * np.sin(k * x) for k in range(1, maximum + 1, 2))
        ax.plot(x, wave, label=f"odd harmonics through {maximum}", color=color)
    ax.set(xlabel="phase x (rad)", ylabel="amplitude")
    ax.legend(fontsize=8)
    k = np.arange(1, 16, 2)
    bx.stem(k, 4 / (np.pi * k), basefmt=" ")
    bx.set(xlabel="harmonic number k", ylabel="sine coefficient 4/(πk)", xticks=k)
    yield "math_fourier", fig


def _physics_figures() -> Iterator[tuple[str, Figure]]:
    fig, (ax, bx) = _figure("Damped oscillator: decaying motion and its phase portrait", 2)
    t = np.linspace(0, 18, 1000)
    zeta = 0.15
    wd = np.sqrt(1 - zeta ** 2)
    x = np.exp(-zeta * t) * (np.cos(wd * t) + zeta / wd * np.sin(wd * t))
    v = -np.exp(-zeta * t) * np.sin(wd * t) / wd
    ax.plot(t, x, color=BLUE)
    ax.plot(t, np.exp(-zeta * t) / wd, "--", color=ORANGE, label="decaying envelope")
    ax.set(xlabel="time (ω₀t)", ylabel="displacement / initial displacement")
    ax.legend()
    bx.plot(x, v, color=GREEN)
    bx.scatter([1, 0], [0, 0], color=[ORANGE, INK])
    bx.set(xlabel="displacement x", ylabel="scaled velocity", title="ζ = 0.15, x(0)=1, v(0)=0")
    yield "physics_oscillator", fig

    fig, (ax, bx) = _figure("Waves and optics: interference sits inside a diffraction envelope", 2)
    q = np.linspace(-4, 4, 1200)
    envelope = np.sinc(q) ** 2
    ax.plot(q, envelope, "--", color=ORANGE, label="one-slit envelope")
    ax.plot(q, envelope * np.cos(3 * np.pi * q) ** 2, color=BLUE, label="two slits: d/a = 3")
    ax.set(xlabel="a sin(θ) / λ", ylabel="normalized intensity")
    ax.legend(fontsize=9)
    bx.axhspan(-1.2, 0, color=PALE)
    bx.axhline(0, color=INK)
    bx.axvline(0, color=INK, ls=":")
    theta1 = np.pi / 4
    theta2 = np.arcsin(np.sin(theta1) / 1.5)
    _arrow(bx, (-np.sin(theta1), np.cos(theta1)), (0, 0), BLUE)
    _arrow(bx, (0, 0), (np.sin(theta2), -np.cos(theta2)), ORANGE)
    bx.text(-1.05, 0.9, "n₁=1, θ₁=45°")
    bx.text(-1.05, -0.85, "n₂=1.5, θ₂≈28.1°")
    bx.set(xlim=(-1.2, 1.2), ylim=(-1.2, 1.2), xlabel="tangential position", ylabel="normal position")
    bx.set_aspect("equal")
    yield "physics_optics", fig

    fig, (ax, bx) = _figure("Continuum models: small shear strain and no-slip flow", 2)
    ax.add_patch(Rectangle((0, 0), 1, 1, fill=False, ec=INK, ls="--", lw=2))
    ax.add_patch(Polygon([[0, 0], [1, 0], [1.3, 1], [0.3, 1]], fill=False, ec=BLUE, lw=2))
    _arrow(ax, (0.5, 1.1), (1.2, 1.1), ORANGE, "shear traction")
    ax.set(xlim=(-0.2, 1.6), ylim=(-0.2, 1.5), xlabel="x / height", ylabel="y / height",
           title="uₓ=γy; εₓᵧ=γ/2 (γ=0.3 schematic)")
    ax.set_aspect("equal")
    y = np.linspace(-1, 1, 101)
    bx.plot(1 - y ** 2, y, color=BLUE)
    for yy in np.linspace(-0.9, 0.9, 9):
        _arrow(bx, (0, float(yy)), (float(1 - yy ** 2), float(yy)), BLUE)
    bx.axhline(-1, color=INK, lw=3)
    bx.axhline(1, color=INK, lw=3)
    bx.set(xlabel="velocity / centreline velocity", ylabel="y / half-gap",
           title="Steady pressure-driven Newtonian flow", xlim=(-0.1, 1.2))
    yield "physics_continuum", fig

    fig, (ax, bx) = _figure("Heat equation: boundaries select the evolution", 2)
    x = np.linspace(0, 1, 301)
    for tau, color in zip((0, 0.02, 0.1, 0.3), COLORS):
        ax.plot(x, np.sin(np.pi * x) * np.exp(-np.pi ** 2 * tau), color=color, label=f"αt/L²={tau:g}")
    ax.set(xlabel="x/L", ylabel="temperature excess / scale", title="Fixed zero excess at both ends")
    ax.legend(fontsize=9)
    bx.plot(x, 1 - x, color=BLUE, label="fixed temperatures: steady linear profile")
    bx.plot(x, np.ones_like(x) * 0.5, "--", color=ORANGE, label="insulated: uniform final state")
    bx.set(xlabel="x/L", ylabel="scaled temperature", title="Different boundary data, different solutions")
    bx.legend(fontsize=8)
    yield "physics_heat", fig

    fig, (ax, bx) = _figure("Series RLC: phasors encode phase, not instantaneous vectors", 2)
    _arrow(ax, (0, 0), (2, 0), BLUE, "Vᵣ = IR")
    _arrow(ax, (2, 0), (2, 1.5), ORANGE, r"$V_L + V_C$")
    _arrow(ax, (0, 0), (2, 1.5), GREEN, "source V")
    ax.set(xlim=(-0.3, 3), ylim=(-0.5, 2.2), xlabel="in-phase component", ylabel="quadrature component",
           title="I is the reference; net inductive example")
    ax.set_aspect("equal")
    w = np.logspace(-1, 1, 500)
    bx.semilogx(w, 1 / np.sqrt(1 + (w - 1 / w) ** 2), color=BLUE)
    bx.axvline(1, color=ORANGE, ls="--", label="ω₀ = 1/√(LC)")
    bx.set(xlabel="ω/ω₀", ylabel="current magnitude / (V/R)", title="R=L=C=1 in consistent units")
    bx.legend()
    yield "physics_phasor", fig

    fig, (ax, bx) = _figure("Quantum confinement: box densities and oscillator levels", 2)
    x = np.linspace(0, 1, 450)
    for n, color in zip((1, 2, 3), COLORS):
        ax.plot(x, n * n + 0.8 * np.sin(n * np.pi * x) ** 2, color=color, label=f"n={n}; E/E₁={n*n}")
        ax.axhline(n * n, color=color, ls=":", lw=1)
    ax.set(xlabel="x/L", ylabel="E/E₁ + scaled probability density", ylim=(0, 11))
    ax.legend(fontsize=9)
    q = np.linspace(-3, 3, 400)
    bx.plot(q, q * q / 2, color=INK, label="V/(ℏω)=q²/2")
    for n, color in zip(range(4), COLORS):
        turning = np.sqrt(2 * n + 1)
        bx.hlines(n + 0.5, -turning, turning, color=color, lw=2)
        bx.text(turning + 0.07, n + 0.5, f"n={n}", va="center", fontsize=9)
    bx.set(xlabel="q=x√(mω/ℏ)", ylabel="energy / ℏω", ylim=(0, 5))
    bx.legend(fontsize=9)
    yield "physics_quantum", fig


def _chemistry_figures() -> Iterator[tuple[str, Figure]]:
    fig, (ax, bx) = _figure("Equilibrium: composition minimizes Gibbs energy", 2)
    fraction = np.linspace(0.001, 0.999, 700)
    dg0 = -1.4
    gibbs = fraction * dg0 + fraction * np.log(fraction) + (1 - fraction) * np.log(1 - fraction)
    equilibrium = 1 / (1 + np.exp(dg0))
    ax.plot(fraction, gibbs, color=BLUE)
    ax.axvline(equilibrium, color=ORANGE, ls="--", label=f"equilibrium xᵦ={equilibrium:.3f}")
    ax.set(xlabel="B mole fraction for ideal A ⇌ B", ylabel="G/(nRT), relative reference")
    ax.legend(fontsize=9)
    ph = np.linspace(0, 14, 400)
    base = 1 / (1 + 10 ** (4.8 - ph))
    bx.plot(ph, 1 - base, label="HA fraction", color=BLUE)
    bx.plot(ph, base, label="A⁻ fraction", color=ORANGE)
    bx.axvline(4.8, color=INK, ls=":", label="pKₐ=4.8")
    bx.set(xlabel="pH", ylabel="fraction of analytical acid", ylim=(0, 1.05))
    bx.legend(fontsize=9)
    yield "chemistry_equilibrium", fig

    fig, (ax, bx) = _figure("Reaction kinetics: barriers change rates, not equilibrium", 2)
    q = np.linspace(0, 1, 400)
    baseline = -0.7 * (3 * q ** 2 - 2 * q ** 3)
    for barrier, label, color in ((1.8, "uncatalysed path", BLUE), (0.85, "alternative catalysed path", ORANGE)):
        ax.plot(q, baseline + barrier * np.sin(np.pi * q) ** 2, color=color, label=label)
    ax.set(xlabel="schematic reaction coordinate", ylabel="relative free energy (arbitrary units)")
    ax.legend(fontsize=9)
    inverse_t = np.linspace(1 / 450, 1 / 280, 200)
    for ea, color in ((40000, BLUE), (65000, ORANGE)):
        bx.plot(1000 * inverse_t, np.log(1e10) - ea / 8.314462618 * inverse_t, color=color,
                label=f"Eₐ={ea/1000:g} kJ/mol, same prefactor")
    bx.set(xlabel="1000/T (K⁻¹)", ylabel="ln(k / s⁻¹)")
    bx.legend(fontsize=9)
    yield "chemistry_kinetics", fig

    fig, (ax, bx) = _figure("Bonding and stereochemistry: energies and 3D identity", 2)
    ax.hlines(0, 0.1, 0.9, color=INK)
    ax.hlines(0, 3.1, 3.9, color=INK)
    ax.hlines([-1, 1], 1.6, 2.4, color=[BLUE, ORANGE], lw=3)
    for endpoint in (0.9, 3.1):
        ax.plot([endpoint, 2], [0, -1], ":", color=BLUE)
        ax.plot([endpoint, 2], [0, 1], ":", color=ORANGE)
    ax.text(2, -0.9, "↑↓", ha="center", fontsize=16)
    ax.text(2, -1.35, "bonding σ", ha="center")
    ax.text(2, 1.15, "antibonding σ*", ha="center")
    ax.set(xlim=(0, 4), ylim=(-1.6, 1.6), ylabel="orbital energy (schematic)",
           xticks=[0.5, 2, 3.5], xticklabels=["H 1s", "H₂", "H 1s"])
    _diagram(bx, 6, 4)
    for center, sign in ((1.4, 1), (4.6, -1)):
        bx.text(center, 2, "C*", ha="center", va="center")
        for dx, dy, label, style in ((-0.8, 0.8, "A", "-"), (0.8, 0.8, "B", "-"),
                                      (-0.6, -0.8, "C", "--"), (0.6, -0.8, "D", "-")):
            bx.plot([center + 0.15 * sign * np.sign(dx), center + sign * dx], [2, 2 + dy],
                    style, color=INK, lw=4 if label == "D" else 1.5)
            bx.text(center + sign * dx, 2 + dy + 0.15 * np.sign(dy), label, ha="center")
    bx.plot([3, 3], [0.5, 3.5], ":", color=ORANGE)
    bx.text(3, 3.7, "mirror", ha="center")
    bx.text(3, 0.15, "four distinct groups; bold toward, dashed away", ha="center", fontsize=9)
    yield "chemistry_orbitals", fig

    fig, (ax, bx) = _figure("Macromolecules: broad size distributions and enzyme saturation", 2)
    mass = np.linspace(1, 150, 500)
    number = np.exp(-((np.log(mass) - 3.5) / 0.5) ** 2 / 2) / mass
    number /= np.trapezoid(number, mass)
    weight = mass * number / np.trapezoid(mass * number, mass)
    ax.plot(mass, number, color=BLUE, label="number-weighted density")
    ax.plot(mass, weight, color=ORANGE, label="mass-weighted density")
    ax.set(xlabel="molar mass (arbitrary units)", ylabel="normalized density")
    ax.legend(fontsize=9)
    substrate = np.linspace(0, 8, 300)
    bx.plot(substrate, substrate / (1 + substrate), color=GREEN)
    bx.axhline(1, color=INK, ls=":", label="Vmax")
    bx.scatter([1], [0.5], color=ORANGE, label="[S]=Kₘ; v=Vmax/2")
    bx.set(xlabel="[S]/Kₘ", ylabel="initial rate / Vmax")
    bx.legend(fontsize=9)
    yield "chemistry_polymers", fig

    fig, (ax, bx) = _figure("Characterization: spectral selectivity and probe-size bias", 2)
    wn = np.linspace(400, 2000, 700)
    for centres, offset, label, color in (((750, 1650), 0, "illustrative IR", BLUE),
                                         ((1050, 1650), 1.25, "illustrative Raman (offset)", ORANGE)):
        spectrum = sum(np.exp(-0.5 * ((wn - c) / 28) ** 2) for c in centres)
        ax.plot(wn, spectrum + offset, color=color, label=label)
    ax.set(xlabel="wavenumber / Raman shift (cm⁻¹)", ylabel="arbitrary signal; not measured data")
    ax.legend(fontsize=9)
    x = np.linspace(-3, 3, 600)
    surface = np.maximum(0, 1 - np.abs(x) / 0.4)
    measured = np.array([np.max(surface - (xx - x) ** 2 / 1.0) for xx in x])
    bx.plot(x, surface, color=INK, label="narrow true feature")
    bx.plot(x, measured, color=GREEN, label="finite parabolic-tip envelope")
    bx.set(xlabel="lateral position (schematic)", ylabel="height (schematic)")
    bx.legend(fontsize=9)
    yield "chemistry_characterization", fig


def _computation_figures() -> Iterator[tuple[str, Figure]]:
    fig, (ax,) = _figure("Array indexing versus linked traversal: addresses matter")
    _diagram(ax)
    for i, value in enumerate([8, 3, 7, 1, 9]):
        _box(ax, 1 + i * 1.3, 3.4, str(value))
        ax.text(1.6 + i * 1.3, 4.3, f"a[{i}]", ha="center")
    ax.text(1, 2.8, "Contiguous slots: address = base + i × slot_size; O(1) indexing")
    positions = [(1, 1), (4.4, 1.6), (7.7, 0.8)]
    for i, (x, y) in enumerate(positions):
        _box(ax, x, y, f"{[8,3,7][i]} | next", width=1.6)
        ax.text(x + 0.8, y - 0.3, ["0xA0", "0xF8", "0xC0"][i], ha="center", fontsize=9)
        if i < 2:
            _arrow(ax, (x + 1.6, y + 0.3), (positions[i + 1][0], positions[i + 1][1] + 0.3))
    ax.text(1, 0.1, "Linked nodes: scattered addresses; O(n) access by index")
    yield "computation_memory", fig

    fig, (ax,) = _figure("Stack and queue expose different removal orders")
    _diagram(ax)
    for i, value in enumerate(["A", "B", "C"]):
        _box(ax, 1.5, 0.7 + i * 0.75, value, width=1.7)
        _box(ax, 5 + i * 1.3, 2, value)
    _arrow(ax, (1.4, 4), (1.9, 3), BLUE, "push")
    _arrow(ax, (2.8, 3), (3.5, 4), ORANGE, "pop C")
    _arrow(ax, (5.4, 1.8), (4.6, 0.9), ORANGE, "dequeue A")
    _arrow(ax, (9.2, 3.2), (8.8, 2.3), BLUE, "enqueue")
    ax.text(2.35, 0.2, "LIFO: last in, first out", ha="center")
    ax.text(7, 0.2, "FIFO: first in, first out", ha="center")
    ax.text(7, 3.8, "front                      back", ha="center")
    yield "computation_stack_queue", fig

    fig, axes = _figure("Binary search tree and min-heap: different invariants", 2)
    locations = [(2.5, 3.5), (1.3, 2.3), (3.7, 2.3), (0.7, 1.1), (1.9, 1.1), (3.1, 1.1), (4.3, 1.1)]
    for ax, values, title in ((axes[0], [5, 2, 8, 1, 4, 6, 9], "BST: left < node < right"),
                              (axes[1], [1, 3, 2, 8, 5, 7, 4], "Heap: parent ≤ children only")):
        _diagram(ax, 5, 4.5)
        ax.set_title(title, fontsize=11)
        for i, (x, y) in enumerate(locations):
            if i:
                px, py = locations[(i - 1) // 2]
                ax.plot([px, x], [py, y], color=INK, zorder=1)
            ax.add_patch(Circle((x, y), 0.24, fc=PALE, ec=BLUE, zorder=2))
            ax.text(x, y, str(values[i]), ha="center", va="center", zorder=3)
        ax.text(2.5, 0.25, "array: " + ", ".join(map(str, values)), ha="center", fontsize=9)
    yield "computation_tree_heap", fig

    fig, (ax, bx) = _figure("Breadth-first search: shortest distances in an unweighted graph", 2)
    positions = [(0, 0), (1, 1), (1, -1), (2, 1), (2, -1), (3, 0)]
    edges = [(0, 1), (0, 2), (1, 3), (1, 4), (2, 4), (3, 5), (4, 5)]
    for a, b in edges:
        ax.plot([positions[a][0], positions[b][0]], [positions[a][1], positions[b][1]], color=INK)
    for i, ((x, y), layer) in enumerate(zip(positions, [0, 1, 1, 2, 2, 3])):
        ax.add_patch(Circle((x, y), 0.22, fc=COLORS[layer], zorder=3))
        ax.text(x, y, chr(65 + i), color="white", ha="center", va="center", zorder=4)
    ax.set(xlim=(-0.5, 3.5), ylim=(-1.5, 1.5), xlabel="BFS distance from A", yticks=[], xticks=range(4))
    ax.set_aspect("equal")
    _diagram(bx, 5, 4)
    for row, (label, values) in enumerate((("start", "A"), ("pop A", "B  C"), ("pop B", "C  D  E"),
                                          ("pop C", "D  E"), ("pop D", "E  F"))):
        y = 3.2 - row * 0.65
        bx.text(0, y + 0.2, label, fontsize=10)
        _box(bx, 1.4, y, values, width=3, height=0.45)
    bx.text(2.5, 0, "Mark visited on enqueue; E enters only once", ha="center", fontsize=9)
    yield "computation_bfs", fig

    fig, (ax,) = _figure("Lower bound: a half-open interval with a precise invariant")
    _diagram(ax, 11, 5)
    values = [1, 3, 3, 5, 8, 10, 12, 15]
    for row, (lo, hi, mid) in enumerate([(0, 8, 4), (0, 4, 2), (3, 4, 3), (3, 3, None)]):
        y = 3.7 - row * 1.05
        for i, value in enumerate(values):
            color = "#f9dabd" if i < lo else ("#d6e8df" if i >= hi else PALE)
            _box(ax, 2.4 + i, y, str(value), width=0.9, height=0.6, color=color)
            if i == mid:
                ax.text(2.85 + i, y + 0.7, "mid", ha="center", fontsize=9, color=BLUE)
        ax.text(0, y + 0.25, f"[lo,hi)=[{lo},{hi})", fontsize=10)
    ax.text(5.5, 0.1, "target=5; orange values <5; green values ≥5; return index 3", ha="center", fontsize=10)
    yield "computation_binary_search", fig

    fig, (ax,) = _figure("Merge sort: stable merging preserves equal-key identity")
    _diagram(ax, 12, 5)
    _box(ax, 3.5, 4.1, "4a, 2, 4b, 1", width=5)
    _box(ax, 1, 2.9, "4a, 2", width=3)
    _box(ax, 8, 2.9, "4b, 1", width=3)
    _arrow(ax, (4.3, 4.05), (2.5, 3.6))
    _arrow(ax, (7.7, 4.05), (9.5, 3.6))
    for x, label in ((0.5, "4a"), (3, "2"), (7.5, "4b"), (10, "1")):
        _box(ax, x, 1.7, label)
    _box(ax, 1, 0.65, "2, 4a", width=3)
    _box(ax, 8, 0.65, "1, 4b", width=3)
    _arrow(ax, (4.1, 0.95), (5.1, 0.95), BLUE)
    _arrow(ax, (7.9, 0.95), (6.9, 0.95), BLUE)
    ax.text(6, 0.1, "final: 1, 2, 4a, 4b — choose left on ties", ha="center", fontsize=11)
    yield "computation_merge_sort", fig

    fig, (ax, bx) = _figure("Dynamic programming: dependencies become a table", 2)
    counts = grid_path_counts(4, 5)
    ax.imshow(np.asarray(counts, dtype=float), cmap="Blues", vmin=0, vmax=55)
    for row in range(4):
        for col in range(5):
            ax.text(col, row, str(counts[row, col]), ha="center", va="center", color=INK)
    ax.set(xlabel="column j", ylabel="row i", xticks=range(5), yticks=range(4))
    ax.grid(False)
    _diagram(bx, 5, 4)
    _box(bx, 2, 2.8, "D[i−1,j]", width=1.8)
    _box(bx, 0.1, 1.2, "D[i,j−1]", width=1.8)
    _box(bx, 2.5, 1.2, "D[i,j]", width=1.8)
    _arrow(bx, (2.9, 2.7), (3.4, 1.9), BLUE)
    _arrow(bx, (1.95, 1.5), (2.45, 1.5), BLUE)
    bx.text(2.5, 0.35, "D[i,j] = top + left\nBoundary row and column contain ones", ha="center", fontsize=10)
    yield "computation_dp", fig

    fig, (ax,) = _figure("Prefix sums and sliding windows: track exactly what is included")
    _diagram(ax, 11, 5)
    values = [2, 1, 3, 2, 4, 1]
    prefix = np.concatenate(([0], np.cumsum(values)))
    for i, value in enumerate(values):
        _box(ax, 2 + i * 1.2, 2.7, str(value), width=1.1,
             color="#f9dabd" if 1 <= i < 4 else PALE)
    for i, value in enumerate(prefix):
        ax.text(1.95 + i * 1.2, 4.1, str(value), ha="center", color=GREEN)
    ax.text(0, 4.1, "prefix P")
    ax.text(0, 3, "array a")
    _arrow(ax, (3.2, 1.5), (3.2, 2.6), ORANGE, "l=1")
    _arrow(ax, (6.8, 1.5), (6.8, 2.6), ORANGE, "r=4")
    ax.text(5.5, 0.9, "sum a[1:4] = P[4] − P[1] = 8 − 2 = 6", ha="center")
    ax.text(5.5, 0.25, "Prefix sums permit negative values; monotone sum windows usually do not", ha="center", fontsize=10)
    yield "computation_windows", fig


def _control_figures() -> Iterator[tuple[str, Figure]]:
    fig, (ax,) = _figure("Negative unity feedback: signals and disturbance entry points")
    _diagram(ax, 12, 5)
    ax.add_patch(Circle((2, 3), 0.27, fill=False, ec=INK))
    ax.text(1.75, 3.35, "+")
    ax.text(2.2, 2.55, "−")
    _arrow(ax, (0.3, 3), (1.7, 3), BLUE, "r")
    _arrow(ax, (2.3, 3), (3.3, 3), BLUE, "e")
    _box(ax, 3.4, 2.6, "C(s)", width=1.6, height=0.8)
    _arrow(ax, (5.1, 3), (6.7, 3), BLUE, "u")
    _box(ax, 6.8, 2.6, "G(s)", width=1.6, height=0.8)
    _arrow(ax, (8.5, 3), (9.1, 3))
    ax.add_patch(Circle((9.4, 3), 0.25, fill=False, ec=INK))
    _arrow(ax, (9.4, 4.3), (9.4, 3.3), ORANGE, "d")
    _arrow(ax, (9.7, 3), (11.5, 3), BLUE, "y")
    ax.plot([10.7, 10.7, 2], [3, 1.2, 1.2], color=INK)
    _arrow(ax, (2, 1.2), (2, 2.7))
    ax.text(6, 0.4, "L=CG       S=1/(1+L)       T=L/(1+L)       y=Tr+Sd", ha="center")
    yield "control_feedback", fig

    fig, (ax, bx) = _figure("Poles predict natural modes; cancellations can hide unstable states", 2)
    ax.axvspan(-3, 0, color="#e7f1eb")
    ax.axvline(0, color=INK)
    ax.axhline(0, color=INK, lw=0.8)
    ax.scatter([-1, -1, -2, 0.5], [1.5, -1.5, 0, 0], marker="x", s=90, color=[BLUE, BLUE, GREEN, ORANGE])
    ax.set(xlim=(-3, 1.2), ylim=(-2.5, 2.5), xlabel="Re(s)", ylabel="Im(s)", title="Left-half-plane poles decay")
    ax.text(0.15, 0.35, "unstable", color=ORANGE)
    t = np.linspace(0, 5, 250)
    bx.plot(t, np.exp(-t), color=BLUE, label="visible mode exp(−t)")
    bx.plot(t, np.exp(0.5 * t), color=ORANGE, label="hidden mode exp(0.5t)")
    bx.set(xlabel="time", ylabel="normalized mode amplitude", title="A=diag(−1,0.5), B=(1,0)ᵀ, C=(1,0)")
    bx.legend(fontsize=9)
    yield "control_poles", fig

    fig, (ax,) = _figure("Root locus for L(s)=K/[s(s+1)(s+2)], negative feedback")
    gains = np.linspace(0, 20, 1001)
    roots = closed_loop_poles(gains)
    for i, color in enumerate(COLORS[:3]):
        ax.plot(roots[:, i].real, roots[:, i].imag, color=color)
        a, b = roots[300, i], roots[340, i]
        _arrow(ax, (float(a.real), float(a.imag)), (float(b.real), float(b.imag)), color)
    ax.scatter([-2, -1, 0], [0, 0, 0], marker="x", color=INK, s=90, label="open-loop poles, K=0")
    ax.scatter([0, 0], [-np.sqrt(2), np.sqrt(2)], color=ORANGE, label="K=6: imaginary-axis crossing")
    ax.axvline(0, color=INK, lw=1)
    ax.axhline(0, color=INK, lw=0.7)
    ax.set(xlabel="Re(s)", ylabel="Im(s)", title="0 < K < 6 stable; arrows show increasing K")
    ax.legend(fontsize=9, loc="upper left")
    yield "control_root_locus", fig

    fig = Figure(figsize=(10, 6), layout="constrained")
    FigureCanvasAgg(fig)
    ax, bx = fig.subplots(2, 1, sharex=True)
    fig.suptitle("Bode plot: L(s)=2/[s(s+1)(s+2)]", fontsize=15, fontweight="bold")
    w = np.logspace(-2, 2, 1400)
    s = 1j * w
    loop = 2 / (s * (s + 1) * (s + 2))
    mag = 20 * np.log10(np.abs(loop))
    phase = np.unwrap(np.angle(loop)) * 180 / np.pi
    crossover = float(np.interp(0, mag[::-1], w[::-1]))
    phase_at = float(np.interp(crossover, w, phase))
    ax.semilogx(w, mag, color=BLUE)
    bx.semilogx(w, phase, color=GREEN)
    ax.axhline(0, color=INK, ls=":")
    bx.axhline(-180, color=INK, ls=":")
    for panel in (ax, bx):
        panel.axvline(crossover, color=ORANGE, ls="--")
        panel.grid(alpha=0.25, which="both")
    bx.annotate(f"phase margin ≈ {180+phase_at:.1f}°", xy=(crossover, phase_at), xytext=(2, -120),
                arrowprops={"arrowstyle": "->"}, color=ORANGE)
    ax.set(ylabel="magnitude (dB)")
    bx.set(xlabel="angular frequency (rad / time unit)", ylabel="unwrapped phase (degrees)")
    yield "control_bode", fig

    fig, (ax, bx) = _figure("Nyquist: count the complete contour, not just positive frequencies", 2)
    w = np.concatenate((-np.logspace(4, -4, 1800), [0], np.logspace(-4, 4, 1800)))
    for panel, gain in ((ax, 2), (bx, 10)):
        response = gain / (1 + 1j * w) ** 3
        panel.plot(response.real, response.imag, color=BLUE)
        for index in (1300, 2050, 2500):
            z, nxt = response[index], response[index + 20]
            _arrow(panel, (float(z.real), float(z.imag)), (float(nxt.real), float(nxt.imag)), BLUE)
        panel.scatter([-1], [0], marker="x", color=ORANGE, s=85)
        panel.axhline(0, color=INK, lw=0.7)
        panel.axvline(0, color=INK, lw=0.7)
        panel.set(xlabel="Re L(jω)", ylabel="Im L(jω)",
                  title=f"L={gain}/(s+1)³; P=0, Z={0 if gain < 8 else 2}")
        panel.set_aspect("equal", adjustable="datalim")
    yield "control_nyquist", fig

    fig, (ax, bx) = _figure("Sensitivity trade-offs and realizable compensator phase", 2)
    w = np.logspace(-2, 2, 1000)
    s = 1j * w
    loop = 2 / (s * (s + 1) * (s + 2))
    sensitivity = 1 / (1 + loop)
    complementary = loop / (1 + loop)
    ax.semilogx(w, 20 * np.log10(np.abs(sensitivity)), color=BLUE, label="S: output disturbance")
    ax.semilogx(w, 20 * np.log10(np.abs(complementary)), color=ORANGE, label="T: reference / sensor noise magnitude")
    ax.axhline(0, color=INK, ls=":")
    ax.set(xlabel="angular frequency", ylabel="magnitude (dB)")
    ax.legend(fontsize=8)
    lead = (1 + s) / (1 + s / 10)
    lag = (1 + s / 10) / (1 + s)
    bx.semilogx(w, np.angle(lead, deg=True), color=GREEN, label="lead: zero −1, pole −10")
    bx.semilogx(w, np.angle(lag, deg=True), color=PURPLE, label="lag: pole −1, zero −10")
    bx.set(xlabel="angular frequency", ylabel="compensator phase (degrees)")
    bx.legend(fontsize=8)
    yield "control_sensitivity", fig


def _nano_figures() -> Iterator[tuple[str, Figure]]:
    fig, (ax, bx) = _figure("Equilibrium p–n junction: mobile carriers leave fixed dopant charge", 2)
    x = np.linspace(-2, 2, 500)
    charge = np.where((x > -1) & (x < 0), -1, np.where((x >= 0) & (x < 1), 1, 0))
    field = np.where(np.abs(x) <= 1, np.abs(x) - 1, 0)
    ax.plot(x, charge, color=BLUE, label="space charge ρ (scaled)")
    ax.plot(x, field, color=ORANGE, label="electric field E (scaled)")
    ax.axvspan(-1, 1, color=PALE, alpha=0.5)
    ax.set(xlabel="x (p side left, n side right)", ylabel="normalized charge / field")
    ax.legend(fontsize=9)
    potential = np.where(x < -1, 0, np.where(x < 0, (x + 1) ** 2 / 2,
                         np.where(x < 1, 1 - (1 - x) ** 2 / 2, 1)))
    bx.plot(x, 1.7 - potential, color=BLUE, label=r"conduction edge $E_C$")
    bx.plot(x, 0.5 - potential, color=GREEN, label=r"valence edge $E_V$")
    bx.axhline(0.6, color=ORANGE, ls="--", label="constant equilibrium Fermi level")
    bx.set(xlabel="x (symmetric depletion approximation)", ylabel="electron energy (schematic)")
    bx.legend(fontsize=8)
    yield "nano_junction", fig

    fig, (ax, bx) = _figure("MOSFET: gate electrostatics controls a conducting channel", 2)
    _diagram(ax, 6, 4)
    _box(ax, 0.2, 0.5, "p-type body", width=5.6, height=1.5)
    _box(ax, 0.5, 1.7, "n+ source", width=1.4, height=0.7, color="#d6e8df")
    _box(ax, 4.1, 1.7, "n+ drain", width=1.4, height=0.7, color="#d6e8df")
    _box(ax, 1.9, 2.25, "oxide", width=2.2, height=0.35, color="#f9dabd")
    _box(ax, 1.9, 2.65, "gate", width=2.2, height=0.55)
    ax.plot([1.9, 4.1], [2.02, 2.02], color=BLUE, lw=3)
    ax.text(3, 0.1, "inversion channel forms below oxide (not to scale)", ha="center", fontsize=9)
    vds = np.linspace(0, 3.5, 300)
    for overdrive, color in ((1, BLUE), (1.5, ORANGE), (2, GREEN)):
        current = np.where(vds < overdrive, overdrive * vds - vds ** 2 / 2, overdrive ** 2 / 2)
        bx.plot(vds, current, color=color, label=f"VGS−Vth={overdrive:g}")
    bx.set(xlabel="VDS (scaled volts)", ylabel="ID / (μCox W/L)", title="Ideal long-channel curves; no channel-length modulation")
    bx.legend(fontsize=8)
    yield "nano_mosfet", fig

    fig, (ax, bx) = _figure("Photonics: index confinement and wavelength-selective interference", 2)
    x = np.linspace(-3, 3, 600)
    ax.plot(x, np.where(np.abs(x) < 1, 1.5, 1.0), color=INK, label="index profile (scaled)")
    mode = np.where(np.abs(x) <= 1, np.cos(0.8 * x), np.cos(0.8) * np.exp(-0.8 * np.tan(0.8) * (np.abs(x) - 1)))
    ax.plot(x, mode, color=BLUE, label="schematic guided field amplitude")
    ax.set(xlabel="transverse coordinate / half-width", ylabel="index / field (different scales)")
    ax.legend(fontsize=9)
    phase = np.linspace(-np.pi, np.pi, 1000)
    finesse_coefficient = 40
    bx.plot(phase, 1 / (1 + finesse_coefficient * np.sin(phase / 2) ** 2), color=GREEN)
    bx.set(xlabel="round-trip phase detuning (rad)", ylabel="normalized transmitted intensity",
           title="Lossless Fabry–Pérot: Airy coefficient F=40")
    yield "nano_photonics", fig

    fig, (ax, bx) = _figure("Interfaces: adsorption saturates; equilibrium voltage is logarithmic", 2)
    pressure = np.logspace(-3, 3, 400)
    ax.semilogx(pressure, pressure / (1 + pressure), color=BLUE)
    ax.axvline(1, color=ORANGE, ls=":", label="Kp=1, half coverage")
    ax.set(xlabel="dimensionless pressure Kp", ylabel="Langmuir coverage θ", ylim=(0, 1.05))
    ax.legend(fontsize=9)
    logq = np.linspace(-4, 4, 300)
    for n, color in ((1, GREEN), (2, PURPLE)):
        bx.plot(logq, -8.314462618 * 298.15 / (n * 96485.33212) * np.log(10) * logq,
                color=color, label=f"n={n} electrons")
    bx.set(xlabel="log₁₀ Q (dimensionless activities)", ylabel="E−E° (V)", title="Nernst equilibrium, T=298.15 K")
    bx.legend(fontsize=9)
    yield "nano_surfaces", fig


def build_diagrams(root: Path) -> list[Path]:
    """Write 36 original figures as PNG/SVG pairs and return all 72 paths.

    No random sampling, network, LaTeX executable, or interactive backend is
    required. Matplotlib's bundled DejaVu Sans is used; SVG dates are omitted
    and element hashes are fixed. Unknown files in the directory are preserved.
    """
    output = Path(root).resolve() / ASSET_DIRECTORY
    output.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    style = {
        "font.family": "DejaVu Sans", "font.size": 10, "axes.labelcolor": INK,
        "text.color": INK, "axes.edgecolor": INK, "axes.titlepad": 12,
        "lines.linewidth": 2, "savefig.facecolor": "white", "figure.facecolor": "white",
        "svg.hashsalt": "mental-map-study-v1", "svg.fonttype": "none", "text.usetex": False,
    }
    with matplotlib.rc_context(style):
        for factory in (_math_figures, _physics_figures, _chemistry_figures,
                        _computation_figures, _control_figures, _nano_figures):
            for name, fig in factory():
                try:
                    for extension in ("png", "svg"):
                        path = output / f"{name}.{extension}"
                        metadata = ({"Software": "Original mental-map study diagrams"} if extension == "png"
                                    else {"Date": None, "Creator": "Original mental-map study diagrams"})
                        fig.savefig(path, format=extension, dpi=160, metadata=metadata)
                        paths.append(path)
                finally:
                    # Shared log axes otherwise warn as clear() resets limits to zero.
                    for ax in fig.axes:
                        ax.set_xscale("linear")
                        ax.set_yscale("linear")
                    fig.clear()
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1],
                        help="repository root; defaults to this module's parent repository")
    args = parser.parse_args()
    paths = build_diagrams(args.root)
    print(f"Generated {len(paths) // 2} figures ({len(paths)} PNG/SVG files) in {paths[0].parent}")


if __name__ == "__main__":
    main()