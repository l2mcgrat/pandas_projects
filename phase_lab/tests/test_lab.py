import ast
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

import numpy as np
import openmm as mm
from openmm import unit

from phase_lab.engine import Config, read_csv, run_sweep
from phase_lab.metrics import (angular_histogram, crystal_order, minimum_image,
                               molecular_coordinates, orientation_metrics)
from phase_lab.model import MOLECULES, build_simulation, fcc_state
from phase_lab.publishing import physics_landing_page, publish_available_runs, publish_run
from phase_lab.visuals import render_run


class MetricsTests(unittest.TestCase):
    def test_aligned_dipoles(self):
        values = orientation_metrics(np.tile([0., 0., 1.], (32, 1)))
        for key in ("polar_order", "nematic_order", "multipolar_order", "a4_squared"):
            self.assertAlmostEqual(values[key], 1)

    def test_multimodal_axes_not_mistaken_for_isotropic(self):
        axes = np.tile(np.concatenate([np.eye(3), -np.eye(3)]), (16, 1))
        values = orientation_metrics(axes)
        self.assertAlmostEqual(values["polar_order"], 0)
        self.assertAlmostEqual(values["nematic_order"], 0)
        self.assertGreater(values["a4_squared"], .55)
        self.assertGreater(values["multipolar_order"], .3)

    def test_isotropic_and_rotation_invariance(self):
        rng = np.random.default_rng(42)
        axes = rng.normal(size=(800, 3))
        axes /= np.linalg.norm(axes, axis=1)[:, None]
        values = orientation_metrics(axes)
        self.assertLess(values["multipolar_order"], .05)
        rotation, _ = np.linalg.qr(rng.normal(size=(3, 3)))
        rotated = orientation_metrics(axes @ rotation)
        for key in values:
            self.assertAlmostEqual(values[key], rotated[key], places=10)

    def test_equal_area_histogram_and_poles(self):
        z = np.repeat(np.linspace(-.95, .95, 10), 16)
        phi = np.tile(np.linspace(-np.pi + np.pi / 16, np.pi - np.pi / 16, 16), 10)
        axes = np.column_stack([np.sqrt(1-z*z)*np.cos(phi), np.sqrt(1-z*z)*np.sin(phi), z])
        hist, _, _ = angular_histogram(axes)
        np.testing.assert_array_equal(hist, np.ones((10, 16)))
        hist, _, _ = angular_histogram(np.array([[0, 0, 1], [0, 0, -1]]))
        self.assertEqual(hist.sum(), 2)

    def test_periodic_dipole_and_fcc(self):
        positions = np.array([[1.98, 1, 1], [.02, 1, 1]])
        centers, axes, _ = molecular_coordinates(positions, np.zeros_like(positions), np.array([2., 2., 2.]))
        np.testing.assert_allclose(centers, [[0., 1., 1.]], atol=1e-10)
        np.testing.assert_allclose(axes, [[1., 0., 0.]])
        np.testing.assert_allclose(minimum_image(np.array([1.95, 0, 0]), np.full(3, 2)), [-.05, 0, 0])
        positions, box = fcc_state(MOLECULES["glycerol"], 2, 1, "multiaxis")
        centers, _, _ = molecular_coordinates(positions, np.zeros_like(positions), np.full(3, box))
        self.assertAlmostEqual(crystal_order(centers, np.full(3, box), 2), 1)
        self.assertAlmostEqual(crystal_order(centers + .123, np.full(3, box), 2), 1)

    def test_invalid_config(self):
        for config in [Config(temperatures=(float("nan"),)), Config(pressures=(0.,)),
                       Config(cells=1), Config(ensemble="nvt", pressures=(1., 2.)),
                       Config(production=52), Config(stride=0), Config(timestep_fs=4),
                       Config(temperatures=(300., 300.))]:
            with self.subTest(config=config), self.assertRaises(ValueError):
                config.validate()


