Molecule tests for the role.

# Test Matrix

Test options in "Other" column flow down through table unless changed.

Test   | # Partitions | Groups in partitions?   | Other
---    | ---          | ---                     | ---
test1  | 1            | N                       | 2x compute node, sequential names (default test), config on all nodes
test1b | 1            | N                       | 1x compute node
test1c | 1            | N                       | 2x compute nodes, nonsequential names
test2  | 2            | N                       | 4x compute node, sequential names
test3  | 1            | Y                       | -
test4  | 1            | N                       | 2x compute node, accounting enabled
test5  | 1            | N                       | As for #1 but configless
test6  | 1            | N                       | 0x compute nodes, configless
test7  | 1            | N                       | 1x compute node, no login node so specified munge key, configless (checks image build should work)
test8  | 1            | N                       | 2x compute node, 2x login-only nodes, configless
test9  | 1            | N                       | As test8 but uses `--limit=testohpc-control,testohpc-compute-0` and checks login nodes still end up in slurm.conf
test10 | 1            | N                       | As for #5 but then tries to add an additional node
test11 | 1            | N                       | As for #5 but then deletes a node (actually changes the partition due to molecule/ansible limitations)
test12 | 1            | N                       | As for #5 but enabling job completion and testing `sacct -c`
test13 | 1            | N                       | As for #5 but tests `openhpc_config` variable.
test14 | 1            | N                       | As for #5 but also tests `extra_nodes` via State=DOWN nodes.
test15 | 1            | N                       | No compute nodes.

# Local Installation & Running

Local installation on a RockyLinux 8.x machine looks like:

    sudo dnf install -y podman
    sudo yum install -y git
    git clone git@github.com:stackhpc/ansible-role-openhpc.git
    cd ansible-role-openhpc/
    python3.9 -m venv venv
    . venv/bin/activate
    pip install -U pip
    pip install -r molecule/requirements.txt
    ansible-galaxy collection install containers.podman:>=1.10.1

Then to run tests, e.g.::

    cd ansible-role-openhpc/
    MOLECULE_IMAGE=centos:7 molecule test --all # NB some won't work as require OpenHPC v2.x (-> CentOS 8.x) features - see `.github/workflows/ci.yml`
    MOLECULE_IMAGE=rockylinux:8.6 molecule test --all

**NB:** If the host network has an MTU smaller than 1500 (the docker default), check `molecule.yml` for the relevant test contains `DOCKER_MTU`, then prepend `DOCKER_MTU=<mtu>` to your command. If you have already run molecule you will need to destroy the instances and run `docker network prune` before retrying.

During development you may want to:

- See some debugging information by prepending:

        MOLECULE_NO_LOG="false" ...

- Prevent destroying insstances using:

        molecule test --destroy never
