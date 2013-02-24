#!/usr/bin/python

###################################################
#
# interactivebidding.py
#
# This is the UI script; only IO considerations go here
#
###################################################

# common.py contains most of the bridge classes and methods we need
from common import *
# conventionmaker.py contains methods for making XML "*.conv" files
import conventionmaker
# makesystem.py contains methods for making "*.system" files
import makesystem
# handgenerator.py contains methods for generating random hands
import handgenerator
# bidder
import bidder

# Here's the menu of options the player has (TODO: improve aesthetics)
def ShowMenu():
    print ''' What would you like to do? 

PLAYER MANAGEMENT:                          CONVENTION/SYSTEM MANAGEMENT:
  Create a (h)uman player,                    Create a (n)ew convention,
  Create a (c)omputer player,                 View available con(v)entions,
 (S)ee a list of players you've created,     (M)odify a convention,
                                              Create a new s(y)stem,           
HAND GENERATOR:                               View available sys(t)ems,
 (G)enerate a totally random deal,            Modi(f)y a system                 
  Generate a random deal with c(r)iteria,     
 
BIDDING:            HELP:                  OTHER:
  (B)id a hand,       (?) Get help            (Q)uit\n'''

# self-explanatory
def Wait():
    print "\n(Press ENTER to continue)\n"
    foo = raw_input()
    return 0

def tellhand(auction, output = 'CLI', hidden = set([]), showstats = False):
    """
    prints the current hand in Auction auction, along
    with info on dealer and vulnerability and board number
    hidden is a list of PLAYERS to hide ('N', 'S', 'W', 'E')
    """
    if not output == 'CLI':
        print "tellhand() is only implemented for the command line, so far.\n"
        return
    # a dict of dicts of handstring for the nonhidden players and empty
    # strings for the hidden players
    handstrings = dict([(player, 
                         dict([(suit, suit + ": " + 
                                auction.hands[player].suits[suit].sortstr()) 
                               for suit in SUITS])
                         if player not in hidden else 
                         dict([(suit,'') for suit in SUITS]))
                        for player in PLAYERS])
    # a dict with 'd' for the dealer and ' ' for the other players
    dealstrings = dict([(player,'d' if player == auction.dealer else ' ')
                        for player in PLAYERS])
    # a dict with 'v' for vulnerable players and ' ' for nonvul players
    vulstrings = dict([(player, 'v' if auction.vuls[player] else ' ')
                       for player in PLAYERS])
    # a string displaying the Board # if there is one
    boardstring = (('Board #' + repr(auction.boardnum) + '.') 
                   if auction.boardnum else '')
    # a string displaying the vulnerability
    vulnstring = ('Everyone' if auction.vuls['N'] and auction.vuls['E']
                  else ('North-South' if auction.vuls['N'] 
                        else ('East-West' if auction.vuls['E']
                              else 'Nobody'))) + ' vulnerable.'
    boardnumabbrev = repr(auction.boardnum).rjust(2) if auction.boardnum else "  "
    # print what we want
    print boardstring, vulnstring, "Dealer is", auction.dealer
    print 'North hand'.center(38)
    for suit in SUITS:
        print  handstrings['N'][suit].ljust(16).rjust(32)
    print 'West hand'.center(16) + '+----+' + 'East hand'.center(16)
    print (handstrings['W']['S'].ljust(16) + 
           '| ' + vulstrings['N'] + dealstrings['N'] + ' | ' +
           handstrings['E']['S'].ljust(16))
    print (handstrings['W']['H'].ljust(16) + '|' + vulstrings['W'] 
           + boardnumabbrev + vulstrings['E'] 
           + '| ' + handstrings['E']['H'].ljust(16))
    print (handstrings['W']['D'].ljust(16) + 
           '|' + dealstrings['W'] + '  ' +  dealstrings['E'] + '| ' +
           handstrings['E']['D'].ljust(16))
    print (handstrings['W']['C'].ljust(16) + 
           '| ' + vulstrings['S'] + dealstrings['S'] + ' | ' +
           handstrings['E']['C'].ljust(16))
    print '+----+'.center(38)
    print 'South hand'.center(38)
    for suit in SUITS:
        print handstrings['S'][suit].ljust(16).rjust(32)
        
    if showstats:
        stats = "Hand statistics:\n         "
        for player in PLAYERS:
            stats += (player + ":").ljust(8)
        stats += "\nShape:  "
        for player in PLAYERS:
            stats +=  string.join([
                    repr(auction.hands[player].shape()[suit]) 
                    for suit in SUITS], '-').ljust(8)
        stats += "\nHCP:    "
        for player in PLAYERS:
            stats += repr(auction.hands[player].hcp()).ljust(8)
        stats += "\nlosers: "
        for player in PLAYERS:
            stats += repr(auction.hands[player].losers()).ljust(8)
        print stats


