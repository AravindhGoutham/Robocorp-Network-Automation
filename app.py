#!/usr/bin/env python3
from flask import Flask, render_template, request
from jinja2 import Environment, FileSystemLoader
from netmiko import ConnectHandler
from datetime import datetime
import yaml, os

app = Flask(__name__)
env = Environment(loader=FileSystemLoader("templates"))

YAML_DIR = "generated/yamls"
CONFIG_DIR = "generated/configs"
os.makedirs(YAML_DIR, exist_ok=True)
os.makedirs(CONFIG_DIR, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/add_device")
def add_device():
    return render_template("add_device.html")


@app.route("/generate", methods=["POST"])
def generate():
    hostname = request.form.get("hostname")
    username = request.form.get("username")
    password = request.form.get("password")

    # --- Interfaces ---
    interfaces = []
    i_names = request.form.getlist("intf_name[]")
    i_ipv4s = request.form.getlist("intf_ipv4[]")
    i_ipv6s = request.form.getlist("intf_ipv6[]")
    i_modes = request.form.getlist("intf_mode[]")
    i_vlans = request.form.getlist("intf_vlan[]")

    for n, ipv4, ipv6, mode, vlan in zip(i_names, i_ipv4s, i_ipv6s, i_modes, i_vlans):
        if n:
            interfaces.append({
                "name": n,
                "switchport_mode": mode if mode else "no",
                "vlan": vlan if vlan else None,
                "ipv4": ipv4 if ipv4 else None,
                "ipv6": ipv6 if ipv6 else None
            })

    # --- VLANs ---
    vlans = []
    v_ids = request.form.getlist("vlan_id[]")
    v_names = request.form.getlist("vlan_name[]")
    for vid, vname in zip(v_ids, v_names):
        if vid:
            vlans.append({"id": vid, "name": vname})

    # --- OSPF ---
    ospf = {
        "enabled": bool(request.form.get("ospf_process")),
        "process_id": request.form.get("ospf_process"),
        "networks": [n for n in request.form.getlist("ospf_network[]") if n]
    }

    # --- RIP ---
    rip = {
        "enabled": bool(request.form.getlist("rip_network[]")),
        "networks": [n for n in request.form.getlist("rip_network[]") if n]
    }

    # --- BGP ---
    neighbors = []
    bgp_neigh_ips = request.form.getlist("bgp_neigh_ip[]")
    bgp_neigh_as = request.form.getlist("bgp_neigh_as[]")
    for ip, ras in zip(bgp_neigh_ips, bgp_neigh_as):
        if ip:
            neighbors.append({"ip": ip, "remote_as": ras})

    bgp = {
        "enabled": bool(request.form.get("bgp_as")),
        "as_number": request.form.get("bgp_as"),
        "neighbors": neighbors,
        "networks": [{"network": n.split()[0], "mask": n.split()[1]} 
                     for n in request.form.getlist("bgp_network[]") if n]
    }

    # --- Combine All ---
    device_data = {
        "hostname": hostname,
        "username": username,
        "password": password,
        "interfaces": interfaces,
        "vlans": vlans,
        "routing": {"ospf": ospf, "rip": rip, "bgp": bgp}
    }

    # --- Save YAML ---
    yaml_file = os.path.join(YAML_DIR, f"{hostname}.yaml")
    with open(yaml_file, "w") as f:
        yaml.dump(device_data, f, sort_keys=False)

    # --- Render Config ---
    template = env.get_template("base_config.j2")
    rendered_config = template.render(**device_data)

    config_file = os.path.join(CONFIG_DIR, f"{hostname}.cfg")
    with open(config_file, "w") as f:
        f.write(rendered_config)

    return render_template("output.html",
                           hostname=hostname,
                           yaml_content=yaml.dump(device_data, sort_keys=False),
                           rendered_config=rendered_config)


# Golden Configs Page
@app.route("/golden_configs")
def golden_configs():
    """Display all devices from devices.yaml"""
    with open("devices.yaml") as f:
        devices = yaml.safe_load(f)
    return render_template("golden_configs.html", devices=devices)


# Fetch Running Config (Netmiko)
@app.route("/fetch_config/<host>")
def fetch_config(host):
    """SSH into device using devices.yaml and retrieve running config"""
    with open("devices.yaml") as f:
        devices = yaml.safe_load(f)

    device_info = next((d for d in devices if str(d["host"]) == str(host)), None)
    if not device_info:
        return f"<h3>Device {host} not found in devices.yaml</h3>"

    try:
        connection = ConnectHandler(
            device_type=device_info["device_type"],
            host=device_info["host"],
            username=device_info["current_username"],
            password=device_info["current_password"],
            secret=device_info.get("current_password")
        )

        # Enter privileged EXEC mode
        connection.enable()

        # Fetch config
        running_config = connection.send_command("show running-config")
        connection.disconnect()

        # Save fetched config locally
        fetched_dir = "generated/fetched_configs"
        os.makedirs(fetched_dir, exist_ok=True)
        with open(f"{fetched_dir}/{host}_running.txt", "w") as f:
            f.write(running_config)

    except Exception as e:
        running_config = f"Error connecting to {host}\n\n{str(e)}"

    return render_template("running_config.html",
                           host=host,
                           running_config=running_config)

# -------------------------------
# Run Flask App
# -------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
