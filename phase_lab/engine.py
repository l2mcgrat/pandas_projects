"""Stream production trajectories; never retain an entire MD trajectory in RAM."""

import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
from itertools import product
import json
from pathlib import Path
import platform

import numpy as np
import openmm as mm
from openmm import unit

from .metrics import (angular_histogram, block_standard_error, crystal_order,
                      minimum_image, molecular_coordinates, orientation_metrics,
                      local_structure, radial_distribution, fluctuation_diagnostics)
from .model import MODEL_NOTICE, MOLECULES, POTENTIALS, build_simulation
from .references import REFERENCE_VERSION


@dataclass
class Config:
    molecules: tuple[str, ...] = ("glycerol", "ethylene_glycol", "dmso")
    temperatures: tuple[float, ...] = (180., 300., 500., 800.)
    pressures: tuple[float, ...] = (101.325,)
    ensemble: str = "npt"
    cells: int = 2
    equilibration: int = 500
    production: int = 1500
    stride: int = 50
    timestep_fs: float = 1.
    seed: int = 20260925
    platform: str = "CPU"
    threads: int = 2
    orientation: str = "multiaxis"
    potentials: tuple[str, ...] = ("coulomb_lj",)
    boundary: str = "periodic"
    density_mode: str = "reference"
    density_g_cm3: float | None = None
    sigma_scale: float = 1.
    epsilon_scale: float = 1.
    cutoff_sigma: float = 2.
    wall_epsilon: float = 5.

    def validate(self):
        if not self.potentials or len(set(self.potentials)) != len(self.potentials) or any(p not in POTENTIALS for p in self.potentials):
            raise ValueError("Select unique supported potentials; bare attractive Coulomb is not stable.")
        if self.boundary not in ("periodic", "walls") or self.density_mode not in ("reference", "legacy"):
            raise ValueError("Unknown boundary or density mode.")
        if self.boundary == "walls" and self.ensemble != "nvt":
            raise ValueError("Stationary LJ walls require NVT; they do not impose a pressure.")
        for value in (self.sigma_scale, self.epsilon_scale, self.cutoff_sigma, self.wall_epsilon):
            if not np.isfinite(value) or value <= 0:
                raise ValueError("Interaction scales must be finite and positive.")
        if self.density_g_cm3 is not None:
            if not np.isfinite(self.density_g_cm3) or self.density_g_cm3 <= 0 or self.density_mode != "reference":
                raise ValueError("Density override must be positive and use reference density mode.")
        for label, values in (("temperatures", self.temperatures), ("pressures", self.pressures)):
            if not values or any(not np.isfinite(x) or x <= 0 for x in values):
                raise ValueError(f"{label} must contain finite, positive numbers.")
            if len(set(values)) != len(values):
                raise ValueError(f"Duplicate {label} are not supported in one sweep.")
        if not self.molecules or any(name not in MOLECULES for name in self.molecules):
            raise ValueError("Select at least one known molecule preset.")
        if len(set(self.molecules)) != len(self.molecules):
            raise ValueError("Duplicate molecules are not supported.")
        if self.ensemble not in ("nvt", "npt"):
            raise ValueError("Ensemble must be nvt or npt.")
        if self.ensemble == "nvt" and len(self.pressures) != 1:
            raise ValueError("A pressure sweep needs NPT; NVT does not control pressure.")
        if self.cells < 2 or self.threads < 1 or self.equilibration < 0:
            raise ValueError("Use cells >= 2, threads >= 1, equilibration >= 0.")
        if self.stride < 1 or self.production < 4 * self.stride:
            raise ValueError("Production must contain at least four reporting intervals.")
        if self.production % self.stride:
            raise ValueError("Production steps must be divisible by stride.")
        if not np.isfinite(self.timestep_fs) or not 0 < self.timestep_fs <= 2:
            raise ValueError("Use a finite timestep in (0, 2] femtoseconds.")
        if not 1 <= self.seed <= 2_000_000_000:
            raise ValueError("Seed must be in [1, 2000000000].")
        if self.orientation not in ("multiaxis", "random"):
            raise ValueError("Unknown initial orientation.")


