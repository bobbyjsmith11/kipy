"""
==============
netlist_utils.py
==============
    :Author: Bobby Smith
    :Description:
        Utilities for reading and manipulating Kicad netlist files

    :Usage:

        >>> from kipy.netlist_utils import *
        >>> nl1 = PadsNetlist("MDV-777-RevD.NET")   # creates a netlist from PADS netlist file
        >>> nl2 = KicadNetlist("venom_upgrade.net") # creats a netlist from a Kicad netlist file
        >>> diff_nets(nl1, nl2, fo="diff_nets.txt", ignore_pins=True)

    :Usage to diff 2 Pads netlist files:
        >>> from kipy import netlist_utils
        >>> netlist_utils.diff_netlist_file("old_netlist.NET", "new_netlist.NET", diff_file="diff.txt")


"""
import re
import sexpdata
import operator

IGNORE_PINS = [
                '1',
                '2',
                'A',
                'C',
                'B',
                'C',
                'D',
                'E',
                'S',
                'G',
                ]

class bcolors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def load_kicad_netlist(in_file):
    """
    """
    fo = open(in_file, "r")
    s = sexpdata.load(fo)
    objs = []
    for elem in s:
        if isinstance(elem, sexpdata.Symbol):
            pass
        else:
            if elem[0].value() == 'version':
                print('version')
            elif elem[0].value() == 'design':
                print('design')
            elif elem[0].value() == 'components':
                print('components')
                cmplst = KicadListOfComponents(elem)
            elif elem[0].value() == 'libparts':
                print('libparts')
            elif elem[0].value() == 'libraries':
                print('libraries')
            elif elem[0].value() == 'nets':
                nlst = KicadListOfNets(elem)
            objs.append(elem[0])
    return s, objs, nlst, cmplst
    # return nlst, cmplst

######################################################################
#       BASE CLASSES
######################################################################

class Netlist(object):
    """
    Base class for all types of netlists.
    This object will have the following properties:
        :list_of_nets (ListOfNetsObj()):
            :ListOfNetsObj() has the following properties and methods:
                :get_dict(): 
                :nets is a list of Net():
                    :Nets(): has the following properties
                        :name (str):
                        :code (int):
                        :nodes (list of Nodes()):
                            :Nodes() has the following properties:
                                :ref (str):
                                :pin (int):
        :list_of_comps (ListOfComponentsObj()):
            :ListofComponentsObj() hsa the following properties and methods:
                :get_dict(): 
                :components is a list of Component():
                    :Component() has the following properties
                        :ref (str):
                        :value (str or float):
                        :footprint (str):
        ...
        Optionally, this object can also have other type-specific properties
    """
    def __init__(self, in_file):
        self.in_file = in_file

    def load_netlist(self, in_file):
        """
        """
        raise NotImplementedError("Cannot instantiate base class")

    def get_pads_netlist(self):
        """
        return the netlist in PADS format as str
        """
        ret = ""
        nlst = self.list_of_nets.get_dict()
        ret += "*NET*\n"
      
        for net in nlst.keys():
             
            ret += "*SIGNAL* {}\n".format(net)
            line_length = 0 
            for node in nlst[net]:
                if (line_length + len(node) + 1) > 75:
                    ret += "\n"
                    line_length = 0
                ret += "{} ".format(node )
                line_length += (len(node) + 1)
            ret += "\n"
    
        return ret

    def get_pads_component_list(self):
        """
        return the netlist in PADS format as str
        """
        ret = ""
        ret += "*PART*\n"
        my_dict = self.list_of_comps.get_dict()
        
        sorted_keys = sort_alpha_num(my_dict.keys())
        for k in sorted_keys:
            ret += "{:<7s}{}\n".format(k, my_dict[k])
        
        return ret 

    def save_pads_netlist(self, out_file=None, separate_files=False):
        """
        Save this object as a PADS netlist. If separate_file is True,
        save separate .NET and .PRT files. If False, combine into
        a single .NET file
        """
        if separate_files:
            if out_file == None:
                prt_file = open(self.in_file.split(".")[0] + "_pads.PRT", "w")
            else:
                prt_file = open(out_file + ".PRT", "w")
            prt_file.write("*PADS-PCB*\n")
            prt_file.write(self.get_pads_component_list())
            prt_file.write("*END*")
            print("PADS .PRT file: {}".format(prt_file.name))
            prt_file.close()
            if out_file == None:
                net_file = open(self.in_file.split(".")[0] + "_pads.NET", "w")
            else:
                net_file = open(out_file + ".NET", "w")
            net_file.write("*PADS-PCB*\n")
            net_file.write(self.get_pads_netlist())
            net_file.write("*END*")
            print("PADS .NET file: {}".format(net_file.name))
            net_file.close()
        else:
            if out_file == None:
                net_file = open(self.in_file.split(".")[0] + "_pads.NET", "w")
            else:
                net_file = open(out_file + ".NET", "w")
            net_file.write("*PADS-PCB*\n")
            net_file.write(self.get_pads_component_list())
            net_file.write("\n")
            net_file.write(self.get_pads_netlist())
            net_file.write("*END*")
            print("PADS .NET file: {}".format(net_file.name))
            net_file.close()

    def get_pinout(self, ref_des):
        """
        return a pinout for the given reference designator.
        :Args:
            :ref_des (str): reference designator
        :Returns:
            :dict:
                :keys:      pin number as str
                :values:    net name as str
        """
        d = {}
        my_dict = self.list_of_nets.get_dict()
        for net in my_dict:
            for node in my_dict[net]:
                if node.split(".")[0] == ref_des:
                    pin = node.split(".")[-1]
                    # print("{} : {}".format(pin, net))
                    d[pin] = net
        return d

    def get_net_from_node(self, node_name):
        """
        """
        nlst = self.list_of_nets.get_dict()
        for net in nlst.keys():
            if node_name in nlst[net]:
                return net 
        return None

    def get_nodes_from_net(self, net_name):
        return self.list_of_nets.get_dict()[net_name]

class ListOfNetsObj(object):
    """
    Object to hold the entire list of nets for the netlist and
    a method for retrieving this list in a usable dict form
    """
    def __init__(self, in_val):
        self.load_list_of_nets(in_val)

    
    def load_list_of_nets(self, in_val):
        """
        """
        raise NotImplementedError("Cannot instantiate base class")

    def get_dict(self):
        """
        return a dict for the netlist with the following format
        :keys:      net names
        :values:    list of nodes
                    :nodes: (str) as <REF>.<PIN NUMBER>
        """
        raise NotImplementedError("Cannot instantiate base class")

    def get_nodes(self):
        """
        return a list of all of the nodes
        """
        d = self.get_dict()
        nodes = []
        for k in d.keys():
            nodes.extend(d[k])
        return nodes

    def get_nets(self):
        """
        return a list of all of the net names
        """
        d = self.get_dict()
        return d.keys()
    
    def get_nodelist(self):
        node_list = {}
        nodes = self.get_nodes()
        nets = self.get_nets()
        my_dict = self.get_dict()
        for node in nodes:
            for net in nets:
                if node in my_dict[net]:
                    node_list[node] = list(set(my_dict[net]) - set([node]))
        return node_list
        
        
    def find_net_from_node(self, node):
        """
        Return the net name to which the given node is attached. 
        If it doesn't exist, return None
        """
        d = self.get_dict()         
        for k in d.keys():
            if node in d[k]:
                return k
        

