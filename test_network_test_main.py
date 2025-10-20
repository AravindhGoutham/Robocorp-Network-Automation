#!/usr/bin/env python3

import builtins
import network_tests
from unittest.mock import MagicMock

def test_main_runs_successfully(monkeypatch):
    """Test the main() function of network_tests.py"""

    # Mock yaml.safe_load to return fake device data
    fake_devices = [
        {
            "host": "10.0.0.2",
            "device_type": "arista_eos",
            "current_username": "user",
            "current_password": "pass"
        },
        {
            "host": "10.0.0.3",
            "device_type": "arista_eos",
            "current_username": "user",
            "current_password": "pass"
        }
    ]
    monkeypatch.setattr("yaml.safe_load", lambda f=None: fake_devices)

    # Mock run_ping to simulate success/failure
    def fake_run_ping(device, target):
        if device["host"] == "10.0.0.2":
            return True, "Success"
        else:
            return False, "100 percent loss"

    monkeypatch.setattr(network_tests, "run_ping", fake_run_ping)

    # Mock print to silence console output
    monkeypatch.setattr(builtins, "print", lambda *a, **k: None)

    # Prevent exit(1) from actually stopping pytest
    monkeypatch.setattr("builtins.exit", lambda x=None: None)

    # Run the main function
    network_tests.main()

