import logging
import json
from queue import Queue
from datetime import timedelta
from timeloop import Timeloop
from typing import Iterable
from server.managers.wifi_bands_ssh_manager import wifi_bands_manager_service
from server.managers.mqtt_liveobjects_manager import mqtt_liveobjects_manager_service
from server.managers.alimelo_manager import alimelo_manager_service

logger = logging.getLogger(__name__)

msg_send_timeloop = Timeloop()

class LiveObjects:
    commands_reception_topic: str
    data_send_topic: str
    sent_queue: Queue

    def init_live_objects_module(self, commands_reception_topic: str, data_send_topic: str) -> None:
        # Interface to connect to Live Objects
        self.commands_reception_topic = commands_reception_topic
        self.data_send_topic = data_send_topic
        self.sent_queue = Queue(maxsize = 5)
        self.schedule_msg_sent_loop()


    def set_notifications_reception_callback(self, callback: callable):
        """Set callback for notifications reception"""
        self.live_objects_interface.set_notification_reception_callback(callback)


    def set_commands_reception_callback(self, callback: callable):
        """Set callback for commands reception from alimelo and from mqtt"""

        # Set alimelo liveobjects command reception
        alimelo_manager_service.set_live_objects_command_reception_callback(callback)

        # Set MQTT commands reception callback
        mqtt_liveobjects_manager_service.subscribe_to_topic(topic=self.commands_reception_topic, callback=callback)


    def publish_data(self, data_to_send, tags: Iterable[str]= None):
        """Publish data to LiveObjects"""

        logger.info(f"Publish data to Live Objects: {data_to_send}")

        # Prepare message
        data_to_send_via_mqtt= {"value": data_to_send, "tags":[]}

        # Add tags if pressent
        if tags is not None :
            for tag in tags:
                if type(tag) is str:
                    data_to_send_via_mqtt["tags"].append(tag)

        # If connnected to internet send via internet, else send via Alimelo
        connected_to_internet = (
                wifi_bands_manager_service.is_connected_to_internet()
        )
        #TODO: MOCK
        #connected_to_internet = False
        if connected_to_internet:
            logger.info("Connected to internet, sending datga via internet")
            # Add protocol used tag
            data_to_send_via_mqtt["tags"].append("livebox")
            # Add element in sent queue
            if not self.sent_queue.full():
                element = {"topic":self.data_send_topic, "data_to_send": data_to_send_via_mqtt}
                self.sent_queue.put_nowait(element)
            #mqtt_liveobjects_manager_service.publish_message(topic=self.data_send_topic, message=data_to_send_via_mqtt)
        else:
            logger.info("Not connected to internet, sending data via Alimelo")
            data = json.dumps(data_to_send).replace(" ", "")
            alimelo_manager_service.send_data_to_live_objects(data)

    def schedule_msg_sent_loop(self):
        """Start msg sent periodic"""

        # Start wifi status polling service
        @msg_send_timeloop.job(
            interval=timedelta(seconds=1)
        )
        def send_messages_in_queue():
            # Send messages in queue
            if self.sent_queue.qsize() > 0 :
                element = self.sent_queue.get_nowait()
                topic = element["topic"]
                data_to_send = element["data_to_send"]
                mqtt_liveobjects_manager_service.publish_message(topic=topic, message=data_to_send)


        msg_send_timeloop.start(block=False)
live_objects_service: LiveObjects = LiveObjects()
