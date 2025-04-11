# Copyright (c) 2019 StackHPC Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

# NB: To test this from the repo root run:
#   ansible-playbook -i tests/inventory -i tests/inventory-mock-groups tests/filter.yml

from ansible import errors
import jinja2
import re

# Pattern to match a hostname with numerical ending
pattern = re.compile("^(.*\D(?=\d))(\d+)$")

def _get_hostvar(context, var_name, inventory_hostname=None):
    if inventory_hostname is None:
        namespace = context
    else:
        if inventory_hostname not in context['hostvars']:
            raise errors.AnsibleFilterError(
                "Inventory hostname '%s' not in hostvars" % inventory_hostname)
        namespace = context["hostvars"][inventory_hostname]
    return namespace.get(var_name)

def hostlist_expression(hosts):
    """ Group hostnames using Slurm's hostlist expression format.

        E.g. with an inventory containing:

            [compute]
            dev-foo-00 ansible_host=localhost
            dev-foo-3  ansible_host=localhost
            my-random-host
            dev-foo-04 ansible_host=localhost
            dev-foo-05 ansible_host=localhost
            dev-compute-000 ansible_host=localhost
            dev-compute-001 ansible_host=localhost

        Then "{{ groups[compute] | hostlist_expression }}" will return:
            
            ['dev-foo-[00,04-05,3]', 'dev-compute-[000-001]', 'my-random-host']

        NB: This does not guranteed to return parts in the same order as `scontrol hostlist`, but its output should return the same hosts when passed to `scontrol hostnames`.
    """

    results = {}
    unmatchable = []
    for v in hosts:
        m = pattern.match(v)
        if m:
            prefix, suffix = m.groups()
            r = results.setdefault(prefix, [])
            r.append(suffix)
        else:
            unmatchable.append(v)
    return ['{}[{}]'.format(k, _group_numbers(v)) for k, v in results.items()] + unmatchable

def _group_numbers(numbers):
    units = []
    ints = [int(n) for n in numbers]
    lengths = [len(n) for n in numbers]
    # sort numbers by int value and length:
    ints, lengths, numbers = zip(*sorted(zip(ints, lengths, numbers)))
    prev = min(ints)
    for i, v in enumerate(sorted(ints)):
        if v == prev + 1:
            units[-1].append(numbers[i])
        else:
            units.append([numbers[i]])
        prev = v
    return ','.join(['{}-{}'.format(u[0], u[-1]) if len(u) > 1 else str(u[0]) for u in units])

def error(condition, msg):
    """ Raise an error if condition is not True """
    
    if not condition:
        raise errors.AnsibleFilterError(msg)

def dict2parameters(d):
    """ Convert a dict into a str in 'k1=v1 k2=v2 ...' format """
    parts = ['%s=%s' % (k, v) for k, v in d.items()]
    return ' '.join(parts)

def config2dict(lines):
    """ Convert a sequence of output lines from `scontrol show config` to a dict.
        
        As per man page uppercase keys are derived parameters, mixed case are from
        from config files.

        The following case-insensitive conversions of values are carried out:
        - '(null)' and 'n/a' are converted to None.
        - yes and no are converted to True and False respectively
        
        Except for these, values are always strings.
    """
    cfg = {}
    for line in lines:
        if '=' not in line: # ditch blank/info lines
            continue
        else:
            parts = [x.strip() for x in line.split('=', maxsplit=1)] # maxplit handles '=' in values
            if len(parts) != 2:
                raise errors.AnsibleFilterError(f'line {line} cannot be split into key=value')
            k, v = parts
            small_v = v.lower()
            if small_v == '(null)':
                v = None
            elif small_v == 'n/a':
                v = None
            elif small_v == 'no':
                v = False
            elif small_v == 'yes':
                v = True
            cfg[k] = v
    return cfg


class FilterModule(object):

    def filters(self):
        return {
            'hostlist_expression': hostlist_expression,
            'error': error,
            'dict2parameters': dict2parameters,
            'config2dict': config2dict,
        }
