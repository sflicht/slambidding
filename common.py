#!/usr/bin/python

###########################################
#
# common classes and methods
#
###########################################

import string

SUITS = ['S', 'H', 'D', 'C']
STRAINS = ['S', 'H', 'D', 'C', 'NT']
LEVELS = range(1, 7)
PLAYERS = ['N', 'E', 'S', 'W']
STNDCALLSDICT = {'1C':(1,'C'), '1D':(1,'D'), '1H':(1,'H'), '1S':(1,'S'), 
                 '1NT':(1, 'NT'), '2C':(2,'C'), '2D':(2,'D'), '2H':(2,'H'), 
                 '2S':(2,'S'), '2NT':(2,'NT'), '3C':(3,'C'), '3D':(3,'D'), 
                 '3H':(3,'H'), '3S':(3,'S'), '3NT':(3,'NT'), '4C':(4,'C'), 
                 '4D':(4,'D'), '4H':(4,'H'), '4S':(4,'S'), '4NT':(4,'NT'),
                 '5C':(5,'C'), '5D':(5,'D'), '5H':(5,'H'), '5S':(5,'S'), 
                 '5NT':(5,'NT'), '6C':(6,'C'), '6D':(6,'D'), '6H':(6,'H'), 
                 '6S':(6,'S'), '6NT':(6,'NT'), '7C':(7,'C'), '7D':(7,'D'), 
                 '7H':(7,'H'), '7S':(7,'S'), '7NT':(7,'NT')}
STNDCALLS = ['1C','1D','1H','1S','1NT','2C','2D','2H','2S','2NT',
             '3C','3D','3H','3S','3NT','4C','4D','4H','4S','4NT',
             '5C','5D','5H','5S','5NT','6C','6D','6H','6S','6NT',
             '7C','7D','7H','7S','7NT']
SPECCALLS = ['X', 'XX', 'PASS']

def compare(a, b):
    """
    compare two cards (in a notrump sense)
    returns + if a is lower than b, - if b is lower than a, and 0 if 
    a and b are equal.
    """
    values = {'2':2, '3':3, '4':4, '5':5, '6':6, '7':7, 
              '8':8, '9':9, 'T':10, 'J':11, 'Q':12, 'K':13, 'A':14}
    return -1 * cmp(values[a],values[b])        

class Auction:
    """
    an Auction is initialized with a specified dealer, 
    NS vulnerability (bool), EW vulnerability (bool), board number,  
    N Hand, S Hand, E Hand, W Hand.
    
    attributes:
    auction is the auction so far (a list of calls, 
                                   which are themselves strings)
    dealer is the dealer, a character 'N', 'S', 'E', or 'W'
    vuls is a dict of 4 bools keyed by PLAYERS reflecting vulnerabilities
    boardnum is the board number of the hand, if any
    hands is a dict of Hands keyed by PLAYERS
    bidmade is a bool saying whether anyone has bid yet
    numpasses counts how many passes have been made since the last bid
       (or the start of the auction, whichever is most recent)
    numnonstd counts how many X, XX, and PASS calls have been made
       since the last bid of a suit/level
    over is a bool saying whether the auction has concluded
    """
    def __init__(self, dealer, NSvul, EWvul, bdnm, Nhand, Shand, Ehand, Whand):
        self.dealer = dealer    
        nvul = True if NSvul else False
        svul = True if NSvul else False
        evul = True if EWvul else False
        wvul = True if EWvul else False
        self.vuls = {'N':nvul, 'S':svul, 'E':evul, 'W':wvul}
        self.boardnum = bdnm 
        self.hands = {'N':Nhand, 'S':Shand, 'E':Ehand, 'W':Whand}
        self.auction = []
        self.bidmade = False
        self.numpasses = 0
        self.numnonstd = 0
        self.over = False
    
    def availablebids(self):
        """
        returns a list of legal calls for the next player
        """
        # if the auction is over no bids are legal
        if self.over:
            return []

        # if no bid has been made, PASS and all STNDCALLS are legal,
        # but X and XX are not
        if not self.bidmade:
            return ['PASS'] + STNDCALLS

        # the last non-PASS call
        lastbid = self.auction[len(self.auction) - self.numpasses - 1]
        bids = ['PASS']
        if lastbid in STNDCALLS and not self.numpasses == 1:
            bids.append('X')
        elif lastbid == 'X' and not self.numpasses == 1:
            bids.append('XX')
        # the last not-PASS-X-XX call    
        laststdbid = self.auction[len(self.auction) - self.numnonstd - 1]
        for bid in STNDCALLS:
            if STNDCALLS.index(laststdbid) < STNDCALLS.index(bid):
               bids.append(bid)

        return bids       


    def addbid(self, bid):
        """
        returns a bool saying whether bid is a valid call
        for the next player in the auction to make
        if true, appends the bid to the self.auction, and
        updates bidmade, numpasses, and over appropriately
        """
        legal = self.availablebids()
        if bid not in legal:
            return False
        elif bid == 'PASS' or bid == 'P' or bid == 'pass' or bid == 'Pass':
            self.numpasses = self.numpasses + 1
            self.numnonstd = self.numnonstd + 1
            if self.numpasses == (3 if self.bidmade else 4):
                self.over = True
            bid = 'PASS'
        elif bid in STNDCALLS:
            self.bidmade = True
            self.numpasses = 0
            self.numnonstd = 0
        else:
            self.numpasses = 0
            self.numnonstd = self.numnonstd + 1

        self.auction.append(bid)
        return True        

