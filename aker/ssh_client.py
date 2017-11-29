# -*- coding: utf-8 -*-
#
#       Copyright 2016 Ahmed Nazmy
#

# Meta
__license__ = 'AGPLv3'
__author__ = 'Ahmed Nazmy <ahmed@nazmy.io>'

import errno
import fcntl
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

TIME_OUT = 10


class Client(object):
    def __init__(self, session):
        self._session = session
        self.sniffers = []

    def attach_sniffer(self, sniffer):
        self.sniffers.append(sniffer)

    def stop_sniffer(self):
        for sniffer in self.sniffers:
            sniffer.stop()

    @staticmethod
    def get_console_dimensions():
        cols, lines = 80, 24
        try:
            fmt = 'HH'
            buffer = struct.pack(fmt, 0, 0)
            result = fcntl.ioctl(
                sys.stdout.fileno(),
                termios.TIOCGWINSZ,
                buffer)
            columns, lines = struct.unpack(fmt, result)
        except Exception as exc:
            pass
        finally:
            return columns, lines


class SSHClient(Client):
    def __init__(self, session):
        super(SSHClient, self).__init__(session)
        self._socket = None
        self.channel = None
        logging.debug('Client: Client Created')

    def connect(self, ip, port, size):
        self._size = size
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.settimeout(TIME_OUT)
        self._socket.connect((ip, port))
        logging.debug('SSHClient: Connected to %s:%s', ip, port)

    def get_transport(self):
        transport = paramiko.Transport(self._socket)
        transport.set_keepalive(10)
        transport.start_client()
        return transport

    def start_session(self, user, auth_secret):
        try:
            transport = self.get_transport()
            if isinstance(auth_secret, basestring):
                logging.debug('SSHClient: Authenticating using password')
                transport.auth_password(user, auth_secret)
            else:
                try:
                    logging.debug('SSHClient: Authenticating using key-pair')
                    transport.auth_publickey(user, auth_secret)
                # Failed to authenticate with SSH key, so
                # try a password instead.
                except paramiko.ssh_exception.AuthenticationException:
                    logging.debug('SSHClient: Authenticating using password')
                    transport.auth_password(user, getpass.getpass())
            self._start_session(transport)
        except Exception as exc:
            logging.error('SSHClient: error authenticating: %s', exc.message)
            self._session.close_session()
            if transport:
                transport.close()
            self._socket.close()
            raise exc

    def attach(self, sniffer):
        """Adds a sniffer to the session"""
        self.sniffers.append(sniffer)

    def _set_sniffer_logs(self):
        for sniffer in self.sniffers:
            try:
                # Incase a sniffer without logs
                sniffer.set_logs()
            except AttributeError:
                pass

    def _start_session(self, transport):
        self.channel = transport.open_session()
        columns, lines = self._size
        self.channel.get_pty('xterm', columns, lines)
        self.channel.invoke_shell()
        try:
            signal.signal(signal.SIGWINCH, self.sigwinch)
        except BaseException:
            pass
        self._set_sniffer_logs()
        self.interactive_shell(self.channel)
        self.channel.close()
        self._session.close_session()
        transport.close()
        self._socket.close()

    def sigwinch(self, signal, data):
        columns, lines = get_console_dimensions()
        logging.debug(
            'SSHClient: setting terminal to %s columns and %s lines' %
            (columns, lines))
        self.channel.resize_pty(columns, lines)
        for sniffer in self.sniffers:
            sniffer.sigwinch(columns, lines)

    def interactive_shell(self, chan):
        """Handles ssh IO"""
        sys.stdout.flush()
        oldtty = termios.tcgetattr(sys.stdin)
        try:
            tty.setraw(sys.stdin.fileno())
            tty.setcbreak(sys.stdin.fileno())
            chan.settimeout(0.0)

            while True:
                try:
                    r, w, e = select.select([chan, sys.stdin], [], [])
                    flag = fcntl.fcntl(sys.stdin, fcntl.F_GETFL, 0)
                    fcntl.fcntl(
                        sys.stdin.fileno(),
                        fcntl.F_SETFL,
                        flag | os.O_NONBLOCK)
                except Exception as exc:
                    logging.error(exc)
                    pass

                if chan in r:
                    try:
                        x = chan.recv(10240)
                        len_x = len(x)
                        if len_x == 0:
                            break
                        for sniffer in self.sniffers:
                            sniffer.channel_filter(x)
                        try:
                            nbytes = os.write(sys.stdout.fileno(), x)
                            logging.debug(
                                'SSHClient: wrote %s bytes to stdout' % nbytes)
                            sys.stdout.flush()
                        except OSError as msg:
                            if msg.errno == errno.EAGAIN:
                                continue
                    except socket.timeout:
                        pass

                if sys.stdin in r:
                    try:
                        buf = os.read(sys.stdin.fileno(), 4096)
                    except OSError as exc:
                        logging.error(exc)
                        pass
                    for sniffer in self.sniffers:
                        sniffer.stdin_filter(buf)

                    chan.send(buf)

        finally:
            logging.debug('SSHClient: interactive session ending')
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, oldtty)