class Net(object):
    """
    Object to hold the following properties of a net:
        :name (str):    the net name
        :code (num):    the net number (sometimes the same as name
        :nodes (list):  a list of Node() (see Node)
    """
    def __init__(self, in_val=None, code=None, name=None, nodes=[]):
        """
        A net has a code (or net number), a name and a list of nodes
        It is instantiated with lst_sexp or directly assign ref and pin
        :Args:
            :in_val (str or list): 
            :ref (str): Reference designator (R29, U18, J5, etc)
            :pin (int): pin number
        """
        if in_val == None:
            self.code=code
            self.name=name
            self.nodes = []
        else:
            self.load_net(in_val)
    
    def load_net(self, in_val):
        """
        """
        raise NotImplementedError("Cannot instantiate base class")

class Node(object):
    """
    Base class for a node. This object usually attached to a net which has the following properties:
        :ref (str): A reference designator
        :pin (int): pin number
    """
    def __init__(self, in_val=None, ref=None, pin=None):
        """
        A node is a reference designator and a pin number. It is usually connected to 
        and, thus, a property of a net.
        Can instantiate with lst_sexp or directly assign ref and pin
        :Args:
            :in_val (str or list): 
            :ref (str): Reference designator (R29, U18, J5, etc)
            :pin (int): pin number
        """
        if in_val == None:
            self.ref = ref
            self.pin = pin
        else:
            self.load_node(in_val) 
    
    def load_node(self, in_val):
        """
        """
        raise NotImplementedError("Cannot instantiate base class")

class ListOfComponentsObj(object):
    """
    Object to hold the entire list of components for the netlist and
    a method for retrieving this list in a usable dict form
    """
    def __init__(self, lst_sexp):
        self.components = self.load_list_of_components(lst_sexp)

    def load_list_of_components(self, in_val):
        """
        """
        raise NotImplementedError("Cannot instantiate base class")

    def get_dict(self, in_val):
        """
        """
        raise NotImplementedError("Cannot instantiate base class")

class Component(object):
    """ Object to hold a component with the following properties:
        :ref (str): reference designator (R1, U8, FL2A, etc.)
        :value (str or number): value field of component (<part number>, 8, 1uF, etc.)
        :footprint (str): name of the footprint as it exists in the library (C0603, SOT-23-6, etc.)
    """
    def __init__(self, in_val=None, ref=None, value=None, footrpint=None):
        """
        """
        if in_val == None:
            self.ref = ref
            self.value = value
            self.footprint = footprint
        else:
            self.load_component(in_val)
    
    def load_component(self, in_val):
        """
        """
        raise NotImplementedError("Cannot instantiate base class")

######################################################################
#       END OF BASE CLASSES
######################################################################

######################################################################
#       KiCAD CLASSES (inherit from BASE CLASSES)
######################################################################

class KicadNetlist(Netlist):

    def __init__(self, in_file):
        super(KicadNetlist, self).__init__(in_file)
        self.type = "kicad"
        self.load_netlist(in_file)
    
    def load_netlist(self, in_file):
        """
        """
        fo = open(in_file, "r")
        s = sexpdata.load(fo)
        objs = []
        for elem in s:
            if isinstance(elem, sexpdata.Symbol):
                pass
            else:
                if elem[0].value() == 'version':
                    print('version')
                elif elem[0].value() == 'design':
                    print('design')
                elif elem[0].value() == 'components':
                    print('components')
                    self.list_of_comps = KicadListOfComponents(elem)
                elif elem[0].value() == 'libparts':
                    print('libparts')
                elif elem[0].value() == 'libraries':
                    print('libraries')
                elif elem[0].value() == 'nets':
                    self.list_of_nets = KicadListOfNets(elem)
                objs.append(elem[0])

class KicadListOfComponents(ListOfComponentsObj):
    """
    Object to hold the entire list of components for the netlist and
    a method for retrieving this list in a usable dict form
    """
    def __init__(self, lst_sexp):
        self.load_list_of_components(lst_sexp)

    def get_dict(self, keep_lib=False):
        """
        return a dict for the component list with the following format
        :keys:      ref
        :values:    footprint

        :Args:
            :keep_lib (bool): If True, keep the library reference in the
                              footprint. If False, only use the footprint
                              name. It is for PADS export, this value
                              should be False
        """
        comps_dict = {}
        for comp in self.components:
            footprint = comp.footprint
            if not(keep_lib):
                footprint = footprint.split(":")[-1]
            comps_dict[comp.ref] = footprint
        return comps_dict
               
    def load_list_of_components(self, sexp_lst):
        """
        given an s-expression in the form of a list, return a net_code, net_name and list of nodes
        :Args:
            :sexp_lst (list): an s-expression list with the following format
        """
        self.components = []
        if sexp_lst[0].value() != 'components':
            raise ValueError("expected 'components' in first item in list. received {}".format(sexp_lst[0].value()))
        for comp in sexp_lst[1:]:
            for c in comp:
                print(c)
            try:
                self.components.append(KicadComponent(comp))
            except:
                pass # no components
    

class KicadComponent(Component):
    """ 
    Based on Component()
    """
    
    def load_component(self, lst_sexp):
        """
        given an s-expression in the form of a list, return a reference, value and footprint
        :Args:
            :lst_sexp (list): an s-expression list with the following format
                [Symbol('comp'),
                 [Symbol('ref'), Symbol('<ref>')],
                 [Symbol('value'), Symbol('<value>')],
                 [Symbol('footprint'), Symbol('<footprint>')],
                 [Symbol('libsource'),
                  [Symbol('lib'), ''],
                  [Symbol('part'), Symbol('DMMT5401')],
                  [Symbol('description'), '']],
                 [Symbol('sheetpath'),
                  [Symbol('names'), Symbol('/')],
                  [Symbol('tstamps'), Symbol('/')]],
                 [Symbol('tstamp'), Symbol('58E1538B')]]
    
        NOTE: Currently only ref, value and footprint are supported
        """
        if lst_sexp[0].value() != 'comp':
            raise ValueError("expected 'comp' in first item in list. received {}".format(lst_sexp[0]))
        if lst_sexp[1][0].value() != 'ref':
            raise ValueError("expected 'ref' in second item in list. received {}".format(lst_sexp[1][0]))
        if lst_sexp[2][0].value() != 'value':
            raise ValueError("expected 'value' in second item in list. received {}".format(lst_sexp[2][0]))
        if lst_sexp[3][0].value() != 'footprint':
            raise ValueError("expected 'footprint' in second item in list. received {}".format(lst_sexp[3][0]))
        self.ref = lst_sexp[1][1].value()
        value = lst_sexp[2][1]
        if isinstance(value, sexpdata.Symbol):
            value = value.value()
        self.value = value
        self.footprint = lst_sexp[3][1].value()


