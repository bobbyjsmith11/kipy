#!/usr/bin/env python
#
#
# Tool for checking netlists against a spreadsheet or another netlist.
#
# It currently understands Eagle and PADS(DxDesigner) .ASC format netlists.
#
# --compare checks net connections and net names
# --comp2   checks only connections, ignores net names
# --flipcheck   checks to make sure components aren't flipped (needs to pass
#    --comp2 first
# --ignorepins  ignores R/C/L pin numbers when checking connectivity
#
#  be sure to specify --format pads or --format eagle
#
#Jeff Porter
#2013
#

import csv

class MissingNet(Exception):
    pass

class InvalidFormat(Exception):

    def __init__(self, line, msg):
        self.value = '%d: %s' % (line,msg)
    def __str__(self):
        return repr(self.value)

class NetID(frozenset):
    """ a frozenset that prints itself like a list of netlist nodes """
    def __repr__(self):
        return ','.join(sorted(self))


class NetIndex(dict):
    """ dictionary that can be searched by value (slowly) """
    def find_by_value(self,item):
        for key,value in self.iteritems():
            if value==item:
                return key
        raise ValueError("Item not found: %s" % item)


def other_pin(part):
    """ return X.1 <--> X.2 """
    ref,pin=part.split('.')
    pin = '%d' % (3-int(pin))
    return '.'.join((ref,pin))


  
