"""Scientific and compatibility regressions for the interaction explorer."""
from dataclasses import replace
import unittest

import numpy as np
import openmm as mm
from openmm import unit

from phase_lab.engine import Config, observe
from phase_lab.metrics import local_structure, molecular_coordinates, fluctuation_diagnostics, radial_distribution
from phase_lab.model import MOLECULES, POTENTIALS, build_simulation, fcc_state
from phase_lab.references import density_reference, empirical_comparison
from phase_lab.visuals import smooth_grid


class ExtensionTests(unittest.TestCase):
    def test_reference_density_and_local_fcc_q6(self):
        for molecule in MOLECULES.values():
            rho = density_reference(molecule.name)["value_g_cm3"]
            positions, length = fcc_state(molecule, 2, 1, "random", rho)
            self.assertAlmostEqual(32*molecule.mass_da*.00166053906660/length**3, rho)
            centers, _, _ = molecular_coordinates(positions, np.zeros_like(positions), np.full(3, length))
            self.assertAlmostEqual(local_structure(centers, np.full(3, length))["local_q6"], .5745242597140697)
        rotation, _ = np.linalg.qr(np.random.default_rng(1).normal(size=(3, 3)))
        original = local_structure(centers, np.full(3, length), False)["local_q6"]
        self.assertAlmostEqual(original, local_structure(centers @ rotation, np.full(3, length), False)["local_q6"])

    def test_invalid_physical_combinations(self):
        for config in [Config(boundary="walls"), Config(potentials=("coulomb",)), Config(potentials=()),
                       Config(sigma_scale=0), Config(density_g_cm3=-1), Config(epsilon_scale=float("nan"))]:
            with self.subTest(config=config), self.assertRaises(ValueError):
                config.validate()

    def test_all_potentials_and_boundaries(self):
        base = Config(molecules=("dmso",), temperatures=(300.,), ensemble="nvt", threads=1,
                      equilibration=0, production=20, stride=5, timestep_fs=.5)
        energies = []
        for boundary in ("periodic", "walls"):
            for potential in POTENTIALS:
                config = replace(base, boundary=boundary, potentials=(potential,))
                config.validate()
                simulation, info = build_simulation(MOLECULES["dmso"], config, 101.325, 33)
                nonbonded = next(f for f in simulation.system.getForces() if isinstance(f, mm.NonbondedForce))
                charge = nonbonded.getParticleParameters(0)[0].value_in_unit(unit.elementary_charge)
                self.assertEqual(charge != 0, potential.startswith("coulomb_"))
                self.assertFalse(any(isinstance(f, mm.MonteCarloBarostat) for f in simulation.system.getForces()))
                simulation.step(20)
                row, *_ = observe(simulation, MOLECULES["dmso"], config, None, None, np.zeros((32, 3)))
                self.assertAlmostEqual(row["density_g_cm3"], 1.100)
                self.assertTrue(all(np.isfinite(v) for v in row.values()))
                self.assertAlmostEqual(row["potential_kJ_mol_molecule"], row["wall_kJ_mol_molecule"] + row["intermolecular_kJ_mol_molecule"])
                if boundary == "walls":
                    positions, length = fcc_state(MOLECULES["dmso"], 2, 1, "random", 1.1)
                    positions[0] = [.1, length/2, length/2]
                    simulation.context.setPositions(positions * unit.nanometer)
                    f = simulation.context.getState(getForces=True, groups={2}).getForces(asNumpy=True).value_in_unit(unit.kilojoule_per_mole/unit.nanometer)
                    self.assertGreater(f[0, 0], 0)  # inward from low-x wall
                    self.assertEqual(info["degrees_of_freedom"], 160)
                energies.append(row["potential_kJ_mol_molecule"])
                del simulation
        self.assertEqual(len(set(round(e, 4) for e in energies)), 8)

    def test_empirical_unavailable_is_not_zero(self):
        ref = empirical_comparison("dmso", 1600, 1000)
        self.assertIsNone(ref["potential_kJ_mol"])
        self.assertFalse(ref["matched_vaporization_TP"])
        self.assertEqual(ref["vaporization"]["temperature_K"], 320)
        self.assertIsNone(empirical_comparison("glycerol", 300, 101.325)["vaporization"])
        # PubChem only gives propylene glycol's latent heat "at BP" in the
        # verified entry; do not attach an invented 298.15 K temperature to it.
        self.assertIsNone(empirical_comparison("propylene_glycol", 300, 101.325)["vaporization"])

    def test_fluctuation_ensemble_and_units(self):
        rows = [{"total_kJ_mol_system": e, "volume_nm3": v} for e, v in [(1, 1), (3, 3)]]
        npt = fluctuation_diagnostics(rows, 300, 100, 32, "npt")
        self.assertEqual(npt["cv_fluct_J_mol_K"], "")
        self.assertAlmostEqual(npt["compressibility_fluct_kPa_inv"], .602214076/(8.314462618*300))
        nvt = fluctuation_diagnostics(rows, 300, 100, 32, "nvt")
        self.assertEqual(nvt["cp_fluct_J_mol_K"], "")
        self.assertAlmostEqual(nvt["cv_fluct_J_mol_K"], 2/(.008314462618*300**2*32)*1000)

    def test_rdf_ideal_gas_normalization(self):
        rng = np.random.default_rng(51)
        edges = np.linspace(.2, .5, 5)
        gr = np.mean([radial_distribution(rng.random((150, 3)), np.ones(3), edges) for _ in range(20)], axis=0)
        np.testing.assert_allclose(gr, np.ones(4), atol=.04)

    def test_smoothing_preserves_nodes_and_missing_data(self):
        rows = [{"temperature_K": str(t), "pressure_kPa": str(p), "q": str(v)}
                for t, p, v in [(100, 10, 0), (300, 10, 1), (100, 1000, .4), (300, 1000, .8)]]
        grid = smooth_grid(rows, "q", 9)
        self.assertEqual(len(grid["samples"]), 4)
        np.testing.assert_allclose(np.array(grid["z"])[[0, -1]][:, [0, -1]], [[0, 1], [.4, .8]])
        self.assertGreaterEqual(np.min(grid["z"]), 0)
        self.assertLessEqual(np.max(grid["z"]), 1)
        self.assertIsNone(smooth_grid(rows[:-1], "q"))
        self.assertIsNone(smooth_grid(rows, "missing_legacy_column"))