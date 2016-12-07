#!/usr/bin/env python
'''
This script simplifies backups of directories using rsync. Thats it.

Prereqesites: linux :)
              python 2.7 or 3.4
              rsync

Usage:        ./backup.py [OPTIONSFILE]

(c) Jochen S. Klar, August 2016
'''

import argparse
import logging
import os
import subprocess
import yaml

parser = argparse.ArgumentParser(description='This script simplifies backups of directories using rsync. Thats it.')
parser.add_argument('options', help='yaml file with options')
parser.add_argument('--debug', action='store_true', help='verbose mode')
parser.add_argument('--dry', action='store_true', help='dry run')

args = parser.parse_args()

options = yaml.load(open(args.options).read())

for backup in options['backups']:

    # prepare log file
    if 'log' in backup:
        logfile = backup['log']
    elif 'log' in options:
        logfile = options['log']
    else:
        logfile = '/var/log/backup/backup.log'

    # prepare logger
    handler = logging.FileHandler(logfile, 'a')
    formatter = logging.Formatter('%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    for old_handler in logger.handlers[:]:
        logger.removeHandler(old_handler)
    logger.addHandler(handler)

    # prepare hosts
    if 'hosts' in backup and 'host' in backup:
        raise Exception('hosts and host are mutually exclusive')
    elif 'hosts' in backup:
        hosts = backup['hosts']
    elif 'host' in backup:
        hosts = [backup['host']]
    else:
        hosts = ['localhost']

    for host in hosts:
        for directory in backup['directories']:

            if not os.path.isabs(directory['path']):
                raise Exception('path needs to be absolute')

            path = os.path.normpath(directory['path']) + '/'

            if host != 'localhost':
                if 'user' in backup:
                    source = '%s@%s:%s' % (backup['user'], host, path)
                else:
                    source = '%s:%s' % (host, path)

                destination = os.path.join(os.path.normpath(backup['destination']), host) + path
            else:
                source = path
                destination = os.path.normpath(backup['destination']) + path

            # prepare excludes
            exclude = []
            if 'exclude' in directory:
                exclude += directory['exclude']
            if 'exclude' in backup:
                exclude += backup['exclude']
            if 'exclude' in options:
                exclude += options['exclude']

            # prepare exclude_from
            exclude_from = []
            if 'exclude_from' in directory:
                exclude_from += backup['exclude_from']
            if 'exclude_from' in backup:
                exclude_from += backup['exclude_from']
            if 'exclude_from' in options:
                exclude_from += options['exclude_from']

            # prepare rsync log file
            if 'rsync_log' in backup:
                rsync_logfile = backup['rsync_log']
            elif 'rsync_log' in options:
                rsync_logfile = options['rsync_log']
            else:
                rsync_logfile = '/var/log/backup/%s.log' % host

            # prepare commands
            mkdir_command = 'mkdir -p ' + destination
            rsync_command = 'rsync -a --numeric-ids --delete --log-file="%s" --log-file-format=""' % rsync_logfile

            if args.debug:
                rsync_command += ' -v'

            for e in exclude:
                rsync_command += ' --exclude=' + e

            for e in exclude_from:
                rsync_command += ' --exclude-from=' + e

            rsync_command += ' %s %s' % (source, destination)

            if args.debug:
                print mkdir_command
                print rsync_command

            if not args.dry:
                logging.info('backup started: %s -> %s' % (source, destination))
                subprocess.call(mkdir_command, shell=True)
                subprocess.call(rsync_command, shell=True)
                logging.info('backup finished: %s -> %s' % (source, destination))
