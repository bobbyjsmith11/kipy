"""
==============
convert_net.py
==============
    :Author: Bobby Smith
    :Description:
        Convert formats between sch/layout tools

"""
import re
from kinparse import parse_netlist
import sexpdata


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
            elif elem[0].value() == 'libparts':
                print('libparts')
            elif elem[0].value() == 'libraries':
                print('libraries')
            elif elem[0].value() == 'nets':
                print('nets')
                nlst = Netlist(elem)
            objs.append(elem[0])
    return s, objs, nlst


class Netlist(object):
    """
    """
    def __init__(self, lst_sexp=None):
        self.nets = load_netlist(lst_sexp)

class Net(object):
    """
    """
    def __init__(self, lst_sexp=None, code=None, name=None, nodes=[]):
        self.code=code
        self.name=name
        self.nodes = []

class Node(object):
    """
    """
    def __init__(self, lst_sexp=None, ref=None, pin=None):
        """
        A node is a reference designator and a pin number. It is usually connected to 
        and, thus, a property of a net.
        Can instantiate with lst_sexp or directly assign ref and pin
        :Args:
            :lst_sexp (list): an s-expression list with the following format
                [Symbol('node'), [Symbol('ref'), Symbol('<ref_des (str)>')], [Symbol('pin'), <pin_num (int)>]]
            :ref (str): Reference designator (R29, U18, J5, etc)
            :pin (int): pin number
        """
        if lst_sexp == None:
            self.ref = ref
            self.pin = pin
        else:
            self.ref, self.pin = load_node(lst_sexp) 

def load_netlist(sexp_lst):
    """
    given an s-expression in the form of a list, return a net_code, net_name and list of nodes
    :Args:
        :sexp_lst (list): an s-expression list with the following format
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
    net_lst = []
    if sexp_lst[0].value() != 'nets':
        raise ValueError("expected 'nets' in first item in list. received {}".format(sexp_lst[0].value()))
    for net in sexp_lst[1:]:   # first net should start at 1
        net_lst.append(Net(net))
    
    return net_lst

def load_net(lst_sexp):
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
    code = lst_sexp[1][1]
    name = lst_sexp[2][1]
    node_lst = []
    for node in lst_sexp[3:]:   # first node should start at 3
        node_lst.append(Node(node))
    return code, name, node_lst


def load_node(lst_sexp):
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
    ref = lst_sexp[1][1].value()
    pin = lst_sexp[2][1]
    return ref, pin
        
def convert_to_pads(in_file, prt_net_separate=True):
    """
    """
    prt, net = get_pads(in_file)
    if prt_net_separate:
        prt_file = open(in_file.split(".")[0] + "_pads.PRT", "w")
        prt_file.write("*PADS-PCB*\n")
        prt_file.write("*PART*\n")
        prt_file.write(prt)
        prt_file.write("*END*")
        prt_file.close()
        net_file = open(in_file.split(".")[0] + "_pads.NET", "w")
        net_file.write("*PADS-PCB*\n")
        net_file.write("*NET*\n")
        net_file.write(net)
        net_file.write("*END*")
        net_file.close()
    else:
        net_file = open(in_file.split(".")[0] + "_pads.NET", "w")
        net_file.write("*PADS-PCB*\n")
        net_file.write("*PART*\n")
        net_file.write(prt)
        net_file.write("\n")
        net_file.write("*NET*\n")
        net_file.write(net)
        net_file.write("*END*")
        net_file.close()
        pass


def get_pads(in_file):
    """
    """
    n = parse_netlist(in_file)
    prt = get_pads_prt(n)
    net = get_pads_net(n)
    return prt, net

def get_pads_prt(nlst, remove_lib_name=True):
    """
    create a PADS PRT file
        :nlst 
        :remove_lib_name (bool): If True, remove all but the footprint name
                                 If False, leave the library reference
    """
    ret = "" 
    # ret += "*PADS-PCB*\n"
    # ret += "*PART*\n"
   
    my_dict = {}
    # write the ref_des \t footprint
    for comp in nlst.components:
        ref = comp.ref.val
        fp = comp.footprint.val
        if remove_lib_name:
            fp = fp.split(":")[-1]
        my_dict[ref] = fp
        
    sorted_keys = sort_alpha_num(my_dict.keys())
    for k in sorted_keys:
        ret += "{:<7s}{}\n".format(k, my_dict[k])
        
    # ret += "*END*\n"
    return ret 
   
def get_pads_net(nlst):
    """
    """
    ret = ""
    # ret += "*PADS-PCB*\n"
    # ret += "*NET*\n"
  
    for net in nlst.nets:
         
        if "Net-" in net.name.val:
            # it is an un-named net, use "net_" and the net number (code)
            net_name = "net_{}".format(net.code.val)
        else:
            # it is a named net, remove the dir structure to keep it clean
            net_name = net.name.val.split("/")[-1]

        ret += "*SIGNAL* {}\n".format(net_name)
        for node in net.nodes:
            ret += "{}.{} ".format(node.ref.val, node.pin.val)
        ret += "\n"

    # ret += "*END*\n"
    return ret

def sort_alpha_num(in_lst):
    """
    sort in_lst alpha-numerically and return
    """
    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
    return sorted(in_lst, key = alphanum_key)
