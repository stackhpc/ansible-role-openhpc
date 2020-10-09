[![Build Status](https://travis-ci.com/stackhpc/ansible-role-openhpc.svg?branch=master)](https://travis-ci.com/stackhpc/ansible-role-openhpc)

# stackhpc.openhpc

This Ansible role installs packages and performs configuration to provide a fully functional OpenHPC cluster. It can also be used to drain and resume nodes.

As a role it must be used from a playbook, for which a simple example is given below. This approach means it is totally modular with no assumptions about available networks or any cluster features except for some hostname conventions. Any desired cluster fileystem or other required functionality may be freely integrated using additional Ansible roles or other approaches.

## Role Variables

`openhpc_slurm_service_enabled`: boolean, whether to enable the appropriate slurm service (slurmd/slurmctld)

`openhpc_slurm_control_host`: ansible host name of the controller e.g `"{{ groups['cluster_control'] | first }}"`

`openhpc_packages`: additional OpenHPC packages to install

`openhpc_slurmdbd_host`: Where to deploy slurmdbd if are using this role to deploy slurmdbd, otherwise where
an existing slurmdbd is running. This should be the name of a host in your inventory. Set this to `none` to
prevent the role from managing slurmdbd.

`openhpc_enable`:
* `control`: whether to enable control host
* `database`: whether to enable slurmdbd
* `batch`: whether to enable compute nodes
* `drain`: whether to drain compute nodes
* `resume`: whether to resume compute nodes

 `openhpc_reconfigure_mode`:
 * `hard`:
    Perform a reconfigure of slurm which requires restart of daemons, i.e.
    - changes to AuthType, ControlMach, PluginDir, StateSaveLocation, SlurmctldHost, SlurmctldPort, or SlurmdPort
    - addition or removal of nodes from the cluster
    NB this deliberately does not use `scontrol shutdown` as a bad config may mean slurmctld cannot contact the slurmds
 * `soft`:
    Perform a reconfigure of slurm which does not requires restart of daemons, i.e. any changes except
    those listed in hard. This avoids interrupting the scheduler.
    NB: This requires communication between the daemons so if that is broken use hard reconfigure

`openhpc_allow_restart`: Flag to prevent daemon restarts. You can use this in conjunction with `scontrol reconfigure` to
perform a more graceful config reload.

`openhpc_slurm_conf`: (optional) mapping possibly containing:

  * `location`: Path for slurm configuration file (default: /etc/slurm/slurm.conf) - parent directories will be created if required.
  * `shared_fs`: bool, whether this is a filesystem shared (writably) across the cluster (default: false)

Note that slurm daemons will **not** automatically be restarted if the location is changed as this affects the scheduler loop.

`openhpc_munge_key`: (optional) mapping possibly containing:

  * `location`: Path for munge key (default: /etc/munge/munge.key) - parent directories will be created if required.
  * `shared_fs`: bool, whether this is a filesystem shared (writably) across the cluster (default: false)

Munge daemons will automatically be restarted if changes are made.

`openhpc_actions`: (optional) string or list of strings containing one or more of the following values:
- `install` to install packages only
- `configure` to configure slurm
- `start` to start slurm and munge daemons
- `post` configure the running cluster (requires the cluster to be started)
- `drain` to drain selected nodes (set `openhpc_enable.drain == True` on relevant nodes)
- `resume` to resume selected nodes (set `openhpc_enable.resume == True` on relevant nodes)

The order in which these actions is specified is ignored. The default is to run all these actions.

Note that a soft reconfiguration avoids disrupting the scheduler, but the following situations require a hard reconfiguration:
- Addition or removal of nodes from the cluster
- Loss of communications between daemons e.g. due to misconfiguration
- Changes to AuthType, ControlMach, PluginDir, StateSaveLocation, SlurmctldHost, SlurmctldPort, or SlurmdPort in `slurm.conf`

Running and queued jobs should be unaffected by either type of reconfiguration.

### slurm.conf

The following options affect `slurm.conf`. Please see the slurm (documentation)[https://slurm.schedmd.com/slurm.conf.html] for more details.

`openhpc_slurm_partitions`: list of one or more slurm partitions.  Each partition may contain the following values:
* `groups`: If there are multiple node groups that make up the partition, a list of group objects can be defined here.
  Otherwise, `groups` can be omitted and the following attributes can be defined in the partition object:
  * `name`: The name of the nodes within this group.
  * `cluster_name`: Optional.  An override for the top-level definition `openhpc_cluster_name`.
  * `ram_mb`: Optional.  The physical RAM available in each server of this group ([slurm.conf](https://slurm.schedmd.com/slurm.conf.html) parameter `RealMemory`). This is set to the Slurm default of `1` if not defined.

  For each group (if used) or partition there must be an ansible inventory group `<cluster_name>_<group_name>`. All nodes in this inventory group will be added to the group/partition. Nodes may have arbitrary hostnames but these should be lowercase to avoid a mismatch between inventory and actual hostname.

* `default`: Optional.  A boolean flag for whether this partion is the default.  Valid settings are `YES` and `NO`.
* `maxtime`: Optional.  A partition-specific time limit in hours, minutes and seconds ([slurm.conf](https://slurm.schedmd.com/slurm.conf.html) parameter `MaxTime`).  The default value is
  given by `openhpc_job_maxtime`.

`openhpc_job_maxtime`: A maximum time job limit in hours, minutes and seconds.  The default is `24:00:00`.

`openhpc_cluster_name`: name of the cluster

#### Accounting

By default, the accounting plugin will use the `accounting_storage/filetxt` storage type. However,
this only supports a subset of `sacct` commands.

To deploy and configure `slurmdbd`:

* Configure a mariadb or mysql server as documented in the slurm accounting (documentation)[https://slurm.schedmd.com/accounting.html]
* Set `openhpc_enable.database` to `true` for one of the nodes in your inventory
* Set `openhpc_slurm_accounting_storage_type` to `accounting_storage/slurmdbd`.
* Configure the variables for `slurmdbd.conf` below.

The role will take care of configuring the following variables for you:

`openhpc_slurm_accounting_storage_host`: Where the accounting storage service is running i.e where slurmdbd running.

`openhpc_slurm_accounting_storage_port`: Which port to use to connect to the accounting storage.

`openhpc_slurm_accounting_storage_type`: How accounting records are stored. Can be one of `accounting_storage/none`,
 `accounting_storage/slurmdbd` or  `accounting_storage/filetxt`.

`openhpc_slurm_accounting_storage_user`: Username for authenticating with the accounting storage.

`openhpc_slurm_accounting_storage_pass`: Mungekey or database password to use for authenticating.
with the accounting storage

For more advanced customisation or to configure another storage type, you might want to modify these values manually.

#### Job accounting

This is largely redundant if you are using the accounting plugin above, but will give you basic
accounting data such as start and end times.

`openhpc_slurm_job_acct_gather_type`: Mechanism for collecting job accounting data. Can be one
 of `jobacct_gather/linux`, `jobacct_gather/cgroup` and `jobacct_gather/none`

`openhpc_slurm_job_acct_gather_frequency`: Sampling period for job accounting (seconds)

`openhpc_slurm_job_comp_type`: Logging mechanism for job accounting. Can be one of
`jobcomp/filetxt`, `jobcomp/none`, `jobcomp/elasticsearch`.

`openhpc_slurm_job_comp_loc`: Location to store the job accounting records. Depends on value of
`openhpc_slurm_job_comp_type`, e.g for `jobcomp/filetxt` represents a path on disk.

### slurmdbd.conf

The following options affect `slurmdbd.conf`. Please see the slurm (documentation)[https://slurm.schedmd.com/slurmdbd.conf.html] for more details.
You will need to configure these variables if you have set `openhpc_enable.database` to `true`.

`openhpc_slurmdbd_port`: Port for slurmdb to listen on, defaults to `6819`

`openhpc_slurmdbd_mysql_host`: Hostname or IP Where mariadb is running, defaults to `openhpc_slurm_control_host`.

`openhpc_slurmdbd_mysql_database`: Database to use for accounting, defaults to `slurm_acct_db`

`openhpc_slurmdbd_mysql_password`: Password for authenticating with the database. You must set this variable.

`openhpc_slurmdbd_mysql_username`: Username for authenticating with the database, defaults to `slurm`

Example Inventory
-----------------

And an Ansible inventory as this:

    [openhpc_login]
    openhpc-login-0 ansible_host=10.60.253.40 ansible_user=centos

    [openhpc_compute]
    openhpc-compute-0 ansible_host=10.60.253.31 ansible_user=centos
    openhpc-compute-1 ansible_host=10.60.253.32 ansible_user=centos

    [cluster_login:children]
    openhpc_login

    [cluster_control:children]
    openhpc_login

    [cluster_batch:children]
    openhpc_compute

Example Playbooks
----------------

To deploy, create a playbook which looks like this:

    ---
    - hosts:
      - cluster_login
      - cluster_control
      - cluster_batch
      become: yes
      roles:
        - role: openhpc
          openhpc_enable:
            control: "{{ inventory_hostname in groups['cluster_control'] }}"
            batch: "{{ inventory_hostname in groups['cluster_batch'] }}"
          openhpc_slurm_service_enabled: true
          openhpc_slurm_control_host: "{{ groups['cluster_control'] | first }}"
          openhpc_slurm_partitions:
            - name: "compute"
              num_nodes: 8
          openhpc_cluster_name: openhpc
          openhpc_packages: []
    ...

Note that the "compute" of the openhpc_slurm_partition name and the
openhpc_cluster_name are used to generate the compute node in the
slurm config of openhpc-compute-[0:7]. Your inventory entries
for that partition must match that convention.

To drain nodes, for example, before scaling down the cluster to 6 nodes:

    ---
    - hosts: openstack
      gather_facts: false
      vars:
        partition: "{{ cluster_group.output_value | selectattr('group', 'equalto', item.name) | list }}"
        openhpc_slurm_partitions:
          - name: "compute"
            flavor: "compute-A"
            image: "CentOS7.5-OpenHPC"
            num_nodes: 6
            user: "centos"
        openhpc_cluster_name: openhpc
      roles:
        # Our stackhpc.cluster-infra role can be invoked in `query` mode which
        # looks up the state of the cluster by querying the Heat API.
        - role: stackhpc.cluster-infra
          cluster_name: "{{ cluster_name }}"
          cluster_state: query
          cluster_params:
            cluster_groups: "{{ cluster_groups }}"
      tasks:
        # Given that the original cluster that was created had 8 nodes and the
        # cluster we want to create has 6 nodes, the computed desired_state
        # variable stores the list of instances to leave untouched.
        - name: Count the number of compute nodes per slurm partition
          set_fact:
            desired_state: "{{ (( partition | first).nodes | map(attribute='name') | list )[:item.num_nodes] + desired_state | default([]) }}"
          when: partition | length > 0
          with_items: "{{ openhpc_slurm_partitions }}"
        - debug: var=desired_state

    - hosts: cluster_batch
      become: yes
      vars:
        desired_state: "{{ hostvars['localhost']['desired_state'] | default([]) }}"
      roles:
        # Now, the stackhpc.openhpc role is invoked in drain/resume modes where
        # the instances in desired_state are resumed if in a drained state and
        # drained if in a resumed state.
        - role: stackhpc.openhpc
          openhpc_slurm_control_host: "{{ groups['cluster_control'] | first }}"
          openhpc_enable:
            drain: "{{ inventory_hostname not in desired_state }}"
            resume: "{{ inventory_hostname in desired_state }}"
    ...


CentOS 8 and OpenHPC 2
----------------------

To deploy OpenHPC 2 on CentOS 8, you must first enable the CentOS PowerTools repo
(this ships as standard, but disabled).  To enable PowerTools:

```
sudo dnf config-manager --set-enabled PowerTools
```
