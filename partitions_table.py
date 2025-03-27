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


def draw_partition_table(partitions):
    # Define fixed memory regions
    FIXED_MEMORY_REGIONS = {
        "FLASH_PRIMARY": {"size_kb": 1024, "start": 0x00000000, "end": 0x00100000},
        "EXTERNAL_FLASH": {"size_kb": 8192, "start": 0x00000000, "end": 0x00800000},
        "SRAM_PRIMARY": {"size_kb": 512, "start": 0x20000000},
    }

    regions = defaultdict(list)
    for name, part in partitions.items():
        regions[part["region"].upper()].append((name, part))

    output = []
    for region, details in FIXED_MEMORY_REGIONS.items():
        output.append(
            f"\nRegion: {region} (Size: {details['size_kb']} KB, Start: {hex(details['start'])})"
        )

        if "end" in details:
            output[-1] += f", End: {hex(details['end'])}"

        if region in regions:
            sorted_parts = sorted(
                regions[region], key=lambda x: int(x[1]["address"], 16)
            )

            merged_parts = []
            prev_name, prev_part = sorted_parts[0]
            for name, part in sorted_parts[1:]:
                if (
                    prev_part["address"] == part["address"]
                    and prev_part["end_address"] == part["end_address"]
                ):
                    prev_name += ", " + name
                else:
                    merged_parts.append(
                        [
                            prev_name,
                            prev_part["address"],
                            prev_part["end_address"],
                            prev_part["size_kb"],
                        ]
                    )
                    prev_name, prev_part = name, part
            merged_parts.append(
                [
                    prev_name,
                    prev_part["address"],
                    prev_part["end_address"],
                    prev_part["size_kb"],
                ]
            )

            headers = ["Partition", "Start Addr", "End Addr", "Size (KB)"]
            output.append(tabulate(merged_parts, headers=headers, tablefmt="pretty"))
        else:
            output.append("No partitions defined.")

    return "\n".join(output)


def draw_partition_table(partitions):
    # Define fixed memory regions
    FIXED_MEMORY_REGIONS = {
        "FLASH_PRIMARY": {"size_kb": 1024, "start": 0x00000000, "end": 0x00100000},
        "EXTERNAL_FLASH": {"size_kb": 8192, "start": 0x00000000, "end": 0x00800000},
        "SRAM_PRIMARY": {"size_kb": 512, "start": 0x20000000},
    }

    regions = defaultdict(list)
    for name, part in partitions.items():
        regions[part["region"].upper()].append((name, part))

    output = []
    for region, details in FIXED_MEMORY_REGIONS.items():
        output.append(
            f"\nRegion: {region} (Size: {details['size_kb']} KB, Start: {hex(details['start'])}, End: {hex(details.get('end', details['start'] + details['size_kb'] * 1024))})"
        )

        if region in regions:
            sorted_parts = sorted(
                regions[region], key=lambda x: int(x[1]["address"], 16)
            )

            merged_parts = []
            prev_name, prev_part = sorted_parts[0]
            for name, part in sorted_parts[1:]:
                if (
                    prev_part["address"] == part["address"]
                    and prev_part["end_address"] == part["end_address"]
                ):
                    prev_name += ", " + name
                else:
                    merged_parts.append(
                        [
                            prev_name,
                            prev_part["address"],
                            prev_part["end_address"],
                            prev_part["size_kb"],
                        ]
                    )
                    prev_name, prev_part = name, part
            merged_parts.append(
                [
                    prev_name,
                    prev_part["address"],
                    prev_part["end_address"],
                    prev_part["size_kb"],
                ]
            )

            headers = ["Partition", "Start Addr", "End Addr", "Size (KB)"]
            output.append(tabulate(merged_parts, headers=headers, tablefmt="pretty"))
        else:
            output.append("No partitions defined.")

    return "\n".join(output)


def draw_partition_hierarchy(partitions):
    region_hierarchy = defaultdict(lambda: defaultdict(list))

    sorted_partitions = sorted(
        partitions.items(), key=lambda x: int(x[1]["address"], 16)
    )

    merged_partitions = {}

    for name, part in sorted_partitions:
        key = (part["region"].upper(), part["address"], part["end_address"])

        if key in merged_partitions:
            # Merge names if partition with same start and end exists
            merged_partitions[key]["name"] += f" / {name}"
        else:
            merged_partitions[key] = {
                "name": name,
                "address": part["address"],
                "end_address": part["end_address"],
                "size_kb": part["size_kb"],
                "region": part["region"].upper(),
            }

    # Reconstruct sorted partitions after merging
    sorted_merged = sorted(
        merged_partitions.values(), key=lambda x: int(x["address"], 16)
    )

    for part in sorted_merged:
        region = part["region"]
        parent_name = None
        for parent in sorted_merged:
            if (
                part["name"] != parent["name"]
                and part["region"] == parent["region"]
                and int(part["address"], 16) >= int(parent["address"], 16)
                and int(part["end_address"], 16) <= int(parent["end_address"], 16)
            ):
                parent_name = parent["name"]
                break
        region_hierarchy[region][parent_name].append(part)

    def format_partition(part, level=0):
        indent = "  " * level
        return f"{indent}- {part['name']}: {part['address']} - {part['end_address']} ({part['size_kb']}KB, {hex((int(part['size_kb'])) * 1024)})"

    def draw_recursive(region, parent_name=None, level=0):
        output = []
        if parent_name in region_hierarchy[region]:
            for part in region_hierarchy[region][parent_name]:
                output.append(format_partition(part, level))
                output.extend(draw_recursive(region, part["name"], level + 1))
        return output

    output = []
    for region in region_hierarchy:
        output.append(f"\nRegion: {region}")
        output.extend(draw_recursive(region))

    return "\n".join(output)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <yaml_file>")
        sys.exit(1)

    yaml_file = sys.argv[1]
    partitions = parse_yaml(yaml_file)

    print("==*==" * 20)
    print(print_memory_layout(partitions))
    print("==*==" * 20)
    print(format_partition_table(partitions))
    print("==*==" * 20)
    print(draw_partition_table(partitions))
    print("==*==" * 20)
    print(draw_partition_hierarchy(partitions))
