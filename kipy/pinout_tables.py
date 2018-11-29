"""
==============
pinout_tables.py
==============
    :Author: Bobby Smith
    :Description:
        Utilities for reading pdfs and netlists to create pinout tables

    :Usage:

"""


from tabula import read_pdf
import xml.etree.ElementTree 
from  xml.etree.ElementTree import Element, SubElement, Comment, tostring
from dicttoxml import dicttoxml
import xml.dom.minidom as minidom
import xmltodict
import re
import csv

from . import netlist_utils

def read_pdf_tables(in_file):
    """
    :Args:
        :in_file (str): input pdf file
    :Returns:
        json of all tables found
    """
    # dj = read_pdf(in_file, pages="all", output_format="json")
    df = read_pdf(in_file, pages="all")

def read_pinout_from_pdf_txt_out(txt_file):
    """
    read the text file produced from the reading the pdf
    """
    reader = csv.DictReader(open(txt_file))
    lst = []
    for row in reader:
        print(row)
        lst.append(row)
    return lst 

def _write_pinout_xml_from_pdf_txt(in_file, out_xml, conn_file="netlist_files/fmc.xml"):
    """
    """
    lst = read_pinout_from_pdf_txt_out(in_file)
    top = Element("pinout")
    for item in lst:
        pin_name = item['FMC_A Signal Name']
        pin_number = find_pin_number(pin_name, conn_file)
        description = item['Signal Description']
        fpga_pin = item['FPGA Pin #']
        d = {
             'fpga_pin':        fpga_pin,
             'description':     description,
             'name':            pin_name,
             'number':          pin_number,
             # 'number':          item["row"],
             }
        pin_elem = SubElement(top, 'pin', d)

    rough_str = tostring(top, 'utf-8')
    reparsed = minidom.parseString(rough_str)
    xml_str = reparsed.toprettyxml(indent="    ")
    fo = open(out_xml, "w")
    fo.write(xml_str)
    fo.close()
    return xml_str

def find_pin_number(name, conn_file):
    c_dict = read_xml_pinout_attribs(conn_file)
    new_name = _parse_name(name)
        
    for k in c_dict:     # k is pin numbers
        if (c_dict[k]['name'] == name) or (c_dict[k]['name'] == new_name):
            return k
    return "TBD"
         
def _parse_name(name):
    if "HA" in name:
        prefix = "HA"
        num = name.split("[")[1].split("]")[0].zfill(2)
    elif "HB" in name:
        prefix = "HB"
        num = name.split("[")[1].split("]")[0].zfill(2)
    elif "LA" in name:
        prefix = "LA"
        num = name.split("[")[1].split("]")[0].zfill(2)
    elif "DP" in name:
        prefix = "DP"
        num = name.split("[")[1].split("]")[0]
    elif "GBTCLK" in name:
        prefix = "GBT_CLK"
        num = name.split("[")[1].split("]")[0]
    elif "_CLK" in name:
        prefix = "CLK"
        num = name.split("[")[1].split("]")[0]
    else:
        return ""
    suffix = name.split("]")[1]
    if suffix == "_CC_N":
        suffix = "_N_CC"
    elif suffix == "_CC_P":
        suffix = "_P_CC"
    # num = int(name.split("[")[1].split("]")[0])
    new_name = prefix + num + suffix
    return new_name

def read_xml_pinout_attribs(xml_file, ignore_pins=['GND','NC']):
    """
    :Returns dict:
        :keys: pin numbers
        :values: dict with all attributes of pin
    """
    pinout = {}
    # pin_lst = []
    root = xml.etree.ElementTree.parse(xml_file).getroot()
    pins = root.findall('pin')
    for pin in pins:
        pin_number = pin.attrib['number']
        if pin_number not in ignore_pins:
            if pin_number in pinout.keys():
                raise ValueError("pin {} is a duplicate".format(pin_number))
            pinout[pin_number] = pin.attrib
            # pin_lst.append(pin.attrib)
    # return pin_lst
    return pinout

def write_xml_attrib_to_elements(xml_file, out_file):
    lst = read_xml_pinout_attribs(xml_file)

def list_dict_to_xml(lst):
    """
    :Returns str:
    """
    s = '<?xml version="1.0" encoding="UTF-8" ?>\n'
    for item in lst:
        for k in item.keys():
            s += '<{}>{}</{}>\n'.format(k, item[k], k)
    return s

