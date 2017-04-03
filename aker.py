#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       Copyright 2016 ahmed@nazmy.io
#
# For license information see LICENSE.txt


# Meta
__version__ = '0.4.2'
__version_info__ = (0, 4, 2)
__license__ = "AGPLv3"
__license_info__ = {
    "AGPLv3": {
        "product": "aker",
        "users": 0, # 0 being unlimited
        "customer": "Unsupported",
        "version": __version__,
        "license_format": "1.0",
    }
}

import logging
import os
import sys
import uuid
import getpass
import paramiko
import socket
from configparser import ConfigParser
import time

from hosts import AuthorityFactory
import tui
from session import SSHSession
from snoop import SSHSniffer


config_file = "aker.ini"
# FIXME: below log needs chmod 777 since we dont have
# server compnent 
log_file = 'aker.log'
session_log_dir = '/var/log/aker/'


class Configuration(object):
	def __init__(self, filename):
		remote_connection = os.environ.get('SSH_CLIENT', '0.0.0.0 0')
		self.src_ip = remote_connection.split()[0]
		self.src_port = remote_connection.split()[1]
		self.session_uuid = uuid.uuid1()
		#TODO: Check file existance , handle exception
		configparser = ConfigParser()
		if filename:
			configparser.read(filename)
			self.log_level = configparser.get('General', 'log_level')
			self.ssh_port = configparser.get('General', 'ssh_port')
			




class User(object):
	def __init__(self,username):
		self.name = username
		configparser = ConfigParser()
		configparser.read(config_file)
		gateway_hostgroup = configparser.get('General', 'gateway_group')
		authority = configparser.get('General','authority')
		# TODO: load authority type from configuration
		self.hosts = AuthorityFactory.getAuthority(authority)(username,gateway_hostgroup)
		self.allowed_ssh_hosts = self.hosts.list_allowed()
		

	def get_priv_key(self):
		try :
			#TODO: check better identity options
			privkey = paramiko.RSAKey.from_private_key_file(os.path.expanduser("~/.ssh/id_rsa"))
		except Exception as e:
			logging.error("Core: Invalid Private Key for user {0} : {1} ".format(self.name, e.message))
			raise Exception("Core: Invalid Private Key")
		else :
			return privkey
			
	


	
    		


class Aker(object):
	""" Aker core module, this is the management module
	"""

	def __init__(self,log_level = 'INFO'):
		self.config = Configuration(config_file)
		self.posix_user = getpass.getuser()
		self.user = User(self.posix_user)
		self.log_level = self.config.log_level
		self.port = self.config.ssh_port
		for handler in logging.root.handlers[:]:
			logging.root.removeHandler(handler)
		logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',filename=log_file,level=self.config.log_level)
		logging.info("Core: Starting up, user={0} from={1}:{2}".format(self.posix_user,self.config.src_ip,self.config.src_port))
		self.build_tui()



	def build_tui(self):
		logging.debug("Core: Drawing TUI")
		self.tui = tui.Window(self)
		self.tui.draw()
		self.tui.start()

	def init_connection(self,host):
		screen_size = self.tui.loop.screen.get_cols_rows()
		logging.debug("Core: pausing TUI")
		self.tui.pause()
		#TODO: check for shorter yet unique uuid
		session_uuid = uuid.uuid4()
		session_start_time = time.strftime("%Y%m%d-%H%M%S")
		session = SSHSession(self,host,session_uuid)
		#TODO: add err handling
		sniffer = SSHSniffer(self.posix_user,self.config.src_port,host,session_uuid,screen_size)
		session.attach_sniffer(sniffer)
		logging.info("Core: Starting session UUID {0} for user {1} to host {2}".format(session_uuid,self.posix_user,host))
		session.connect(screen_size)
		try:
			session.start_session()
		finally:
			session.stop_sniffer()
			self.tui.restore()
			self.tui.search_edit.set_edit_text("") # Clear selected hosts


	def session_end_callback(self, session):
		logging.info("Core: Finished session UUID {0} for user {1} to host {2}".format(session.uuid,self.posix_user,session.host))


if __name__ == '__main__':
	Aker().build_tui()