def write_csv(path, rows):
    if not rows:
        return
    with Path(path).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def save_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def observe(simulation, molecule, config, box_previous, fraction_previous, displacement):
    state = simulation.context.getState(getPositions=True, getVelocities=True, getEnergy=True)
    positions = np.asarray(state.getPositions(asNumpy=True).value_in_unit(unit.nanometer))
    velocities = np.asarray(state.getVelocities(asNumpy=True).value_in_unit(unit.nanometer / unit.picosecond))
    box = np.diag(np.asarray(state.getPeriodicBoxVectors(asNumpy=True).value_in_unit(unit.nanometer)))
    if not np.isfinite(positions).all() or not np.isfinite(box).all():
        raise RuntimeError("Non-finite state. Reduce timestep and inspect interaction scales.")
    periodic = config.boundary == "periodic"
    if not periodic and (np.any(positions <= 0) or np.any(positions >= box)):
        raise RuntimeError("A site crossed a repulsive wall. Reduce timestep; do not interpret this run.")
    centers, axes, com_velocity = molecular_coordinates(positions, velocities, box, periodic)
    fraction = centers / box
    if fraction_previous is not None:
        delta = fraction - fraction_previous
        if periodic:
            delta = minimum_image(delta, np.ones(3))
        displacement += delta * (box + box_previous) / 2
    count = len(centers)
    pe = state.getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole)
    ke = state.getKineticEnergy().value_in_unit(unit.kilojoule_per_mole)
    values = {
        "step": simulation.currentStep,
        "time_ps": state.getTime().value_in_unit(unit.picosecond),
        "measured_temperature_K": 2 * ke / ((5 * count - (3 if periodic else 0)) * 0.008314462618),
        "potential_kJ_mol_system": pe, "kinetic_kJ_mol_system": ke,
        "total_kJ_mol_system": pe + ke,
        "potential_kJ_mol_molecule": pe / count,
        "box_nm": float(box[0]), "volume_nm3": float(np.prod(box)),
        "density_g_cm3": float(count * molecule.mass_da * .00166053906660 / np.prod(box)),
        "msd_nonaffine_nm2": float(np.mean(np.sum(displacement ** 2, axis=1))),
        "fcc_order": crystal_order(centers, box, config.cells),
        **orientation_metrics(axes),
        **local_structure(centers, box, periodic),
    }
    wall_energy = simulation.context.getState(getEnergy=True, groups={2}).getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole) if not periodic else 0.
    values["wall_kJ_mol_molecule"] = wall_energy / count
    values["intermolecular_kJ_mol_molecule"] = (pe - wall_energy) / count
    if not all(np.isfinite(value) for value in values.values()):
        raise RuntimeError("Non-finite energy/metric. Run failed; do not interpret partial results.")
    return values, centers, axes, com_velocity, fraction, box


