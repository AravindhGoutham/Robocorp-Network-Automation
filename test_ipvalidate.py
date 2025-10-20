#!/usr/bin/env python3

import ipvalidate
import builtins
import io
import csv
import os

def test_validate_ipv4_valid():
    assert "Valid" in ipvalidate.validate_ipv4("192.168.1.1/24")

def test_validate_ipv4_invalid():
    result = ipvalidate.validate_ipv4("999.999.999.999")
    assert "not a valid IPv4" in result

def test_validate_ipv4_loopback():
    result = ipvalidate.validate_ipv4("127.0.0.1")
    assert "loopback" in result

def test_get_ipam_data_missing_file(monkeypatch):
    monkeypatch.setattr(builtins, "print", lambda *a, **kw: None)
    result = ipvalidate.get_ipam_data("nonexistent.csv")
    assert result == []

def test_get_ipam_data_reads_file(tmp_path):
    file = tmp_path / "test.csv"
    file.write_text("hostname,interface,cidr,status\nR1,Eth0,10.0.0.1/24,up\n")
    result = ipvalidate.get_ipam_data(str(file))
    assert result[0]["cidr"] == "10.0.0.1/24"

def test_main_with_empty_csv(tmp_path, monkeypatch):
    file = tmp_path / "empty.csv"
    file.write_text("")
    monkeypatch.setattr("ipvalidate.get_ipam_data", lambda x: [])
    monkeypatch.setattr(builtins, "print", lambda *a, **kw: None)
    ipvalidate.main()
