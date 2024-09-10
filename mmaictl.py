#!/usr/bin/env python3 

import argparse
import logging
import sys
import os
from api_client import APIClient
from utils import setup_logging
from commands import cluster, department, nodegroup, project, workload, billing, topology, nodes


# Enable tab completion if installed
try:
    import argcomplete
except ImportError:
    pass

class CustomArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        """
        Override the default error method to provide better error message formatting.
        """
        # Print a custom error message
        sys.stderr.write(f"\nError: {message}\n\n")
        
        # Print usage message
        self.print_usage()
        
        # Print available commands in a more readable format
        sys.stderr.write("\nAvailable subcommands:\n")
        for action in self._actions:
            if isinstance(action, argparse._SubParsersAction):
                for choice, subparser in action.choices.items():
                    sys.stderr.write(f"  - {choice}: {subparser.description}\n")
        sys.exit(2)

def main():
    #parser = argparse.ArgumentParser(
    #    description="mmaictl: Command-line utility to manage platform resources like clusters, departments, and node groups."
    #)
    parser = CustomArgumentParser(description="mmaictl: Command-line utility to manage platform resources like clusters, departments, and node groups")
    
    # Global options
    parser.add_argument('--api-url', default='http://18.191.234.20:32323/v1', help='Base URL for the API')
    parser.add_argument('--token', help='Authentication token')
    parser.add_argument('-v', '--verbose', action='count', default=0, help='Increase verbosity (can be used multiple times)')
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
    nodes.setup_parser(subparsers)

    # Enable tab completion if available
    if 'argcomplete' in globals():
        argcomplete.autocomplete(parser)

    args = parser.parse_args()

    # Setup logging based on verbose and quiet flags
    setup_logging(args.verbose)

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