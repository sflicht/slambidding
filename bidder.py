#!/usr/bin/python

#############################################
#
# bidder.py
#
# methods for finding a bid from a (computer) player's
# system file and the current auction (i.e. list of bids)
#
# this is designed to work with *.conv XML files
# adhering to the conventionsv2 format
# (see conventionsv2/conventionsv2.txt)
#
#############################################

# common bridge classes (Suit, Hand, Auction, etc.)
from common import *

import glob
import string

# XML manipulation
from xml.etree import ElementTree as ET

# useless wrapper class (like an Object(), if such a thing existed in Python)
class Actions():
    def __init__(self):
        return
ACTIONS = Actions()
# A wrapper for three globals (recognizable actions)
ACTIONS.OPEN = ['open']
ACTIONS.CONSTR = ['raise', 'invite', 'accept', 'decline', 'ask', 'tell',
                 'pass', 'signoff', 'relay', 'relaybid']
ACTIONS.COMPET = ['overcall', 'balance', 'advance', 'competitiveraise']

TYPEELEMS = {'HCP':lambda p,e: CheckHCP(p,e),
             'spades':lambda p,e: CheckSuit(p, 'S', e),
             'hearts':lambda p,e: CheckSuit(p, 'H', e),
             'diamonds':lambda p,e: CheckSuit(p, 'D', e),
             'clubs':lambda p,e: CheckSuit(p, 'C', e)}
# to be supported in the future:
# EXTENDEDTYPEELEMS = ['support', 'stopper', 'vul']

def makeconventiondict(directory="./conventionsv2/"):
    """
    return a dict of convention filenames in directory
    as values keyed by thename(s) of the conventions provided by the file
    """
    conventionfiles = glob.glob(directory + "*.conv")
    conventions = []
    for conventionfile in conventionfiles:
        try:
            convention = ET.parse(conventionfile)
        except Exception, inst:
            print "\nError parsing file %s: %s" % (conventionfile, inst)
            continue
        names = convention.findall("name")
        for name in names:
            conventions.append((name.text, conventionfile))
    return dict(conventions)

def makesystemdict(directory="./systems/"):
    """
    return a dict of system filenames in directory
    as values keyed by thename(s) of the systems provided by the file
    """
    systemfiles = glob.glob(directory + "*.system")
    systems = []
    for systemfile in systemfiles:
        try:
            system = ET.parse(systemfile)
        except Exception, inst:
            print "\nError parsing file %s: %s" % (systemfile, inst)
            continue
        names = system.findall("name")
        for name in names:
            systems.append((name.text, systemfile))
    return dict(systems)
        
def ConvNameToSequence(convname, directory="./conventionsv2/"):
    """
    accepts a convention name and a directory of convention files
    as arguments

    returns an Element object created from
    the *.conv file (conventionsv2 format) corresponding to convname
    stripped of everything except action elements and
    with all "convention" subelements (subconventions) replaced by the sets of
    of action elements specified in the corresponding *.conv files. 

    returns None on failure
    """
    # our specified conv's filename
    conventions = makeconventiondict(directory)
    convfilename = conventions.get(convname,None)
    if not convfilename:
        return None
    try:
        tree = ET.parse(convfilename)
    except Exception, inst:
        print "\nError parsing file %s: %s" % (convfilename, inst)
        return None
    elem = tree.getroot()
    nameelems = elem.findall("name")
    actions = elem.findall("actions")[0]
    
    # this will, ultimately, be what we return
    sequence = ET.Element("sequence")
    # fill it with all the actions from actions
    sequence[:] = actions[:]

    names = [elem.text for elem in nameelems]
    parent_map = dict((c, p) for p in sequence.getiterator() for c in p)
    subconventions = sequence.getiterator("subconvention")
    for subconvention in subconventions:
            parent = parent_map[subconvention]
            index = list(parent).index(subconvention)
            subconvname = subconvention.attrib["name"]
            filename = conventions.get(subconvname, None)
            if not filename:
                print "\nNo .conv file for", subconvname, "found"
                parent.remove(subconvention)
                continue
            print filename
            try:
                subtree = ET.parse(filename)
            except Exception, inst:
                print "\nError parsing file %s: %s" % (convfilename, inst)
                parent.remove(subconvention)
                continue
            subconv = subtree.getroot()
            parents = [p.text for p in subconv.findall("parent")]
            flag = False
            for pname in parents:
                if pname in names:
                    flag = True
            if not flag:
                continue
            # recursively perform this method on the subconvention
            subsequence = ConvNameToSequence(subconvname, directory)
            # substitute the result for the subconvention in sequence
            parent[index:index+1] = list(subsequence)
    return sequence

