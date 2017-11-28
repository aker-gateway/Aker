#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       Copyright 2016 ahmed@nazmy.io
#
# For license information see LICENSE.txt


# Meta
__version__ = '0.4.5'
__version_info__ = tuple(__version__.split('.'))
__license__ = 'AGPLv3'
__license_info__ = {
    'AGPLv3': {
        'customer': 'Unsupported',
        'license_format': '1.0',
        'product': 'aker',
        'users': 0,  # 0 being unlimited
        'version': __version__,
    }
}

import getpass
import logging
import os
import time

from argparse import ArgumentParser
from uuid import uuid4

import paramiko

from tui import Window

from config import Config
from hosts import Hosts
from session import SSHSession
from snoop import SSHSniffer


class User(object):
    def __init__(self, username):
        self.name = username
        gateway_hostgroup = config.get('gateway_group')
        idp = config.get('idp')
        logging.debug('Core: using Identity Provider {0}'.format(idp))
        self.hosts = Hosts(config, self.name, gateway_hostgroup, idp)
        self.allowed_ssh_hosts, self.hostgroups = self.hosts.list_allowed()

    def get_priv_key(self):
        try:
            # TODO: check better identity options
            privkey = paramiko.RSAKey.from_private_key_file(
                os.path.expanduser('~/.ssh/id_rsa'))
        except Exception as exc:
            logging.error(
                'Core: Invalid Private Key for user {0} : {1} '.format(
                    self.name, exc.message))
            raise Exception('Core: Invalid Private Key')
        else:
            return privkey

    def refresh_allowed_hosts(self, fromcache):
        logging.info(
            'Core: reloading hosts for user {0} from backened identity provider'.format(
                self.name))
        self.allowed_ssh_hosts, self.hostgroups = self.hosts.list_allowed(
            from_cache=fromcache)


class Aker(object):
    """ Aker core module, this is the management module
    """

    def __init__(self, config):
        self.config = config
        self.posix_user = getpass.getuser()
        self.port = config.ssh_port
        self.tui = None

        logging.info(
            'Core: Starting up, user={0} from={1}:{2}'.format(
                self.posix_user,
                config.src_ip,
                config.src_port))

        self.user = User(self.posix_user)

    def build_tui(self):
        logging.debug('Core: Drawing TUI')
        self.tui = Window(self)
        self.tui.draw()
        self.tui.start()

    def init_connection(self, host):
        screen_size = self.tui.loop.screen.get_cols_rows()
        logging.debug('Core: pausing TUI')
        self.tui.pause()
        # TODO: check for shorter yet unique uuid
        session_uuid = uuid4()
        session_start_time = time.strftime('%Y%m%d-%H%M%S')
        session = SSHSession(self, host, session_uuid)
        # TODO: add err handling
        sniffer = SSHSniffer(
            self.posix_user,
            config.src_port,
            host,
            session_uuid,
            screen_size)
        session.attach_sniffer(sniffer)
        logging.info(
            'Core: Starting session UUID {0} for user {1} to host {2}'.format(
                session_uuid, self.posix_user, host))
        session.connect(screen_size)
        try:
            session.start_session()
        finally:
            session.stop_sniffer()
            self.tui.restore()
            self.tui.hostlist.search.clear()  # Clear selected hosts

    def session_end_callback(self, session):
        logging.info(
            'Core: Finished session UUID {0} for user {1} to host {2}'.format(
                session.uuid,
                self.posix_user,
                session.host))


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--config', '-c', default='/etc/aker/aker.ini', help='Path to config file')
    parser.add_argument('--log-file', default='/var/log/aker/aker.log', help='Path to log file')
    parser.add_argument('--log-level', default='INFO', help='Set log level', choices=('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL', 'FATAL'))
    parser.add_argument('--session-log-dir', default='/var/log/aker', help='Session log dir')
    args = parser.parse_args()

    config = Config(
        filename=args.config,
        log_file=args.log_file,
        log_level=args.log_level,
        session_log_dir=args.session_log_dir,
    )

    # Setup logging first thing
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    logging.basicConfig(
        format='%(asctime)s - %(levelname)s - %(message)s',
        filename=config.log_file,
        level=config.log_level)

    Aker(config).build_tui()
