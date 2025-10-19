#!/usr/bin/env python3
import csv
import ipaddress

def validate_ipv4(ip):
    try:
        if "/" in ip:
            ip_obj = ipaddress.IPv4Interface(ip).ip
        else:
            ip_obj = ipaddress.IPv4Address(ip)

        if ip_obj.is_multicast:
            return f"Invalid {ip} - it is a multicast address"
        if ip_obj.is_loopback:
            return f"Invalid {ip} - it is a loopback address"
        if ip_obj.is_link_local:
            return f"Invalid {ip} - it is a link-local address"
        if ip_obj.is_reserved:
            return f"Invalid {ip} - it is a reserved address"
        if ip_obj == ipaddress.IPv4Address("255.255.255.255"):
            return f"Invalid {ip} - it is a broadcast address"

        return f"Valid {ip}"

    except ValueError:
        return f"Invalid {ip} - it is not a valid IPv4 address"


def get_ipam_data(csv_file):
    records = []
    try:
        with open(csv_file, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(row)
    except FileNotFoundError:
        print(f"Error: {csv_file} not found")
    except Exception as e:
        print(f"Error reading CSV: {e}")
    return records


def main():
    csv_file = "IPAM_Robocorp.csv"
    ipam_data = get_ipam_data(csv_file)
    if not ipam_data:
        print("No records found in CSV.")
        return

    print("\nIP Address Validation Results (from IPAM_Robocorp.csv):\n")
    print(f"{'Hostname':<15} {'Interface':<15} {'CIDR':<20} {'Validation Result'}")
    print("-" * 70)

    for device in ipam_data:
        hostname = device.get("hostname", "Unknown")
        interface = device.get("interface", "Unknown")
        cidr = device.get("cidr", "")
        status = device.get("status", "")

        if cidr:
            result = validate_ipv4(cidr)
            print(f"{hostname:<15} {interface:<15} {cidr:<20} {result}")
        else:
            print(f"{hostname:<15} {interface:<15} {'N/A':<20} No IP found")

if __name__ == "__main__":
    main()
	

