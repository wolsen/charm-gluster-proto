# Copyright 2017 Canonical Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import charm.openstack.glusterfs as glusterfs
import charms.reactive as reactive


@reactive.when_not('installed')
def install_packages():
    """Install packages for glusterfs"""
    glusterfs.install()
    reactive.set_state('installed')


@reactive.when('server.connected')
def peer_available(peer):
    """
    The peer.available state is set when there are one or more peer units
    that have joined.

    :return:
    """
    glusterfs.probe_peers(peer)


@reactive.when('storage.available')
def storage_available():
    """
    The storage.available state is set when local disks are available to
    prepare them as bricks.

    :return:
    """
    glusterfs.prepare_storage()


@reactive.when('bricks.available', 'peering.complete')
@reactive.when_not('volume.created')
def create_volume():
    """

    :return:
    """

#

