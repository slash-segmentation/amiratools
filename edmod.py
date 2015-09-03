#! /usr/bin/env python

import os
import sys
import re
import array
import fileinput
import array
import shutil
import math
from random import randrange
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
        if re.match(regexp, line):
            return line
            break
        else:
            continue
        break

# Parse through the object list given by --objects. Remove any entries whose
# values are greater than the actual number of objects in the model file (if, for
# example, these were added to the list accidentally). Append individual object
# numbers to an array
def parseObjectList(objstr, objarray, objmax):
    objsplit = objstr.split(",")
    for i in range(0, len(objsplit)):
        if "-" not in objsplit[i]:
            val = int(objsplit[i])
            if val < objmax:
                objarray.append(val)
        else:
            objrange1 = int(objsplit[i].split("-")[0])
            objrange2 = int(objsplit[i].split("-")[1])
            if objrange2 > objrange1:
                for j in range(objrange1, objrange2 + 1 ):
                    if j < objmax:
                        objarray.append(j)
            else:
                usage("Improper object string %s." % objstr)
    return objarray

# Parse the color string input by either --colorin or --colorout. These should be
# in one of two formats (1) "R,G,B" where each are values from 0-1, or (2) "rand", where
# rand specifies the color should be random. A value of "rand" is only valid for the
# --colorout argument.
def parseColorString(str):
    splitCommas = str.split(',')
    if len(splitCommas) == 1 and (splitCommas[0] == "rand" or splitCommas[0] == "random"):
        return splitCommas[0], 1
    elif len(splitCommas) == 3:
        rgb = [i for i in splitCommas]
        rgbstr = "color %s %s %s" % (rgb[0], rgb[1], rgb[2])
        return rgbstr, 3
    else:
        usage("Color strings must be specified as R,G,B.")

# Determines the object type of a given ASCII model file. Open objects have a line that
# begins with "open" following the "color" line. Scattered objects have a line that begins
# with "scattered" following the "open" line. Closed objects have neither. objtype = 1 for
# closed, objtype = 2 for open, and objtype = 3 for scattered.
def getObjectType(handle):
    for line in handle:
        if re.match("^color", line):
            line2 = next(handle)
            line3 = next(handle)
            break
        else:
            continue
        break
    if re.match("^open", line2):
        objtype = 2
        if re.match("^scattered", line3):
            objtype = 3
    else:
        objtype = 1
    return objtype

# Determines if an object needs to be removed based on the value given to --rmcont. First
# reads the number of objects in the file, then makes a decision based on this value. If
# necessary, the value is removed from the array and returned.
def rmObjCheck(rmarray, handle, opts, i):
    line = matchLine("^object", handle)
    ncont = line.split()[2]
    if opts.rmempty and int(ncont) == 0:
        rmarray.append(i+1)
    if opts.rmcont and int(ncont) <= int(opts.rmcont):
        rmarray.append(i+1)
    return rmarray

# Removes contours that have less than the number of points given by --rmbypoint. Read 
# through the file line by line. When a line beginning with "contour" is found, increment
# the contsum counter. IF the contour has less than the number of points, increment the
# C counter, DO NOT print the line, and flip contswitch. If it has at least the correct 
# number of points, do not increment the C counter and DO print the line. For lines that
# do not begin with "contour", print the line if contswitch is off. Otherwise do not print
# the line. After the entire file has been parsed, update the "object" line with the total
# number of new contours.
def rmSmallContours(file_in, opts, handle):
    C = 0
    contsum = 0
    contswitch = 0
    for line in fileinput.input(file_in + ".txt", inplace = True):
        if not re.match("^contour", line):
            if not contswitch:
                sys.stdout.write(line)
            else:
                continue
        else:
            contsum = contsum + 1
            if int(line.split()[3]) <= int(opts.rmpoint):
                C = C + 1
                contswitch = 1
            else:
                contsplit = line.split()
                contnum = int(contsplit[1])
                line = "contour %d %s %s\n"  %(contnum - C, contsplit[2], contsplit[3])
                contswitch = 0
                sys.stdout.write(line)
    if C is not 0:
        handle.seek(0)
        objswitch = 0
        for line in fileinput.input(file_in + ".txt", inplace = True):
            if not objswitch and re.match("^object", line):
                objsplit = line.split()
                line = "object %s %s %s\n" %(objsplit[1], contsum - C, objsplit[3])
                objswitch = 1
            sys.stdout.write(line)
    return C

