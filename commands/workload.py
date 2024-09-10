import json
import logging
from utils import flatten_json, get_cluster_uid, filter_json

def setup_parser(subparsers):
    """Sets up the argparse subcommands for workloads."""
    workload_parser = subparsers.add_parser('workload', help='Manage workloads')
    workload_subparsers = workload_parser.add_subparsers(dest='action', help='Action to perform')

    # workload list
    list_parser = workload_subparsers.add_parser('list', help='List all workloads in a cluster')
    list_parser.add_argument('--cluster', help='Cluster name or UID (optional, will auto-select if only one cluster exists)')
    list_parser.add_argument('--output', '-o', choices=['text', 'json'], default='text', help='Output format (default: text)')
    list_parser.add_argument('--filter', help='Comma-separated list of fields to display (e.g., "name,id")')
    list_parser.set_defaults(func=list_workloads)

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

    # workload list in cluster
    list_cluster_parser = workload_subparsers.add_parser('list-cluster', help='List all workloads in a cluster')
    list_cluster_parser.add_argument('--cluster', required=True, help='Cluster name')
    list_cluster_parser.set_defaults(func=list_workloads_in_cluster)

def list_workloads(args, client):
    """Lists all workloads in a cluster."""
    try:
        cluster_uid = get_cluster_uid(client, args.cluster)
        workloads = client.get(f"clusters/{cluster_uid}/workloads")

        # Apply filter if provided
        if args.filter:
            filters = args.filter.split(',')
            workloads = filter_json(workloads, filters)

        if args.output == 'json':
            return json.dumps(workloads, indent=4)

        flattened_workloads = []
        for i, workload in enumerate(workloads):
            flattened_workload = flatten_json(workload, parent_key=f'workload[{i}]')
            flattened_workloads.append(flattened_workload)

        output_lines = []
        for flattened_workload in flattened_workloads:
            for key, value in flattened_workload.items():
                output_lines.append(f"{key}: {value}")

        return "\n".join(output_lines)

    except Exception as e:
        return f"Error: {str(e)}"

def resume_workload(args, client):
    """Resumes a suspended workload."""
    result = client.put(f"projects/{args.project}/workloads/{args.name}/resume")
    logging.info(f"Workload '{args.name}' resumed in project '{args.project}'")
    return result

def suspend_workload(args, client):
    """Suspends a running workload."""
    result = client.put(f"projects/{args.project}/workloads/{args.name}/suspend")
    logging.info(f"Workload '{args.name}' suspended in project '{args.project}'")
    return result

def list_workloads_in_cluster(args, client):
    """Lists all workloads in a cluster."""
    workloads = client.get(f"clusters/{args.cluster}/workloads")
    return workloads
