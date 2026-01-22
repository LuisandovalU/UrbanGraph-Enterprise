#!/usr/bin/env python3
"""UrbanGraph Engine CLI."""
import argparse
import subprocess
import sys
import os


def run_lint(_):
    """Run linting tools."""
    try:
        print("Running flake8...")
        subprocess.run([sys.executable, "-m", "flake8", "src/urban_graph_engine"], check=True)
        print("Running black...")
        subprocess.run([sys.executable, "-m", "black", "--check", "src/urban_graph_engine"], check=True)
        print("Running isort...")
        subprocess.run([sys.executable, "-m", "isort", "--check-only", "--profile", "black", "src/urban_graph_engine"], check=True)
        print("Linting passed!")
    except subprocess.CalledProcessError as e:
        print(f"Linting failed: {e}")
        sys.exit(1)


def run_tests(_):
    """Run tests."""
    try:
        print("Running pytest...")
        subprocess.run([sys.executable, "-m", "pytest", "tests/"], check=True)
        print("Tests passed!")
    except subprocess.CalledProcessError as e:
        print(f"Tests failed: {e}")
        sys.exit(1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="urban_graph_engine",
        description="UrbanGraph Engine CLI",
    )
    sub = parser.add_subparsers(dest="command")

    # Status command
    status_cmd = sub.add_parser("status", help="Show status")
    status_cmd.set_defaults(func=lambda _: print("UrbanGraph Engine: operational"))

    # Version command
    ver_cmd = sub.add_parser("version", help="Show version")
    ver_cmd.set_defaults(func=lambda _: print("UrbanGraph Engine v0.1.0"))

    # Lint command
    lint_cmd = sub.add_parser("lint", help="Run linting tools (flake8, black, isort)")
    lint_cmd.set_defaults(func=run_lint)

    # Test command
    test_cmd = sub.add_parser("test", help="Run tests")
    test_cmd.set_defaults(func=run_tests)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
