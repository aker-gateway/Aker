# -*- coding: utf-8 -*-
#
#       Copyright 2016 Ahmed Nazmy 
#

# Meta
__license__ = "AGPLv3"
__author__ = 'Ahmed Nazmy <ahmed@nazmy.io>'

import json
import logging
from types import NoneType

_IPA_LOADED_=True

try:
	import pyhbac
	from ipalib import api, errors, output, util
	from ipalib import Command, Str, Flag, Int
	from ipalib.cli import to_cli
	from ipalib import _, ngettext
	from ipapython.dn import DN
	from ipalib.plugable import Registry
except ImportError as e:
	logging.warn("There was an error loading ipalib, falling back to JSON")
	_IPA_LOADED_=False


class Authority(object):
	'''
	Base class to implement shared functionality
	This should enable different authorities to manage allowed connections 
	'''

	def __init__(self,username,gateway_hostgroup):
		self._all_ssh_hosts = []
		self._allowed_ssh_hosts = []
		self.user = username
		self.gateway_hostgroup = gateway_hostgroup
	
	def list_allowed(self):
		pass


	def _load_all_hosts(self):
		pass


class IPA(Authority):
	'''
	Abstract represtation of  user allowed hosts.
	Currently relaying on FreeIPA API
	'''
	def __init__(self,username,gateway_hostgroup):
		super(Hosts,self).__init__(username,gateway_hostgroup)
		api.bootstrap(context='cli')
		api.finalize()
		try:
			api.Backend.rpcclient.connect()
		except AttributeError:
			api.Backend.xmlclient.connect() #FreeIPA < 4.0 compatibility
		self.api = api
		
		
	def convert_to_ipa_rule(self,rule):
		# convert a dict with a rule to an pyhbac rule
		ipa_rule = pyhbac.HbacRule(rule['cn'][0])
		ipa_rule.enabled = rule['ipaenabledflag'][0]
		# Following code attempts to process rule systematically
		structure = \
			(('user',       'memberuser',    'user',    'group',        ipa_rule.users),
			 ('host',       'memberhost',    'host',    'hostgroup',    ipa_rule.targethosts),
			 ('sourcehost', 'sourcehost',    'host',    'hostgroup',    ipa_rule.srchosts),
			 ('service',    'memberservice', 'hbacsvc', 'hbacsvcgroup', ipa_rule.services),
			)
		for element in structure:
			category = '%scategory' % (element[0])
			if (category in rule and rule[category][0] == u'all') or (element[0] == 'sourcehost'):
				# rule applies to all elements
				# sourcehost is always set to 'all'
				element[4].category = set([pyhbac.HBAC_CATEGORY_ALL])
			else:
				# rule is about specific entities
				# Check if there are explicitly listed entities
				attr_name = '%s_%s' % (element[1], element[2])
				if attr_name in rule:
					element[4].names = rule[attr_name]
				# Now add groups of entities if they are there
				attr_name = '%s_%s' % (element[1], element[3])
				if attr_name in rule:
					element[4].groups = rule[attr_name]
		if 'externalhost' in rule:
				ipa_rule.srchosts.names.extend(rule['externalhost']) #pylint: disable=E1101
		return ipa_rule
		
		
	def _load_all_hosts(self,api):
		'''
		This function prints a list of all hosts. This function requires
		one argument, the FreeIPA/IPA API object.
		'''
		#FIXME: make search hostgroup configurable instead of hardcoded
		result = api.Command.host_find(not_in_hostgroup=self.gateway_hostgroup)['result']
		members = []
		for host in result:
			hostname = host['fqdn']
			if isinstance(hostname, (tuple, list)):
				hostname = hostname[0]
				members.append(hostname)
			logging.debug("Core: ALL_HOSTS %s", hostname)

		return members
		
		
	def _load_user_allowed_hosts(self):
		self._all_ssh_hosts = self._load_all_hosts(self.api)
		hbacset = []
		rules = []
		sizelimit = None
		hbacset = api.Command.hbacrule_find(sizelimit=sizelimit)['result']
		for rule in hbacset:
			ipa_rule = self.convert_to_ipa_rule(rule)
			if ipa_rule.enabled:
				rules.append(ipa_rule)		

		for ipa_rule in rules:
			for host in self._all_ssh_hosts:
				request = pyhbac.HbacRequest()
		
				#Build request user/usergroups
				try:
					request.user.name = self.user
					search_result = api.Command.user_show(request.user.name)['result']
					groups = search_result['memberof_group']
					if 'memberofindirect_group' in search_result:
						groups += search_result['memberofindirect_group']
					request.user.groups = sorted(set(groups))
				except:
					pass
		
				# Add sshd service + service groups it belongs to
				try:
					request.service.name = "sshd"
					service_result = api.Command.hbacsvc_show(request.service.name)['result']
					if 'memberof_hbacsvcgroup' in service_result:
						request.service.groups = service_result['memberof_hbacsvcgroup']
				except:
					pass	
				
				# Build request host/hostgroups	
				try:
					request.targethost.name = host
					tgthost_result = api.Command.host_show(request.targethost.name)['result']
					groups = tgthost_result['memberof_hostgroup']
					if 'memberofindirect_hostgroup' in tgthost_result:
						groups += tgthost_result['memberofindirect_hostgroup']
					request.targethost.groups = sorted(set(groups))                
				except:
					pass
				try:
					logging.debug("Core: Checking %s", host)
					res = request.evaluate([ipa_rule])
					if res == pyhbac.HBAC_EVAL_ALLOW:	
						logging.debug("Core: ALLOWED_HOSTS %s", host)
						self._allowed_ssh_hosts.append(host)
				except pyhbac.HbacError as (code, rule_name):
					if code == pyhbac.HBAC_EVAL_ERROR:
						#TODO log error
						print('Native IPA HBAC rule "%s" parsing error: %s' % \
							(rule_name, pyhbac.hbac_result_string(code)))
				except (TypeError, IOError) as (info):
					print('Native IPA HBAC module error: %s' % (info))
		
	
	def list_allowed(self):
		self._all_ssh_hosts = self._load_all_hosts(self.api)
		self._load_user_allowed_hosts()
		return self._allowed_ssh_hosts

# TODO: remove the placeholder and allow configuration from json file.
class JsonConfig(Authority):
	'''
	Fetch the authority informataion from a JSON configuration 
	'''
	def __init__(self,username,gateway_hostgroup):
		super(JsonConfig,self).__init__(username,gateway_hostgroup)
		self.__init_json_config()

	def __init_json_config(self):
		pass

	def list_allowed(self):
		# TODO: Don't return hardcoded value
		return ["pinky.ratman.org"]

class AuthorityFactory(object):
	#TODO: Register authorities via annotations?
	@staticmethod
	def getAuthority(choice):
		'''
		Fetch the authority class based on a type
		'''
		types = {
			"json":lambda: JsonConfig,
			"IPA": lambda: IPA if _IPA_LOADED_ else JsonConfig
		}
		selection = types.get(choice,None)
		if selection is None:
			raise Exception("core: \"{}\" is not a valid authority".format(choice))
		else:
			return selection()