def LoadSystem(Cplayer, systemfile, directory="./conventionsv2/"):
    """
    accepts a computer player and systemfile as arguments, [and a conventions
    directory]. initializes the computer player's system by converting the 
    system to an XML hierarchy of recognizable bidding sequences, and
    attaching it to the computer player.
    """
    print "Attempting to load", systemfile, "for player", Cplayer.name
    mysystem = ET.Element("system")
    try:
        tree = ET.parse(systemfile)
    except Exception, inst:
        print "Error parsing", systemfile, ":", inst
        return None
    system = tree.getroot()
    print Cplayer.name+"'s system is:"
    print ET.tostring(system)
    convelems = system.findall("convention")
    for convelem in convelems:
        parents = convelem.findall("parent")
        if not len(parents) == 0:
            continue
        name = convelem.text
        print "Adding convention", name, "to system."
        sequence = ConvNameToSequence(name, directory)
        if not ET.iselement(sequence):
            print "Uh oh", repr(sequence), "is not an element"
        mysystem.append(sequence)
    Cplayer.system = mysystem
    print "Success!"

def CheckHCP(player, elem):
    """
    accepts a ComputerPlayer and a HCP element
    as arguments, and returns a bool saying whether the
    player's hand satisfies the corresponding HCP requirements
    """
    print "Checking whether", player.name + "'s hand satisfies", ET.tostring(elem)
    try:
        min = int(elem.get('min', '0'))
    except Exception:
        min = 0
    try:
        max = int(elem.get('max', '40'))
    except Exception:
        max = 40
    if not min <= player.hand.hcp() <= max:
        return False    
    return True

def CheckSuit(player, suit, elem):
    """
    accepts a Computer player, a suit (from SUITS),
    and a suit element (spades, hearts, etc.) as arguments,
    and returns a bool saying whether the player's hand satisfies
    the corresponding length, honors, and controls requirements
    in the suit.

    note that unrecognizable values are set to their defaults
    """
    try:
        minl = int(elem.get('min', '0'))
    except Exception:
        minl = 0
    try:
        maxl = int(elem.get('max', '13'))
    except Exception:
        maxl = 13
    try:
        minh = int(elem.get('honorsmin', '0'))
    except Exception:
        minh = 0
    try:
        maxh = int(elem.get('honorsmax', '5'))
    except Exception:
        maxh = 5
    try:
        minc = int(elem.get('controlsmin', '0'))
    except Exception:
        minc = 0
    try:
        maxc = int(elem.get('controlsmax', '3'))
    except Exception:
        maxc = 3
    if not minl <= player.hand.shape()[suit] <= maxl:
        print "Bad", suit, "length"
        return False
    #if not minh <= len(player.hand.suits[suit].honors()) <= minh:
    #    print "Bad", suit, "honors: need betwee", minh, "and", maxh, "but have", repr(player.hand.suits[suit].honors())
    #    return False
    #if not minc <= player.hand.suits[suit].controls() <= maxc:
    #    print "Bad", suit, "controls"
    #    return False
    return True

def CheckType(player, type):
    """
    accepts a computer player and a type element.
    returns True if the computer player's current hand satisfies
    the type, False otherwise.
    (False if hand is not initialized yet.)
    """
    print "Checking", player.name + "'s hand:"
    for elem in type:
        print "Testing", elem.tag
        if not elem.tag in TYPEELEMS.keys():
            print elem.tag, "type subelement not recognized."
            continue
        elif not TYPEELEMS[elem.tag](player, elem):
            print elem.tag, "type subelement violated."
            return False
        else:
            print elem.tag, "OK."
    print player.name +"'s hand is OK"
    return True

def CheckOver(action, auction):
    """
    Accepts an action element and a bidding sequence
    (e.g. an Auction.auction) as arguments.
    Returns true is the action is valid as the next bid in the 
    sequence, false otherwise.
    """
    overstring = action.get("over")
    if overstring is None:
        over = ['PASS']
    else:
        over = overstring.split(', ')
    if overstring == 'all':
        return True
    if len(auction)  == 0:
        return True
    if (action.tag == 'balance' and len(auction) > 2 and
        auction[len(auction) - 1] == 'PASS' and 
        PartnersLast(auction) == 'PASS'):
        try:
            lastcall = auction[len(auction) - 3]
        except Exception:
            return False
    else:
        try:
            lastcall = auction[len(auction) - 1]
        except Exception:
            return False
    if lastcall in over:
        return True
    else:
        return False

def PartnersLast(auction):
    """
    accepts a bidding sequence (e.g. an Auction.auction) as argument.
    return Partner's last bid in the sequence (i.e. the second to 
    last bid) if there is one, None otherwise.
    """
    try:
        bid = auction[len(auction) - 2]
    except Exception:
        bid = None
    return bid

