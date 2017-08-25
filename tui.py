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

class MenuItem(urwid.Text):
    def __init__(self, caption):
        urwid.Text.__init__(self, caption)
        urwid.register_signal(self.__class__, ['connect'])

        
    def keypress(self, size, key):
        if key == 'enter':
            urwid.emit_signal(self, 'connect')
        else:
            return key
            
    def selectable(self):
        return True 

    
class Window(object):
	""" Where all the Tui magic happens,
		handles creating urwid widgets and
		user keypresses 
		"""
	
	def __init__(self,aker_core):   
		self.aker = aker_core
		self.draw()
	
	
	def refresh_hosts(self,hosts):
		body = []
		#for hostname in hosts:
		for host in hosts.values():
			# Use Host() FQDN as button text
			host_menuitem = MenuItem("%s" % (host.fqdn))
			urwid.connect_signal(host_menuitem, 'connect', self.host_chosen, host.fqdn) # host chosen action
			body.append(urwid.AttrMap(host_menuitem,'body', focus_map='SSH_focus'))
			logging.debug("TUI: adding host %s to user %s " % (host.fqdn,self.aker.user.name))
		return urwid.ListBox(urwid.SimpleFocusListWalker(body))

	def refresh_hostgroups(self,hostgroups):
		body = []
		for group in hostgroups.values():
			# Use HostGroup() name as button text
			group_menuitem = MenuItem("%s" % (group.name))
			urwid.connect_signal(group_menuitem, 'connect', self.group_chosen, group.name) # host chosen action
			body.append(urwid.AttrMap(group_menuitem,'body', focus_map='SSH_focus'))
			logging.debug("TUI: adding group %s to user %s listbox" % (group.name,self.aker.user.name))
		return urwid.ListBox(urwid.SimpleFocusListWalker(body))
			
	def host_chosen(self,choice):
		username = self.aker.user.name
		# TODO: per host port
		port = self.aker.port
		logging.debug("TUI: user %s chose server %s " % (username,choice))
		self.loop.draw_screen()
		self.aker.init_connection(choice)
	
	def group_chosen(self,choice):
		logging.debug("TUI: user %s chose group %s " % (self.aker.user.name,choice))
		self.top.body = self.hosts_frame
		self.loop.draw_screen()
		
	

    
	def draw(self):
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
		
		
		self.header_text = [
			('key', "Aker"), " ",
			('msg', "User:"),
			('key', "%s" % self.aker.posix_user), " "]
		
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
        
		# Hosts ListBox 
		self.hosts_listbox = self.refresh_hosts(self.aker.user.allowed_ssh_hosts)
		self.hosts_map = urwid.AttrWrap(self.hosts_listbox,'body')
		
		#Hostgroups ListBox
		self.hostgroups_listbox = self.refresh_hostgroups(self.aker.user.hostgroups)
		self.hostgroups_map = urwid.AttrWrap(self.hostgroups_listbox,'body')
		
        # Hostgroups edit Text area to capture user input    
		self.groups_search_edit = urwid.Edit("Type to search:\n")
		urwid.connect_signal(self.groups_search_edit, 'change', self.groups_search_change, self.hostgroups_listbox) # search field change action
		
		# Hosts edit Text area to capture user input    
		self.search_edit = urwid.Edit("Type to search:\n")
		urwid.connect_signal(self.search_edit, 'change', self.search_change, self.hosts_listbox) # search field change action


				
		# Hosts frame
		self.hosts_frame = urwid.Frame(self.hosts_map, header=self.search_edit)
		
		# Hostgroups frame
		self.groups_frame = urwid.Frame(self.hostgroups_map, header=self.groups_search_edit)		
		
		#Footer
		self.footer_text = urwid.Text(self.footer_text, align='center')
		self.footer = urwid.AttrMap(self.footer_text, 'foot')
		
		# Popup
		self.popup = SimplePopupLauncher()
		self.popup_padding = urwid.Padding(self.popup, 'right', 20)
		self.popup_map = urwid.AttrMap(self.popup_padding, 'indicator')
		
		# Header
		self.header_widget = urwid.Text(self.header_text, align='left')
		self.header_map = urwid.AttrMap(self.header_widget, 'head')
		self.header = urwid.Columns([self.header_map, self.popup_map])
		
		# Hosts top most frame
		self.top = urwid.Frame(self.groups_frame, header=self.header, footer=self.footer)
		self.screen = urwid.raw_display.Screen()
		
		
		#MainLoop start
		self.loop = urwid.MainLoop(self.top, palette=self.palette, unhandled_input=self.update_search_edit,screen=self.screen, pop_ups=True)
		
		

	def search_change(self,edit, text, list):
		logging.debug("TUI: host search edit key <{0}>".format(text))
		del list.body[:] # clear listbox
		for hostentry in self.aker.user.allowed_ssh_hosts:
			if text in hostentry:
				host = MenuItem("%s" % (hostentry))
				urwid.connect_signal(host, 'connect', self.host_chosen, hostentry)
				list.body.append(urwid.AttrMap(host, 'body', focus_map='SSH_focus'))
				
	def groups_search_change(self,edit, text, list):
		logging.debug("TUI: hostgroup search edit key <{0}>".format(text))
		del list.body[:] # clear listbox
		for groupentry in self.aker.user.hostgroups:
			if text in groupentry:
				group = MenuItem("%s" % (groupentry))
				urwid.connect_signal(group, 'connect', self.group_chosen, groupentry)
				list.body.append(urwid.AttrMap(group, 'body', focus_map='SSH_focus'))
				
	def update_search_edit(self,key):
		if not urwid.is_mouse_event(key):
			if key == 'esc':
				self.groups_search_edit.set_edit_text("")
			elif key == 'f5':
				self.fetch_hosts_from_idp()
			elif key == 'f9':
				logging.info("TUI: User {0} logging out of Aker".format(self.aker.user.name))
				raise urwid.ExitMainLoop()
			else:
				
				self.top.get_body().keypress((100, 50), key)
		return True
	
	def fetch_hosts_from_idp(self):
		self.aker.user.refresh_allowed_hosts(False)
		#TODO: refactor below ?
		self.search_change(self.search_edit,"",self.hosts_listbox)
		self.popup_message("Hosts Refreshed")
		
		
	def popup_message(self, message):
		self.popup.message = str(message)
		self.popup.open_pop_up()

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
