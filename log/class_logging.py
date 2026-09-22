"""
# Name:        class_logging.py
# Purpose:     logging
#
# Author:      Yannish RAMGULAM
#
# Created:     12/2024
# Copyright:   (c) Y.Ramgulam 2024
# Licence:     <your licence>
#
# Last updated: 12/2024
#
"""

import os, sys
import inspect
import logging
import json
from io import StringIO

# pylint: disable=no-name-in-module
from PyQt6.QtGui import QColor, QTextCursor
from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtCore import QObject, pyqtSignal

# Get the absolute path to the parent directory
root_path = ".."
if getattr(sys, 'frozen', False):
    root_path = os.path.abspath(os.path.join(os.path.dirname(sys.executable), '.'))
elif __file__:
    root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(root_path)

#--------------------------------------------------------------------------------------
#
#--------------------------------------------------------------------------------------

format_template = '%(asctime)s [%(levelname)-8s] - Module: %(module)-30sMethod: %(funcName)-30sMessage: %(message)s'

base_path = f"{root_path}\\Log"#os.path.dirname(__file__)

class QtLogSignal(QObject):
        """
        Used to handle signals for GUI
        """
        new_log = pyqtSignal(str)

class QTextEditLogHandler(logging.Handler):
    def __init__(self, text_edit: QTextEdit):
        super().__init__()
        self.text_edit = text_edit
        self.signal = QtLogSignal()
        self.signal.new_log.connect(self.append_text)

    def emit(self, record):
        msg = self.format(record)
        self.signal.new_log.emit(msg)

    def append_text(self, msg):
        self.text_edit.moveCursor(QTextCursor.MoveOperation.End)
        #self.text_edit.insertPlainText(msg + "\n")
        self.text_edit.insertHtml(msg + "<br>")
        self.text_edit.moveCursor(QTextCursor.MoveOperation.End)

class HtmlFormatter(logging.Formatter):
    """
    Class for adding colors to the GUI log
    """

    def __init__(self, fmt, datefmt=None):
        # Initialize with custom datefmt if provided
        super().__init__(fmt, datefmt)
        self.colors = self.read_color_config()["gui_colors"]
        self.colors = {key: value.encode().decode('unicode_escape') for key, value in self.colors.items()} # this is to manage the \

    def format(self, record):
        level = record.levelname
        color = self.colors.get(level, 'black')
        message = super().format(record)

        return f'<pre style="color:{color}; font-family: Courier New; margin:0;">{message}</pre>'

    def read_color_config(self):
        """
        load json config file
        """
        with open(f"{base_path}\\logger_config.json", "r", encoding="utf-8") as f:
            f = json.loads(f.read())
        return f


class PrettyFormatter(logging.Formatter):
    """
    Class that creates a console logging format using colors
    """
    def __init__(self, fmt, datefmt=None):
        # Initialize with custom datefmt if provided
        super().__init__(fmt, datefmt)
        self.colors = self.read_color_config()["console_colors"]
        self.colors = {key: value.encode().decode('unicode_escape') for key, value in self.colors.items()} # this is to manage the \

    def read_color_config(self):
        """
        load json config file
        """
        with open(f"{base_path}\\logger_config.json", "r", encoding="utf-8") as f:
            f = json.loads(f.read())
        return f

    def format(self, record):
        # Apply color to the entire log string based on log level
        log_color = self.colors.get(record.levelname, self.colors["reset"])
        # Format the entire string
        log_message = super().format(record)
        # Colorize the whole log message
        return f"{log_color}{log_message}{self.colors["reset"]}"

# Set up logging
def setup_logger(gui_log_widget: QTextEdit = None):
    """
    Create the console logger and the file logger

    Parameters  :
                    gui_log_widget: QTextEdit
                        widget used to display log

    Returns     :
                    logger
                        logger instance
    """

    with open(f"{root_path}\\config\\config.json", "r", encoding="utf-8") as f:
        f = json.loads(f.read())

    logger      = logging.getLogger("custom_logger")
    if f["misc"]["debug_log"] is True:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    # Prevent duplicate logs
    if logger.hasHandlers():
        logger.handlers.clear()

    # Console Handler using colors
    handler     = logging.StreamHandler()
    handler.setFormatter(PrettyFormatter(format_template, datefmt='%d/%m/%Y %H:%M:%S'))
    logger.addHandler(handler)
    #logger.setLevel(logging.DEBUG)

    # File handler
    file_handler = logging.FileHandler(filename=f"{base_path}\\debug.log", mode="w")
    file_handler.setFormatter(logging.Formatter(format_template, datefmt='%d/%m/%Y %H:%M:%S'))
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)

    # Optional GUI handler
    # if gui_log_widget is not None and f["misc"]["enable_console"] is True:
    #     gui_handler = QTextEditLogHandler(gui_log_widget)
    #     gui_handler.setFormatter(HtmlFormatter(format_template, datefmt='%d/%m/%Y %H:%M:%S'))
    #     logger.addHandler(gui_handler)

    return logger

#
# Instantiate logger
#
log = setup_logger()

#-----------------------------------------------------------------------------------------------
#       UNIT TESTS
#-----------------------------------------------------------------------------------------------

if __name__ == "__main__":
    log.debug("This is a debug message")
    log.info("This is an info message")
    log.warning("This is a warning message")
    log.error("This is an error message")
    log.critical("This is a critical message")
    try:
        raise ValueError
    except ValueError:
        log.exception("This is a exception message")
