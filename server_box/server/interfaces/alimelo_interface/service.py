"""
Alimelo interface service
"""
import logging
import threading
import serial

logger = logging.getLogger(__name__)


class AlimeloSerialCom(threading.Thread):
    """Service class for Alimelo management"""

    serial_port: str
    notification_separator: str
    serial: serial.Serial
    notification_callback: callable

    def __init__(self, serial_port: str, notification_separator: str):
        self.serial_port = serial_port
        self.notification_separator = notification_separator
        self.serial = None
        self.notification_callback = None

        # setup thread network
        self.setup_serial_communication()

        # Running flag
        self.running = True

        # Call Super constructor
        super(AlimeloSerialCom, self).__init__(name="AlimeloSerialComThread")
        self.setDaemon(True)

    def run(self):
        """Run thread"""
        notification_separator_start = self.notification_separator + "_BEGINS"
        notification_separator_end = self.notification_separator + "_ENDS"
        notification_info = ""
        while self.running:
            try:
                serial_read = self.serial.readline().decode("utf-8")
                if len(serial_read) > 10:
                    if notification_separator_start in serial_read:
                        reading_notification = True
                        while reading_notification:
                            notification_read = self.serial.readline().decode("utf-8")
                            if notification_separator_end in notification_read:
                                reading_notification = False
                                if self.notification_callback is None:
                                    logger.error("Notification reception callback is None")
                                    break
                                self.notification_callback(notification_info.replace("\r\n", ""))
                                notification_info = ""
                                continue
                            notification_info += notification_read

            except (Exception, ValueError) as e:  # TODO: manage serial com exceptions
                self.serial.close()
                logger.error("Error in serial communication, restarting connection")
                self.setup_serial_communication()
        logger.info("End of Alimelo serial communication")
        self.serial.close()

    def set_notification_reception_callback(self, callback: callable):
        """Set Serial notification reception callback"""
        self.notification_callback = callback

    def setup_serial_communication(self):
        """Setup the Serial communication with Alimelo"""
        logger.info("Setting up the serial communication")

        self.serial = serial.Serial(
            port=self.serial_port,
            baudrate=9600,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=0,
        )

        self.serial.flushInput()
        self.serial.flushOutput()

        logger.info("Connected to: " + self.serial.portstr)
