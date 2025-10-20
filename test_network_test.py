#!/usr/bin/env python3

from unittest.mock import patch, MagicMock
import network_tests

@patch("network_tests.ConnectHandler")
def test_run_ping_success(mock_conn):
    mock_conn.return_value.send_command.return_value = "Success rate is 100 percent"
    device = {
        "device_type": "arista_eos",
        "host": "10.0.0.2",
        "current_username": "user",
        "current_password": "pass"
    }
    ok, output = network_tests.run_ping(device, "8.8.8.8")
    assert ok and "Success" in output

@patch("network_tests.ConnectHandler")
def test_run_ping_fail(mock_conn):
    mock_conn.return_value.send_command.return_value = "100 percent loss"
    device = {"device_type": "arista_eos","host": "10.0.0.2","current_username": "u","current_password": "p"}
    ok, output = network_tests.run_ping(device, "8.8.8.8")
    assert not ok

@patch("network_tests.ConnectHandler", side_effect=Exception("SSH failed"))
def test_run_ping_exception(mock_conn):
    device = {"device_type": "arista_eos","host": "10.0.0.2","current_username": "u","current_password": "p"}
    ok, output = network_tests.run_ping(device, "8.8.8.8")
    assert not ok
    assert "failed" in output.lower()