def get_pinout_from_netlist(ref_des, 
                            netlist_file, 
                            conn_xml,
                            output_file=None, 
                            netlist_format="pads",
                            omit_gnd=True,
                            columns=[
                                       'name',
                                       'number',
                                       'description',
                                       'net',
                                       'net_description',
                                       'logic/standard',
                                       'type',
                                       'comments',
                                    ]):
    """
    generate pinout of reference designator in given netlist
    :Args:
        :ref_des (str): reference designator for pinout
        :netlist_file (str): path to netlist file
        :conn_xml (str): path to xml file for connector
        :netlist_format (str): 
        :columns (list): list of columns to include
    Returns
        pinout as dict where the key is the pin number and the value is the netname.
        If a pin is missing, it is NO CONNECT
    """
    if netlist_format == "pads":
        n = netlist_utils.PadsNetlist(netlist_file)
        p = n.get_pinout(ref_des)
    c = read_xml_pinout_attribs(conn_xml)
    pin_list = list(set(p.keys()) | set(c.keys())) # find all of the pins from both lists
    
    pinout = {}
    for pin in pin_list:
        d= {}
        if pin in p.keys():
            d['net'] = p[pin] 
        else:
            d['net'] = "NC"
        if pin in c.keys():
            for k in c[pin].keys():
                d[k] = c[pin][k]
        else:
            d['name'] = "NC"
        pinout[pin] = d

    s = "%s" % ", ".join(columns)
    s += "\n"
    for k in sort_alpha_num(pinout.keys()):
        if (pinout[k]['name'] == 'GND') and omit_gnd:
            del pinout[k]
            pass
        else:
            dat = {}
            for col in columns:
                try:
                    dat[col] = pinout[k][col]
                except KeyError:
                    dat[col] = ""
                s += "{}, ".format(dat[col]) 
            # s += ("%s" % ", ".join(dat.values()))
            s += "\n"
   
    if output_file != None:
        fo = open(output_file, "w")
        fo.write(s)
        fo.close()
    return pinout

def map_pins_netlist_fgpa(left, right, l_name='SKIQ-X4', r_name='HTG', out_file=None):
    """
    :Args:
        :left (dict): pinout for the left side (such as netlist to the interface connector)
        :right (dict): pinout for the right side (such as the FPGA to the interface connector)
    """
    pin_list = list(set(left.keys()) | set(right.keys())) # find all of the pins from both lists
    d = {}
    for pin in pin_list:
        d[pin] = {}
        if pin in left:
            for k in list(set(left[pin].keys()) - set(['number'])):
                d[pin][l_name + '_' + k] = left[pin][k] 
        else:
                d[pin][l_name + '_name'] = None
        if pin in right:
            for k in list(set(right[pin].keys()) - set(['number'])):
                d[pin][r_name + '_' + k] = right[pin][k] 
        else:
                d[pin][r_name + '_name'] = None
    return d


def map_xml_by_pin_numbers(l_xml, r_xml, l_name='SKIQ-X4', r_name='HTG', out_xml=None):
    """
    read two xml files for pinouts to a common interface connector and map them based on
    pin number. Write to xml file if provided.
    """
    l_keys_found = False
    r_keys_found = False
    left = read_xml_pinout_attribs(l_xml)
    right = read_xml_pinout_attribs(r_xml)
    pin_list = list(set(left.keys()) | set(right.keys())) # find all of the pins from both lists
    d = {}
    # first find the key list for both left and right
    for pin in pin_list:
        if l_keys_found and r_keys_found:
            break
        if l_keys_found == False:
            l_keys = left[pin].keys()
            l_keys_found = True
        if r_keys_found == False:
            r_keys = right[pin].keys()
            r_keys_found = True

    for pin in pin_list:
        d[pin] = {}
        if pin in left:

            for k in list(set(left[pin].keys()) - set(['number'])):
                d[pin][l_name + '_' + k] = left[pin][k] 
        else:
                # d[pin][l_name + '_name'] = "NC"
            for k in list(set(l_keys) - set(['number'])):
                d[pin][l_name + '_' + k] = "NC"
        
        if pin in right:
            for k in list(set(right[pin].keys()) - set(['number'])):
                d[pin][r_name + '_' + k] = right[pin][k] 
        else:
            for k in list(set(r_keys) - set(['number'])):
                d[pin][r_name + '_' + k] = "NC"
    if out_xml != None:
        write_pinmap_to_xml(d, out_xml=out_xml)
    return d

def write_pinmap_to_xml(pinout, out_xml=None):
    """
    write a pin map to an file in xml format
    """
    ar = [] 
    for k in sort_alpha_num(pinout.keys()):
        d = pinout[k]
        d['number'] = k
        # ar.append({'pin': d})
        ar.append( d)

    # x = dicttoxml(pinout, custom_root='pin_map', attr_type=True)
    my_item_func = lambda x: 'pin'
    # x = dicttoxml(ar, custom_root='pin_map', attr_type=False)
    x = dicttoxml(ar, custom_root='pin_map', item_func=my_item_func, attr_type=False)
    reparsed = minidom.parseString(x)
    xml_str = reparsed.toprettyxml(indent="    ")
    fo = open(out_xml, "w")
    fo.write(xml_str)
    fo.close()
    return xml_str

