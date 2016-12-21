# -*- coding: utf-8 -*-
#
#       Copyright 2016 Ahmed Nazmy
#

# Meta
import getpass
import logging
import os
import select
import signal
import socket
import sys
import termios
import tty

import paramiko

__license__ = "AGPLv3"
__author__ = 'Ahmed Nazmy <ahmed@nazmy.io>'

TIME_OUT = 10


class Client(object):
    def __init__(self, session):
        self._session = session


class SSHClient(Client):
    def __init__(self, session):
        super(SSHClient, self).__init__(session)
        self._socket = None
        logging.debug("Client: Client Created")

    def connect(self, ip, port, size):
        self._size = size
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.settimeout(TIME_OUT)
        self._socket.connect((ip, port))
        logging.debug("SSHClient: Connected to {0}:{1}".format(ip, port))

    def get_transport(self):
        transport = paramiko.Transport(self._socket)
        transport.set_keepalive(10)
        transport.start_client()
        return transport

    def start_session(self, user, auth_secret):
        logging.debug("SSHClient: Authenticating session.")
        try:
            transport = self.get_transport()
            if isinstance(auth_secret, basestring):
                transport.auth_password(user, auth_secret)
            else:
                try:
                    transport.auth_publickey(user, auth_secret)
                # Failed to authenticate with SSH key, so
                # try a password instead.
                except paramiko.ssh_exception.AuthenticationException:
                    transport.auth_password(user, getpass.getpass())
            self._start_session(transport)
        except EOFError as exc:
            logging.error('EOFError.  Assuming bad SSH implementation.')
            logging.error('Original Erorr: %s', exc)
            self._handle_exception(transport)
        except Exception as e:
            logging.error(e)
            self._handle_exception(transport)
            raise e

    def _handle_exception(self, transport):
        self._session.close_session()
        if transport:
            transport.close()
        self._socket.close()

    def _start_session(self, transport):
        chan = transport.open_session()
        cols, rows = self._size
        chan.get_pty('xterm', cols, rows)
        chan.invoke_shell()
        self.interactive_shell(chan)
        chan.close()
        self._session.close_session()
        transport.close()
        self._socket.close()

    def interactive_shell(self, chan):
        # Handle session IO
        sys.stdout.flush()
        try:
            signal.signal(signal.SIGHUP, self._session.kill_session)
            oldtty = termios.tcgetattr(sys.stdin)
            tty.setraw(sys.stdin.fileno())
            tty.setcbreak(sys.stdin.fileno())
            chan.settimeout(0.0)
            while True:
                r, w, e = select.select([chan, sys.stdin], [], [])
                if chan in r:
                    try:
                        x = chan.recv(1024)
                        if len(x) == 0:
                            break
                        sys.stdout.write(x)
                        sys.stdout.flush()
                    except socket.timeout:
                        break
                if sys.stdin in r:
                    x = os.read(sys.stdin.fileno(), 1)
                    if len(x) == 0:
                        break
                    chan.send(x)
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, oldtty)
        except Exception as e:
            logging.error(e)
            raise e
