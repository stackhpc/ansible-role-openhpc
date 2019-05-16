[![Build Status](https://travis-ci.com/stackhpc/ansible-role-openhpc.svg?branch=master)](https://travis-ci.com/stackhpc/ansible-role-openhpc)

# stackhpc.openhpc

This Ansible role is used to install the necessary packages to have a fully functional OpenHPC cluster.

Role Variables
--------------

`openhpc_slurm_service_enabled`: checks whether `openhpc_slurm_service` is enabled

`openhpc_slurm_service`: name of the slurm service e.g. `slurmd`

`openhpc_slurm_control_host`: ansible host name of the controller e.g `"{{ groups['cluster_control'] | first }}"`

`openhpc_slurm_partitions`: list of slurm partitions

`openhpc_cluster_name`: name of the cluster

`openhpc_packages`: additional OpenHPC packages to install

`openhpc_enable`: 
* `control`: whether to enable control host
* `batch`: whether to enable compute nodes 
* `runtime`: whether to enable OpenHPC runtime
* `drain`: whether to drain a compute nodes
* `resume`: whether to resume a compute nodes

Example Inventory
-----------------

And an Ansible inventory as this:

    [openhpc_login]
    openhpc-login-0 ansible_host=10.60.253.40 ansible_user=centos

    [openhpc_compute]
    openhpc-compute-0 ansible_host=10.60.253.31 ansible_user=centos
    openhpc-compute-1 ansible_host=10.60.253.32 ansible_user=centos

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
            runtime: true
          openhpc_slurm_service_enabled: true
          openhpc_slurm_service: slurmd
          openhpc_slurm_control_host: "{{ groups['cluster_control'] | first }}"
          openhpc_slurm_partitions:
            - name: "compute"
              flavor: "compute-A"
              image: "CentOS7.5-OpenHPC"
              num_nodes: 8
              user: "centos"
          openhpc_cluster_name: openhpc
          openhpc_packages: []
    ...


To drain nodes, for example, before scaling down the cluster to 6 nodes:

    ---
    - hosts: openstack
      gather_facts: false
      
      roles:
        - role: stackhpc.cluster-infra
          cluster_name: "{{ cluster_name }}"
          cluster_state: query
          cluster_params:
            cluster_groups: "{{ cluster_groups }}"
      tasks:
        - name: Count the number of compute nodes per slurm partition
          vars:
            partition: "{{ cluster_group.output_value | selectattr('group', 'equalto', item.name) | list }}"
            openhpc_slurm_partitions:
              - name: "compute"
                flavor: "compute-A"
                image: "CentOS7.5-OpenHPC"
                num_nodes: 6
                user: "centos"
            openhpc_cluster_name: openhpc
          set_fact:
            desired_state: "{{ (( partition | first).nodes | map(attribute='name') | list )[:item.num_nodes] + desired_state | default([]) }}"
          when: partition | length > 0
          with_items: "{{ openhpc_slurm_partitions }}"
        - debug: var=desired_state

    - hosts: cluster_batch
      become: yes
      roles:
        - role: stackhpc.openhpc
          desired_state: "{{ hostvars['localhost']['desired_state'] | default([]) }}"
          openhpc_slurm_control_host: "{{ groups['cluster_control'] | first }}"
          openhpc_enable:
            drain: "{{ inventory_hostname not in desired_state }}"
            resume: "{{ inventory_hostname in desired_state }}"
    ...

