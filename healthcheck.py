#!/usr/bin/env python3
import yaml
from netmiko import ConnectHandler, NetMikoTimeoutException, NetMikoAuthenticationException

def run_health_check(ip):
    with open("devices.yaml") as f:
        devices = yaml.safe_load(f)

    device_info = next((d for d in devices if str(d["host"]) == str(ip)), None)
    if not device_info:
        return f"Device with IP {ip} not found"

    device = {
        "host": device_info["host"],
        "device_type": device_info["device_type"],
        "username": device_info["current_username"],
        "password": device_info["current_password"]
    }

    try:
        conn = ConnectHandler(**device)
    except NetMikoTimeoutException:
        return f"[ERROR] Timeout connecting to {ip}"
    except NetMikoAuthenticationException:
        return f"[ERROR] Authentication failed for {ip}"
    except Exception as e:
        return f"[ERROR] {str(e)}"

    # Commands to run
    cmds = {
        "IP Route": "show ip route",
        "OSPF Neighbors": "show ip ospf neighbor",
        "BGP Summary": "show ip bgp summary",
        "Interface Status": "show ip int brief",
        "Webserver Reachability": "ping 8.8.8.8"
    }

    results = {}
    for label, cmd in cmds.items():
        try:
            output = conn.send_command(cmd)
            results[label] = output
        except Exception as e:
            results[label] = f"Error: {str(e)}"

    conn.disconnect()
    return results
