#!/usr/bin/env python
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

from argparse import ArgumentParser
from contextlib import closing

from .config import Config


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


def main(args, config):
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


if __name__ == '__main__':
    PARSER = ArgumentParser(description='Aker session replay')
    PARSER.add_argument('--config', '-c', default='/etc/aker/aker.ini', help='Path to config file')
    PARSER.add_argument('--session-log-dir', default='/var/log/aker', help='Session log dir')
    PARSER.add_argument('--uuid', '-u', action='store', help='Recorded Session UUID', required=True)

    GROUP = PARSER.add_mutually_exclusive_group(required=True)
    GROUP.add_argument('--replay', '-r', action='store_true', help='Replay Session')
    GROUP.add_argument('--commands', '-c', action='store_true', help='Print Commands Entered By User During Session')

    ARGS = PARSER.parse_args()

    CONFIG = Config(
        filename=ARGS.config,
        session_log_dir=ARGS.session_log_dir,
    )

    main(ARGS, CONFIG)