def tellauction(auction, output = 'CLI'):
    """
    prints auction.auction prettily for an Auction auction
    """
    if not output == 'CLI':
        print "tellauction() only implemented for the command line, so far.\n"
        return
    dealerindex = PLAYERS.index(auction.dealer)
    
    # headings
    print ("North".center(9) + "East".center(9) + 
           "South".center(9) +  "West".center(9))
    
    toprint = ""
    for i in range(dealerindex):
        toprint += "".ljust(9)

    columnindex = dealerindex

    bidstrings = [bid.center(9) for bid in auction.auction]
    for bid in bidstrings:
        toprint += bid
        columnindex = (columnindex + 1) % 4
        if not columnindex:
            toprint += "\n"

    if not auction.over:
        toprint += "?".center(9)

    print toprint

    if auction.over:
        print "\n Final Contract: ",
        if not auction.bidmade:
            print "PASSOUT"
        else:
            print auction.auction[len(auction.auction) - auction.numnonstd - 1],
            if not auction.numnonstd == auction.numpasses:
                print auction.auction[len(auction.auction) - 4],
            print "by", PLAYERS[(dealerindex + len(auction.auction)
                                 - auction.numnonstd - 1) % 4]

# quitting
def Goodbye():
    print "Goodbye!\n"
    return 1

# whent he user types something wrong
def Default():
    print "Sorry, that's not a valid command.\n"
    return Wait()

# Creates a human player
def CreateHuman():
    print "What is the name of the player you wish to create?\n"
    name = raw_input('Name: ')
    for player in players:
        if player.name == name:
            print "A player of that name already exists!\n"
            return Wait()
    players.add(HumanPlayer(name))
    print "Created human player", name + ".\n"
    return Wait()

# Creates a computer player using a pre-existing system file
def CreateComputer():
    print "What is the name of the player you wish to create?\n"
    name = raw_input('Name: ')
    for player in players:
        if player.name == name:
            print "A player of that name already exists!\n"
            return Wait()
    print "What is the name of", name + "'s system? Available systems:\n"
    makesystem.view()
    systems = bidder.makesystemdict()
    system = raw_input('System name: ')
    if not system in systems.keys():
        print "No system of that name is on record!\n"
        return Wait()
    newplayer = bidder.ComputerPlayer(name, systems[system])
    players.add(newplayer)
    print "Created computer player", name, "with system", system + ".\n"
    return Wait()

# Shows a list of players in the current session 
# (TODO: make players persistent across sessions via .plyr files)
def SeePlayers():
    print "Current players are:\n"
    if len(players) == 0:
        print "None\n"
    for player in players:
        print player.name + " (" + player.type + ")\n"
    return Wait()

# Invokes conventionmaker to create a new .conv file
def CreateConvention():
    print "ALERT: The current versions of this utility supports only"
    print "old (version 1) convention file format. These files are"
    print "not supported by the automatic bidder. Educational use only."
    conventionmaker.new()
    return Wait()

# Lists .conv files in ./conventions/ directory and
# the names of the associated conventions
def SeeConventions():
    n = conventionmaker.view()
    print n, "conventions found."
    return Wait()

def CreateSystem():
    print "Not yet implemented!\n"
    return Wait()

def SeeSystems():
    makesystem.view()
    return Wait()

def GeneratorPlus():
    # TODO: allow user to specify how hard to look for the hand (# hands to try)
    randomdeal = CriteriaGenerator()
    if randomdeal:
        tellhand(randomdeal)
    else:
        print "There don't seem to be many hands satisfying those criteria."
    return Wait()

def getValue(prompt, rangemin, rangemax, default):
    """ 
    Prompt user for a non-negative integer value in a specified 
    range with a specified default for no or invalid input.
    """
    val = raw_input(prompt + " (range " + repr(rangemin) + "-" + 
                    repr(rangemax) + ", default " + repr(default) +"): ")
    if val.isdigit():
        if rangemin <= int(val) <= rangemax:
            value = val
        else:
            print "Set to default value of", default
            value = default
    else:
        print "Set to default value of", default
        value = default
    return value

