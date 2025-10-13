#!/usr/bin/env python3
import yaml
from netmiko import ConnectHandler, NetMikoTimeoutException, NetMikoAuthenticationException
import questionary
from rich.console import Console
from rich.table import Table

console = Console()

# Load device info from YAML
with open("devices.yaml") as f:
    devices = yaml.safe_load(f)

# Build menu with host IPs
device_choices = [device['host'] for device in devices] + ["Quit"]

def get_device_by_ip(ip):
    for d in devices:
        if d['host'] == ip:
            return d
    return None

def run_health_check(ip):
    device_info = get_device_by_ip(ip)
    if not device_info:
        console.print(f"[bold red]Device with IP {ip} not found[/bold red]")
        return

    # Map YAML fields to Netmiko fields
    device = {
        "host": device_info['host'],
        "device_type": device_info['device_type'],
        "username": device_info['current_username'],
        "password": device_info['current_password']
    }

    console.print(f"[bold cyan]Connecting to {ip}[/bold cyan]")

    try:
        conn = ConnectHandler(**device)
    except NetMikoTimeoutException:
        console.print(f"[bold red]Timeout connecting to {ip}[/bold red]")
        return
    except NetMikoAuthenticationException:
        console.print(f"[bold red]Authentication failed for {ip}[/bold red]")
        return

    # Commands to run
    cmds = {
        "IP Route": "show ip route",
        "OSPF Neighbors": "show ip ospf neighbor",
        "BGP Summary": "show ip bgp summary",
   	"Interface Status": "show ip int brief"
    }

    table = Table(
        title=f"Health Check for {ip}",
        show_lines=True,
        expand=True
    )
    table.add_column("Check", style="cyan", no_wrap=True)
    table.add_column("Result", style="green", overflow="fold")

    for label, cmd in cmds.items():
        try:
            output = conn.send_command(cmd)
            table.add_row(label, output)
        except Exception as e:
            table.add_row(label, f"[red]Error: {str(e)}[/red]")

    console.print(table)
    conn.disconnect()

if __name__ == "__main__":
    while True:
        choice = questionary.select(
            "Choose the device IP you want to check or quit:",
            choices=device_choices
        ).ask()

        if choice == "Quit" or choice is None:
            console.print("[bold yellow]Exiting NetHealth[/bold yellow]")
            break

        run_health_check(choice)
