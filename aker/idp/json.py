# -*- coding: utf-8 -*-
#
#       Copyright 2017 Ahmed Nazmy
#

# Meta

from __future__ import absolute_import  # TODO Remove when use Python3 only

import json
import logging

from ..idp_factory import IdP


class Json(IdP):
    """Fetch the authority informataion from a JSON configuration"""

    def __init__(self, config, username, gateway_hostgroup):
        super(Json, self).__init__(username, gateway_hostgroup)
        logging.info('Json: loaded')
        self.config = config
        self.posix_user = username
        self._init_json_config()
        self._user_groups = None

    def list_allowed(self):
        # is our list empty ?
        if not self._allowed_ssh_hosts:
            self._load_user_allowed_hosts()
        return self._allowed_ssh_hosts

    def _init_json_config(self):
        # Load the configration from the already intitialised config
        hosts_file = self.config.hosts_file
        try:
            data = json.load(open(hosts_file, 'r'))
        except ValueError as exc:
            logging.error('JSON: could not read json file %s , error : %s', hosts_file, exc.message)

        self._all_ssh_hosts = data['hosts']
        self._all_users = data.get('users')
        self._all_usergroups = data.get('usergroups')
        self._allowed_ssh_hosts = {}
        self._load_user_allowed_hosts()

    def _load_user_allowed_hosts(self):
        """Fetch the allowed hosts based usergroup/hostgroup membership"""
        for user in self._all_users:
            if user.get('username') == self.posix_user:
                self._user_groups = user.get('usergroups')
                for host in self._all_ssh_hosts:
                    for usergroup in host.get('usergroups'):
                        if usergroup in self._user_groups:
                            self._allowed_ssh_hosts[host.get('name')] = {
                                'fqdn': host.get('name'),
                                'hostgroups': host.get('hostgroups'),
                                'ssh_port': host.get('port'),
                            }
