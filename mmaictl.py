#!/usr/bin/env python3 

import argparse
import logging
import sys
import os
from api_client import APIClient
from utils import setup_logging
from commands import cluster, department, nodegroup, project, workload, billing, topology  # Include the command modules

# Enable tab completion if installed
try:
    import argcomplete
except ImportError:
    pass

def main():
    parser = argparse.ArgumentParser(
        description="mmaictl: Command-line utility to manage platform resources like clusters, departments, and node groups."
    )
    
    # Global options
    parser.add_argument('--api-url', default='http://18.191.234.20:32323/v1', help='Base URL for the API')
    parser.add_argument('--token', help='Authentication token')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose mode for debugging')
    parser.add_argument('--quiet', action='store_true', help='Enable quiet mode (minimal output)')
    
    # Create subparsers for objects
    subparsers = parser.add_subparsers(dest='object', help='Object to manage')
    subparsers.required = True  # Ensure a subcommand is required to be provided
    
    # Register command subparsers by calling their setup function
    cluster.setup_parser(subparsers)
    department.setup_parser(subparsers)
    nodegroup.setup_parser(subparsers)
    project.setup_parser(subparsers)
    workload.setup_parser(subparsers)
    billing.setup_parser(subparsers)
    topology.setup_parser(subparsers)

    # Enable tab completion if available
    if 'argcomplete' in globals():
        argcomplete.autocomplete(parser)

    args = parser.parse_args()

    # Setup logging based on verbose and quiet flags
    setup_logging(args.verbose, args.quiet)

    # Ensure a valid subcommand was provided
    if hasattr(args, 'func'):
        client = APIClient(base_url=args.api_url, token=args.token)
        try:
            result = args.func(args, client)
            print(result)  # Output the result in a formatted way
        except Exception as e:
            logging.error(f"Error: {str(e)}")
            exit(1)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()