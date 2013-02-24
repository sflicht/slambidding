#!/usr/bin/python

#######################################
#
# makesystem.py
#
# Interactive methods for making and viewing
# *.system XML files
#
####################################


# standard library imports
import glob
import string
from xml.etree import ElementTree

import conventionmaker

def view():
    """
    displays the name(s) of conventions provided by  existing system XML 
    files (*.system) in the ./systems/ directory
    """
    systemfiles = glob.glob("./systems/*.system")
    if len(systemfiles) == 0:
        print "No system files currently available.\n"
    else:
        print "Available systems:\n"
        for systemfile in systemfiles:
            try:
                system = ElementTree.parse(systemfile)
            except Exception, inst:
                print "\nError parsing file %s: %s" % (systemfile, 
                                                       inst)
            output = ""
            # output += systemfile + " provides "
            names = system.findall("name")
            if len(names) != 0:
                output += names[0].text 
                if len(names) > 1:
                    del names[0]
                    output += " (A.K.A: " 
                    output += string.join(map(lambda x: x.text, names), ', ')
                    output += ")"
            output += "\ncontains conventions:\n"
            conventions = system.findall("convention")
            if len(conventions) == 0:
                output += "None.\n"
            else:
                output += string.join(map(lambda x: x.text, conventions),
                                      ', ')
                output += "\n"
            print output

def edit():
    #TODO
    return

def new():
    #TODO
    return

