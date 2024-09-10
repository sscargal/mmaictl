import json
import logging
from utils import flatten_json, get_cluster_uid, filter_json

def setup_parser(subparsers):
    """Sets up the argparse subcommands for projects."""
    project_parser = subparsers.add_parser('project', help='Manage projects')
    project_subparsers = project_parser.add_subparsers(dest='action', help='Action to perform')

    # project add
    add_parser = project_subparsers.add_parser('add', help='Add a new project')
    add_parser.add_argument('--name', required=True, help='Name of the project')
    add_parser.add_argument('--description', help='Description of the project')
    add_parser.set_defaults(func=add_project)

    # project list
    list_parser = project_subparsers.add_parser('list', help='List all projects in a cluster')
    list_parser.add_argument('--cluster', help='Cluster name or UID (optional, will auto-select if only one cluster exists)')
    list_parser.add_argument('--output', '-o', choices=['text', 'json'], default='text', help='Output format (default: text)')
    list_parser.add_argument('--filter', help='Comma-separated list of fields to display (e.g., "name,description")')
    list_parser.set_defaults(func=list_projects)

    # project get
    get_parser = project_subparsers.add_parser('get', help='Get a project by name')
    get_parser.add_argument('name', help='Name of the project')
    get_parser.set_defaults(func=get_project)

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
    """Lists all projects in a cluster."""
    try:
        cluster_uid = get_cluster_uid(client, args.cluster)
        projects = client.get(f"clusters/{cluster_uid}/projects")

        # Apply filter if provided
        if args.filter:
            filters = args.filter.split(',')
            projects = filter_json(projects, filters)

        if args.output == 'json':
            return json.dumps(projects, indent=4)

        flattened_projects = []
        for i, project in enumerate(projects):
            flattened_project = flatten_json(project, parent_key=f'project[{i}]')
            flattened_projects.append(flattened_project)

        output_lines = []
        for flattened_project in flattened_projects:
            for key, value in flattened_project.items():
                output_lines.append(f"{key}: {value}")

        return "\n".join(output_lines)

    except Exception as e:
        return f"Error: {str(e)}"
    
def get_project(args, client):
    """Retrieves a specific project by name."""
    project = client.get(f"projects/{args.name}")
    return project

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
