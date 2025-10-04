import glob, xml.etree.ElementTree as ET

pacs002_dir = 'data/ISO20022_pacs002'
for file in glob.glob(f'{pacs002_dir}/*.xml'):
    print(f"\nFile: {file}")
    tree = ET.parse(file)
    root = tree.getroot()
    ns = {'ns': root.tag.split('}')[0].strip('{')}

    org_msgid = root.findtext('.//ns:OrgnlMsgId', namespaces=ns)
    print("OrgnlMsgId:", org_msgid)

    for tx in root.findall('.//ns:TxInfAndSts', ns):
        org_endtoend = tx.findtext('.//ns:OrgnlEndToEndId', namespaces=ns)
        accpt_time = tx.findtext('.//ns:AccptncDtTm', namespaces=ns)
        print("  EndToEndId:", org_endtoend, "| AccptncDtTm:", accpt_time)
    break
