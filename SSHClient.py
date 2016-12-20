# -*- coding: utf-8 -*-
#
#       Copyright 2016 Ahmed Nazmy
#

# Meta
__license__ = "AGPLv3"
__author__ = 'Ahmed Nazmy <ahmed@nazmy.io>'

import logging
import paramiko
import socket
import tty
import sys
import termios
import signal
import select
import os

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
		logging.debug("SSHClient: Connected to {0}:{1}".format(ip,port))
		
		
	def get_transport(self):
		transport = paramiko.Transport(self._socket)
		transport.set_keepalive(10)
		transport.start_client()
		return transport

	def start_session(self, user, private_key):
		logging.debug("SSHClient: Authenticating using key-pair")
		try:
			transport = self.get_transport()
			transport.auth_publickey(user, private_key)
			self._start_session(transport)
		except Exception as e:
			logging.error(e)
			self._session.close_session()
			if transport:
				transport.close()
			self._socket.close()
			raise e

			
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
