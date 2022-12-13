"""
Telnet connection service
"""
import logging
import socket
import telnetlib
import time
from server.common import ServerBoxException, ErrorCode

logger = logging.getLogger(__name__)


class Telnet:
    """Service class for telnet connection and commands management"""

    def __init__(
        self,
        host: str,
        port: int = 23,
        login: str = None,
        password: str = None,
        telnet_timeout_in_secs: float = 5,
    ):
        self.host = host
        self.port = port
        self.login = login
        self.password = password
        self.telnet_timeout_in_secs = telnet_timeout_in_secs
        self.connection = self.create_telnet_connection()
        self.super_user_session = False

    def create_telnet_connection(self):
        """Create telnet connection with host"""

        # try to connect
        try:
            tn_connection = telnetlib.Telnet(
                self.host, self.port, timeout=self.telnet_timeout_in_secs
            )
            tn_connection.read_until(b"login: ", timeout=self.telnet_timeout_in_secs)
            login = self.login + "\n"
            # Enter login
            tn_connection.write(login.encode("utf-8"))

            if self.password:
                tn_connection.read_until(b"Password: ", timeout=self.telnet_timeout_in_secs)
                password = self.password + "\n"
                # Enter password
                tn_connection.write(password.encode("utf-8"))
        except (socket.timeout, socket.error):
            logger.error("Telnet connection creation failed")
            raise ServerBoxException(ErrorCode.TELNET_CONNECTION_ERROR)

        logger.info(f"Telnet connection established with host: %s", self.host)
        return tn_connection

    def create_super_user_session(self):
        """Create superuser session in connected host (~$sudo su)"""
        try:
            self.connection.write("sudo su\n".encode("utf-8"))
            flag = self.login + ":"
            self.connection.read_until(flag.encode("utf-8"), timeout=self.telnet_timeout_in_secs)
            password = self.password + "\n"
            # Enter password
            self.connection.write(password.encode("utf-8"))
        except (socket.timeout, socket.error):
            raise ServerBoxException(ErrorCode.TELNET_CONNECTION_ERROR)

        self.super_user_session = True
        logger.debu("Super user session created")

    def close(self):
        try:
            self.connection.write(b"exit\n")
        except (socket.timeout, socket.error):
            logger.error("Error in telnet connection")
            raise ServerBoxException(ErrorCode.TELNET_CONNECTION_ERROR)
        logger.debug(f"Telnet connection closed with host: %s", self.host)

    def send_command(self, command: str) -> str:
        """Send command to telnet host"""
        if "sudo " in command:
            self.create_super_user_session()
        try:
            command = f"echo -n 'EE''EE '; {command}; echo 'FF''FF'\n"
            self.connection.write(command.encode("ascii"))
            return self.get_command_output()
        except (socket.timeout, socket.error):
            raise ServerBoxException(ErrorCode.TELNET_CONNECTION_ERROR)

    def send_fast_command(self, command: str):
        """Send command without waiting for response"""
        command = command + "\n"
        self.connection.write(command.encode("ascii"))
        time.sleep(0.1)
        return "OK"

    def parse_telnet_output(self, raw_output: str):
        """Parse the output of the sent command"""
        _splitted_patern = raw_output.split("EEEE")
        return _splitted_patern[len(_splitted_patern) - 1].split("FFFF")[0].lstrip()[:-2]

    def get_command_output(self):
        """retrieve and parse command output"""

        # retrieve output
        output_brut = self.connection.read_until(b"FFFF", 3).decode("ascii")

        # parse output
        return str(self.parse_telnet_output(output_brut))
