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

@jinja2.contextfilter
def group_hosts(context, group_name):
    """ Group hostnames in specified inventory group using Slurm's hostlist expression format.

        E.g. with an inventory containing:

            [compute]
            dev-foo-0 ansible_host=localhost
            dev-foo-3 ansible_host=localhost
            my-random-host
            dev-foo-4 ansible_host=localhost
            dev-foo-5 ansible_host=localhost
            dev-compute-0 ansible_host=localhost
            dev-compute-1 ansible_host=localhost

        This will return:
            
            ["dev-foo-[0,3-5]", "dev-compute-[0-1]", "my-random-host"]
    """

    group = context["groups"].get(group_name, [])
    return _group_hosts(group)

def _group_hosts(hosts):
    results = {}
    unmatchable = []
    for v in hosts:
        m = pattern.match(v)
        if m:
            prefix, suffix = m.groups()
            r = results.setdefault(prefix, [])
            r.append(int(suffix))
        else:
            unmatchable.append(v)
    return ['{}[{}]'.format(k, _group_numbers(v)) for k, v in results.items()] + unmatchable

def _group_numbers(numbers):
    units = []
    prev = min(numbers)
    for v in sorted(numbers):
        if v == prev + 1:
            units[-1].append(v)
        else:
            units.append([v])
        prev = v
    return ','.join(['{}-{}'.format(u[0], u[-1]) if len(u) > 1 else str(u[0]) for u in units])

class FilterModule(object):

    def filters(self):
        return {
            'group_hosts': group_hosts
        }