class NetList(object):
    """ Holds a netlist and performs certain basic operations:
        compareNetList(self,another):  print out differences going from self to another
        
    """
    
    def __init__(self,fi=None,netlist_format='eagle',ignorepins=False):
        """ Creates a netlist object from a PADS ascii format netlist (.ASC).
            Three structures are built:
            parts = dict() that maps each ref des to its part type (footprint/part num)
            pins = dict() that maps each pin to its connected net
            nets = dict() that maps net name to set() of pins that make up net's connections
            index = dict() that maps a set
            """
        self.pins={}
        self.parts={}
        self.nets={}
        self.index=NetIndex({})
        if ignorepins:
            self.ignore_pins_prefix = ['R','C','L']
        else:
            self.ignore_pins_prefix = []
            
        if fi!=None:
            self.loadFile(fi,netlist_format)

    def find_onepins(self):
        count = 0
        for n in self.nets.keys():
            if len(self.nets[n])==1:
                print n
                count += 1
        if count==0:
            print "** None **"
        
        
    def indexNetList(self):
        self.index = NetIndex({})

        
    def find_nodes_on_net(self,net):
        for key,name in self.index2.iteritems():
            if name==net:
                return key
        raise MissingNet("couldn't find net name " + net)
    
    def _ignore_pins_on_this_ref(self,ref):
        for y in self.ignore_pins_prefix:
            if ref.startswith(y):
                return True
        return False

    def build_index_ignoring_certain_pins(self):
        self.index2 = NetIndex({})
        for key,name in self.index.iteritems():
            nodes = []
            for r_p in key:
                ref,pin = r_p.split('.')
                if self._ignore_pins_on_this_ref(ref):
                    nodes.append( ref )
                else:
                    nodes.append( r_p )
            self.index2[NetID(nodes)] = name

    def compareNetList2(self,newNets):
        """ perform a comparison that ignores pin numbers on R,C,Ls """
        if not isinstance(newNets,NetList):
            raise Exception("Can only compare NetList objects")
        self.build_index_ignoring_certain_pins()
        newNets.build_index_ignoring_certain_pins()
        for key,name in self.index2.iteritems():
            #print key,name
            if newNets.index2.has_key(key):
                pass
                #print self.index[name], "-->MATCH"
            else:
                print "-----"
                print name, "!!! NO MATCH"
                #print "    ",key  #NetID(key)
                try:
                    old_nodes = self.index2.find_by_value(name)
                    new_nodes = newNets.index2.find_by_value(name)
                except ValueError:
                    print "Unable to cross reference net",name
                    continue

                a = old_nodes - new_nodes
                b = new_nodes - old_nodes
                if len(b)>0:
                    print "Added by new",b
                if len(a)>0:
                    print "Missing from new",a
 
    def find_flipped_parts(self,newNets):
        """ find the R,C,Ls that have pin 1/2 swapped on newNets """
        if not isinstance(newNets,NetList):
            raise Exception("Can only compare NetList objects")
        self.build_index_ignoring_certain_pins()
        newNets.build_index_ignoring_certain_pins()
        flipped_list = []
        not_flipped = 0

        for key,name in self.index2.iteritems():
            #print key,name
            if not newNets.index2.has_key(key):
                print "Warning:  Net %s does not match" % name
                continue
            #now we know the list of nodes match except possibly for pin1/2
            #situtations
            old_nodes = self.nets[name]
            new_nodes = newNets.nets[ newNets.index2[key] ]
            for node in new_nodes:
                if node not in old_nodes:
                    if other_pin(node) in old_nodes:
                        flipped_list.append(node)
                    else:
                        print "Part %s isn't flipped but isn't right, either" % node
                else:
                    not_flipped += 1

        print "Total flipped parts = ",len(flipped_list)/2
        print "Parts not flipped = ",not_flipped/2

        flipped_list = sorted(flipped_list)

        flipped_list = [flipped_list[x] for x in range(0,len(flipped_list),2)]
        print "Flipped parts:"
        for f in flipped_list:
            print f.split('.')[0],
        print

    def find_nets_on_part(self,ref_des):
        """  returns a list of (pin,net) tuples for pins of the given
             ref_des.  Note that the pin name should be of the format
             REFDES.PIN in order for the matching to work correctly. """

        ref_des = ref_des.upper() + "."
        res = []
        for net_name,net_pins in self.nets.iteritems():
            for p in net_pins:
                if p.startswith(ref_des):
                    res.append( (p,net_name) )
        return res
            
    def compareNetList(self,newNets,ignoreNames=False):
        """ print out differences between self and a new netlist """
        if not isinstance(newNets,NetList):
            raise Exception("Can only compare NetList objects")
        verifiedChanges = set([])
        for net_pins,net_name in self.index.iteritems():
            if newNets.index.has_key(net_pins):
                if newNets.index[net_pins]==net_name: # nets match contents and name
                    continue
                else: # net contents match but name is different
                    if not ignoreNames:
                        print "Net %s name changed from %s to %s." % (net_pins,net_name,newNets.index[net_pins])
            else: # net contents do not match
                closest_new_net_name = newNets.findClosestMatch( net_pins, net_name )
                if closest_new_net_name != None:
                    # net of the same name exists, so find differences in nodes(pins) connected
                    oldset = self.nets[net_name] 
                    newset = newNets.nets[closest_new_net_name]
                    newNodes = " ".join(newset - oldset) #added pins
                    oldNodes = " ".join(oldset - newset) #removed pins
                    if newNodes != "":
                        newNodes = " added pins %s" % newNodes
                    if oldNodes != "":
                        oldNodes = " removed pins %s" % oldNodes
                    if oldNodes != "" and newNodes != "":
                        connector = " and"
                    else:
                        connector = ""
                    if closest_new_net_name==net_name:
                        name = net_name
                    else:
                        name = "%s %s/%s" % (net_pins,net_name,closest_new_net_name)
                    print "Net %s %s%s%s." % (name, newNodes,connector,oldNodes)

                    verifiedChanges.add( closest_new_net_name )
                else:
                    if len(self.nets[net_name])>1:
                        print "Net %s (%s) is not present in new netlist." % (net_pins,net_name)
                    
        #check to see if anything left in the new netlist that hasn't been checked           
        for key in newNets.index:
            if not self.index.has_key(key) and not newNets.index[key] in verifiedChanges:
                print "Net %s (%s) is in the new netlist but not the original" % (key,newNets.index[key])

    def findClosestMatch(self, pin_list, net_name):
        # if there is a matching netname...
        if self.nets.has_key( net_name ):
            return net_name   
        else:
            # look through to see which nets might match
            best_score = 0
            best_match = None
            for name,pins in self.nets.iteritems():
                #if no pins in common, bail
                c = len(pin_list & pins)
                if c==0:
                    continue
                #see if one adds nets to the other
                a = len(pin_list - pins)
                b = len(pins - pin_list)
                if (a==0 and b>0) or (b==0 and a>0):
                    return name
                #look for best match (max# of pins in common)
                if c>best_score:
                    best_score = c
                    best_match = name
            if best_score>2:
                return best_match
            else:
                return None


    def loadFile(self,fi,netlist_format):
        if netlist_format.lower()=='eagle':
            self.loadFile_Eagle(fi)
        elif netlist_format.lower()=='pads':
            self.loadFile_Pads(fi)
        else:
            raise Exception("Unknown format '%s'" % netlist_format)
    
    def loadFile_Eagle(self,fi):
        """ load the .NET netlist file from eagle """
        self.parts = {}
        self.nets = {}
        self.pins = {}
        state = 'skip_header'
        assert self.ignore_pins_prefix==None,"Not supported in Eagle yet"
        lineNum = 0
        net = None
        for txt in fi:
            lineNum +=1
            tokens=txt.split()
            if state.startswith('skip_header'):
                if len(tokens)==0:
                    continue
                if state=='skip_header':
                    if tokens[0] != 'Netlist':
                        raise InvalidFormat(lineNum, "Expected first line to be Netlist")
                    state='skip_header_1'
                elif state=='skip_header_1':
                    if tokens[0] != 'Exported':
                        raise InvalidFormat(lineNum, "Expected Exported line")
                    state = 'skip_header_2'
                elif state=='skip_header_2':
                    if tokens[0] != 'EAGLE':
                        raise InvalidFormat(lineNum, "Expected EAGLE version")
                    state = 'skip_header_3'
                elif state=='skip_header_3':
                    if tokens[0] != 'Net':
                        raise InvalidFormat(lineNum, "Expected Net")
                    state = 'find_net'
                else:
                    raise InvalidFormat("Reached illegal state")               
            else:
                if state=='find_net':
                    if len(tokens)==0:
                        continue
                    self.parts[tokens[1]]=tokens[1]
                    net = tokens[0]
                    self.nets[net] = set([tokens[1]+"."+tokens[2]])
                    state='add_pins'
                elif state=='add_pins':
                    if len(tokens)==0:
                        state='find_net'
                    else:
                        self.parts[tokens[0]]=tokens[0]
                        self.nets[net] |= set([tokens[0]+"."+tokens[1]])
            
        self.make_index()
        
    def loadFile_Pads(self,fi):
        """ Load the ASCII netlist file (parts and connections,
            constraints are ignored) """
        self.parts = {} # dict { refdes : partNumber/footprint }  optional
        self.nets = {} # dict  { netname1 : set(pin list1), ... }
        self.pins = {} # dict { pin : net } for checking if pin is on multiple nets
        state = 'findparts'
        lineNum = 0
        net = None
        for txt in fi:
            lineNum += 1
            txt = txt.strip()
            if state=='findparts':
                if txt.startswith('*PART*'):
                    state = 'readparts'
                elif txt.startswith('*NET*'):
                    state = 'readnets'
            elif state=='readparts':
                if txt.startswith('*CONNECTION*') or txt.startswith('*NET*'):
                    state = 'readnets'
                elif txt[0]=='*':
                    raise InvalidFormat(lineNum,'Unexpected keyword %s' % txt)
                else:
                    try:
                        ref,part = txt.split()
                    except ValueError:
                        raise InvalidFormat(lineNum,'Parts section needs REF PART entries')
                    self.parts[ref] = part
            elif state=='readnets':
                res = txt.split()
                if len(res)==0:
                    continue
                else:
                    if res[0][0]=='*':
                        if res[0]=='*END*' or res[0]=='*MISC*':
                            state='done'
                        elif not res[0] in ['*SIGNAL*','*SIG*'] or len(res)!=2:
                            raise InvalidFormat(lineNum,'*SIGNAL <NET> expected')
                        else:
                            net = res[1]
                            self.nets[net]=set([])
                    else:
                        #if self.ignore_pins_prefix:
                        #    res = removePinNumbers(res, self.ignore_pins_prefix)
                        if net==None:
                            raise InvalidFormat(lineNum,'Expected *SIGNAL*')
                        self.nets[net] |= set(res)
                        for r in res:
                            if self.pins.has_key(r):
                                if self.pins[r] != net:
                                    print "Warning:  Pin %s is assigned to multiple nets: %s and %s" % (
                                        r, self.pins[r], net)
                            else:
                                self.pins[r] = net
            if state=='done':
                break

        self.make_index()
        
    def make_index(self):   
        #build an index from connections to net name (helps in finding nets that get renamed)
        for net,pins in self.nets.iteritems():
            self.index[NetID(pins)] = net

    def comparePart(self, csvfile, ref_des, showNC=False):
        """ compares entries for the given ref_des with the net assignments
            in the CSV file.  The CSV file should a a 'Pin' and 'Net' column
            for each pin in REF_DES """  
        errors = 0
        ok = 0
        nc_count = 0
        for row in csv.DictReader(csvfile):
            pin = '%s.%s' % (ref_des,row['Pin'])
            net = row['Net']
            if net!='':
                if not self.nets.has_key(net):
                    print "%s: No such net %s in netlist" %(pin, net)
                    errors += 1
                elif not pin in self.nets[net]:
                    print "%s: Not connected to net %s" % (pin,net)
                    errors += 1
                else:
                    ok += 1
            elif self.pins.has_key(pin) and self.pins[pin][0]!='$':
                errors += 1
                print "%s:  Net %s assigned in netlist but not CSV." % (pin,self.pins[pin])
            else:
                nc_count +=1
                if showNC:
                    print "%s: not assigned" % pin

        print "Netlist/CSV check completed.  %d mismatches, %d verified, %d not connected" % (errors,ok, nc_count)


