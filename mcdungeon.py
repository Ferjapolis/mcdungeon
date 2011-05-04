#!/usr/bin/python

import sys
import os
import argparse
import logging
from pymclevel import mclevel, nbt

__version__ = '0.2.0'
__version_info__ = tuple([ int(num) for num in __version__.split('.')])
_vstring = '%%(prog)s %s' % (__version__)

parent_parser = argparse.ArgumentParser(add_help=False,
    description='Generate a tile-based dungeon in a Minecraft map.')
parent_parser.add_argument('-v', '--version',
                           action='version', version=_vstring,
                           help='Print version and exit')
parent_parser.add_argument('--config',
                    dest='config',
                    metavar='CFGFILE',
                    default='configs/default.cfg',
                    help='Alternate config file. Default: configs/default.cfg')
parent_parser.add_argument('--write',
                    action='store_true',
                    dest='write' ,
                    help='Write the dungeon to disk')
parent_parser.add_argument('--skip-relight',
                    action='store_true',
                    dest='skiprelight',
                    help='Skip relighting the level')
parent_parser.add_argument('-t','--term',
                    type=int,dest='term',
                    metavar='FLOOR',
                    help='Print a text version of a given floor to the \
                    terminal')
parent_parser.add_argument('--html',
                    dest='html',
                    metavar='BASENAME',
                    help='Output html versions of the dungeon. This \
                    produces one file per level of the form \
                    BASENAME-(level number).html')
parent_parser.add_argument('--force',
                    action='store_true',
                    dest='force',
                    help='Force overwriting of html output files')
parent_parser.add_argument('-s', '--seed',
                    dest='seed',
                    metavar='SEED',
                    help='Provide a seed for this dungeon. This can be \
                    anything')
parent_parser.add_argument('-o', '--offset',
                    dest='offset',
                    nargs=3,
                    type=int,
                    metavar=('X', 'Y', 'Z'),
                    help='Provide a location offset. (overrides .cfg file)')
parent_parser.add_argument('-n','--number',
                    type=int,dest='number',
                    metavar='NUM',
                    default=1,
                    help='Number of dungeons to generate. -1 will create as \
                    many as possible given X, Z, and LEVEL settings.')

i_parser = argparse.ArgumentParser(parents=[parent_parser], add_help=False)
i_parser.add_argument('-i', '--interactive',
                    action='store_true',
                    dest='interactive' ,
                    help='Start in interactive mode. Prompt for SAVEDIR, Z, X, \
                    CFGFILE, and LEVELS.')


noi_parser = argparse.ArgumentParser(parents=[i_parser])
noi_parser.add_argument('world',
                    metavar='SAVEDIR',
                    help='Target world (path to save directory)')
noi_parser.add_argument('z',
                    metavar='Z',
                    type=int,
                    help='Number of rooms West -> East. Use -1 for random.')
noi_parser.add_argument('x',
                    metavar='X',
                    type=int,
                    help='Number of rooms North -> South. Use -1 for random.')
noi_parser.add_argument('levels',
                    metavar='LEVELS',
                    type=int,
                    help='Number of levels. Use -1 for random.')

iargs = i_parser.parse_known_args()
if (iargs[0].interactive == False):
    args = noi_parser.parse_args()
else:
    args = iargs[0]

import cfg
import loottable
from dungeon import *
from utils import *

if (args.interactive == True):
    print 'Starting interactive mode!'

    configDir = 'configs'
    if (os.path.isdir(configDir) == False):
        sys.exit('\nI cannot find your configs directory! Aborting!')
    print '\nConfigurations in your configs directory:\n'
    for file in os.listdir(configDir):
        file_path = os.path.join(configDir, file)
        file = file.replace('.cfg', '')
        if (os.path.isfile(file_path) and
           file_path.endswith('.cfg')):
            print '   ',file
    print '\nEnter the name of the configuration you wish to use.'
    config = raw_input('(leave blank for default): ')
    if (config == ''):
        config = 'default'
    args.config = str(os.path.join(configDir, config))+'.cfg'
    cfg.Load(args.config)

    saveFileDir = mclevel.saveFileDir
    print '\nYour save directory is:\n', saveFileDir
    if (os.path.isdir(saveFileDir) == False):
        sys.exit('\nI cannot find your save directory! Aborting!')
    print '\nWorlds in your save directory:\n'
    for file in os.listdir(saveFileDir):
        file_path = os.path.join(saveFileDir, file)
        if os.path.isdir(file_path):
            print '   ',file
    world = raw_input('\nEnter the name of the world you wish to modify: ')
    args.world = os.path.join(saveFileDir, world)

    m = cfg.max_dist - cfg.min_dist
    print '\nEnter the size of the dungeon from East to West. (Z size)'
    print 'This should be between 2 and %d, but you can try larger sizes.'%(m)
    print 'Enter -1 to generate a random size.'
    args.z = int(raw_input('Z size: '))

    print '\nEnter the size of the dungeon from North to South. (X size)'
    print 'This should be between 2 and %d, but you can try larger sizes.'%(m)
    print 'Enter -1 to generate a random size.'
    args.x = int(raw_input('X size: '))

    print '\nEnter a number of levels for the dungeon.'
    print 'This should be greater than zero.'
    print 'Enter -1 to generate a random number of levels.'
    args.levels = int(raw_input('Levels: '))

    #html = raw_input('\nWould you like to create an HTML map? (y/n): ')
    #if (html.lower() == 'y'):
    #    args.html = world
    #    args.force = True
    args.write = True
