import logging
import subprocess
from server.common import ServerBoxException, ErrorCode

logger = logging.getLogger(__name__)


class IpDiscoveryService:
    """Ip discovery service"""

    def reload_tables(self):
        """Make a brodcast ping to reload arp tables"""
        brodcast_ping = subprocess.run(["nmap", "-sn", "192.168.1.0/24"])
        if brodcast_ping != 0:
            logger.error(f"Error in brodcast ping")
            raise ServerBoxException(ErrorCode.IP_DISCOVERY_BRODCAST_PING_ERROR)
        logger.info(f"brodcast ping ok")

    def get_ip_addr(self, mac: str) -> str:
        """Get ip address from mac"""

        # ip neighbor | greep -i {mac}
        try:
            cmd1 = subprocess.Popen(["ip", "neighbor"], stdout=subprocess.PIPE)
            cmd2 = subprocess.check_output(["grep", "-i", "E4:5F:01:1E:0A:34"], stdin=cmd1.stdout)
            station_ip = cmd2.decode().split(" ")[0]
        except:
            logger.error(f"Station {mac} not connected")
            raise ServerBoxException(ErrorCode.IP_DISCOVERY_UNKNOWN_STATION)
        logger.info(f"Station {mac} connected in {station_ip}")
        return station_ip


ip_discovery_service: IpDiscoveryService = IpDiscoveryService()
""" Ip discovery service singleton"""
