#!/usr/bin/python

######################################
#
# prettyprint.py
#
# Usage: prettyprint.py xmlfile
#
# Writes a new XML file with newlines and indentation
# added, called xmlfile.pretty
#
####################################
import sys

from xml.etree import ElementTree as et

def indent(elem, level=0):
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

def main():
    infile = sys.argv[1]
    try:
        tree = et.parse(infile)
    except Exception, inst:
        sys.exit("Error parsing file "+ infile + ": " + inst)
    outfile = infile + ".pretty"
    elem = tree.getroot()
    indent(elem)
    et.ElementTree(elem).write(outfile)
    print "Successfully wrote", outfile

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: prettyprint.py <infile>")
    main()