def removePinNumbers(list_of_pins, refs_to_ignore):
    res = []
    for x in list_of_pins:
        ref,pin = x.split('.')
        ignore = False
        for y in refs_to_ignore:
            if ref.startswith(y):
                ignore = True
                break
        if ignore:
            res.append( ref )
        else:
            res.append( x )
    return res


if __name__=='__main__':

    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option("--compare", dest="compare", 
                       default=False, action="store_true",
                       help="Compare two netlists (OLD / NEW)")
    parser.add_option("--comp2", dest="comp2", 
                       default=False, action="store_true",
                       help="Compare two netlists (OLD / NEW)")
    parser.add_option("--flipcheck", dest="flipcheck", 
                       default=False, action="store_true",
                       help="Compare for flipped parts (OLD / NEW)")
    parser.add_option("--partnets", dest="partnets",
                      default=False, action="store_true",
                      help="Display nets connected to given part (REFDES)")
    
    parser.add_option("--checkpart", dest="checkpart", 
                       default=False, action="store_true",
                       help="Check connections on a part (NET and CSV and REF)")
    parser.add_option("--showNC", dest="showNC", default=False,
                      action="store_true",
                      help="Display NC pins when checking parts against CSV")
    parser.add_option("--format", dest="format", default='pads',
                      help="Netlist format (pads or eagle)")

    parser.add_option("--ignorepins", dest="ignorepins", default=False,
                      action="store_true",
                      help="Ignore pin numbers on R, L, Cs")
    parser.add_option("--ignorenames", dest="ignorenames", default=False,
                      action="store_true",
                      help="Ignore net names during comparison")
    parser.add_option("--1pin", dest="onepin", default=False,
                      action="store_true",
                      help="Print a list of 1-pin nets")
    
    (options,args) = parser.parse_args()


    if options.compare or options.comp2 or options.flipcheck:
        if len(args)!=2:
            print "Must specify OLD and NEW netlists"
        else:
            old = NetList(open(args[0]),netlist_format=options.format,ignorepins=options.ignorepins)
            new = NetList(open(args[1]),netlist_format=options.format,ignorepins=options.ignorepins)
            if options.compare:
                old.compareNetList(new,options.ignorenames)
            elif options.comp2:
                old.compareNetList2(new)
            elif options.flipcheck:
                old.find_flipped_parts(new)
    elif options.checkpart:
        if len(args)!=3:
            print "Must specify NETLIST and CSV file and REFDES"
        else:
            net = NetList(open(args[0]))
            net.comparePart( open(args[1]), args[2], showNC=options.showNC )
    elif options.partnets:
        if len(args)!=2:
            print "Must specify NETLIST and REFDES"
        else:
            netlist = NetList(open(args[0]),netlist_format=options.format,ignorepins=options.ignorepins)
            nets = netlist.find_nets_on_part( args[1] )
            for n in nets:
                print "%-16s %s" % (n[0],n[1])
            
    if options.onepin:
        nets = NetList(open(args[0]),netlist_format=options.format,ignorepins=options.ignorepins)
        nets.find_onepins()
        
