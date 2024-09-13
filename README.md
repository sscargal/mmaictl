Here’s a sample `README.md` file for your project that includes a general introduction, installation instructions, and usage examples for all the subcommands:

---

# MMAI Command-Line Tool

MMAI is a command-line tool to manage platform resources like clusters, departments, node groups, projects, and workloads. It provides a convenient interface to interact with the MMAI API and perform operations such as listing, updating, and deleting platform resources.

## Table of Contents
- [Installation](#installation)
- [Usage](#usage)
  - [General Options](#general-options)
  - [Cluster Subcommand](#cluster-subcommand)
  - [Department Subcommand](#department-subcommand)
  - [NodeGroup Subcommand](#nodegroup-subcommand)
  - [Project Subcommand](#project-subcommand)
  - [Workload Subcommand](#workload-subcommand)
  - [Billing Subcommand](#billing-subcommand)
  - [Topology Subcommand](#topology-subcommand)
  - [Node Subcommand](#node-subcommand)
- [License](#license)

---

## Installation

### Prerequisites
- Python 3.6 or higher

### Install Dependencies

1. Clone this repository:
```bash
git clone https://github.com/your-username/mmaictl.git
cd mmaictl
```

2. Install the required Python packages:
```bash
pip install -r requirements.txt
```

3. (Optional) Enable tab completion by running:
```bash
activate-global-python-argcomplete --dest=/etc/bash_completion.d/
```

4. (Optional) Add tab completion for the `mmaictl` command in your `.bashrc`:
```bash
echo 'eval "$(register-python-argcomplete ./mmaictl.py)"' >> ~/.bashrc
source ~/.bashrc
```

## Usage

```bash
./mmaictl.py [OPTIONS] <subcommand> <action> [ARGUMENTS]

mmaictl.py [-h] [--api-url API_URL] [--token TOKEN] [-v] [--quiet]
                  {cluster,department,nodegroup,project,workload,billing,topology,node} ...

mmaictl: Command-line utility to manage platform resources like clusters, departments, and node groups

positional arguments:
  {cluster,department,nodegroup,project,workload,billing,topology,node}
                        Object to manage
    cluster             Manage clusters
    department          Manage departments
    nodegroup           Manage node groups
    project             Manage projects
    workload            Manage workloads
    billing             Get billing details for departments
    topology            Display the environment topology (MMAI or Kubernetes)
    node                Manage nodes in clusters

options:
  -h, --help            show this help message and exit
  --api-url API_URL     Base URL for the API
  --token TOKEN         Authentication token
  -v, --verbose         Increase verbosity (can be used multiple times)
  --quiet               Enable quiet mode (minimal output)
```

### General Options:
- `--api-url API_URL`: Specify the base API URL.
- `--token TOKEN`: Specify the authentication token.
- `-v, --verbose`: Increase verbosity (can be used multiple times).
- `--quiet`: Run in quiet mode (minimal output).

### Cluster Subcommand

The `cluster` subcommand manages clusters in the MMAI platform.

#### Actions:

1. **List all clusters**:
```bash
./mmaictl.py cluster list
```

2. **Add a new cluster**:
```bash
./mmaictl.py cluster add --name <cluster-name>
```

3. **Get a cluster by UID**:
```bash
./mmaictl.py cluster get --uid <cluster-uid>
```

4. **Update a cluster property**:
```bash
./mmaictl.py cluster set <cluster-name> <property=value>
# Example:
./mmaictl.py cluster set my-cluster name=newClusterName
```

5. **Delete a cluster by UID**:
```bash
./mmaictl.py cluster delete --uid <cluster-uid>
```

### Department Subcommand

The `department` subcommand manages departments in a cluster.

#### Actions:

1. **List all departments in a cluster**:
```bash
./mmaictl.py department list --cluster <cluster-name>
```

2. **Add a new department**:
```bash
./mmaictl.py department add --cluster <cluster-name> --name <department-name>
```

3. **Get a department by name**:
```bash
./mmaictl.py department get --cluster <cluster-name> --name <department-name>
```

4. **Delete a department by name**:
```bash
./mmaictl.py department delete --cluster <cluster-name> --name <department-name>
```

### NodeGroup Subcommand

The `nodegroup` subcommand manages node groups in a cluster.

#### Actions:

1. **List all node groups in a cluster**:
```bash
./mmaictl.py nodegroup list --cluster <cluster-name>
```

2. **Add a new node group**:
```bash
./mmaictl.py nodegroup add --cluster <cluster-name> --name <nodegroup-name>
```

3. **Get a node group by name**:
```bash
./mmaictl.py nodegroup get --cluster <cluster-name> --name <nodegroup-name>
```

4. **Delete a node group by name**:
```bash
./mmaictl.py nodegroup delete --cluster <cluster-name> --name <nodegroup-name>
```

### Project Subcommand

The `project` subcommand manages projects in a cluster.

#### Actions:

1. **List all projects in a cluster**:
```bash
./mmaictl.py project list --cluster <cluster-name>
```

2. **Add a new project**:
```bash
./mmaictl.py project add --cluster <cluster-name> --department <department-name> --name <project-name>
```

3. **Get a project by name**:
```bash
./mmaictl.py project get --cluster <cluster-name> --name <project-name>
```

4. **Delete a project by name**:
```bash
./mmaictl.py project delete --cluster <cluster-name> --name <project-name>
```

### Workload Subcommand

The `workload` subcommand manages workloads in a project.

#### Actions:

1. **List all workloads in a project**:
```bash
./mmaictl.py workload list --cluster <cluster-name> --project <project-name>
```

2. **Resume a workload**:
```bash
./mmaictl.py workload resume --cluster <cluster-name> --project <project-name> --workload <workload-id>
```

3. **Suspend a workload**:
```bash
./mmaictl.py workload suspend --cluster <cluster-name> --project <project-name> --workload <workload-id>
```

### Billing Subcommand

The `billing` subcommand retrieves billing information for departments.

#### Actions:

1. **Get billing information per department**:
```bash
./mmaictl.py billing department --name <department-name>
```

### Topology Subcommand

The `topology` subcommand displays the MMAI hardware/software or Kubernetes topology.

#### Actions:

1. **Display the MMAI topology**:
```bash
./mmaictl.py topology --mmai
```

2. **Display the Kubernetes topology**:
```bash
./mmaictl.py topology --k8s
```

### Node Subcommand

The `node` subcommand manages nodes in a cluster.

#### Actions:

1. **List all nodes in a cluster or all clusters**:
```bash
./mmaictl.py node list --cluster <cluster-name>  # Or omit --cluster to list nodes from all clusters
```

---

### Notes:
- Ensure you have access to the MMAI API server at `http://<hostname or ip address>:32323/v1`.
- For more detailed usage, refer to the `--help` option for each subcommand.