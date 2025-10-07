# -*- coding: utf-8 -*-
"""
Extraction script for ISO 20022 messages (pain.001, pacs.008, pacs.002, camt.054)
Parses all tags and attributes into flat tables (CSV), one per message type.
"""

import os
import glob
import csv
import xml.etree.ElementTree as ET

# ========================
# CONFIG
# ========================
BASE_DIR = 'data'   # Adjust to your folder structure
STAGING_DIR = 'staging'
os.makedirs(STAGING_DIR, exist_ok=True)

DIRS = {
    'pain001': os.path.join(BASE_DIR, 'ISO20022_pain001'),
    'pacs008': os.path.join(BASE_DIR, 'ISO20022_pacs008'),
    'pacs002': os.path.join(BASE_DIR, 'ISO20022_pacs002'),
    'camt054': os.path.join(BASE_DIR, 'ISO20022_camt054'),
}

# ========================
# HELPERS
# ========================

def localname(tag):
    """Remove namespace and return local tag name."""
    if '}' in tag:
        return tag.split('}', 1)[1]
    return tag

def detect_message_type(root):
    """Return (message_type, message_root_tag) based on namespace and first child."""
    ns_uri = ''
    if '}' in root.tag:
        ns_uri = root.tag.split('}')[0].strip('{')
    first_child = next(iter(root), root)
    msg_root_local = localname(first_child.tag)
    msg_type = ns_uri.split('tech:xsd:')[-1] if 'tech:xsd:' in ns_uri else 'unknown'
    return msg_type, msg_root_local

def walk_tree(elem, path, depth, file_name, message_type, message_root, rows):
    """Recursive tree walker that flattens elements and attributes."""
    tag_local = localname(elem.tag)
    current_path = f"{path}/{tag_local}" if path else f"/{tag_local}"

    # Element row
    text_val = elem.text.strip() if elem.text and elem.text.strip() != '' else None
    rows.append({
        'FileName': file_name,
        'MessageType': message_type,
        'MessageRoot': message_root,
        'ElementPath': current_path,
        'Tag': tag_local,
        'Text': text_val,
        'AttrName': None,
        'AttrValue': None,
        'Depth': depth,
        'RowType': 'elem'
    })

    # Attribute rows
    for attr_name, attr_val in elem.attrib.items():
        rows.append({
            'FileName': file_name,
            'MessageType': message_type,
            'MessageRoot': message_root,
            'ElementPath': current_path,
            'Tag': tag_local,
            'Text': None,
            'AttrName': attr_name,
            'AttrValue': attr_val,
            'Depth': depth,
            'RowType': 'attr'
        })

    # Recurse
    for child in elem:
        walk_tree(child, current_path, depth + 1, file_name, message_type, message_root, rows)

def parse_xml_file(xml_path):
    """Parse a single XML file into a list of flattened rows."""
    tree = ET.parse(xml_path)
    root = tree.getroot()
    msg_type, msg_root = detect_message_type(root)
    file_name = os.path.basename(xml_path)

    rows = []
    walk_tree(root, '', 0, file_name, msg_type, msg_root, rows)
    return rows

def write_csv(rows, out_path):
    headers = ['FileName', 'MessageType', 'MessageRoot', 'ElementPath', 'Tag', 'Text', 'AttrName', 'AttrValue', 'Depth', 'RowType']
    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

# ========================
# MAIN EXTRACTION
# ========================

if __name__ == '__main__':
    for msg_type, folder in DIRS.items():
        out_csv = os.path.join(STAGING_DIR, f"staging_{msg_type}.csv")
        all_rows = []

        for xml_file in glob.glob(os.path.join(folder, '*.xml')):
            try:
                rows = parse_xml_file(xml_file)
                all_rows.extend(rows)
            except Exception as e:
                print(f"Error parsing {xml_file}: {e}")

        write_csv(all_rows, out_csv)
        print(f"[{msg_type}] Extracted {len(all_rows)} rows → {out_csv}")

    print("✅ Extraction complete")
