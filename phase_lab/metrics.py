"""Rotational invariants and periodic-box structural diagnostics."""

import numpy as np


def minimum_image(displacement, box):
    """Orthorhombic periodic displacement (the isotropic barostat preserves this)."""
    return displacement - box * np.rint(displacement / box)


def molecular_coordinates(positions, velocities, box, periodic=True):
    pairs = positions.reshape(-1, 2, 3)
    bonds = pairs[:, 1] - pairs[:, 0]
    if periodic:
        bonds = minimum_image(bonds, box)
    centers = pairs[:, 0] + bonds / 2
    if periodic:
        centers %= box
    axes = bonds / np.linalg.norm(bonds, axis=1)[:, None]
    com_velocity = velocities.reshape(-1, 2, 3).mean(axis=1)
    return centers, axes, com_velocity


def angular_histogram(axes, bins=(10, 16)):
    """Uniform cos(theta), NOT uniform theta, gives equal-solid-angle bins."""
    phi = np.arctan2(axes[:, 1], axes[:, 0])
    return np.histogram2d(np.clip(axes[:, 2], -1, 1), phi,
                          bins=bins, range=[[-1, 1], [-np.pi, np.pi]])


def orientation_metrics(axes, max_degree=6):
    """Addition theorem: A_l^2 = mean_ij P_l(u_i dot u_j).

    Remove diagonal self-pairs so the isotropic expectation is zero. Keep signed
    estimates in CSV; clip only when combining into the nonnegative display score.
    l=4/6 retain multi-axis order that polar and nematic order can miss.
    """
    n = len(axes)
    if n < 2:
        raise ValueError("At least two orientations are required.")
    dots = np.clip(axes @ axes.T, -1, 1)
    previous = np.ones_like(dots)
    current = dots.copy()
    spectrum = []
    for degree in range(1, max_degree + 1):
        if degree > 1:
            previous, current = current, ((2 * degree - 1) * dots * current
                                          - (degree - 1) * previous) / degree
        spectrum.append(float((current.sum() - n) / (n * (n - 1))))
    tensor = 1.5 * (axes.T @ axes) / n - 0.5 * np.eye(3)
    return {
        "polar_order": float(np.linalg.norm(axes.mean(axis=0))),
        "nematic_order": float(np.linalg.eigvalsh(tensor)[-1]),
        "multipolar_order": float(np.sqrt(np.mean(np.maximum(spectrum, 0)))),
        **{f"a{degree}_squared": value for degree, value in enumerate(spectrum, 1)},
    }


def crystal_order(centers, box, cells):
    """FCC reference Bragg intensity: unity for initial FCC, ~1/N for a gas.

    Translation invariant, but tied to initial crystal orientation; not a general
    bond-order classifier. Fractional coordinates remove uniform box expansion.
    """
    reciprocal = cells * np.array([[1, 1, 1], [1, 1, -1], [1, -1, 1], [-1, 1, 1],
                                    [2, 0, 0], [0, 2, 0], [0, 0, 2]])
    amplitudes = np.exp(2j * np.pi * ((centers / box) @ reciprocal.T)).mean(axis=0)
    return float(np.mean(np.abs(amplitudes) ** 2))


def block_standard_error(values, blocks=4):
    """Exploratory block SE, not a convergence certificate for correlated MD."""
    chunks = np.array_split(np.asarray(values, dtype=float), min(blocks, len(values)))
    means = np.array([chunk.mean() for chunk in chunks])
    return float(means.std(ddof=1) / np.sqrt(len(means))) if len(means) > 1 else 0.0


def local_structure(centers, box, periodic=True):
    """Mean local Steinhardt q6 over 12 nearest centers; NOT dipole O6.

    Addition theorem avoids harmonic convention/version dependencies. Twelve
    nearest neighbors are used even in dilute states: this is not a phase label.
    """
    delta = centers[None, :, :] - centers[:, None, :]
    if periodic:
        delta = minimum_image(delta, box)
    distances = np.linalg.norm(delta, axis=2)
    np.fill_diagonal(distances, np.inf)
    neighbors = np.argsort(distances, axis=1)[:, :min(12, len(centers)-1)]
    vectors = np.take_along_axis(delta, neighbors[:, :, None], axis=1)
    vectors /= np.linalg.norm(vectors, axis=2)[:, :, None]
    dots = np.clip(np.einsum("nik,njk->nij", vectors, vectors), -1, 1)
    p6 = (231*dots**6 - 315*dots**4 + 105*dots**2 - 5) / 16
    return {"local_q6": float(np.sqrt(np.maximum(p6.mean(axis=(1, 2)), 0)).mean()),
            "nearest_neighbor_nm": float(distances.min(axis=1).mean())}


def radial_distribution(centers, box, edges):
    """Periodic COM g(r); finite-N ideal-gas normalization, one frame."""
    n = len(centers)
    delta = minimum_image(centers[:, None, :] - centers[None, :, :], box)
    distances = np.linalg.norm(delta, axis=2)[np.triu_indices(n, 1)]
    counts, _ = np.histogram(distances, edges)
    shells = 4*np.pi/3 * np.diff(edges**3)
    return counts / (n*(n-1)/2 * shells / np.prod(box))


def fluctuation_diagnostics(rows, temperature, pressure, count, ensemble):
    """Exploratory molar responses, using OpenMM system molar energy units."""
    r = .008314462618  # kJ mol^-1 K^-1
    pv = .602214076  # kPa nm^3 -> J/mol of simulation boxes
    energy = np.array([row["total_kJ_mol_system"] for row in rows])
    volume = np.array([row["volume_nm3"] for row in rows])
    result = {"cv_fluct_J_mol_K": "", "cp_fluct_J_mol_K": "",
              "compressibility_fluct_kPa_inv": "", "expansion_fluct_K_inv": ""}
    if ensemble == "npt":
        enthalpy = energy + pressure * volume * pv / 1000
        result["cp_fluct_J_mol_K"] = float(np.var(enthalpy, ddof=1) / (r*temperature**2*count) * 1000)
        result["compressibility_fluct_kPa_inv"] = float(np.var(volume, ddof=1) * pv / (volume.mean()*r*1000*temperature))
        result["expansion_fluct_K_inv"] = float(np.cov(volume, enthalpy, ddof=1)[0, 1] / (volume.mean()*r*temperature**2))
    else:
        result["cv_fluct_J_mol_K"] = float(np.var(energy, ddof=1) / (r*temperature**2*count) * 1000)
    return result