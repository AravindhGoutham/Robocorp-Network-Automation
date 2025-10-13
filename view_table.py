#!/usr/bin/env python3

import csv
from prettytable import PrettyTable

LOGFILE = "Device-credentials.txt"

table = PrettyTable()
table.field_names = ["timestamp_utc", "device", "username", "password"]

with open(LOGFILE, newline="") as f:
    reader = csv.reader(f)
    next(reader)
    for row in reader:
        table.add_row(row)

table.align["timestamp_utc"] = "l"
table.align["device"] = "l"
table.align["username"] = "l"
table.align["password"] = "l"

print(table)