# Takes each line of an ASCII model file as input. Checks for all possible modifications,
# and makes the replacements when necessary.
def matchAndReplace(line, opts, colorstrout, colortypeout):
    if opts.colorout and re.match('^color', line):
        line = replaceColor(line, opts, colorstrout, colortypeout)
    elif opts.nameout and re.match('^name', line):
        line = re.sub('^name.+', "name " + opts.nameout, line)
    elif opts.linewidth and re.match('^width2D', line):
        line = re.sub('^width2D.+', "width2D " + opts.linewidth, line)
    elif opts.filled and re.match('^symflags', line):
        line = re.sub('^symflags.+', 'symflags 1', line)
    elif opts.notfilled and re.match('^symflags', line):
        line = re.sub('^symflags.+', 'symflags 0', line)
    elif opts.pointsize and re.match('^pointsize', line):
        line = re.sub('^pointsize.+', "pointsize " + opts.pointsize, line)
    return line

# Edits color lines to have the correct specified color and/or transparency values. When
# "rand" is supplied to --colorout, determine the random colored values based on the 
# range given by the line number.
def replaceColor(line, opts, colorstr, colortype):
    if colortype == 3 and not opts.transparency:
        line = re.sub('^color\s\S*\s\S*\s\S*\s', colorstr + " ", line)
    elif colortype == 1 and not opts.transparency:
        line = re.sub('^color\s\S*\s\S*\s\S*\s', "color %0.2f %0.2f %0.2f " %
                     (float(randrange(0,fileinput.lineno())) / fileinput.lineno(),
                     float(randrange(0,fileinput.lineno())) / fileinput.lineno(),
                     float(randrange(0,fileinput.lineno())) / fileinput.lineno()),
                     line)
    elif colortype == 3 and opts.transparency:
        line = re.sub('^color.+', colorstr + " " + opts.transparency, line)
    elif colortype == 1 and opts.transparency:
        line = re.sub('^color.+', "color %0.2f %0.2f %0.2f %s" %
                     (float(randrange(0,fileinput.lineno())) / fileinput.lineno(),
                     float(randrange(0,fileinput.lineno())) / fileinput.lineno(),
                     float(randrange(0,fileinput.lineno())) / fileinput.lineno(),
                     opts.transparency), line)
    return line

