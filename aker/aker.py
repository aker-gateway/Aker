# -*- coding: utf-8 -*-
#
#       Copyright 2016 ahmed@nazmy.io
#
# For license information see LICENSE.txt

import getpass
import logging

from uuid import uuid4

from .session import SSHSession
from .snoop import SSHSniffer
from .tui import Window
from .user import User


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
