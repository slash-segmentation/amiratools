#! /usr/bin/env python

"""
Command line program to provide quantitative metrics of all organelles in an
input IMOD model file using Amira. All objects in the input model file are
first converted to VRML and named according to their Name field in IMOD.
"""

import os
import os.path
import sys
import re
import fileinput
from sys import argv
from subprocess import call, check_output, Popen, PIPE
from optparse import OptionParser

# Print erorr messages and exit
def usage(errstr):
    print ""
    print "ERROR: %s" % errstr
    print ""
    p.print_help()
    print ""
    exit(1)

# Convert IMOD model file to ASCII using imodinfo
def mod2ascii(mod_in, ascii_out):
    handle = open(ascii_out, "w+")
    cmd = "imodinfo -a {0}".format(mod_in)
    call(cmd.split(), stdout = handle)
    return handle

# Parse through a text file until the regexp is matched. Once a match occurs,
# return the entire line and break the loop.
def matchLine(regexp, handle):
    for line in handle:
        if re.match(regexp, line.lstrip()):
            return line
            break
        else:
            continue
        break

# Get header info from an input MRC stack
def getMrcStackInfo(file_mrc, string):
    cmd = "header -{0} {1}".format(string, file_mrc)
    headerout = Popen(cmd.split(), stdout = PIPE).communicate()[0]
    header = headerout.split()
    return header

def maskSubvolume(file_in, file_out, mrc_in):
    cmd = "imodmop -mask 1 -border 0 {0} {1} {2}".format(file_in + ".mod",
           mrc_in, file_out + ".mrc")
    call(cmd.split())

def imod2amira(file_mod, file_wrl, scale, origin):
    cmd = "imod2vrml2 {0} {1}".format(file_mod, file_wrl)
    call(cmd.split())
    handle = open(file_wrl, "r+")
    coordswitch = 0
    for line in fileinput.input(file_wrl, inplace = True):
        if re.match("^point", line.lstrip()):
            coordswitch = 1
            sys.stdout.write(line)
            continue
        if re.match("\]", line.lstrip()):
            coordswitch = 0
            sys.stdout.write(line)
            continue
        if coordswitch:
            lineafter = line.lstrip()
            lenbefore = len(line)
            lenafter = len(lineafter)
            nspaces = lenbefore - lenafter
            blankspace = " " * nspaces
            coordx = float(lineafter.split()[0]) * float(scale[0]) + float(origin[0])
            coordy = float(lineafter.split()[1]) * float(scale[1]) + float(origin[1])
            coordz = lineafter.split()[2]
            coordz = float(coordz.split(",")[0]) * float(scale[2]) + float(origin[2])
            line = "%s%0.1f %0.1f %0.1f,\n" % (blankspace, coordx, coordy, coordz)
            sys.stdout.write(line)
        else:
            sys.stdout.write(line)
    handle.close()

def get_imodinfo(file_mod, vsa):
    vsa_ascii_i = open(file_mod + ".txt", "w+")
    cmd = "imodinfo -o 1 -F %s" %(file_mod + ".mod") 
    subprocess.call(cmd.split(), stdout = vsa_ascii_i)
    line_cent = parse_global(vsa_ascii_i, 'Center').split("(")[1]
    cent = line_cent.split(",")
    xcent = float(cent[0])
    ycent = float(cent[1])
    zcent = float(cent[2].split(")")[0])
    xcent = (xcent * lat_pix_size) / 1000
    ycent = (ycent * lat_pix_size) / 1000
    zcent = (zcent * axl_pix_size) / (zscale * 1000)
    if vsa: 
        line_vol = parse_global(vsa_ascii_i, 'Volume Inside Mesh')
        line_sa = parse_global(vsa_ascii_i, 'Mesh Surface Area')
        vol = float(line_vol.split("=")[1].lstrip().split()[0])
        sa = float(line_sa.split("=")[1].lstrip().split()[0])
        vol = vol / (1000**3)
        sa = sa / (1000**2)
        svr = sa / vol
    else:
        vol = "NA"
	sa = "NA"
	svr = "NA"
    os.remove(file_mod + ".txt")
    return xcent, ycent, zcent, vol, sa, svr

