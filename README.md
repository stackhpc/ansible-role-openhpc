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

`openhpc_slurm_partitions`: Optional. List of one or more slurm partitions, default `[]`.  Each partition may contain the following values:
* `groups`: If there are multiple node groups that make up the partition, a list of group objects can be defined here.
  Otherwise, `groups` can be omitted and the following attributes can be defined in the partition object:
  * `name`: The name of the nodes within this group.
  * `cluster_name`: Optional.  An override for the top-level definition `openhpc_cluster_name`.
  * `extra_nodes`: Optional. A list of additional node definitions, e.g. for nodes in this group/partition not controlled by this role. Each item should be a dict, with keys/values as per the ["NODE CONFIGURATION"](https://slurm.schedmd.com/slurm.conf.html#lbAE) docs for slurm.conf. Note the key `NodeName` must be first.
  * `ram_mb`: Optional.  The physical RAM available in each node of this group ([slurm.conf](https://slurm.schedmd.com/slurm.conf.html) parameter `RealMemory`) in MiB. This is set using ansible facts if not defined, equivalent to `free --mebi` total * `openhpc_ram_multiplier`.
  * `ram_multiplier`: Optional.  An override for the top-level definition `openhpc_ram_multiplier`. Has no effect if `ram_mb` is set.
  * `gres`: Optional. List of dicts defining [generic resources](https://slurm.schedmd.com/gres.html). Each dict must define:
      - `conf`: A string with the [resource specification](https://slurm.schedmd.com/slurm.conf.html#OPT_Gres_1) but requiring the format `<name>:<type>:<number>`, e.g. `gpu:A100:2`. Note the `type` is an arbitrary string.
      - `file`: A string with the [File](https://slurm.schedmd.com/gres.conf.html#OPT_File) (path to device(s)) for this resource, e.g. `/dev/nvidia[0-1]` for the above example.

    Note [GresTypes](https://slurm.schedmd.com/slurm.conf.html#OPT_GresTypes) must be set in `openhpc_config` if this is used.

* `default`: Optional.  A boolean flag for whether this partion is the default.  Valid settings are `YES` and `NO`.
* `maxtime`: Optional.  A partition-specific time limit following the format of [slurm.conf](https://slurm.schedmd.com/slurm.conf.html) parameter `MaxTime`.  The default value is
  given by `openhpc_job_maxtime`. The value should be quoted to avoid Ansible conversions.
* `partition_params`: Optional. Mapping of additional parameters and values for [partition configuration](https://slurm.schedmd.com/slurm.conf.html#SECTION_PARTITION-CONFIGURATION).

For each group (if used) or partition any nodes in an ansible inventory group `<cluster_name>_<group_name>` will be added to the group/partition. Note that:
- Nodes may have arbitrary hostnames but these should be lowercase to avoid a mismatch between inventory and actual hostname.
- Nodes in a group are assumed to be homogenous in terms of processor and memory.
- An inventory group may be empty or missing, but if it is not then the play must contain at least one node from it (used to set processor information).
- Nodes may not appear in more than one group.

`openhpc_job_maxtime`: Maximum job time limit, default `'60-0'` (60 days). See [slurm.conf](https://slurm.schedmd.com/slurm.conf.html) parameter `MaxTime` for format. The default is 60 days. The value should be quoted to avoid Ansible conversions.

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

## Example Inventory

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

## Example Playbooks

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
            runtime: true
          openhpc_slurm_service_enabled: true
          openhpc_slurm_control_host: "{{ groups['cluster_control'] | first }}"
          openhpc_slurm_partitions:
            - name: "compute"
          openhpc_cluster_name: openhpc
          openhpc_packages: []
    ...

---

<b id="slurm_ver_footnote">1</b> Slurm 20.11 removed `accounting_storage/filetxt` as an option. This version of Slurm was introduced in OpenHPC v2.1 but the OpenHPC repos are common to all OpenHPC v2.x releases. [↩](#accounting_storage)
