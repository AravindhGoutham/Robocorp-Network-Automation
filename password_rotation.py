#!/usr/bin/env python3

import csv
import random
import string
import yaml
from datetime import datetime, UTC
from netmiko import ConnectHandler
import yagmail

LOGFILE = "Device-credentials.txt"
DEVICES_FILE = "devices.yaml"

SMTP_USER = "aravindh.goutham.mahe@gmail.com"
SMTP_APP_PASSWORD = "bgmo ivnj oopn viku"
TO_EMAIL = "aravindh.goutham.mahe@gmail.com"

def rand_pass(length=16):
    chars = string.ascii_letters + string.digits + "!@#$%&*()-_=+"
    return "".join(random.choice(chars) for _ in range(length))

def make_new_username():
    return f"user{datetime.now(UTC).strftime('%Y%m%d')}_{random.randint(10,99)}"

def load_devices():
    with open(DEVICES_FILE, "r") as f:
        return yaml.safe_load(f)

def save_devices(devices):
    with open(DEVICES_FILE, "w") as f:
        yaml.safe_dump(devices, f, sort_keys=False)

def rotate_on_device(dev):
    conn = {
        "host": dev["host"],
        "username": dev["current_username"],
        "password": dev["current_password"],
        "device_type": dev["device_type"],
    }

    new_user = make_new_username()
    new_pass = rand_pass(16)

    cfg_lines = [
        f"no username {dev['current_username']}",
        f"username {new_user} secret {new_pass}"
    ]

    print(f"[{dev['host']}] Connecting as {dev['current_username']}")
    with ConnectHandler(**conn) as net:
        net.enable()
        output = net.send_config_set(cfg_lines)
        print(f"[{dev['host']}] Rotation complete.")
        print(output)

    return new_user, new_pass

def append_csv(timestamp_iso, host, username, password):
    header = ["timestamp_utc", "device", "username", "password"]
    new_file = False
    try:
        with open(LOGFILE, "r"):
            pass
    except FileNotFoundError:
        new_file = True

    with open(LOGFILE, "a", newline="") as f:
        writer = csv.writer(f)
        if new_file:
            writer.writerow(header)
        writer.writerow([timestamp_iso, host, username, password])

def send_email_notification(rotated_data):
    subject = f"Device credentials updated ({datetime.now(UTC).strftime('%m-%d-%Y')})"
    body_lines = ["Daily credential rotation completed.\n\nDetails:"]
    for entry in rotated_data:
        body_lines.append(
            f"Device: {entry['device']} | Username: {entry['username']} | Password: {entry['password']} | Time: {entry['timestamp']}"
        )
    body = "\n".join(body_lines)

    yag = yagmail.SMTP(SMTP_USER, SMTP_APP_PASSWORD)
    yag.send(to=TO_EMAIL, subject=subject, contents=body)
    print(f"Email sent to {TO_EMAIL}")

def main():
    devices = load_devices()
    rotated_info = []

    for dev in devices:
        try:
            new_user, new_pass = rotate_on_device(dev)
            ts = datetime.now(UTC).isoformat()
            append_csv(ts, dev["host"], new_user, new_pass)
            print(f"[{dev['host']}] Logged credentials to {LOGFILE}")

            rotated_info.append({
                "device": dev["host"],
                "username": new_user,
                "password": new_pass,
                "timestamp": ts
            })

            dev["current_username"] = new_user
            dev["current_password"] = new_pass

        except Exception as e:
            print(f"[{dev['host']}] ERROR: {e}")

    save_devices(devices)
    print("devices.yaml updated with latest credentials.")

    if rotated_info:
        send_email_notification(rotated_info)

if __name__ == "__main__":
    main()
