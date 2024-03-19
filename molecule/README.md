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


# Local Installation & Running

Local installation on a RockyLinux 8.x machine looks like:

    sudo dnf install -y podman
    sudo dnf install podman-plugins # required for DNS
    sudo yum install -y git
    git clone git@github.com:stackhpc/ansible-role-openhpc.git
    cd ansible-role-openhpc/
    python3.9 -m venv venv
    . venv/bin/activate
    pip install -U pip
    pip install -r molecule/requirements.txt
    ansible-galaxy collection install containers.podman:>=1.10.1

Build a RockyLinux 9.3 image with systemd included:

    cd ansible-role-openhpc/molecule/images
    podman build -t rocky93systemd:latest .

Run tests, e.g.:

    cd ansible-role-openhpc/
    MOLECULE_NO_LOG="false" MOLECULE_IMAGE=rockylinux:8.9 molecule test --all

where the image may be `rockylinux:8.9` or `localhost/rocky93systemd`.

Other useful options during development:
- Prevent destroying instances by using `molecule test --destroy never`
- Run only a single test using e.g. `molecule test --scenario test5`
