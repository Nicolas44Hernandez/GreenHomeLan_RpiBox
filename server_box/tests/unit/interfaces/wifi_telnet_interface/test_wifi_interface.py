"""Wifi interface unit tests"""
import logging
import pytest
from server.interfaces.wifi_interface_telnet import wifi_telnet_interface
from server.common import ServerBoxException

HOST_LOGIN = "nicolas"
HOST_PASSWORD = "Nico44"


@pytest.fixture(scope="function")
def telnet():
    telnet_service = wifi_telnet_interface(
        host="localhost",
        port=23,
        login=HOST_LOGIN,
        password=HOST_PASSWORD,
        telnet_timeout_in_secs=5,
    )
    yield telnet_service
    telnet_service.close()


logger = logging.getLogger(__name__)


def test_create_telnet_connection():
    # GIVEN
    host = "localhost"
    port = 23
    login = HOST_LOGIN
    password = HOST_PASSWORD
    telnet_timeout_in_secs = 5

    # WHEN
    telnet = wifi_telnet_interface(host, port, login, password, telnet_timeout_in_secs)

    # THEN
    assert not telnet.connection.sock._closed
    telnet.close()


def test_create_telnet_connection_KO():
    # GIVEN
    host = "wronghost"
    port = 23
    login = "login"
    password = "pw"
    telnet_timeout_in_secs = 5

    # WHEN / THEN
    with pytest.raises(ServerBoxException):
        wifi_telnet_interface(host, port, login, password, telnet_timeout_in_secs)


def test_create_superuser_session(telnet):
    # GIVEN
    login = HOST_LOGIN
    password = HOST_PASSWORD

    # WHEN
    assert not telnet.super_user_session
    telnet.create_super_user_session()

    # THEN
    assert telnet.super_user_session


# TODO: Update test
def test_send_command(telnet):
    # GIVEN
    command = "echo test-send-command"

    # WHEN
    telnet.send_command(command)

    # THEN
    # No exception raised


def test_parce_telnet_output():
    pass


def test_get_command_output():
    pass
