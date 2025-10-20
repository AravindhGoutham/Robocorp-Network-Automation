#!/usr/bin/env python3

from unittest.mock import patch, MagicMock
import os
import ssh_check

def test_load_devices_file_not_found(monkeypatch):
    monkeypatch.setattr("builtins.print", lambda *a, **kw: None)
    result = ssh_check.load_devices("nope.yaml")
    assert result == []

def test_load_devices_yaml_error(tmp_path, monkeypatch):
    bad_yaml = tmp_path / "bad.yaml"
    bad_yaml.write_text("::::")
    monkeypatch.setattr("builtins.print", lambda *a, **kw: None)
    result = ssh_check.load_devices(str(bad_yaml))
    assert isinstance(result, list)

@patch("ssh_check.ConnectHandler")
def test_check_ssh_success(mock_conn):
    mock_conn.return_value.send_command.return_value = "Success"
    device = {"host": "10.0.0.2","device_type": "arista_eos","current_username": "u","current_password": "p"}
    status, ping = ssh_check.check_ssh(device)
    assert status == "SSH OK" and ping == "Reachable"

@patch("ssh_check.ConnectHandler", side_effect=Exception("Auth fail"))
def test_check_ssh_exception(mock_conn):
    device = {"host": "10.0.0.2","device_type": "arista_eos","current_username": "u","current_password": "p"}
    status, ping = ssh_check.check_ssh(device)
    assert "Error" in status

@patch("ssh_check.ConnectHandler")
def test_check_ssh_unreachable_ping(mock_conn):
    mock_conn.return_value.send_command.return_value = "Unreachable"
    device = {"host": "10.0.0.2","device_type": "arista_eos","current_username": "u","current_password": "p"}
    status, ping = ssh_check.check_ssh(device)
    assert ping == "Unreachable"
