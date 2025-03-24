#!/usr/bin/env python3

import yaml
import sys
from collections import defaultdict
from tabulate import tabulate


def parse_yaml(yaml_file):
    with open(yaml_file, "r") as file:
        data = yaml.safe_load(file)

    # Convert addresses to hex string format and calculate size in KB
    for part in data.values():
        part["address"] = f"0x{part['address']:X}"
        part["end_address"] = f"0x{part['end_address']:X}"
        part["size_kb"] = (
            int(part["end_address"], 16) - int(part["address"], 16)
        ) / 1024  # Convert bytes to KB

    return data


def format_partition_table(partitions):
    regions = defaultdict(list)

    # Organize partitions by region
    for name, part in partitions.items():
        regions[part["region"]].append((name, part))

    output = []
    for region, parts in regions.items():
        output.append(f"\nRegion: {region.upper()}")

        # Calculate total size in KB
        total_size_kb = sum(part[1]["size_kb"] for part in parts)
        output.append(f"Total Size: {total_size_kb} KB\n")

        # sort partitions by start address
        sorted_parts = sorted(parts, key=lambda x: int(x[1]["address"], 16))

        # Prepare table data
        table = [
            [name, part["address"], part["end_address"], part["size_kb"]]
            for name, part in sorted_parts
        ]

        headers = ["Partition", "Start Addr", "End Addr", "Size (KB)"]
        output.append(tabulate(table, headers=headers, tablefmt="pretty"))

    return "\n".join(output)


def print_memory_layout(partitions):
    table = []
    regions = defaultdict(list)

    for name, part in partitions.items():
        regions[part["region"]].append((name, part))

    # Sort by region name, then by start address within each region
    sorted_regions = sorted(regions.items(), key=lambda x: x[0])

    for region, parts in sorted_regions:
        for name, part in sorted(
            parts, key=lambda x: int(x[1]["address"], 16)
        ):  # Sort by start address
            start = part["address"]
            end = part["end_address"]
            size_kb = part["size_kb"]
            table.append([region, start, end, name, size_kb])

    headers = ["Region", "Start Address", "End Address", "Partition Name", "Size (KB)"]
    return tabulate(table, headers=headers, tablefmt="pretty")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <yaml_file>")
        sys.exit(1)

    yaml_file = sys.argv[1]
    partitions = parse_yaml(yaml_file)

    # print(print_memory_layout(partitions))
    print(format_partition_table(partitions))
