#!/usr/bin/python

#######################################
#
# conventionmaker.py
#
# Interactive methods for making and viewing
# *.conv XML files
#
####################################


# standard library imports
import glob
import string
from xml.etree import ElementTree

from common import *

def view(directory="./conventionsv2/"):
    """
    displays the name(s) of conventions provided by  existing convention XML 
    files (*.conv) in the ./conventionsv2/ directory
    """
    
    conventionfiles = glob.glob(directory + "*.conv")
    if len(conventionfiles) == 0:
        print "No convention files currently available.\n"
    else:
        print "Available conventions:"
        for conventionfile in conventionfiles:
            try:
                convention = ElementTree.parse(conventionfile)
            except Exception, inst:
                print "\nError parsing file %s: %s" % (conventionfile, 
                                                       inst)
                continue
            output = ""
            # output += conventionfile + " provides "
            names = convention.findall("name")
            if len(names) != 0:
                output += names[0].text 
                if len(names) > 1:
                    del names[0]
                    output += " (A.K.A: " 
                    output += string.join(map(lambda x: x.text, names), ', ')
                    output += ")"
            print output
    return len(conventionfiles)

def edit():
    """
    allows users to update a convention, e.g.
    by adding alternate names or adjusting requirements
    """
    #TODO

def new():
    """
    allows users to create a new convention file
    (with limited control)
    """
    convention = ElementTree.Element('convention')
    print "What is the name of this convention?"
    names = []
    name = None
    while not name:
        name = raw_input('Name: ')
    while name:
        names.append(name)
        name = raw_input('Alternate name (ENTER to skip): ')
    for anyname in names:
        newname = ElementTree.Element('name')
        newname.text = anyname
        convention.append(newname)
    #TODO implement convention type (opening, response, etc.)
    print "For your reference, the currently",
    print "available conventions are as follows."
    n = view()
    if len(names) > 0:
        name = names[0]
    else:
        name = "(unnamed)"
    print "What conventions does", name, "require?"
    print "Enter their names, or simply press ENTER to proceed."
    requires = []
    req = raw_input('Required convention: ')
    while req:
        requires.append(req)
        req = raw_input('Next required convention: ')
    for reqconv in requires:
        newreq = ElementTree.Element('reqconv')
        newreq.set("name",reqconv)
        convention.append(newreq)
    print "What conventions does", name, "force?"
    forces = []
    force = raw_input(name + ' forces: ')
    while force:
        forces.append(force)
        force = raw_input(name + ' also forces: ')
    for subconv in forces:
        newsub = ElementTree.Element('subconv')
        newsub.set("name",subconv)
        convention.append(newsub)
    print "So far, only a very limited class of conventions are supported",
    print "by this utility; you're in luck if and only if", name,
    print "can be specified explicitly by a list of relevant auction sequences."
    action = "foo"
    auctions = []
    while action:
        print "Enter a possible action (a legal call) for the", name, "bidder."
        print "(ENTER to end.)"
        action = raw_input( name + " bidder's call: ")
        if action:
            newaction = ElementTree.Element("action")
            newaction.set("bid",action)
            print "Enter possible sequences of calls made by both pairs"
            print "BEFORE the", name, "bid of", action,
            print "including ALL passes. Legal calls are"
            print "<#><strain> where <#> is 1-7 and <strain> is C,",
            print "D, H, S, or NT, as well as PASS, X, and XX."
            print "These are case sensitive."
            print "If you enter an illegal auction,",
            print "it will never come up, but that's your problem."
            print "Enter a single space for an opening bid in first seat.\n"

            print "Enter first auction (or enter an empty auction to end)."
            print "Enter 'same' as first bid to use the same set of auctions",
            print "just used."
            auction = []
            bid = "foo"
            while bid:
                bid = raw_input('Enter a bid (ENTER to end auction): ')
                if bid == 'same':
                    bid = None
                elif bid:
                    auctions = []
                    auction.append(bid)
            if len(auction) > 0:
                while len(auction) > 0:
                    auctions.append(auction)
                    auction = []
                    print "Enter next auction (enter an empty auction to end)."
                    bid = "foo"
                    while bid:
                        bid = raw_input('Enter a bid (ENTER to end auction): ')
                        if bid:
                            auction.append(bid)
            possibleauctions = ElementTree.Element("PossibleAuctions")
            for anyauction in auctions:
                auctionstring = string.join(anyauction, ', ')
                newauction = ElementTree.Element("auction")
                newauction.text = auctionstring
                possibleauctions.append(newauction)
            newaction.append(possibleauctions)
            
            print "Enter the conditions for taking action", action, 
            print "(invalid input will default to specified value)"
            print "\nHigh card points (HCP) are computed as A=4, K=3, Q=2, J=1"
            val = raw_input("Minimum HCP (range 0-40, default 0): ")
            if val.isdigit():
                if 0 <= int(val) <= 40:
                    HCPmin = val
                else:
                    print "Set to default value of 0."
                    HCPmin = "0"
            else:
                print "Set to default value of 0."
                HCPmin = "0"
            val = raw_input("Maximum HCP (range 0-40, default 40): ")
            if val.isdigit():
                if 0 <= int(val) <= 40:
                    HCPmax = val
                else:
                    print "Set to default value of 40."
                    HCPmax = "40"
            else:
                print "Set to default value of 40."
                HCPmax = "40"
            newHCP = ElementTree.Element("HCP")
            newHCP.set("min", HCPmin)
            newHCP.set("max", HCPmax)
            newaction.append(newHCP)
            # TODO: Add support (no pun intended) for support points
            # (in various trump suits) right here!
            print "Now we move on to suit lengths."
            newshape = ElementTree.Element("shape")
            suits = {'S':"spade", 'H':"heart", 'D':"diamond", 'C':"club"}
            mins = {'S':None, 'H':None, 'D':None, 'C':None}
            maxs = {'S':None, 'H':None, 'D':None, 'C':None}
            for suit in SUITS:
                val = raw_input("Minimum " + suits[suit] +
                                " length (range 0-13, default 0): ")
                if val.isdigit():
                    if 0 <= int(val) <= 13:
                        mins[suit] = val
                    else:
                        print "Set to default value of 0"
                        mins[suit] = "0"
                else:
                    print "Set to default value of 0"
                    mins[suit] = "0"
                val = raw_input("Maximum " + suits[suit] + 
                                    " length (range 0-13, default 13): ")
                if val.isdigit():
                    if 0 <= int(val) <= 13:
                        maxs[suit] = val
                    else:
                        print "Set to default value of 13"
                        maxs[suit] = "13"
                else:
                    print "Set to default value of 13"
                    maxs[suit] = "13"
                newsuit = ElementTree.Element(suits[suit] + "s")
                newsuit.set("min",mins[suit])
                newsuit.set("max",maxs[suit])
                newshape.append(newsuit)
            newaction.append(newshape)
            convention.append(newaction)
    filename = "./conventions/auto" + repr(n + 1) + ".conv"
    ElementTree.ElementTree(convention).write(filename)
    print "Successfully wrote", filename, "containing convention", name + "."
        
