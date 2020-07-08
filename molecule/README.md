Molecule tests for the role.

# Test Matrix

Test options "flow down" thro table unless changed.

test   | # partitions | # groups in partitions? | other
---    | ---          | ---                     | ---
test1  | 1            | N                       | 2x compute node, sequential names (default test)
test1b | 1            | N                       | 1x compute node
test1c | 1            | N                       | 2x compute nodes, nonsequential names


# Installation


# Running
To run install docker, molecule etc then:

    cd <repo_root>
    molecule test

