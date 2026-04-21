# -*- coding: utf-8 -*- {{{
# ===----------------------------------------------------------------------===
#
#                 Installable Component of Eclipse VOLTTRON
#
# ===----------------------------------------------------------------------===
#
# Copyright 2022 Battelle Memorial Institute
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy
# of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# ===----------------------------------------------------------------------===
# }}}

import logging
import re

from importlib.metadata import distribution, PackageNotFoundError

try:
    distribution('volttron-core')
    from volttron.client.known_identities import CONFIGURATION_STORE
except PackageNotFoundError:
    from volttron.platform.agent.known_identities import CONFIGURATION_STORE

from .topic import TopicTree, TopicNode

_log = logging.getLogger(__name__)


class DeviceNode(TopicNode):
    def __init__(self, tag=None, identifier=None, expanded=True, data=None, segment_type='TOPIC_SEGMENT', topic=''):
        super(DeviceNode, self).__init__(tag, identifier, expanded, data, segment_type, topic)

    def is_point(self):
        return True if self.segment_type == 'POINT' else False

    def is_device(self):
        return True if self.segment_type == 'DEVICE' else False


class DeviceTree(TopicTree):
    def __init__(self, topic_list=None, root_name='devices', assume_full_topics=False,  *args, **kwargs):
        super(DeviceTree, self).__init__(topic_list=topic_list, root_name=root_name, node_class=DeviceNode,
                                         *args, **kwargs)
        if assume_full_topics:
            for n in self.leaves():
                n.data['segment_type'] = 'POINT'
            for n in [self.parent(l.identifier) for l in self.leaves()]:
                n.data['segment_type'] = 'DEVICE'

    def points(self, nid=None):
        if nid is None:
            points = [n for n in self._nodes.values() if n.is_point()]
        else:
            points = [self[n] for n in self.expand_tree(nid) if self[n].is_point()]
        return points

    def devices(self, nid=None):
        if nid is None:
            points = [n for n in self._nodes.values() if n.is_device()]
        else:
            points = [self[n] for n in self.expand_tree(nid) if self[n].is_device()]
        return points

    # TODO: Getting points requires getting device config, using it to find the registry config,
    #  and then parsing that. There is not a method in config.store, nor in the platform.driver for
    #  getting a completed configuration. The configuration is only fully assembled in the subsystem's
    #  _initial_update method called when the agent itself calls get_configs at startup. There does not
    #  seem to be an equivalent management method, and the code for this is in the agent subsystem
    #  rather than the service (though it is reached through the service, oddly...
    @classmethod
    def from_store(cls, platform, rpc_caller):
        # TODO: Duplicate logic for external_platform check from VUIEndpoints to remove reference to it from here.
        kwargs = {'external_platform': platform} if 'VUIEndpoints' in rpc_caller.__repr__() else {}
        devices = rpc_caller(CONFIGURATION_STORE, 'manage_list_configs', 'platform.driver', **kwargs)
        devices = devices if kwargs else devices.get(timeout=5)
        devices = [d for d in devices if re.match('^devices/.*', d)]
        device_tree = cls(devices)
        for d in devices:
            dev_config = rpc_caller(CONFIGURATION_STORE, 'manage_get', 'platform.driver', d, raw=False, **kwargs)
            # TODO: If not AsyncResponse instead of if kwargs
            dev_config = dev_config if kwargs else dev_config.get(timeout=5)
            reg_cfg_name = dev_config.pop('registry_config')[len('config://'):]
            data = {'config': dev_config, 'segment_type': 'DEVICE'}
            device_tree.update_node(d, data=data)
            registry_config = rpc_caller('config.store', 'manage_get', 'platform.driver',
                                         f'{reg_cfg_name}', raw=False, **kwargs)
            registry_config = registry_config if kwargs else registry_config.get(timeout=5)
            for pnt in registry_config:
                point_name = pnt.pop('Volttron Point Name')
                n = device_tree.create_node(point_name, f"{d}/{point_name}", parent=d, data=pnt)
                n.data['segment_type'] = 'POINT'
        return device_tree
