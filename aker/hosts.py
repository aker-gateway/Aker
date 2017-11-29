# -*- coding: utf-8 -*-
#
#       Copyright 2016 Ahmed Nazmy
#

# Meta
__license__ = 'AGPLv3'
__author__ = 'Ahmed Nazmy <ahmed@nazmy.io>'

import json
import logging
from redis import StrictRedis
from .idp_factory import IdPFactory


class HostGroup(object):
    """Class representing single hostgroup.A hostgroup
    holds a list of hosts/servers that are members of it.
    Attributes
    name: Hostgroup name
    """

    def __init__(self, name):
        self.name = name
        self.hosts = []

    def __str__(self):
        return '{0}(name: {1}, hosts:{2})'.format(self.__class__.__name__, self.name, self.hosts)

    def __iter__(self):
        return self

    def add_host(self, hostname):
        self.hosts.append(hostname)


class Host(object):
    """Class representing a single server entry,
    each Host/server has to be a member one or more
    hostgroup. Servers have the following attributes :

    Attributes
    fqdn: fully qualified domain name
    ssh_port: server ssh port , default is 22
    hostgroups: list of hostgroups this server is part of
    """

    def __init__(self, name, memberof_hostgroups, ssh_port=22):
        self.fqdn = name
        self.name = name
        self.ssh_port = ssh_port
        self.hostgroups = memberof_hostgroups

    def equal(self, server):
        return bool(self.fqdn == server.fqdn and self.ssh_port == server.ssh_port)

    def __str__(self):
        return '{0}(fqdn: {1}, ssh_port: {2}, hostgroups: {3}'.format(self.__class__.__name__, self.fqdn, self.ssh_port, self.hostgroups)

    def __iter__(self):
        return self