if __name__ == "__main__":
    p = OptionParser(usage = "%prog [options] file_in.mod file_out.mod")

    p.add_option("--colorin", dest = "colorin", metavar = "R,G,B",
                 help = "Color to change, given as R,G,B values ranging "
                        "from 0-1. Alternatively, this can be set to 'rand' "
                        "to generate random colors.")

    p.add_option("--namein", dest = "namein", metavar = "NAME",
                 help = "Object name to change.")

    p.add_option("--objects", dest = "objects", metavar = "INTEGER",
                 help = "List of objects to operate on. Objects are separated "
                        "by commas or by dashes for multiple selections.")

    p.add_option("--colorout", dest = "colorout", metavar = "R,G,B",
                 help = "Color to change, given as R,G,B values ranging "
                        "from 0-1. Alternatively, this can be set to 'rand' "
                        "to generate random colors.")

    p.add_option("--nameout", dest = "nameout", metavar = "NAME",
                 help = "Object name to change to.")

    p.add_option("--linewidth", dest = "linewidth", metavar = "INT",
                 help = "Line width to change to.")

    p.add_option("--filled", action = "store_true", dest = "filled",
                 help = "Use this argument to set objects to filled. This is "
                        "most useful for scattered point objects.")

    p.add_option("--notfilled", action = "store_true", dest = "notfilled",
                 help = "Use this argument to set objects to not filled.")

    p.add_option("--pointsize", dest = "pointsize", metavar = "INT",
                 help = "Point size to change to.")

    p.add_option("--transparency", dest = "transparency", metavar = "INT",
                 help = "Transparency of the object (in %, where 0 = opaque)")
 
    p.add_option("--vlow", dest = "vlow", metavar = "INT",
                 help = "Low threshold for object removal based on volume. All "
                        "objects with volumes less than this wil be removed.")

    p.add_option("--vhigh", dest = "vhigh", metavar = "INT",
                 help = "High threshold for object removal based on volume. All "
                        "objects with volumes greater than this will be removed.")

    p.add_option("--slow", dest = "slow", metavar = "INT",
                 help = "Low threshold for object removal based on surface area. "
                        "All objects with surface areas less than this wil be "
                        "removed.")

    p.add_option("--shigh", dest = "shigh", metavar = "INT",
                 help = "High threshold for object removal based on surface area. "
                        "All objects with volumes greater than this will be "
                        "removed.")

    p.add_option("--sphericitylow", dest = "spherlow", metavar = "FLOAT",
                 help = "Low threshold for object removal based on sphericity. All "
                        "objects with a sphericity coefficient less than this will "
                        "be removed. Sphericity ranges from 0 to 1, where 1 is a "
                        "perfect sphere.")

    p.add_option("--sphericityhigh", dest = "spherhigh", metavar = "FLOAT",
                 help = "High threshold for object removal based on sphericity. All "
                        "objects with a sphericity coefficient greater than this will "
                        "be removed.")

    p.add_option("--units", dest = "unit", metavar ="STR",
                 help = "Units for the low and high volume cutoffs. Available "
                        "options are: pix, nm, um. Default units are pix.")

    p.add_option("--rmbycont", dest = "rmcont", metavar = "INT",
                 help = "Removes all objects that have a number of contours "
                        "less than or equal to the specified value.")

    p.add_option("--rmbypoint", dest = "rmpoint", metavar = "INT",
                 help = "Removes all contours that have a number of points "
                        "less than or equal to the specified value.")

    p.add_option("--rmempty", action = "store_true", dest = "rmempty",
                 help = "Removes all objects that don't contain any contours")

    p.add_option("--rmall", action = "store_true", dest = "rmall",
                 help = "Removes objects across the whole model file, independent "
                        "of the options specified by --objects, --colorin, or "
                        "--namein. The default behavior is to remove only objects "
                        "that also satisfy the requirements of these arguments.")

    p.add_option("--ignorescattered", action = "store_true", dest = "ignorescat",
                 help = "Ignores scattered objects.")

    p.add_option("--ignoreopen", action = "store_true", dest = "ignoreopen",
                 help = "Ignores open objects.")

    p.add_option("--ignoreclosed", action = "store_true", dest = "ignoreclosed",
                 help = "Ignores closed object.")

    p.add_option("--all", action = "store_true", dest = "all",
                 help = "Use this argument to change the values for all "
                        "objects in the input model file.")

    (opts, args) = p.parse_args()

    # Parse the positional arguments
    if len(args) is not 2:
        usage("Improper number of arguments. See the usage below.")
    file_in = args[0]
    file_out = args[1]
    path_out = os.path.dirname(file_out)
    if not path_out:
        path_out = os.getcwd()
    path_tmp = os.path.join(path_out, "tmp")
    base_out = os.path.basename(file_out)

    # Check validity of positional arguments
    if not os.path.isfile(file_in):
        usage("The input file {0} does not exist".format(file_in))

    if not os.path.isdir(path_out):
        usage("The output path {0} does not exist.".format(path_out))

    # Check validity of optional arguments
    if opts.rmcont and opts.rmempty:
        usage("The option --rmcont is incompatible with the option --rmempty")
 
    if opts.rmall and not (opts.rmcont or opts.rmempty):
        usage("The option --rmall requires either --rmcont or --rmempty.")

    # Create temporary directory in the output path
    if os.path.isdir(path_tmp):
        usage("There is already a folder with the name tmp in the output "
              "path {0}".format(path_out))
    os.makedirs(path_tmp)

    # Set switches
    checkobjtype = 0
    objmodsswitch = 0
    runimodinfo = 0
    if (opts.colorout or opts.nameout or opts.linewidth or opts.filled or
       opts.notfilled or opts.pointsize or opts.transparency):
        objmodsswitch = 1
    if opts.vlow or opts.vhigh or opts.slow or opts.shigh or opts.spherlow or opts.spherhigh:
        runimodinfo = 1
        opts.ignorescat = True
    if opts.ignorescat or opts.ignoreopen or opts.ignoreclosed:
        checkobjtype = 1

    # Initialize arrays
    rmarray = array.array('l')
    objarray = array.array('l')
    filterarray = array.array('l')
    ignorearray = array.array('l')

    # Convert entire model to ASCII format 
    asciifile = os.path.join(path_tmp, file_in.split('.')[0] + ".txt")
    handle = mod2ascii(file_in, asciifile)

    # Parse the ASCII file to get the total number of objects and the units
    handle.seek(0)
    line = matchLine("^imod", handle)
    nobj = int(line.split()[1])
    line = matchLine("^units", handle)
    modunit = line.split()[1]
    if not opts.all:
        handle.close()
        os.remove(asciifile)

    # (OPTIONAL) Get volume/surface area of all objects
    if runimodinfo:
        if not opts.unit:
            opts.unit = modunit
        if ((opts.unit != "nm") and (opts.unit != "um") and
           (opts.unit != "pix")):
            usage("Improper unit string for --units.")
        if modunit is "pix" and (opts.unit is "nm" or opts.unit is "um"):
            usage("Model header units must be set to {0}".format(opts.unit))
        infofile = os.path.join(path_tmp, 'imodinfo.txt')
        infohandle = open(infofile, "w+")
        cmd = "imodinfo -c {0}".format(file_in)
        call(cmd.split(), stdout = infohandle)
        infohandle.seek(0)
        line = matchLine("#-", infohandle)
        C = 0
        if modunit == "nm" and opts.unit == "um":
            scale = 0.001
        elif modunit == "um" and opts.unit == "nm":
            scale = 1000
        else:
            scale = 1
        for line in infohandle:
            split = line.split()
            if len(split) == 8:
                C = C + 1
                vol = float(split[3]) * (scale**3)
                sa = float(split[4]) * (scale**2)
                if opts.spherlow or opts.spherhigh:
                    if sa == 0:
                        spher = 0
                    else:
                        spher = (math.pi**(1.0/3) * (6*vol)**(2.0/3))/sa
                if ((opts.vlow and vol < float(opts.vlow)) or
                   (opts.vhigh and vol > float(opts.vhigh)) or
                   (opts.slow and sa < float(opts.slow)) or
                   (opts.shigh and sa > float(opts.shigh)) or
                   (opts.spherlow and spher < float(opts.spherlow)) or
                   (opts.spherhigh and spher > float(opts.spherhigh))):
                    filterarray.append(C)
        infohandle.close()
        os.remove(infofile)

    # (OPTIONAL) If the --objects option is seleted, initiate a new array that 
    # contains the desired objects. If it is not selected, set this array to 
    # contain a list of all objects in the model file.
    if opts.objects:
        objarray = parseObjectList(opts.objects, objarray, nobj)
    else:
        for i in range(0, nobj):
            objarray.append(i+1)

    # (OPTIONAL) Parse color strings
    if opts.colorin:
        colorstrin, colortypein = parseColorString(opts.colorin)
        if colortypein == 1:
            usage("Input to --colorin must be specified as R,G,B.")
    if opts.colorout:
        colorstrout, colortypeout = parseColorString(opts.colorout)

    # (OPTIONAL) If the --all option is selected, perform the desired changes by 
    # parsing through the ASCII model file once in its entirety. This is faster.
    if opts.all:
        handle.seek(0)
        for line in fileinput.input(asciifile, inplace = True):
            if opts.colorout:
                line = matchAndReplace(line, opts, colorstrout, colortypeout)
            else:
                line = matchAndReplace(line, opts, 0, 0)
            sys.stdout.write(line)
        handle.close()
        os.rename(asciifile, os.path.join(path_out, file_out))
        os.rmdir(path_tmp) 
        sys.exit(0)

    ##########
    ## MAIN LOOP 
    ##########

    for i in range(0, nobj):
        # Extract the object to a new model file, then convert it to ASCII
        objfile = os.path.join(path_tmp, "obj_" + str(i+1).zfill(8))
        cmd = "imodextract {0} {1} {2}".format(i+1, file_in, objfile + ".mod")
        call(cmd.split())
        handle = mod2ascii(objfile + ".mod", objfile + ".txt")
        os.remove(objfile + ".mod")
        handle.seek(0)

        # (OPTIONAL) Determine the object type. 
        if checkobjtype:
            objtype = getObjectType(handle)
            if ((opts.ignoreclosed and objtype == 1) or (opts.ignoreopen and objtype == 2) or
               (opts.ignorescat and objtype == 3)):
                ignorearray.append(i+1)
            handle.seek(0)
        if i+1 in filterarray and not i+1 in ignorearray:
            rmarray.append(i+1)
            os.remove(objfile + ".txt")
            continue      
 
        # (OPTIONAL) If --rmall is given, look for objects to remove BEFORE
        # updating objarray based on --colorin or --namein. 
        if opts.rmall and (opts.rmempty or opts.rmcont) and i+1 in objarray and not i+1 in ignorearray:
            rmarray = rmObjCheck(rmarray, handle, opts, i)

        # (OPTIONAL) Check the object to see if it satisfies the arguments given by --colorin
        # and/or --namein. If it does, keep it in objarray. If it doesn't, remove it from
        # objarray.
        if (opts.colorin or opts.namein) and i+1 in objarray and not i+1 in ignorearray:
            colorswitch = 0
            nameswitch = 0
            for line in handle:
                if opts.colorin and re.match(colorstrin, line):
                    colorswitch = 1
                elif opts.namein and re.match("^name " + opts.namein, line):
                    nameswitch = 1
                elif re.match("^contour", line):
                    break
            if (opts.colorin and not colorswitch) or (opts.namein and not nameswitch):
                objarray.remove(i + 1)

        # If the --rmall argument was not given, look for ojbects to remove AFTER updating
        # the objarray based on --colorin or --namein
        if not opts.rmall and (opts.rmempty or opts.rmcont) and i+1 in objarray and not i+1 in ignorearray:
            handle.seek(0)
            rmarray = rmObjCheck(rmarray, handle, opts, i)

        # (OPTIONAL) Parse through individual contours, and remove contours that have a number
        # of points less than that specified by --rmbypoint.
        if opts.rmpoint and i+1 in objarray and not i+1 in ignorearray:
            handle.seek(0)
            C = rmSmallContours(objfile, opts, handle)
    
    handle.close()
 
    # Loop over each entry remaining in objarray. For each entry, load the corresponding
    # ASCII model file, and modify it as desired.
    if objmodsswitch:
        for i in range(0, len(objarray)):
            if i+1 in rmarray or i+1 in ignorearray:
                continue
            objfile = os.path.join(path_tmp, "obj_" + str(objarray[i]).zfill(8) + ".txt")
            for line in fileinput.input(objfile, inplace = True):
                if opts.colorout:
                    line = matchAndReplace(line, opts, colorstrout, colortypeout)
                else:
                    line = matchAndReplace(line, opts, 0, 0)
                sys.stdout.write(line)

    # Combine all files
    objstr = ""
    C=0
    for i in range(0, nobj):
        if not i + 1 in rmarray:
            objfile = os.path.join(path_tmp, "obj_" + str(i + 1).zfill(8))
            os.rename(objfile + ".txt", objfile + ".mod")
            objstr = objstr + objfile + ".mod" + " "
            C = C +1
    if C == 1:
        cmd = "mv %s%s" % (objstr, file_out)
    else:
        cmd = "imodjoin %s%s" %(objstr, file_out)
    call(cmd.split())
    shutil.rmtree(path_tmp)
    if os.path.isfile(file_out + "~"):
        os.remove(file_out + "~")
