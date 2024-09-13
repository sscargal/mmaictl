import json
import logging
from utils import flatten_json, get_cluster_uid, filter_json

def setup_parser(subparsers):
    """Sets up the argparse subcommands for node groups."""
    nodegroup_parser = subparsers.add_parser(
        'nodegroup', 
        description='Manage Node Groups in the MMAI Platform.',
        help='Manage node groups'
    )
    nodegroup_subparsers = nodegroup_parser.add_subparsers(dest='action', help='Action to perform')

    # nodegroup add
    add_parser = nodegroup_subparsers.add_parser('add', help='Add a new node group')
    add_parser.add_argument('--name', required=True, help='Name of the node group')
    add_parser.add_argument('--description', help='Description of the node group')
    add_parser.set_defaults(func=add_nodegroup)

    # nodegroup list
    list_parser = nodegroup_subparsers.add_parser('list', help='List all node groups in a cluster')
    list_parser.add_argument('--cluster', help='Cluster name or UID (optional, will auto-select if only one cluster exists)')
    list_parser.add_argument('--output', '-o', choices=['default', 'dot', 'json'], default='default', help='Output format (default: text)')
    list_parser.set_defaults(func=list_nodegroups)

    # nodegroup get
    get_parser = nodegroup_subparsers.add_parser('get', help='Get all properties of one or more node groups')
    get_parser.add_argument('--cluster', help='Cluster name or UID (optional, will auto-select if only one cluster exists)')
    get_parser.add_argument('--name', '-n', nargs='+', help='List of node group names to show')
    get_parser.add_argument('--output', '-o', choices=['text', 'json'], default='text', help='Output format (default: text)')
    get_parser.add_argument('--filter', help='Comma-separated list of fields to display (e.g., "name,description")')
    get_parser.set_defaults(func=get_nodegroups)

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
    """Lists the node groups in a cluster with support for multiple output formats."""
    try:
        # If no cluster is specified, fetch all clusters
        if not args.cluster:
            clusters = client.get("clusters")
            if not clusters or not isinstance(clusters, list):
                logging.error("No clusters found.")
                return None
        else:
            # Fetch only the specified cluster
            cluster_uid = get_cluster_uid(client, args.cluster)
            clusters = [{"name": args.cluster, "uid": cluster_uid}]

        nodegroup_dict = {}

        for cluster in clusters:
            cluster_name = cluster.get('name')
            cluster_uid = cluster.get('uid')

            # Fetch nodegroups for this cluster
            nodegroups = client.get(f"clusters/{cluster_uid}/nodeGroups")
            if not nodegroups:
                logging.warning(f"No node groups found for cluster {cluster_name}.")
                continue

            # Add nodegroup names to the dictionary under their respective cluster
            nodegroup_dict[cluster_name] = [nodegroup['name'] for nodegroup in nodegroups]

        if not nodegroup_dict:
            print("No node groups found.")
            return

        # Output format handling
        if args.output == 'json':
            # JSON format with cluster as the key and node group names as the list
            print(json.dumps(nodegroup_dict, indent=4))
        
        elif args.output == 'dot':
            # Dot notation format
            output_lines = []
            for cluster_name, nodegroups in nodegroup_dict.items():
                for i, nodegroup in enumerate(nodegroups):
                    output_lines.append(f"cluster[{cluster_name}].nodegroup[{i}].name: {nodegroup}")
            print("\n".join(output_lines))
        
        else:
            # Default format with cluster name as a header and a blank line between clusters
            output_lines = []
            for cluster_name, nodegroups in nodegroup_dict.items():
                output_lines.append(f"[{cluster_name}]")
                for nodegroup in nodegroups:
                    output_lines.append(f"{nodegroup}")
                output_lines.append("")  # Add a blank line after each cluster's node groups
            print("\n".join(output_lines))

    except Exception as e:
        logging.error(f"Failed to fetch node groups: {e}")
        return None



def list_nodegroups_by_cluster_uid(cluster_uid, client):
    """Lists all node groups in a cluster using the cluster UID directly."""
    try:
        logging.info(f"Fetching node groups for cluster UID: {cluster_uid}")
        nodegroups = client.get(f"clusters/{cluster_uid}/nodeGroups")

        # Ensure the response is a list of node groups
        if not isinstance(nodegroups, list):
            logging.error(f"Unexpected response type: {type(nodegroups)}. Expected list.")
            return None

        return nodegroups

    except Exception as e:
        logging.error(f"Failed to fetch node groups for cluster {cluster_uid}: {e}")
        return None

def get_nodegroup(args, client):
    """Retrieves a specific node group by name."""
    nodegroup = client.get(f"nodegroups/{args.name}")
    return nodegroup

def get_nodegroups(args, client):
    """Shows all properties of one or more node groups in a cluster."""
    try:
        # If no cluster is specified, fetch all clusters
        if not args.cluster:
            clusters = client.get("clusters")
            if not clusters or not isinstance(clusters, list):
                logging.error("No clusters found.")
                return None
        else:
            # Fetch only the specified cluster
            cluster_uid = get_cluster_uid(client, args.cluster)
            clusters = [{"name": args.cluster, "uid": cluster_uid}]

        all_nodegroups = []

        for cluster in clusters:
            cluster_name = cluster.get('name')
            cluster_uid = cluster.get('uid')

            # Fetch nodegroups for this cluster
            nodegroups = client.get(f"clusters/{cluster_uid}/nodeGroups")
            if not nodegroups:
                logging.warning(f"No node groups found for cluster {cluster_name}.")
                continue

            # If --name is provided, filter node groups by the given names
            if args.name:
                nodegroups = [ng for ng in nodegroups if ng['name'] in args.name]

            if not nodegroups:
                logging.info(f"No matching node groups found for cluster {cluster_name}.")
                continue

            # Apply filter if provided
            if args.filter:
                filters = args.filter.split(',')
                nodegroups = filter_json(nodegroups, filters)

            # Flatten each nodegroup and prefix with the cluster name
            for i, nodegroup in enumerate(nodegroups):
                flattened_nodegroup = flatten_json(nodegroup, parent_key=f"cluster[{cluster_name}].nodegroup[{i}]")
                all_nodegroups.append(flattened_nodegroup)

        if not all_nodegroups:
            print("No matching node groups found.")
            return

        # If JSON output is requested
        if args.output == 'json':
            print(json.dumps(all_nodegroups, indent=4))
            return

        # Prepare text output
        output_lines = []
        for nodegroup in all_nodegroups:
            for key, value in nodegroup.items():
                output_lines.append(f"{key}: {value}")

        print("\n".join(output_lines))

    except Exception as e:
        logging.error(f"Failed to fetch node groups: {e}")
        return None

def delete_nodegroup(args, client):
    """Deletes a node group by name."""
    success = client.delete(f"nodegroups/{args.name}")
    if success:
        logging.info(f"Node group {args.name} deleted successfully")
    return success
