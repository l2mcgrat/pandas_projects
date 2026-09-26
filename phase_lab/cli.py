"""Command-line orchestration. Plot/publish previous runs without rerunning MD."""

import argparse
from datetime import datetime, timezone
from pathlib import Path
import re

from .model import MODEL_NOTICE, MOLECULES, POTENTIALS
from .engine import Config, run_sweep


ROOT = Path(__file__).resolve().parents[1]


def parser():
    result = argparse.ArgumentParser(description="Dipole Atlas: qualitative molecular order, NOT calibrated phase boundaries.")
    result.add_argument("--molecules", nargs="+", choices=list(MOLECULES), default=list(MOLECULES))
    result.add_argument("--temperatures", nargs="+", type=float, default=[180, 300, 500, 800], metavar="K",
                        help="Plateaus in supplied order; descending values make a cooling path.")
    result.add_argument("--pressures", nargs="+", type=float, default=[101.325], metavar="KPA")
    result.add_argument("--ensemble", choices=["npt", "nvt"], default="npt")
    result.add_argument("--potentials", nargs="+", choices=list(POTENTIALS), default=["coulomb_lj"])
    result.add_argument("--boundary", choices=["periodic", "walls"], default="periodic")
    result.add_argument("--density-mode", choices=["reference", "legacy"], default="reference",
                        help="Room-T reference start (NVT holds density, NPT allows it to change) or old sigma-based FCC start.")
    result.add_argument("--density-g-cm3", type=float, help="Override starting bulk density, g/cm3.")
    result.add_argument("--sigma-scale", type=float, default=1.)
    result.add_argument("--epsilon-scale", type=float, default=1.)
    result.add_argument("--cutoff-sigma", type=float, default=2.)
    result.add_argument("--wall-epsilon", type=float, default=5., help="Repulsive LJ wall well scale in kJ/mol per site.")
    result.add_argument("--quality", choices=["demo", "extended"], default="demo",
                        help="demo: 32 molecules/2 ps per plateau; extended: 108 molecules/50 ps.")
    result.add_argument("--cells", type=int)
    result.add_argument("--equilibration", type=int)
    result.add_argument("--production", type=int)
    result.add_argument("--stride", type=int)
    result.add_argument("--timestep-fs", type=float, default=1)
    result.add_argument("--platform", choices=["CPU", "Reference", "CUDA", "OpenCL"], default="CPU")
    result.add_argument("--threads", type=int, default=2)
    result.add_argument("--seed", type=int, default=20260925)
    result.add_argument("--orientation", choices=["multiaxis", "random"], default="multiaxis")
    result.add_argument("--run-id", help="Unique output folder name; existing runs are never overwritten.")
    result.add_argument("--render-only", metavar="RUN_ID", help="Rebuild plots/HTML from existing CSVs.")
    result.add_argument("--publish", action="store_true", help="Copy completed artifacts into local website (no push).")
    result.add_argument("--site-dir", type=Path, help="Explicit website root for --publish.")
    return result


def main(argv=None):
    arguments = parser()
    args = arguments.parse_args(argv)
    run_id = args.render_only or args.run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", run_id):
        arguments.error("Run ID must be 1-80 letters, digits, underscores or hyphens; start with a letter/digit.")
    if args.render_only and args.run_id:
        arguments.error("Use --render-only OR --run-id, not both.")
    if args.site_dir and not args.publish:
        arguments.error("--site-dir requires --publish.")
    print(MODEL_NOTICE, flush=True)
    try:
        if not args.render_only:
            defaults = (2, 500, 1500, 50) if args.quality == "demo" else (3, 10000, 40000, 250)
            cells, equilibration, production, stride = [
                default if value is None else value
                for value, default in zip((args.cells, args.equilibration, args.production, args.stride), defaults)
            ]
            config = Config(tuple(args.molecules), tuple(args.temperatures), tuple(args.pressures),
                            args.ensemble, cells, equilibration, production, stride, args.timestep_fs,
                            args.seed, args.platform, args.threads, args.orientation,
                            potentials=tuple(args.potentials), boundary=args.boundary, density_mode=args.density_mode,
                            density_g_cm3=args.density_g_cm3, sigma_scale=args.sigma_scale,
                            epsilon_scale=args.epsilon_scale, cutoff_sigma=args.cutoff_sigma, wall_epsilon=args.wall_epsilon)
            config.validate()
            steps = len(config.potentials) * len(config.molecules) * len(config.pressures) * len(config.temperatures) * (equilibration + production)
            print(f"Run {run_id}: {4 * cells ** 3} molecules, {steps:,} total MD steps. No phase labels are forced.", flush=True)
            run_sweep(config, ROOT, run_id)
        from .visuals import render_run
        from .publishing import publish_run
        render_run(ROOT, run_id)
        if args.publish:
            sibling = ROOT.parent / "liammspandasprojects"
            site = args.site_dir or (sibling if sibling.exists() else ROOT / "LiamMs_PandasProjects")
            publish_run(ROOT, run_id, site)
            print(f"Website prepared locally: {site / 'Physics' / 'Dipole-Atlas' / run_id / 'index.html'}")
        print(f"Records: {ROOT / 'records' / 'phase_simulations' / run_id}")
        print(f"Reports: {ROOT / 'reports' / 'phase_simulations' / run_id}")
        print(f"Animation: {ROOT / 'media' / 'phase_simulations' / run_id / 'index.html'}")
    except (ValueError, FileExistsError, FileNotFoundError) as exc:
        arguments.exit(2, f"Error: {exc}\n")