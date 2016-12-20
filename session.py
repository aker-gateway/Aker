# -*- coding: utf-8 -*-
#
#       Copyright 2016 Ahmed Nazmy
#

# Meta
__license__ = "AGPLv3"
__author__ = 'Ahmed Nazmy <ahmed@nazmy.io>'


import logging
import signal
import os
from SSHClient import SSHClient

class Session(object):
	""" Base class for sessions
		Different type of sessions to be
		added later
	"""
	
	def __init__(self,aker_core,host,uuid):
		self.aker= aker_core
		self.host = host
		self.host_user = self.aker.user.name
		self.host_port = int(self.aker.port)
		self.uuid = uuid
		logging.debug("Session: Base Session created")

		
	def connect(self, size):
		self._client.connect(self.host, self.host_port, size)
        
	def start_session(self):
		raise NotImplementedError
		
	def close_session(self):
		self.aker.session_end_callback(self)
		
	def kill_session(self, signum, stack):
		#TODO : Change behavoir to show screen again
		logging.debug("Session: Session Killed")
		self.close_session()
		os.kill(os.getpid(), signal.SIGKILL)


class SSHSession(Session):
	""" Wrapper around SSHClient instantiating 
		a new SSHClient instance everytime
	"""
	
	def __init__(self, aker_core, host,uuid):
		super(SSHSession, self).__init__(aker_core, host,uuid)
		self._client = SSHClient(self)
		logging.debug("Session: SSHSession created")

		
	def start_session(self):
		priv_key = self.aker.user.get_priv_key()
		self._client.start_session(self.host_user,priv_key)
