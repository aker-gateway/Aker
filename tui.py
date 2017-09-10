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
	def __init__(self, items=None):
		self.search = Search()
		self.search.update_text("Type to search:\n")
		self._items = []
		if items is not None:
			for item in items:
				listitem = MenuItem("%s" % (item))
				self._items.append(urwid.AttrMap(listitem,'body', focus_map='SSH_focus'))
		super(Listing, self).__init__(urwid.SimpleFocusListWalker(self._items))


	def update(self, items):
		self._items = []
		for item in items:
			listitem = MenuItem("%s" % (item))
			self._items.append(urwid.AttrMap(listitem,'body', focus_map='SSH_focus'))
		self.body = urwid.SimpleFocusListWalker(self._items)


	def add_item(self, item):
		listitem = MenuItem("%s" % (item))
		self.body.append(urwid.AttrMap(listitem,'body', focus_map='SSH_focus'))

		
	def empty(self):
		del self.body[:] # clear listbox

		
	def get_selected(self):
		return self.focus
	
	def get_box(self):
		self.search.clear()
		return urwid.Frame(urwid.AttrWrap(self,'body'), header=self.search)


class HostList(Listing):
	def __init__(self, hosts=None):
		super(HostList, self).__init__(hosts)

	def keypress(self, size, key):
		if key == 'enter':
			urwid.emit_signal(self, 'connect', self.focus.original_widget.get_caption())
			key = None
		elif key == 'esc':
			self.search.clear()
			key = None
		#Unless its arrow keys send keypress to search box,
		#implies emitting EditBox "change" signal
		elif key not in ['right', 'down', 'up', 'left','page up','page down']:
			self.search.keypress((10,), key)
		return super(HostList, self).keypress(size, key)
		return key


class HostGroupList(Listing):
	def __init__(self, hostgroups=None):
		super(HostGroupList, self).__init__(hostgroups)

	def keypress(self, size, key):
		if key == 'enter':
			# emit signal to call hostgroup_chosen_handler with MenuItem caption,
			# caption is group name showing on screen
			urwid.emit_signal(self, 'group_chosen',self.focus.original_widget.get_caption())
			key = None
		elif key == 'esc':
			self.search.clear()
			key = None
		#Unless its arrow keys send keypress to search box,
		#implies emitting EditBox "change" signal
		elif key not in ['right', 'down', 'up', 'left','page up','page down']:
			self.search.keypress((10,), key)
		return super(HostGroupList, self).keypress(size, key)	
		

class Header(urwid.Columns):
	def __init__(self,text):
		self.text = text
		self.header_widget = urwid.Text(self.text, align='left')
		self.popup = SimplePopupLauncher()
		self.popup_padding = urwid.Padding(self.popup, 'right', 20)
		self._widget_list=[
				('pack',urwid.AttrMap(self.header_widget, 'head')),
				('pack',urwid.AttrMap(self.popup_padding, 'indicator'))]
		super(Header, self).__init__(self._widget_list)

				
	def popup_message(self, message):
		logging.debug("DEBUG: popup message is {0}".format(message))
		self.popup.message = str(message)	
		self.popup.open_pop_up()
        
