"""Independent portfolio build; does not regenerate or import Smash analytics."""
import argparse
from pathlib import Path

from .analysis import analyze_code, analyze_music
from .publishing import load_analysis, publish_portfolio


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    sibling = root.parent / 'liammspandasprojects'
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--site-dir', type=Path, default=sibling if sibling.exists() else root / 'LiamMs_PandasProjects')
    parser.add_argument('--also-local', action='store_true', help='Also update the in-workspace site preview.')
    parser.add_argument('--music-repo', type=Path, default=root.parent / 'music_work')
    parser.add_argument('--code-repo', type=Path, default=root.parent / 'leetcode_problems')
    args = parser.parse_args()
    music = load_analysis(root, 'music-analysis', analyze_music, args.music_repo)
    code = load_analysis(root, 'code-analysis', analyze_code, args.code_repo)
    publish_portfolio(root, args.site_dir, music, code)
    local = root / 'LiamMs_PandasProjects'
    if args.also_local and local.resolve() != args.site_dir.resolve():
        publish_portfolio(root, local, music, code)


if __name__ == '__main__':
    main()