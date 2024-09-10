import json
import logging
from utils import flatten_json, get_cluster_uid, filter_json

def setup_parser(subparsers):
    """Sets up the argparse subcommands for node groups."""
    nodegroup_parser = subparsers.add_parser('nodegroup', help='Manage node groups')
    nodegroup_subparsers = nodegroup_parser.add_subparsers(dest='action', help='Action to perform')

    # nodegroup add
    add_parser = nodegroup_subparsers.add_parser('add', help='Add a new node group')
    add_parser.add_argument('--name', required=True, help='Name of the node group')
    add_parser.add_argument('--description', help='Description of the node group')
    add_parser.set_defaults(func=add_nodegroup)

    # nodegroup list
    list_parser = nodegroup_subparsers.add_parser('list', help='List all node groups in a cluster')
    list_parser.add_argument('--cluster', help='Cluster name or UID (optional, will auto-select if only one cluster exists)')
    list_parser.add_argument('--output', '-o', choices=['text', 'json'], default='text', help='Output format (default: text)')
    list_parser.add_argument('--filter', help='Comma-separated list of fields to display (e.g., "name,description")')
    list_parser.set_defaults(func=list_nodegroups)

    # nodegroup get
    get_parser = nodegroup_subparsers.add_parser('get', help='Get a node group by name')
    get_parser.add_argument('name', help='Name of the node group')
    get_parser.set_defaults(func=get_nodegroup)

    # nodegroup delete
    delete_parser = nodegroup_subparsers.add_parser('delete', help='Delete a node group by name')
    delete_parser.add_argument('name', help='Name of the node group')
    delete_parser.set_defaults(func=delete_nodegroup)

def add_nodegroup(args, client):
    """Adds a new node group."""
    data = {
        "name": args.name,
        "description": args.description,
    }
    result = client.post("nodegroups", data)
    logging.info(f"Node group '{args.name}' added successfully")
    return result

def list_nodegroups(args, client):
    """Lists all node groups in a cluster."""
    try:
        cluster_uid = get_cluster_uid(client, args.cluster)
        nodegroups = client.get(f"clusters/{cluster_uid}/nodeGroups")

        # Apply filter if provided
        if args.filter:
            filters = args.filter.split(',')
            nodegroups = filter_json(nodegroups, filters)

        if args.output == 'json':
            return json.dumps(nodegroups, indent=4)

        flattened_nodegroups = []
        for i, nodegroup in enumerate(nodegroups):
            flattened_nodegroup = flatten_json(nodegroup, parent_key=f'nodegroup[{i}]')
            flattened_nodegroups.append(flattened_nodegroup)

        output_lines = []
        for flattened_nodegroup in flattened_nodegroups:
            for key, value in flattened_nodegroup.items():
                output_lines.append(f"{key}: {value}")

        return "\n".join(output_lines)

    except Exception as e:
        return f"Error: {str(e)}"

def get_nodegroup(args, client):
    """Retrieves a specific node group by name."""
    nodegroup = client.get(f"nodegroups/{args.name}")
    return nodegroup

def delete_nodegroup(args, client):
    """Deletes a node group by name."""
    success = client.delete(f"nodegroups/{args.name}")
    if success:
        logging.info(f"Node group {args.name} deleted successfully")
    return success
