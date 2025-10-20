#!/usr/bin/env python3
import os
import csv
import pytest
import yaml
from unittest import mock
from datetime import datetime, UTC

import password_rotation as pr


# -------------------------------
# Fixtures & Helpers
# -------------------------------

@pytest.fixture
def sample_devices(tmp_path):
    """Create a temporary devices.yaml file with fake data."""
    devices = [
        {
            "host": "10.0.0.1",
            "device_type": "cisco_ios",
            "current_username": "admin",
            "current_password": "admin",
        },
        {
            "host": "10.0.0.2",
            "device_type": "arista_eos",
            "current_username": "user1",
            "current_password": "pass1",
        },
    ]
    yaml_file = tmp_path / "devices.yaml"
    with open(yaml_file, "w") as f:
        yaml.safe_dump(devices, f)
    return yaml_file


@pytest.fixture
def temp_log(tmp_path):
    """Return path for temporary log file."""
    return tmp_path / "Device-credentials.txt"


# -------------------------------
# Test Functions
# -------------------------------

def test_rand_pass_length_and_charset():
    password = pr.rand_pass(12)
    assert len(password) == 12
    # Contains at least one letter, digit, and symbol
    assert any(c.isdigit() for c in password)
    assert any(c.isalpha() for c in password)
    assert any(c in "!@#$%&*()-_=+" for c in password)


def test_make_new_username_format():
    username = pr.make_new_username()
    assert username.startswith("user")
    assert "_" in username


def test_load_and_save_devices(sample_devices):
    pr.DEVICES_FILE = str(sample_devices)
    devices = pr.load_devices()
    assert isinstance(devices, list)
    assert "host" in devices[0]

    # Modify and save
    devices[0]["current_username"] = "newuser"
    pr.save_devices(devices)

    with open(sample_devices) as f:
        loaded = yaml.safe_load(f)
    assert loaded[0]["current_username"] == "newuser"


@mock.patch("password_rotation.ConnectHandler")
def test_rotate_on_device(mock_conn):
    """Mock SSH connection to test password rotation logic."""
    fake_dev = {
        "host": "10.0.0.3",
        "device_type": "cisco_ios",
        "current_username": "admin",
        "current_password": "admin123",
    }

    # Create a fake Netmiko session mock
    mock_instance = mock.Mock()
    mock_instance.send_config_set.return_value = "Config done"
    mock_conn.return_value.__enter__.return_value = mock_instance

    new_user, new_pass = pr.rotate_on_device(fake_dev)
    assert new_user.startswith("user")
    assert len(new_pass) >= 8
    mock_instance.send_config_set.assert_called_once()


def test_append_csv(temp_log):
    ts = datetime.now(UTC).isoformat()
    pr.LOGFILE = str(temp_log)
    pr.append_csv(ts, "10.0.0.1", "user_test", "pass_test")

    with open(temp_log, newline="") as f:
        reader = list(csv.reader(f))
    assert reader[-1][1] == "10.0.0.1"
    assert "user_test" in reader[-1]
    assert os.path.exists(temp_log)


@mock.patch("password_rotation.yagmail.SMTP")
def test_send_email_notification(mock_yag):
    """Test that email notification sends with correct subject."""
    fake_rotated = [
        {"device": "10.0.0.1", "username": "userA", "password": "pwA", "timestamp": "2025-10-19T10:00Z"}
    ]
    pr.send_email_notification(fake_rotated)

    mock_yag.assert_called_once_with(pr.SMTP_USER, pr.SMTP_APP_PASSWORD)
    smtp_instance = mock_yag.return_value
    smtp_instance.send.assert_called_once()
    args, kwargs = smtp_instance.send.call_args
    assert pr.TO_EMAIL in kwargs["to"]
    assert "Device credentials updated" in kwargs["subject"]


@mock.patch("password_rotation.rotate_on_device", return_value=("newU", "newP"))
@mock.patch("password_rotation.append_csv")
@mock.patch("password_rotation.send_email_notification")
def test_main_flow(mock_email, mock_csv, mock_rotate, sample_devices, tmp_path):
    """Test the full main() logic without real SSH or emails."""
    pr.DEVICES_FILE = str(sample_devices)
    pr.LOGFILE = str(tmp_path / "Device-credentials.txt")

    pr.main()

    # After main() runs, devices.yaml should be updated with new creds
    with open(sample_devices) as f:
        devices = yaml.safe_load(f)
    assert all(d["current_username"].startswith("user") or d["current_username"] == "newU" for d in devices)

    mock_email.assert_called_once()
