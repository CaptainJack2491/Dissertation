"""
Main entry point for running experiments.
Uses config.yaml to define what to run.
"""
import argparse
from runner import run_from_config
from logger import setup_logger
from config_loader import ConfigLoader


def main():
    """Run all experiments defined in config.yaml."""
    parser = argparse.ArgumentParser(description="Run experiments from config")
    parser.add_argument("--config", default="config.yaml", help="Path to config file")
    parser.add_argument("--no-resume", dest="resume", action="store_false",
                        default=True, help="Ignore existing logs and start fresh")
    args = parser.parse_args()

    # Load config to get logging settings
    config = ConfigLoader(args.config)
    config.load()

    # Initialize logger
    log_config = config.logging_config
    setup_logger(
        name="experiment",
        level=log_config.get('level', 3),
        log_format=log_config.get('format', '[{level}] {message}'),
        output=log_config.get('output', 'console'),
        log_file=log_config.get('file')
    )

    run_from_config(args.config, resume=args.resume)


if __name__ == "__main__":
    main()
