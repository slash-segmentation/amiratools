#! /usr/bin/env python

"""
Command line program to convert a meshed IMOD model file to a VRML file that
can be loaded into Amira. The output VRML file will be scaled properly to
correspond to a given MRC file, so that when both are loaded in Amira, the
mesh will appear in the correct location relative to the MRC file.
"""

import os
import sys
import re
import fileinput
import shutil
from optparse import OptionParser
from subprocess import Popen, call, PIPE
from sys import stderr, exit, argv

# Print error messages and exit
def usage(errstr):
    print ""
    print "ERROR: %s" % errstr
    print ""
    p.print_help()
    print ""
    exit(1)

# Parse through a text file until the regexp is matched. Once a match occurs,
# return the entire line and break the loop.
def matchLine(regexp, fid):
    for line in fid:
        if re.match(regexp, line.lstrip()):
            return line
            break
        else:
            continue
        break

# Convert IMOD model file to ASCII using imodinfo
def mod2ascii(mod_in, ascii_out):
    handle = open(ascii_out, "w+")
    cmd = "imodinfo -a {0}".format(mod_in)
    call(cmd.split(), stdout = handle)
    return handle

# Get header info from an input MRC stack
def getMrcStackInfo(file_mrc, string):
    cmd = "header -{0} {1}".format(string, file_mrc)
    headerout = Popen(cmd.split(), stdout = PIPE).communicate()[0]
    header = headerout.split()
    # If the numbers are in scientific notation, IMOD's header will sometimes 
    # output them without spaces. In this case, find where the '+'s occur, and
    # split in this way.
    if len(header) is not 3:
        for i in range(0, len(header)):
            headerstr = header[i]
            positionOfPlusSigns = findPositions(headerstr, '+')
            initialPos = 0
            if len(positionOfPlusSigns) is 0:
                header.append(headerstr)
            else:
                for j in range(0, len(positionOfPlusSigns)):
                    finalPos = positionOfPlusSigns[j] + 3
                    header.append(headerstr[initialPos:finalPos])
                    initialPos = finalPos
        header = header[len(header)-3:len(header)]
    return header

# Finds all positions of a character in a given string
def findPositions(str, char):
    return [i for i, ltr in enumerate(str) if ltr == char]

def get_blank_spaces(line):
    lineafter = line.lstrip()
    lenbefore = len(line)
    lenafter = len(lineafter)
    nspaces = lenbefore - lenafter
    blankspace = " " * nspaces
    return blankspace

if __name__ == "__main__":
    p = OptionParser(usage = "%prog [options] file.mrc file_in.mod file_out.wrl")

    p.add_option("--scale", dest = "scale", metavar = "X,Y,Z",
                 help = "Pixel scales in X,Y,Z.")
    (opts, args) = p.parse_args()

    # Parse the positional arguments
    if len(args) is not 3:
        usage("Improper number of arguments. See the usage below.")
    file_mrc = args[0]
    file_in = args[1]
    file_out = args[2]
    path_out = os.path.dirname(file_out)

    if not path_out:
        path_out = os.getcwd()

    base_out = os.path.basename(file_out)

    # Check validity of positional arguments
    if not os.path.isfile(file_mrc):
        usage("The input file {0} does not exit".format(file_mrc))

    if not os.path.isfile(file_in):
        usage("The input file {0} does not exist".format(file_in))

    if not os.path.isdir(path_out):
        usage("The output path {0} does not exist.".format(path_out))

    # Parse the scale option if provided. If not provided, extract scale info
    # from the model header. Scale values are typically in Angstroms
    if opts.scale:
        scale = opts.scale.split(",")
    else:
        scale = getMrcStackInfo(file_mrc, "pixel")

    # Get origin info from mrc stack
    origin = getMrcStackInfo(file_mrc, "origin")
    if len(origin) is not 3:
        print "Not 3"

    # Get the Z scale from the model file. Also check for object type.
    cmd = 'imodinfo -a {0}'.format(file_in)
    proc = Popen(cmd.split(), stdout = PIPE)
    typeOpen = False
    typeScat = False
    for line in proc.stdout:
        if re.match('^scale', line.lstrip()):
            modelzscale = float(line.split()[3])
        elif re.match('^open', line.lstrip()):
            typeOpen = True
        elif re.match('^scattered', line.lstrip()):
            typeScat = True
            break

    # Print header info
    print "Scale (x,y,z): {0}, {1}, {2}".format(scale[0], scale[1], scale[2])
    print "Origin (x,y,z): {0}, {1}, {2}".format(origin[0], origin[1], origin[2])

    # First, convert the IMOD model file to vrml using the IMOD program
    cmd = "imod2vrml2 {0} {1}".format(file_in, file_out)
    call(cmd.split())
    fid = open(file_out, "r+")

    if (typeOpen and not typeScat) or (not typeOpen and not typeScat):
        # Loop through every line of the output VRML file. When necessary, scale
        # the coordinates appropriately so that the VRML will load into the proper
        # position when loaded with the corresponding MRC file.
        print "Processing as closed type object."
        coordswitch = 0
        for line in fileinput.input(file_out, inplace = True):
            if re.match("^point", line.lstrip()):
                coordswitch = 1
                sys.stdout.write(line)
                continue
            if re.match("\]", line.lstrip()):
                coordswitch = 0
                sys.stdout.write(line)
                continue
            if coordswitch:
                blankspace = get_blank_spaces(line)
                line = line.lstrip()
                coordx = float(line.split()[0]) * float(scale[0]) + float(origin[0])
                coordy = float(line.split()[1]) * float(scale[1]) + float(origin[1])
                coordz = line.split()[2]
                coordz = float(coordz.split(",")[0]) * float(scale[2])/modelzscale + float(origin[2])
                line = "%s%0.1f %0.1f %0.1f,\n" % (blankspace, coordx, coordy, coordz)
                sys.stdout.write(line)
            else:
                sys.stdout.write(line)
    elif typeScat:
        print "Processing as scattered type object."
        for line in fileinput.input(file_out, inplace = True):
            if re.match("^translation", line.lstrip()): 
                # Scale the sphere center to match the input MRC file
                blankspace = get_blank_spaces(line)
                line = line.lstrip()
                coordx = float(line.split()[1]) * float(scale[0]) + float(origin[0])
                coordy = float(line.split()[2]) * float(scale[1]) + float(origin[1]) 
                coordz = float(line.split()[3]) * float(scale[2])/modelzscale + float(origin[2]) 
                line = '%stranslation %0.1f %0.2f %0.1f\n' % (blankspace, coordx, coordy, coordz)
                sys.stdout.write(line)
                continue
            elif re.match("^geometry", line.lstrip()):
                # Scale the sphere readius to match the input MRC file
                blankspace = get_blank_spaces(line)
                line = line.lstrip().split()
                line[6] = str(float(line[6]) * float(scale[0]))
                line = blankspace + ' '.join(line)
                sys.stdout.write(line)
                continue
            else:
                sys.stdout.write(line)
    fid.close()
    print 'Output written to {0}'.format(file_out)
