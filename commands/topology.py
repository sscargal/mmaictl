import logging
from kubernetes import client, config
from kubernetes.config.config_exception import ConfigException
from .department import list_departments, list_departments_by_cluster_uid
from .nodegroup import list_nodegroups, list_nodegroups_by_cluster_uid
from .project import list_projects, list_projects_by_cluster_uid
import logging

def setup_parser(subparsers):
    """Sets up the argparse subcommands for displaying topologies."""
    topology_parser = subparsers.add_parser(
        'topology', 
        description='Display the MMAI or Kubernetes topology.',
        help='Display the environment topology (MMAI or Kubernetes)'
    )
    
    # Options for selecting the type of topology
    topology_parser.add_argument('--k8s', action='store_true', help='Show Kubernetes cluster topology')
    topology_parser.add_argument('--mmai', action='store_true', help='Show MMAI hardware/software topology')
    topology_parser.set_defaults(func=topology_view)

def topology_view(args, client):
    """Displays the selected topology based on the user's choice."""
    try:
        if args.k8s:
            print("Displaying Kubernetes topology...")
            k8s_topology(args)  # Call function to display Kubernetes topology
        elif args.mmai:
            print("Displaying MMAI hardware/software topology...")
            mmai_topology(args, client)  # Call function to display MMAI topology
        else:
            print("Error: You must specify either --k8s or --mmai to display the topology.")
    
    except Exception as e:
        logging.error(f"Error displaying topology: {str(e)}")
        return f"Error: {str(e)}"


# Kubernetes Topology Function
def fetch_k8s_topology():
    """
    Fetches the Kubernetes topology, including namespaces, nodes, pods, and services.
    Handles errors related to kubeconfig loading, permissions, and API access.
    
    Returns:
        dict: A structured dictionary representing the Kubernetes cluster topology or an error message.
    """
    topology_data = {}

    try:
        # Load Kubernetes configuration
        config.load_kube_config()  # This will use the default kubeconfig (~/.kube/config)

    except FileNotFoundError:
        # Handle missing kubeconfig file
        logging.error("Kubeconfig file not found. Please make sure the kubeconfig file exists at '~/.kube/config' or provide a valid file using the KUBECONFIG environment variable.")
        return {
            "error": "Kubeconfig file not found.",
            "suggestion": "Please make sure the kubeconfig file exists at '~/.kube/config' or set the KUBECONFIG environment variable to the correct file location."
        }
    
    except ConfigException as e:
        # Handle invalid kubeconfig file or other config-related issues
        logging.error(f"Invalid kubeconfig file: {e}. Ensure the file is correctly formatted and accessible.")
        return {
            "error": "Invalid kubeconfig file.",
            "suggestion": "Please ensure that the kubeconfig file is correctly formatted and accessible. You can check it with `kubectl config view` or recreate it from the Kubernetes cluster."
        }

    except PermissionError:
        # Handle file permission errors
        logging.error("Permission denied: Unable to read the kubeconfig file. Please check the file permissions.")
        return {
            "error": "Permission denied to read kubeconfig.",
            "suggestion": "Ensure the kubeconfig file has the correct permissions. Use `chmod 600 ~/.kube/config` to set appropriate permissions."
        }

    try:
        # Initialize Kubernetes API client
        v1 = client.CoreV1Api()

        # Fetch all namespaces
        namespaces = v1.list_namespace().items
        topology_data['Namespaces'] = []

        for namespace in namespaces:
            ns_data = {'Namespace': namespace.metadata.name, 'Nodes': []}

            # Fetch nodes in the cluster
            nodes = v1.list_node().items
            for node in nodes:
                node_data = {'Node': node.metadata.name, 'Pods': []}

                # Fetch all pods in this namespace
                pods = v1.list_namespaced_pod(namespace.metadata.name).items
                for pod in pods:
                    # Check if the pod is scheduled on this node
                    if pod.spec.node_name == node.metadata.name:
                        pod_data = {
                            'Pod': pod.metadata.name,
                            'Containers': [container.name for container in pod.spec.containers]
                        }
                        node_data['Pods'].append(pod_data)

                ns_data['Nodes'].append(node_data)

            # Fetch services in the namespace
            services = v1.list_namespaced_service(namespace.metadata.name).items
            ns_data['Services'] = [{'Service': svc.metadata.name} for svc in services]

            topology_data['Namespaces'].append(ns_data)

        return topology_data

    except client.exceptions.ApiException as e:
        # Handle Kubernetes API errors (e.g., authentication issues)
        logging.error(f"Kubernetes API error: {e}")
        return {
            "error": "Kubernetes API error.",
            "suggestion": "Please verify your kubeconfig file and ensure you have access to the Kubernetes cluster. Try running `kubectl get nodes` to confirm."
        }

    except Exception as e:
        # Handle any other unexpected errors
        logging.error(f"Unexpected error: {e}")
        return {
            "error": "Unexpected error occurred.",
            "suggestion": f"An unexpected error occurred: {str(e)}. Please check your environment and try again."
        }


