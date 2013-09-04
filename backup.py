#!/usr/bin/env python
'''
This script simplifies backups of directories using rdiff-backup. It is also able
to trigger database dumps for mysql and postgres.

prereqesites: linux :)
              python 2.x
              rdiff-backup
              mysqldump (optional, for mysql)
              pg_dump (optional, for postgres)

(c) Jochen S. Klar, September 2013
'''
# the executable
rdiff     = 'rdiff-backup'
mysqldump = 'mysqldump'
pg_dump   = 'pg_dump'

# include some common python modules
import os,sys,datetime,json

# a function to call somthing using os.system
def cmd(call):
    print call
    #os.system(call)

# a function which returns the current time in a convenient format
def getTime():
    return datetime.datetime.now().strftime('%Y-%m-%dT%H-%M-%S')

# path of the running script
path = os.path.abspath(os.path.dirname(__file__))

# get the options file from the commandline or take the default
try:
    optionsFile = path + '/' + sys.argv[1]
except IndexError:
    optionsFile = path + '/' + 'options.json'

# read and parse options.json
try:
    optionsString = open(optionsFile).read()
except IOError:
    sys.exit('Error options file: ' + optionsFile + ' does not exist.')
try:
    options = json.loads(optionsString)
except ValueError as e:
    sys.exit('Error with json: ' + e.message + '.')

# sanity checks
if 'databases' not in options: options['databases'] = []
if 'directories' not in options: options['directories'] = []
if 'destination' not in options: sys.exit('Error: destination missing.')
if 'host' not in options['destination'] or options['destination']['host'] == '': 
    sys.exit('Error: destination host missing.')
if 'user' not in options['destination'] or options['destination']['user'] == '':
    sys.exit('Error: destination user missing.')
if 'path' not in options['destination'] or options['destination']['path'] == '':
    sys.exit('Error: destination path missing.')

# prepare destination string
destination = options['destination']['user'] + '@' + \
    options['destination']['host'] + '::' + \
    options['destination']['path'] + '/'

if 'mysql' in options['databases'] and options['databases']['mysql']: 
    # prepare mysql database directory
    cmd('mkdir -p ' + path +'/mysql')

    # add mysql dir to rdiff directories
    options['directories'].append({
            'name': 'mysql',
            'path': path +'/mysql'
        })

    # dump mysql databases
    for database in options['databases']['mysql']:
        dump = path + '/mysql/' + database['dbname'] + '.' + getTime() + '.gz'
        call = mysqldump + ' ' + database['dbname'] + ' --user=' + database['user'] + ' --password=' + database['password'] + ' | gzip -9 > ' + dump 
        cmd(call)

if 'postgres' in options['databases'] and options['databases']['postgres']: 
    # prepare postgres database directory
    cmd('mkdir -p ' + path + '/postgres')

    # add postgres dir to rdiff directories
    options['directories'].append({
            'name': 'postgres',
            'path': path +'/postgres'
        })

    # dump postgres databases
    for database in options['databases']['postgres']:
        dump = path + '/postgres/' + database['dbname'] + '.' + getTime() + '.gz'
        os.putenv('PGPASSWORD', database['password'])
        call = pg_dump + ' ' + database['dbname'] + ' --username=' + database['user'] + ' | gzip -9 > ' + dump 
        cmd(call)
        os.unsetenv('PGPASSWORD')

if options['directories']:
    # prepare log directory
    cmd('mkdir -p ' + path + '/logs')

    # add logs dir to rdiff directories
    options['directories'].append({
            'name': 'logs',
            'path': path +'/logs'
        })

    # rdiff directories to the destination host
    for directory in options['directories']:
        # specify logfile
        log = path + '/logs/' + directory['name'] + '.' + getTime() + '.log'

        # produce call
        call = rdiff + ' -v 5 '
        if 'exclude' in directory:
            for exclude in directory['exclude']:
                call += '--exclude="' + directory['path'] + '/' + exclude + '" '
        call += directory['path'] + ' ' + destination + '/' + directory['name'] + '/ &> ' + log
        cmd(call)
