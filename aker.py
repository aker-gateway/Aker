#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       Copyright 2016 ahmed@nazmy.io
#
# For license information see LICENSE.txt


# Meta
from configparser import ConfigParser
import getpass
import logging
import os
import paramiko
import time
import uuid

import tui
from session import SSHSession
from snoop import Sniffer

__version__ = '0.2.1'
__version_info__ = (0, 2, 1)
__license__ = "AGPLv3"
__license_info__ = {
    "AGPLv3": {
        "product": "aker",
        "users": 0,  # 0 being unlimited
        "customer": "Unsupported",
        "version": __version__,
        "license_format": "1.0",
    }
}

config_file = "/etc/aker.ini"
log_file = 'aker.log'
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                    filename=log_file, level=logging.INFO)


class Configuration(object):
    def __init__(self, filename):
        remote_connection = os.environ.get('SSH_CLIENT', '0.0.0.0 0')
        self.src_ip = remote_connection.split()[0]
        self.src_port = remote_connection.split()[1]
        self.session_uuid = uuid.uuid1()
        # TODO: Check file existance , handle exception
        configparser = ConfigParser()
        if filename:
            configparser.read(filename)
            self.log_level = configparser.get('General', 'log_level')


class User(object):
    def __init__(self, username):
        self.name = username
        configparser = ConfigParser()
        configparser.read(config_file)
        # TODO: Add excpetion to handle problems with users in config
        hosts = configparser.get(self.name, 'hosts').split("\n")
        self.enabled = configparser.get(self.name, 'enabled')
        self.ssh_hosts = {}
        self.load_ssh_hosts(hosts)

    def load_ssh_hosts(self, hosts):
        for host in hosts:
            # TODO: handle exception for incomplete or misplaced entry,
            #       i.e host,user,port
            hostname, port, username = host.split(",")
            self.ssh_hosts[hostname] = {'port': port, 'username': username}

    def get_priv_key(self):
        try:
            # TODO: check better identity options
            # TODO: get user priv key from configfile
            privkey = paramiko.RSAKey.from_private_key_file(
                os.path.expanduser("~/.ssh/id_rsa")
            )
        except Exception as e:
            logging.error("Core: Invalid Private Key for user {0} : {1} "
                          .format(self.name, e.message))
            raise Exception("Core: Invalid Private Key")
        else:
            return privkey


class Aker(object):
    """ Aker core module, this is the management module
    """

    def __init__(self, log_level='INFO'):
        self.config = Configuration(config_file)
        self.posix_user = getpass.getuser()
        self.user = User(self.posix_user)
        self.log_level = self.config.log_level
        self.sniffer = Sniffer()
        logging.info("Core: Starting up, user={0} from={1}:{2}".format(
            self.posix_user, self.config.src_ip, self.config.src_port)
        )
        self.build_tui()

    def build_tui(self):
        logging.debug("Core: Drawing TUI")
        self.tui = tui.Window(self)
        self.tui.draw()
        self.tui.start()

    def init_connection(self, host):
        screen_size = self.tui.loop.screen.get_cols_rows()
        logging.debug("Core: pausing TUI")
        self.tui.pause()
        session_uuid = uuid.uuid4()
        session_start_time = time.strftime("%Y%m%d-%H%M%S")
        session = SSHSession(self, host, session_uuid)
        # TODO: add err handling
        session.connect(screen_size)
        # TODO enhance sniffer code
        session_log_filename = "{0}-{1}-{2}_{3}_{4}.log".format(
            self.posix_user, host,
            session_start_time, self.config.src_port,
            session_uuid
        )
        logging.info("Core: Started session UUID {0} for user {1} to host {2}"
                     .format(session_uuid, self.posix_user, host))
        self.sniffer.set_log_filename(session_log_filename)
        self.sniffer.capture()
        try:
            session.start_session()
        finally:
            self.sniffer.restore()
            self.tui.restore()
            # TODO: better handling through session_ended_handler
            self.tui.search_edit.set_edit_text("")  # Clear selected hosts

    def session_end_callback(self, session):
        logging.info("Core: Finished session UUID {0} for user {1} to host {2}"
                     .format(session.uuid, self.posix_user, session.host))


if __name__ == '__main__':
    Aker().build_tui()
