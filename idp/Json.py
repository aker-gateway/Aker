#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       Copyright 2017 Ahmed Nazmy
#

# Meta

from IdPFactory import IdP
import json
import logging


class Json(IdP):
    """
    Fetch the authority informataion from a JSON configuration
    """

    def __init__(self, config, username, gateway_hostgroup):
        super(Json, self).__init__(username, gateway_hostgroup)
        logging.info("Json: loaded")
        self.config = config
        self.posix_user = username
        self._init_json_config()

    def _init_json_config(self):
        # Load the configration from the already intitialised config parser
        hosts_file = self.config.get("General", "hosts_file", "hosts.json")
        try:
            JSON = json.load(open(hosts_file, 'r'))
        except ValueError as e:
            logging.error(
                "JSON: could not read json file {0} , error : {1}".format(
                    hosts_file, e.message))

        logging.debug("Json: loading all hosts from {0}".format(hosts_file))
        self._all_ssh_hosts = JSON["hosts"]
        logging.debug("Json: loading all users from {0}".format(hosts_file))
        self._all_users = JSON.get("users")
        logging.debug(
            "Json: loading all usergroups from {0}".format(hosts_file))
        self._all_usergroups = JSON.get("usergroups")
        self._allowed_ssh_hosts = {}
        self._load_user_allowed_hosts()

    def _load_user_allowed_hosts(self):
        """
        Fetch the allowed hosts based usergroup/hostgroup membership
        """
        for user in self._all_users:
            if user.get("username") == self.posix_user:
                logging.debug("Json: loading hosts/groups for user {0}".format(
                    self.posix_user))
                self._user_groups = user.get("usergroups")
                for host in self._all_ssh_hosts:
                    for usergroup in host.get("usergroups"):
                        if usergroup in self._user_groups:
                            logging.debug(
                                "Json: loading host {0} for user {1}".format(
                                    host.get("name"), self.posix_user))
                            self._allowed_ssh_hosts[host.get("name")] = {
                                'name': host.get("name"),
                                'fqdn': host.get("hostname"),
                                'ssh_port': host.get("port"),
                                'user': host.get("user"),
                                'hostgroups': host.get("hostgroups")
                            }

    def list_allowed(self):
        # is our list empty ?
        if not self._allowed_ssh_hosts:
            self._load_user_allowed_hosts()
        return self._allowed_ssh_hosts
