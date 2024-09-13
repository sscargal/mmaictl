import json
import logging
from utils import flatten_json, get_cluster_uid, filter_json

def setup_parser(subparsers):
    """Sets up the argparse subcommands for departments."""
    department_parser = subparsers.add_parser(
        'department', 
        description='Manage Departments in the MMAI platform.',
        help='Manage departments'
    )
    department_subparsers = department_parser.add_subparsers(dest='action', help='Action to perform')

    # department add
    add_parser = department_subparsers.add_parser('add', help='Add a new department')
    add_parser.add_argument('--name', required=True, help='Name of the department')
    add_parser.add_argument('--description', help='Description of the department')
    add_parser.set_defaults(func=add_department)

    # department list
    list_parser = department_subparsers.add_parser('list', help='List all departments in a cluster')
    list_parser.add_argument('--cluster', help='Cluster name or UID (optional, will auto-select if only one cluster exists)')
    list_parser.add_argument('--output', '-o', choices=['text', 'json'], default='text', help='Output format (default: text)')
    list_parser.add_argument('--filter', help='Comma-separated list of fields to display (e.g., "name,description")')
    list_parser.set_defaults(func=list_departments)

    # department get
    get_parser = department_subparsers.add_parser('get', help='Get a department by name')
    get_parser.add_argument('name', help='Name of the department')
    get_parser.set_defaults(func=get_department)

    # department delete
    delete_parser = department_subparsers.add_parser('delete', help='Delete a department by name')
    delete_parser.add_argument('name', help='Name of the department')
    delete_parser.set_defaults(func=delete_department)

def add_department(args, client):
    """Adds a new department."""
    data = {
        "name": args.name,
        "description": args.description,
    }
    result = client.post("departments", data)
    logging.info(f"Department '{args.name}' added successfully")
    return result

def list_departments(args, client):
    """Lists all departments in a cluster or from all clusters if no cluster is specified."""
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

        all_departments = []

        for cluster in clusters:
            cluster_name = cluster.get('name')
            cluster_uid = cluster.get('uid')

            # Fetch departments for this cluster
            departments = client.get(f"clusters/{cluster_uid}/departments")
            if not departments:
                logging.warning(f"No departments found for cluster {cluster_name}.")
                continue

            # Apply filter if provided
            if args.filter:
                filters = args.filter.split(',')
                departments = filter_json(departments, filters)

            # Flatten each department and prefix with the cluster name
            for i, department in enumerate(departments):
                flattened_department = flatten_json(department, parent_key=f"cluster[{cluster_name}].department[{i}]")
                all_departments.append(flattened_department)

        # If JSON output is requested
        if args.output == 'json':
            return json.dumps(all_departments, indent=4)

        # Prepare text output
        output_lines = []
        for department in all_departments:
            for key, value in department.items():
                output_lines.append(f"{key}: {value}")

        print("\n".join(output_lines))

    except Exception as e:
        logging.error(f"Failed to fetch departments: {e}")
        return None


def list_departments_by_cluster_uid(cluster_uid, client):
    """
    Fetches the list of departments for a given cluster UID using the provided API client.
    
    Args:
        cluster_uid (str): The UID of the cluster.
        client: The API client used for making requests.
    
    Returns:
        list or str: A list of departments or an error message if the request fails.
    """
    try:
        logging.info(f"Fetching departments for cluster UID: {cluster_uid}")
        departments = client.get(f"clusters/{cluster_uid}/departments")

        # Check if the response is a list (the expected type)
        if not isinstance(departments, list):
            logging.error(f"Unexpected response type: {type(departments)}. Expected list.")
            return None

        return departments

    except Exception as e:
        logging.error(f"Failed to fetch departments for cluster {cluster_uid}: {e}")
        return None

def get_department(args, client):
    """Retrieves a specific department by name."""
    department = client.get(f"departments/{args.name}")
    return department

def delete_department(args, client):
    """Deletes a department by name."""
    success = client.delete(f"departments/{args.name}")
    if success:
        logging.info(f"Department {args.name} deleted successfully")
    return success