def map_csv_by_pin_numbers(l_xml, r_xml, l_name='SKIQ-X4', r_name='HTG', out_csv=None):
    """
    read two xml files for pinouts to a common interface connector and map them based on
    pin number. Write to csv file if provided.
    """
    l_keys = []
    r_keys = []
    l_keys_found = False
    r_keys_found = False
    left = read_xml_pinout_attribs(l_xml)
    right = read_xml_pinout_attribs(r_xml)
    pin_list = list(set(left.keys()) | set(right.keys())) # find all of the pins from both lists
    d = {}
    # first find the key list for both left and right
    for pin in pin_list:
        if l_keys_found and r_keys_found:
            break
        if l_keys_found == False:
            for k in list(set(left[pin].keys()) - set(['number'])):
                l_keys.append(l_name + '_' + k)
            l_keys_found = True
        if r_keys_found == False:
            for k in list(set(right[pin].keys()) - set(['number'])):
                r_keys.append(r_name + '_' + k)
            r_keys_found = True

    for pin in pin_list:
        d[pin] = {}
        if pin in left:
            for k in list(set(left[pin].keys()) - set(['number'])):
                d[pin][l_name + '_' + k] = left[pin][k] 
        else:
                # d[pin][l_name + '_name'] = "NC"
            for k in l_keys:
                d[pin][k] = ""
        
        if pin in right:
            for k in list(set(right[pin].keys()) - set(['number'])):
                d[pin][r_name + '_' + k] = right[pin][k] 
        else:
            for k in r_keys:
                d[pin][k] = ""

    headers = []
    headers.append('pin')
    headers.extend(l_keys)
    headers.extend(r_keys)
    s = ""
    for header in headers:
        s += ("{}, ".format(header))
    s += "\n"
    for pin in sort_alpha_num(d.keys()):
        s += ("{}, ".format(pin))
        print(pin)
        for lkey in l_keys:
            s += ("{}, ".format(d[pin][lkey]))
        for rkey in r_keys:
            s += ("{}, ".format(d[pin][rkey]))
        
        s += "\n"
    print(s)
    if out_csv != None:
        fo = open(out_csv, "w")
        fo.write(s)
        fo.close()
    return d

def write_pinout_to_xml_attribs(pinout, out_xml=None):
    """
    """
    top = Element("pinout")
    for k in pinout:
        pin_elem = SubElement(top, 'pin', pinout[k])

    rough_str = tostring(top, 'utf-8')
    reparsed = minidom.parseString(rough_str)
    xml_str = reparsed.toprettyxml(indent="    ")
    if out_xml != None:
        fo = open(out_xml, "w")
        fo.write(xml_str)
        fo.close()
    return xml_str

def read_xml_pinout(xml_file, ignore_pins=['GND','NC']):
    """
    :Returns dict:
        :keys: pin numbers
        :values: dict with all attributes of pin
    """
    pinout = {}
    pinlst = []
    root = xml.etree.ElementTree.parse(xml_file).getroot()
    pins = root.findall('.pin')
    for pin in pins:
        pin_number = pin.find('number').text
        d = {}
        for item in pin:
            d[item.tag] = item.text
        pinlst.append(d)
        pinout[pin_number] = d
    return pinout

def write_pinout_to_xml(pinout, out_xml=None):
    """
    """
    ar = [] 
    for k in sort_alpha_num(pinout.keys()):
        d = pinout[k]
        d['number'] = k
        # ar.append({'pin': d})
        ar.append( d)

    # x = dicttoxml(pinout, custom_root='pin_map', attr_type=True)
    my_item_func = lambda x: 'pin'
    # x = dicttoxml(ar, custom_root='pin_map', attr_type=False)
    x = dicttoxml(ar, custom_root='pin_map', item_func=my_item_func, attr_type=False)
    reparsed = minidom.parseString(x)
    xml_pretty = reparsed.toprettyxml(indent="    ")

    if out_xml != None:
        fo = open(out_xml, "w")
        fo.write(xml_pretty)
        fo.close()
    return xml_pretty

def write_pinout_xml_from_txt(in_file, out_xml):
    """
    """
    lst = read_pinout_from_pdf_txt_out(in_file)
    xml_str = dicttoxml(lst, custom_root='pinout', attr_type=False)
    xml_dom_str = minidom.parseString(xml_str)
    xml_pretty = xml_dom_str.toprettyxml()
    fo = open(out_xml, "w")
    fo.write(xml_pretty)
    fo.close()
    return xml_pretty

def write_pinout_csv(pinout, out_csv=None):
    """
    """
    for pin in pinout:
        mykeys = pinout[pin].keys()
        break

    s = ""
    for header in mykeys:
        s += ("{}, ".format(header))
    s += "\n"
    for pin in sort_alpha_num(pinout.keys()):
        for k in pinout[pin]:
            s += ("{}, ".format(pinout[pin][k]))
        s += "\n"

    print(s)
    if out_csv != None:
        fo = open(out_csv, "w")
        fo.write(s)
        fo.close()
    # return pinout

def write_xml_pinout_csv(xml_file, out_csv=None):
    """
    """
    p = read_xml_pinout_attribs(xml_file)
   
    for pin in p:
        mykeys = p[pin].keys()
        break

    s = ""
    for header in mykeys:
        s += ("{}, ".format(header))
    s += "\n"
    for pin in sort_alpha_num(p.keys()):
        for k in p[pin]:
            s += ("{}, ".format(p[pin][k]))
        s += "\n"

    print(s)
    if out_csv != None:
        fo = open(out_csv, "w")
        fo.write(s)
        fo.close()
    return p


def sort_alpha_num(in_lst):
    """
    sort in_lst alpha-numerically and return
    """
    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
    return sorted(in_lst, key = alphanum_key)

















