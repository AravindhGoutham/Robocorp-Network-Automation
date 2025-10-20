#!/usr/bin/env python3
import os
import csv
import pytest
from ipvalidate import validate_ipv4, get_ipam_data


def test_valid_ip():
    result = validate_ipv4("192.168.1.1")
    assert "Valid" in result

def test_valid_ip_with_cidr():
    result = validate_ipv4("10.0.0.1/24")
    assert "Valid" in result

def test_invalid_ip_format():
    result = validate_ipv4("999.999.999.999")
    assert "Invalid" in result and "not a valid IPv4 address" in result

def test_loopback_ip():
    result = validate_ipv4("127.0.0.1")
    assert "loopback" in result

def test_multicast_ip():
    result = validate_ipv4("224.0.0.1")
    assert "multicast" in result

def test_broadcast_ip():
    result = validate_ipv4("255.255.255.255")
    assert "broadcast" in result


def test_get_ipam_data_valid_csv(tmp_path):
    data = [
        {"hostname": "R1", "interface": "Eth0", "cidr": "10.0.0.1/24", "status": "up"},
        {"hostname": "R2", "interface": "Eth1", "cidr": "10.0.0.2/24", "status": "up"}
    ]
    csv_file = tmp_path / "IPAM_Robocorp.csv"
    with open(csv_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["hostname", "interface", "cidr", "status"])
        writer.writeheader()
        writer.writerows(data)

    result = get_ipam_data(csv_file)
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["hostname"] == "R1"
    assert result[1]["cidr"] == "10.0.0.2/24"

def test_get_ipam_data_file_not_found(capsys):
    result = get_ipam_data("nonexistent.csv")
    captured = capsys.readouterr()
    assert result == []
    assert "not found" in captured.out


def test_get_ipam_data_invalid_format(tmp_path, capsys):
    # Create a malformed CSV file
    csv_file = tmp_path / "bad.csv"
    with open(csv_file, "w") as f:
        f.write("hostname,interface,cidr\nR1,Eth0,10.0.0.1/24\nR2")

    result = get_ipam_data(csv_file)
    assert isinstance(result, list)
    captured = capsys.readouterr()
    assert "Error reading CSV" not in captured.out
