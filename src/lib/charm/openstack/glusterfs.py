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

import charms_openstack.adapters as os_adapters
import charms_openstack.charm.classes as os_classes
import charms.reactive as reactive

import gluster.cli.peer as gluster_peer
import gluster.cli.utils as gluster_utils

import charmhelpers.core.hookenv as hookenv
import charmhelpers.core.host as host

import os
import subprocess


def install():
    """Use the singleton from the GlusterCharm to install the packages on the
    unit.

    @returns: None
    """
    GlusterFSCharm.singleton.install()


def probe_peers(peer):
    GlusterFSCharm.singleton.probe_peers(peer)


def create_bricks():
    GlusterFSCharm.singleton.create_bricks()


class BaseGlusterCharm(os_classes.BaseOpenStackCharm,
                       os_classes.BaseOpenStackCharmActions,
                       os_classes.BaseOpenStackCharmAssessStatus):
    """

    """

    abstract_class = True

    # this is the first release in which this charm works
    release = None

    # list of packages to install
    packages = []

    # Package to determine application version from
    # defaults to the first package provided in packages if not provided
    version_package = None

    # List of the relation names which are required
    required_relations = []


class StorageMixin(object):
    """
    Designed as a mixin
    """

    def is_mounted(self, path):
        """Indicates whether the device path is mounted or not.

        :param device: the path to check if mounted
        :return bool: True if the path is mounted, False otherwise
        """
        for mount_point, dev in host.mounts():
            if dev == path or mount_point == path:
                return True

        return False

    def get_mount_point(self, device):
        """

        :param device:
        :return:
        """
        for mount_point, dev in host.mounts():
            if dev == device:
                return mount_point

        return None

    def unmount(self, path):
        """

        :param path:
        :return:
        """
        # Check to make sure the path exists
        if not os.path.exists(path):
            return True

        return host.umount(path)

    def ephemeral_unmount(self, path):
        """

        :param path:
        :return:
        """
        ephemeral_mountpoint = (hookenv.config('ephemeral-mountpoint') or
                                '').strip()
        if not ephemeral_mountpoint:
            return

        if self.is_mounted(ephemeral_mountpoint):
            self.unmount(ephemeral_mountpoint)

    def mount(self, device, mount_point=None, fstype=None, **options):
        """

        :param device:
        :param mountpoint:
        :param fstype:
        :param options:
        :return:
        """
        pass

    def format(self, device, fstype, **options):
        """

        :param device:
        :param fstype:
        :param options:
        :return:
        """
        # TODO(wolsen) make this a bit more generic
        cmd = ['mkfs.xfs']
        if options:
            for key, value in options:
                cmd.extend(['-%s' % key, value])

        cmd.append(device)

        try:
            out = subprocess.check_output(cmd)
        except subprocess.CalledProcessError as e:
            hookenv.log('Error formatting filesystem on disk %s: %s' %
                        (device, e), hookenv.ERROR)
            raise

    def reformat(self, device):
        """

        :param device:
        :return:
        """
        if self.is_mounted(device):
            self.unmount(device)

        self.zap_disk(device)
        self.format(device, 'xfs', i="size=512", n="size=8192")

    def zap_disk(self, device):
        """

        :param device:
        :return:
        """
        pass


class GlusterFSCharm(BaseGlusterCharm):
    """

    """

    release = "mitaka"
    name = 'gluster'
    packages = ["glusterfs-server", "glusterfs-common", "glusterfs-client",
                "ctdb", "nfs-common"]

    def config_changed(self):
        """

        :return:
        """
        bricks = (hookenv.config('brick_devices') or '').split(' ')
        bricks = [i for i in filter(lambda y: not y == "",
                                    map(lambda x: x.strip(), bricks))]
        unmount = hookenv.config('ephemeral_unmount')
        reformat = hookenv.config('reformat_bricks')


    def probe_peers(self, peer):
        """
        Attempts tp probe all peer units
        :return:
        """
        if not hookenv.is_leader():
            hookenv.log('Deferring probing of peers to leader unit')
            return

        hookenv.log('Probing peers')
        probed_units = hookenv.leader_get('probed-units') or []
        new_units = []
        for (unit, address) in peer.ip_map():
            if unit in probed_units:
                hookenv.debug('unit %s already probed.' % unit)
                continue

            hookenv.log('probing host %s at %s' % (unit, address))
            hookenv.status_set('maintenance', 'Probing peer %s' % unit)
            try:
                out = gluster_peer.probe(address)
                hookenv.log('successfully probed %s: %s' % (unit, out),
                            hookenv.DEBUG)
                new_units.append(unit)
            except gluster_utils.GlusterCmdException as e:
                hookenv.log('Error probing host %s: %s' % (unit, e),
                            hookenv.ERROR)

        if new_units:
            settings = {'probed-units': probed_units.extend(new_units)}
            hookenv.leader_set(settings)
            # This isn't right, but just figure out what to assess here.
            hookenv.status_set('active', 'ready')
