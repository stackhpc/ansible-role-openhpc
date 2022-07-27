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
    """

    results = {}
    unmatchable = []
    for v in hosts:
        m = pattern.match(v)
        if m:
            prefix, suffix = m.groups()
            print(prefix,suffix)
            r = results.setdefault(prefix, [])
            r.append(suffix)
        else:
            unmatchable.append(v)
    return ['{}[{}]'.format(k, _group_numbers(v)) for k, v in results.items()] + unmatchable

def _group_numbers(numbers):
    print('numbers:', sorted(numbers))
    units = []
    prev = min(int(n) for n in numbers)
    for v in sorted(numbers):
        if int(v) == prev + 1:
            units[-1].append(v)
        else:
            units.append([v])
        print('units:', units)
        prev = int(v)
    return ','.join(['{}-{}'.format(u[0], u[-1]) if len(u) > 1 else str(u[0]) for u in units])

def error(condition, msg):
    """ Raise an error if condition is not True """
    
    if not condition:
        raise errors.AnsibleFilterError(msg)

def dict2parameters(d):
    """ Convert a dict into a str in 'k1=v1 k2=v2 ...' format """
    parts = ['%s=%s' % (k, v) for k, v in d.items()]
    return ' '.join(parts)

class FilterModule(object):

    def filters(self):
        return {
            'hostlist_expression': hostlist_expression,
            'error': error,
            'dict2parameters': dict2parameters,
        }
