import json
import logging
from utils import flatten_json

def setup_parser(subparsers):
    """Sets up the argparse subcommands for clusters."""
    cluster_parser = subparsers.add_parser('cluster', help='Manage clusters')
    cluster_subparsers = cluster_parser.add_subparsers(dest='action', help='Action to perform')
    
    # cluster add
    add_parser = cluster_subparsers.add_parser('add', help='Add a new cluster')
    add_parser.add_argument('--name', required=True, help='Name of the cluster')
    add_parser.add_argument('--description', help='Description of the cluster')
    add_parser.set_defaults(func=add_cluster)

    # cluster list
    list_parser = cluster_subparsers.add_parser('list', help='List all clusters')
    list_parser.add_argument('--output', '-o', choices=['text', 'json'], default='text', help='Output format (default: text)')
    list_parser.set_defaults(func=list_clusters)

    # cluster get
    get_parser = cluster_subparsers.add_parser('get', help='Get a cluster by UID')
    get_parser.add_argument('uid', help='UID of the cluster')
    get_parser.set_defaults(func=get_cluster)

    # cluster delete
    delete_parser = cluster_subparsers.add_parser('delete', help='Delete a cluster by UID')
    delete_parser.add_argument('uid', help='UID of the cluster')
    delete_parser.set_defaults(func=delete_cluster)

    # Similarly, add update and other subcommands here

def add_cluster(args, client):
    """Adds a new cluster."""
    data = {
        "name": args.name,
        "description": args.description,
    }
    result = client.post("clusters", data)
    logging.info(f"Cluster '{args.name}' added successfully")
    return result

def list_clusters(args, client):
    """Lists all clusters."""
    try:
        clusters = client.get("clusters")

        if args.output == 'json':
            # Output the data as JSON
            return json.dumps(clusters, indent=4)

        # Default output: Flattened dot notation for text format
        flattened_clusters = []
        for i, cluster in enumerate(clusters):
            flattened_cluster = flatten_json(cluster, parent_key=f'cluster[{i}]')
            flattened_clusters.append(flattened_cluster)

        # Format the flattened clusters as key: value text
        output_lines = []
        for flattened_cluster in flattened_clusters:
            for key, value in flattened_cluster.items():
                output_lines.append(f"{key}: {value}")
        
        return "\n".join(output_lines)

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return f"Error: {str(e)}"

def get_cluster(args, client):
    """Retrieves a specific cluster by UID."""
    cluster = client.get(f"clusters/{args.uid}")
    return cluster

def delete_cluster(args, client):
    """Deletes a cluster by UID."""
    success = client.delete(f"clusters/{args.uid}")
    if success:
        logging.info(f"Cluster {args.uid} deleted successfully")
    return success
