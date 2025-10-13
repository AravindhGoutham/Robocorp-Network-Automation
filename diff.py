#!/usr/bin/env python3

import os
import difflib
import yaml
from netmiko import ConnectHandler, NetMikoTimeoutException, NetMikoAuthenticationException

# --- Global Paths ---
GOLDEN_DIR = "/home/student/Network-Automation/generated/fetched_configs"
DEVICES_FILE = "/home/student/Network-Automation/devices.yaml"


def load_device_info(device_ip):
    """Load device details from devices.yaml"""
    if not os.path.exists(DEVICES_FILE):
        raise FileNotFoundError(f"Device file not found: {DEVICES_FILE}")

    with open(DEVICES_FILE) as f:
        devices = yaml.safe_load(f)

    for device in devices:
        if str(device["host"]) == str(device_ip):
            return device
    raise ValueError(f"Device {device_ip} not found in devices.yaml")


def get_running_config(device):
    """SSH into device and retrieve running configuration"""
    connection = None
    try:
        connection = ConnectHandler(
            device_type=device["device_type"],
            host=device["host"],
            username=device["current_username"],
            password=device["current_password"],
            secret=device.get("current_password", None),
        )
        connection.enable()
        running_config = connection.send_command("show running-config")
        connection.disconnect()
        return running_config

    except NetMikoTimeoutException:
        raise ConnectionError(f"Timeout connecting to {device['host']}")
    except NetMikoAuthenticationException:
        raise ConnectionError(f"Authentication failed for {device['host']}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error: {str(e)}")
    finally:
        if connection:
            connection.disconnect()


def get_golden_config(device_ip):
    """Load golden config from stored file"""
    golden_path = os.path.join(GOLDEN_DIR, f"{device_ip}_running.txt")
    if not os.path.exists(golden_path):
        raise FileNotFoundError(f"No golden config found for {device_ip}")
    with open(golden_path, "r") as f:
        return f.read()


def compare_config_diff(device_ip):
    """
    Perform diff between golden and live running config.
    Returns a formatted diff string.
    """
    device = load_device_info(device_ip)
    running_config = get_running_config(device)
    golden_config = get_golden_config(device_ip)

    # Compute diff
    diff = difflib.unified_diff(
        golden_config.splitlines(),
        running_config.splitlines(),
        fromfile="GOLDEN CONFIG",
        tofile="RUNNING CONFIG",
        lineterm=""
    )

    return "\n".join(diff)


if __name__ == "__main__":
    test_ip = input("Enter device IP to compare: ").strip()
    try:
        result = compare_config_diff(test_ip)
        print(result if result else "No differences found.")
    except Exception as e:
        print(f"Error: {e}")