class Footer(urwid.AttrMap):
    def __init__(self,text):
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
	user keypresses 
	"""
		
	def __init__(self,aker_core):
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
		('SSH_focus', 'light green', 'dark blue', 'standout')] # Focus


	def draw(self):
		self.header_text = [
			('key', "Aker"), " ",
			('msg', "User:"),
			('key', "%s" % self.user.name), " "]
		
		self.footer_text = [
            ('msg', "Move:"),
            ('key', "Up"), ",", ('key', "Down"), ",",
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
		
		#Define widgets
		self.header= Header(self.header_text)
		self.footer= Footer(self.footer_text)
		self.hostgrouplist= HostGroupList(list(self.user.hostgroups.keys()))
		self.hostlist= HostList(list(self.user.allowed_ssh_hosts.keys()))
		self.topframe = urwid.Frame(self.hostgrouplist.get_box(),header=self.header, footer=self.footer)
		self.screen = urwid.raw_display.Screen()
		
		#Register signals
		urwid.register_signal(HostList, ['connect'])
		urwid.register_signal(HostGroupList, ['group_chosen'])
		
		#Connect signals
		urwid.connect_signal(self.hostgrouplist.search, 'change',self.group_search_handler)
		urwid.connect_signal(self.hostgrouplist, 'group_chosen',self.group_chosen_handler)
		urwid.connect_signal(self.hostlist.search, 'change',self.host_search_handler)
		urwid.connect_signal(self.hostlist, 'connect',self.host_chosen_handler)
		
		self.loop = urwid.MainLoop(self.topframe, palette=self.palette, unhandled_input=self._input_handler,screen=self.screen, pop_ups=True)
		
		
	def _input_handler(self,key):
		if not urwid.is_mouse_event(key):
			if key == 'f5':
				self.update_lists()
			elif key == 'f9':
				logging.info("TUI: User {0} logging out of Aker".format(self.user.name))
				raise urwid.ExitMainLoop()
			elif key == 'left':
				self.current_hostgroup = ""
				self.hostlist.empty()
				self.topframe.set_body(self.hostgrouplist.get_box())
			else:
				logging.debug("TUI: User {0} unhandled input : {1}".format(self.user.name,key))

	def group_search_handler(self,search,search_text):
		logging.debug("TUI: Group search handler called with text {0}".format(search_text))
		self.hostgrouplist.empty()
		for hostgroup in self.user.hostgroups.keys():
			if search_text in hostgroup:
				self.hostgrouplist.add_item(hostgroup)
				logging.debug("DEBUG: hostgroup {1} matches search text {0}".format(search_text,hostgroup))

	def host_search_handler(self,search,search_text):
		logging.debug("TUI: Host search handler called with text {0}".format(search_text))
		self.hostlist.empty()
		for host in self.user.hostgroups[self.current_hostgroup].hosts:
			if search_text in host:
				self.hostlist.add_item(host)
				logging.debug("DEBUG: host {1} matches search text {0}".format(search_text,host))

		
				
	def group_chosen_handler(self,hostgroup):
		logging.debug("TUI: user %s chose hostgroup %s " % (self.user.name,hostgroup))
		self.current_hostgroup = hostgroup
		self.hostlist.empty()
		for host in self.user.hostgroups[self.current_hostgroup].hosts:
				self.hostlist.add_item(host)
				logging.debug("DEBUG: host {1} is in hostgroup {0}, adding".format(hostgroup,host))
		self.topframe.set_body(self.hostlist.get_box())
		
				
	def host_chosen_handler(self,choice):
		host = choice
		logging.debug("TUI: user %s chose server %s " % (self.user.name,host))
		self.aker.init_connection(host)

	def update_lists(self):
		logging.info("TUI: Refreshing entries for user {0}".format(self.aker.user.name))
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
				

	#def __init__(self,aker_core):   
		#self.aker = aker_core
		#self.current_hostgroup=""
		#self.palette = [
            #('body', 'black', 'light gray'),  # Normal Text
            #('focus', 'light green', 'black', 'standout'),  # Focus
            #('head', 'white', 'dark gray', 'standout'),  # Header
            #('foot', 'light gray', 'dark gray'),  # Footer Separator
            #('key', 'light green', 'dark gray', 'bold'),
            #('title', 'white', 'black', 'bold'),
            #('popup', 'white', 'dark red'),
            #('msg', 'yellow', 'dark gray'),
            #('SSH', 'dark blue', 'light gray', 'underline'),
            #('SSH_focus', 'light green', 'dark blue', 'standout')] # Focus
				
		#self.header_text = [
			#('key', "Aker"), " ",
			#('msg', "User:"),
			#('key', "%s" % self.aker.posix_user), " "]
				
		#self.footer_text = [
            #('msg', "Move:"),
            #('key', "Up"), ",", ('key', "Down"), ",",
            #('key', "PgUp"), ",",
            #('key', "PgDn"), ",",
            #('msg', "Select:"),
            #('key', "Enter"), " ",
            #('msg', "Refresh:"),
            #('key', "F5"), " ",
            #('msg', "Quit:"),
            #('key', "F9"), " ",
            #('msg', "By:"),
            #('key', "Ahmed Nazmy")]
            
		#self.draw()
	
	
	#def refresh_hosts(self,hosts,hostgroup):
		#body = []
		#for host in hosts.values():
			#if hostgroup in host.hostgroups:
				## Use Host() FQDN as button text
				#host_menuitem = MenuItem("%s" % (host.fqdn))
				#urwid.connect_signal(host_menuitem, 'connect', self.host_chosen, host.fqdn) # host chosen action
				#body.append(urwid.AttrMap(host_menuitem,'body', focus_map='SSH_focus'))
				#logging.debug("TUI: adding host %s to user %s " % (host.fqdn,self.aker.user.name))
		#return urwid.ListBox(urwid.SimpleFocusListWalker(body))

	#def refresh_hostgroups(self,hostgroups):
		#body = []
		#for group in hostgroups.values():
			## Use HostGroup() name as button text
			#group_menuitem = MenuItem("%s" % (group.name))
			#urwid.connect_signal(group_menuitem, 'connect', self.group_chosen, group.name) # hostgroup chosen action
			#body.append(urwid.AttrMap(group_menuitem,'body', focus_map='SSH_focus'))
			#logging.debug("TUI: adding group %s to user %s listbox" % (group.name,self.aker.user.name))
		#return urwid.ListBox(urwid.SimpleFocusListWalker(body))
			
	#def host_chosen(self,choice):
		#username = self.aker.user.name
		## TODO: per host port
		#port = self.aker.port
		#logging.debug("TUI: user %s chose server %s " % (username,choice))
		#self.loop.draw_screen()
		#self.aker.init_connection(choice)
	
	#def group_chosen(self,choice):
		#logging.debug("TUI: user %s chose hostgroup %s " % (self.aker.user.name,choice))
		#self.current_hostgroup = choice
		
		## Hosts ListBox 
		#self.hosts_listbox = self.refresh_hosts(self.aker.user.allowed_ssh_hosts, choice)
		#self.hosts_map = urwid.AttrWrap(self.hosts_listbox,'body')
		
		## Hosts edit Text area to capture user input    
		#self.search_edit = urwid.Edit("Type to search:\n")
		#urwid.connect_signal(self.search_edit, 'change', self.search_change, self.hosts_listbox) # search field change action

		## Hosts frame
		#self.hosts_frame = urwid.Frame(self.hosts_map, header=self.search_edit)
		
		#self.top.body = self.hosts_frame

		
	

    
	#def draw(self):

        
		
		##Hostgroups ListBox
		#self.hostgroups_listbox = self.refresh_hostgroups(self.aker.user.hostgroups)
		#self.hostgroups_map = urwid.AttrWrap(self.hostgroups_listbox,'body')
		
        ## Hostgroups edit Text area to capture user input    
		#self.groups_search_edit = urwid.Edit("Type to search:\n")
		#urwid.connect_signal(self.groups_search_edit, 'change', self.groups_search_change, self.hostgroups_listbox) # search field change action
		
		## Hostgroups frame
		#self.groups_frame = urwid.Frame(self.hostgroups_map, header=self.groups_search_edit)		
		
		##Footer
		#self.footer_widget = urwid.Text(self.footer_text, align='center')
		#self.footer = urwid.AttrMap(self.footer_widget, 'foot')
		
		## Popup
		#self.popup = SimplePopupLauncher()
		#self.popup_padding = urwid.Padding(self.popup, 'right', 20)
		#self.popup_map = urwid.AttrMap(self.popup_padding, 'indicator')
		
		## Header
		#self.header_widget = urwid.Text(self.header_text, align='left')
		#self.header_map = urwid.AttrMap(self.header_widget, 'head')
		#self.header = urwid.Columns([self.header_map, self.popup_map])
		
		
		## Top most frame, we start with hostgroups widget here
		#self.top = urwid.Frame(self.groups_frame,header=self.header, footer=self.footer)
		#self.top.set_body(self.groups_frame)
		#self.screen = urwid.raw_display.Screen()
		
		
		##MainLoop start
		#self.loop = urwid.MainLoop(self.top, palette=self.palette, unhandled_input=self.keypress_handler,screen=self.screen, pop_ups=True)
		
		

	#def search_change(self,edit, text, list):
		#logging.debug("TUI: host search edit key <{0}>".format(text))
		#del list.body[:] # clear listbox
		#for hostentry in self.aker.user.allowed_ssh_hosts:
			#if text in hostentry and self.current_hostgroup in self.aker.user.allowed_ssh_hosts[hostentry].hostgroups:
				#host = MenuItem("%s" % (hostentry))
				#urwid.connect_signal(host, 'connect', self.host_chosen, hostentry)
				#list.body.append(urwid.AttrMap(host, 'body', focus_map='SSH_focus'))
				
	#def groups_search_change(self,edit, text, list):
		#logging.debug("TUI: hostgroup search edit key <{0}>".format(text))
		#del list.body[:] # clear listbox
		#for groupentry in self.aker.user.hostgroups:
			#if text in groupentry:
				#group = MenuItem("%s" % (groupentry))
				#urwid.connect_signal(group, 'connect', self.group_chosen, groupentry)
				#list.body.append(urwid.AttrMap(group, 'body', focus_map='SSH_focus'))
				
	#def keypress_handler(self,key):
		#if not urwid.is_mouse_event(key):
			#if key == 'esc':
				#if self.top.get_body() == self.groups_frame:
					#self.groups_search_edit.set_edit_text("")
				#elif self.top.get_body() == self.hosts_frame:
					#self.search_edit.set_edit_text("")
			#elif key == 'f5':
				#self.fetch_hosts_groups_from_idp()
			#elif key == 'f9':
				#logging.info("TUI: User {0} logging out of Aker".format(self.aker.user.name))
				#raise urwid.ExitMainLoop()
			#elif key == 'left':
				#if self.top.get_body() == self.hosts_frame:
					#self.groups_search_edit.set_edit_text("")
					#self.top.set_body(self.groups_frame)	
			#else:
				#if self.top.get_body() == self.groups_frame:
					#self.groups_search_edit.keypress((10, ), key)
				#elif self.top.get_body() == self.hosts_frame:
					#self.search_edit.keypress((10, ), key)
		#return True
	
	#def fetch_hosts_groups_from_idp(self):
		#self.aker.user.refresh_allowed_hosts(False)
		##TODO: refactor below ?
		#self.groups_search_change(self.groups_search_edit,"",self.hostgroups_listbox)
		#self.search_change(self.search_edit,"",self.hosts_listbox)
		#self.popup_message("Entries Refreshed")
		
		
	#def popup_message(self, message):
		#self.popup.message = str(message)
		#self.popup.open_pop_up()

	#def start(self):
		#logging.debug("TUI: tui started")
		#self.loop.run()
		
	#def stop(self):
		#logging.debug(u"TUI: tui stopped")
		#raise urwid.ExitMainLoop()
		
	#def pause(self):
		#logging.debug("TUI: tui paused")
		#self.loop.screen.stop()

	#def restore(self):
		#logging.debug("TUI restored")
		#self.loop.screen.start()
