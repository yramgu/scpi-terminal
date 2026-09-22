"""
# Name:        utils.py
# Purpose:     data stuctures, dictionaries, etc
#
# Author:      Yannish RAMGULAM
#
# Created:     08/2025
# Copyright:   (c) Y.Ramgulam 2025
# Licence:     <your licence>
#
#
"""
import sys
import os
# Get the absolute path to the parent directory
parent_dir = ".."
if getattr(sys, 'frozen', False):
    parent_dir = os.path.abspath(os.path.join(os.path.dirname(sys.executable), '.'))
elif __file__:
    parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(parent_dir)

#---------------------------------------------------------------------------------
#
#---------------------------------------------------------------------------------





if __name__== "__main__":
    pass