def CriteriaGenerator():
    # TODO: allow user to specify dealer and vulnerability
    theplayers = {'N':"North", 'S':"South", 'E':"East", 'W':"West"}
    thesuits = {'S':"spade", 'H':"heart", 'D':"diamond", 'C':"club"}
    suits = {'N':None, 'S':None, 'E':None, 'W':None}
    ind_strengths = {'N':None, 'S':None, 'E':None, 'W':None}
    print "Note that in the invalid entries will result in default value."
    print "\nSpecify vulnerability? Enter 'NS', 'EW', 'none', or 'all'."
    vul = raw_input("Vulnerability (default random): ")
    if vul not in ['NS', 'EW', 'none', 'all']:
        vul = 'random'
    print "\nSpecify dealer? Enter 'N', 'S', 'E', or 'W'."
    dealer = raw_input("Dealer (default random): ")
    if dealer not in PLAYERS:
        dealer = 'random'
    print "\nFor which players would you like to specify length and/or strength"
    print "in at least one suit?"
    print "Enter a string containing only characters 'N', 'S', 'E', 'W'."
    playerstring = raw_input("Players (default none): ")
    myplayers = list(playerstring)
    if not set(myplayers) <= set(PLAYERS):
        myplayers = []
    for player in PLAYERS:
        if player not in myplayers:
            suits[player] = {'S':{"strength":{"min":0,"max":10}, 
                                  "shape":{"min":0, "max":13}},
                             'H':{"strength":{"min":0,"max":10}, 
                                  "shape":{"min":0, "max":13}},
                             'D':{"strength":{"min":0,"max":10}, 
                                  "shape":{"min":0, "max":13}},
                             'C':{"strength":{"min":0,"max":10}, 
                                  "shape":{"min":0, "max":13}}}
    for player in myplayers:
        suitdict = {'S':None, 'H':None, 'D':None, 'C':None}
        print "For which of", theplayers[player] + "'s suits would you like to"
        print "specify specific length and HCP ranges?"
        print "Enter a string containing only characters 'S', 'H', 'D', 'C'."
        specsuitsstring = raw_input("Suits (default none): ")
        specsuits = list(specsuitsstring)
        if not set(specsuits) <= set(SUITS):
            specsuits = []
        for suit in SUITS:
            if suit not in specsuits:
                suitdict[suit] = {"strength":{"min":0,"max":10}, 
                                  "shape":{"min":0, "max":13}}
        for suit in specsuits:
            maxl = getValue(theplayers[player] + "'s maximum " +
                            thesuits[suit] + " length", 0, 13, 13)
            minl = getValue(theplayers[player] + "'s minimum " +
                            thesuits[suit] + " length", 0, 13, 0)
            maxs = getValue(theplayers[player] + "'s maximum " + 
                            thesuits[suit] + " HCP strength", 0, 10, 10)
            mins = getValue(theplayers[player] + "'s minimum " + 
                            thesuits[suit] + " HCP strength", 0, 10, 0)
            info = {"strength":{"min":int(mins),"max":int(maxs)}, 
                    "shape":{"min":int(minl), "max":int(maxl)}}
            suitdict[suit] = info
        suits[player] = suitdict
    
    print "\nFor which players would you like to specify total HCP strength?"
    print "Enter a string containing only characters 'N', 'S', 'E', 'W'."
    playerstring = raw_input("Players (default none): ")
    myplayers = list(playerstring)
    if not set(myplayers) <= set(PLAYERS):
        myplayers = []
    for player in PLAYERS:
        if player not in myplayers:
            ind_strengths[player] = {"min":0, "max":40}
    for player in myplayers:
        min = getValue(theplayers[player] + "'s minimum " +  
                       " HCP strength", 0, 40, 0)
        max = getValue(theplayers[player] + "'s maximum " +  
                       " HCP strength", 0, 40, 40)
        ind_strengths[player] = {"min":int(min), "max":int(max)}
    
    print "\nNext enter the total strength ranges for each partnership."
    minns = getValue("North-South's minimum HCP strength", 0, 40, 0)
    maxns = getValue("North-South's maximum HCP strength", 0, 40, 40)
    northsouth = {"min":int(minns), "max":int(maxns)}
    minew = getValue("\nEast-West's minimum HCP strength", 0, 40, 0)
    maxew = getValue("East-West's maximum HCP strength", 0, 40, 40)
    eastwest = {"min":int(minew), "max":int(maxew)}
    comb_strengths = {'NS':northsouth, 'EW':eastwest}
    criteria = handgenerator.Criteria(suits, ind_strengths, comb_strengths)
    deal = handgenerator.criteriadeal(criteria, dealer, vul)
    return deal

