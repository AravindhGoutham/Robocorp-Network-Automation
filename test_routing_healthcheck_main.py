#!/usr/bin/env python3

import builtins
import routing_healthcheck
from unittest.mock import MagicMock

def test_main_runs_successfully(monkeypatch):
    """Test that routing_healthcheck.main() executes without errors."""

    # Mock yaml.safe_load to return a fake list of devices
    fake_devices = [
        {"host": "10.0.0.4", "device_type": "arista_eos", "current_username": "user", "current_password": "pass"},
        {"host": "10.0.0.8", "device_type": "arista_eos", "current_username": "user", "current_password": "pass"},
    ]
    monkeypatch.setattr("yaml.safe_load", lambda f=None: fake_devices)

    # Mock ConnectHandler so it doesn't SSH anywhere
    fake_conn = MagicMock()

    def fake_send_command(cmd):
        if "ospf" in cmd:
            return "Neighbor FULL"
        elif "bgp" in cmd:
            return "BGP state Established"
        else:
            return ""

    fake_conn.send_command.side_effect = fake_send_command
    fake_conn.disconnect.return_value = None

    # Patch ConnectHandler to use the fake connection
    monkeypatch.setattr("routing_healthcheck.ConnectHandler", lambda **kwargs: fake_conn)

    # Prevent exit(1) from stopping pytest
    monkeypatch.setattr("builtins.exit", lambda x=None: None)

    # Mock print to silence console output
    monkeypatch.setattr(builtins, "print", lambda *a, **k: None)

    # Run the main function
    routing_healthcheck.main()
