#!/usr/bin/env python3
import yaml
from netmiko import ConnectHandler, NetMikoTimeoutException, NetMikoAuthenticationException
from prettytable import PrettyTable

YAML_FILE = "devices.yaml"
NMAS_IP = "10.0.0.1"  # IP to ping from each device

def load_devices(file_path):
    """Load device credentials from YAML file"""
    try:
        with open(file_path, "r") as f:
            devices = yaml.safe_load(f)
        if not devices:
            print("[ERROR] devices.yaml is empty or invalid.")
            return []
        return devices
    except FileNotFoundError:
        print(f"[ERROR] {file_path} not found.")
        return []
    except yaml.YAMLError as e:
        print(f"[ERROR] Failed to parse YAML: {e}")
        return []

def check_ssh(dev):
    """Check SSH connectivity and NMAS ping"""
    device = {
        "host": dev["host"],
        "device_type": dev["device_type"],
        "username": dev["current_username"],
        "password": dev["current_password"],
    }

    try:
        conn = ConnectHandler(**device)
    except NetMikoTimeoutException:
        return ("Timeout", "N/A")
    except NetMikoAuthenticationException:
        return ("Authentication Failed", "N/A")
    except Exception as e:
        return (f"SSH Error: {str(e)}", "N/A")

    # SSH connected successfully — now ping NMAS
    try:
        output = conn.send_command(f"ping {NMAS_IP}")
        if "Success" in output or "bytes from" in output or "100% success" in output:
            ping_status = "Reachable"
        else:
            ping_status = "Unreachable"
    except Exception as e:
        ping_status = f"Ping Error: {str(e)}"

    conn.disconnect()
    return ("SSH OK", ping_status)

def main():
    devices = load_devices(YAML_FILE)
    if not devices:
        return

    table = PrettyTable()
    table.field_names = ["Host", "Username", "SSH Status", f"Ping {NMAS_IP}"]

    print("Checking SSH connectivity and NMAS reachability...\n")

    for dev in devices:
        host = dev["host"]
        username = dev["current_username"]
        ssh_status, ping_status = check_ssh(dev)
        table.add_row([host, username, ssh_status, ping_status])

    print(table)

if __name__ == "__main__":
    main()