class KicadListOfNets(ListOfNetsObj):
    """
    Inherits from ListOfNetsObj 
    """
    def load_list_of_nets(self, input_value):
        """
        given an s-expression in the form of a list, return a net_code, net_name and list of nodes
        :Args:
            :in_val (list): an s-expression list with the following format
            [Symbol('nets'),
                [Symbol('net'),
                 [Symbol('code'), <code_num[0]>],
                 [Symbol('name'), '<net_name>'],
                 [Symbol('node'), [Symbol('ref'), Symbol('<ref[0]>')], [Symbol('pin'), <pin_num[0]>]],
                 [Symbol('node'), [Symbol('ref'), Symbol('<ref[1]>')], [Symbol('pin'), <pin_num[1]>]],
                    ... 
                 [Symbol('node'), [Symbol('ref'), Symbol('<ref[n]>')], [Symbol('pin'), <pin_num[n]]]],
                [Symbol('net'),
                 [Symbol('code'), <code_num[1]>],
                 [Symbol('name'), '<net_name>'],
                 [Symbol('node'), [Symbol('ref'), Symbol('<ref[0]>')], [Symbol('pin'), <pin_num[0]>]],
                 [Symbol('node'), [Symbol('ref'), Symbol('<ref[1]>')], [Symbol('pin'), <pin_num[1]>]],
                    ... 
                 [Symbol('node'), [Symbol('ref'), Symbol('<ref[n]>')], [Symbol('pin'), <pin_num[n]]]],
                ...
                [Symbol('net'),
                 [Symbol('code'), <code_num[n]>],
                 [Symbol('name'), '<net_name>'],
                 [Symbol('node'), [Symbol('ref'), Symbol('<ref[0]>')], [Symbol('pin'), <pin_num[0]>]],
                 [Symbol('node'), [Symbol('ref'), Symbol('<ref[1]>')], [Symbol('pin'), <pin_num[1]>]],
                    ... 
                 [Symbol('node'), [Symbol('ref'), Symbol('<ref[n]>')], [Symbol('pin'), <pin_num[n]]]],
        """
        self.nets = []
        if input_value[0].value() != 'nets':
            raise ValueError("expected 'nets' in first item in list. received {}".format(input_value[0].value()))
        for net in input_value[1:]:   # first net should start at 1
            self.nets.append(KicadNet(net))
        
    def get_dict(self, keep_sheets=True):
        """
        return a dict for the netlist with the following format
        :keys:      net names
        :values:    list of nodes
                    :nodes: (str) as <REF>.<PIN NUMBER>
        :Args:
            :keep_sheet (bool): If True, retain the full net name to include
                                the sheet hierarchy. If False, only use
                                the last net label. To avoid net ambiguity
                                it is recommended leave this as True.
        """
        nets_dict = {}
        
        for net in self.nets:
            if "Net-" in net.name:
                netname = "net_{}".format(net.code)
            else:
                if keep_sheets:    
                    # retain the full net name with the sheet hierarchy
                    netname = net.name
                else:
                    # remove hierarchy and use only the net label
                    netname = net.name.split("/")[-1]
            nets_dict[netname] = []
            for node in net.nodes:
                nets_dict[netname].append("{}.{}".format(node.ref, node.pin))
        return nets_dict


class KicadNet(Net):
    """
    """

    def load_net(self, lst_sexp):
        """
        given an s-expression in the form of a list, return a net_code, net_name and list of nodes
        :Args:
            :lst_sexp (list): an s-expression list with the following format
                [Symbol('net'),
                 [Symbol('code'), <code_num>],
                 [Symbol('name'), '<net_name>'],
                 [Symbol('node'), [Symbol('ref'), Symbol('<ref[0]>')], [Symbol('pin'), <pin_num[0]>]],
                 [Symbol('node'), [Symbol('ref'), Symbol('<ref[1]>')], [Symbol('pin'), <pin_num[1]>]],
                    ... 
                 [Symbol('node'), [Symbol('ref'), Symbol('<ref[n]>')], [Symbol('pin'), <pin_num[n]]]]
        """
        if lst_sexp[0].value() != 'net':
            raise ValueError("expected 'net' in first item in list. received {}".format(lst_sexp[0]))
        if lst_sexp[1][0].value() != 'code':
            raise ValueError("expected 'code' in second item in list. received {}".format(lst_sexp[1][0]))
        if lst_sexp[2][0].value() != 'name':
            raise ValueError("expected 'name' in second item in list. received {}".format(lst_sexp[2][0]))
        self.code = lst_sexp[1][1]
        name = lst_sexp[2][1]
        if isinstance(name, sexpdata.Symbol):
            name = name.value()
        self.name = name
        self.nodes = []
        for node in lst_sexp[3:]:   # first node should start at 3
            self.nodes.append(KicadNode(node))

class KicadNode(Node):
    """
    Inherits from Node()
    """
    def load_node(self, lst_sexp):
        """
        given an s-expression in the form of a list, return a reference designator and a pin
        :Args:
            :lst_sexp (list): an s-expression list with the following format
                [Symbol('node'), [Symbol('ref'), Symbol('<ref_des (str)>')], [Symbol('pin'), <pin_num (int)>]]
        """
        if lst_sexp[0].value() != 'node':
            raise ValueError("expected 'node' in first item in list. received {}".format(lst_sexp[0]))
        if lst_sexp[1][0].value() != 'ref':
            raise ValueError("expected 'ref' in second item in list. received {}".format(lst_sexp[1][0]))
        if lst_sexp[2][0].value() != 'pin':
            raise ValueError("expected 'pin' in second item in list. received {}".format(lst_sexp[2][0]))
        self.ref = lst_sexp[1][1].value()
        self.pin = lst_sexp[2][1]

######################################################################
#       END OF KiCAD CLASSES 
######################################################################


######################################################################
#       PADS CLASSES
######################################################################

class PadsNetlist(Netlist):
    """
    """
    def __init__(self, net_file, prt_file=None):
        super(PadsNetlist, self).__init__(net_file)
        self.type = "pads"
        self.load_netlist()
        if prt_file == None:
            self.load_partlist(self.in_file)
        else:
            self.load_partlist(prt_file)

    def load_netlist(self):
        nets = load_pads_netlist(self.in_file)
        self.list_of_nets = PadsListOfNets(nets)
    
    def load_partlist(self, fi):
        self.list_of_comps = PadsListOfComponents(fi) 
        # try: 
        #     self.list_of_comps = PadsListOfComponents(fi) 
        # except:
        #     self.list_of_comps = None

class PadsListOfNets(ListOfNetsObj):
    """
    Inherits from ListOfNetsObj 
    """
    def load_list_of_nets(self, in_list):
        """
        """
        self.nets = []
        for net in in_list:
            self.nets.append(PadsNet(net))
        
    def get_dict(self):
        """
        return a dict for the netlist with the following format
        :keys:      net names
        :values:    list of nodes
                    :nodes: (str) as <REF>.<PIN NUMBER>
        """
        nets_dict = {}
        
        for net in self.nets:
            netname = "{}".format(net.name)
            nets_dict[netname] = []
            for node in net.nodes:
                nets_dict[netname].append("{}.{}".format(node.ref, node.pin))
        return nets_dict

