"""Two-site polar Lennard-Jones surrogates, NOT chemical force fields."""

from dataclasses import asdict, dataclass

import numpy as np
import openmm as mm
from openmm import app, unit

from .references import density_reference

POTENTIALS = {"coulomb_lj": "Partial-charge Coulomb + LJ", "lj": "Lennard–Jones only",
              "coulomb_wca": "Partial-charge Coulomb + WCA", "wca": "WCA repulsion only"}


@dataclass(frozen=True)
class Molecule:
    name: str
    label: str
    mass_da: float
    dipole_debye: float
    sigma_nm: float
    epsilon_kj_mol: float

    @property
    def bond_nm(self) -> float:
        return 0.25 * self.sigma_nm

    @property
    def charge_e(self) -> float:
        # 1 Debye = 0.020819434 e nm; the axis points from -q to +q.
        return self.dipole_debye * 0.020819434 / self.bond_nm

    def parameters(self) -> dict:
        return {**asdict(self), "bond_nm": self.bond_nm, "charge_e": self.charge_e}


# Masses/dipoles are approximate molecular scales, not validated force-field data.
# Sigma/epsilon are explicitly illustrative (not fitted to melting/vapour data).
MOLECULES = {
    "glycerol": Molecule("glycerol", "Glycerol-inspired", 92.094, 2.6, 0.48, 6.0),
    "ethylene_glycol": Molecule("ethylene_glycol", "Ethylene glycol-inspired", 62.068, 2.3, 0.43, 4.5),
    "dmso": Molecule("dmso", "DMSO-inspired", 78.133, 3.96, 0.46, 5.0),
    "propylene_glycol": Molecule("propylene_glycol", "Propylene glycol-inspired", 76.095, 2.3, .46, 5.),
    "formamide": Molecule("formamide", "Formamide-inspired", 45.041, 3.73, .36, 4.5),
    "benzyl_alcohol": Molecule("benzyl_alcohol", "Benzyl alcohol-inspired", 108.14, 1.7, .50, 5.5),
}

MODEL_NOTICE = (
    "Qualitative two-site polar Lennard-Jones surrogates, not atomistic models of the named "
    "chemicals. Interaction scales are illustrative; hydrogen bonds, molecular flexibility, "
    "chemical reactions and decomposition are absent. Short finite-box heating/cooling "
    "runs do not establish melting points, boiling points, vapour pressures or phase boundaries. "
    "High-temperature results are model behavior, not predictions for stable real molecules."
)


def fcc_state(molecule: Molecule, cells: int, seed: int, orientation: str, density=None):
    """Ordered FCC centers, with either six narrow dipole populations or random axes."""
    basis = np.array([[0, 0, 0], [0, .5, .5], [.5, 0, .5], [.5, .5, 0]])
    lattice = np.sqrt(2) * 1.35 * molecule.sigma_nm
    if density is not None:
        lattice = (4 * molecule.mass_da * .00166053906660 / density) ** (1 / 3)
    centers = np.array([
        (np.array([i, j, k]) + b + .25) * lattice
        for i in range(cells) for j in range(cells) for k in range(cells) for b in basis
    ])
    if orientation == "random":
        axes = np.random.default_rng(seed).normal(size=centers.shape)
        axes /= np.linalg.norm(axes, axis=1)[:, None]
    else:
        directions = np.concatenate([np.eye(3), -np.eye(3)])
        axes = directions[np.arange(len(centers)) % 6]
    positions = np.stack([centers - axes * molecule.bond_nm / 2,
                          centers + axes * molecule.bond_nm / 2], axis=1)
    return positions.reshape(-1, 3), cells * lattice


