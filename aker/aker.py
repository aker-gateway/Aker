#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       Copyright 2016 ahmed@nazmy.io
#
# For license information see LICENSE.txt


# Meta
__version__ = '0.5.0'
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
# import time

from argparse import ArgumentParser
from uuid import uuid4

import paramiko

from .config import Config
from .hosts import Hosts
from .session import SSHSession
from .snoop import SSHSniffer
from .tui import Window


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
            privkey = paramiko.RSAKey.from_private_key_file(
                os.path.expanduser('~/.ssh/id_rsa'))
        except Exception as exc:
            logging.error('Core: Invalid Private Key for user %s: %s ', self.name, exc.message)
            raise Exception('Core: Invalid Private Key')
        else:
            return privkey

    def refresh_allowed_hosts(self, fromcache):
        logging.info('Core: reloading hosts for user %s from backened identity provider', self.name)
        self.allowed_ssh_hosts, self.hostgroups = self.hosts.list_allowed(from_cache=fromcache)


class Aker(object):
    """Aker core module, this is the management module"""

    def __init__(self, config):
        self.config = config
        self.posix_user = getpass.getuser()
        self.port = config.ssh_port
        self.tui = None

        logging.info('Core: Starting up, user=%s from=%s: %s', self.posix_user, config.src_ip, config.src_port)

        self.user = User(self.config, self.posix_user)

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
        # session_start_time = time.strftime('%Y%m%d-%H%M%S')
        session = SSHSession(self, host, session_uuid)
        # TODO: add err handling
        sniffer = SSHSniffer(
            self.posix_user,
            self.config.src_port,
            host,
            session_uuid,
            screen_size,
            self.config.session_log_dir)
        session.attach_sniffer(sniffer)
        logging.info('Core: Starting session UUID %s for user %s to host %s', session_uuid, self.posix_user, host)
        session.connect(screen_size)
        try:
            session.start_session()
        except Exception as exc:
            logging.error('Core: start_session failed: %s', exc.message)
            raise
        finally:
            session.stop_sniffer()
            self.tui.restore()
            self.tui.hostlist.search.clear()  # Clear selected hosts

    def session_end_callback(self, session):
        logging.info('Core: Finished session UUID %s for user %s to host %s', session.uuid, self.posix_user, session.host)


if __name__ == '__main__':
    PARSER = ArgumentParser(description='Aker SSH gateway')
    PARSER.add_argument('--config', '-c', default='/etc/aker/aker.ini', help='Path to config file')
    PARSER.add_argument('--hosts-file', default='/etc/aker/hosts.json', help='Path to JSON file with allowed hosts')
    PARSER.add_argument('--idp', default='ipa', help='idp provider', choices=('ipa', 'json',))
    PARSER.add_argument('--log-file', default='/var/log/aker/aker.log', help='Path to log file')
    PARSER.add_argument('--log-level', default='INFO', help='Set log level', choices=('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL', 'FATAL'))
    PARSER.add_argument('--session-log-dir', default='/var/log/aker', help='Session log dir')
    ARGS = PARSER.parse_args()

    CONFIG = Config(
        filename=ARGS.config,
        hosts_file=ARGS.hosts_file,
        idp=ARGS.idp,
        log_file=ARGS.log_file,
        log_level=ARGS.log_level,
        session_log_dir=ARGS.session_log_dir,
    )

    # Setup logging first thing
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    logging.basicConfig(
        format='%(asctime)s - %(levelname)s - %(message)s',
        filename=CONFIG.log_file,
        level=CONFIG.log_level)

    Aker(CONFIG).build_tui()
