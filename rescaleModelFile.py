#! /usr/bin/env python

"""
Command line program that rescales an IMOD model file to match the same MRC
file, but with different pixel spacing values. This may occur if the header
information was not entered properly after data collection, and then a model
file was generated on this data. The model file will not load properly on the 
same MRC file if its header information is altered to the proper pixel sizes.
Running this script using the correct MRC file and old model file will output
a new model file that can be loaded properly on the new MRC file, and then
imported into Amira for visualization and quantification using the correct
pixel sizes.

Maintains object names and colors.
"""

import os
import sys
import re
import shutil
from optparse import OptionParser
from subprocess import Popen, call, PIPE
from sys import stderr, exit, argv

# Print erorr messages and exit
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
    fid = open(ascii_out, "w+")
    cmd = "imodinfo -a {0}".format(mod_in)
    call(cmd.split(), stdout = fid)
    return fid

if __name__ == "__main__":
    p = OptionParser(usage = "%prog [options] file.mrc file_in.mod file_out.mod")

    (opts, args) = p.parse_args()

    if len(args) is not 3:
        usage("Improper number of arguments. See the usage below.")
 
    file_mrc = args[0]
    file_in = args[1]
    file_out = args[2]
    
    path_out = os.path.dirname(file_out)
    base_out = os.path.basename(file_out)
    if not path_out:
        path_out = os.getcwd()

    path_tmp = os.path.join(path_out, "tmp")

    # Check validity of positional arguments
    if not os.path.isfile(file_mrc):
        usage("The input file {0} does not exit".format(file_mrc))

    if not os.path.isfile(file_in):
        usage("The input file {0} does not exist".format(file_in))

    # Create temporary directory in the output path
    if os.path.isdir(path_tmp):
        usage("There is already a folder with the name tmp in the output "
              "path {0}".format(path_out))
    os.makedirs(path_tmp)
  
    # Get the number of objects in the whole model file
    print "Determining the number of objects in {0}".format(file_in)
    asciifile = os.path.join(path_tmp, "ascii.txt")
    fid = mod2ascii(file_in, asciifile)
    fid.seek(0)
    line = matchLine("^imod", fid)
    nobj = int(line.split()[1])
    fid.close()
    os.remove(asciifile)
    print "Objects found: {0}".format(nobj)
    
    for N in range(0, nobj):
        print "Processing object {0}.".format(N+1)
        base_tmp = "object_" + str(N+1).zfill(6)
        mod_tmp = os.path.join(path_tmp, base_tmp + ".mod")
        txt_tmp = os.path.join(path_tmp, base_tmp + ".txt")

        # Extract the object to a new model file
        cmd = "imodextract {0} {1} {2}".format(N+1, file_in, mod_tmp)
        call(cmd.split())

        # Get the object name and object color
        fid = mod2ascii(mod_tmp, asciifile)
        fid.seek(0)
        line = matchLine("^name", fid)
        name = line.split()[1:]
        name = " ".join(name)
        line = matchLine("^color", fid)
        color = line.split()[1:4]
        colorR = int(round(float(color[0]) * 255))
        colorG = int(round(float(color[1]) * 255))
        colorB = int(round(float(color[2]) * 255))
        fid.close()
        os.remove(asciifile)

        # Convert object to point notation, then back to a model scaled to
        # the desired MRC file
        cmd = "model2point -object {0} {1}".format(mod_tmp, txt_tmp)
        call(cmd.split())
        os.remove(mod_tmp)
        cmd = list()
        cmd.append("point2model")
        cmd.append("-image")
        cmd.append(file_mrc) 
        cmd.append("-name")
        cmd.append(name)
        cmd.append("-color")
        cmd.append("{0},{1},{2}".format(colorR, colorG, colorB))
        cmd.append(txt_tmp)
        cmd.append(mod_tmp)
        print " ".join(cmd)
        call(cmd)
        os.remove(txt_tmp)

        # Join the individual files into the final output model file
        if N == 0:
            os.rename(mod_tmp, file_out)
        else:
            cmd = "imodjoin {0} {1} {0}".format(file_out, mod_tmp)
            call(cmd.split())
            os.remove(mod_tmp)

    # Cleanup
    os.remove(file_out + "~")
    shutil.rmtree(path_tmp)

    # Print disclaimer about meshing
    print("SUCCESS! {0} created".format(file_out))
    print("WARNING: Need to regenerate meshes using imodmesh")
