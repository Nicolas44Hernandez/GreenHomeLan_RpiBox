""" Server box errors """

from enum import Enum


class ErrorCode(Enum):
    """Enumerate which gather all data about possible errors"""

    # Please enrich this enumeration in order to handle other kind of errors
    UNEXPECTED_ERROR = (0, 500, "Unexpected error occurs")
    TELNET_CONNECTION_ERROR = (1, 500, "Error in Telnet connection")
    TELNET_COMMANDS_FILE_ERROR = (
        2,
        500,
        "Error in telnet commands load, check commands file",
    )
    TELNET_COMMAND_NOT_FOUND = (3, 500, "Telnet command not found, check config")
    UNKNOWN_BAND_WIFI = (4, 400, "Wifi band doesnt exist")
    MODULE_NOT_FOUND = (5, 400, "Module not found in RPI box")
    STATUS_CHANGE_TIMER = (
        6,
        500,
        "Wifi status change is taking too long, verify wifi status",
    )
    THREAD_CONFIG_FILE_ERROR = (
        7,
        500,
        "Error in Thread configuration load, check file",
    )
    THREAD_NODE_NOT_CONFIGURED = (
        8,
        400,
        "Thread node not configured, check thread config file",
    )
    INVALID_RELAY_NUMBER = (9, 400, "Invalid relay number")
    RELAYS_STATUS_NOT_RECEIVED = (
        10,
        400,
        "The relays status have not been received yet",
    )
    THREAD_NODE_UNREACHABLE = (
        11,
        500,
        "Node server is unreachable, check if node is running",
    )
    THREAD_NETWORK_SETUP_ERROR = (12, 500, "Thread network configuration error")
    USE_SITUATIONS_CONFIG_FILE_ERROR = (
        13,
        500,
        "Error in Use situations configuration load, check file",
    )
    INVALID_USE_SITUATION = (14, 400, "Invalid use situation selected")
    THREAD_NETWORK_NOT_RUNNING = (15, 500, "Thread network is not running")
    ERROR_IN_PREDICTOR_MODEL_LOAD = (
        16,
        500,
        "Error in 5GHZ ON/OFF rtt predictor model load",
    )
    ORCHESTRATOR_COMMANDS_FILE_ERROR = (
        17,
        500,
        "Error in orchestrator commands load, check commands file",
    )
    INVALID_ENERGY_RECOMMENDATION_DATETIME = (
        18,
        400,
        "Invalid energy recommendation datetime",
    )
    INVALID_ENERGY_RECOMMENDATION_ARGS = (
        19,
        400,
        "Invalid energy recommendation arguments for this client",
    )

    # pylint: disable=unused-argument
    def __new__(cls, *args, **kwds):
        """Custom new in order to initialize properties"""
        obj = object.__new__(cls)
        obj._value_ = args[0]
        obj._http_code_ = args[1]
        obj._message_ = args[2]
        return obj

    @property
    def http_code(self):
        """The http code corresponding to the error"""
        return self._http_code_

    @property
    def message(self):
        """The message corresponding to the error"""
        return self._message_
