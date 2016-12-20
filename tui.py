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
		for hostname in hosts:
			host = MenuItem("%s" % (hostname))
			urwid.connect_signal(host, 'connect', self.host_chosen, hostname) # host chosen action
			body.append(urwid.AttrMap(host,'body', focus_map='SSH_focus'))
		return urwid.ListBox(urwid.SimpleFocusListWalker(body))
	
	def host_chosen(self,choice):
		username = self.aker.user.name
		port = self.aker.port
		logging.debug("TUI: init conenction to %s as %s on port %s" % (choice,username,port))
		#os.system("ssh -l %s -p %s %s" % (username,port,choice))
		self.loop.draw_screen()
		self.aker.init_connection(choice)
		
    
    
	def draw(self):
		self.palette = [
            ('body', 'black', 'light gray'),  # Normal Text
            ('focus', 'light green', 'black', 'standout'),  # Focus
            ('head', 'white', 'dark gray', 'standout'),  # Header
            ('foot', 'light gray', 'dark gray'),  # Footer Separator
            ('key', 'light green', 'dark gray', 'bold'),
            ('title', 'white', 'black', 'bold'),
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
            ('msg', "Quit:"),
            ('key', "F9"), " ",
            ('msg', "By:"),
            ('key', "Ahmed Nazmy")]
        
		# Hosts ListBox 
		self.hosts_listbox = self.refresh_hosts(self.aker.user.allowed_ssh_hosts)
		self.hosts_map = urwid.AttrWrap(self.hosts_listbox,'body')
		
        # Edit Text area to capture user input    
		self.search_edit = urwid.Edit("Type to search:\n")
		urwid.connect_signal(self.search_edit, 'change', self.search_change, self.hosts_listbox) # search field change action
		
		# Frame
		self.frame = urwid.Frame(self.hosts_map, header=self.search_edit)
		
		
		#Footer
		self.footer_text = urwid.Text(self.footer_text, align='center')
		self.footer = urwid.AttrMap(self.footer_text, 'foot')
		
		# Header
		self.header_widget = urwid.Text(self.header_text, align='left')
		self.header_map = urwid.AttrMap(self.header_widget, 'head')
		
		# Top most frame
		self.top = urwid.Frame(self.frame, header=self.header_map, footer=self.footer)
		self.screen = urwid.raw_display.Screen()
		
		#MainLoop start
		self.loop = urwid.MainLoop(self.top, palette=self.palette, unhandled_input=self.update_search_edit,screen=self.screen)
		
		

	def search_change(self,edit, text, list):
		logging.debug("TUI: search edit key <{0}>".format(text))
		del list.body[:] # clear listbox
		for hostentry in self.aker.user.allowed_ssh_hosts:
			if text in hostentry:
				host = MenuItem("%s" % (hostentry))
				urwid.connect_signal(host, 'connect', self.host_chosen, hostentry)
				list.body.append(urwid.AttrMap(host, 'body', focus_map='SSH_focus'))
				
	def update_search_edit(self,key):
		if not urwid.is_mouse_event(key):
			if key == 'esc':
				self.search_edit.set_edit_text("")
			elif key == 'f9':
				# TODO: Fix the need for multiple F9s to exit
				raise urwid.ExitMainLoop()
			else:
				self.search_edit.keypress((10, ), key)
		return True

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
