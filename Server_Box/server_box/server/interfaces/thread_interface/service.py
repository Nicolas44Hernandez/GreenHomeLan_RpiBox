"""
Thread interface service
"""
import logging
import yaml
import subprocess
import shlex
import threading
from typing import Iterable
from server.common import ServerBoxException, ErrorCode

logger = logging.getLogger(__name__)


class ThreadNode:
    """Thread nodes model"""

    name: str
    mac: str
    url: str

    def __init__(self, name: str, mac: str, url: str):
        self.name = name
        self.mac = mac
        self.url = url


class ThreadBoarderRouter(threading.Thread):
    """Service class for thread network setup management"""

    sudo_password: str
    thread_network_setup: dict = {}
    nodes = Iterable[ThreadNode]
    running: bool
    msg_callback: callable

    def __init__(self, sudo_password: str, thread_network_config_file: str):
        self.sudo_password = sudo_password
        self.msg_callback = None

        # setup thread network
        self.setup_thread_network(thread_network_config_file)

        # Running flag
        self.running = True

        # Call Super constructor
        super(ThreadBoarderRouter, self).__init__(name="ThreadBorderRouterThread")
        self.setDaemon(True)

    def run(self):
        """Run thread"""
        process = subprocess.Popen(shlex.split("sudo ot-ctl"), stdout=subprocess.PIPE)
        while self.running:
            try:
                output = process.stdout.readline()
                if output == "" and process.poll() is not None:
                    break
                elif output:
                    logger.info("Thread Message received")
                    msg = output.strip().split()[-1].decode()
                    if self.msg_callback is None:
                        logger.error("Message reception callback is None")
                        break
                    self.msg_callback(msg)
            except KeyboardInterrupt:
                break
        logger.info("End of Border Router thread")

    def set_msg_reception_callback(self, callback: callable):
        """Set Thread message reception callback"""
        self.msg_callback = callback

    def setup_thread_network(self, thread_network_config_file: str):
        """Setup the thread network"""
        logger.info("Thread network config file: %s", thread_network_config_file)

        # Load Thread network configuration
        with open(thread_network_config_file) as stream:
            try:
                configuration = yaml.safe_load(stream)
                self.nodes = [
                    ThreadNode(name=node["name"], mac=node["mac"], url=node["server_url"])
                    for node in configuration["THREAD"]["NODES"]
                ]
            except (yaml.YAMLError, KeyError) as exc:
                raise ServerBoxException(ErrorCode.THREAD_CONFIG_FILE_ERROR)

        # Thread network initialisation (ot-cli)
        for command in configuration["THREAD"]["NETWORK_SETUP_COMMANDS"]:
            try:
                # run command
                cmd = command.split()
                cmd1 = subprocess.Popen(["echo", self.sudo_password], stdout=subprocess.PIPE)
                cmd2 = subprocess.Popen(
                    ["sudo", "-S"] + cmd, stdin=cmd1.stdout, stdout=subprocess.PIPE
                )
                if "ipaddr" in command:
                    output = cmd2.stdout.read().decode()
                    out = output.split("\r\n")[:-2]
                    self.thread_network_setup["ipv6_otbr"] = out[3]
                    self.thread_network_setup["ipv6_mesh"] = out[-1]
                elif "dataset active -x" in command:
                    output = cmd2.stdout.read().decode()
                    out = output.split("\r\n")
                    self.thread_network_setup["dataset_key"] = out[0]
            except:
                logger.error("Thread network setup error")
                raise ServerBoxException(ErrorCode.THREAD_NETWORK_SETUP_ERROR)

        logger.info(f"Thread network config: {self.thread_network_setup}")

    def getNodes(self) -> Iterable[ThreadNode]:
        """Returns the configured nodes"""
        return self.nodes
