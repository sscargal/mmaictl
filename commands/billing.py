import json
import logging
from utils import flatten_json, get_cluster_uid, filter_json

def setup_parser(subparsers):
    """Sets up the argparse subcommands for billing."""
    billing_parser = subparsers.add_parser('billing', help='Get billing details for departments')
    billing_subparsers = billing_parser.add_subparsers(dest='action', help='Action to perform')

    # billing list
    list_parser = billing_subparsers.add_parser('list', help='List billing details for all departments in a cluster')
    list_parser.add_argument('--cluster', help='Cluster name or UID (optional, will auto-select if only one cluster exists)')
    list_parser.add_argument('--output', '-o', choices=['text', 'json'], default='text', help='Output format (default: text)')
    list_parser.add_argument('--filter', help='Comma-separated list of fields to display (e.g., "name,amount")')
    list_parser.set_defaults(func=list_billing)

def list_billing(args, client):
    """Lists billing details for all departments in a cluster."""
    try:
        cluster_uid = get_cluster_uid(client, args.cluster)
        billing = client.get(f"clusters/{cluster_uid}/billing")

        # Apply filter if provided
        if args.filter:
            filters = args.filter.split(',')
            billing = filter_json(billing, filters)

        if args.output == 'json':
            return json.dumps(billing, indent=4)

        flattened_billing = []
        for i, item in enumerate(billing):
            flattened_item = flatten_json(item, parent_key=f'billing[{i}]')
            flattened_billing.append(flattened_item)

        output_lines = []
        for flattened_item in flattened_billing:
            for key, value in flattened_item.items():
                output_lines.append(f"{key}: {value}")

        return "\n".join(output_lines)

    except Exception as e:
        return f"Error: {str(e)}"