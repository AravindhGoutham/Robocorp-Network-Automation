#!/usr/bin/env python3
import yaml
from netmiko import ConnectHandler

DEVICES_FILE = "devices.yaml"

OSPF_DEVICES = ["10.0.0.4", "10.0.0.5", "10.0.0.6", "10.0.0.7", "10.0.0.8", "10.0.0.9"]
BGP_DEVICES = ["10.0.0.8", "10.0.0.9"]


def connect_device(device):
    try:
        connection = ConnectHandler(
            device_type=device["device_type"],
            host=device["host"],
            username=device["current_username"],
            password=device["current_password"],
            secret=device.get("current_password"),
        )
        connection.enable()
        return connection
    except Exception as e:
        return f"Connection failed: {str(e)}"


def test_ospf(connection):
    output = connection.send_command("show ip ospf neighbor")
    result = "PASS" if "FULL" in output else "FAIL"
    return result


def test_bgp(connection):
    output = connection.send_command("show ip bgp summary")
    lower_out = output.lower()
    if "established" in lower_out or "estab" in lower_out:
        result = "PASS"
    else:
        result = "FAIL"
    return result



def main():
    with open(DEVICES_FILE) as f:
        devices = yaml.safe_load(f)

    overall_ok = True

    print("\n=== Routing Health Check ===\n")

    for device in devices:
        host = device["host"]
        if host not in OSPF_DEVICES + BGP_DEVICES:
            continue

        print(f"--- Device {host} ---")

        conn = connect_device(device)
        if isinstance(conn, str):
            print(conn)
            overall_ok = False
            continue

        if host in OSPF_DEVICES:
            result = test_ospf(conn)
            print(f"OSPF Neighborship: {result}")
            if result == "FAIL":
                overall_ok = False

        if host in BGP_DEVICES:
            result = test_bgp(conn)
            print(f"BGP Neighborship: {result}")
            if result == "FAIL":
                overall_ok = False

        conn.disconnect()
        print()

    print("=== End of Routing Health Check ===\n")

    if not overall_ok:
        exit(1)


if __name__ == "__main__":
    main()
