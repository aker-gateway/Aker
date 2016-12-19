# -*- coding: utf-8 -*-
#
#       Copyright 2016 Ahmed Nazmy
#

# Meta
__license__ = "AGPLv3"
__author__ = 'Ahmed Nazmy <ahmed@nazmy.io>'

import getpass
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
        self.host_user = self.aker.user.ssh_hosts[host]['username']
        self.host_port = int(self.aker.user.ssh_hosts[host]['port'])
        self.uuid = uuid
        logging.debug("Session: Base Session created")
        #TODO : Add UUID shit 
        
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
        try:
            auth_secret = self.aker.user.get_priv_key()
        # currently, if no SSH public key exists, an ``Exception``
        # is raised.  Catch it and try a password.
        except Exception as exc:
            if str(exc) == 'Core: Invalid Private Key':
                auth_secret = getpass.getpass("Password: ")
            else:
                raise
        self._client.start_session(self.host_user, auth_secret)
