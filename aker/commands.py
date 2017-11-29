# -*- coding: utf-8 -*-
#
#       Copyright 2017 Ahmed Nazmy
#

# Meta
__license__ = 'AGPLv3'
__author__ = 'Ahmed Nazmy <ahmed@nazmy.io>'

import codecs
import fnmatch
import json
import os
import sys
import time

from contextlib import closing


def akerctl_commands(args, config):
    session_uuid = args.uuid
    base_filename = '*' + session_uuid + '*'
    log_file = base_filename + '.log'
    log_timer = base_filename + '.timer'
    cmds_file = base_filename + '.cmds'

    logfile_path = locate(log_file, config.session_log_dir)
    timefile_path = locate(log_timer, config.session_log_dir)
    if args.replay:
        replay(logfile_path, timefile_path)
    elif args.commands:
        cmds_filepath = locate(cmds_file, config.session_log_dir)
        show_cmds(cmds_filepath)


def show_cmds(cmds_file):
    data = []
    with open(cmds_file) as json_file:
        for line in json_file:
            data.append(json.loads(line))
        for k in data:
            try:
                print(k['timing'] + ':' + k['cmd'])
            except Exception:
                pass


def replay(log_file, time_file):
    with open(log_file) as logf:
        with open(time_file) as timef:
            timing = get_timing(timef)
            with closing(logf):
                logf.readline()  # ignore first line, (Session Start)
                for times in timing:
                    data = logf.read(times[1])
                    # print('data is %s , t is %s' % (data,t[1]))
                    text = codecs.decode(data, 'UTF-8', 'replace')
                    time.sleep(times[0])
                    sys.stdout.write(text)
                    sys.stdout.flush()
                    text = ''


def locate(pattern, root=os.curdir):
    for path, _, files in os.walk(os.path.abspath(root)):
        for filename in fnmatch.filter(files, pattern):
            matches = os.path.join(path, filename)
    return matches


def get_timing(timef):
    timing = None
    with closing(timef):
        timing = [l.strip().split(' ') for l in timef]
        timing = [(float(r[0]), int(r[1])) for r in timing]
    return timing