if __name__ == "__main__":
    p = OptionParser(usage = "%prog [options] file_in.mrc file_in.mod")
   
    p.add_option("--scale", dest = "scalein", metavar = "PATH",
                 help = "Pixel scales in X,Y,Z.")
 
    p.add_option("--output", dest = "path_out", metavar = "PATH",
                 help = "Output path.")

    (opts, args) = p.parse_args()

    # Check the validity of the input arguments
    if len(args) is not 2:
        usage("Improper number of arguments. See the usage below.")
    mrc_in = args[0]
    mod_in = args[1]

    path_out = os.getcwd()
    if opts.path_out:
        path_out = opts.path_out

    if not os.path.isfile(mod_in):
        usage("The model file {0} does not exist".format(mod_in))
    if not os.path.isfile(mrc_in):
        usage("The MRC file {0} does not exist".format(mrc_in))
    if not os.path.isdir(path_out):
        usage("The output path {0} does not exist".format(path_out)) 

    # Get scale info from mrc stack if not specified by user
    if opts.scalein:
        scale = opts.scalein.split(",")
    else:
        scale = getMrcStackInfo(mrc_in, "pixel")
    print scale

    # Get origin info from mrc stack
    origin = getMrcStackInfo(mrc_in, "origin")

    # Create temporary directory in the output path
    mod_base = os.path.basename(os.path.splitext(mod_in)[0])
    path_tmp = os.path.join(path_out, mod_base)
    os.makedirs(path_tmp)
    print path_tmp

    # Parse model file for global model values
    asciifile = os.path.join(path_tmp, mod_base + ".txt")
    fid = mod2ascii(mod_in, asciifile)
    fid.seek(0)
    line = matchLine("^imod", fid)
    nobj = int(line.split()[1])
    line = matchLine("^scale", fid)
    zscale = float(line.split()[3])
    line = matchLine("^pixsize", fid)
    lat_pix_size = float(line.split()[1])
    line = matchLine("^units", fid)
    units = line.split()[1]
    if not units == "nm":
        usage("The units in the model's header must be given in nm/pixel.")
    axl_pix_size = int(round(zscale * lat_pix_size))
    fid.close()
    os.remove(os.path.join(asciifile))

    # Parse each object in the model file
    for i in range(0, nobj):
	file_i = os.path.join(path_tmp, str(i+1).zfill(4))
        cmd = "imodextract {0} {1} {2}".format(i+1, mod_in, file_i + ".mod")
        call(cmd.split())
        handle = mod2ascii(file_i + ".mod", file_i + ".txt")
        handle.seek(0)
        line = matchLine("^name", handle)
        name = line[5:].rstrip().lower()
        handle.close()
        os.remove(file_i + ".txt")
	if (name == "mitochondrion") or (name == "mitochondria") or (name == "mito"):
            feature = "mitochondrion"
            fname = os.path.join(path_tmp, feature + "_" + str(i+1).zfill(4))
            imod2amira(file_i + ".mod", fname + ".wrl", scale, origin)
            os.remove(file_i + ".mod")
            #xcent, ycent, zcent, vol, sa, svr = get_imodinfo(file_i, 1)
	    #print "%d,%s,%f,%f,%f,%f,%f,%f" %(i+1, feature, xcent, ycent, zcent, vol, sa, svr )
	elif (name == "nucleus") or (name == "nuclei"):
	    feature = "nucleus"
            fname = os.path.join(path_tmp, feature + "_" + str(i+1).zfill(4))
            imod2amira(file_i + ".mod", fname + ".wrl", scale, origin)
            os.remove(file_i + ".mod")
            #xcent, ycent, zcent, vol, sa, svr = get_imodinfo(file_i, 1)
            #print "%d,%s,%f,%f,%f,%f,%f,%f" %(i+1, feature, xcent, ycent, zcent, vol, sa, svr )
	elif (name == "nucleolus") or (name == "nucleoli"):
	    feature = "nucleolus"
            fname = os.path.join(path_tmp, feature + "_" + str(i+1).zfill(4))
            imod2amira(file_i + ".mod", fname + ".wrl", scale, origin)
            os.remove(file_i + ".mod")
            #xcent, ycent, zcent, vol, sa, svr = get_imodinfo(file_i, 1)
	    #print "%d,%s,%f,%f,%f,%f,%f,%f" %(i+1, feature, xcent, ycent, zcent, vol, sa, svr )
	elif (name == "lysosome") or (name == "lysosomes"):
	    feature = "lysosome"
            fname = os.path.join(path_tmp, feature + "_" + str(i+1).zfill(4))
            imod2amira(file_i + ".mod", fname + ".wrl", scale, origin)
            os.remove(file_i + ".mod")
            #xcent, ycent, zcent, vol, sa, svr = get_imodinfo(file_i, 1)
	    #print "%d,%s,%f,%f,%f,%f,%f,%f" %(i+1, feature, xcent, ycent, zcent, vol, sa, svr )
	elif (name == "centriole"):
	    feature = "centriole"
	    #xcent, ycent, zcent, vol, sa, svr = get_imodinfo(file_i, 0)
	    #print "%d,%s,%f,%f,%f,%s,%s,%s" %(i+1, feature, xcent, ycent, zcent, vol, sa, svr)
	elif (name == "basal body") or (name == "basalbody"):
	    feature = "basalbody"
            #xcent, ycent, zcent, vol, sa, svr = get_imodinfo(file_i, 0)
            #print "%d,%s,%f,%f,%f,%s,%s,%s" %(i+1, feature, xcent, ycent, zcent, vol, sa, svr)
	elif ((name == "stigmoid body") or (name == "stigmoidbody") or 
               (name == "stb")):
	    feature = "stigmoidbody"
            fname = os.path.join(path_tmp, feature + "_" + str(i+1).zfill(4))
            imod2amira(file_i + ".mod", fname + ".wrl", scale, origin)
            os.remove(file_i + ".mod")
            #xcent, ycent, zcent, vol, sa, svr = get_imodinfo(file_i, 1)
	    #print "%d,%s,%f,%f,%f,%f,%f,%f" %(i+1, feature, xcent, ycent, zcent, vol, sa, svr )
	elif ((name == "primary cilium") or (name == "primary cilia") or 
               (name == "cilia") or (name == "cilium")):
	    feature = "primarycilium"
            fname = os.path.join(path_tmp, feature + "_" + str(i+1).zfill(4))
            imod2amira(file_i + ".mod", fname + ".wrl", scale, origin)
            os.remove(file_i + ".mod")
	elif ((name == "plasma membrane") or (name == "plasmamembrane") or
               (name == "membrane") or (name == "neuron")):
	    feature = "plasmamembrane"
            fname = os.path.join(path_tmp, feature + "_" + str(i+1).zfill(4))
            imod2amira(file_i + ".mod", fname + ".wrl", scale, origin)
            os.remove(file_i + ".mod")
	    #print "%d,%s" %(i+1, feature)
        else:
            feature = "unknownfeature"
        print "{0} written.\n".format(fname + ".wrl")

	#os.remove(file_i + ".mod")

    # Run programs
    #cmd = "/usr/local/apps/Amira-5.6.0/bin/start -no_gui /home/aperez/usr/local/amira/mito_skeleton.hx"
    #subprocess.call(cmd.split())
