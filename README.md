[![Build Status](https://github.com/stackhpc/ansible-role-openhpc/workflows/CI/badge.svg)](https://github.com/stackhpc/ansible-role-openhpc/actions)

# stackhpc.openhpc

This Ansible role installs packages and performs configuration to provide an OpenHPC v2.x Slurm cluster.

As a role it must be used from a playbook, for which a simple example is given below. This approach means it is totally modular with no assumptions about available networks or any cluster features except for some hostname conventions. Any desired cluster fileystem or other required functionality may be freely integrated using additional Ansible roles or other approaches.

The minimal image for nodes is a RockyLinux 8 GenericCloud image.

## Role Variables

`openhpc_extra_repos`: Optional list. Extra Yum repository definitions to configure, following the format of the Ansible
[yum_repository](https://docs.ansible.com/ansible/2.9/modules/yum_repository_module.html) module. Respected keys for
each list element:
* `name`: Required
* `description`: Optional
* `file`: Required
* `baseurl`: Optional
* `metalink`: Optional
* `mirrorlist`: Optional
* `gpgcheck`: Optional
* `gpgkey`: Optional

`openhpc_slurm_service_enabled`: boolean, whether to enable the appropriate slurm service (slurmd/slurmctld).

`openhpc_slurm_service_started`: Optional boolean. Whether to start slurm services. If set to false, all services will be stopped. Defaults to `openhpc_slurm_service_enabled`.

`openhpc_slurm_control_host`: Required string. Ansible inventory hostname (and short hostname) of the controller e.g. `"{{ groups['cluster_control'] | first }}"`.

`openhpc_slurm_control_host_address`: Optional string. IP address or name to use for the `openhpc_slurm_control_host`, e.g. to use a different interface than is resolved from `openhpc_slurm_control_host`.

`openhpc_packages`: additional OpenHPC packages to install.

`openhpc_enable`:
* `control`: whether to enable control host
* `database`: whether to enable slurmdbd
* `batch`: whether to enable compute nodes
* `runtime`: whether to enable OpenHPC runtime

`openhpc_slurmdbd_host`: Optional. Where to deploy slurmdbd if are using this role to deploy slurmdbd, otherwise where an existing slurmdbd is running. This should be the name of a host in your inventory. Set this to `none` to prevent the role from managing slurmdbd. Defaults to `openhpc_slurm_control_host`.

`openhpc_slurm_configless`: Optional, default false. If true then slurm's ["configless" mode](https://slurm.schedmd.com/configless_slurm.html) is used.

`openhpc_munge_key`: Optional. Define a munge key to use. If not provided then one is generated but the `openhpc_slurm_control_host` must be in the play.

`openhpc_login_only_nodes`: Optional. If using "configless" mode specify the name of an ansible group containing nodes which are login-only nodes (i.e. not also control nodes), if required. These nodes will run `slurmd` to contact the control node for config.

`openhpc_module_system_install`: Optional, default true. Whether or not to install an environment module system. If true, lmod will be installed. If false, You can either supply your own module system or go without one.

### slurm.conf

`openhpc_nodegroups`: Optional, default `[]`. List of mappings, each defining a
unique set of homogenous nodes:
  * `name`: Required. Name of node group.
  * `ram_mb`: Optional.  The physical RAM available in each node of this group
  ([slurm.conf](https://slurm.schedmd.com/slurm.conf.html) parameter `RealMemory`)
  in MiB. This is set using ansible facts if not defined, equivalent to
  `free --mebi` total * `openhpc_ram_multiplier`.
  * `ram_multiplier`: Optional.  An override for the top-level definition
  `openhpc_ram_multiplier`. Has no effect if `ram_mb` is set.
  * `gres`: Optional. List of dicts defining [generic resources](https://slurm.schedmd.com/gres.html). Each dict must define:
      - `conf`: A string with the [resource specification](https://slurm.schedmd.com/slurm.conf.html#OPT_Gres_1) but requiring the format `<name>:<type>:<number>`, e.g. `gpu:A100:2`. Note the `type` is an arbitrary string.
      - `file`: A string with the [File](https://slurm.schedmd.com/gres.conf.html#OPT_File) (path to device(s)) for this resource, e.g. `/dev/nvidia[0-1]` for the above example.
    Note [GresTypes](https://slurm.schedmd.com/slurm.conf.html#OPT_GresTypes) must be set in `openhpc_config` if this is used.
  * `features`: Optional. List of [Features](https://slurm.schedmd.com/slurm.conf.html#OPT_Features) strings.
  * `node_params`: Optional. Mapping of additional parameters and values for
  [node configuration](https://slurm.schedmd.com/slurm.conf.html#lbAE).
  **NB:** Parameters which can be set via the keys above must not be included here.

  Each nodegroup will contain hosts from an Ansible inventory group named
  `{{ openhpc_cluster_name }}_{{ group_name}}`. Note that:
  - Each host may only appear in one nodegroup.
  - Hosts in a nodegroup are assumed to be homogenous in terms of processor and memory.
  - Hosts may have arbitrary hostnames, but these should be lowercase to avoid a
    mismatch between inventory and actual hostname.
  - An inventory group may be missing or empty, in which case the node group
    contains no hosts.
  - If the inventory group is not empty the play must contain at least one host.
    This is used to set `Sockets`, `CoresPerSocket`, `ThreadsPerCore` and
    optionally `RealMemory` for the nodegroup.

`openhpc_partitions`: Optional. List of mappings, each defining a
partition. Each partition mapping may contain:
  * `name`: Required. Name of partition.
  * `nodegroups`: Optional. List of node group names. If omitted, the node group
     with the same name as the partition is used.
  * `default`: Optional.  A boolean flag for whether this partion is the default.  Valid settings are `YES` and `NO`.
  * `maxtime`: Optional.  A partition-specific time limit overriding `openhpc_job_maxtime`.
  * `partition_params`: Optional. Mapping of additional parameters and values for
  [partition configuration](https://slurm.schedmd.com/slurm.conf.html#SECTION_PARTITION-CONFIGURATION).
  **NB:** Parameters which can be set via the keys above must not be included here.

If this variable is not set one partition per nodegroup is created, with default
partition configuration for each.

`openhpc_job_maxtime`: Maximum job time limit, default `'60-0'` (60 days), see
[slurm.conf:MaxTime](https://slurm.schedmd.com/slurm.conf.html#OPT_MaxTime).
**NB:** This should be quoted to avoid Ansible conversions.

`openhpc_cluster_name`: name of the cluster.

`openhpc_config`: Optional. Mapping of additional parameters and values for `slurm.conf`. Note these will override any included in `templates/slurm.conf.j2`.

`openhpc_ram_multiplier`: Optional, default `0.95`. Multiplier used in the calculation: `total_memory * openhpc_ram_multiplier` when setting `RealMemory` for the partition in slurm.conf. Can be overriden on a per partition basis using `openhpc_slurm_partitions.ram_multiplier`. Has no effect if `openhpc_slurm_partitions.ram_mb` is set.

`openhpc_state_save_location`: Optional. Absolute path for Slurm controller state (`slurm.conf` parameter [StateSaveLocation](https://slurm.schedmd.com/slurm.conf.html#OPT_StateSaveLocation))

#### Accounting

By default, no accounting storage is configured. OpenHPC v1.x and un-updated OpenHPC v2.0 clusters support file-based accounting storage which can be selected by setting the role variable `openhpc_slurm_accounting_storage_type` to `accounting_storage/filetxt`<sup id="accounting_storage">[1](#slurm_ver_footnote)</sup>. Accounting for OpenHPC v2.1 and updated OpenHPC v2.0 clusters requires the Slurm database daemon, `slurmdbd` (although job completion may be a limited alternative, see [below](#Job-accounting). To enable accounting:

* Configure a mariadb or mysql server as described in the slurm accounting [documentation](https://slurm.schedmd.com/accounting.html) on one of the nodes in your inventory and set `openhpc_enable.database `to `true` for this node.
* Set `openhpc_slurm_accounting_storage_type` to `accounting_storage/slurmdbd`.
* Configure the variables for `slurmdbd.conf` below.

The role will take care of configuring the following variables for you:

`openhpc_slurm_accounting_storage_host`: Where the accounting storage service is running i.e where slurmdbd running.

`openhpc_slurm_accounting_storage_port`: Which port to use to connect to the accounting storage.

`openhpc_slurm_accounting_storage_user`: Username for authenticating with the accounting storage.

`openhpc_slurm_accounting_storage_pass`: Mungekey or database password to use for authenticating.

For more advanced customisation or to configure another storage type, you might want to modify these values manually.

#### Job accounting

This is largely redundant if you are using the accounting plugin above, but will give you basic
accounting data such as start and end times. By default no job accounting is configured.

`openhpc_slurm_job_comp_type`: Logging mechanism for job accounting. Can be one of
`jobcomp/filetxt`, `jobcomp/none`, `jobcomp/elasticsearch`.

`openhpc_slurm_job_acct_gather_type`: Mechanism for collecting job accounting data. Can be one
 of `jobacct_gather/linux`, `jobacct_gather/cgroup` and `jobacct_gather/none`.

`openhpc_slurm_job_acct_gather_frequency`: Sampling period for job accounting (seconds).

`openhpc_slurm_job_comp_loc`: Location to store the job accounting records. Depends on value of
`openhpc_slurm_job_comp_type`, e.g for `jobcomp/filetxt` represents a path on disk.

### slurmdbd.conf

The following options affect `slurmdbd.conf`. Please see the slurm [documentation](https://slurm.schedmd.com/slurmdbd.conf.html) for more details.
You will need to configure these variables if you have set `openhpc_enable.database` to `true`.

`openhpc_slurmdbd_port`: Port for slurmdb to listen on, defaults to `6819`.

`openhpc_slurmdbd_mysql_host`: Hostname or IP Where mariadb is running, defaults to `openhpc_slurm_control_host`.

`openhpc_slurmdbd_mysql_database`: Database to use for accounting, defaults to `slurm_acct_db`.

`openhpc_slurmdbd_mysql_password`: Password for authenticating with the database. You must set this variable.

`openhpc_slurmdbd_mysql_username`: Username for authenticating with the database, defaults to `slurm`.

## Facts

This role creates local facts from the live Slurm configuration, which can be
accessed (with facts gathering enabled) using `ansible_local.slurm`. As per the
`scontrol show config` man page, uppercase keys are derived parameters and keys
in mixed case are from from config files. Note the facts are only refreshed
when this role is run.

## Example

### Simple

The following creates a cluster with a a single partition `compute`
containing two nodes:

```ini
# inventory/hosts:
[hpc_login]
cluster-login-0

[hpc_compute]
cluster-compute-0
cluster-compute-1

[hpc_control]
cluster-control
```

```yaml
#playbook.yml
---
- hosts: all
  become: yes
  tasks:
    - import_role:
        name: stackhpc.openhpc
      vars:
        openhpc_cluster_name: hpc
        openhpc_enable:
          control: "{{ inventory_hostname in groups['cluster_control'] }}"
          batch: "{{ inventory_hostname in groups['cluster_compute'] }}"
          runtime: true
        openhpc_slurm_control_host: "{{ groups['cluster_control'] | first }}"
        openhpc_nodegroups:
          - name: compute
        openhpc_partitions:
          - name: compute
---
```

### Multiple nodegroups

This example shows how partitions can span multiple types of compute node.

This example inventory describes three types of compute node (login and
control nodes are omitted for brevity):

```ini
# inventory/hosts:
...
[hpc_general]
# standard compute nodes
cluster-general-0
cluster-general-1

[hpc_large]
# large memory nodes
cluster-largemem-0
cluster-largemem-1

[hpc_gpu]
# GPU nodes
cluster-a100-0
cluster-a100-1
...
```

Firstly the `openhpc_nodegroups` is set to capture these inventory groups and
apply any node-level parameters - in this case the `largemem` nodes have
2x cores reserved for some reason, and GRES is configured for the GPU nodes:

```yaml
openhpc_cluster_name: hpc
openhpc_nodegroups:
  - name: general
  - name: large
    node_params:
      CoreSpecCount: 2
  - name: gpu
    gres:
      - conf: gpu:A100:2
        file: /dev/nvidia[0-1]
```

Now two partitions can be configured - a default one with a short timelimit and
no large memory nodes for testing jobs, and another with all hardware and longer
job runtime for "production" jobs:

```yaml
openhpc_partitions:
  - name: test
    nodegroups:
      - general
      - gpu
    maxtime: '1:0:0' # 1 hour
    default: 'YES'
  - name: general
    nodegroups:
      - general
      - large
      - gpu
    maxtime: '2-0' # 2 days
    default: 'NO'
```
Users will select the partition using `--partition` argument and request nodes
with appropriate memory or GPUs using the `--mem` and `--gres` or `--gpus*`
options for `sbatch` or `srun`.

Finally here some additional configuration must be provided for GRES:
```yaml
openhpc_config:
  GresTypes:
    -gpu
```

<b id="slurm_ver_footnote">1</b> Slurm 20.11 removed `accounting_storage/filetxt` as an option. This version of Slurm was introduced in OpenHPC v2.1 but the OpenHPC repos are common to all OpenHPC v2.x releases. [↩](#accounting_storage)
