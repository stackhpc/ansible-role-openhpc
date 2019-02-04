[![Build Status](https://travis-ci.com/stackhpc/ansible-role-openhpc.svg?branch=master)](https://travis-ci.com/stackhpc/ansible-role-openhpc)

# stackhpc.openhpc

This Ansible role is used to install the necessary packages to have a fully functional OpenHPC cluster.

Role Variables
--------------

`openhpc_slurm_service_enabled`: checks whether `openhpc_slurm_service` is enabled

`openhpc_slurm_service`: name of the slurm service e.g. `slurmd`

`openhpc_slurm_control_host`: ansible host name of the controller e.g `"{{ groups['cluster_login'] | first }}"`

`openhpc_slurm_partitions`: list of slurm partitions

`openhpc_cluster_name`: name of the cluster

`openhpc_packages`: additional OpenHPC packages to install

`openhpc_enable`: 
* `control`: whether to enable control host
* `batch`: whether to enable compute nodes 
* `runtime`: whether to enable OpenHPC runtime

Example Playbook
----------------
 
To deploy, create a playbook which looks like this:

    ---
    - hosts:
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
          openhpc_slurm_service: slurmd
          openhpc_slurm_control_host: "{{ groups['cluster_login'] | first }}"
          openhpc_slurm_partitions: "{{ slurm_compute }}"
          openhpc_cluster_name: openhpc
          openhpc_packages: []
    ...

Example Inventory
-----------------

And an Ansible inventory as this:

    [openhpc_login]
    openhpc-login-0 ansible_host=10.60.253.40 ansible_user=centos

    [openhpc_compute]
    openhpc-compute-0 ansible_host=10.60.253.33 ansible_user=centos

    [cluster_control:children]
    openhpc_login

    [cluster_batch:children]
    openhpc_compute
