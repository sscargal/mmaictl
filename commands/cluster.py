import json
import logging
import requests
from utils import flatten_json, get_cluster_uid, filter_json
import textwrap

def setup_parser(subparsers):
    """Sets up the argparse subcommands for clusters."""
    cluster_parser = subparsers.add_parser(
        'cluster', 
        description='Manage Clusters in the MMAI Platform',
        help='Manage clusters'
    )
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

    # cluster set property
    set_parser = cluster_subparsers.add_parser('set', help='Update a cluster property')
    set_parser.add_argument('cluster', help='The name of the cluster to update')
    set_parser.add_argument('properties', nargs='+', help='The property to update in the format property=value (e.g., name=newClusterName)')
    set_parser.set_defaults(func=set_cluster_property)

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

def set_cluster_property(args, client):
    """
    Sets a cluster property by cluster UID.
    
    Args:
        args: Command-line arguments.
        client: The API client used for making requests.
    """
    try:
        # Get the cluster UID from the cluster name provided by the user
        cluster_uid = get_cluster_uid(client, args.cluster)

        # Ensure that the API URL is available (from --api-url argument)
        if not args.api_url:
            raise ValueError("API URL is not provided. Use --api-url to specify the API endpoint.")

        # Prepare the data to be updated
        update_data = {}
        for prop in args.properties:
            key, value = prop.split('=')
            update_data[key] = value

        logging.info(f"Updating cluster '{args.cluster}' (UID: {cluster_uid}) with data: {update_data}")

        # Construct the API URL
        api_url = f"{args.api_url}/clusters/{cluster_uid}"

        # Convert the update_data dictionary to a JSON string
        update_data_json = json.dumps(update_data)

        # Make the PUT request using the `requests` library
        response = requests.put(api_url, data=update_data_json, headers={'Content-Type': 'application/json'})

        # Handle successful response
        if response.status_code == 200:
            logging.info(f"Cluster '{args.cluster}' updated successfully.")
            print(f"Cluster updated: {response.json()}")
        else:
            # Handle 400 (Not Found) or other errors
            logging.error(f"Failed to update cluster: {response.text}")
            print(f"Error: {response.text}")

    except Exception as e:
        logging.error(f"Failed to update cluster: {e}")
        print(f"Error: {str(e)}")