def print_tree(data, indent=""):
    """
    Recursively prints the tree structure for the Kubernetes topology or MMAI topology.
    
    Args:
        data (dict): The structured data representing the topology.
        indent (str): Indentation for tree levels.
    """
    for key, value in data.items():
        if isinstance(value, dict):
            print(f"{indent}{key}:")
            print_tree(value, indent + "│   ")
        elif isinstance(value, list):
            print(f"{indent}{key}:")
            for item in value:
                print_tree(item, indent + "│   ")
        else:
            print(f"{indent}{key}: {value}")


def k8s_topology(args):
    """Displays the Kubernetes cluster topology in a tree view format."""
    try:
        # Fetch Kubernetes topology data
        topology_data = fetch_k8s_topology()

        # Print the tree starting from the cluster level
        print("Kubernetes Cluster:")
        print_tree(topology_data)

    except Exception as e:
        logging.error(f"Error fetching Kubernetes topology: {str(e)}")
        return f"Error: {str(e)}"


# MMAI Topology Function
def fetch_mmai_topology(client):
    """
    Fetches the MMAI topology, including clusters, node groups, nodes, hardware, departments, projects, and workloads.
    Uses the existing list functions to obtain information and build the tree structure.
    
    Returns:
        dict: A structured dictionary representing the MMAI topology or an error message.
    """
    topology_data = {}

    try:
        # Fetch clusters
        clusters = client.get("clusters")
        logging.info(f"Clusters fetched: {clusters}")

        if not isinstance(clusters, list) or len(clusters) == 0:
            logging.error("No clusters found.")
            return {
                "error": "No clusters found.",
                "suggestion": "Please verify that clusters are available in the system and that the API is responding correctly."
            }

        topology_data['Clusters'] = []

        for cluster in clusters:
            if 'uid' in cluster and 'name' in cluster:
                cluster_uid = cluster['uid']
                cluster_name = cluster['name']
                logging.info(f"Processing cluster {cluster_name} with UID {cluster_uid}")
            else:
                logging.error(f"Cluster data missing 'uid' or 'name': {cluster}")
                continue

            cluster_data = {'Cluster': cluster_name, 'NodeGroups': [], 'Departments': [], 'Projects': []}

            # Fetch node groups using list_nodegroups_by_cluster_uid
            nodegroups = list_nodegroups_by_cluster_uid(cluster_uid, client)
            logging.info(f"Node groups fetched for cluster {cluster_uid}: {nodegroups}")
            
            if not nodegroups:
                logging.error(f"Failed to fetch node groups for cluster {cluster_uid}.")
                return {
                    "error": f"Failed to fetch node groups for cluster {cluster_uid}.",
                    "suggestion": "Please verify that the node groups endpoint is functioning correctly."
                }

            for nodegroup in nodegroups:
                if not isinstance(nodegroup, dict):
                    logging.error(f"Expected dictionary for node group, got {type(nodegroup)}: {nodegroup}")
                    continue

                logging.info(f"Processing node group {nodegroup['name']}")
                nodegroup_data = {
                    'NodeGroup': nodegroup['name'],
                    'Nodes': nodegroup.get('nodes', []),
                    'Resources': nodegroup.get('resources', {}),
                    'Reserved': nodegroup.get('reserved', {})
                }
                cluster_data['NodeGroups'].append(nodegroup_data)

            # Fetch departments using list_departments_by_cluster_uid
            departments = list_departments_by_cluster_uid(cluster_uid, client)
            logging.info(f"Departments fetched for cluster {cluster_uid}: {departments}")
            
            if not departments:
                logging.error(f"Failed to fetch departments for cluster {cluster_uid}.")
                return {
                    "error": f"Failed to fetch departments for cluster {cluster_uid}.",
                    "suggestion": "Please verify that the departments endpoint is functioning correctly."
                }

            for department in departments:
                if not isinstance(department, dict):
                    logging.error(f"Expected dictionary for department, got {type(department)}: {department}")
                    continue

                logging.info(f"Processing department {department['name']}")
                department_data = {'Department': department['name'], 'Projects': []}

                # Fetch projects for the entire cluster using list_projects_by_cluster_uid
                projects = list_projects_by_cluster_uid(cluster_uid, client)
                logging.info(f"Projects fetched for cluster {cluster_uid}: {projects}")
                
                if not projects:
                    logging.error(f"Failed to fetch projects for cluster {cluster_uid}.")
                    return {
                        "error": f"Failed to fetch projects for cluster {cluster_uid}.",
                        "suggestion": "Please verify that the projects endpoint is functioning correctly."
                    }

                for project in projects:
                    if not isinstance(project, dict):
                        logging.error(f"Expected dictionary for project, got {type(project)}: {project}")
                        continue

                    logging.info(f"Processing project {project['name']}")
                    project_data = {
                        'Project': project['name'],
                        'PriorityClass': project['priorityClass'],
                        'Reservations': project['reservations'],
                        'UsedQuotas': project['usedQuotas'],
                        'NumberOfAdmittedWorkloads': project['numberOfAdmittedWorkloads'],
                        'NumberOfPendingWorkloads': project['numberOfPendingWorkloads'],
                    }
                    department_data['Projects'].append(project_data)
                
                cluster_data['Departments'].append(department_data)

            topology_data['Clusters'].append(cluster_data)

        return topology_data

    except Exception as e:
        # Handle any other unexpected errors
        logging.error(f"Unexpected error occurred: {e}")
        return {
            "error": "Unexpected error occurred.",
            "suggestion": f"An unexpected error occurred: {str(e)}. Please check your environment and try again."
        }

