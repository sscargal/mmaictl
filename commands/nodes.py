import json
import logging
from utils import flatten_json, get_cluster_uid, filter_json

def setup_parser(subparsers):
    """
    Sets up the argument parser for the `node` subcommand.
    
    Args:
        subparsers: The main subparsers object to add subcommands to.
    """
    # Create the parser for `node`
    node_parser = subparsers.add_parser(
        'node', 
        description='Manage Nodes in the MMAI Platform.',
        help='Manage nodes in clusters'
    )
    
    # Create subparsers for actions under `node`
    node_subparsers = node_parser.add_subparsers(dest='action')

    # Create `list` action under `node`
    list_parser = node_subparsers.add_parser('list', help='List node names in a cluster or all clusters')
    list_parser.add_argument('--cluster', help='The name of the cluster to list nodes for (optional)')
    list_parser.add_argument('--output', '-o', choices=['default', 'dot', 'json'], default='default', help='Output format (default, dot, or json)')
    list_parser.set_defaults(func=list_nodes)

    # Create `get` action under `node`
    get_parser = node_subparsers.add_parser('get', help='Get details of nodes in a cluster or all clusters')
    get_parser.add_argument('--cluster', help='The name of the cluster to get node details for (optional)')
    get_parser.add_argument('--output', choices=['text', 'json'], default='text', help='Output format (text or json)')
    get_parser.add_argument('--filter', help='Comma-separated list of fields to filter the output')
    get_parser.set_defaults(func=get_node)

def list_nodes(args, client):
    """Lists the names of nodes in a cluster or from all clusters."""
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

        node_dict = {}

        for cluster in clusters:
            cluster_name = cluster.get('name')
            cluster_uid = cluster.get('uid')

            nodes = list_nodes_by_cluster_uid(cluster_uid, client)
            if not nodes:
                logging.warning(f"No nodes found for cluster {cluster_name}.")
                continue

            # Only extract node names
            node_dict[cluster_name] = [node['name'] for node in nodes]

        if not node_dict:
            print("No nodes found.")
            return

        # Output format handling
        if args.output == 'json':
            # JSON format
            print(json.dumps(node_dict, indent=4))
        
        elif args.output == 'dot':
            # Dot notation format
            output_lines = []
            for cluster_name, nodes in node_dict.items():
                for i, node in enumerate(nodes):
                    output_lines.append(f"cluster[{cluster_name}].node[{i}].name: {node}")
            print("\n".join(output_lines))
        
        else:
            # Default format with cluster name as a header
            output_lines = []
            for cluster_name, nodes in node_dict.items():
                output_lines.append(f"[{cluster_name}]")
                for node in nodes:
                    output_lines.append(f"{node}")
                output_lines.append("")  # Add blank line after each cluster
            print("\n".join(output_lines))

    except Exception as e:
        logging.error(f"Failed to list nodes: {e}")
        return None

def get_node(args, client):
    """Gets detailed information about nodes in a cluster or from all clusters."""
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

        all_nodes = []

        for cluster in clusters:
            cluster_name = cluster.get('name')
            cluster_uid = cluster.get('uid')

            nodes = list_nodes_by_cluster_uid(cluster_uid, client)
            if not nodes:
                logging.warning(f"No nodes found for cluster {cluster_name}.")
                continue

            # Apply filter if provided
            if args.filter:
                filters = args.filter.split(',')
                nodes = filter_json(nodes, filters)

            for i, node in enumerate(nodes):
                # Add node details to the list under their respective cluster
                all_nodes.append({
                    'cluster': cluster_name,
                    'node': flatten_json(node, parent_key=f"cluster[{cluster_name}].node[{i}]")
                })

        if not all_nodes:
            print("No node details found.")
            return

        # Output format handling
        if args.output == 'json':
            # JSON format
            node_output = {}
            for node in all_nodes:
                cluster_name = node['cluster']
                if cluster_name not in node_output:
                    node_output[cluster_name] = []
                node_output[cluster_name].append(node['node'])
            print(json.dumps(node_output, indent=4))

        else:
            # Text output
            output_lines = []
            for node in all_nodes:
                for key, value in node['node'].items():
                    output_lines.append(f"{key}: {value}")
            print("\n".join(output_lines))

    except Exception as e:
        logging.error(f"Failed to get node details: {e}")
        return None

def list_nodes_by_cluster_uid(cluster_uid, client):
    """
    Fetches the list of nodes for a given cluster UID using the provided API client.
    
    Args:
        cluster_uid (str): The UID of the cluster.
        client: The API client used for making requests.
    
    Returns:
        list or None: A list of nodes or None if the request fails.
    """
    try:
        logging.info(f"Fetching nodes for cluster UID: {cluster_uid}")
        nodes = client.get(f"clusters/{cluster_uid}/nodes")

        # Ensure the response is a list
        if not isinstance(nodes, list):
            logging.error(f"Unexpected response type: {type(nodes)}. Expected list.")
            return None

        return nodes

    except Exception as e:
        logging.error(f"Failed to fetch nodes for cluster {cluster_uid}: {e}")
        return None
