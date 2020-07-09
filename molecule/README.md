Molecule tests for the role.

# Test Matrix

Test options "flow down" thro table unless changed.

test   | # partitions | # groups in partitions? | other
---    | ---          | ---                     | ---
test1  | 1            | N                       | 2x compute node, sequential names (default test)
test1b | 1            | N                       | 1x compute node
test1c | 1            | N                       | 2x compute nodes, nonsequential names
test2  | 2            | N                       | 4x compute node, sequential names
test3  | 1            | Y                       |

# Local Installation & Running

Local installation on a Centos7 machine looks like:

    sudo yum install -y gcc python3-pip python3-devel openssl-devel python3-libselinux
    sudo yum install -y docker-ce docker-ce-cli containerd.io
    sudo yum install -y yum-utils
    sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
    sudo yum install -y docker-ce docker-ce-cli containerd.io
    pip3 install -r molecule/requirements.txt --user
    
    sudo systemctl start docker
    sudo usermod -aG docker ${USER}
    newgrp docker
    docker run hello-world # test docker works without sudo
    
    sudo yum install -y git
    git clone git@github.com:stackhpc/ansible-role-openhpc.git
    cd ansible-role-openhpc/
    
Then to run all tests:

    cd ansible-role-openhpc/
    molecule test --all

