#!/usr/bin/env python3
from contextlib import contextmanager
from rich.console import Console
from rich.table import Table
from rich.columns import Columns
from rich.panel import Panel
from rich import box

import time
import fileinput
import re
import random
from itertools import zip_longest

console = Console()

# https://github.com/willmcgugan/rich/blob/master/examples/table_movie.py
BEAT_TIME = 0.02
COLOUR = "white on red"
CLR_AGE = 750
DIM_AGE = 4000
MAX_AGE = 6000
MAX_COLUMNS = 5
BATCH = 50
table_data = {}

@contextmanager
def beat(length: int = 1) -> None:
    with console:
        console.clear()
        yield
    time.sleep(length * BEAT_TIME)

def assemble_table(data):
    table = Table(show_header=False)

    for k, v in sorted(data.items(), key=lambda x: x[0]):
        table.add_row(k, v["formatted"], str(v["count"]))

    return table

def get_panel(dataset):
    output = ""
    for key, entry in dataset:
        formatted = entry.get('formatted', '')
        output += f"[yellow]{key}[/yellow] {formatted}\n"

    return output.strip()

# https://docs.python.org/3/library/itertools.html#itertools-recipes
def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)

def max_height():
  global console
  return console.size.height - 4

def assemble_panels(data):
    global console
    panel_list = [Panel.fit(get_panel(dataset)) for dataset in grouper(sorted(data.items(), key=lambda x: x[0]), max_height(), ("", {}))]
    return Columns(panel_list)

def highlight_diff(entry, new):
    entry["formatted"] = ""
    for a, b in zip(entry["raw"], new):
        if a != b:
            entry["formatted"] += "[{0}]{1}[/{0}]".format(COLOUR, b)
        else:
            entry["formatted"] += b

    entry["count"] += 1
    entry["ts"] = t_ms()

    return entry

def t_ms():
   return int(round(time.time() * 1000))

def load_items(batch):
    global table_data
    for k, v in batch:
        if k in table_data:
            table_data[k] = highlight_diff(table_data[k], v)
        else:
            table_data[k] = {"formatted":"[{0}]{1}[/{0}]".format(COLOUR, v), "raw":v, "count":1, "ts":t_ms()}

    for k, v in batch:
        table_data[k]["raw"] = v

    # Drop stale entries
    while len(table_data) > max_height()*MAX_COLUMNS:
        aged_keys = [k for k in table_data.keys() if table_data[k]["ts"] < (t_ms() - MAX_AGE)]
        try:
            del table_data[random.choice(aged_keys)]
        except IndexError:
            # aged_keys is empty
            del table_data[random.choice(list(table_data.keys()))]

    with console:
        console.clear()
        console.print(assemble_panels(table_data), justify="left")

    # Clear highlights, fade out entries
    for k in table_data.keys():
        if table_data[k]["ts"] < (t_ms() - DIM_AGE):
            table_data[k]["formatted"] = "[dim]{}[/dim]".format(table_data[k]["raw"])
        elif table_data[k]["ts"] < (t_ms() - CLR_AGE):
            table_data[k]["formatted"] = table_data[k]["raw"]


console.clear()
console.show_cursor(False)

# 987987.367525 Frame ID: 0047, Data: 00 00 00 00 00 00 00 20 
# Interpret usbcan output
re_header = re.compile('Frame ID: ([0-9a-fA-F]{4})')
re_body = re.compile('Data: ([0-9a-fA-F ]{23})')

batch = []
for line in fileinput.input():
    header = re_header.search(line)
    body = re_body.search(line)

    if not header or not body:
        #print("Skipping line: {}".format(line.strip()))
        continue

    batch.append((header[1], body[1]))

    if len(batch) > BATCH:
        load_items(batch)
        batch = []



