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
import sys

import yaml

parser = argparse.ArgumentParser(description='This script simplifies backups of directories using rsync. Thats it.')
parser.add_argument('host', nargs='*', help='list of hosts to backup [default: all]')
parser.add_argument('-c', default='/etc/backup.yml', help='yaml file with configuration [default: /etc/backup.yml]')
parser.add_argument('-l', default=None, help='limit backup to yaml file with configuration')
parser.add_argument('--debug', action='store_true', help='verbose mode')
parser.add_argument('--dry', action='store_true', help='dry run')

args = parser.parse_args()

try:
    config = yaml.load(open(args.c).read())
except IOError:
    sys.exit('unable to open config file ' + args.c)

for backup in config['backups']:

    # prepare hosts
    if 'hosts' in backup and 'host' in backup:
        raise Exception('hosts and host are mutually exclusive')
    elif 'hosts' in backup:
        hosts = backup['hosts']
    elif 'host' in backup:
        hosts = [backup['host']]
    else:
        hosts = ['localhost']

    # filter hosts
    if args.host:
        hosts = [host for host in hosts if host in args.host]

    # only continue if there are any hosts
    if hosts:

        # prepare log file
        if 'log' in backup:
            logfile = backup['log']
        elif 'log' in config:
            logfile = config['log']
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
                if 'exclude' in config:
                    exclude += config['exclude']

                # prepare exclude_from
                exclude_from = []
                if 'exclude_from' in directory:
                    exclude_from += backup['exclude_from']
                if 'exclude_from' in backup:
                    exclude_from += backup['exclude_from']
                if 'exclude_from' in config:
                    exclude_from += config['exclude_from']

                # prepare rsync log file
                if 'rsync_log' in backup:
                    rsync_logfile = backup['rsync_log']
                elif 'rsync_log' in config:
                    rsync_logfile = config['rsync_log']
                else:
                    rsync_logfile = '/var/log/backup/%s.log' % host

                # prepare commands
                mkdir_args = ['mkdir', '-p', destination]
                rsync_args = ['rsync', '-a', '--numeric-ids', '--delete', '--log-file="{}"'.format(rsync_logfile), '--log-file-format=""']

                if args.debug:
                    rsync_args.append('-v')

                for e in exclude:
                    rsync_args.append('--exclude={}'.format(e))

                for e in exclude_from:
                    rsync_args.append('--exclude-from={}'.format(e))

                rsync_args.append(source, destination)

                if args.debug:
                    print(' '.join(mkdir_args))
                    print(' '.join(rsync_args))

                if not args.dry:
                    logging.info('backup started: %s -> %s' % (source, destination))
                    try:
                        subprocess.check_call(mkdir_args)
                        subprocess.check_call(rsync_args)
                        logging.info('backup finished: %s -> %s' % (source, destination))
                    except subprocess.CalledProcessError as e:
                        logging.info('backup error (%i): %s -> %s' % (e.returncode, source, destination))