class SimulationTests(unittest.TestCase):
    def test_model_charge_constraints_and_pressure_units(self):
        config = Config(molecules=("dmso",), temperatures=(180.,), threads=1)
        simulation, info = build_simulation(MOLECULES["dmso"], config, 101.325, 3)
        self.assertEqual(simulation.system.getNumParticles(), 64)
        self.assertEqual(simulation.system.getNumConstraints(), 32)
        force = next(f for f in simulation.system.getForces() if isinstance(f, mm.NonbondedForce))
        charge = sum(force.getParticleParameters(i)[0].value_in_unit(unit.elementary_charge) for i in range(64))
        self.assertAlmostEqual(charge, 0)
        self.assertAlmostEqual(simulation.context.getParameter(mm.MonteCarloBarostat.Pressure()), 1.01325)
        simulation.step(5)
        state = simulation.context.getState(getPositions=True, getEnergy=True)
        p = state.getPositions(asNumpy=True).value_in_unit(unit.nanometer)
        self.assertTrue(np.isfinite(p).all())
        self.assertEqual(info["degrees_of_freedom"], 157)
        del simulation

    def test_end_to_end_csv_plots_publish(self):
        with tempfile.TemporaryDirectory() as temp, contextlib.redirect_stdout(io.StringIO()):
            root = Path(temp)
            config = Config(molecules=("glycerol",), temperatures=(180., 250.), pressures=(10., 101.325),
                            equilibration=5, production=20, stride=5, threads=1)
            records = run_sweep(config, root, "test")
            summary = read_csv(records / "summary.csv")
            self.assertEqual(len(summary), 4)
            metadata = json.loads((records / "metadata.json").read_text())
            self.assertEqual(metadata["status"], "complete")
            for row in summary:
                folder = records / row["condition"]
                trajectory = read_csv(folder / "trajectory.csv")
                self.assertEqual(len(trajectory), 32 * 4)
                first = trajectory[0]
                self.assertAlmostEqual(sum(float(first[f"dipole_u{k}"]) ** 2 for k in "xyz"), 1, places=6)
                hist = read_csv(folder / "orientation_histogram.csv")
                self.assertAlmostEqual(sum(float(bin_["probability"]) for bin_ in hist), 1)
            with self.assertRaises(FileExistsError):
                run_sweep(config, root, "test")
            render_run(root, "test")
            reports = root / "reports" / "phase_simulations" / "test"
            self.assertTrue((reports / "glycerol_surface.png").exists())
            self.assertTrue((reports / "dipole_atlas.pdf").read_bytes().startswith(b"%PDF"))
            publish_run(root, "test", root / "site")
            published = root / "site" / "Physics" / "Dipole-Atlas" / "test"
            page = (published / "index.html").read_text(encoding="utf-8")
            self.assertNotIn("@@", page)
            self.assertIn('href="figures/dipole_atlas.pdf"', page)
            stable = (published.parent / "index.html").read_text(encoding="utf-8")
            self.assertIn('<base href="test/">', stable)
            self.assertTrue((published / "theory.pdf").read_bytes().startswith(b"%PDF"))
            theory = (published / "theory.html").read_text(encoding="utf-8")
            self.assertIn('id="empirical"', theory)
            self.assertIn("<svg", theory)
            self.assertTrue((published / "theory.tex").exists())
            self.assertTrue((published / "render_metadata.json").exists())
            with zipfile.ZipFile(published / "records.zip") as archive:
                self.assertIn("summary.csv", archive.namelist())
            # Existing custom Physics content must survive local publication.
            landing = root / "site" / "Physics" / "index.html"
            landing.write_text("<html><body><h1>Keep my physics</h1></body></html>", encoding="utf-8")
            publish_run(root, "test", root / "site")
            self.assertIn("Keep my physics", landing.read_text())
            # Normal website builds discover completed rendered runs without running MD.
            publish_available_runs(root, root / "build")
            self.assertTrue((root / "build" / "Physics" / "Dipole-Atlas" / "test" / "records.zip").exists())
            generator = Path(__file__).resolve().parents[2] / "generate_liamms_site.py"
            tree = ast.parse(generator.read_text(encoding="utf-8"))
            category = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "category_page")
            namespace = {"physics_landing_page": physics_landing_page, "SITE_DIR": root / "build"}
            exec(compile(ast.Module(body=[category], type_ignores=[]), str(generator), "exec"), namespace)
            self.assertIn("Dipole-Atlas/test/index.html", namespace["category_page"]("Physics"))
            self.assertIn("Dipole-Atlas/index.html", namespace["category_page"]("Physics"))

    def test_nvt_no_pressure_and_temperature_only_plot(self):
        with tempfile.TemporaryDirectory() as temp, contextlib.redirect_stdout(io.StringIO()):
            root = Path(temp)
            config = Config(molecules=("dmso",), temperatures=(200.,), ensemble="nvt",
                            equilibration=2, production=20, stride=5, threads=1)
            records = run_sweep(config, root, "test_nvt")
            row = read_csv(records / "summary.csv")[0]
            self.assertEqual(row["pressure_kPa"], "")
            thermo = read_csv(records / row["condition"] / "thermodynamics.csv")
            self.assertEqual(len({sample["volume_nm3"] for sample in thermo}), 1)
            render_run(root, "test_nvt")
            self.assertFalse(list((root / "reports").rglob("*_surface.png")))


if __name__ == "__main__":
    unittest.main()