class PadsNet(Net):
    """
    Inherits from Net()
    """
    def load_net(self, in_dict):
        """
        :Args:
            :in_dict (dict): having the following keys
                :name (str): net name
                :nodes (list): list of dicts having the following keys
                    :ref (str): part reference designator
                    :pin (str): part pin number
        """
        self.name = in_dict['name']
        self.code = self.name       # PADS netlist doesn't have code
        self.nodes = []
        for node in in_dict['nodes']:
            self.nodes.append(PadsNode(node))

class PadsNode(Node):
    """
    Inherits from Node()
    """
    def load_node(self, in_dict):
        """
        :Args:
            :in_dict (dict): having the following keys
                :ref (str): part reference designator
                :pin (str): part pin number
        """
        self.ref = in_dict['ref'] 
        self.pin = in_dict['pin']

class PadsListOfComponents(ListOfComponentsObj):
    """
    Object to hold the entire list of components for the netlist and
    a method for retrieving this list in a usable dict form
    """
    def __init__(self, in_file):
        self.load_list_of_components(in_file)

    def get_dict(self):
        """
        return a dict for the component list with the following format
        :keys:      ref
        :values:    footprint
        """
        comps_dict = {}
        for comp in self.components:
            footprint = comp.footprint
            comps_dict[comp.ref] = footprint
        return comps_dict
               
    def load_list_of_components(self, in_file):
        """
        given an s-expression in the form of a list, return a net_code, net_name and list of nodes
        :Args:
            :sexp_lst (list): an s-expression list with the following format
        """
        comps = load_pads_complist(in_file)
        self.components = []
        for comp in comps:
            self.components.append(PadsComponent(comp))
    
class PadsComponent(Component):
    """ 
    Based on Component()
    """
    
    def load_component(self, in_dict):
        """
        """
        self.ref = in_dict['ref']
        value = in_dict['value']
        self.footprint = in_dict['footprint']


######################################################################
#       END OF PADS CLASSES
######################################################################

######################################################################
#       SHARED METHODS
######################################################################

def load_pads_complist(fi):
    """ 
    Take a PADS netlist file and returns a list of dicts for the 
    components. Returns None if there is no *PART* section in the file
    :Args:
        :fi (str): path to PADS netlist file
    :Returns:
        :list of dicts:
            {'ref':             <part ref des>,
             'footprint':       <part footprint>,
             'value':           <part value (same as footprint)>
    """
    fo = open(fi, "r")
    dat = fo.read()
    fo.close()
    try:
        my_lst = dat.split("*PART*")[1].split("*NET*")[0].strip().split("\n")
    except IndexError:
        print("No *PART* statement in {}".format(fo.name))
        return
    comp_dict = []
    for line in my_lst:
        line = line.strip().split()
        try:
            fp = line[1]
        except IndexError:
            fp = "NO_FOOTPRINT"
        comp_dict.append({
                    'ref':          line[0],
                    'footprint':    fp,
                    'value':        fp,
                    })
    return comp_dict

# def load_pads_netlist(fi):
#     """ 
#     """
#     fo = open(fi, "r")
#     dat = fo.read()
#     fo.close()
#     net_str = dat.replace("\n", " ").replace("\r", " ").split("*SIGNAL*")
#     # print(net_str)
#     nets = []
#     
#     for item in net_str[1:]:
#         # print(item)
#         name, nodes = parse_net(item)
#         nets.append({'name': name, 'nodes': nodes}) 
#     return nets 

def load_pads_netlist(fi):
    """ 
    """
    fo = open(fi, "r")
    s = fo.read()
    fo.close()
    net_str = s.split("*NET*")[-1].split("*END*")[0].strip()
    # net_str = s.replace("\n", " ").replace("\r", " ").split("*SIGNAL*")
    net_str = net_str.replace("\n", " ").replace("\r", " ").split("*SIGNAL*")
    nets = []
    for item in net_str[1:]:
        print(item)
        name, nodes = parse_net(item)
        nets.append({'name': name, 'nodes': nodes}) 
    return nets 

def parse_net(net_str):
    """
    """
    # split on carriage returns or whitespace
    net_str = net_str.replace("\n", " ").replace("\r", " ").split()
    name = net_str[0]
    nodes = []
    for s in net_str[1:]:
        if s == "*END*" or s == "*PART":
            break
        else:
            node = s.split(".")
            print("node: {}".format(node))
            nodes.append({'ref': node[0], 'pin': node[1]})
    return name, nodes
     

def sort_alpha_num(in_lst):
    """
    sort in_lst alpha-numerically and return
    """
    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
    return sorted(in_lst, key = alphanum_key)

def compare_partlists(nl1, nl2):
    """
    Compare the parts lists for 2 netlists.
    :Args:
        :nl1 (Netlist()): old netlist
        :nl2 (Netlist()): net netlist
    :Returns (dict):
        'additions':        list of ref designators in nl2 but not in nl1
        'subtractions':     list of ref designators in nl1 but not in nl2
        :changes':          list of dicts showing the differences 
                            between nl1 and nl2 as {'ref': <ref des>,
                                                    'old': <old footprint>,
                                                    'new': <new footprint>}
    """
    p1 = nl1.list_of_comps.get_dict()
    p2 = nl2.list_of_comps.get_dict()

    d = {}
    
    d['deletions'] = []
    d['additions'] = []
    d['changes'] = []

    for k1 in p1.keys():
        if k1 not in p2.keys():
            d['deletions'].append(k1) 
        else:
            #compare footrpints
            if p1[k1] != p2[k1]:
                # d['changes'].append((p1[k1], p2[k1]))
                d['changes'].append({
                                    'ref': k1,
                                    'old': p1[k1], 
                                    'new': p2[k1],
                                    })
    
    for k2 in p2.keys():
        if k2 not in p1.keys():
            d['additions'].append(k2) 
    
    return p1, p2, d


def compare_netlists(nl1, nl2):
    """
    Compare the parts lists for 2 netlists.
    :Args:
        :nl1 (Netlist()): old netlist
        :nl2 (Netlist()): net netlist
    :Returns (dict):
        :deletions: list of nets that are in nl1 but not nl2
        :additions: list of nets that are in nl2 but not nl1
        :name_changed: dict
            :keys:      old net name from nl1
            :values:    net net name in nl2
    """
    n1 = nl1.list_of_nets.get_dict()
    n2 = nl2.list_of_nets.get_dict()

    d = {}
    
    d['deletions'] = []
    d['additions'] = []
    d['changes'] = []

    for k1 in n1.keys():
        if k1 not in n2.keys():
            d['deletions'].append(k1) 
        else:
            #compare nodes
            pass
            # if n1[k1] != n2[k1]:
            #     d['changes'].append({
            #                         'ref': k1,
            #                         'old': p1[k1], 
            #                         'new': p2[k1],
            #                         })
    
    for k2 in n2.keys():
        if k2 not in n1.keys():
            d['additions'].append(k2) 
   
    d['matched_nets_new'] = []
    d['matched_nets_old'] = []
    d['name_changed'] = {}  # keys are nl1 net names, values are nl2 net names
   
    for k1 in n1.keys():
        for k2 in n2.keys():
            if compare_lists(n1[k1], n2[k2]):
                d['matched_nets_new'].append(k2)        # net is matched add new net name to list
                d['matched_nets_old'].append(k1)        # net is matched add new net name to list
                if k1 != k2:
                    d['name_changed'][k1] = k2

    d['unmatched_new'] = list(set(n2.keys()) - set(d['matched_nets_new']))
    d['unmatched_old'] = list(set(n1.keys()) - set(d['matched_nets_old']))
    
    return n1, n2, d


