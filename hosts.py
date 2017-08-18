# -*- coding: utf-8 -*-
#
#       Copyright 2016 Ahmed Nazmy 
#

# Meta
__license__ = "AGPLv3"
__author__ = 'Ahmed Nazmy <ahmed@nazmy.io>'

import json
import logging
import redis
from IdPFactory import IdPFactory


class HostGroup(object):
	"""

	"""
	
	def __init__(self, name):
		self.name = name
		self.hosts = []
           
	def __str__(self):
		return "name:%s, hosts:%s" % (self.fqdn, self.ssh_port,list(self.hosts))
		
	def __iter__(self):
		return self
		
	def add_host(hostname):
		self.hosts.append(hostname)
	
		
class HostGroups(object):
	"""
	Class representing hostgroups i.e. server groups,
	 visible to a user
	"""
	
	def __init__(self,user):
		self.user = user
		self.user_hostgroups = {}
		
	def create_hostgroup(self,hostgroup):
		new_hostgroup = HostGroup(hostgroup)
		self.user_hostgroups[new_hostgroup.name] = {}
		
	def add_host_to_hostgroups(self,host):
		for group in host.hostgroups:
			if group in self.user_hostgroups:
				self.user_hostgroups[group]= json.dumps(vars(group)) 
			else:
				self.create_hostgroup(group)
				self.user_hostgroups[group][host.fqdn]= json.dumps(vars(group))

	def list(self):
		return self.user_hostgroups
						
	def __iter__(self):
		return self



class Host(object):
	"""
	Class representing a single server entry, 
	each Host/server has to be a membor of at least one 
	hostgroup. Servers have the following attributes :
	
	Attributes
	fqdn: fully qualified domain name
	ssh_port: server ssh port , default is 22
	hostgroups: list of hostgroups this server is part of
	"""
	
	def __init__(self, name,memberof_hostgroups, ssh_port=22):
		self.fqdn = name
		self.ssh_port = ssh_port
		self.hostgroups = memberof_hostgroups
   
	def equal(self,server):
		if self.fqdn == server.fqdn and self.ssh_port == server.ssh_port:
			return True
		else:
			return False
            
	def __str__(self):
		return "fqdn:%s, ssh_port:%d, hostgroups:%s" % (self.fqdn, self.ssh_port,list(self.hostgroups))
		
	def __iter__(self):
		return self



class Hosts(object):
	"""
	A class to handle all interactions with hosts allowed to the user,
	it handles operations between cache(Redis) and backend identity providers
	like IPA, Json etc..
	
	The responsibility of defining HBAC (hosts allowed to the user) lies on the
	underlaying identity provider .
	"""
	def __init__(self,config,username,gateway_hostgroup,idp):
		self._allowed_ssh_hosts = {}
		self.user = username
		self.hostgroups= HostGroups(self.user)
		# username is the redis key, well kinda 
		self.hosts_cache_key  = self.user+":hosts"
		self.hostgroups_cache_key  = self.user+":hostgroups"
		self.gateway_hostgroup = gateway_hostgroup
		self.idp = IdPFactory.getIdP(idp)(config,username,gateway_hostgroup)
		#TODO: do we need a configurable redis host?
		self.redis = self._init_redis_conn('localhost')
		
		
	def _init_redis_conn(self,RedisHost):
		redis_connection = redis.StrictRedis(RedisHost, db=0, decode_responses = True)		
		try:
			if redis_connection.ping():
				return redis_connection
		except Exception as e:
			logging.error("Hosts: all subsequent calls will fallback to backened idp, cache error: {0}".format(e.message))
			return None
	
	def _load_hosts_from_cache(self, hkey):
		
		result = self.redis.hgetall(hkey)
		cached = False
		if result is not None:
			try:
				#Clear our list first
				#del self._allowed_ssh_hosts[:]
				
				#Clear our dict first
				self._allowed_ssh_hosts.clear()
				
				for k,v in result.iteritems():					
					#Deserialize back from redis
					hostentry= Host(json.loads(v)['fqdn'],json.loads(v)['hostgroups'])
					self._allowed_ssh_hosts[hostentry.fqdn] = hostentry
					cached = True
			except Exception as e:
				logging.error("Hosts: redis error: {0}".format(e.message))
				cached = False 			
		else:
			logging.info("Hosts: no hosts loaded from cache for user %s" % self.user) 
			cached = False
				
		return cached 

	
	def _save_hosts_to_cache(self, hosts):
		"""
		hosts passed to this function should be a dict of Host object		
		"""
		# Delete existing cache if any
		try:
			self._del_cache_key(self.hosts_cache_key )
			logging.debug("Hosts: deleting hosts for user {0} from cache".format(self.user))
		except Exception as e:
			logging.error("Hosts: error deleting hosts from cache: {0}".format(e.message))		
		
		# populate cache with new entries	
		for host in hosts.values():
			try:
				# Serialize (cache) Host objects in redis under $user:hosts
				self.redis.hset(self.hosts_cache_key ,host.fqdn,json.dumps(vars(host)))
				logging.debug("Hosts: adding host {0} to cache".format(host.fqdn))
				hostentry = None
			except Exception as e:
				logging.error("Hosts: error saving to cache : {0}".format(e.message))
		
		for host in hosts.values():
			try:
				for group in host.hostgroups:
					logging.debug("DEBUG:: %s" % group)
			except Exception as e:
				logging.error("Hosts: error saving to cache : {0}".format(e.message))
		
	
	def _del_cache_key(self,hkey):
		try:
			self.redis.delete(hkey)
		except Exception as e:
			logging.error("Hosts: error deleting from cache : {0}".format(e.message))
			
			
	
	def list_allowed(self,from_cache=True):
		
		cached=False
		
		#load from cache
		if from_cache:
			# is redis up ?
			if self.redis is not None :
				cached = self._load_hosts_from_cache(self.hosts_cache_key )
		
		#backened cache has some entries for us?
		if cached is True :
			logging.info("Hosts: loading hosts from cache")
			return self._allowed_ssh_hosts

		else:
			
			#Clear current hosts dict
			self._allowed_ssh_hosts.clear()
			
			#Passing the baton from the backend 
			self._backend_hosts = self.idp.list_allowed()
			
			#Build Host objects out of items we got from backend
			for backend_host,backend_host_attributes in self._backend_hosts.iteritems():
				hostentry= Host(backend_host_attributes['fqdn'],backend_host_attributes['hostgroups'])
				self._allowed_ssh_hosts[hostentry.fqdn] = hostentry
				self.hostgroups.add_host_to_hostgroups(hostentry)
			if self.redis is not None :
				self._save_hosts_to_cache(self._allowed_ssh_hosts)
			return self._allowed_ssh_hosts























