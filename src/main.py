"""
Main entry point for running experiments.
Uses config.yaml to define what to run.
"""
from runner import run_from_config
from logger import setup_logger
from config_loader import ConfigLoader


def main():
    """Run all experiments defined in config.yaml."""
    # Load config to get logging settings
    config = ConfigLoader("config.yaml")
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

    run_from_config("config.yaml")


if __name__ == "__main__":
    main()
