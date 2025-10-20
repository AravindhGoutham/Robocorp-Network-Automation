#!/usr/bin/env python3

import builtins
import ipvalidate
from unittest.mock import mock_open, patch

def test_main_runs_with_valid_and_invalid_ips(monkeypatch):
    """Test that ipvalidate.main() runs end-to-end with mixed IPs."""

    # Prepare fake CSV data
    csv_content = (
        "hostname,interface,cidr\n"
        "R1,Ethernet1,10.0.0.1/24\n"
        "R2,Ethernet2,127.0.0.1/32\n"
        "R3,Ethernet3,224.0.0.1/32\n"
        "R4,Ethernet4,255.255.255.255/32\n"
    )

    # Patch open() for the CSV file
    with patch("builtins.open", mock_open(read_data=csv_content)):
        # Patch print to silence console output
        monkeypatch.setattr(builtins, "print", lambda *a, **k: None)

        # Run the main() function
        ipvalidate.main()


def test_validate_ipv4_all_special_cases():
    """Test all special IP cases to cover each condition."""

    assert "multicast" in ipvalidate.validate_ipv4("224.0.0.1")
    assert "loopback" in ipvalidate.validate_ipv4("127.0.0.1")
    assert "link-local" in ipvalidate.validate_ipv4("169.254.0.1")
    assert "reserved" in ipvalidate.validate_ipv4("240.0.0.1")
    assert "broadcast" in ipvalidate.validate_ipv4("255.255.255.255")
    assert "Valid" in ipvalidate.validate_ipv4("192.168.1.1")
    assert "not a valid IPv4" in ipvalidate.validate_ipv4("invalid_ip")

