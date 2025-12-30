"""
Main entry point for running experiments.
Uses config.yaml to define what to run.
"""
from runner import run_from_config


def main():
    """Run all experiments defined in config.yaml."""
    run_from_config("config.yaml")


if __name__ == "__main__":
    main()