else:
    cfg.Load(args.config)

# Load lewts
loottable.Load()

# Do some initial error checking
if (args.z < 2 and args.z >= 0):
    sys.exit('Too few rooms in Z direction. (%d) Try >= 2.'%(args.z))
if (args.x < 2 and args.z >= 0):
    sys.exit('Too few rooms in X direction. (%d) Try >= 2.'%(args.x))
if (args.levels == 0 or args.levels > 18):
    sys.exit('Invalid number of levels. (%d)'%(args.levels))

if (args.offset is not None):
    cfg.offset = '%d, %d, %d' % (args.offset[0],
                                 args.offset[1],
                                 args.offset[2])

# Some options don't work with multidungeons
if (args.number is not 1):
    if (args.offset is not None):
        print 'WARN: Offset option is ignored when generating multiple dungeons.'
        cfg.offset = None
    if  (args.html is not None):
        print 'WARN: HTML option is ignored when generating multiple dungeons.'
        args.html = None
    if  (args.seed is not None):
        print 'WARN: Seed option is ignored when generating multiple dungeons.'
        args.seed = None


# Attempt to open the world.
try:
    world = mclevel.fromFile(args.world)
except:
    print "Failed to open world:",args.world
    sys.exit(1)
print 'Loaded world: %s (%d chunks)' % (args.world, world.chunkCount)

#dumpEnts(world)
#sys.exit()

print "Startup compete. "

depths = {}
dungeons = []

while args.number is not 0:

    # Define our dungeon.
    x = args.x
    z = args.z
    levels = args.levels
    if (args.z < 0):
        z = randint(2, cfg.max_dist - cfg.min_dist)
    if (args.x < 0):
        x = randint(2, cfg.max_dist - cfg.min_dist)
    if (args.levels < 0):
        levels = randint(2, 8)

    dungeon = None
    located = False

    if (cfg.offset is not None and cfg.offset is not ''):
        dungeon = Dungeon(x, z, levels, depths)
        print 'Dungeon size: %d x %d x %d' % (z, x, levels)
        dungeon.position = str2Vec(cfg.offset)
        print "location set to",cfg.offset
        located = True

    else:
        print "Searching for a suitable location..."
        while (located is False):
            dungeon = Dungeon(x, z, levels, depths)
            print 'Dungeon size: %d x %d x %d' % (z, x, levels)
            located = dungeon.findlocation(world)
            if (located is False):
                print 'No locations found.'
                adjusted = False
                if (args.x < 0 and x > 2):
                    x -= 1
                    adjusted = True
                if (args.z < 0 and z > 2):
                    z -= 1
                    adjusted = True
                if (args.levels < 0 and levels > 1):
                    levels -= 1
                    adjusted = True
                if (adjusted is False):
                    print 'Unable to place any more dungeons.'
                    break
    if (located is True):
        if (args.seed is not None):
            seed(args.seed)
            print 'Seed:',args.seed

        print "Generating rooms..."
        dungeon.genrooms()

        print "Generating halls..."
        dungeon.genhalls()

        print "Generating floors..."
        dungeon.genfloors()

        print "Generating features..."
        dungeon.genfeatures()

        print "Extending the entrance to the surface..."
        dungeon.setentrance(world)

        print "Rendering rooms..."
        dungeon.renderrooms()

        print "Rendering halls..."
        dungeon.renderhalls()

        print "Rendering floors..."
        dungeon.renderfloors()

        print "Rendering features..."
        dungeon.renderfeatures()

        print "Placing doors..."
        dungeon.placedoors(cfg.doors)

        print "Placing portcullises..."
        dungeon.placeportcullises(cfg.portcullises)

        print "Placing torches..."
        dungeon.placetorches()

        print "Placing chests..."
        dungeon.placechests()

        print "Placing spawners..."
        dungeon.placespawners()

        # Write the changes to the world.
        if (args.write is True):
            print "Writing blocks..."
            dungeon.applychanges(world)

        # Output an html version.
        if (args.html is not None):
            dungeon.outputhtml(args.html, args.force)

        # Output a slice of the dungeon to the terminal if requested.
        if (args.term is not None):
            dungeon.outputterminal(args.term)

        start = dungeon.position
        end = Vec(start.x + dungeon.xsize * dungeon.room_size - 1,
          start.y - dungeon.levels * dungeon.room_height + 1,
          start.z - dungeon.zsize * dungeon.room_size + 1)
        dungeons.append('Dungeon %d (%d x %d x %d): %s to %s' %
                        (len(dungeons)+1,
                         z,
                         x,
                         levels,
                         start.__str__(),
                         end.__str__()))

    args.number -= 1
    if (located is False):
        args.number = 0

if (dungeons is 0):
    print 'Unable to place any dungeons. Check your settings.'
    sys.exit(1)

# Relight
if (args.write is True and args.skiprelight is False):
    print "Relighting chunks..."
    logging.getLogger().level = logging.INFO
    world.generateLights()

# Save the world.
if (args.write is True):
    print "Saving..."
    world.saveInPlace()
else:
    print "Map NOT saved! This was a dry run. Use --write to enable saving."

print 'Done!                   '

print 'Placed', len(dungeons), 'dungeons!'
for d in dungeons:
    print d

