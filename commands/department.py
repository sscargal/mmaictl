import json
import logging
from utils import flatten_json, get_cluster_uid, filter_json

def setup_parser(subparsers):
    """Sets up the argparse subcommands for departments."""
    department_parser = subparsers.add_parser('department', help='Manage departments')
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
    """Lists all departments in a cluster."""
    try:
        cluster_uid = get_cluster_uid(client, args.cluster)
        departments = client.get(f"clusters/{cluster_uid}/departments")

        # If filters are provided, apply them
        if args.filter:
            filters = args.filter.split(',')
            departments = filter_json(departments, filters)

        if args.output == 'json':
            return json.dumps(departments, indent=4)

        flattened_departments = []
        for i, department in enumerate(departments):
            flattened_department = flatten_json(department, parent_key=f'department[{i}]')
            flattened_departments.append(flattened_department)

        output_lines = []
        for flattened_department in flattened_departments:
            for key, value in flattened_department.items():
                output_lines.append(f"{key}: {value}")

        return "\n".join(output_lines)

    except Exception as e:
        return f"Error: {str(e)}"

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
