
import os

from configparser import ConfigParser, NoOptionError
from uuid import uuid1


class Config(object):
    """Configuration object"""

    def __init__(self, filename, hosts_file='', idp='', log_file='', log_level='', session_log_dir=''):
        remote_connection = os.environ.get('SSH_CLIENT', '0.0.0.0 0').split()
        self.src_ip = remote_connection[0]
        self.src_port = remote_connection[1]
        self.session_uuid = uuid1()
        # TODO: Check file existence, handle exception

        self.parser = ConfigParser()
        if filename:
            self.parser.read(filename)

            self.hosts_file = hosts_file or self.parser.get('General', 'hosts_file')
            self.idp = idp or self.parser.get('General', 'idp')
            self.log_file = log_file or self.parser.get('General', 'log_file')
            self.log_level = log_level or self.parser.get('General', 'log_level')
            self.session_log_dir = session_log_dir or self.parser.get('General', 'session_log_dir')
            self.ssh_port = self.parser.get('General', 'ssh_port')

    def get(self, *args):
        """Get arbitrary config value from config file"""
        if len(args) == 3:
            try:
                return self.parser.get(args[0], args[1])
            except NoOptionError:
                return args[2]
        if len(args) == 2:
            return self.parser.get(args[0], args[1])
        return self.parser.get('General', args[0])
