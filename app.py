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
                    row.get("ip_address")
                    or row.get("cidr")
                    or row.get("IP")
                    or row.get("ip")
                )
                if ip_field:
                    ip_csv = ip_field.split("/")[0]
                    if ip_csv == ip_input:
                        return True
        return False
    except Exception as e:
        print(f"Error reading IPAM file: {e}")
        return False

# ---- Push Configs ----
@app.route("/push_config", methods=["GET", "POST"])
def push_config():
    import requests

    config_files = os.listdir(CONFIG_DIR)
    result = None

    if request.method == "POST":
        ip = request.form.get("device_ip")
        username = request.form.get("username")
        password = request.form.get("password")
        file_name = request.form.get("config_file")

        config_path = os.path.join(CONFIG_DIR, file_name)

        if not os.path.exists(config_path):
            result = f"❌ Config file '{file_name}' not found."
        else:
            try:
                # --- Push configuration to the device ---
                connection = ConnectHandler(
                    device_type="cisco_ios",
                    host=ip,
                    username=username,
                    password=password,
                )

                connection.enable()
                with open(config_path) as f:
                    lines = f.read().splitlines()

                output = connection.send_config_set(lines)
                connection.save_config()
                connection.disconnect()

                result = f"Configuration pushed successfully to {ip}<br><pre>{output}</pre>"

                # --- Trigger Jenkins pipeline ---
                try:
                    JENKINS_URL = "http://localhost:8080"
                    JOB_NAME = "Unit-test"
                    TOKEN = "Unit-test"
                    USERNAME = "Aravindh"
                    API_TOKEN = "11381987b78492f783ccce0512e2dd51b5"

                    trigger_url = f"{JENKINS_URL}/job/{JOB_NAME}/buildWithParameters"

                    payload = {
                        "token": TOKEN,
                        "device_ip": ip,
                        "config_file": file_name,
                    }

                    response = requests.post(
                        trigger_url,
                        params=payload,
                        auth=(USERNAME, API_TOKEN),
                        timeout=10,
                    )

                    if response.status_code in [200, 201]:
                        result += (
                            "<br><b style='color:lime;'>Jenkins pipeline triggered successfully.</b>"
                            f"<br><a href='{JENKINS_URL}/job/{JOB_NAME}/' target='_blank' style='color:#00bfff;'>"
                            "View Jenkins Job</a>"
                        )
                    else:
                        result += (
                            f"<br><b style='color:orange;'>Jenkins trigger failed (HTTP {response.status_code}).</b>"
                            f"<br><pre>{response.text}</pre>"
                        )

                except Exception as je:
                    result += f"<br><b style='color:red;'>Jenkins trigger error: {je}</b>"

            except Exception as e:
                result = f"Error pushing config: {e}"

    return render_template("push_config.html", config_files=config_files, result=result)


