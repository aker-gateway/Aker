# -*- coding: utf-8 -*-
#
#       Copyright 2016 Ahmed Nazmy
#

# Meta
__license__ = "AGPLv3"
__author__ = 'Ahmed Nazmy <ahmed@nazmy.io>'


import getpass
import logging

from .ssh_client import SSHClient


class Session(object):
    """Base Session class"""

    def __init__(self, aker_core, host, uuid):
        self.aker = aker_core
        self.host = host
        self.host_port = int(self.aker.port)
        self.host_user = self.aker.user.name
        self.src_port = self.aker.config.src_port
        self.uuid = uuid
        self._client = self.create_client()
        logging.debug('Session: Base Session created')

    def create_client(self):
        """Abstract method that creates client instance"""
        raise NotImplementedError()

    def get_credentials(self):
        """Abstract method that must return user and secret to start session"""
        raise NotImplementedError()

    def start_session(self):
        user, secret = self.get_credentials()
        self._client.start_session(user, secret)

    def attach_sniffer(self, sniffer):
        self._client.attach_sniffer(sniffer)

    def stop_sniffer(self):
        self._client.stop_sniffer()

    def connect(self, size):
        self._client.connect(self.host, self.host_port, size)

    def close_session(self):
        self.aker.session_end_callback(self)

    def kill_session(self, signum, stack):
        logging.debug('Session: Session ended')
        self.close_session()


class SSHSession(Session):
    """Wrapper around SSHClient instantiating a new SSHClient instance every time"""

    def create_client(self):
        client = SSHClient(self)
        logging.debug('Session: SSHSession created')
        return client

    def get_credentials(self):
        try:
            auth_secret = self.aker.user.get_priv_key()
        # currently, if no SSH public key exists, an ``Exception``
        # is raised.  Catch it and try a password.
        except Exception as exc:
            if str(exc) == 'Core: Invalid Private Key':
                auth_secret = getpass.getpass('Password: ')
            else:
                raise
        return self.host_user, auth_secret
