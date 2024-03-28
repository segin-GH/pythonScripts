#!/usr/bin/env python3

import os
import tempfile
import subprocess

buffer = {}

def search_and_edit(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r') as f:
                    lines = f.readlines()
                for i, line in enumerate(lines):
                    if "HSPL_LOGE" in line:
                        print(f"File: {file_path}, Line: {i+1}")
                        print(line.strip())
                        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
                            temp_file.write(line.strip())
                        subprocess.call(['vim', temp_file.name])
                        with open(temp_file.name, 'r') as f:
                            new_line = f.read().strip()
                        lines[i] = new_line + "\n"
                        with open(file_path, 'w') as f:
                            f.writelines(lines)
                        print(f"Updated line in {file_path}")
            except (IOError, UnicodeDecodeError):
                print(f"Error reading file {file_path}")

directory = input("Enter the directory to search: ")
search_and_edit(directory)

