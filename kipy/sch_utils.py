"""
=======================================
sch_utils.py
=======================================
:Author:    Bobby Smith
:email:     bobbyjsmith11@gmail.com
:Description:
    This module is used for interacting with .sch files in KiCAD.

"""
from datetime import datetime

class Schematic(object):
    """
    """
    def __init__(self, fi):
        """
        Parameters
            fi (file-object or str) - file or path to file
        """
        if isinstance(fi, str):
            fi = open(fi, 'r')

        self.libs = []
        self.sheets = []
        self.components = []

        while True:
            line = fi.readline()
            if not line:
                break
            if line.startswith("EESchema"):     # parse main information
                self.version, self.time = self._parse_version(line)
            if line.startswith("LIBS"):         # parse libraries
                self.libs.extend(self._parse_libs(line))
            if line.startswith("$Descr"):
                desc = line
                while True:
                    new_line = fi.readline()
                    desc += new_line
                    if new_line.startswith("$EndDescr"):
                        break
                self.description = Description(desc)
            if line.startswith("$Comp"):
                comp_str = line
                while True:
                    new_line = fi.readline()
                    comp_str += new_line
                    if new_line.startswith("$EndComp"):
                        break
                self.components.append(Component(comp_str))

    def _parse_libs(self, line):
        """ parse a line beginning with 'LIBS'. return a list of all libs
        listed in the line
        """
        line = line.split(":")[1].split(",")
        ret_lst = []
        for item in line:
            ret_lst.append(item)
        return ret_lst

    def _parse_version(self, line):
        """ parse the line beginning with EESchema. Return the version as str
        and a datetime object if the date is included.
        """
        lin_els = line.split(" ")
        ver_idx = lin_els.index("Version") + 1
        version = lin_els[ver_idx]
        time = None 
        if "date" in lin_els:
            date_idx = lin_els.index("date") + 1
            date_lst = lin_els[date_idx].split("/")
            month = int(date_lst[0])
            day = int(date_lst[1])
            year = int(date_lst[2])
            time_idx = date_idx + 1
            time_lst = lin_els[time_idx].split(":")
            am_pm = lin_els[time_idx+1]
            if am_pm.upper() == "PM":
                hour = int(time_lst[0]) + 12
            else:
                hour = int(time_lst[0])
            minute = int(time_lst[1])
            second = int(time_lst[2])
            time = datetime(year, month, day, hour, minute, second)
        return version, time

class Sheet(object):
    """
    """
    def __init__(self):
        pass

class Component(object):
    """
    """
    def __init__(self, comp_str):
        self.comp_str = comp_str

class Description(object):
    """
    """
    def __init__(self, desc_str):
        desc_lines = desc_str.split("\n") 
        self.attr_dict = {} 
        self.size = desc_lines[0].split(" ")[1]
        self.width = desc_lines[0].split(" ")[2]
        self.height = desc_lines[0].split(" ")[3]
        for line in desc_lines[1:]:
            if "$EndDescr" in line:
                break
            if "Sheet" in line:
                self.sheet_number = line.split(" ")[1]
                self.sheet_total = line.split(" ")[2]
            elif len(line.split(" ")) == 1:
                self.title = line
            else:
                k = line.split(" ")[0]
                v = line.replace(k + " ", "").replace('"',"")
                self.attr_dict[k] = v                

def change_schematic_fp_libs(sch_file, new_lib, keep_old=True):
    """ change all of the footprint libraries in a .sch file
    and all child .sch files
    to point to a single library. Use this when preparing for distribution.
    See here: 
    https://hackaday.com/2017/05/18/kicad-best-practises-library-management/

    Parameters
        sch_file (file-object or str)
        new_lib (str) - name of new library
        keep_old (bool) - True = add _tmp to the file name of the new 
                                 file and keep the old files
                          False = overwrite the old files
            If None, sch_file is used
    """

def find_all_child_sheet_file_names(sch_file):
    """
    return a list of child sheet names in .sch file
    """
    sch_list = []
    if isinstance(sch_file, str):
        sch_file = open(sch_file, 'r')
    file_data = sch_file.readlines()
    sch_file.close()
    for i in range(len(file_data)):
        if file_data[i].startswith("$Sheet"):
            print("found a sheet")
            while True:
                i += 1
                if file_data[i].startswith("$EndSheet"):
                    print("found end of sheet")
                    break
                if file_data[i].startswith("F1 "):
                    s_line = file_data[i].split('"')
                    print(file_data[i])
                    sch_list.append(s_line[1])
    return sch_list

def change_fp_libs_schematic(root_sch_file, new_lib, keep_old=True):
    """ change all of the footprint libraries in an entire schematic
    point to a single library. Use this when preparing for distribution.
    See here: 
    https://hackaday.com/2017/05/18/kicad-best-practises-library-management/

    Parameters
        root_sch_file (file-object or str)
        new_lib (str) - name of new library
        keep_old (bool) - True = add _tmp to the file name of the new 
                                 file and keep the old files
                          False = overwrite the old files
            If None, sch_file is used
    """
    
    child_list = find_all_child_sheet_file_names(root_sch_file)
    change_fp_libs_sheet(root_sch_file, new_lib, keep_old=keep_old)
    for child_sheet in child_list:
        change_fp_libs_sheet(child_sheet, new_lib, keep_old=keep_old)


def change_fp_libs_sheet(sch_file, new_lib, keep_old=True):
    """ change all of the footprint libraries in a .sch file to
    point to a single library. Use this when preparing for distribution.
    See here: 
    https://hackaday.com/2017/05/18/kicad-best-practises-library-management/

    Parameters
        sch_file (file-object or str)
        new_lib (str) - name of new library
        keep_old (bool) - True = add _tmp to the file name of the new 
                                 file and keep the old files
                          False = overwrite the old files
            If None, sch_file is used
    """
    if isinstance(sch_file, str):
        sch_file = open(sch_file, 'r')
    file_data = sch_file.readlines()
    sch_file.close()
    for i in range(len(file_data)):
        if file_data[i].startswith("$Comp"):
            while True:
                i += 1
                if file_data[i].startswith("$EndComp"):
                    break
                if file_data[i].startswith("F 2"):
                    s_line = file_data[i].split(" ")
                    if s_line[2] != '""':
                        lib_lst = file_data[i].split('"')
                        if ":" in lib_lst[1]:
                            lib_str = lib_lst[1].split(":")[0]
                            file_data[i] = file_data[i].replace(lib_str, new_lib)
    if not keep_old:
        out_file = open(sch_file.name, 'w')
    else:
        new_name = sch_file.name.replace(".sch","_tmp") + ".sch"
        out_file = open(new_name, 'w')

    for line in file_data:
        out_file.write(line)
    out_file.close()

