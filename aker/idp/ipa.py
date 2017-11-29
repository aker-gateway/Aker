# -*- coding: utf-8 -*-
#
#       Copyright 2017 Ahmed Nazmy
#

# Meta


import logging
import pyhbac

from ipalib import _, ngettext
from ipalib import api, errors, output, util
from ipalib import Command, Str, Flag, Int
from ipalib.cli import to_cli
from ipalib.plugable import Registry
from ipapython.dn import DN

from ..idp_factory import IdP


class Ipa(IdP):
    """Abstract represtation of user allowed hosts.
    Currently relying on FreeIPA API"""

    def __init__(self, config, username, gateway_hostgroup):
        super(Ipa, self).__init__(username, gateway_hostgroup)
        logging.info('IPA: loaded')
        api.bootstrap(context='cli')
        api.finalize()
        try:
            api.Backend.rpcclient.connect()
        except AttributeError:
            api.Backend.xmlclient.connect()  # FreeIPA < 4.0 compatibility
        self.api = api
        self.default_ssh_port = config.ssh_port

    def list_allowed(self):
        self._all_ssh_hosts = self._load_all_hosts()
        self._load_user_allowed_hosts()
        return self._allowed_ssh_hosts

    @staticmethod
    def convert_to_ipa_rule(rule):
        # convert a dict with a rule to an pyhbac rule
        ipa_rule = pyhbac.HbacRule(rule['cn'][0])
        ipa_rule.enabled = rule['ipaenabledflag'][0]
        # Following code attempts to process rule systematically
        structure = (
            ('user', 'memberuser', 'user', 'group', ipa_rule.users),
            ('host', 'memberhost', 'host', 'hostgroup', ipa_rule.targethosts),
            ('sourcehost', 'sourcehost', 'host', 'hostgroup', ipa_rule.srchosts),
            ('service', 'memberservice', 'hbacsvc', 'hbacsvcgroup', ipa_rule.services),
        )
        for element in structure:
            category = '%scategory' % (element[0])
            if (category in rule and rule[category][0] == u'all') or (
                    element[0] == 'sourcehost'):
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
            ipa_rule.srchosts.names.extend(
                rule['externalhost'])  # pylint: disable=E1101
        return ipa_rule

    def _load_all_hosts(self):
        """This function prints a list of all hosts. This function requires
        one argument, the FreeIPA/IPA API object"""
        result = self.api.Command.host_find(
            not_in_hostgroup=self.gateway_hostgroup)['result']
        members = {}
        for ipa_host in result:
            ipa_hostname = ipa_host['fqdn']
            if isinstance(ipa_hostname, (tuple, list)):
                ipa_hostname = ipa_hostname[0]
            members[ipa_hostname] = {'fqdn': ipa_hostname}
            logging.debug('IPA: ALL_HOSTS %s', ipa_hostname)

        return members

    def _load_user_allowed_hosts(self):
        self._all_ssh_hosts = self._load_all_hosts()
        hbacset = []
        rules = []
        sizelimit = None
        hbacset = api.Command.hbacrule_find(sizelimit=sizelimit)['result']
        for rule in hbacset:
            ipa_rule = self.convert_to_ipa_rule(rule)
            # Add only enabled rules
            if ipa_rule.enabled:
                rules.append(ipa_rule.name)

        for host, host_attributes in self._all_ssh_hosts.iteritems():
            try:
                hostname = host_attributes['fqdn']
                logging.debug('IPA: Checking %s', hostname)
                ret = api.Command.hbactest(
                    user=self.user.decode('utf-8'),
                    targethost=hostname,
                    service=u'sshd',
                    rules=rules)
                if ret['value']:
                    result = api.Command.host_show(
                        host_attributes['fqdn'])['result']
                    memberof_hostgroup = result['memberof_hostgroup']
                    # TODO: Add per-host ssh port checks
                    sshport = self.default_ssh_port
                    self._allowed_ssh_hosts[host] = {
                        'fqdn': hostname,
                        'hostgroups': memberof_hostgroup,
                        'ssh_port': sshport,
                    }
                    logging.debug('IPA: ALLOWED_HOSTS %s', host)
            except Exception as exc:
                logging.error('IPA: error evaluating HBAC : %s', exc.message)
