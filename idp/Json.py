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
	'''
	Fetch the authority informataion from a JSON configuration 
	'''
	def __init__(self,config,username,gateway_hostgroup):
		super(Json,self).__init__(username,gateway_hostgroup)
		logging.info("Json: loaded")
		self.config = config
		self.__init_json_config()

	def __init_json_config(self):
		# Load the configration from the already intitialised config parser
		hosts_file = self.config.get("General","hosts_file","hosts.json")
		
		try:
			JSON = json.load(open(hosts_file,'r'))
		except ValueError as e :
			logging.error("JSON: could not read json file {0} , error : {1}".format(hosts_file,e.message))
		
		self._all_ssh_hosts = JSON["hosts"]
		self.users = JSON.get("users")
		self.groups = JSON.get("groups")
		self.__define_allowed_hosts()

	def __define_allowed_hosts(self):
		'''
		Fetch the allowed hosts based on if the user has a record in the users array.
		Fetch hosts that are associated with selected user or groups the user is a member of
		'''
		user = next((user for user in self.users if user.get("username") == self.user), None)
		if(user == None):
			self._allowed_ssh_hosts = []
			return
		userGroups = user.get("groups")
		
		for h in self._all_ssh_hosts:
			if h.get("users") is not None:
				for u in h.get("users"):
				 	if self.user == u:
						self.__add_host_to_allowed(h.get("hostname"))


		if userGroups is not None:
			for h in self._all_ssh_hosts:
				if h.get("groups") is not None:
					for g in user.get("groups"):
						if g in h.get("groups"):
							self.__add_host_to_allowed(h.get("hostname"))

	def __add_host_to_allowed(self,host):
		'''
		Add a unique host to the list of allowed hosts
		'''
		if host not in self._allowed_ssh_hosts:
			logging.debug("Json: adding host {0} to allowed hosts".format(host))
			self._allowed_ssh_hosts.insert(0,host)		

	def list_allowed(self):
		# is our list empty ?
		if not self._allowed_ssh_hosts:
			self.__define_allowed_hosts()
		return self._allowed_ssh_hosts
