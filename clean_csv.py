#!/usr/bin/env python3
"""
Script to clean Git merge conflicts from CSV file
"""

import re

def clean_csv_merge_conflicts(file_path):
    """Remove Git merge conflict markers from CSV file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove Git merge conflict markers
    lines = content.split('\n')
    cleaned_lines = []
    
    skip_until_end_marker = False
    
    for line in lines:
        # Skip merge conflict start markers
        if line.startswith('<<<<<<< '):
            skip_until_end_marker = False
            continue
        # Skip merge conflict middle markers
        elif line.startswith('======='):
            skip_until_end_marker = True
            continue
        # Skip merge conflict end markers
        elif line.startswith('>>>>>>> '):
            skip_until_end_marker = False
            continue
        # Skip lines between middle and end markers (duplicate content)
        elif skip_until_end_marker:
            continue
        else:
            cleaned_lines.append(line)
    
    # Write cleaned content back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(cleaned_lines))
    
    print(f"Cleaned merge conflicts from {file_path}")

if __name__ == "__main__":
    clean_csv_merge_conflicts('scrapped_output/23.08.2025.csv')
    print("CSV file cleaned successfully!")