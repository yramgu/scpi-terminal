"""
#------------------------------------------------------------------------------
# Name:        eqpt
# Purpose:     Equipment control baseclass
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

# Get the absolute path to the parent directory
parent_dir = ".."
if getattr(sys, 'frozen', False):
    parent_dir = os.path.abspath(os.path.join(os.path.dirname(sys.executable), '.'))
elif __file__:
    parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(parent_dir)

import pyvisa as visa

try:
    from log.class_logging import log
except ModuleNotFoundError:
    import logging
    log = logging.getLogger(__name__)
    log.warning("Imported local logger")

#--------------------------------------------------------------------------------------------
#
#--------------------------------------------------------------------------------------------

class Eqpt:
    """
    Equipment class
    """

    def __init__(self, subinstrument=0):

        self.instrument = None
        self.connected  = False
        self.subinstrument = subinstrument
        log.info("Instantiating Equipment class")

    def connect_instrument(self, ip, subinstrument):
        """
        Open instrument connection

        Parameters:
                    ip : str
                        IP address

        Returns   : None
        """

        try:
            self.instrument = visa.ResourceManager('@py').open_resource(f"TCPIP::{ip}::inst{subinstrument}::INSTR")
        except (visa.VisaIOError, OSError) as e:
            log.exception(f"Cannot find instrument with IP address {ip}")
            return e
        log.info("Connected")
        self.connected = True
        return 0


    def close_instrument(self):
        """
        Close instrument connection

        Parameters: None
        Returns   : None
        """

        if self.connected:
            log.info("Connection closed")
            self.instrument.close()
            self.connected = False

    #-----------------------------------------------------------------
    #                     Generic commands
    #-----------------------------------------------------------------

    def send_command(self, command, read=False, read_trycount=1):
        """
        Send SCPI command to instrument

        Parameters:
                    command : str
                        SCPI command to send
                    read : bool
                        read back instrument reply
                    read_trycount : int
                        Number of tries to read, 0.2s between tries

        Returns   :
                    -1 or instrument reply if read=True
        """

        log.debug(f"{command}")
        command = command.replace("\"", "'")
        if self.connected:
            try:
                self.instrument.write(command)
                if read:
                    trycount = 0
                    while trycount < read_trycount:
                        try:
                            res = self.instrument.read()
                            return res
                        except visa.VisaIOError as e:
                            log.info("waiting for read")
                            sleep(0.2)
                        trycount += 1
                else:
                    return -1
            except (visa.VisaIOError, UnicodeEncodeError) as e:
                log.exception("Error:")
                return "tool_error: " + str(e)
        else:
            return -1

    def read(self):
        """
        Read value from instrument

        Parameters: None

        Returns   :
                    result: str
                        return string from instrument
        """

        result = ""
        if self.connected:
            result = self.instrument.read()
            return result
        else:
            return -1

    def idn(self):
        """
        Returns instrument Identification string

        Parameters: None

        Returns   :
                    result: str
                        return string from instrument
        """

        command = "*IDN?"
        result = self.send_command(command, read=True)
        log.debug("Reply: %s", result)
        return result

    def opc(self):
        """
        Check if instrument is ready

        Parameters: None

        Returns   :
                    result: str
                        return string from instrument
        """

        command = "*OPC?"
        result = self.send_command(command, read=True)
        try:
            pass
            #log.info("CMW100 reply: %s"%result.replace("\n",""))
        except AttributeError:
            pass
        return result

    def wait(self, timeout_s=10, verbose=False):
        """
        send OPC command and wait for it to return "ready"

        Parameters:
                    timeout_s : int
                        wait timeout in seconds
                    verbose: bool
                        additional verbosity if True

        Returns   : None
        """

        trycount = 0
        opc = self.opc()
        while trycount < timeout_s*10:
            sleep(0.1)
            opc = self.opc()
            if opc != '-1':
                return
            if verbose:
                log.info(f"Try {trycount} - Waiting for instrument...")
            trycount += 1
        log.warning("OPC Waiting timeout!")

    def clear_errors(self):
        """
        Clear the event status registers and empty the error queue

        Parameters: None
        Returns   : None
        """

        command = "*CLS"
        res = self.send_command(command)
        return None

    def preset(self):
        """
        reset the instruments and wait for operation complete via the *opc?, i.e. the operation complete command.

        Parameters: None
        Returns   : None
        """

        command = "SYST:PRES"
        res = self.send_command(command)
        self.wait()
        log.info("Preset complete")

        return None

    def reset(self):
        """
        reset the instruments and wait for operation complete via the *opc?, i.e. the operation complete command.

        Parameters: None
        Returns   : None
        """

        command = "SYST:RES"
        res = self.send_command(command)
        self.wait()
        log.info("Preset complete")
        return None

    def read_errors(self):
        """
        Query instrument errrors

        Parameters: None
        Returns   :
                    result: str
                        instrument reply
        """

        command = "SYST:ERR?"
        res = self.send_command(command, read=True)
        log.debug("reply: %s", res)
        return res

    def debug(self):
        """
        """
        return "DEBUG"


#--------------------------------------------------------------------------------------------
#
#--------------------------------------------------------------------------------------------

if __name__ == "__main__":

    logging.basicConfig(format='%(asctime)s\t[%(levelname)s]\t[%(module)s]\t[%(funcName)s]\t%(message)s',datefmt='%d/%m/%Y %H:%M:%S', level=logging.INFO)
    logger = logging.getLogger(__name__)