class Suit:
    """
    a Suit is contains a set (Suit.suit) of cards
    """
    def __init__(self, suit):  # constructed with a string or list of cards;
        self.suit = set(suit)  # the suit itself is a set
    
    def highcards(self):
        """
        return the set of high cards in the suit
        high cards are 9, T, J, Q, K, A    
        """
        return self.suit & set('AKQJT9') 

    def honors(self):
        """
        return the set of legit honors in the suit
        honors are T, J, Q, K, A
        """
        return self.suit & set('AKQJT')
    
    def hcp(self):             
        """
        compute HCP of the suit
        """
        honors = list(self.highcards())
        hcp = 0
        hcp += honors.count('J')
        hcp += 2 * honors.count('Q') 
        hcp += 3 * honors.count('K')
        hcp += 4 * honors.count('A')
        return hcp

    def controls(self):
        """
        compute controls (A=2, K=1) in suit
        """
        honors = list(self.highcards())
        controls = 0
        if 'K' in honors:
            controls += 1
        if 'A' in honors:
            controls += 2
        return controls
    
    def sort(self):
        """
        return a sorted list of cards in the suit
        """
        sortsuit = list(self.suit)
        return sorted(sortsuit, compare)
    
    def sortstr(self):
        """
        return sorted suit as a string
        """
        sortsuit = self.sort()
        sortstr = string.join(sortsuit, '')
        return sortstr
    
    
    def len(self):
        """
        compute length of the suit
        """
        return len(self.suit)

    
    def losers(self):
        """
        compute losing trick count
        """
        length = self.len()
        if length == 0:
            return 0
        elif length == 1:
            rel = set('A')
        elif length == 2:
            rel = set('AK')
        else:
            rel = set('AKQ')
        return len(rel - self.highcards())   

class Hand:
    """
    a Hand is constructed of four Suits (in order SHDC)
    """
    def __init__(self, spades, hearts, diamonds, clubs):
        self.suits = {'S':spades, 'H':hearts, 'D':diamonds, 'C':clubs}
    
    def hcp(self):
        """
        compute HCP of a hand
        """
        hcp = 0
        for suit in SUITS:
            hcp += self.suits[suit].hcp()
        return hcp

    def controls(self):
        """
        compute controls of the hand
        """
        controls = 0
        for suit in SUITS:
            controls += self.suits[suit].controls()
        return controls
    
    def losers(self):
        """
        compute LTC of a hand
        """
        losers = 0
        for suit in SUITS:
            losers += self.suits[suit].losers()
        return losers
    
    def shape(self):
        """
        return the SHDC shape of the hand as a dict keyed by SUITS
        """
        return dict([(suit,self.suits[suit].len()) for suit in SUITS])
    
    def supportpts(self, trump):
        """
        returns number of support points when trump (from SUITS) is trumps

        this is computed as
        HCP + (trumplength - 4) + 5 points per void outside trumps
        + 3 points per singleton outside trumps + 1 point per doubleton
        outside trumps + (N - 5) points for every suit of length > 5
        outside trumps
        """
        count = self.hcp()
        mysuits = self.shape()
        count += mysuits(trump) - 4
        suitset = set(SUITS)
        suitset.remove(trump)
        for suit in suitset:
            if mysuits(suit) > 5:
                count += mysuits(suit) - 5
            if mysuits(suit) < 1:
                count += 2
            if mysuits(suit) < 2:
                count += 2
            if mysuits(suit) < 3:
                count += 1
        return  count

    def stopper(self, suit):
        """
        return True if the hand has a stopper in suit, False otherwise
        a stopper is Axx, Kxx, QJx, QT9, Qxxx or longer
        """
        honors = self.suits[suit].highcards()
        length = self.shape()[suit]
        if length < 3:
            return False
        elif 'A' in honors or 'K' in honors:
            return True
        elif 'Q' in honors and ('J' in honors or ('T' in honors
                                                  and '9' in honors)):
            return True
        elif length > 3 and 'Q' in honors:
            return False

    def halfstopper(self, suit):
        """
        return True if the hand has a stopper or halfstopper in suit, 
        False otherwise.
        a half-stopper is A, Kx, Qxx, Jxxx or longer
        """
        honors = self.suits[suit].highcards()
        length = self.shape()[suit]
        if self.stopper(suit):
            return True
        elif length < 1:
            return False
        elif 'A' in honors:
            return True
        elif length > 1 and 'K' in honors:
            return True
        elif length > 2 and 'Q' in honors:
            return True
        elif length > 3 and 'J' in honors:
            return True
        else:
            return False

class Player:
    """
    a Player is initialized with a name
    
    attributes:
    name is the name
    """
    def __init__(self, name):
        self.name = name   


class HumanPlayer(Player):
    def __init__(self, name):
        Player.__init__(self, name)
        self.type = 'Human'


        

        
        
        

        
        

        
    
