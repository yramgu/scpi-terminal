"""
# Name:        scpi_terminal.py
# Purpose:     Talk to test equipment by ethernet / VISA driver
#
# Author:      Yannish RAMGULAM
#
# Created:     08/2025
# Copyright:   (c) Y.Ramgulam 2025
# Licence:     <your licence>
#
#

GUI update:
------
pyuic6 -o ui/scpi_term_ui.py ui/scpi_term_ui.ui

"""

import sys
import os
import traceback
import json
import copy
from   datetime       import datetime
from   collections    import deque

# pylint: disable=no-name-in-module
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QMessageBox, QFileDialog, QTableWidgetItem, QVBoxLayout,
    QHeaderView, QTableWidget, QTreeWidgetItem, QTreeWidget
)
from PyQt6 import QtGui
from PyQt6.QtCore import  QTimer, QEventLoop, Qt, QTime, QThread, pyqtSignal

from ui.scpi_term_ui                    import Ui_MainWindow
from log.class_logging                  import setup_logger, log
from equipment.command_manager          import CommandManager

VERSION_MAJOR = 1
VERSION_MINOR = 1


#--------------------------------------------------------------------------------------------
#
#                                Main class
#
#--------------------------------------------------------------------------------------------

class Window(QMainWindow, Ui_MainWindow):
    """
    Main Window
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        # launch GUI
        self.setupUi(self)

        # reinstantiate the logger by enabling the gui console
        setup_logger(gui_log_widget=self.console)

        # Paths
        self.path           = self.get_app_path()

        # restart the logger
        log.info("**********************************************")
        log.info("*                                            *")
        log.info("*                SCPI TERMINAL               *")
        log.info(f"*                    v{VERSION_MAJOR}.{VERSION_MINOR}                    *")
        log.info("*              Y.Ramgulam - 2025             *")
        log.info("*                                            *")
        log.info("**********************************************\n")

        log.info(f"Version {VERSION_MAJOR}.{VERSION_MINOR}")

        # read config
        self.config = self.init_general()

        # custom buttons
        self.custom_shortcuts = self.init_custom_buttons()

        # set icon
        self.icon = self.path + '\\ui\\terminal.ico'
        self.setWindowIcon(QtGui.QIcon(self.icon))
        self.setWindowTitle(f"SCPI TERMINAL - v{VERSION_MAJOR}.{VERSION_MINOR}")

        self.scpi_record = None

        # setup classes
        self.init_services()

        # callbacks
        self.connect_callbacks()

    #--------------------------------------------------
    #               GENERAL FUNCTIONS
    #--------------------------------------------------
    def debug(self):
        """
        Used only in DEBUG mode
        It's a callback to the DEBUG button
        """
        log.info( "DEBUG CALLBACK")

    def closeEvent(self, event):
        """
        Event raised when closing the window. Allows to gracefully close everything
        """

        log.info( "Closing program")
        if self.scpi_record is not None:
            self.scpi_record.close()
        event.accept()
        os._exit(0)

    def display_error(self, message):
        """
        Display an error popup window

        Parameters  :
                        message: str
                            message to display

        Returns     :   None
        """

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setText(message)
        msg.setWindowTitle("Error")
        msg.exec()

    def display_warning(self, message):
        """
        Display a warning popup window

        Parameters  :
                        message: str
                            message to display

        Returns     :   None
        """

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setText(message)
        msg.setWindowTitle("Warning")
        msg.exec()

    def display_info(self, message):
        """
        Display an info popup window

        Parameters  :
                        message: str
                            message to display

        Returns     :   None
        """

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setText(message)
        msg.setWindowTitle("Info")
        msg.exec()

    def about(self):
        """
        Display tool information

        Parameters  :   None
        Returns     :   None
        """

        msg = QMessageBox()
        msg.setIconPixmap(QtGui.QPixmap(self.path + '\\ui\terminal.png'))
        msg.setText(f"(c) Y.RAMGULAM - 2025 \n\n SCPI Terminal \n\n V{VERSION_MAJOR}.{VERSION_MINOR}")
        msg.setWindowTitle("About")
        msg.exec()

    def sleep_ms(self, delay):
        """
        Sleep for <delay> ms

        Parameters  :
                        delay: int
                            sleep time in ms

        Returns     :   None
        """

        loop = QEventLoop()
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(loop.quit)
        timer.start(delay)
        loop.exec()

    #--------------------------------------------------
    #               INIT
    #--------------------------------------------------

    def get_app_path(self):
        """
        Determine if application is a script file or frozen exe
        and get the proper path to fetch files
        otherwise when we create an exe the paths are borken by pyInstaller

        Parameters  :   None

        Returns     :
                        application_path: str
                            application path
        """

        application_path = "."
        if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable)
        elif __file__:
            application_path = os.path.dirname(__file__)
        return application_path

    def init_general(self):
        """
        init main config file and gui

        Parameters  :   None

        Returns     :
                        config: dict
                            main config content
        """

        log.info("Loading config")

        with open(f"{self.path}\\config\\config.json", "r", encoding="utf-8") as f:
            config =  json.load(f)

        if config["instrument"].get("ip", None) is not None:
            self.txt_ip.setText(config["instrument"].get("ip", None))

        if config["instrument"].get("subinstrument", None) is not None:
            self.sbx_subinstr.setValue(int(config["instrument"].get("subinstrument", None)))

        self.console.setStyleSheet("""
            QTextEdit {
                background-color: #2E3440;   /* Dark background */
                color: #D8DEE9;              /* Light font color */
                font-size: 16px;             /* Font size */
                font-family: Courier New;       /* Optional: font family */
            }
        """)

        self.chk_record.setCheckState(Qt.CheckState.Checked if config["misc"]["record"] is True else Qt.CheckState.Unchecked)

        self.tbl_macros.horizontalHeader().setStretchLastSection(True)
        self.tbl_macros.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

        # shortcuts
        self.custom_buttons = {
            "1": self.cbtn1,
            "2": self.cbtn2,
            "3": self.cbtn3,
            "4": self.cbtn4,
            "5": self.cbtn5,
            "6": self.cbtn6,
            "7": self.cbtn7,
            "8": self.cbtn8,
            "9": self.cbtn9,
            "10": self.cbtn10,
            "11": self.cbtn11,
            "12": self.cbtn12,
        }


        return config

    def init_services(self):
        """
        start services

        Parameters  :   None
        Returns     :   None
        """

        self.cmd_thread = QThread()
        self.cmd_mgr = CommandManager(self)
        self.cmd_mgr.moveToThread(self.cmd_thread)
        self.cmd_thread.finished.connect(self.cmd_thread.deleteLater)
        self.cmd_thread.started.connect(self.cmd_mgr.run)
        self.cmd_mgr.finished_signal.connect(self.cmd_thread.quit)
        self.cmd_mgr.finished_signal.connect(self.cmd_mgr.deleteLater) # ensure no memory leak
        self.cmd_mgr.data_signal.connect(self.process_data)
        self.cmd_mgr.status_signal.connect(self.process_status)

        self.cmd_thread.start()

    def init_custom_buttons(self):
        """
        Init the custom buttons

        Parameters  :   None
        Returns     :   None
        """
        custom_btn = []

        for cst in self.config["custom_shortcuts"]:
            button = self.custom_buttons.get(str(cst["button"]), None)
            if button is None:
                self.display_error(f"Invalid custom button: {str(cst["button"])}. Cannot initialise custom shortcuts")
                return []
            custom_btn.append(
                {
                    "button": button,
                    "name": button.objectName(),
                    "title": cst["title"],
                    "command": f"{cst['command']} {"" if cst["args"] is None else cst["args"]}",
                }
            )
            button.setText(cst["title"])

        return custom_btn


    def connect_callbacks(self):
        """
        GUI callbacks

        Parameters  :   None
        Returns     :   None
        """

        self.macro_load.clicked.connect(self.load_macro)
        self.macro_export.clicked.connect(self.export_macro)

    #--------------------------------------------------
    #               instrument
    #--------------------------------------------------

    def process_data(self, data):
        """
        CALLBACK

        Process incoming data

        Parameters  :   data: data to display
        Returns     :   None
        """

        if data.get("message_type", None) =="connection":
            self.lbl_idstring.setText(data.get("message", None).strip("\r\n"))
        else:
            msg_color = self.config["misc"]["log_colors"].get("default", "#D8DEE9")
            if data["message_type"] == "out":
                msg_color = self.config["misc"]["log_colors"].get("out", "#D8DEE9")
            elif data["message_type"] == "in":
                msg_color = self.config["misc"]["log_colors"].get("in", "#D8DEE9")
            elif data["message_type"] == "err":
                msg_color = self.config["misc"]["log_colors"].get("err", "#D8DEE9")
            elif data["message_type"] == "pause":
                msg_color = self.config["misc"]["log_colors"].get("pause", "#D8DEE9")

            if data["message"] is None:
                data["message"] = "None\r\n"

            msg = f"{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")} - [{data['message_type'].ljust(5)}] :: {data["message"]}"

            self.write_console(msg, msg_color)

            if self.scpi_record is not None:
                self.scpi_record.write(f"{msg}\n")


    def process_status(self, status):
        """
        CALLBACK

        Process status signals

        Parameters  :   status: status to display
        Returns     :   None
        """
        self.statusBar().showMessage(status)

    def write_console(self, msg, msg_color):
        """
        Display console message

        Parameters  :
                        msg: dict
                        msg_color: Qcolor

        Returns     :   None
        """

        self.console.setTextColor(QtGui.QColor(msg_color))
        self.console.append(msg.encode('utf-8', errors='replace').decode('utf-8'))
        self.console.moveCursor(QtGui.QTextCursor.MoveOperation.End)
        self.console.update()

    #--------------------------------------------------
    #               Macro
    #--------------------------------------------------

    def load_macro(self):
        """
        load a macro file

        Parameters  :   None
        Returns     :   None
        """

        filepath = QFileDialog.getOpenFileName(self, 'Open File', f"{self.path}\\macros\\", 'JSON file (*.json)')[0]
        if filepath != "":
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    macro = json.load(f)
                self.process_status(f"Opened Macro file: {filepath}")
            except json.JSONDecodeError:
                self.display_error("Cannot open Macro file! Check log.")
                log.exception("")
                return
            try:
                self.tbl_macros.setRowCount(0)
                for command in macro["commands"]:
                    rowpos = self.tbl_macros.rowCount()
                    self.tbl_macros.insertRow(rowpos)
                    self.tbl_macros.setItem(rowpos, 0, QTableWidgetItem(command["name"]))
                    self.tbl_macros.setItem(rowpos, 1, QTableWidgetItem(command["args"]))
                #self.cmd_mgr.set_macro(macro["commands"])
            except KeyError:
                log.error(f"{filepath} does not seem to be a valid macro file")
                return

    def export_macro(self):
        """
        export a macro file

        Parameters  :   None
        Returns     :   None
        """

        filepath = QFileDialog.getSaveFileName(self, 'Save File', f"{self.path}\\macros\\", 'JSON file (*.json)')[0]
        if filepath != "":
            # init json structure
            macro_file = {
                "commands": []
            }
            # iterate through table
            macro_table = self.tbl_macros

            for row in range(macro_table.rowCount()):
                macro_file["commands"].append({"name": macro_table.item(row, 0).text(), "args": macro_table.item(row, 1).text()})
            # save
            log.info(f"Macro file saved at {filepath}")
            self.process_status(f"Save Macro file : {filepath}")
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(macro_file, f, indent=4)

#--------------------------------------------------------------------------------------------
#
#--------------------------------------------------------------------------------------------

if __name__ == "__main__":

    try:
        app = QApplication(sys.argv)
        #app.setStyle('Fusion')
        app.setStyle('windowsvista')
        win = Window()
        win.showMaximized()
        #win.show()
        sys.exit(app.exec())
    except Exception:
        log.exception(traceback.format_exc())
        input()
