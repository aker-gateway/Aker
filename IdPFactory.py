#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       Copyright 2017 Ahmed Nazmy
#

# Meta
__license__ = "AGPLv3"
__author__ = 'Ahmed Nazmy <ahmed@nazmy.io>'


import logging
import importlib
import sys
import os


class IdPFactory(object):

    @staticmethod
    def getIdP(choice):

        logging.info(
            "IdPFactory: trying dynamic loading of module : {0} ".format(choice))
        # load module from subdir idp
        idp = "idp." + choice
        try:
            idp_module = importlib.import_module(idp)
            idp_class = getattr(idp_module, choice)
        except Exception as e:
            logging.error(
                "IdPFactory: error loading module : {0}".format(
                    e.message))

        return idp_class


class IdP(object):
    '''
    Base class to implement shared functionality
    This should enable different identity providers
    '''

    def __init__(self, username, gateway_hostgroup):
        self._all_ssh_hosts = {}
        self._allowed_ssh_hosts = {}
        self.user = username
        self.gateway_hostgroup = gateway_hostgroup

    def list_allowed(self):
        pass

    def _load_all_hosts(self):
        pass