def match_nets(nl1, nl2):
    """
    Return a dict of matched nets
    """
    n1 = nl1.list_of_nets.get_dict()
    n2 = nl2.list_of_nets.get_dict()
    
    d = {}
    d['name_changed'] = {}  # keys are nl1 net names, values are nl2 net names
    d['unmatched_old'] = []
    d['unmatched_new'] = []
    for k1 in n1.keys():
        for k2 in n2.keys():
            if compare_lists(n1[k1], n2[k2]):
                d[k2] = k1
                if k1 != k2:
                    d['name_changed'][k1] = k2

    return d


def find_correlated_nets(in_net, in_netlist, thresh=0.0, ignore_pins=False):
    """
    :Args:
        :in_net (list): net, or list of nodes to look for correlation
        :in_netlist (Netlist): 
    :Returns:
        list of dict of netnames as keys and values between 0 and 1 for the 
        level of correlation
    """
    ret = []
    for k in in_netlist.keys():
        val = correlate_lists(in_net, in_netlist[k], ignore_pin_nums=ignore_pins)
        if val > thresh:
            ret.append({k: val})
    return ret


def find_occurences_in_list_of_dicts(list_dict, in_val):
    """
    return number of occurences of value in dict
    """
    n = 0
    for item in list_dict:
        for k in item.keys():
            if item[k] == in_val:
                n += 1
    return n

def correlate_lists(lst1, lst2, ignore_pin_nums=False):
    """
    """
    if ignore_pin_nums:
        for k in range(len(lst1)):
            lst1[k] = lst1[k].split(".")[0]
            # try:
            #     pin_num =  lst1[k].split(".")[1]
            # except:
            #     pin_num = ''
            # if pin_num in IGNORE_PINS:
            #     lst1[k] = lst1[k].split(".")[0]

        for k in range(len(lst2)):
            lst2[k] = lst2[k].split(".")[0]
            # try:
            #     pin_num =  lst2[k].split(".")[1]
            # except:
            #     pin_num = ''
            # if pin_num in IGNORE_PINS:
            #     lst2[k] = lst2[k].split(".")[0]

    num_in_common = len(set(lst1) & set(lst2))
    num_not_in_common = len(set(lst2) - set(lst1)) + len(set(lst1) - set(lst2))

    return float(num_in_common)/(num_in_common + num_not_in_common) 


def compare_lists(net1, net2):
    """
    a net is a list of nodes
    """
    if set(net1) == set(net2):
        return True
    else:
        return False


def correlate_nets(nl1, nl2, fo="corr_nets.txt"):
    """
    Return a dict of matched nets
    """
    fo = open(fo, "w")
    n1 = nl1.list_of_nets.get_dict()
    n2 = nl2.list_of_nets.get_dict()
    
    # make a separate list containing all the net names
    # in each netlist
    n1_keys = n1.keys()
    n2_keys = n2.keys()
  
    new_nets = []
    n_map = [] 
    un_mapped = []
    old_names = [] 
    new_to_old = {}
    old_to_new = {}
    d = {}
    ret_dict = {
                'unchanged': [],
                'changed': [],
                'deleted': [],
                'added': [],
                'name_changed': [],
                }
    for k2 in n2.keys():
        # gets a list of dicts of net names and the correlation value (0-1)
        # between the new net name (k2) and the old netlist n1 
        d[k2] = find_correlated_nets(n2[k2], n1)

        if not d[k2]:
            # no correlations. add this net name (k2) to the net_nets list
            new_nets.append(k2)
            n_map.append((None, k2))
            new_to_old[k2] = None
            ret_dict['added'].append(k2)
        elif len(d[k2]) == 1:
            # there is only one correlated net in the old netlist (n1) with
            # the new net name (k2) add it correlates exactly
            # 
            n_map.append((k2, d[k2][0].keys()[0]))
            new_to_old[k2] = d[k2][0].keys()[0]
            old_to_new[d[k2][0].keys()[0]] = k2
            ret_dict['unchanged'].append(k2)
            if k2 != d[k2][0].keys()[0]:
                ret_dict['name_changed'].append(k2)
        else:
            # there is more than one correlation. need to find out 
            # if there is only one maximum correlation. if so
            # add it to new_to_old
            # un_mapped[k2] = d[k2]
            
            # print(d[k2]) 
            ret_dict['changed'].append(k2)
            # print(k2)
            max_val = max(d[k2])    # find max value in the list of dicts
            # max_key = max(d.items(), key=operator.itemgetter(1))[0]
            # max_key = max(d, key=d.get)
            old_key = max_key
            old_names.append(old_key)
            if find_occurences_in_list_of_dicts(d[k2], max_key) > 1:
                un_mapped.append(d[k2])
            else: 
                # n_map.append((k2, d[k2][0].keys()[0]))
                n_map.append((k2, max_key))
                # new_to_old[k2] = d[k2][0].keys()[0]
                new_to_old[k2] = max_key
                # old_to_new[d[k2][0].keys()[0]] = k2
                old_to_new[max_key] = k2
                # if k2 != d[k2][0].keys()[0]:
                if k2 != max_key:
                    ret_dict['name_changed'].append(k2)
   
    for k in n1.keys():
        if k not in old_to_new.keys():
            old_to_new[k] = None
            ret_dict['deleted'].append(k2)
        

    # return d, n_map, un_mapped, new_nets, new_to_old, old_to_new
    return ret_dict, new_to_old, old_to_new

