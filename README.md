[![Build Status](https://github.com/stackhpc/ansible-role-openhpc/workflows/CI/badge.svg)](https://github.com/stackhpc/ansible-role-openhpc/actions)

# stackhpc.openhpc

This Ansible role installs packages and performs configuration to provide a Slurm cluster. By default this uses packages from [OpenHPC](https://openhpc.community/) but it can also use user-provided Slurm binaries.

As a role it must be used from a playbook, for which a simple example is given below. This approach means it is totally modular with no assumptions about available networks or any cluster features except for some hostname conventions. Any desired cluster fileystem or other required functionality may be freely integrated using additional Ansible roles or other approaches.

The minimal image for nodes is a Rocky Linux 8 GenericCloud image.

## Task files
This role provides four task files which can be selected by using the `tasks_from` parameter of Ansible's `import_role` or `include_role` modules:
- `main.yml`: Runs `install-ohpc.yml` and `runtime.yml`. Default if no `tasks_from` parameter is used.
- `install-ohpc.yml`: Installs repos and packages for OpenHPC.
- `install-generic.yml`: Installs systemd units etc. for user-provided binaries.
- `runtime.yml`: Slurm/service configuration.

## Role Variables

Variables only relevant for `install-ohpc.yml` or `install-generic.yml` task files are marked as such below.

`openhpc_extra_repos`: Optional list. Extra Yum repository definitions to configure, following the format of the Ansible
[yum_repository](https://docs.ansible.com/ansible/2.9/modules/yum_repository_module.html) module.

`openhpc_slurm_service_enabled`: Optional boolean, whether to enable the appropriate slurm service (slurmd/slurmctld). Default `true`.

`openhpc_slurm_service_started`: Optional boolean. Whether to start slurm services. If set to false, all services will be stopped. Defaults to `openhpc_slurm_service_enabled`.

`openhpc_slurm_control_host`: Required string. Ansible inventory hostname (and short hostname) of the controller e.g. `"{{ groups['cluster_control'] | first }}"`.

`openhpc_slurm_control_host_address`: Optional string. IP address or name to use for the `openhpc_slurm_control_host`, e.g. to use a different interface than is resolved from `openhpc_slurm_control_host`.

`openhpc_packages`: Optional list. Additional OpenHPC packages to install (`install-ohpc.yml` only).

`openhpc_enable`:
* `control`: whether to enable control host
* `database`: whether to enable slurmdbd
* `batch`: whether to enable compute nodes
* `runtime`: whether to enable OpenHPC runtime

`openhpc_slurmdbd_host`: Optional. Where to deploy slurmdbd if are using this role to deploy slurmdbd, otherwise where an existing slurmdbd is running. This should be the name of a host in your inventory. Set this to `none` to prevent the role from managing slurmdbd. Defaults to `openhpc_slurm_control_host`.

`openhpc_munge_key_b64`: Optional. A base-64 encoded munge key. If not provided then the one generated on package install is used, but the `openhpc_slurm_control_host` must be in the play.

`openhpc_login_only_nodes`: Optional. If using "configless" mode specify the name of an ansible group containing nodes which are login-only nodes (i.e. not also control nodes), if required. These nodes will run `slurmd` to contact the control node for config.

`openhpc_module_system_install`: Optional, default true. Whether or not to install an environment module system. If true, lmod will be installed. If false, You can either supply your own module system or go without one (`install-ohpc.yml` only).

`openhpc_generic_packages`: Optional. List of system packages to install, see `defaults/main.yml` for details (`install-generic.yml` only).

`openhpc_sbin_dir`: Optional. Path to slurm daemon binaries such as `slurmctld`, default `/usr/sbin` (`install-generic.yml` only).

`openhpc_bin_dir`: Optional. Path to Slurm user binaries such as `sinfo`, default `/usr/bin` (`install-generic.yml` only).

`openhpc_lib_dir`: Optional. Path to Slurm libraries, default `/usr/lib64/slurm` (`install-generic.yml` only).

### slurm.conf

Note this role always operates in Slurm's [configless mode](https://slurm.schedmd.com/configless_slurm.html)
where the `slurm.conf` configuration file is only present on the control node.

`openhpc_nodegroups`: Optional, default `[]`. List of mappings, each defining a
unique set of homogenous nodes:
  * `name`: Required. Name of node group.
  * `ram_mb`: Optional.  The physical RAM available in each node of this group
  ([slurm.conf](https://slurm.schedmd.com/slurm.conf.html) parameter `RealMemory`)
  in MiB. This is set using ansible facts if not defined, equivalent to
  `free --mebi` total * `openhpc_ram_multiplier`.
  * `ram_multiplier`: Optional.  An override for the top-level definition
  `openhpc_ram_multiplier`. Has no effect if `ram_mb` is set.
  * `gres_autodetect`: Optional. The [hardware autodetection mechanism](https://slurm.schedmd.com/gres.conf.html#OPT_AutoDetect)
     to use for [generic resources](https://slurm.schedmd.com/gres.html).
     **NB:** A value of `'off'` (the default) must be quoted to avoid yaml
     conversion to `false`.
  * `gres`: Optional. List of dicts defining [generic resources](https://slurm.schedmd.com/gres.html).
     Not required if using `nvml` GRES autodetection. Keys/values in dicts are:
      - `conf`: A string defining the [resource specification](https://slurm.schedmd.com/slurm.conf.html#OPT_Gres_1)
        in the format `<name>:<type>:<number>`, e.g. `gpu:A100:2`.
      - `file`: A string defining device path(s) as per [File](https://slurm.schedmd.com/gres.conf.html#OPT_File),
        e.g. `/dev/nvidia[0-1]`. Not required if using any GRES autodetection.
    
    Note [GresTypes](https://slurm.schedmd.com/slurm.conf.html#OPT_GresTypes) is
    automatically set from the defined GRES or GRES autodetection. See [GRES Configuration](#gres-configuration)
    for more discussion.
  * `features`: Optional. List of [Features](https://slurm.schedmd.com/slurm.conf.html#OPT_Features) strings.
  * `node_params`: Optional. Mapping of additional parameters and values for
  [node configuration](https://slurm.schedmd.com/slurm.conf.html#lbAE).
  **NB:** Parameters which can be set via the keys above must not be included here.

  Each nodegroup will contain hosts from an Ansible inventory group named
  `{{ openhpc_cluster_name }}_{{ name }}`, where `name` is the nodegroup name.
  Note that:
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

`openhpc_gres_autodetect`: Optional. A global default for `openhpc_nodegroups.gres_autodetect`
defined above. **NB:** A value of `'off'` (the default) must be quoted to avoid
yaml conversion to `false`.

`openhpc_job_maxtime`: Maximum job time limit, default `'60-0'` (60 days), see
[slurm.conf:MaxTime](https://slurm.schedmd.com/slurm.conf.html#OPT_MaxTime).
**NB:** This should be quoted to avoid Ansible conversions.

`openhpc_cluster_name`: name of the cluster.

`openhpc_config`: Optional. Mapping of additional parameters and values for
[slurm.conf](https://slurm.schedmd.com/slurm.conf.html). Keys are slurm.conf
parameter names and values are lists or strings as appropriate. This can be
used to supplement or override the template defaults. Templated parameters can
also be removed by setting the value to the literal string `'omit'` - note
that this is *not the same* as the Ansible `omit` [special variable](https://docs.ansible.com/ansible/latest/reference_appendices/special_variables.html#term-omit).

`openhpc_cgroup_config`: Optional. Mapping of additional parameters and values for
[cgroup.conf](https://slurm.schedmd.com/cgroup.conf.html). Keys are cgroup.conf
parameter names and values are lists or strings as appropriate. This can be
used to supplement or override the template defaults. Templated parameters can
also be removed by setting the value to the literal string `'omit'` - note
that this is *not the same* as the Ansible `omit` [special variable](https://docs.ansible.com/ansible/latest/reference_appendices/special_variables.html#term-omit).

`openhpc_mpi_config`: Optional. Mapping of additional parameters and values for
[mpi.conf](https://slurm.schedmd.com/mpi.conf.html). Keys are mpi.conf
parameter names and values are lists or strings as appropriate. This can be
used to supplement or override the template defaults. Templated parameters can
also be removed by setting the value to the literal string `'omit'` - note
that this is *not the same* as the Ansible `omit` [special variable](https://docs.ansible.com/ansible/latest/reference_appendices/special_variables.html#term-omit).

`openhpc_ram_multiplier`: Optional, default `0.95`. Multiplier used in the calculation: `total_memory * openhpc_ram_multiplier` when setting `RealMemory` for the partition in slurm.conf. Can be overriden on a per partition basis using `openhpc_slurm_partitions.ram_multiplier`. Has no effect if `openhpc_slurm_partitions.ram_mb` is set.

`openhpc_state_save_location`: Optional. Absolute path for Slurm controller state (`slurm.conf` parameter [StateSaveLocation](https://slurm.schedmd.com/slurm.conf.html#OPT_StateSaveLocation))

`openhpc_slurmd_spool_dir`: Optional. Absolute path for slurmd state (`slurm.conf` parameter [SlurmdSpoolDir](https://slurm.schedmd.com/slurm.conf.html#OPT_SlurmdSpoolDir))

`openhpc_slurm_conf_template`: Optional. Path of Jinja template for `slurm.conf` configuration file. Default is `slurm.conf.j2` template in role. **NB:** The required templating is complex, if just setting specific parameters use `openhpc_config` intead.

`openhpc_slurm_conf_path`: Optional. Path to template `slurm.conf` configuration file to. Default `/etc/slurm/slurm.conf`

`openhpc_gres_template`: Optional. Path of Jinja template for `gres.conf` configuration file. Default is `gres.conf.j2` template in role.

`openhpc_cgroup_template`: Optional. Path of Jinja template for `cgroup.conf` configuration file. Default is `cgroup.conf.j2` template in role.

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

### slurmdbd

When the slurm database daemon (`slurmdbd`) is enabled by setting
`openhpc_enable.database` to `true` the following options must be configured.
See documentation for [slurmdbd.conf](https://slurm.schedmd.com/slurmdbd.conf.html)
for more details.

`openhpc_slurmdbd_port`: Port for slurmdb to listen on, defaults to `6819`.

`openhpc_slurmdbd_mysql_host`: Hostname or IP Where mariadb is running, defaults to `openhpc_slurm_control_host`.

`openhpc_slurmdbd_mysql_database`: Database to use for accounting, defaults to `slurm_acct_db`.

`openhpc_slurmdbd_mysql_password`: Password for authenticating with the database. You must set this variable.

`openhpc_slurmdbd_mysql_username`: Username for authenticating with the database, defaults to `slurm`.

Before starting `slurmdbd`, the role will check if a database upgrade is
required to due to a Slurm major version upgrade and carry it out if so.
Slurm versions before 24.11 do not support this check and so no upgrade will
occur. The following variables control behaviour during this upgrade:

`openhpc_slurm_accounting_storage_client_package`: Optional. String giving the
name of the database client package to install, e.g. `mariadb`. Default `mysql`.

`openhpc_slurm_accounting_storage_backup_cmd`: Optional. String (possibly
multi-line) giving a command for `ansible.builtin.shell` to run a backup of the
Slurm database before performing the databse upgrade. Default is the empty
string which performs no backup.

`openhpc_slurm_accounting_storage_backup_host`: Optional. Inventory hostname
defining host to run the backup command. Default is `openhpc_slurm_accounting_storage_host`.

`openhpc_slurm_accounting_storage_backup_become`: Optional. Whether to run the
backup command as root. Default `true`.

`openhpc_slurm_accounting_storage_service`: Optional. Name of systemd service
for the accounting storage database, e.g. `mysql`. If this is defined this
service is stopped before the backup and restarted after, to allow for physical
backups. Default is the empty string, which does not stop/restart any service.

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

Assume an inventory containing two types of compute node (login and
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
...
```

Firstly `openhpc_nodegroups` maps to these inventory groups and applies any
node-level parameters - in this case the `largemem` nodes have 2x cores
reserved for some reason:

```yaml
openhpc_cluster_name: hpc
openhpc_nodegroups:
  - name: general
  - name: large
    node_params:
      CoreSpecCount: 2
```

Now two partitions can be configured using `openhpc_partitions`: A default
partition for testing jobs with a short timelimit and no large memory nodes,
and another partition with all hardware and longer job runtime for "production"
jobs:

```yaml
openhpc_partitions:
  - name: test
    nodegroups:
      - general
    maxtime: '1:0:0' # 1 hour
    default: 'YES'
  - name: general
    nodegroups:
      - general
      - large
    maxtime: '2-0' # 2 days
    default: 'NO'
```
Users will select the partition using `--partition` argument and request nodes
with appropriate memory using the `--mem` option for `sbatch` or `srun`.

## GRES Configuration

### Autodetection

Some autodetection mechanisms require recompilation of Slurm packages to link
against external libraries. Examples are shown in the sections below.

#### Recompiling Slurm binaries against the [NVIDIA Management library](https://developer.nvidia.com/management-library-nvml)

This allows using `openhpc_gres_autodetect: nvml` or `openhpc_nodegroup.gres_autodetect: nvml`.

First, [install the complete cuda toolkit from NVIDIA](https://docs.nvidia.com/cuda/cuda-installation-guide-linux/).
You can then recompile the slurm packages from the source RPMS as follows:

```sh
dnf download --source slurm-slurmd-ohpc
rpm -i slurm-ohpc-*.src.rpm
cd /root/rpmbuild/SPECS
dnf builddep slurm.spec
rpmbuild -bb -D "_with_nvml --with-nvml=/usr/local/cuda-12.8/targets/x86_64-linux/" slurm.spec | tee /tmp/build.txt
```

NOTE: This will need to be adapted for the version of CUDA installed (12.8 is used in the example).

The RPMs will be created in `/root/rpmbuild/RPMS/x86_64/`. The method to distribute these RPMs to
each compute node is out of scope of this document.

## GRES configuration examples

For NVIDIA GPUs, `nvml` GRES autodetection can be used. This requires:
- The relevant GPU nodes to have the `nvidia-smi` binary installed
- Slurm to be compiled against the NVIDIA management library as above

Autodetection can then be enabled using either for all nodegroups:

```yaml
openhpc_gres_autodetection: nvml
```

or for individual nodegroups e.g:
```yaml
openhpc_nodegroups:
  - name: example
    gres_autodetection: nvml
  ...
```

In either case no additional configuration of GRES is required. Any nodegroups
with NVIDIA GPUs will automatically get `gpu` GRES defined for all GPUs found.
GPUs within a node do not need to be the same model but nodes in a nodegroup
must be homogenous. GRES types are set to the autodetected model names e.g. `H100`.

For `nvml` GRES autodetection per-nodegroup `gres_autodetection` and/or `gres` keys
can be still be provided. These can be used to disable/override the default
autodetection method, or to allow checking autodetected resources against
expectations as described by [gres.conf documentation](https://slurm.schedmd.com/gres.conf.html).

Without any autodetection, a GRES configuration for NVIDIA GPUs might be:

```
openhpc_nodegroups:
  - name: general
  - name: gpu
    gres:
      - conf: gpu:H200:2
        file: /dev/nvidia[0-1]
```

Note that the `nvml` autodetection is special in this role. Other autodetection
mechanisms, e.g. `nvidia` or `rsmi` allow the `gres.file:` specification to be
omitted but still require `gres.conf:` to be defined.

<b id="slurm_ver_footnote">1</b> Slurm 20.11 removed `accounting_storage/filetxt` as an option. This version of Slurm was introduced in OpenHPC v2.1 but the OpenHPC repos are common to all OpenHPC v2.x releases. [↩](#accounting_storage)
