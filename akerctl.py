#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       Copyright 2017 Ahmed Nazmy 
#

# Meta
__license__ = "AGPLv3"
__author__ = 'Ahmed Nazmy <ahmed@nazmy.io>'

import sys
from contextlib import closing
from math import ceil
import time
import os
import codecs
import os
import fnmatch
import argparse
import json


parser = argparse.ArgumentParser(description="Aker session reply")
parser.add_argument("-u", "--uuid", action="store", dest='uuid',help="Recorded Session UUID",required=True)
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("-r","--replay", action='store_true', dest="replay",help="Replay Session")
group.add_argument("-c","--commands", action='store_true',dest="cmds",help="Print Commands Entered By User During Session")


def main(argv):
	from aker import session_log_dir
	args = parser.parse_args()
	session_uuid = args.uuid
	log_file = "*" + session_uuid + "*" + ".log"
	log_timer = "*" + session_uuid + "*" + ".timer"
	cmds_file = "*" + session_uuid + "*" + ".cmds"
	logfile_path = locate(log_file, session_log_dir)
	timefile_path = locate(log_timer, session_log_dir)
	if args.replay:
		replay(logfile_path,timefile_path)
	elif args.cmds:
		cmds_filepath = locate(cmds_file, session_log_dir)
		show_cmds(cmds_filepath)

def show_cmds(cmds_file):
	data = []
	with open(cmds_file) as json_file:
		for line in json_file:
			data.append(json.loads(line))
		for k in data:
			try :
				print (k['timing'] + ':' + k['cmd'])
			except Exception:
				pass


def replay(log_file, time_file):
	with open(log_file) as logf:
		with open(time_file) as timef:
			timing = get_timing(timef)
			with closing(logf):
				logf.readline()  # ignore first line, (Session Start)
				for t in timing:
					data = logf.read(t[1])
					#print("data is %s , t is %s" % (data,t[1]))
					text = codecs.decode(data,'UTF-8',"replace")
					time.sleep(t[0])
					sys.stdout.write(text)
					sys.stdout.flush()
					text= ""
					

def locate(pattern, root=os.curdir):
	match = "" 
	for path, dirs, files in os.walk(os.path.abspath(root)):
		for filename in fnmatch.filter(files, pattern):
			matches= os.path.join(path, filename)
	return matches

def get_timing(timef):
	timing = None
	with closing(timef):
		timing = [l.strip().split(' ') for l in timef]
		timing = [(float(r[0]), int(r[1])) for r in timing]
	return timing




if __name__ == "__main__":
	main(sys.argv)
