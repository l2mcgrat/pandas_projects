# Dipole Atlas

A small, reproducible OpenMM laboratory for **qualitative** orientational and
structural changes in polar fluids. Entry point: [simulations.py](../simulations.py).
The old unrelated interstellar calculation and incomplete mixture skeleton were
replaced; this no longer requires Packmol, a PDB, or an external force-field download.

## Start here

Version 2 adds independent molecule/temperature/pressure controls, four real
Hamiltonian choices, nine diagnostic views, charge-site/center displays, and
shareable query URLs. The stable public entry is
[the interaction explorer](http://liammspandasprojects.org/Physics/Dipole-Atlas/index.html).
Archived run URLs remain valid. Smoothing uses PCHIP in temperature and log
pressure; gold points show actual sampled means, not a measured phase boundary.

The full theory manuscript is maintained in [docs/theory.json](docs/theory.json).
Rendering creates offline mathematical HTML, a PDF, LaTeX source and a source
copy for every run, linked from its viewer. See its introduction for the overview,
sections 2–12 for physics/diagnostics, and section 14 for the update checklist.
**Changes to physics or diagnostic definitions must update this document, its
design history and corresponding regression tests before generating new runs.**

The original demonstration below remains an archive of the earlier model setup;
rerendering it never changes its dynamics or fills in unrecorded diagnostics.

Current generated comparisons:
- [Periodic NPT interaction atlas](../media/phase_simulations/interaction_atlas_v2/index.html):
  216 conditions = 6 presets × 4 potentials × 3 temperatures (180/300/600 K) ×
  3 pressures (10/101.325/1000 kPa).
- [Fixed-wall NVT atlas](../media/phase_simulations/wall_atlas_v2/index.html):
  72 conditions with the same presets/potentials/temperatures, at fixed reference
  bulk density; no pressure is controlled.
- [Theory PDF](../reports/phase_simulations/interaction_atlas_v2/theory.pdf) and
  [offline mathematical document](../media/phase_simulations/interaction_atlas_v2/theory.html).

Both v2 runs use 32 molecules, 0.5 fs steps, 0.5 ps equilibration and 2 ps production
per plateau, with 40 saved frames. Together: 368,640 molecule-frame rows.
They are bounded demonstration runs, not equilibrium material measurements.

- [Interactive demonstration](../media/phase_simulations/demo_tp_20260925/index.html)
  — open in a browser, choose a condition, play/scrub frames, drag the molecular box.
- [Figure book](../reports/phase_simulations/demo_tp_20260925/dipole_atlas.pdf)
- [Summary CSV](../records/phase_simulations/demo_tp_20260925/summary.csv)
- [Run metadata](../records/phase_simulations/demo_tp_20260925/metadata.json)

The demonstration contains 45 plateaus: 3 surrogates × 5 temperatures
(180, 300, 600, 1000, 1600 K) × 3 imposed pressures (10, 101.325, 1000 kPa).
Each independent pressure/material path starts with 32 ordered FCC molecular
centers. Each temperature gets 1 ps equilibration and 3 ps production. Only
production is recorded, every 0.05 ps: **86,400 molecule-frame rows** altogether.
It is an integration/visualization demo, not equilibrated material-property data.

## Running (from the repository root, PowerShell)

Use the selected Python environment, which already contains the four dependencies
in [requirements.txt](requirements.txt). For another environment, install that
file with its Python package manager first.

```powershell
# Quick temperature path: all 6 presets at 101.325 kPa, 32 molecules.
py -3.12 simulations.py

# Temperature AND pressure, producing 3D response surfaces as well as 2D curves.
py -3.12 simulations.py --temperatures 180 300 600 1000 --pressures 10 101.325 1000 --run-id my_tp_sweep

# Fixed-volume temperature-only experiment. No imposed/measured pressure is claimed.
py -3.12 simulations.py --ensemble nvt --molecules dmso --temperatures 150 250 350

# Larger/longer path: 108 molecules, 10 ps equilibration + 40 ps production per plateau.
# This is still NOT a guarantee of equilibration. CPU runtime can be substantial.
py -3.12 simulations.py --quality extended --molecules glycerol --temperatures 150 250 350 500 700

# Cooling uses the supplied temperature order. Separate runs allow independent seeds.
py -3.12 simulations.py --molecules dmso --temperatures 1000 800 600 400 200 --seed 73

# Rebuild figures/animation and copy to the local website; no simulation, commit or push.
py -3.12 simulations.py --render-only demo_tp_20260925 --publish

# Explicit website destination overrides automatic selection.
py -3.12 simulations.py --render-only demo_tp_20260925 --publish --site-dir .\LiamMs_PandasProjects

py -3.12 simulations.py --help
py -3.12 -m unittest discover -s phase_lab/tests -v
```

Advanced overrides: `--cells` (4 × cells³ molecules, minimum 2), `--equilibration`,
`--production`, `--stride`, `--timestep-fs` (0–2 fs, default 1), `--threads`,
`--platform CPU|Reference|OpenCL|CUDA`, `--orientation multiaxis|random`.
Production must contain at least four full reporting intervals. The CPU backend
works here; GPU backends require compatible drivers/hardware and are not tested.
An existing run ID is never silently overwritten. Failed runs retain metadata and
partial CSVs for diagnosis, but cannot be rendered/published as completed results.
There is no resume/checkpoint support; start a new run after fixing the cause.

### Interaction, density and boundary options

- `--potentials coulomb_lj lj coulomb_wca wca` runs all four independently.
  A subset is allowed. Bare attractive Coulomb without a repulsive core is not.
- `--boundary periodic` (default) uses PME and periodic pair cutoffs.
  `--boundary walls --ensemble nvt` uses six stationary repulsive LJ walls and
  finite-system, no-cutoff pair interactions. Wall NPT is rejected.
- `--density-mode reference` initializes from sourced room-temperature density
  anchors, mostly at 293.15 K (benzyl alcohol: 297.15 K), with source pressure
  unspecified. These are **not exact 300 K/1 atm values**.
  NVT holds this bulk density; NPT only starts there and then varies volume.
  `--density-g-cm3` overrides the anchor. `--density-mode legacy` keeps the older
  sigma-based initial spacing.
- `--sigma-scale`, `--epsilon-scale`, `--cutoff-sigma` configure the LJ/WCA
  core, strength and pair cutoff. Sigma scaling does not alter the preset bond
  or charge. `--wall-epsilon` sets repulsive wall strength in kJ/mol per site.
- All combinations describe **different illustrative models**, not fitted real
  materials. Small timesteps and convergence/sensitivity studies are necessary.

## What is actually simulated?

**Not atomistic versions of the six named materials.** Each neutral rigid molecule
is a two-site dumbbell carrying −q and +q. Its dipole is measured from − to +.
Each site has half the molecular mass and one-quarter of the illustrative
Lennard-Jones epsilon. Four intermolecular site pairs give approximately the
molecular epsilon in the far-field limit. All intermolecular charges interact by
PME for charged periodic models; wall models use finite-system Coulomb.
The bonded intramolecular pair is excluded from nonbonded forces.
Uncharged models set both charges and the exported physical dipole magnitude to
zero, retaining a geometric orientation axis for structural comparisons.

| Inspired by | Approximate mass / Da | Illustrative dipole / D | σ / nm | ε / kJ mol⁻¹ |
| --- | ---: | ---: | ---: | ---: |
| Glycerol | 92.094 | 2.6 | 0.48 | 6.0 |
| Ethylene glycol | 62.068 | 2.3 | 0.43 | 4.5 |
| DMSO | 78.133 | 3.96 | 0.46 | 5.0 |
| Propylene glycol | 76.095 | 2.3 | 0.46 | 5.0 |
| Formamide | 45.041 | 3.73 | 0.36 | 4.5 |
| Benzyl alcohol | 108.14 | 1.7 | 0.50 | 5.5 |

These relatively low-volatility molecular inspirations are labels for comparing
interaction scales. **σ/ε are invented model parameters, not a fitted force field;
the dipoles are approximate illustrative scales, not conformer-resolved data.**
Bond length is 0.25σ; charge is μ × 0.020819434 / bond_length in elementary charges.
Change/add presets in [model.py](model.py). There are no mixtures in this version.

- Default three-dimensional periodic cube, minimized FCC initial centers, six initial
  dipole directions (or seeded random orientations).
- Constrained Langevin-middle integration; 1/ps friction; center-of-mass removal.
- NPT uses an isotropic Monte Carlo barostat every 25 steps. kPa are explicitly
  converted to bar for OpenMM. NVT has no barostat and pressure is blank in records.
- Cutoff = min(2σ, 0.36 × initial box length), LJ switching begins at 85% cutoff;
  PME error tolerance 5e-4. A homogeneous LJ dispersion correction is enabled.
  Tiny-box cutoffs/finite size and homogeneous tails limit quantitative results.
- Each pressure/material starts independently, but temperatures within a path
  inherit the previous plateau's configuration. Seeds, parameters, initial box,
  software versions and source hashes are written to the run metadata. Bitwise
  reproducibility across CPU/GPU platforms or versions is not promised.

## Angular metrics: more than net polarization

An isotropic sphere has uniform **cos(θ)** and φ; its θ density is sin(θ)/2.
Uniform θ bins would falsely suggest directional preference. The pooled maps
use 10 × 16 equal-solid-angle bins in (cos(θ), φ); φ wraps at ±π.
Probabilities divided by 1/160 give a density relative to an isotropic distribution.

For normalized dipoles u_i and Legendre polynomial P_l, the per-frame spectrum is

$$A_l^2 = \frac{1}{N(N-1)}\sum_{i\ne j}P_l(\mathbf u_i\cdot\mathbf u_j),\quad l=1,\ldots,6.$$

This is the spherical-harmonic power via the addition theorem, with self-pairs
removed. The signed estimates have expectation zero for independently isotropic
orientations. Negative finite-sample estimates are **kept in CSV**, not hidden.
The display statistic is

$$O_6=\sqrt{\frac{1}{6}\sum_{l=1}^{6}\max(0,A_l^2)}.$$

- O₆ ranges from 0 to 1; aligned dipoles give 1. Clipping creates a positive noise
  floor for finite N; with 32 molecules, random samples need not be close to zero.
- l=1 detects polarization; higher degrees retain patterns such as opposing or
  six-axis populations. This is rotationally invariant, unlike the plotted map.
- Polar order = norm of mean dipole; nematic order = largest eigenvalue of
  (3〈uuᵀ〉−I)/2. Both can miss a six-direction distribution that l=4 sees.
- The angular KL statistic is Σ p_b log(p_b / (1/B)) on **pooled production samples**.
  It retains multiple peaks, but has positive finite-sample bias and time
  correlations. Unlike averaged instantaneous O₆, a rotating ordered cluster
  can wash out in a pooled lab-frame map. Neither metric fits Gaussian mixtures
  or infers an exact number of peaks; narrow angular features above l=6 can be missed.
- No hand-coded melting temperature, logistic phase curve, or forced solid/liquid/gas labels.

## Structural evidence and limitations

Additional version-2 diagnostics: local structural `local_q6` (twelve nearest
neighbors, distinct from dipole O₆), nearest-neighbor distance, periodic COM RDF,
single-origin rotational `rotation_c2`, late-half MSD-slope/6 mobility proxy,
NVT Cv or NPT Cp/thermal expansion/compressibility fluctuation estimates.
Wall energy is exported separately from intermolecular energy. NPT RDF bins have
per-frame radius edges and must be rebinned before pooling in physical distance.
These are exploratory finite-trajectory estimates, not converged material constants.
The theory document defines normalization, units, ensemble restrictions and caveats.

Empirical absolute potential energy at arbitrary selected T/P is unavailable.
[references.py](references.py) instead provides sourced density anchors and sparse
vaporization enthalpies, showing their actual conditions and missing pressures.
The optional static `−mean(U_inter)/N + RT` proxy is a different, assumption-heavy
quantity, not a validated measurement or a substitute for missing empirical data.

FCC reference order averages normalized structure-factor intensities at the
initial lattice's {111} and {200} reciprocal vectors. It is 1 for the initial FCC
centers and approximately 1/N for random centers. It is invariant to translation
and uniform box expansion, but **not to rotation or a different crystal lattice**.

Nonaffine MSD accumulates minimum-image changes in fractional molecular centers,
scaled by adjacent-frame mean box lengths. It resets after each plateau's
equilibration, subtracting uniform barostat rescaling. It is NOT a fitted diffusion
coefficient. Reporting intervals must be short enough that no molecule moves more
than half the box between samples; otherwise unwrapping can alias motion.

Interpret loss of lattice order together with sustained displacement, density,
and energy changes. Dipole disorder alone could describe a rotationally disordered
solid. A gas-like interpretation also needs dilute density and structural evidence.
An NPT periodic box has no free surface and does not directly measure sublimation
flux or vapour pressure. The demo shows order loss/density changes but establishes
neither a melting point nor gas/solid coexistence. The first 180 K points are still
relaxing in several paths; comparing pressure curves confounds pressure with
independent trajectory noise. Four-block standard errors are descriptive, not
reliable thermodynamic confidence intervals for these short correlated trajectories.

For physically meaningful chemical predictions: obtain validated atomistic
force fields and conformations, include appropriate hydrogen bonding/flexibility,
compare with measured densities/enthalpies and phase data, run larger/longer boxes,
independent seeds and heating/cooling/coexistence protocols, inspect convergence
and autocorrelation times, and test cutoff/timestep sensitivity. Real molecules
may decompose long before the demonstration's highest temperatures; this rigid
nonreactive model cannot describe that chemistry.

## Output/data dictionary

Canonical files stay committable; no data/PDF ignore rules are added.
Runs are partitioned by material/pressure/temperature instead of one giant CSV.

| Location relative to root | Contents |
| --- | --- |
| `records/phase_simulations/<run>/metadata.json` | Status, units via field names, parameters, seeds, protocol, versions, source hashes |
| `records/phase_simulations/<run>/summary.csv` | One row per condition, metric means, 4-block SEs, pooled KL, final MSD |
| `records/phase_simulations/<run>/<condition>/trajectory.csv` | Frame, global MD step/time, molecule ID, box length, wrapped COM xyz (nm), accumulated nonaffine displacement (nm), COM velocity (nm/ps), unit dipole xyz, θ/φ (radians), dipole magnitude (D) |
| `records/phase_simulations/<run>/<condition>/thermodynamics.csv` | Per-frame potential/kinetic/total system energy (OpenMM kJ/mol), potential energy per molecule, measured kinetic temperature, volume, density, MSD, FCC/polar/nematic/multipolar metrics and signed harmonic spectrum |
| `records/phase_simulations/<run>/<condition>/orientation_histogram.csv` | Bin edges, counts, probability and density relative to isotropy |
| `reports/phase_simulations/<run>/` | PNG overview, angular maps/spectra, optional pressure surfaces, combined PDF |
| `media/phase_simulations/<run>/` | Offline HTML/CSS/JS trajectory viewer, compressed full CSV archive, summary and metadata copies |

Energy is a system quantity, not a uniquely assigned per-molecule interaction
energy; divide by N for the reported per-molecule mean. Temperature uses
5N−3 degrees of freedom for periodic systems (two sites, one bond constraint per
molecule, and removed COM translation), or 5N for walls without COM removal.
OpenMM integration velocities retain the integrator's
own velocity convention. Equilibration frames are intentionally excluded. The
saved dipole and COM coordinates reconstruct the two site positions via ±bond/2;
angular velocities/site velocities are not exported.

The browser preview caps **120 frames / 256 molecules per condition** to keep
loading reasonable; CSVs contain every requested saved sample. Static figures
are referenced, not duplicated, in the local media viewer. Publishing copies them
into the deployable site folder. There is no MP4/GIF dependency; the HTML plays
the time evolution offline using Canvas and can be screen-recorded if needed.

## Website integration and Git

`--publish` selects the sibling `liammspandasprojects` repository when it exists,
otherwise the local `LiamMs_PandasProjects` directory; `--site-dir` overrides this.
The stable entry is `Physics/Dipole-Atlas/index.html`, using a base URL to share
the featured NPT run's assets without a dated browser address or duplicate data.
Query parameters preserve the chosen potential, metric, molecule, temperature,
pressure and display. Archived output remains at `Physics/Dipole-Atlas/<run>/index.html`, with a Physics landing
page linking runs, plots, PDFs, and compressed records. Existing hand-written Physics
content is preserved by the standalone publisher.

[generate_liamms_site.py](../generate_liamms_site.py) now copies completed,
already-rendered runs into the site during normal builds and generates the Physics
landing page. It does **not** rerun molecular dynamics. That full generator still
owns/rebuilds category pages, so edit [publishing.py](publishing.py) rather than
hand-editing generated Physics HTML for lasting design changes.

No commits or pushes are performed automatically. Commit source, canonical CSVs,
PDFs/PNGs and media assets in this repository; commit/push the separate site output
repository when using the sibling destination. The demonstration's files are below
GitHub's ordinary 100 MiB/file limit. Larger runs can still exceed it: partition
runs, increase saved-frame stride deliberately, or use a suitable asset store.
Git LFS needs a deployment step that downloads real objects; don't publish LFS
pointer files as website downloads. Keep generated artifacts out of routine AI
context by requesting just this README, one module, or one condition's CSV.

## Code map

- [cli.py](cli.py): arguments, run IDs, rendering and publication.
- [model.py](model.py): molecule presets, FCC initialization, OpenMM forces.
- [engine.py](engine.py): simulation protocol and streamed records.
- [metrics.py](metrics.py): angular statistics, reference crystal order, periodic handling.
- [visuals.py](visuals.py): PNG/PDF figures, bounded preview payload, archive.
- [publishing.py](publishing.py): static Physics pages and copies.
- [references.py](references.py): attributed density/enthalpy observations and missing-data semantics.
- [documentation.py](documentation.py), [docs/theory.json](docs/theory.json): single-source theory HTML/PDF/LaTeX builder.
- [web/viewer.html](web/viewer.html), [web/viewer.css](web/viewer.css), [web/viewer.js](web/viewer.js): browser interface.
- [tests/test_lab.py](tests/test_lab.py): numerical and short NPT/NVT integration tests.
- [tests/test_extensions.py](tests/test_extensions.py): all potentials/boundaries, density, q6, RDF and fluctuation invariants.

Implementation references: [OpenMM NonbondedForce](https://docs.openmm.org/latest/api-python/generated/openmm.openmm.NonbondedForce.html),
[LangevinMiddleIntegrator](https://docs.openmm.org/latest/api-python/generated/openmm.openmm.LangevinMiddleIntegrator.html),
[MonteCarloBarostat](https://docs.openmm.org/latest/api-python/generated/openmm.openmm.MonteCarloBarostat.html).