class ComputerPlayer(Player):
    """
    initialized with a name, a systemfile, [and a conventions directory]
    """
    def __init__(self, name, systemfile, directory="./conventionsv2/"):
        Player.__init__(self, name)
        self.type = 'Computer'
        self.hand = None
        self.system = None
        self.currseq = None
        LoadSystem(self, systemfile, directory)
        

    def bid(self, auction):
        # check proper initialization
        if not self.hand:
            print "I can't see my hand!"
            return None
        if self.system is None:
            print "I don't know my system!"
            return None
        plast = PartnersLast(auction.auction)
        sequences = self.system.findall("sequence")
        openings = []
        overcalls = []
        balances = []
        for sequence in sequences:
            openings.extend(sequence.findall("open"))
            overcalls.extend(sequence.findall("overcall"))
            balances.extend(sequence.findall("balance"))
        
        # if no bid has been made in the auction, attempt to open
        if not auction.bidmade:
            print "Attempting to open. Possible openings:"
            print [action.get("bid", None) for action in openings]
            myaction = None
            for opening in openings:
                print "Testing opening", opening.get("bid", None)
                handtypes = opening.find("handtypes")
                if not handtypes:
                    continue
                for type in handtypes:
                    if CheckType(self, type):
                        myaction = opening
                        mybid = myaction.get("bid", None)
                        self.currseq = myaction
                        return mybid
                    print "Couldn't open", opening.get("bid", None), ":"
                    #print "My hand is", self.hand.suits['S'].sortstr(), 
                    #print self.hand.suits['H'].sortstr(), 
                    #print self.hand.suits['D'].sortstr(),
                    #print self.hand.suits['C'].sortstr()
                    print "Required hand type is", ET.tostring(type)
        # if you're not in a particular sequence and partner has not yet bid,
        # then attempt to overcall or balance
        elif self.currseq is None and (plast is None or plast == 'PASS'):
            print "Attempting to overcall or balance."
            actions = overcalls
            actions.extend(balances)
            myaction = None
            # for each competitive action
            for action in actions:
                handtypes = action.find("handtypes")
                # with specified handtypees
                if not handtypes:
                    continue
                # which is valid in the current auction
                if not CheckOver(action, auction.auction):
                    continue
                # if any handtype checks out, enter that sequence
                # by making the appropriate bid, wait for response from P
                for type in handtypes:
                    if CheckType(self, type):
                        myaction = action
                        mybid = myaction.get("bid", None)
                        self.currseq = myaction
                        return mybid
            print "Couldn't overcall or balance."
        # if you're already in a sequence, or if not but partner bid, 
        # then try to interpret partner's last call and take appropriate action
        else:
            print "Attempting to interpret my partner's bid"
            partnersauction = auction.auction[:]
            partnersauction.pop()
            partnersauction.pop()
            print "Partner had auction",
            print repr(partnersauction)
            if self.currseq is None:
                print "I have no current sequence"
            else:
                print "My last bid was", self.currseq.get("bid",None)
            if self.currseq is None:
                insequence = False
            else:
                insequence = True
            for sequence in sequences:
                if not insequence:
                    self.currseq = sequence
                partnersaction = None
                for action in self.currseq:
                    if action.tag == 'handtypes':
                        continue
                    print "Checking sequence", self.currseq.get("bid",None), 
                    print "-", action.get("bid", None)
                    if not CheckOver(action, partnersauction):
                        print "He could not have bid", action.get("bid", "")
                        continue
                    print "He could have bid", action.get("bid", "")
                    if PartnersLast(auction.auction) == action.get("bid", " "):
                        print "And indeed he did bid", 
                        print PartnersLast(auction.auction)
                        partnersaction = action
                    else:
                        print "But in fact be bid", 
                        print PartnersLast(auction.auction)
                # if you can't understand partner's action, take no action of 
                # your own
                    if partnersaction is None:
                        print "Partner's bid does not fit into this sequence"
                        myaction = None
                    else:
                        print "Understood partner's bid."
                        myaction = None
                        for subaction in partnersaction:
                            print "Testing response", subaction.get("bid", "")
                            handtypes = subaction.find("handtypes")
                            if not handtypes:
                                continue
                            if not CheckOver(subaction, auction.auction):
                                print "Cannot reply", subaction.get("bid", ""),
                                print "in this auction."
                                continue
                            for type in handtypes:
                                if CheckType(self, type):
                                    myaction = subaction
                                    mybid = myaction.get("bid", None)
                                    self.currseq = myaction
                                    print "I can reply", myaction.get("bid", "")
                                    return mybid
                                else:
                                    print "My hand does not fit the",
                                    print subaction.get("bid", ""), "reply"
                # if already in sequence, no need to check through all top
                # level sequences
                if insequence:
                    break
        # if we get here, myaction should be None
        self.currseq = None
        return "PASS"
