import json
import logging
from utils import flatten_json, get_cluster_uid, filter_json

def setup_parser(subparsers):
    """Sets up the argparse subcommands for projects."""
    project_parser = subparsers.add_parser(
        'project', 
        description='Manage Projects in the MMAI Platform.',
        help='Manage projects'
    )
    project_subparsers = project_parser.add_subparsers(dest='action', help='Action to perform')

    # project add
    add_parser = project_subparsers.add_parser('add', help='Add a new project')
    add_parser.add_argument('--name', required=True, help='Name of the project')
    add_parser.add_argument('--description', help='Description of the project')
    add_parser.set_defaults(func=add_project)

    # project list
    list_parser = project_subparsers.add_parser('list', help='List project names in a cluster or all clusters')
    list_parser.add_argument('--cluster', help='Cluster name or UID (optional, will auto-select if only one cluster exists)')
    list_parser.add_argument('--output', '-o', choices=['default', 'dot', 'json'], default='default', help='Output format (default, dot, or json)')
    list_parser.set_defaults(func=list_projects)

    # project get
    get_parser = project_subparsers.add_parser('get', help='Get detailed information for projects in a cluster')
    get_parser.add_argument('--cluster', help='Cluster name or UID (optional, will auto-select if only one cluster exists)')
    get_parser.add_argument('--output', choices=['text', 'json'], default='text', help='Output format (text or json)')
    get_parser.add_argument('--filter', help='Comma-separated list of fields to display (e.g., "name,description")')
    get_parser.set_defaults(func=get_projects)

    # project update
    update_parser = project_subparsers.add_parser('update', help='Update a project by name')
    update_parser.add_argument('name', help='Name of the project')
    update_parser.add_argument('--new-name', help='New name for the project')
    update_parser.add_argument('--description', help='New description for the project')
    update_parser.set_defaults(func=update_project)

    # project delete
    delete_parser = project_subparsers.add_parser('delete', help='Delete a project by name')
    delete_parser.add_argument('name', help='Name of the project')
    delete_parser.set_defaults(func=delete_project)

def add_project(args, client):
    """Adds a new project."""
    data = {
        "name": args.name,
        "description": args.description,
    }
    result = client.post("projects", data)
    logging.info(f"Project '{args.name}' added successfully")
    return result

def list_projects(args, client):
    """Lists the names of projects in a cluster or from all clusters."""
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

        project_dict = {}

        for cluster in clusters:
            cluster_name = cluster.get('name')
            cluster_uid = cluster.get('uid')

            # Fetch projects for this cluster
            projects = client.get(f"clusters/{cluster_uid}/projects")
            if not projects:
                logging.warning(f"No projects found for cluster {cluster_name}.")
                continue

            # Only extract project names
            project_dict[cluster_name] = [project['name'] for project in projects]

        if not project_dict:
            print("No projects found.")
            return

        # Output format handling
        if args.output == 'json':
            # JSON format
            print(json.dumps(project_dict, indent=4))
        
        elif args.output == 'dot':
            # Dot notation format
            output_lines = []
            for cluster_name, projects in project_dict.items():
                for i, project in enumerate(projects):
                    output_lines.append(f"cluster[{cluster_name}].project[{i}].name: {project}")
            print("\n".join(output_lines))
        
        else:
            # Default format with cluster name as a header
            output_lines = []
            for cluster_name, projects in project_dict.items():
                output_lines.append(f"[{cluster_name}]")
                for project in projects:
                    output_lines.append(f"{project}")
                output_lines.append("")  # Add blank line after each cluster
            print("\n".join(output_lines))

    except Exception as e:
        logging.error(f"Failed to list projects: {e}")
        return None

def get_projects(args, client):
    """Gets properties for each project in a cluster or from all clusters."""
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

        all_projects = []

        for cluster in clusters:
            cluster_name = cluster.get('name')
            cluster_uid = cluster.get('uid')

            # Fetch projects for this cluster
            projects = client.get(f"clusters/{cluster_uid}/projects")
            if not projects:
                logging.warning(f"No projects found for cluster {cluster_name}.")
                continue

            # Apply filter if provided
            if args.filter:
                filters = args.filter.split(',')
                projects = filter_json(projects, filters)

            # Add project details to the list under their respective cluster
            for i, project in enumerate(projects):
                all_projects.append({
                    'cluster': cluster_name,
                    'project': flatten_json(project, parent_key=f"cluster[{cluster_name}].project[{i}]")
                })

        if not all_projects:
            print("No project details found.")
            return

        # Output format handling
        if args.output == 'json':
            # JSON format
            project_output = {}
            for project in all_projects:
                cluster_name = project['cluster']
                if cluster_name not in project_output:
                    project_output[cluster_name] = []
                project_output[cluster_name].append(project['project'])
            print(json.dumps(project_output, indent=4))

        else:
            # Text output
            output_lines = []
            for project in all_projects:
                for key, value in project['project'].items():
                    output_lines.append(f"{key}: {value}")
            print("\n".join(output_lines))

    except Exception as e:
        logging.error(f"Failed to get project details: {e}")
        return None

def list_projects_by_cluster_uid(cluster_uid, client):
    """
    Fetches the list of projects for a given cluster UID using the provided API client.
    
    Args:
        cluster_uid (str): The UID of the cluster.
        client: The API client used for making requests.
    
    Returns:
        list or str: A list of projects or an error message if the request fails.
    """
    try:
        logging.info(f"Fetching projects for cluster UID: {cluster_uid}")
        projects = client.get(f"clusters/{cluster_uid}/projects")

        # Ensure the response is a list (the expected type)
        if not isinstance(projects, list):
            logging.error(f"Unexpected response type: {type(projects)}. Expected list.")
            return None

        return projects

    except Exception as e:
        logging.error(f"Failed to fetch projects for cluster {cluster_uid}: {e}")
        return None

def update_project(args, client):
    """Updates a specific project."""
    data = {}
    if args.new_name:
        data['name'] = args.new_name
    if args.description:
        data['description'] = args.description

    if not data:
        logging.error("No updates provided.")
        return None

    result = client.put(f"projects/{args.name}", data)
    logging.info(f"Project '{args.name}' updated successfully")
    return result

def delete_project(args, client):
    """Deletes a project by name."""
    success = client.delete(f"projects/{args.name}")
    if success:
        logging.info(f"Project '{args.name}' deleted successfully")
    return success
