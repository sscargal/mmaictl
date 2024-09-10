import logging
from kubernetes import client, config
from kubernetes.config.config_exception import ConfigException

def setup_parser(subparsers):
    """Sets up the argparse subcommands for displaying topologies."""
    topology_parser = subparsers.add_parser('topology', help='Display the environment topology (MMAI or Kubernetes)')
    
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
def fetch_environment_data(client):
    """
    Fetches the MMAI topology, including clusters, node groups, nodes, hardware, departments, projects, and workloads.
    Handles errors when endpoints are not found or other exceptions occur.

    Returns:
        dict: A structured dictionary representing the MMAI topology or an error message.
    """
    topology_data = {}

    try:
        # Fetch clusters
        clusters = client.get("clusters")

        if not isinstance(clusters, list) or len(clusters) == 0:
            logging.error("No clusters found.")
            return {
                "error": "No clusters found.",
                "suggestion": "Please verify that clusters are available in the system and that the API is responding correctly."
            }

        topology_data['Clusters'] = []

        for cluster in clusters:
            cluster_data = {'Cluster': cluster['name'], 'NodeGroups': [], 'Departments': []}

            try:
                # Fetch node groups
                nodegroups = client.get(f"clusters/{cluster['uid']}/nodeGroups")
                if not isinstance(nodegroups, list):
                    logging.error(f"Failed to fetch node groups for cluster {cluster['uid']}.")
                    return {
                        "error": f"Failed to fetch node groups for cluster {cluster['uid']}.",
                        "suggestion": "Please verify that the node groups endpoint is functioning correctly."
                    }

            except Exception as e:
                logging.error(f"Error fetching node groups for cluster {cluster['uid']}: {e}")
                return {
                    "error": f"Error fetching node groups for cluster {cluster['uid']}.",
                    "suggestion": f"An error occurred while fetching node groups: {str(e)}"
                }

            for nodegroup in nodegroups:
                nodegroup_data = {'NodeGroup': nodegroup['name'], 'Nodes': []}

                try:
                    # Fetch nodes for each node group
                    nodes = client.get(f"nodegroups/{nodegroup['uid']}/nodes")
                    if not isinstance(nodes, list):
                        logging.error(f"Failed to fetch nodes for node group {nodegroup['uid']}.")
                        return {
                            "error": f"Failed to fetch nodes for node group {nodegroup['uid']}.",
                            "suggestion": "Please verify that the nodes endpoint is functioning correctly."
                        }

                except Exception as e:
                    logging.error(f"Error fetching nodes for node group {nodegroup['uid']}: {e}")
                    return {
                        "error": f"Error fetching nodes for node group {nodegroup['uid']}.",
                        "suggestion": f"An error occurred while fetching nodes: {str(e)}"
                    }

                for node in nodes:
                    node_data = {
                        'Node': node['name'],
                        'CPU': f"{node['cpu']['cores']} cores",
                        'Memory': f"{node['memory']['total']} GB",
                        'Network': node['network'],
                        'Storage': node['storage'],
                        'GPUs': node.get('gpus', "None")
                    }
                    nodegroup_data['Nodes'].append(node_data)

                cluster_data['NodeGroups'].append(nodegroup_data)

            # Fetch departments
            try:
                departments = client.get(f"clusters/{cluster['uid']}/departments")
                if not isinstance(departments, list):
                    logging.error(f"Failed to fetch departments for cluster {cluster['uid']}.")
                    return {
                        "error": f"Failed to fetch departments for cluster {cluster['uid']}.",
                        "suggestion": "Please verify that the departments endpoint is functioning correctly."
                    }

            except Exception as e:
                logging.error(f"Error fetching departments for cluster {cluster['uid']}: {e}")
                return {
                    "error": f"Error fetching departments for cluster {cluster['uid']}.",
                    "suggestion": f"An error occurred while fetching departments: {str(e)}"
                }

            for department in departments:
                department_data = {'Department': department['name'], 'Projects': []}

                # Fetch projects for each department
                try:
                    projects = client.get(f"departments/{department['uid']}/projects")
                    if not isinstance(projects, list):
                        logging.error(f"Failed to fetch projects for department {department['uid']}.")
                        return {
                            "error": f"Failed to fetch projects for department {department['uid']}.",
                            "suggestion": "Please verify that the projects endpoint is functioning correctly."
                        }

                except Exception as e:
                    logging.error(f"Error fetching projects for department {department['uid']}: {e}")
                    return {
                        "error": f"Error fetching projects for department {department['uid']}.",
                        "suggestion": f"An error occurred while fetching projects: {str(e)}"
                    }

                for project in projects:
                    project_data = {'Project': project['name'], 'Workloads': []}

                    # Fetch workloads for each project
                    try:
                        workloads = client.get(f"projects/{project['uid']}/workloads")
                        if not isinstance(workloads, list):
                            logging.error(f"Failed to fetch workloads for project {project['uid']}.")
                            return {
                                "error": f"Failed to fetch workloads for project {project['uid']}.",
                                "suggestion": "Please verify that the workloads endpoint is functioning correctly."
                            }

                    except Exception as e:
                        logging.error(f"Error fetching workloads for project {project['uid']}: {e}")
                        return {
                            "error": f"Error fetching workloads for project {project['uid']}.",
                            "suggestion": f"An error occurred while fetching workloads: {str(e)}"
                        }

                    for workload in workloads:
                        project_data['Workloads'].append({'Workload': workload['name']})

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


def mmai_topology(args, client):
    """Displays the MMAI hardware/software topology in a tree view format."""
    try:
        # Fetch the MMAI topology data
        topology_data = fetch_environment_data(client)

        # Print the tree starting from the cluster
        print("MMAI Topology:")
        print_tree(topology_data)

    except Exception as e:
        logging.error(f"Error fetching MMAI topology: {str(e)}")
        return f"Error: {str(e)}"
