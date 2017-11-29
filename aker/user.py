
import logging
import os

import paramiko

from .hosts import Hosts


class User(object):

    def __init__(self, config, username):
        self.config = config
        self.name = username
        gateway_hostgroup = self.config.get('gateway_group')
        idp = self.config.idp
        logging.debug('Core: using Identity Provider %s', idp)
        self.hosts = Hosts(self.config, self.name, gateway_hostgroup, idp)
        self.allowed_ssh_hosts, self.hostgroups = self.hosts.list_allowed()

    def get_priv_key(self):
        try:
            # TODO: check better identity options
            privkey = paramiko.RSAKey.from_private_key_file(os.path.expanduser('~/.ssh/id_rsa'))
        except Exception as exc:
            logging.error('Core: Invalid Private Key for user %s: %s ', self.name, exc.message)
            raise Exception('Core: Invalid Private Key')
        else:
            return privkey

    def refresh_allowed_hosts(self, fromcache):
        logging.info('Core: reloading hosts for user %s from backened identity provider', self.name)
        self.allowed_ssh_hosts, self.hostgroups = self.hosts.list_allowed(from_cache=fromcache)