def run_sweep(config: Config, root: Path, run_id: str):
    config.validate()
    destination = root / "records" / "phase_simulations" / run_id
    destination.mkdir(parents=True, exist_ok=False)
    source_files = [Path(__file__).resolve().parents[1] / "simulations.py", *sorted(Path(__file__).parent.glob("*.py")),
                    *sorted((Path(__file__).parent / "docs").glob("*.*"))]
    metadata = {
        "run_id": run_id, "status": "running", "created_utc": datetime.now(timezone.utc).isoformat(),
        "notice": MODEL_NOTICE, "config": asdict(config),
        "schema_version": 2, "reference_version": REFERENCE_VERSION,
        "versions": {"python": platform.python_version(), "numpy": np.__version__, "openmm": mm.__version__},
        "parameters": [MOLECULES[name].parameters() for name in config.molecules],
        "source_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files},
        "protocol": "Independent ordered FCC start per pressure/preset; sequential temperature plateaus in supplied order. Production-only sampling; per-plateau MSD resets after equilibration.",
        "conditions": [],
    }
    save_json(destination / "metadata.json", metadata)
    summary = []
    try:
        for mi, name in enumerate(config.molecules):
            molecule = MOLECULES[name]
            for (pi, pressure), potential in product(enumerate(config.pressures), config.potentials):
                seed = config.seed + mi * 1000 + pi
                simulation, model_info = build_simulation(molecule, config, pressure, seed, potential)
                try:
                    for ti, temperature in enumerate(config.temperatures):
                        condition = f"{name}_{potential}_p{pi:02d}_t{ti:02d}"
                        folder = destination / condition
                        folder.mkdir()
                        print(f"  {condition}: {temperature:g} K, " +
                              (f"{pressure:g} kPa" if config.ensemble == "npt" else "fixed volume"), flush=True)
                        simulation.integrator.setTemperature(temperature * unit.kelvin)
                        if config.ensemble == "npt":
                            simulation.context.setParameter(mm.MonteCarloBarostat.Temperature(), temperature)
                        simulation.step(config.equilibration)
                        displacement = np.zeros((model_info["molecule_count"], 3))
                        baseline = observe(simulation, molecule, config, None, None, displacement)
                        fraction_previous, box_previous = baseline[-2:]
                        rows, histogram, rdf_rows = [], np.zeros((10, 16)), []
                        with (folder / "trajectory.csv").open("w", newline="", encoding="utf-8") as stream:
                            writer = csv.writer(stream)
                            writer.writerow(["frame", "step", "time_ps", "molecule_id", "box_nm",
                                             "x_nm", "y_nm", "z_nm", "dx_nonaffine_nm", "dy_nonaffine_nm", "dz_nonaffine_nm",
                                             "vx_nm_ps", "vy_nm_ps", "vz_nm_ps", "dipole_ux", "dipole_uy", "dipole_uz",
                                             "theta_rad", "phi_rad", "dipole_debye"])
                            for frame in range(config.production // config.stride):
                                simulation.step(config.stride)
                                row, centers, axes, velocity, fraction_previous, box_previous = observe(
                                    simulation, molecule, config, box_previous, fraction_previous, displacement)
                                row["frame"] = frame
                                dots = np.clip(np.sum(axes * baseline[2], axis=1), -1, 1)
                                row["rotation_c2"] = float(np.mean((3*dots*dots-1)/2))
                                rows.append(row)
                                if config.boundary == "periodic":
                                    edges = np.linspace(0, float(box_previous.min()) / 2, 33)
                                    gr = radial_distribution(centers, box_previous, edges)
                                    rdf_rows.extend({"frame": frame, "r_lower_nm": edges[j], "r_upper_nm": edges[j+1],
                                                     "g_r": value} for j, value in enumerate(gr))
                                counts, cost_edges, phi_edges = angular_histogram(axes)
                                histogram += counts
                                theta = np.arccos(np.clip(axes[:, 2], -1, 1))
                                phi = np.arctan2(axes[:, 1], axes[:, 0])
                                for index in range(len(centers)):
                                    values = [*centers[index], *displacement[index], *velocity[index], *axes[index],
                                              theta[index], phi[index], molecule.dipole_debye if potential.startswith("coulomb_") else 0.]
                                    writer.writerow([frame, row["step"], f'{row["time_ps"]:.6f}', index,
                                                     f'{row["box_nm"]:.8g}', *[f"{v:.8g}" for v in values]])
                        write_csv(folder / "thermodynamics.csv", rows)
                        write_csv(folder / "radial_distribution.csv", rdf_rows)
                        probabilities = histogram / histogram.sum()
                        populated = probabilities > 0
                        kl = float(np.sum(probabilities[populated] * np.log(probabilities[populated] * probabilities.size)))
                        angular_rows = [
                            {"cos_theta_lower": cost_edges[i], "cos_theta_upper": cost_edges[i + 1],
                             "phi_lower_rad": phi_edges[j], "phi_upper_rad": phi_edges[j + 1],
                             "count": int(histogram[i, j]), "probability": probabilities[i, j],
                             "relative_to_isotropic": probabilities[i, j] * probabilities.size}
                            for i in range(10) for j in range(16)
                        ]
                        write_csv(folder / "orientation_histogram.csv", angular_rows)
                        record = {"condition": condition, "molecule": name, "label": molecule.label,
                                  "potential": potential, "boundary": config.boundary,
                                  "density_mode": config.density_mode,
                                  "initial_density_g_cm3": model_info["initial_density_g_cm3"],
                                  "ensemble": config.ensemble, "temperature_K": temperature,
                                  "pressure_kPa": pressure if config.ensemble == "npt" else "",
                                  "molecules": model_info["molecule_count"], "frames": len(rows),
                                  "production_ps": config.production * config.timestep_fs / 1000,
                                  "angular_kl_nats": kl, "msd_final_nm2": rows[-1]["msd_nonaffine_nm2"]}
                        for key in ("measured_temperature_K", "potential_kJ_mol_molecule", "density_g_cm3",
                                    "fcc_order", "polar_order", "nematic_order", "multipolar_order",
                                    "local_q6", "nearest_neighbor_nm", "rotation_c2",
                                    "wall_kJ_mol_molecule", "intermolecular_kJ_mol_molecule",
                                    *[f"a{degree}_squared" for degree in range(1, 7)]):
                            values = [row[key] for row in rows]
                            record[key] = float(np.mean(values))
                            record[f"{key}_block_se"] = block_standard_error(values)
                        tail = rows[len(rows)//2:]
                        slope = np.polyfit([r["time_ps"] for r in tail], [r["msd_nonaffine_nm2"] for r in tail], 1)[0]
                        record["msd_slope_proxy_nm2_ps"] = float(slope / 6)
                        record.update(fluctuation_diagnostics(rows, temperature, pressure, model_info["molecule_count"], config.ensemble))
                        summary.append(record)
                        metadata["conditions"].append({"condition": condition, **model_info})
                        write_csv(destination / "summary.csv", summary)
                        save_json(destination / "metadata.json", metadata)
                finally:
                    del simulation
        metadata["status"] = "complete"
    except BaseException as exc:
        metadata["status"] = "failed"
        metadata["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        save_json(destination / "metadata.json", metadata)
    return destination