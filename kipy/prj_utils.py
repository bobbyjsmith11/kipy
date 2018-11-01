"""
=======================================
prj_utils.py
=======================================
:Author:    Bobby Smith
:email:     bobbyjsmith11@gmail.com
:Description:
    This module is used for packaging KiCAD projects
    so that they can be archived and shared

"""

import os
from shutil import copyfile


def archive_remap_sch_libs():
    """
    """
    pass

def copy_cache(dest_name="prj_sch.lib"):
    """
    copies the cache.lib file to lib_sch/prj_sch.lib
    """
    cache_lib = find_cache()
    create_lib_sch_dir()
    dest = "lib_sch/" + dest_name
    copyfile(cache_lib, dest)


def find_cache(mydir=None):
    """
    search the mydir and return the cache.lib file
    """
    for item in os.listdir(mydir):
        if item.endswith("cache.lib"):
            return item

def create_lib_sch_dir(lib_sch_dir="lib_sch"):
    if not os.path.exists(lib_sch_dir):
        os.makedirs(lib_sch_dir)
