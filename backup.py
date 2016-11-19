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
import yaml
import subprocess

parser = argparse.ArgumentParser(description='This script simplifies backups of directories using rsync. Thats it.')
parser.add_argument('options', help='yaml file with options')
parser.add_argument('--debug', action='store_true', help='verbose mode')
parser.add_argument('--dry', action='store_true', help='dry run')
parser.add_argument('--arcfour', action='store_true', help='use --arcfour for ssh')

args = parser.parse_args()

backups = yaml.load(open(args.options).read())

for backup in backups:
    for directory in backup['directories']:

        mkdir_command = 'mkdir -p %s%s' % (backup['destination'], directory['path'])

        rsync_command = 'rsync -a --delete'

        if args.arcfour:
            rsync_command += ' -e \'ssh -c arcfour\''

        if args.arcfour:
            rsync_command += ' -e \'ssh -c arcfour\''

        if args.debug:
            rsync_command += ' -v'
        else:
            rsync_command += ' --log-file=%(log)s --log-file-format=""' % backup

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

        rsync_command += ' '
        if 'host' in backup:
            if 'user' in backup:
                rsync_command += ' %(user)s@%(host)s:' % backup
            else:
                rsync_command += ' %(host)s:' % backup

        rsync_command += ' %(destination)s' % backup + directory['path']

        if args.dry:
            print mkdir_command
            print rsync_command
        else:
            if not args.debug:
                subprocess.call('echo "%s" >> %s' % (rsync_command, backup['log']), shell=True)

            subprocess.call(mkdir_command, shell=True)
            subprocess.call(rsync_command, shell=True)