# ---- Home Page ----
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
                diff_output=diff_output,
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
    i_ipv6_ospf = request.form.getlist("intf_ipv6_ospf[]")
    i_ipv6_area = request.form.getlist("intf_ipv6_area[]")

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

    for n, ipv4, ipv6, mode, vlan, ipv6_ospf, ipv6_area in zip(
        i_names, i_ipv4s, i_ipv6s, i_modes, i_vlans, i_ipv6_ospf, i_ipv6_area
    ):
        if n:
            interfaces.append(
                {
                    "name": n,
                    "switchport_mode": mode if mode else "no",
                    "vlan": vlan if vlan else None,
                    "ipv4": ipv4 if ipv4 else None,
                    "ipv6": ipv6 if ipv6 else None,
                    "ipv6_ospf": ipv6_ospf == "yes",
                    "ipv6_area": ipv6_area if ipv6_area else "0",
                }
            )

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
            ospf_networks.append(
                {"network": net, "area": area if area else "0"}
            )

    ospf = {
        "enabled": bool(request.form.get("ospf_process")),
        "process_id": request.form.get("ospf_process"),
        "networks": ospf_networks,
        "redistribute_bgp": request.form.get("ospf_redistribute_bgp") == "yes",
    }

    # ---------- RIP ----------
    rip = {
        "enabled": bool(request.form.getlist("rip_network[]")),
        "networks": [n for n in request.form.getlist("rip_network[]") if n],
        "redistribute_ospf": request.form.get("rip_redistribute_ospf") == "yes",
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
            for n in request.form.getlist("bgp_network[]")
            if n
        ],
    }

    # ---------- Static Routes ----------
    static_routes = []
    s_destinations = request.form.getlist("static_dest[]")
    s_masks = request.form.getlist("static_mask[]")
    s_next_hops = request.form.getlist("static_nh[]")

    for dest, mask, nh in zip(s_destinations, s_masks, s_next_hops):
        if dest and nh:
            static_routes.append(
                {
                    "destination": dest,
                    "mask": mask if mask else "255.255.255.0",
                    "next_hop": nh,
                }
            )

    # ---------- IPv6 Static Routes ----------
    static_routes_v6 = []
    s6_destinations = request.form.getlist("staticv6_dest[]")
    s6_next_hops = request.form.getlist("staticv6_nh[]")

    for dest6, nh6 in zip(s6_destinations, s6_next_hops):
        if dest6 and nh6:
            static_routes_v6.append({"destination": dest6, "next_hop": nh6})

    # ---------- Device Data ----------
    device_data = {
        "hostname": hostname,
        "username": username,
        "password": password,
        "interfaces": interfaces,
        "vlans": vlans,
        "routing": {"ospf": ospf, "rip": rip, "bgp": bgp},
        "static_routes": static_routes,
        "static_routes_v6": static_routes_v6,
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
        rendered_config=rendered_config,
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
            secret=device_info.get("current_password"),
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

    return render_template("running_config.html", host=host, running_config=running_config)
# ---- Run Show Commands ----
@app.route("/run_show", methods=["GET", "POST"])
def run_show():
    # --- Load device list dynamically from devices.yaml ---
    try:
        with open("devices.yaml") as f:
            devices = yaml.safe_load(f)
            device_list = [d["host"] for d in devices if "host" in d]
    except Exception as e:
        device_list = []
        print(f"Error reading devices.yaml: {e}")

    # --- Predefined common show commands ---
    commands = [
        "show ip interface brief",
        "show interfaces status",
        "show ip ospf neighbor",
        "show ip bgp summary",
        "show ipv6 ospf neighbor",
        "show ip arp",
        "show ip route",
        "show ip ospf database",
        "show lldp neighbor",
	"show ipv6 int brief",
    ]

    result = None

    # --- When form is submitted ---
    if request.method == "POST":
        ip = request.form.get("device_ip")
        username = request.form.get("username")
        password = request.form.get("password")
        command = request.form.get("command")

        try:
            # Match the selected IP to device info in YAML
            with open("devices.yaml") as f:
                devices = yaml.safe_load(f)
            device_info = next((d for d in devices if str(d["host"]) == str(ip)), None)

            if not device_info:
                result = f"<b style='color:red;'>Device {ip} not found in devices.yaml</b>"
            else:
                # Connect and run the command
                connection = ConnectHandler(
                    device_type=device_info.get("device_type", "cisco_ios"),
                    host=device_info["host"],
                    username=username or device_info.get("current_username"),
                    password=password or device_info.get("current_password"),
                    secret=password or device_info.get("current_password"),
                )

                connection.enable()
                output = connection.send_command(command)
                connection.disconnect()

                result = (
                    f"<b>Device:</b> {ip}<br>"
                    f"<b>Command:</b> {command}<br><br>"
                    f"<pre>{output}</pre>"
                )

        except Exception as e:
            result = f"<b style='color:red;'>Error connecting to {ip}: {e}</b>"

    return render_template("run_show.html", devices=device_list, commands=commands, result=result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
