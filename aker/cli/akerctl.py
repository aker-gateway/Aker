#!/usr/bin/env python

from argparse import ArgumentParser

from ..commands import akerctl_commands
from ..config import Config


def run():
    parser = ArgumentParser(description='Aker session replay')
    parser.add_argument('--config', '-c', default='/etc/aker/aker.ini', help='Path to config file')
    parser.add_argument('--log-file', default='/var/log/aker/aker.log', help='Path to log file')
    parser.add_argument('--log-level', default='INFO', help='Set log level', choices=('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL', 'FATAL'))
    parser.add_argument('--session-log-dir', default='/var/log/aker', help='Session log dir')
    parser.add_argument('--uuid', action='store', help='Recorded Session UUID', required=True)

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--replay', action='store_true', help='Replay Session')
    group.add_argument('--commands', action='store_true', help='Print Commands Entered By User During Session')

    args = parser.parse_args()

    config = Config(
        filename=args.config,
        log_file=args.log_file,
        log_level=args.log_level,
        session_log_dir=args.session_log_dir,
    )

    akerctl_commands(args, config)


if __name__ == '__main__':
    run()
