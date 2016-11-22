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
parser.add_argument('--fast', action='store_true', help='use --arcfour for ssh and more')

args = parser.parse_args()

backups = yaml.load(open(args.options).read())

for backup in backups:

    if 'hosts' in backup and 'host' in backup:
        raise Exception('hosts and host are mutually exclusive')
    elif 'hosts' in backup:
        hosts = backup['hosts']
    elif 'host' in backup:
        hosts = [backup['host']]
    else:
        hosts = [None]

    for host in hosts:
        for directory in backup['directories']:

            if not os.path.isabs(directory['path']):
                raise Exception('path needs to be absolute')

            path = os.path.normpath(directory['path']) + '/'

            if host:
                if 'user' in backup:
                    source = '%s@%s:%s' % (backup['user'], host, path)
                else:
                    source = '%s:%s' % (host, path)

                destination = os.path.join(os.path.normpath(backup['destination']), host) + path
            else:
                source = path
                destination = os.path.normpath(backup['destination']) + path

            mkdir_command = 'mkdir -p ' + destination
            rsync_command = 'rsync -a --numeric-ids --delete --log-file=%(log)s --log-file-format=""' % backup

            if args.debug:
                rsync_command += ' -v'

            if args.fast:
                rsync_command += ' -e \'ssh -T -c arcfour\' -o Compression=no -x'

            if 'exclude' in backup:
                for e in backup['exclude']:
                    rsync_command += ' --exclude=' + e

            if 'exclude_from' in backup:
                for e in backup['exclude_from']:
                    rsync_command += ' --exclude-from=' + e

            if 'exclude' in directory:
                for e in directory['exclude']:
                    rsync_command += ' --exclude=' + e

            if 'exclude_from' in directory:
                for e in directory['exclude_from']:
                    rsync_command += ' --exclude-from=' + e

            rsync_command += ' %s %s' % (source, destination)

            logging.basicConfig(
                filename=backup['log'],
                level=logging.INFO,
                format='%(asctime)s %(levelname)s %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )

            if args.debug:
                print mkdir_command
                print rsync_command

            if not args.dry:
                logging.info('backup started: %s -> %s' % (source, destination))
                subprocess.call(mkdir_command, shell=True)
                subprocess.call(rsync_command, shell=True)
                logging.info('backup finished: %s -> %s' % (source, destination))
