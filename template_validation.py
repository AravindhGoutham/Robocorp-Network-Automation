#!/usr/bin/env python3
import os
from jinja2 import Environment, FileSystemLoader, exceptions

TEMPLATES_DIR = "./templates"

# Dummy context variables to satisfy references
DUMMY_CONTEXT = {
    "hostname": "TestDevice",
    "username": "admin",
    "password": "admin",
    "interfaces": [],
    "vlans": [],
    "routing": {
        "ospf": {"enabled": True, "process_id": "1", "networks": ["10.0.0.0/24"]},
        "rip": {"enabled": False, "networks": []},
        "bgp": {"enabled": True, "as_number": "65000", "neighbors": [], "networks": []},
    },
}

def validate_templates():
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    all_passed = True

    print("\n=== Validating Jinja2 Templates ===\n")

    for filename in os.listdir(TEMPLATES_DIR):
        if filename.endswith(".j2"):
            print(f"Checking {filename} ", end="", flush=True)
            try:
                template = env.get_template(filename)
                template.render(**DUMMY_CONTEXT)
                print("PASS")
            except exceptions.TemplateSyntaxError as e:
                print(f"FAIL (Syntax error at line {e.lineno}: {e.message})")
                all_passed = False
            except exceptions.UndefinedError as e:
                print(f"FAIL (Undefined variable: {str(e)})")
                all_passed = False
            except Exception as e:
                print(f"FAIL ({str(e)})")
                all_passed = False

    print("\n=== End of Template Validation ===\n")
    return all_passed


if __name__ == "__main__":
    if not os.path.exists(TEMPLATES_DIR):
        print(f"Templates directory '{TEMPLATES_DIR}' not found.")
        exit(1)

    if not validate_templates():
        exit(1)
