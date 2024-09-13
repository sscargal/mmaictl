import json
import logging
from utils import flatten_json, get_cluster_uid, filter_json

def setup_parser(subparsers):
    """Sets up the argparse subcommands for workloads."""
    workload_parser = subparsers.add_parser(
        'workload', 
        description='Manage Workloads in the MMAI Platform.',
        help='Manage workloads'
    )
    workload_subparsers = workload_parser.add_subparsers(dest='action', help='Action to perform')

    # workload list
    list_parser = workload_subparsers.add_parser('list', help='List all workloads in a cluster')
    list_parser.add_argument('--cluster', help='Cluster name or UID (optional, will auto-select if only one cluster exists)')
    list_parser.add_argument('--project', help='Project name (optional, specify to filter by project)')
    list_parser.add_argument('--filter', help='Comma-separated list of fields to display (e.g., "name,id")')
    list_parser.add_argument('--output', '-o', choices=['text', 'dot', 'json'], default='text', help='Output format (default: text)')
    list_parser.set_defaults(func=list_workloads)

    # workload get
    get_parser = workload_subparsers.add_parser('get', help='Get all workload properties in a cluster or project')
    get_parser.add_argument('--cluster', help='Cluster name or UID (optional, will auto-select if only one cluster exists)')
    get_parser.add_argument('--project', help='Project name (optional, specify to filter by project)')
    get_parser.add_argument('--filter', help='Comma-separated list of fields to display (e.g., "name,id")')
    get_parser.add_argument('--output', '-o', choices=['text', 'dot', 'json'], default='text', help='Output format (default: text)')
    get_parser.set_defaults(func=get_workloads)

    # workload resume
    resume_parser = workload_subparsers.add_parser('resume', help='Resume a suspended workload')
    resume_parser.add_argument('--project', required=True, help='Project name')
    resume_parser.add_argument('--name', required=True, help='Workload name')
    resume_parser.set_defaults(func=resume_workload)

    # workload suspend
    suspend_parser = workload_subparsers.add_parser('suspend', help='Suspend a running workload')
    suspend_parser.add_argument('--project', required=True, help='Project name')
    suspend_parser.add_argument('--name', required=True, help='Workload name')
    suspend_parser.set_defaults(func=suspend_workload)


def list_workloads(args, client):
    """Lists all workloads in a cluster."""
    try:
        cluster_uid = get_cluster_uid(client, args.cluster)
        
        # If project is specified, fetch workloads for that project within the cluster
        if args.project:
            workloads = client.get(f"clusters/{cluster_uid}/projects/{args.project}/workloads")
        else:
            workloads = client.get(f"clusters/{cluster_uid}/workloads")

        # Fetch the cluster name
        cluster_info = client.get(f"clusters/{cluster_uid}")
        cluster_name = cluster_info['name']

        # Apply filter if provided
        if args.filter:
            filters = args.filter.split(',')
            workloads = filter_json(workloads, filters)

        if args.output == 'json':
            # JSON format should show only cluster name and workload names
            simplified_output = {
                "cluster": cluster_name,
                "workloads": [workload['name'] for workload in workloads]
            }
            print(json.dumps(simplified_output, indent=4))
        elif args.output == 'dot':
            # Dot notation format
            output_lines = [f"cluster[{cluster_name}].workload[{i}].name: {workload['name']}" for i, workload in enumerate(workloads)]
            print("\n".join(output_lines))
        else:  # Default output: text format, show workload names under each cluster
            output_lines = [f"[{cluster_name}]"]
            output_lines.extend([workload['name'] for workload in workloads])
            print("\n".join(output_lines))

    except Exception as e:
        logging.error(f"Failed to fetch workloads: {e}")
        return None


def get_workloads(args, client):
    """Gets all workload properties in a cluster or project."""
    try:
        cluster_uid = get_cluster_uid(client, args.cluster)
        if args.project:
            workloads = client.get(f"clusters/{cluster_uid}/projects/{args.project}/workloads")
        else:
            workloads = client.get(f"clusters/{cluster_uid}/workloads")

        # Apply filter if provided
        if args.filter:
            filters = args.filter.split(',')
            workloads = filter_json(workloads, filters)

        if args.output == 'json':
            print(json.dumps(workloads, indent=4))
        elif args.output == 'dot':
            flattened_workloads = []
            for i, workload in enumerate(workloads):
                flattened_workload = flatten_json(workload, parent_key=f'cluster[{cluster_uid}].workload[{i}]')
                flattened_workloads.append(flattened_workload)
            
            output_lines = []
            for workload in flattened_workloads:
                for key, value in workload.items():
                    output_lines.append(f"{key}: {value}")
            print("\n".join(output_lines))
        else:  # text output
            flattened_workloads = []
            for i, workload in enumerate(workloads):
                flattened_workload = flatten_json(workload, parent_key=f'workload[{i}]')
                flattened_workloads.append(flattened_workload)

            output_lines = []
            for workload in flattened_workloads:
                for key, value in workload.items():
                    output_lines.append(f"{key}: {value}")
            print("\n".join(output_lines))

    except Exception as e:
        logging.error(f"Failed to fetch workloads: {e}")
        return None


def resume_workload(args, client):
    """Resumes a suspended workload."""
    result = client.put(f"projects/{args.project}/workloads/{args.name}/resume")
    logging.info(f"Workload '{args.name}' resumed in project '{args.project}'")
    print(f"Workload '{args.name}' resumed in project '{args.project}'")
    return result

def suspend_workload(args, client):
    """Suspends a running workload."""
    result = client.put(f"projects/{args.project}/workloads/{args.name}/suspend")
    logging.info(f"Workload '{args.name}' suspended in project '{args.project}'")
    print(f"Workload '{args.name}' suspended in project '{args.project}'")
    return result
