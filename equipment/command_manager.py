"""
#------------------------------------------------------------------------------
# Name:        command_manager
# Purpose:     manage commend sending/receiving
#
#
# Author:      Yannish RAMGULAM
#
# Created:     08/2025
# Copyright:   (c) Y.Ramgulam 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------
"""

#!usr/bin/env python

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import os, sys
from time import sleep
from datetime import datetime
from queue import Queue

# Get the absolute path to the parent directory
parent_dir = ".."
if getattr(sys, 'frozen', False):
    parent_dir = os.path.abspath(os.path.join(os.path.dirname(sys.executable), '.'))
elif __file__:
    parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(parent_dir)


from PyQt6.QtCore import  QThread, pyqtSignal, Qt, QObject, pyqtSlot
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QColor, QKeySequence, QShortcut

try:
    from log.class_logging import log
except ModuleNotFoundError:
    import logging
    log = logging.getLogger(__name__)
    log.warning("Imported local logger")

from equipment.eqpt import Eqpt

#--------------------------------------------------------------------------------------------
#
#--------------------------------------------------------------------------------------------

class CommandManager(QObject, Eqpt):
    """"""

    finished_signal = pyqtSignal()
    data_signal     = pyqtSignal(object)
    status_signal   = pyqtSignal(str)

    def __init__(self, gui=None):

       super().__init__()

       self.gui=gui
       self.command_queue = Queue()
       self.connect_signals()

       self.macro = None

       log.info("Command Manager service started")

    def run(self):
        """
        main run function
        """
        while True:
            while not self.command_queue.empty():
                command = self.command_queue.get()
                self.execute_command(command=command)
            sleep(0.1)
        self.finished_signal.emit()

    def connect_signals(self):
        """
        connect signals and slots
        """
        self.gui.btn_connect.clicked.connect(lambda: self.connect_instrument(ip=self.gui.txt_ip.text(), subinstrument=self.gui.sbx_subinstr.value()))
        self.gui.btn_send.clicked.connect(self.send_single)
        self.gui.macro_execute.clicked.connect(self.execute_macro)
        self.gui.macro_add.clicked.connect(self.add_macro)
        self.gui.macro_remove.clicked.connect(self.delete_macro)
        for id, btn in self.gui.custom_buttons.items():
            btn.clicked.connect(self.execute_shortcut)

    def connect_instrument(self, ip, subinstrument):
        """
        connect test instrument

        Parameters  :
                        ip: str
                            ip address
                        subinstrument: int
                            for boxes with subtinstruments such as EXM

        Returns     :
                        None
        """

        # open the record log
        log_enabled = "Disabled"
        if self.gui.chk_record.checkState()==Qt.CheckState.Checked:
            self.gui.scpi_record = open(f"{self.gui.path}\\log\\{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_scpi_record.txt", "w", encoding="utf-8")
            log_enabled = "Enabled"
        # attempt connection
        self.data_signal.emit({"message_type":"out", "message":f"Connecting Instrument with ip: {ip}"})
        self.data_signal.emit({"message_type":"out", "message":f"SCPI record log: {log_enabled}"})
        if super().connect_instrument(ip, subinstrument) == 0:
            idn = self.idn()
            self.status_signal.emit("Connection success")
            self.data_signal.emit({"message_type":"connection", "message":idn})
            self.data_signal.emit({"message_type":"in", "message":f"Instrument connected: {idn}"})
        else:
            self.status_signal.emit("Connection failed")
            self.data_signal.emit({"message_type":"connection", "message":"CONNECTION FAILED, CHECK LOG"})
            self.data_signal.emit({"message_type":"err", "message":"CONNECTION FAILED, CHECK LOG"})

    def send_single(self, target="visa"):
        """
        send single command
        """
        if self.connected is True:
            command = self.gui.txt_command.text()
            self.command_queue.put(command)
            #self.execute_command(target=target, command=command)
        else:
            self.gui.display_error("Instrument not connected")

    def execute_command(self, target="visa", command=None, read=True):
        """
        send a command
        """
        if "pause" in command.lower():
            try:
                pause = int(command.split("=")[1])
                self.data_signal.emit({"message_type": "pause", "message": f"Pause {pause}s\n"})
                sleep(pause)
            except (TypeError, ValueError, IndexError) as e:
                self.data_signal.emit({"message_type": "err", "message": "Invalid pause: " + str(e)})
        else:
            self.data_signal.emit({"message_type":"out", "message":command})
            res = self.send_command(command, read=read)
            if str(res).startswith("tool_error"):
                self.data_signal.emit({"message_type":"err", "message":res})
            else:
                self.data_signal.emit({"message_type":"in", "message":res})

    def execute_macro(self, target="visa"):
        """
        Execute a macro

        Parameters  :
                        target: str
                            http | visa
                        macro: list
                            list of commands to send

        Returns     : None
        """

        macro = []

        if self.connected is True:
            # build the array
            for row in range(self.gui.tbl_macros.rowCount()):
                    command_name = self.gui.tbl_macros.item(row, 0).text()
                    try:
                        command_args = self.gui.tbl_macros.item(row, 1).text()
                    except AttributeError:
                        command_args = ""
                    if command_args != "":
                        if command_name == "pause":
                            command_name += "="
                        else:
                            command_name += " "
                    macro.append(f"{command_name}{command_args}\n")

            if len(macro) == 0 :
                self.gui.display_error("No macro to execute!")
                return

            # execute
            for command in macro:
                self.command_queue.put(command.strip())
                #self.execute_command(target=target, command=command.strip())
        else:
            self.gui.display_error("Instrument not connected!")
            return

    def add_macro(self):
        """
        add a new macro command

        Parameters  :   None
        Returns     :   None
        """
        rowpos = self.gui.tbl_macros.rowCount()
        self.gui.tbl_macros.insertRow(rowpos)

    def delete_macro(self):
        """
        delete a macro command

        Parameters  :   None
        Returns     :   None
        """
        rowpos = self.gui.tbl_macros.currentRow()
        self.gui.tbl_macros.removeRow(rowpos)

    def get_macro(self):
        """
        returnt the macro

        Parameters  :   None
        Returns     :   None
        """
        return self.macro

    def execute_shortcut(self):
        """
        execute a shortcut
        """
        sender_name = self.gui.sender().objectName()
        for shortcut in self.gui.custom_shortcuts:
            if shortcut["name"] == sender_name:
                if self.connected is True:
                    command = shortcut["command"]
                    self.command_queue.put(command.strip())
                    #self.execute_command(target="visa", command=command)
                    return
                else:
                    self.gui.display_error("Instrument not connected!")
                    return


    def cmd_mgr_test(self, command):
        """
        simple debug function
        """
        self.data_signal.emit("TEST")
        res = self.send_command(command, read=True)
        self.data_signal.emit({"message_type":"in", "message":res})

#--------------------------------------------------------------------------------------------
#
#--------------------------------------------------------------------------------------------

if __name__ == '__main__':

    pass