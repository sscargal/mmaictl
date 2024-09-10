import logging
import json

def setup_logging(verbose, quiet):
    """Set up logging configuration based on verbosity and quiet mode."""
    if quiet:
        logging.basicConfig(level=logging.CRITICAL)
    elif verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

def output_formatter(data, args):
    if isinstance(data, dict):
        print(json.dumps(data, indent=4))
    elif isinstance(data, list):
        for item in data:
            print(json.dumps(item, indent=4))
    else:
        print(data)

def flatten_json(nested_json, parent_key='', sep='.'):
    """
    Flattens a nested JSON object into a single-level dictionary with dot notation.
    
    Args:
        nested_json (dict): The nested JSON object to flatten.
        parent_key (str): The base key to prepend (used in recursion).
        sep (str): The separator between parent and child keys.

    Returns:
        dict: A flattened dictionary with dot notation for nested keys.
    """
    items = []
    for key, value in nested_json.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        if isinstance(value, dict):
            items.extend(flatten_json(value, new_key, sep=sep).items())
        else:
            items.append((new_key, value))
    return dict(items)

def get_cluster_uid(client, cluster_identifier=None):
    """
    Fetches the cluster UID based on either the cluster name or UID.
    
    Args:
        client: APIClient instance to communicate with the API.
        cluster_identifier: The name or UID of the cluster. If None, it will auto-select the cluster if only one exists.

    Returns:
        The UID of the cluster or raises an error if not found.
    """
    clusters = client.get("clusters")

    if not clusters:
        raise Exception("No clusters found.")
    
    if cluster_identifier:
        # Try to find the cluster by name or UID
        for cluster in clusters:
            if cluster['name'] == cluster_identifier or cluster['uid'] == cluster_identifier:
                return cluster['uid']
        raise Exception(f"Cluster '{cluster_identifier}' not found.")
    
    # If only one cluster exists, use it
    if len(clusters) == 1:
        return clusters[0]['uid']

    # If multiple clusters exist and no cluster is specified, print the options
    available_clusters = [cluster['name'] for cluster in clusters]
    raise Exception(f"Multiple clusters found. Specify a cluster with --cluster. Available clusters: {', '.join(available_clusters)}")

def filter_json(data, filters):
    """
    Filters a nested JSON object and returns only the specified fields.
    
    Args:
        data (list or dict): The JSON object (either a list of dictionaries or a single dictionary).
        filters (list): A list of fields to extract, specified in dot notation (e.g., ['name', 'description']).
    
    Returns:
        A filtered version of the data.
    """
    def extract_field(obj, field):
        """Extracts a field from a nested dictionary using dot notation."""
        keys = field.split('.')
        for key in keys:
            if isinstance(obj, dict) and key in obj:
                obj = obj[key]
            else:
                return None  # Return None if the key doesn't exist
        return obj

    if isinstance(data, list):
        return [{field: extract_field(item, field) for field in filters} for item in data]
    elif isinstance(data, dict):
        return {field: extract_field(data, field) for field in filters}
    return data