def compare_nodes(nl1, nl2):
    """
    """
    nodes1 = nl1.list_of_nets.get_nodes()
    nodes2 = nl2.list_of_nets.get_nodes()
  
    n1 = nl1.list_of_nets.get_dict()
    n2 = nl2.list_of_nets.get_dict()


    d = {}
    d['added'] = sort_alpha_num(list(set(nodes2) - set(nodes1)))
    d['deleted'] = sort_alpha_num(list(set(nodes1) - set(nodes2)))
    d['moved'] = [] 
    d['unchanged'] = []
   

    netcat, new_to_old, old_to_new = correlate_nets(nl1, nl2)

    # get all nets that have some type of change
    # deleted, added, changed or name_changed
    nl_changes = list( set(netcat['changed']) |\
                       set(netcat['name_changed']) |\
                       set(netcat['added']) |\
                       set(netcat['deleted']) )
    
    nl_changes = sort_alpha_num(nl_changes)
    master_nodes = []
    for net in nl_changes:
        # print(net)
        try:
            master_nodes.extend(n1[net])
        except KeyError:
            pass
        try:
            master_nodes.extend(n2[net])
        except KeyError:
            pass
  
    node_dict = {}
    master_nodes = list(set(master_nodes))   # remove all duplicates
    for node in master_nodes:
        old_net = nl1.list_of_nets.find_net_from_node(node)
        new_net = nl2.list_of_nets.find_net_from_node(node)
        if old_net and new_net:         # node is in both sets. check if moved
            if new_to_old[new_net] == old_net:   # it's the same net, just the name is changed
                d['unchanged'].append(node)
            else:       # node is in both sets, but is moved
                d['moved'].append(node)
                node_dict[node] = {'status': 'moved',
                                   'from': old_net,
                                   'to': new_net}
        if old_net and not new_net:     # node was deleted
            d['deleted'].append(node)
            node_dict[node] = {'status': 'deleted'}
        if not old_net and new_net:     # node was added
            d['added'].append(node)
            node_dict[node] = {'status': 'added'}

    return netcat, node_dict


def find_net_from_node(node, in_dict, in_keys):
    """
    Return the net name to which the given node is attached. 
    If it doesn't exist, return None
    """
    for k in in_keys:
        if node in in_dict[k]:
            return k
        
def diff_netlist_files(file1, file2, diff_file="diff_net.txt", ignore_pins=False):
    """
    Evaluate the netlists from both files and print the differences. Also,
    write to a diff_file if provided.
    """
    fname1 = file1.split("/")[-1]
    fname2 = file2.split("/")[-1]
    
    nlst1 = PadsNetlist(file1)
    nlst2 = PadsNetlist(file2)

    if diff_file != None:
        fo = open(diff_file, "w")
    else:
        fo = None
    
    col_width = 35 

    line = ""
    line += ("{:<{w}}|{:<{w}}\n".format("OLD: {}".format(fname1), "NEW: {}".format(fname2), w=col_width))
    line += ("{:=<{w}}|{:=<{w}}\n".format("", "", w=col_width))
    print(line),
    if fo != None:
        fo.write(line)

    # PARTS DIFF
    p1, p2, d = compare_partlists(nlst1, nlst2) 
    output_parts_diff(p1, p2, d, fo=fo, col_width=col_width)

    n1 = nlst1.list_of_nets.get_dict() 
    n2 = nlst2.list_of_nets.get_dict() 
    # nets_changed, nodes_changed = compare_nodes(nlst1, nlst2)
    # output_nets_diff(nlst1, nlst2, fo=fo, col_width=col_width)
    write_nets_diff(nlst1, nlst2, fo=fo, col_width=col_width, ignore_pins=ignore_pins)

    if diff_file != None:
        fo.close()
    
    return

def output_parts_diff(p1, p2, d, fo=None, col_width=50):
    """
    :Args:
        :p1 (list of parts):
        :p2 (list of parts):
        :d (dict):
    """
    ref_w = 8
    pn_w = col_width - ref_w
    # DELETIONS
    line = ""
    line += ("{:<{w}}|{:<{w}}\n".format("PART DELETIONS", "", w=col_width))
    line += ("{:-<{w}}|{:-<{w}}\n".format("", "", w=col_width)) 
    
    for k in d['deletions']:
        line += ("{:<{ref_w}}{:<{pn_w}}|\n".format(k +":", p1[k], ref_w=ref_w, pn_w=pn_w))

    # ADDITIONS
    line += ("{:-<{w}}|{:-<{w}}\n".format("", "", w=col_width)) 
    line += ("{:<{w}}|{:<{w}}\n".format("", "PART ADDITIONS", w=col_width))
    line += ("{:-<{w}}|{:-<{w}}\n".format("", "", w=col_width))
            
    
    for k in d['additions']:
        line += ("{:<{w}}|{:<{ref_w}}{:<{pn_w}}\n".format("", k, p2[k], w=col_width, ref_w=ref_w, pn_w=pn_w))
        # line += ("{:<{w}}|{:<{w}}\n".format(k, p2[k], w=col_width))
    
    # CHANGES
    line += ("{:-<{w}}|{:-<{w}}\n".format("", "", w=col_width))
    line += ("{:<{w}}|{:<{w}}\n".format("FOOTPRINT CHANGES", "", w=col_width))
    line += ("{:-<{w}}|{:-<{w}}\n".format("", "", w=col_width))
            
    for k in d['changes']:
        ref = k['ref']
        line += ("{:<{ref_w}}{:<{pn_w}}|{:<{ref_w}}{:<{pn_w}}\n".format(ref, p1[ref], ref, p2[ref], ref_w=ref_w, pn_w=pn_w))
    print(line),
    if fo != None:
        fo.write(line)

def output_nets_diff(nl1, nl2, fo=None, col_width=50):
    """
    """
    nodes1 = nl1.list_of_nets.get_nodes()
    nodes2 = nl2.list_of_nets.get_nodes()
  
    nets1 = nl1.list_of_nets.get_dict()
    nets2 = nl2.list_of_nets.get_dict()

    nodes_d = {}
    nodes_d['added'] = sort_alpha_num(list(set(nodes2) - set(nodes1)))
    nodes_d['deleted'] = sort_alpha_num(list(set(nodes1) - set(nodes2)))
    nodes_d['changed'] = [] 
    nodes_d['unchanged'] = []
   
    nets_d = {}
    nets_d['added'] = sort_alpha_num(list(set(nets2) - set(nets1)))
    nets_d['deleted'] = sort_alpha_num(list(set(nets1) - set(nets2)))
    nets_d['changed'] = [] 
    nets_d['unchanged'] = []
   
    # common_nets = list(set(nets2) - set(nets_d['added']))
    # for net in common_nets:
    #     if nets1[net] != nets2[net]:
    #         nets_d['changed'].append(net)
    #     else:
    #         nets_d['unchanged'].append(net)
    
    line = ""
    line += ("{:=<{w}}|{:=<{w}}\n".format("", "", w=col_width))
    line += ("{:<{w}}|{:<{w}}\n".format("NETLIST CHANGES", "NETLIST CHANGES", w=col_width))
    line += ("{:=<{w}}|{:=<{w}}\n".format("", "", w=col_width))

    master_nets = sort_alpha_num(list(set(nets1.keys()) | set(nets2.keys())))
    line += ("{:-<{w}}|{:-<{w}}\n".format("", "", w=col_width)) 
    line += ("{:<{w}}|{:<{w}}\n".format("OLD", "NEW", w=col_width))
    line += ("{:-<{w}}|{:-<{w}}\n".format("", "", w=col_width)) 
   
    for item in master_nets:
        if item in nets_d['deleted']:   # net name deleted
            line += ("{:<{w}}|{:<{w}}\n".format("*" + item + "* --> DELETED", "",  w=col_width))
            for node in nets1[item]:
                line += ("{:<{w}}|{:<{w}}\n".format("  " + node + " -", "",  w=col_width))
                
        elif item in nets_d['added']:   # new net name
            line += ("{:<{w}}|{:<{w}}\n".format("", "*" + item + "* --> NEW NET", w=col_width))
            for node in nets2[item]:
                line += ("{:<{w}}|{:<{w}}\n".format("", "  " + node + " +",  w=col_width))
        
        else:   # net name is common to both sets
            if set(nets1[item]) != set(nets2[item]):  # node list is different
                line += ("{:<{w}}|{:<{w}}\n".format("*" + item + "* --> CHANGED" ,"*" + item + "* --> CHANGED",  w=col_width))
                lst_node = sort_alpha_num(list(set(nets1[item]) | set(nets2[item])))
                for node in lst_node:
                    if node not in nets2[item]:     # deleted node
                        line += ("{:<{w}}|{:<{w}}\n".format("  " + node + " -", "",  w=col_width))
                    elif node not in nets1[item]:   # added node
                        line += ("{:<{w}}|{:<{w}}\n".format("", "  " + node + " +",  w=col_width))
                    else:
                        pass
        
    print(line),
    if fo != None:
        fo.write(line)

