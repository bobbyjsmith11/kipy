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
        :in_file (str): kicad netlist
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
