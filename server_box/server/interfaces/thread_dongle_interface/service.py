"""
Thread interface service
"""
import time
import logging
import threading
import serial

logger = logging.getLogger(__name__)


class ThreadServerDongle(threading.Thread):
    """Service class for thread server dongle setup management"""

    network_set_up_is_ok: bool
    msg_callback: callable
    keep_alive_callback: callable

    def __init__(self, thread_serial_port: str, serial_speed: int = 115200):
        self.msg_callback = None
        self.keep_alive_callback = None

        self.thread_serial_port = thread_serial_port

        # Run Thread interface dedicated thread
        logger.info(f"Creatting serial interface object...")
        self.serial_interface = serial.Serial(
            self.thread_serial_port, serial_speed, stopbits=serial.STOPBITS_ONE
        )
        super(ThreadServerDongle, self).__init__(name="ThreadServerDongleThread")
        self.setDaemon(True)

    def run_dedicated_thread(self):
        """Run Thread loop in dedicated"""
        logger.info(f"Running Thread loop in dedicated thread")
        try:
            self.start()
        except Exception as e:
            logger.error(e)

    def run(self):
        """Run thread"""
        while True:
            if self.serial_interface.inWaiting() > 0:
                received_data = self.serial_interface.read(
                    self.serial_interface.inWaiting()
                )
                msg = received_data.decode("utf-8")
                msg = str(msg[: len(msg) - 1])

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
            time.sleep(0.1)

    def set_msg_reception_callback(self, callback: callable):
        """Set Thread message reception callback"""
        self.msg_callback = callback

    def set_keep_alive_reception_callback(self, callback: callable):
        """Set Thread keep_alive reception callback"""
        self.keep_alive_callback = callback

    def write_message_to_dongle(self, msg: str):
        """Write message to dongle"""
        message = "~" + msg + "#"
        logger.info(f"Sending msg: %s", message)
        ret = self.serial_interface.write(message.encode("utf-8"))
        # TODO: manage return values and exceptions

        if ret != 0:
            return True
        return False