def print_topology_data(topology_data):
    """
    Prints the fetched topology data as a tree structure with proper indentation, including node resource details.
    
    Args:
        topology_data (dict): A dictionary representing the MMAI topology.
    """
    try:
        print("MMAI Topology:")
        if 'Clusters' not in topology_data or not isinstance(topology_data['Clusters'], list):
            logging.error("Invalid topology data: 'Clusters' key missing or not a list")
            return

        for cluster in topology_data['Clusters']:
            if not isinstance(cluster, dict):
                logging.error(f"Expected dictionary for cluster, got {type(cluster)}: {cluster}")
                continue

            print(f"Clusters:")
            print(f"│   Cluster: {cluster.get('Cluster', 'N/A')}")

            # Process NodeGroups with indentation
            if 'NodeGroups' in cluster and isinstance(cluster['NodeGroups'], list):
                print("│   │   NodeGroups:")
                for nodegroup in cluster['NodeGroups']:
                    if isinstance(nodegroup, dict):
                        print(f"│   │   │   NodeGroup: {nodegroup.get('NodeGroup', 'N/A')}")
                        if 'Nodes' in nodegroup and isinstance(nodegroup['Nodes'], list):
                            print("│   │   │   │   Nodes:")
                            for node in nodegroup['Nodes']:
                                print(f"│   │   │   │   │   {node}")
                                
                                # Assuming the resource information is available in the node structure
                                # Display CPUs, Memory, and GPUs
                                cpu_count = nodegroup.get('Resources', {}).get('cpu', 'Unknown')
                                memory_capacity = nodegroup.get('Resources', {}).get('memory', 'Unknown')
                                gpus = nodegroup.get('Resources', {}).get('gpu', {})
                                
                                # Assume GPU details (e.g., model) are in the gpu dictionary
                                gpu_count = gpus.get('nvidia.com/gpu', '0')
                                
                                # Display node resources (CPUs, Memory, GPUs)
                                print(f"│   │   │   │   │   │   CPUs: {cpu_count}")
                                print(f"│   │   │   │   │   │   Memory: {memory_capacity} GiB")
                                print(f"│   │   │   │   │   │   GPUs: {gpu_count}")
                    else:
                        logging.error(f"Expected dictionary for nodegroup, got {type(nodegroup)}: {nodegroup}")
            else:
                logging.error("NodeGroups missing or invalid in cluster data")

            # Process Departments with indentation
            if 'Departments' in cluster and isinstance(cluster['Departments'], list):
                print("│   │   Departments:")
                for department in cluster['Departments']:
                    if isinstance(department, dict):
                        print(f"│   │   │   Department: {department.get('Department', 'N/A')}")
                        if 'Projects' in department and isinstance(department['Projects'], list):
                            print("│   │   │   │   Projects:")
                            for project in department['Projects']:
                                if isinstance(project, dict):
                                    print(f"│   │   │   │   │   Project: {project.get('Project', 'N/A')}")
                                else:
                                    logging.error(f"Expected dictionary for project, got {type(project)}: {project}")
                    else:
                        logging.error(f"Expected dictionary for department, got {type(department)}: {department}")
            else:
                logging.error("Departments missing or invalid in cluster data")

    except Exception as e:
        logging.error(f"Error fetching MMAI topology: {e}")


def mmai_topology(args, client):
    """Displays the MMAI hardware/software topology in a tree view format."""
    try:
        # Fetch the MMAI topology data
        topology_data = fetch_mmai_topology(client)

        # Print the tree starting from the cluster
        print_topology_data(topology_data)

    except Exception as e:
        logging.error(f"Error fetching MMAI topology: {str(e)}")
        return f"Error: {str(e)}"
