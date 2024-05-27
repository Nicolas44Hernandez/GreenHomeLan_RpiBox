"""
SSH connection service
"""
import logging
from fabric import Connection
from server.common import ServerBoxException, ErrorCode

logger = logging.getLogger(__name__)


class SshClient:
    """Service class for ssh connection and commands management"""

    def __init__(
        self,
        host: str,
        port: int = 22,
        user: str = None,
        password: str = None,
        timeout_in_secs: float = 5,
    ):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.timeout_in_secs = timeout_in_secs
        self.connection = self.create_connection()
        self.super_user_session = False


    def create_connection(self):
        """Create ssh connection with host"""

        # try to connect
        try:
            connection = Connection(
                host=self.host,
                port=self.port,
                user=self.user,
                connect_kwargs={"password": self.password},
                connect_timeout=self.timeout_in_secs
            )
        except Exception:
            logger.error("SSH connection creation failed")
            return None

        return connection

    def close(self):
        try:
            if not self.connection:
                logger.error("SSH connection not stablished")
                return None
            self.connection.close()
        except Exception:
            logger.error("Error in SSH connection")
            raise ServerBoxException(ErrorCode.SSH_CONNECTION_ERROR)
        logger.debug(f"SSH connection closed with host: %s", self.host)


    def send_command(self, command: str) -> str:
        """Send command to SSH host"""
        try:
            if not self.connection:
                logger.error("SSH connection not stablished")
                return None
            result = self.connection.run(command, hide=True)
            #logger.info(f"command: '{result.command}' result: '{result.stdout}'")
            if len(result.stdout) > 2 and result.stdout[-1] == '\n':
                return result.stdout[0:-1]
            return result.stdout
        except Exception as e:
            logger.error(e)
            raise ServerBoxException(ErrorCode.SSH_CONNECTION_ERROR)
