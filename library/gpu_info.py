#!/usr/bin/python

# Copyright: (c) 2025, StackHPC
# Apache 2 License

from ansible.module_utils.basic import AnsibleModule

ANSIBLE_METADATA = {
    "metadata_version": "0.1",
    "status": ["preview"],
    "supported_by": "community",
}

DOCUMENTATION = """
---
module: gpu_info
short_description: Gathers information about NVIDIA GPUs on a node
description:
    - "This module queries for NVIDIA GPUs using `nvidia-smi` and returns information about them. It is designed to fail gracefully if `nvidia-smi` is not present or if the NVIDIA driver is not running."
options: {}
requirements:
    - "python >= 3.6"
author:
    - Steve Brasier, StackHPC
"""

EXAMPLES = """
"""

import collections

def run_module():
    module_args = dict({})

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    try:
        rc ,stdout, stderr = module.run_command("nvidia-smi --query-gpu=name --format=noheader", check_rc=False, handle_exceptions=False)
    except FileNotFoundError: # nvidia-smi not installed
        rc = None
    
    # nvidia-smi return codes: https://docs.nvidia.com/deploy/nvidia-smi/index.html
    gpus = {}
    result = {'changed': False, 'gpus': gpus, 'gres':''}
    if rc == 0:
        # stdout line e.g. 'NVIDIA H200' for each GPU
        lines = [line for line in stdout.splitlines() if line != ''] # defensive: currently no blank lines
        models = [line.split()[1] for line in lines]
        gpus.update(collections.Counter(models))
    elif rc == 9:
        # nvidia-smi installed but driver not running
        pass
    elif rc == None:
        # nvidia-smi not installed
        pass
    else:
        result.update({'stdout': stdout, 'rc': rc, 'stderr':stderr})
        module.fail_json(**result)
    
    if len(gpus) > 0:
        gres_parts = []
        for model, count in gpus.items():
            gres_parts.append(f"gpu:{model}:{count}")
        result.update({'gres': ','.join(gres_parts)})

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
