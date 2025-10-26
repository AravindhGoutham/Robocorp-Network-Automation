#!/usr/bin/env python3
from flask import Flask, render_template, request
from jinja2 import Environment, FileSystemLoader
from netmiko import ConnectHandler
from datetime import datetime
from healthcheck import run_health_check
import yaml, os, csv
from diff import compare_config_diff
from ipvalidate import validate_ipv4

app = Flask(__name__)
env = Environment(loader=FileSystemLoader("templates"))

YAML_DIR = "generated/yamls"
CONFIG_DIR = "generated/configs"
IPAM_FILE = "IPAM_Robocorp.csv"

os.makedirs(YAML_DIR, exist_ok=True)
os.makedirs(CONFIG_DIR, exist_ok=True)


# ---- Check for duplicate IPs in IPAM ----
def ip_exists_in_ipam(ip):
    if not os.path.exists(IPAM_FILE):
        return False

    try:
        ip_input = ip.split("/")[0]
        with open(IPAM_FILE, newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                ip_field = (
                    row.get("ip_address") or
                    row.get("cidr") or
                    row.get("IP") or
                    row.get("ip")
                )
                if ip_field:
                    ip_csv = ip_field.split("/")[0]
                    if ip_csv == ip_input:
                        return True
        return False
    except Exception as e:
        print(f"Error reading IPAM file: {e}")
        return False


@app.route("/")
def index():
    return render_template("index.html")


# ---- Config Diff ----
@app.route("/config_diff", methods=["GET", "POST"])
def config_diff():
    with open("devices.yaml") as f:
        devices = yaml.safe_load(f)

    if request.method == "POST":
        device_ip = request.form.get("device_ip")
        try:
            diff_output = compare_config_diff(device_ip)
            return render_template(
                "config_diff_result.html",
                device_ip=device_ip,
                diff_output=diff_output
            )
        except Exception as e:
            return f"<h3 style='color:red;'>Error: {e}</h3>"

    return render_template("config_diff.html", devices=devices)


# ---- Add Device ----
@app.route("/add_device")
def add_device():
    return render_template("add_device.html")


# ---- Health Check ----
@app.route("/healthcheck", methods=["GET", "POST"])
def healthcheck():
    with open("devices.yaml") as f:
        devices = yaml.safe_load(f)

    if request.method == "POST":
        ip = request.form.get("device_ip")
        results = run_health_check(ip)
        return render_template("health_results.html", ip=ip, results=results)

    return render_template("healthcheck.html", devices=devices)


# ---- Generate Config ----
@app.route("/generate", methods=["POST"])
def generate():
    hostname = request.form.get("hostname")
    username = request.form.get("username")
    password = request.form.get("password")

    # ---------- Interfaces ----------
    interfaces = []
    i_names = request.form.getlist("intf_name[]")
    i_ipv4s = request.form.getlist("intf_ipv4[]")
    i_ipv6s = request.form.getlist("intf_ipv6[]")
    i_modes = request.form.getlist("intf_mode[]")
    i_vlans = request.form.getlist("intf_vlan[]")

    invalid_ips = []
    duplicate_ips = []

    for ip in i_ipv4s:
        if ip:
            result = validate_ipv4(ip)
            if "Invalid" in result:
                invalid_ips.append(result)
            elif ip_exists_in_ipam(ip):
                duplicate_ips.append(f"Duplicate {ip} - already exists in IPAM")

    if invalid_ips or duplicate_ips:
        errors = invalid_ips + duplicate_ips
        return render_template("error.html", hostname=hostname, errors=errors)

    for n, ipv4, ipv6, mode, vlan in zip(i_names, i_ipv4s, i_ipv6s, i_modes, i_vlans):
        if n:
            interfaces.append({
                "name": n,
                "switchport_mode": mode if mode else "no",
                "vlan": vlan if vlan else None,
                "ipv4": ipv4 if ipv4 else None,
                "ipv6": ipv6 if ipv6 else None
            })

    # ---------- VLAN ----------
    vlans = []
    v_ids = request.form.getlist("vlan_id[]")
    v_names = request.form.getlist("vlan_name[]")
    for vid, vname in zip(v_ids, v_names):
        if vid:
            vlans.append({"id": vid, "name": vname})

    # ---------- OSPF ----------
    ospf_networks = []
    ospf_nets = request.form.getlist("ospf_network[]")
    ospf_areas = request.form.getlist("ospf_area[]")

    for net, area in zip(ospf_nets, ospf_areas):
        net = net.strip()
        area = area.strip()
        if net:
            ospf_networks.append({
                "network": net,
                "area": area if area else "0"   # Default area 0 if blank
            })

    ospf = {
        "enabled": bool(request.form.get("ospf_process")),
        "process_id": request.form.get("ospf_process"),
        "networks": ospf_networks
    }

    # ---------- RIP ----------
    rip = {
        "enabled": bool(request.form.getlist("rip_network[]")),
        "networks": [n for n in request.form.getlist("rip_network[]") if n]
    }

    # ---------- BGP ----------
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
        "networks": [
            {"network": n.split()[0], "mask": n.split()[1]} 
            for n in request.form.getlist("bgp_network[]") if n
        ]
    }

    # ---------- Static Routes ----------
    static_routes = []
    s_destinations = request.form.getlist("static_dest[]")
    s_masks = request.form.getlist("static_mask[]")
    s_next_hops = request.form.getlist("static_nh[]")

    for dest, mask, nh in zip(s_destinations, s_masks, s_next_hops):
        if dest and nh:
            static_routes.append({
                "destination": dest,
                "mask": mask if mask else "255.255.255.0",
                "next_hop": nh
            })

    # ---------- IPv6 Static Routes ----------
    static_routes_v6 = []
    s6_destinations = request.form.getlist("staticv6_dest[]")
    s6_next_hops = request.form.getlist("staticv6_nh[]")

    for dest6, nh6 in zip(s6_destinations, s6_next_hops):
        if dest6 and nh6:
            static_routes_v6.append({
                "destination": dest6,
                "next_hop": nh6
            })

    # ---------- Device Data ----------
    device_data = {
        "hostname": hostname,
        "username": username,
        "password": password,
        "interfaces": interfaces,
        "vlans": vlans,
        "routing": {"ospf": ospf, "rip": rip, "bgp": bgp},
        "static_routes": static_routes,
        "static_routes_v6": static_routes_v6
    }

    # ---------- YAML Generation ----------
    yaml_file = os.path.join(YAML_DIR, f"{hostname}.yaml")
    with open(yaml_file, "w") as f:
        yaml.dump(device_data, f, sort_keys=False)

    # ---------- Config Rendering ----------
    template = env.get_template("base_config.j2")
    rendered_config = template.render(**device_data)

    config_file = os.path.join(CONFIG_DIR, f"{hostname}.cfg")
    with open(config_file, "w") as f:
        f.write(rendered_config)

    # ---------- Update IPAM ----------
    with open(IPAM_FILE, "a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        if os.path.getsize(IPAM_FILE) == 0:
            writer.writerow(["hostname", "interface", "ip_address"])
        for iface in interfaces:
            if iface["ipv4"]:
                writer.writerow([hostname, iface["name"], iface["ipv4"]])

    # ---------- Render Output ----------
    return render_template(
        "output.html",
        hostname=hostname,
        yaml_content=yaml.dump(device_data, sort_keys=False),
        rendered_config=rendered_config
    )


# ---- Golden Configs ----
@app.route("/golden_configs")
def golden_configs():
    with open("devices.yaml") as f:
        devices = yaml.safe_load(f)
    return render_template("golden_configs.html", devices=devices)


# ---- Fetch Config ----
@app.route("/fetch_config/<host>")
def fetch_config(host):
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

        connection.enable()
        running_config = connection.send_command("show running-config")
        connection.disconnect()

        fetched_dir = "generated/fetched_configs"
        os.makedirs(fetched_dir, exist_ok=True)
        with open(f"{fetched_dir}/{host}_running.txt", "w") as f:
            f.write(running_config)

    except Exception as e:
        running_config = f"Error connecting to {host}\n\n{str(e)}"

    return render_template(
        "running_config.html",
        host=host,
        running_config=running_config
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
