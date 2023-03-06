"""
Thread interface service
"""
import time
import logging
import yaml
import subprocess
import threading
from typing import Iterable
from server.common import ServerBoxException, ErrorCode
from queue import Queue, Empty


logger = logging.getLogger(__name__)


class ThreadNode:
    """Thread nodes model"""

    name: str
    _id: str
    connected: bool

    def __init__(self, name: str, _id: str):
        self.name = name
        self._id = _id
        self.connected = False

    # TODO: modify connected status


class ThreadBoarderRouter(threading.Thread):
    """Service class for thread network setup management"""

    sudo_password: str
    thread_network_setup: dict = {}
    nodes = Iterable[ThreadNode]
    running: bool
    network_set_up_is_ok: bool
    msg_callback: callable
    keep_alive_callback: callable

    def __init__(self, sudo_password: str, thread_network_config_file: str):
        self.sudo_password = sudo_password
        self.msg_callback = None
        self.keep_alive_callback = None
        self.network_set_up_is_ok = False
        self.running = False

        # setup thread network
        self.setup_thread_network(thread_network_config_file)

    def enqueue_output(self, out, queue):
        for line in iter(out.readline, b""):
            queue.put(line)
        out.close()

    def run_dedicated_thread(self):
        """Run Thread loop in dedicated if network is setted up"""
        if self.network_set_up_is_ok and self.running:
            logger.info(f"Running Thread loop in dedicated thread")
            try:
                self.start()
            except Exception as e:
                logger.error(e)
        else:
            logger.error(f"Thread loop cant be run, network setup failed")

    def run(self):
        """Run thread"""

        process = subprocess.Popen(
            ["sudo", "ot-ctl"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        queue = Queue()
        reading_thread = threading.Thread(target=self.enqueue_output, args=(process.stdout, queue))
        reading_thread.daemon = True
        try:
            reading_thread.start()
        except Exception as e:
                logger.error(e)
        while self.running:
            try:
                output = queue.get_nowait()
            except Empty:
                pass
            else:
                msg = output.strip().split()[-1].decode()
                logger.info(f"Thread Message received: {msg}")
                if msg.startswith("ka"):
                    node = msg.split("_")[1]
                    logger.info(f"Keep alive message received for node {node}")
                    if self.keep_alive_callback is None:
                        logger.error("Keep alive reception callback is None")
                    else:
                        self.keep_alive_callback(node_id=node)
                    continue

                if self.msg_callback is None:
                    logger.error("Message reception callback is None")
                    continue
                self.msg_callback(msg)
        logger.info("End of Border Router thread")

    def set_msg_reception_callback(self, callback: callable):
        """Set Thread message reception callback"""
        self.msg_callback = callback

    def set_keep_alive_reception_callback(self, callback: callable):
        """Set Thread keep_alive reception callback"""
        self.keep_alive_callback = callback

    def setup_thread_network(self, thread_network_config_file: str) -> bool:
        """Setup the thread network"""
        logger.info("Thread network config file: %s", thread_network_config_file)

        # Load Thread network configuration
        with open(thread_network_config_file) as stream:
            try:
                configuration = yaml.safe_load(stream)
                self.nodes = [
                    ThreadNode(
                        name=node["name"],
                        _id=node["id"],
                    )
                    for node in configuration["THREAD"]["NODES"]
                ]
            except (yaml.YAMLError, KeyError):
                logger.error("Error in Thread configuration load, check file")
                self.network_set_up_is_ok = False
                return False

        # Thread network initialisation (ot-cli)
        # Necesary for boot ?
        time.sleep(5)

        try:
            for command in configuration["THREAD"]["NETWORK_SETUP_COMMANDS"]:
                # run command
                logger.debug(f"command: {command}")
                cmd = command.split()
                cmd1 = subprocess.Popen(["echo", self.sudo_password], stdout=subprocess.PIPE)
                cmd2 = subprocess.Popen(
                    ["sudo", "-S"] + cmd, stdin=cmd1.stdout, stdout=subprocess.PIPE
                )
                output = cmd2.stdout.read().decode()
                logger.debug(f"output: {output}")
                if "Done" not in output:
                    raise ServerBoxException(ErrorCode.THREAD_NETWORK_SETUP_ERROR)
                if "ipaddr" in command:
                    out = output.split("\r\n")[:-2]
                    self.thread_network_setup["ipv6_otbr"] = out[3]
                    self.thread_network_setup["ipv6_mesh"] = out[-1]
                elif "dataset active -x" in command:
                    out = output.split("\r\n")
                    self.thread_network_setup["dataset_key"] = out[0]
                time.sleep(2)
        except Exception as exc:
            logger.error("Thread network setup error")
            logger.error(exc)
            self.network_set_up_is_ok = False
            return False

        self.network_set_up_is_ok = True

        # Run dedicated thread
        if self.network_set_up_is_ok:
            self.running = True
            # Call Super constructor
            super(ThreadBoarderRouter, self).__init__(name="ThreadBorderRouterThread")
            self.setDaemon(True)

        logger.info(f"Thread network is running")
        logger.info(f"Thread network config: {self.thread_network_setup}")
        return True

    def getNodes(self) -> Iterable[ThreadNode]:
        """Returns the configured nodes"""
        return self.nodes
