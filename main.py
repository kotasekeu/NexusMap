"""
Command-line entry point for running a NexusMap analysis.

Usage:
    python3 main.py --input data.csv --config config.json --output results/
"""

import argparse
import os
import sys
from project_processor import process_project


def main():
    parser = argparse.ArgumentParser(description='Train a Kohonen SOM on a CSV file and generate the analysis outputs.')
    parser.add_argument('-i', '--input', required=True, help='Path to the input CSV file')
    parser.add_argument('-c', '--config', required=True,
                        help='Path to a JSON file with "project_settings" and "som_settings"')
    parser.add_argument('-o', '--output', required=True, help='Output directory (created if missing)')
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        sys.exit(f"Error: input file {args.input} does not exist.")
    if not os.path.isfile(args.config):
        sys.exit(f"Error: configuration file {args.config} does not exist.")

    process_project(args.input, args.config, args.output)


if __name__ == "__main__":
    main()