class Hosts(object):
    """A class to handle all interactions with hosts allowed to the user,
    it handles operations between cache(Redis) and backend identity providers
    like IPA, Json etc..

    The responsibility of defining HBAC (hosts allowed to the user) lies on the
    underlaying identity provider .
    """

    def __init__(self, config, username, gateway_hostgroup, idp):
        self._allowed_ssh_hosts = {}
        self._backend_hosts = None
        self.user = username
        self._hostgroups = {}
        # username is the redis key, well kinda
        self.hosts_cache_key = self.user + ':hosts'
        self.hostgroups_cache_key = self.user + ':hostgroups'
        self.gateway_hostgroup = gateway_hostgroup
        self.idp = IdPFactory.get_idp(idp)(config, username, gateway_hostgroup)
        # TODO: do we need a configurable redis host?
        self.redis = self._init_redis_conn('localhost')

    @staticmethod
    def _init_redis_conn(redis_host):
        redis_connection = StrictRedis(redis_host, db=0, decode_responses=True)
        try:
            if redis_connection.ping():
                return redis_connection
        except Exception as exc:
            logging.error('Hosts: all subsequent calls will fallback to backened idp, cache error: %s', exc.message)
            return None

    def _load_hosts_from_cache(self, hkey):
        result = self.redis.hgetall(hkey)
        cached = False
        if result is not None:
            try:
                for _, val in result.iteritems():
                    # Deserialize back from redis
                    hostentry = Host(
                        json.loads(val)['fqdn'],
                        json.loads(val)['hostgroups'])
                    self._allowed_ssh_hosts[hostentry.fqdn] = hostentry
                    logging.debug('Hosts: loading host %s from cache', hostentry.fqdn)
                    cached = True
            except Exception as exc:
                logging.error('Hosts: redis error: %s', exc.message)
                cached = False
        else:
            logging.info('Hosts: no hosts loaded from cache for user %s', self.user)
            cached = False

        return cached

    def _save_hosts_to_cache(self, hosts):
        """Hosts passed to this function should be a dict of Host object"""
        # Delete existing cache if any
        try:
            self._del_cache_key(self.hosts_cache_key)
            logging.debug('Hosts: deleting hosts for user %s from cache', self.user)
        except Exception as exc:
            logging.error('Hosts: error deleting hosts from cache: %s', exc.message)

        # populate cache with new entries
        for host in hosts.values():
            try:
                # Serialize (cache) Host objects in redis under $user:hosts
                self.redis.hset(
                    self.hosts_cache_key,
                    host.fqdn,
                    json.dumps(
                        vars(host)))
                logging.debug('Hosts: adding host %s to cache', host.fqdn)
            except Exception as exc:
                logging.error('Hosts: error saving to cache: %s', exc.message)

    def _load_hostgroups_from_cache(self, hkey):
        result = self.redis.hgetall(hkey)
        cached = False
        if result is not None:
            try:
                for _, val in result.iteritems():
                    # Deserialize back from redis
                    hostgroupentry = HostGroup(json.loads(val)['name'])
                    for host in json.loads(val)['hosts']:
                        hostgroupentry.add_host(host)
                    self._hostgroups[hostgroupentry.name] = hostgroupentry
                    cached = True
            except Exception as exc:
                logging.error('Hostgroups: redis error: %s', exc.message)
                cached = False
        else:
            logging.info('Hostgroups: no hostgroups loaded from cache for user %s', self.user)
            cached = False
        return cached

    def _save_hostgroups_to_cache(self, hostgroups):
        """Hosts passed to this function should be a dict of HostGroup object"""

        # Delete existing cache if any
        try:
            self._del_cache_key(self.hostgroups_cache_key)
            logging.debug('Hosts: deleting hostgroups for user %s from cache', self.user)
        except Exception as exc:
            logging.error('Hosts: error deleting hostgroups from cache: %s', exc.message)

        for hostgroup in hostgroups.values():
            try:
                logging.debug('Hosts: adding hostgroup %s to cache', hostgroup.name)
                self.redis.hset(
                    self.hostgroups_cache_key,
                    hostgroup.name,
                    json.dumps(vars(hostgroup))
                )
            except Exception as exc:
                logging.error('Hosts: error saving to cache: %s', exc.message)

    def _del_cache_key(self, hkey):
        try:
            self.redis.delete(hkey)
        except Exception as exc:
            logging.error('Hosts: error deleting from cache: %s', exc.message)

    def list_allowed(self, from_cache=True):
        """This function is the interface to the TUI"""

        cached = False

        # Clear our dicts first
        self._allowed_ssh_hosts.clear()
        self._hostgroups.clear()

        # load from cache
        if from_cache:
            # is redis up ?
            if self.redis is not None:
                cached = self._load_hosts_from_cache(self.hosts_cache_key)
                # FIXME: using cached twice!, need better approach
                cached = self._load_hostgroups_from_cache(
                    self.hostgroups_cache_key)

        # backened cache has some entries for us?
        if cached is True:
            logging.info('Hosts: loading hosts from cache')
            return self._allowed_ssh_hosts, self._hostgroups
        # No cached objects
        else:
            # Passing the baton from the backend
            self._backend_hosts = self.idp.list_allowed()

            # Build Host() objects out of items we got from backend
            for _, backend_host_attributes in self._backend_hosts.iteritems():
                hostentry = Host(
                    backend_host_attributes['fqdn'],
                    backend_host_attributes['hostgroups'])
                self._allowed_ssh_hosts[hostentry.fqdn] = hostentry

                # Build HostGroup() objects from items we got from backend
                for group in hostentry.hostgroups:
                    if group not in self._hostgroups:
                        self._hostgroups[group] = HostGroup(group)
                        self._hostgroups[group].add_host(hostentry.fqdn)
                    else:
                        self._hostgroups[group].add_host(hostentry.fqdn)
            # Save entries we got to the cache
            if self.redis is not None:
                self._save_hosts_to_cache(self._allowed_ssh_hosts)
                self._save_hostgroups_to_cache(self._hostgroups)
            return self._allowed_ssh_hosts, self._hostgroups