def build_simulation(molecule: Molecule, config, pressure_kpa: float, seed: int, potential=None):
    """Explicit site forces provide both net translation and constrained rotation."""
    potential = potential or config.potentials[0]
    periodic = config.boundary == "periodic"
    charged = potential.startswith("coulomb_")
    wca = potential.endswith("wca")
    reference = density_reference(molecule.name)
    density = (config.density_g_cm3 or reference["value_g_cm3"]) if config.density_mode == "reference" else None
    positions, length = fcc_state(molecule, config.cells, seed, config.orientation, density)
    count = len(positions) // 2
    system = mm.System()
    topology = app.Topology()
    chain = topology.addChain()
    vectors = tuple(mm.Vec3(*v) * unit.nanometer for v in np.eye(3) * length)
    system.setDefaultPeriodicBoxVectors(*vectors)
    if periodic:
        topology.setPeriodicBoxVectors(vectors)
    force = mm.NonbondedForce()
    force.setNonbondedMethod(mm.NonbondedForce.PME if periodic else mm.NonbondedForce.NoCutoff)
    sigma = molecule.sigma_nm * config.sigma_scale
    epsilon = molecule.epsilon_kj_mol * config.epsilon_scale / 4
    cutoff = min(config.cutoff_sigma * sigma, 0.36 * length)
    force.setCutoffDistance(cutoff * unit.nanometer)
    force.setUseSwitchingFunction(periodic)
    force.setSwitchingDistance(0.85 * cutoff * unit.nanometer)
    force.setUseDispersionCorrection(periodic and not wca)
    force.setEwaldErrorTolerance(5e-4)
    repulsion = None
    if wca:
        repulsion = mm.CustomNonbondedForce("step(rc-r)*(4*eps*((sig/r)^12-(sig/r)^6)+eps)")
        for key, value in (("eps", epsilon), ("sig", sigma), ("rc", 2 ** (1/6) * sigma)):
            repulsion.addGlobalParameter(key, value)
        repulsion.setNonbondedMethod(mm.CustomNonbondedForce.CutoffPeriodic if periodic else mm.CustomNonbondedForce.NoCutoff)
        # Use the same neighbor-list cutoff as PME; never truncate the WCA core.
        if periodic and cutoff < 2 ** (1/6) * sigma:
            raise ValueError("Box/cutoff too small for WCA; increase cells or cutoff-sigma.")
        repulsion.setCutoffDistance(cutoff)
        repulsion.setForceGroup(1)
    for index in range(count):
        residue = topology.addResidue("DIP", chain)
        atoms = [topology.addAtom(name, None, residue) for name in ("NEG", "POS")]
        topology.addBond(*atoms)
        for sign in (-1, 1):
            system.addParticle(molecule.mass_da / 2)
            # Four site-site LJ pairs recover epsilon approximately at r >> bond.
            force.addParticle(sign * molecule.charge_e if charged else 0, sigma,
                              0 if wca else epsilon)
            if repulsion is not None:
                repulsion.addParticle([])
        system.addConstraint(2 * index, 2 * index + 1, molecule.bond_nm)
        force.addException(2 * index, 2 * index + 1, 0, 1, 0)
        if repulsion is not None:
            repulsion.addExclusion(2 * index, 2 * index + 1)
    system.addForce(force)
    if repulsion is not None:
        system.addForce(repulsion)
    if periodic:
        system.addForce(mm.CMMotionRemover())
    else:
        # Six shifted/truncated repulsive LJ planes, not a periodic image force.
        terms = [f"step(rc-({d}))*(4*ew*((sw/({d}))^12-(sw/({d}))^6)+ew)"
                 for d in ("x", "L-x", "y", "L-y", "z", "L-z")]
        walls = mm.CustomExternalForce("+".join(terms))
        for key, value in (("L", length), ("sw", sigma * .25), ("ew", config.wall_epsilon),
                           ("rc", 2 ** (1/6) * sigma * .25)):
            # Avoid a global parameter collision with the pair WCA cutoff.
            walls.addGlobalParameter("wall_" + key, value)
        expression = "+".join(terms)
        import re
        walls.setEnergyFunction(re.sub(r"\b(L|sw|ew|rc)\b", r"wall_\1", expression))
        walls.setForceGroup(2)
        for index in range(2 * count):
            walls.addParticle(index, [])
        system.addForce(walls)
    if config.ensemble == "npt":
        barostat = mm.MonteCarloBarostat(pressure_kpa / 100 * unit.bar,
                                       config.temperatures[0] * unit.kelvin, 25)
        barostat.setRandomNumberSeed(seed)
        system.addForce(barostat)
    integrator = mm.LangevinMiddleIntegrator(config.temperatures[0] * unit.kelvin,
                                            1 / unit.picosecond,
                                            config.timestep_fs * unit.femtosecond)
    integrator.setConstraintTolerance(1e-6)
    integrator.setRandomNumberSeed(seed)
    platform = mm.Platform.getPlatformByName(config.platform)
    properties = {"Threads": str(config.threads)} if config.platform == "CPU" else {}
    simulation = app.Simulation(topology, system, integrator, platform, properties)
    simulation.context.setPositions(positions * unit.nanometer)
    simulation.minimizeEnergy(maxIterations=400)
    simulation.context.setVelocitiesToTemperature(config.temperatures[0] * unit.kelvin, seed)
    return simulation, {"molecule_count": count, "initial_box_nm": length,
                        "cutoff_nm": cutoff, "platform": platform.getName(),
                        "seed": seed, "degrees_of_freedom": 5 * count - (3 if periodic else 0),
                        "potential": potential, "boundary": config.boundary,
                        "effective_sigma_nm": sigma, "effective_site_epsilon_kJ_mol": epsilon,
                        "effective_charge_e": molecule.charge_e if charged else 0,
                        "initial_density_g_cm3": count * molecule.mass_da * .00166053906660 / length ** 3,
                        "density_reference": reference}