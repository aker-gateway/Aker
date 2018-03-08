# -*- coding: utf-8 -*-
#
#       Copyright 2016 Ahmed Nazmy
#

# Meta
__license__ = "AGPLv3"
__author__ = 'Ahmed Nazmy <ahmed@nazmy.io>'


import urwid
import aker
import signal
import logging
import os
from popup import SimplePopupLauncher


class Listing(urwid.ListBox):
    """
    Base class to handle listbox actions
    """

    def __init__(self, items=None):
        self.search = Search()
        self.search.update_text("Type to search:\n")
        self._items = []
        if items is not None:
            for item in items:
                listitem = MenuItem("%s" % (item))
                self._items.append(
                    urwid.AttrMap(
                        listitem,
                        'body',
                        focus_map='SSH_focus'))
        super(Listing, self).__init__(urwid.SimpleFocusListWalker(self._items))

    def updatelist(self, items):
        self.empty()
        for item in items:
            self.add_item(item)

    def add_item(self, item):
        listitem = MenuItem("%s" % (item))
        self.body.append(
            urwid.AttrMap(
                listitem,
                'body',
                focus_map='SSH_focus'))

    def empty(self):
        del self.body[:]  # clear listbox

    def get_selected(self):
        return self.focus

    def get_box(self):
        self.search.clear()
        return urwid.Frame(urwid.AttrWrap(self, 'body'), header=self.search)


class HostList(Listing):
    """
    Class to handle hosts screen actions,
    keypresses for now.
    """

    def __init__(self, hosts=None):
        super(HostList, self).__init__(hosts)

    def keypress(self, size, key):
        if (key == 'enter') or (key == 'right'):
            urwid.emit_signal(
                self,
                'connect',
                self.focus.original_widget.get_caption())
            key = None
        elif key == 'esc':
            if self.search.get_edit_text() == "":
                key = 'left'
            else:
                self.search.clear()
                key = None
        # Unless its arrow keys send keypress to search box,
        # implies emitting EditBox "change" signal
        elif key not in ['right', 'down', 'up', 'left', 'page up', 'page down']:
            self.search.keypress((10,), key)
        return super(HostList, self).keypress(size, key)


class HostGroupList(Listing):
    """
    Class to handle hostgroups screen actions,
    keypresses for now.
    """

    def __init__(self, hostgroups=None):
        super(HostGroupList, self).__init__(hostgroups)

    def keypress(self, size, key):
        if (key == 'enter') or (key == 'right'):
            # emit signal to call hostgroup_chosen_handler with MenuItem caption,
            # caption is group name showing on screen
            if self.focus is not None:
                urwid.emit_signal(
                    self,
                    'group_chosen',
                    self.focus.original_widget.get_caption())
            key = None
        elif key == 'esc':
            self.search.clear()
            key = None
        # Unless its arrow keys send keypress to search box,
        # implies emitting EditBox "change" signal
        elif key not in ['right', 'down', 'up', 'left', 'page up', 'page down']:
            self.search.keypress((10,), key)
        return super(HostGroupList, self).keypress(size, key)


class Header(urwid.Columns):
    def __init__(self, text):
        self.text = text
        self.header_widget = urwid.Text(self.text, align='left')
        self.popup = SimplePopupLauncher()
        self.popup_padding = urwid.Padding(self.popup, 'right', 20)
        self.popup_map = urwid.AttrMap(self.popup_padding, 'indicator')
        self.header_map = urwid.AttrMap(self.header_widget, 'head')
        super(Header, self).__init__([self.header_map, self.popup_map])

    def update_text(self, text):
        self.text = text
        self.header_map.original_widget.set_text(self.text)

    def popup_message(self, message):
        logging.debug("TUI: popup message is {0}".format(message))
        self.popup.message = str(message)
        self.popup.open_pop_up()


class Footer(urwid.AttrMap):
    def __init__(self, text):
        self.footer_text = urwid.Text(text, align='center')
        super(Footer, self).__init__(self.footer_text, 'foot')


class Search(urwid.Edit):
    def __init__(self):
        super(Search, self).__init__()

    def update_text(self, caption):
        self.set_caption(caption)

    def clear(self):
        self.set_edit_text("")


class MenuItem(urwid.Text):
    def __init__(self, caption):
        self.caption = caption
        urwid.Text.__init__(self, self.caption)

    def keypress(self, size, key):
        return key

    def selectable(self):
        return True

    def get_caption(self):
        return str(self.caption)


