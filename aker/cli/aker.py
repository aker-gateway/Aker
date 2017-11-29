#!/usr/bin/env python

import logging

from argparse import ArgumentParser

from ..config import Config
from ..aker import Aker


def run():
    parser = ArgumentParser(description='Aker SSH gateway')
    parser.add_argument('--config', '-c', default='/etc/aker/aker.ini', help='Path to config file')
    parser.add_argument('--hosts-file', default='/etc/aker/hosts.json', help='Path to JSON file with allowed hosts')
    parser.add_argument('--idp', default='ipa', help='idp provider', choices=('ipa', 'json',))
    parser.add_argument('--log-file', default='/var/log/aker/aker.log', help='Path to log file')
    parser.add_argument('--log-level', default='INFO', help='Set log level', choices=('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL', 'FATAL'))
    parser.add_argument('--session-log-dir', default='/var/log/aker', help='Session log dir')
    args = parser.parse_args()

    config = Config(
        filename=args.config,
        hosts_file=args.hosts_file,
        idp=args.idp,
        log_file=args.log_file,
        log_level=args.log_level,
        session_log_dir=args.session_log_dir,
    )

    # Setup logging first thing
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    logging.basicConfig(
        format='%(asctime)s - %(levelname)s - %(message)s',
        filename=config.log_file,
        level=config.log_level)

    Aker(config).build_tui()


if __name__ == '__main__':
    run()