def get_correlated_nets(list_of_nodes, nlst, keys_to_use=None, ignore_pins=False):
    """
    :Args:
        :in_net (list): net, or list of nodes to look for correlation
        :in_netlist (Netlist): 
    :Returns:
        list of dict of netnames as keys and values between 0 and 1 for the 
        level of correlation
    """
    ret = []
    nets = nlst.list_of_nets.get_dict()
    if keys_to_use == None:
        compare_keys = nets.keys()
    else:
        compare_keys = keys_to_use
    for net in compare_keys:
        val = calc_node_correlation(list_of_nodes, nets[net], ignore_pins=ignore_pins)
        if val > 0.0:
            ret.append({net: val})
    return ret

def get_most_correlated_net(nets_corr):
    """
    :Args:
        :nets_corr (list of dicts): each dict in the list is a single key value pair
                                    where the key is the net name and the value is
                                    the correlation value
    :Returns:
        dict where the key is the net name and the value 
        is the correlation value
    """
    lst = []
    for i in range(len(nets_corr)):
        lst.append(list(nets_corr[i].values())[0])
    max_idx = lst.index(max(lst))
    d = {}
    d['name'] = list(nets_corr[max_idx].keys())[0] 
    d['correlation'] = nets_corr[max_idx][d['name']]
    return d

def calc_node_correlation(node1, node2, ignore_pins=False):
    """
    :Args:
        :node1 (list of pins):
        "node2 (list of pins):
    """
    new_node1 = node1.copy()
    new_node2 = node2.copy()
    if ignore_pins:
        for k in range(len(new_node1)):
            new_node1[k] = new_node1[k].split(".")[0]
        for k in range(len(new_node2)):
            new_node2[k] = new_node2[k].split(".")[0]
    num_in_common = len(set(new_node1) & set(new_node2))
    num_not_in_common = len(set(new_node2) - set(new_node1)) + len(set(new_node1) - set(new_node2))
    val = float(num_in_common)/(num_in_common + num_not_in_common)
    return val

def map_nets(nl1, nl2, ignore_pins=True):
    """
    """
    n1 = nl1.list_of_nets.get_dict()
    n2 = nl2.list_of_nets.get_dict()
    
    # make a separate list containing all the net names
    # in each netlist
    n1_keys = list(n1.keys())
    n2_keys = list(n2.keys())
    d = {} 
    ret = []
    
    while len(n2_keys) > 0:
        B_NAME = n2_keys.pop(0)    # need to remove from n2_keys so there are no duplicates
        # print("B_NAME: {}".format(B_NAME)) 
        # gets a list of dicts of net names and the correlation value (0-1)
        # between the new net name (k2) and the old netlist n1 
        corr_nets = get_correlated_nets(n2[B_NAME], nl1, keys_to_use=n1_keys, ignore_pins=ignore_pins)
        if corr_nets == []:
            # no correlations. add this net name (k2) to the new_nets list
            ret.append(
                        {
                         'TYPE':                'NEW',
                         'A_NAME':              '',
                         'A_NODES':             [],
                         'B_NAME':              B_NAME,
                         'B_NODES':             n2[B_NAME], 
                         'CORRELATION':         0,
                         'DELETED_FROM_A':      [],
                         'ADDED_TO_B':          n2[B_NAME],
                         }
                       )
        else:
            best_net = get_most_correlated_net(corr_nets)
            if best_net['correlation'] == 1.0:
                net_type = 'SAME'
            else:
                net_type = 'CHANGED'
            A_NAME = n1_keys.pop(n1_keys.index(best_net['name']))  
            A_NODES = n1[A_NAME]
            B_NODES = n2[B_NAME]
            A_DELETED = list(set(A_NODES) - set(B_NODES))
            B_ADDED = list(set(B_NODES) - set(A_NODES))
            ret.append(
                        {
                         'TYPE':                net_type,
                         'A_NAME':              A_NAME,
                         'A_NODES':             A_NODES,
                         'B_NAME':              B_NAME,
                         'B_NODES':             n2[B_NAME], 
                         'CORRELATION':         best_net['correlation'],
                         'DELETED_FROM_A':      A_DELETED,
                         'ADDED_TO_B':          B_ADDED,
                         }
                       )
    
    # remaining keys in n1_keys are deleted nets
    for k1 in n1_keys:
        ret.append(
                    {
                     'TYPE':                'DELETED',
                     'A_NAME':              k1,
                     'A_NODES':             n1[k1],
                     'B_NAME':              '',
                     'B_NODES':             [],
                     'CORRELATION':         0,
                     'DELETED_FROM_A':      n1[k1],
                     'ADDED_TO_B':          [],
                     }
                   )

    return ret

