#!/usr/bin/env python3

from unittest.mock import patch, MagicMock
import routing_healthcheck

@patch("routing_healthcheck.ConnectHandler")
def test_connect_device_success(mock_conn):
    mock_conn.return_value.enable.return_value = None
    conn = routing_healthcheck.connect_device({
        "device_type": "arista_eos",
        "host": "10.0.0.8",
        "current_username": "user",
        "current_password": "pass"
    })
    assert conn is not None

@patch("routing_healthcheck.ConnectHandler", side_effect=Exception("SSH fail"))
def test_connect_device_failure(mock_conn):
    result = routing_healthcheck.connect_device({
        "device_type": "arista_eos",
        "host": "10.0.0.9",
        "current_username": "user",
        "current_password": "pass"
    })
    assert "failed" in result.lower()

def test_test_ospf_pass():
    mock_conn = MagicMock()
    mock_conn.send_command.return_value = "FULL adjacency"
    result = routing_healthcheck.test_ospf(mock_conn)
    assert result == "PASS"

def test_test_ospf_fail():
    mock_conn = MagicMock()
    mock_conn.send_command.return_value = "DOWN"
    result = routing_healthcheck.test_ospf(mock_conn)
    assert result == "FAIL"

def test_test_bgp_pass():
    mock_conn = MagicMock()
    mock_conn.send_command.return_value = "Established"
    result = routing_healthcheck.test_bgp(mock_conn)
    assert result == "PASS"

def test_test_bgp_fail():
    mock_conn = MagicMock()
    mock_conn.send_command.return_value = "Idle"
    result = routing_healthcheck.test_bgp(mock_conn)
    assert result == "FAIL"