class Window(object):
    """
    Where all the Tui magic happens,
    handles creating urwid widgets and
    user interactions
    """

    def __init__(self, aker_core):
        self.aker = aker_core
        self.user = self.aker.user
        self.current_hostgroup = ""
        self.set_palette()

    def set_palette(self):
        self.palette = [
            ('body', 'black', 'light gray'),  # Normal Text
            ('focus', 'light green', 'black', 'standout'),  # Focus
            ('head', 'white', 'dark gray', 'standout'),  # Header
            ('foot', 'light gray', 'dark gray'),  # Footer Separator
            ('key', 'light green', 'dark gray', 'bold'),
            ('title', 'white', 'black', 'bold'),
            ('popup', 'white', 'dark red'),
            ('msg', 'yellow', 'dark gray'),
            ('SSH', 'dark blue', 'light gray', 'underline'),
            ('SSH_focus', 'light green', 'dark blue', 'standout')]  # Focus

    def draw(self):
        self.header_text = [
            ('key', "Aker"), " ",
            ('msg', "User:"),
            ('key', "%s" % self.user.name), " "]

        self.footer_text = [
            ('msg', "Move:"),
            ('key', "Up"), ",",
            ('key', "Down"), ",",
            ('key', "Left"), ",",
            ('key', "Right"), ",",
            ('key', "PgUp"), ",",
            ('key', "PgDn"), ",",
            ('msg', "Select:"),
            ('key', "Enter"), " ",
            ('msg', "Refresh:"),
            ('key', "F5"), " ",
            ('msg', "Quit:"),
            ('key', "F9"), " ",
            ('msg', "By:"),
            ('key', "Ahmed Nazmy")]

        # Define widgets
        self.header = Header(self.header_text)
        self.footer = Footer(self.footer_text)
        self.hostgrouplist = HostGroupList(list(self.user.hostgroups.keys()))
        self.hostlist = HostList(list(self.user.allowed_ssh_hosts.keys()))
        self.topframe = urwid.Frame(
            self.hostgrouplist.get_box(),
            header=self.header,
            footer=self.footer)
        self.screen = urwid.raw_display.Screen()

        # Register signals
        urwid.register_signal(HostList, ['connect'])
        urwid.register_signal(HostGroupList, ['group_chosen'])

        # Connect signals
        urwid.connect_signal(
            self.hostgrouplist.search,
            'change',
            self.group_search_handler)
        urwid.connect_signal(
            self.hostgrouplist,
            'group_chosen',
            self.group_chosen_handler)
        urwid.connect_signal(
            self.hostlist.search,
            'change',
            self.host_search_handler)
        urwid.connect_signal(
            self.hostlist,
            'connect',
            self.host_chosen_handler)

        self.loop = urwid.MainLoop(
            self.topframe,
            palette=self.palette,
            unhandled_input=self._input_handler,
            screen=self.screen,
            pop_ups=True)

    def _input_handler(self, key):
        if not urwid.is_mouse_event(key):
            if key == 'f5':
                self.update_lists()
            elif key == 'f9':
                logging.info(
                    "TUI: User {0} logging out of Aker".format(
                        self.user.name))
                raise urwid.ExitMainLoop()
            elif key == 'left':
                # For now if its not hostgroup window left should bring it up
                if self.topframe.get_body() != self.hostgrouplist.get_box():
                    self.current_hostgroup = ""
                    self.hostlist.empty()
                    self.header.update_text(self.header_text)
                    self.topframe.set_body(self.hostgrouplist.get_box())
            else:
                logging.debug(
                    "TUI: User {0} unhandled input : {1}".format(
                        self.user.name, key))

    def group_search_handler(self, search, search_text):
        logging.debug(
            "TUI: Group search handler called with text {0}".format(search_text))
        matchinghostgroups = []
        for hostgroup in self.user.hostgroups.keys():
            if search_text in hostgroup:
                logging.debug(
                    "TUI: hostgroup {1} matches search text {0}".format(
                        search_text, hostgroup))
                matchinghostgroups.append(hostgroup)
        self.hostgrouplist.updatelist(matchinghostgroups)

    def host_search_handler(self, search, search_text):
        logging.debug(
            "TUI: Host search handler called with text {0}".format(search_text))
        matchinghosts = []
        for host in self.user.hostgroups[self.current_hostgroup].hosts:
            if search_text in host:
                logging.debug(
                    "TUI: host {1} matches search text {0}".format(
                        search_text, host))
                matchinghosts.append(host)
        self.hostlist.updatelist(sorted(matchinghosts))

    def group_chosen_handler(self, hostgroup):
        logging.debug(
            "TUI: user %s chose hostgroup %s " %
            (self.user.name, hostgroup))
        self.current_hostgroup = hostgroup
        self.hostlist.empty()
        matchinghosts = []
        for host in self.user.hostgroups[self.current_hostgroup].hosts:
            logging.debug(
                "TUI: host {1} is in hostgroup {0}, adding".format(
                    hostgroup, host))
            matchinghosts.append(host)
        self.hostlist.updatelist(sorted(matchinghosts))
        header_text = [
            ('key', "Aker"), " ",
            ('msg', "User:"),
            ('key', "%s" % self.user.name), " ",
            ('msg', "HostGroup:"),
            ('key', "%s" % self.current_hostgroup)]
        self.header.update_text(header_text)
        self.topframe.set_body(self.hostlist.get_box())

    def host_chosen_handler(self, choice):
        host = choice
        logging.debug("TUI: user %s chose server %s " % (self.user.name, host))
        self.aker.init_connection(host)

    def update_lists(self):
        logging.info(
            "TUI: Refreshing entries for user {0}".format(
                self.aker.user.name))
        self.aker.user.refresh_allowed_hosts(False)
        self.hostgrouplist.empty()
        for hostgroup in self.user.hostgroups.keys():
            self.hostgrouplist.add_item(hostgroup)
        if self.current_hostgroup != "":
            self.hostlist.empty()
            for host in self.user.hostgroups[self.current_hostgroup].hosts:
                self.hostlist.add_item(host)
        self.header.popup_message("Entries Refreshed")

    def start(self):
        logging.debug("TUI: tui started")
        self.loop.run()

    def stop(self):
        logging.debug(u"TUI: tui stopped")
        raise urwid.ExitMainLoop()

    def pause(self):
        logging.debug("TUI: tui paused")
        self.loop.screen.stop()

    def restore(self):
        logging.debug("TUI restored")
        self.loop.screen.start()