def correlate_nets_based_on_nodes(nl1, nl2, ignore_pins=False):
    """
    Return a dict of matched nets
    :Args:
        :nl1 (Netlist): old netlist
        :nl2 (Netlist): new netlist
    :Returns:
        list of dicts with the following keys:
            :old_name: str net name in nl1
            :new_name: str 1377                         
            :old_nodes: list of str nodes on the old net
            :net_nodes: list of str nodes on the new net
            :type: str
    """
    n1 = nl1.list_of_nets.get_dict()
    n2 = nl2.list_of_nets.get_dict()
    
    # make a separate list containing all the net names
    # in each netlist
    n1_keys = list(n1.keys())
    n2_keys = list(n2.keys())
    d = {} 
    ret = []
    for k in range(len(n2_keys)):
        # print("k: {}".format(k))
        B_NAME = n2_keys.pop(k)    # need to remove from n2_keys so there are no duplicates
        # print("B_NAME: {}".format(B_NAME)) 
        # gets a list of dicts of net names and the correlation value (0-1)
        # between the new net name (k2) and the old netlist n1 
        corr_nets = get_correlated_nets(n2[B_NAME], nl1, ignore_pins=ignore_pins)
        if corr_nets == []:
            # no correlations. add this net name (k2) to the new_nets list
            ret.append(
                        {
                         'A_NAME':              '',
                         'A_NODES':             [],
                         'B_NAME':              B_NAME,
                         'B_NODES':             n2[B_NAME], 
                         'CORRELATION':         0,
                         'DELETED_FROM_A':      [],
                         'ADDED_TO_B':          n2[B_NAME],
                         }
                       )
        else:
            best_net = get_most_correlated_net(corr_nets)

            A_NAME = n1_keys.pop(n1_keys.index(best_net['name']))  
            A_NODES = n1[A_NAME]
            B_NODES = n2[B_NAME]
            A_DELETED = list(set(A_NODES) - set(B_NODES))
            B_ADDED = list(set(B_NODES) - set(A_NODES))
            ret.append(
                        {
                         'A_NAME':              A_NAME,
                         'A_NODES':             A_NODES,
                         'B_NAME':              B_NAME,
                         'B_NODES':             n2[B_NAME], 
                         'CORRELATION':         best_net['correlation'],
                         'DELETED_FROM_A':      A_DELETED,
                         'ADDED_TO_B':          B_ADDED,
                         }
                       )

    # remaining keys in n1_keys are deleted nets
    for k1 in n1_keys:
        ret.append(
                    {
                     'A_NAME':              k1,
                     'A_NODES':             n1[k1],
                     'B_NAME':              '',
                     'B_NODES':             [],
                     'CORRELATION':         0,
                     'DELETED_FROM_A':      n1[k1],
                     'ADDED_TO_B':          [],
                     }
                   )

    return ret

def diff_nets(nl1, nl2, fo=None, col_width=50, ignore_pins=False):
    """
    """

    ret = map_nets(nl1, nl2, ignore_pins=ignore_pins)

    nets1 = nl1.list_of_nets.get_dict()
    nets2 = nl2.list_of_nets.get_dict()

    same = []
    deleted = []
    added = []
    changed = []
    for r in ret:
        if r['TYPE'] == 'DELETED':
            deleted.append(r)
        elif r['TYPE'] == 'SAME':
            same.append(r)
        elif r['TYPE'] == 'CHANGED':
            changed.append(r)
        elif r['TYPE'] == 'NEW':
            added.append(r)
        else:
            raise Exception("no type for net {}".format(r))

    line = ""
    line += ("{:=<{w}}|{:=<{w}}\n".format("", "", w=col_width))
    line += ("{:<{w}}|{:<{w}}\n".format("NETLIST CHANGES", "NETLIST CHANGES", w=col_width))
    line += ("{:=<{w}}|{:=<{w}}\n".format("", "", w=col_width))

    master_nets = sort_alpha_num(list(set(nets1.keys()) | set(nets2.keys())))
    line += ("{:-<{w}}|{:-<{w}}\n".format("", "", w=col_width)) 
    line += ("{:<{w}}|{:<{w}}\n".format("OLD", "NEW", w=col_width))
    line += ("{:-<{w}}|{:-<{w}}\n".format("", "", w=col_width)) 
 
    for item in changed:
        line += ("{:<{w}}|{:<{w}}\n".format("*" + item['A_NAME'] + "* --> CHANGED" ,"*" + item['B_NAME'] + "* --> CHANGED",  w=col_width))
        old_nodes = item['A_NODES']
        new_nodes = item['B_NODES']
        all_nodes = list(set(old_nodes).union(new_nodes))
        nodes_deleted = list(set(old_nodes) - set(new_nodes))
        nodes_added = list(set(new_nodes) - set(old_nodes))
        for node in all_nodes:
            if node in nodes_deleted:
                node = node + "(-)"
                line += ("{:<{w}}|{:<{w}}\n".format("    " + node , "",  w=col_width))
            elif node in nodes_added:
                node = node + "(+)"
                line += ("{:<{w}}|{:<{w}}\n".format("", "    " + node ,  w=col_width))
            else:
                line += ("{:<{w}}|{:<{w}}\n".format("    " + node, "    " + node ,  w=col_width))

    line += ("{:=<{w}}|{:=<{w}}\n".format("", "", w=col_width))
    line += ("{:<{w}}|{:<{w}}\n".format("NETLIST DELETIONS", "", w=col_width))
    line += ("{:=<{w}}|{:=<{w}}\n".format("", "", w=col_width))
    for item in deleted:
        line += ("{:<{w}}|{:<{w}}\n".format("*" + item['A_NAME'] + "* --> DELETED", "",  w=col_width))
        old_nodes = item['A_NAME']
        for node in old_nodes:
            node = node + "(-)"
            line += ("{:<{w}}|{:<{w}}\n".format("    " + node, "",  w=col_width))

    line += ("{:=<{w}}|{:=<{w}}\n".format("", "", w=col_width))
    line += ("{:<{w}}|{:<{w}}\n".format("", "NETLIST ADDITIONS", w=col_width))
    line += ("{:=<{w}}|{:=<{w}}\n".format("", "", w=col_width))
    for item in added:
        line += ("{:<{w}}|{:<{w}}\n".format("", "*" + item['B_NAME'] + "* --> NEW NET", w=col_width))
        new_nodes = item['B_NODES']
        for node in new_nodes:
            node = node + "(+)"
            line += ("{:<{w}}|{:<{w}}\n".format("" , "    " + node,  w=col_width))

    line += ("{:=<{w}}|{:=<{w}}\n".format("", "", w=col_width))
    line += ("{:<{w}}|{:<{w}}\n".format("SAME NETS", "SAME NETS", w=col_width))
    line += ("{:=<{w}}|{:=<{w}}\n".format("", "", w=col_width))
    
    for item in same:
        line += ("{:<{w}}|{:<{w}}\n".format("*" + item['A_NAME'] + "* --> CHANGED" ,"*" + item['B_NAME'] + "* --> CHANGED",  w=col_width))
        old_nodes = item['A_NODES']
        new_nodes = item['B_NODES']
        all_nodes = list(set(old_nodes).union(new_nodes))
        nodes_deleted = list(set(old_nodes) - set(new_nodes))
        nodes_added = list(set(new_nodes) - set(old_nodes))
        for node in all_nodes:
            if node in nodes_deleted:
                node = node + "(-)"
                line += ("{:<{w}}|{:<{w}}\n".format("    " + node , "",  w=col_width))
            elif node in nodes_added:
                node = node + "(+)"
                line += ("{:<{w}}|{:<{w}}\n".format("", "    " + node ,  w=col_width))
            else:
                line += ("{:<{w}}|{:<{w}}\n".format("    " + node, "    " + node ,  w=col_width))

    print(line),
    if fo != None:
        fo = open(fo, "w")
        fo.write(line)
    return added

def quick_get_netlists(f1, f2):
    """
    """
    nl1 = PadsNetlist("MDV-777-RevD.NET")
    nl2 = KicadNetlist("venom_upgrade.net")
    return nl1, nl2



if __name__ == '__main__':

    pass

