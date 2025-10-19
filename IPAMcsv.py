#!/usr/bin/env python3

import csv
import yaml
from netmiko import ConnectHandler
from prettytable import PrettyTable

DEVICES_FILE = "devices.yaml"
OUTPUT_FILE = f"IPAM_Robocorp.csv"


def parse_interfaces(output):
    interfaces = []
    lines = output.strip().splitlines()

    for line in lines:
        if line.lower().startswith(("interface", "---")) or not line.strip():
            continue

        parts = line.split()
        if len(parts) < 3:
            continue

        intf = parts[0]
        ip_addr = parts[1]
        status = parts[2]

        if "unassigned" in ip_addr.lower():
            continue

        if "/" in ip_addr:
            cidr = ip_addr
        else:
            cidr = f"{ip_addr}/?"

        interfaces.append({
            "interface": intf,
            "cidr": cidr,
            "status": status
        })

    return interfaces


def discover_device(device):
    try:
        conn = ConnectHandler(**device)
        hostname = device["host"]
        print(f"Connecting to {hostname}")

        output = conn.send_command("show ip interface brief")
        interfaces = parse_interfaces(output)

        for intf in interfaces:
            intf["hostname"] = hostname

        conn.disconnect()
        print(f"Collected {len(interfaces)} interfaces from {hostname}")
        return interfaces

    except Exception as e:
        print(f"Failed to connect {device['host']}: {e}")
        return []


def main():
    # Load device info
    with open(DEVICES_FILE) as f:
        devices = yaml.safe_load(f)

    all_data = []

    for device in devices:
        device_info = {
            "device_type": device.get("device_type", "arista_eos"),
            "host": device["host"],
            "username": device["current_username"],
            "password": device["current_password"]
        }
        interfaces = discover_device(device_info)
        all_data.extend(interfaces)

    if not all_data:
        print(" No data collected.")
        return

    table = PrettyTable()
    table.field_names = ["Hostname", "Interface", "IP/Subnet", "Status"]
    for row in all_data:
        table.add_row([row["hostname"], row["interface"], row["cidr"], row["status"]])

    print("\nDynamic IPAM Discovery Table\n")
    print(table)

    with open(OUTPUT_FILE, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["hostname", "interface", "cidr", "status"])
        writer.writeheader()
        writer.writerows(all_data)

    print(f"\nSaved results to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
