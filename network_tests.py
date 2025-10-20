#!/usr/bin/env python3
import yaml
from netmiko import ConnectHandler

DEVICES_FILE = "devices.yaml"
PING_TARGET = "8.8.8.8"


def run_ping(device, target):
    try:
        connection = ConnectHandler(
            device_type=device["device_type"],
            host=device["host"],
            username=device["current_username"],
            password=device["current_password"],
            secret=device.get("current_password"),
        )
        connection.enable()
        output = connection.send_command(f"ping {target}", expect_string=r"#|Success|Loss")
        connection.disconnect()

        if "100 percent loss" in output.lower() or "unreachable" in output.lower():
            return False, output
        return True, output

    except Exception as e:
        return False, f"Connection failed: {str(e)}"


def main():
    with open(DEVICES_FILE) as f:
        devices = yaml.safe_load(f)

    success_all = True

    print("\n=== Webserver Ping Test ===\n")

    for device in devices:
        host = device["host"]
        print(f"Testing {host} -> {PING_TARGET}", end="", flush=True)

        success, output = run_ping(device, PING_TARGET)
        status = "PASS" if success else "FAIL"
        print(status)

        if not success:
            success_all = False


    if not success_all:
        exit(1)


if __name__ == "__main__":
    main()