def GetHelp():
    """
    print README.txt to stdout
    """
    readme = open("README.txt", "r")
    for line in readme:
        print line,
    return Wait()

def GenerateDeal():
    randomdeal = handgenerator.randomdeal()
    # tellhand(randomdeal, 'CLI', set([]), True)
    tellhand(randomdeal)
    return Wait()  

def nextposn(posn):
    currentindex = PLAYERS.index(posn)
    nextindex = (currentindex + 1) % 4
    return PLAYERS[nextindex]

def BidHand():
    myplayers = {'N':None, 'S':None, 'E':None, 'W':None}
    print "Select players for each position."
    print "Current players are:\n"
    if len(players) == 0:
        print "None\n"
    for player in players:
        s = player.name + " (" + player.type + ")\n"
        print s
    for posn in PLAYERS:
        flag = False
        while not flag:
            name = raw_input('Select ' + posn + ' name: ')
            for player in players:
                if player.name == name:
                    flag = True
                    myplayers[posn] = player
                    break
            if not flag:
                print "There's no player of that name."
        
    print "Generate a (r)andom deal, or a random deal according to (c)riteria?"
    mydeal = None
    while not mydeal:
        choice = raw_input('Enter a choice: ')
        choices = { 'R':handgenerator.randomdeal, 
                    'r':handgenerator.randomdeal,
                    'C':CriteriaGenerator,
                    'c':CriteriaGenerator }
        mydeal = choices.get(choice, lambda:None)()

    print "Today we'll be playing..."
    tellhand(mydeal, 'CLI', set(PLAYERS), False)

    for posn in PLAYERS:
        if myplayers[posn].type == 'Computer':
            myplayers[posn].hand = mydeal.hands[posn]
            myplayers[posn].currseq = None

    Wait()

    currentposn = mydeal.dealer

    while not mydeal.over:
        currentplayer = myplayers[currentposn]
        if currentplayer.type == 'Human':
            hidden = set(PLAYERS)
            hidden.remove(currentposn)
            tellhand(mydeal, 'CLI', hidden, False)
            tellauction(mydeal)
            print currentplayer.name, "it's your turn to bid"
            flag = False
            while not flag:
                bid = raw_input('Enter a bid: ')
                flag = mydeal.addbid(bid)
                if not flag:
                    print "Invalid bid."
        else:
            bid = currentplayer.bid(mydeal)
            if bid is None:
                bid = 'PASS'
            flag = mydeal.addbid(bid)
            print "Computer player", currentplayer.name, "bid", bid + "."
            if not flag:
                print currentplayer.name, "made an invalid bid! Uh oh!"
                return Wait()
        currentposn = nextposn(currentposn)

    print "This was the hand:"
    tellhand(mydeal, 'CLI', set([]), True)
    print "This was the auction:"
    tellauction(mydeal)

    print "Thanks for using the interactive bidding feature!"
                            
    return Wait()

def ModifyConvention():
    print "Not yet implemented!\n"
    return Wait()

def ModifySystem():
    print "Not yet implemented!\n"
    return Wait()

# The following gives the basic UI for the interactivebidding script
print "Welcome to SLAMBidding command-line version 0.0!\n"
print "(Best viewed using a 24 x 80 character terminal window.)\n"
players = set([]) # start each session with an empty set of players
# TODO: In a future version, store player files in a subdirectory
goodbye = 0
while not goodbye:
    ShowMenu()
    choice = raw_input('\n\n\n\n\nChoice: ')
    # this is a trick for getting around Python's lack of 'switch'
    choices = { 'H':CreateHuman, 'h':CreateHuman,
                'C':CreateComputer, 'c':CreateComputer,
                'S':SeePlayers, 's':SeePlayers,
                'G':GenerateDeal, 'g':GenerateDeal,
                'B':BidHand, 'b':BidHand,
                'Q':Goodbye, 'q':Goodbye,
                'N':CreateConvention, 'n':CreateConvention,
                'V':SeeConventions, 'v':SeeConventions,
                'Y':CreateSystem, 'y':CreateSystem,
                'T':SeeSystems, 't':SeeSystems,
                'R':GeneratorPlus, 'r':GeneratorPlus,
                'M':ModifyConvention, 'm':ModifyConvention,
                'F':ModifySystem, 'f':ModifySystem,
                '?':GetHelp }
    goodbye = choices.get(choice, Default)()
