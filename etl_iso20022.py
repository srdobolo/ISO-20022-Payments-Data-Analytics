import os
import glob
import csv
import xml.etree.ElementTree as ET
from datetime import datetime

# ---------- CONFIG ----------
# Base folder where the XML files are stored
BASE_DIR = 'data'

# Folder where the generated CSV files will be saved
OUTPUT_DIR = 'output'
os.makedirs(OUTPUT_DIR, exist_ok=True)  # Create output folder if it doesn't exist

# Paths for each ISO 20022 message type
pain001_dir = os.path.join(BASE_DIR, 'ISO20022_pain001')
pacs008_dir = os.path.join(BASE_DIR, 'ISO20022_pacs008')

# ---------- HELPERS ----------
def parse_datetime(dt_str):
    """
    Helper function to safely parse ISO 8601 date-time strings like '2025-09-24T13:22:11Z'.
    Returns a datetime object or None if parsing fails.
    """
    if not dt_str:
        return None
    try:
        # Remove 'Z' (Zulu time) if present and parse
        return datetime.fromisoformat(dt_str.replace('Z', ''))
    except Exception:
        return None

# ---------- DIM PARTY ----------
# We'll store parties (debtors and creditors) in a dictionary to avoid duplicates
parties = {}
party_counter = 1

def get_or_create_party(name, iban, country):
    """
    If a party (Debtor or Creditor) already exists, return its PartyID.
    If not, create a new entry with a unique PartyID and return it.
    """
    global party_counter
    # We use (name, IBAN) as the unique key to avoid duplicates
    key = (name or '', iban or '')
    if key not in parties:
        parties[key] = {
            'PartyID': f'P{party_counter:05d}',  # Example: P00001
            'Name': name,
            'IBAN': iban,
            'CountryCode': country
        }
        party_counter += 1
    return parties[key]['PartyID']

# ---------- STEP 1: DimParty from pain.001 ----------
print("🔸 Extracting parties from pain.001 ...")

# Loop over all pain.001 XML files in the folder
for file in glob.glob(os.path.join(pain001_dir, '*.xml')):
    tree = ET.parse(file)      # Parse XML
    root = tree.getroot()      # Get root element

    # Extract the XML namespace (e.g. 'urn:iso:std:iso:20022:tech:xsd:pain.001.001.03')
    ns = {'ns': root.tag.split('}')[0].strip('{')}

    # ---- Debtor ----
    dbtr_name = root.find('.//ns:Dbtr/ns:Nm', ns)
    dbtr_iban = root.find('.//ns:DbtrAcct/ns:Id/ns:IBAN', ns)
    dbtr_country = root.find('.//ns:Dbtr/ns:PstlAdr/ns:Ctry', ns)
    get_or_create_party(
        dbtr_name.text if dbtr_name is not None else None,
        dbtr_iban.text if dbtr_iban is not None else None,
        dbtr_country.text if dbtr_country is not None else None
    )

    # ---- Creditors ----
    # Each transaction (CdtTrfTxInf) can have a different creditor
    for cdt in root.findall('.//ns:CdtTrfTxInf', ns):
        cdtr_name = cdt.find('.//ns:Cdtr/ns:Nm', ns)
        cdtr_iban = cdt.find('.//ns:CdtrAcct/ns:Id/ns:IBAN', ns)
        cdtr_country = cdt.find('.//ns:Cdtr/ns:PstlAdr/ns:Ctry', ns)
        get_or_create_party(
            cdtr_name.text if cdtr_name is not None else None,
            cdtr_iban.text if cdtr_iban is not None else None,
            cdtr_country.text if cdtr_country is not None else None
        )

# ✅ Write all unique parties into DimParty.csv
with open(os.path.join(OUTPUT_DIR, 'DimParty.csv'), 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['PartyID', 'Name', 'IBAN', 'CountryCode'])
    writer.writeheader()
    writer.writerows(parties.values())

print(f"✅ DimParty.csv created with {len(parties)} rows")

# ---------- STEP 2: FactPayments from pacs.008 ----------
print("🔸 Extracting transactions from pacs.008 ...")

fact_rows = []

# Loop over all pacs.008 XML files
for file in glob.glob(os.path.join(pacs008_dir, '*.xml')):
    tree = ET.parse(file)
    root = tree.getroot()
    ns = {'ns': root.tag.split('}')[0].strip('{')}

    # Common header info for the message
    msg_id = root.findtext('.//ns:GrpHdr/ns:MsgId', namespaces=ns)
    payment_date_str = root.findtext('.//ns:GrpHdr/ns:CreDtTm', namespaces=ns)
    payment_date = parse_datetime(payment_date_str)

    # ---- Debtor Info (applies to all transactions in this message) ----
    debtor_name = root.findtext('.//ns:Dbtr/ns:Nm', namespaces=ns)
    debtor_iban = root.findtext('.//ns:DbtrAcct/ns:Id/ns:IBAN', namespaces=ns)
    debtor_country = root.findtext('.//ns:Dbtr/ns:PstlAdr/ns:Ctry', namespaces=ns)
    debtor_id = get_or_create_party(debtor_name, debtor_iban, debtor_country)

    # ---- Loop over each transaction (CdtTrfTxInf) ----
    for tx in root.findall('.//ns:CdtTrfTxInf', ns):
        instr_id = tx.findtext('.//ns:PmtId/ns:InstrId', namespaces=ns)
        end_to_end = tx.findtext('.//ns:PmtId/ns:EndToEndId', namespaces=ns)

        # Amount and currency
        amount_el = tx.find('.//ns:Amt/ns:InstdAmt', ns)
        amount = amount_el.text if amount_el is not None else None
        currency = amount_el.attrib.get('Ccy') if amount_el is not None else None

        # Creditor Info
        cdtr_name = tx.findtext('.//ns:Cdtr/ns:Nm', namespaces=ns)
        cdtr_iban = tx.findtext('.//ns:CdtrAcct/ns:Id/ns:IBAN', namespaces=ns)
        cdtr_country = tx.findtext('.//ns:Cdtr/ns:PstlAdr/ns:Ctry', namespaces=ns)
        creditor_id = get_or_create_party(cdtr_name, cdtr_iban, cdtr_country)

        # Agents, Purpose Code, Charge Bearer
        debtor_bic = root.findtext('.//ns:DbtrAgt/ns:FinInstnId/ns:BICFI', namespaces=ns)
        creditor_bic = tx.findtext('.//ns:CdtrAgt/ns:FinInstnId/ns:BICFI', namespaces=ns)
        purpose_code = tx.findtext('.//ns:Purp/ns:Cd', namespaces=ns)
        charge_bearer = root.findtext('.//ns:ChrgBr', namespaces=ns)

        # Create a row for the FactPayments table
        fact_rows.append({
            'PaymentID': f"{msg_id}-{instr_id}",  # unique ID
            'MsgId': msg_id,
            'InstrId': instr_id,
            'EndToEndId': end_to_end,
            'PaymentDate': payment_date.isoformat() if payment_date else None,
            'SettlementDate': None,  # to be filled later with pacs.002 / camt.054
            'Amount': amount,
            'CurrencyCode': currency,
            'DebtorID': debtor_id,
            'CreditorID': creditor_id,
            'DebtorAgentBIC': debtor_bic,
            'CreditorAgentBIC': creditor_bic,
            'PurposeCode': purpose_code,
            'StatusCode': None,  # will be enriched with pacs.002
            'ChargeBearer': charge_bearer,
            'ProcessingTimeMinutes': None
        })

# ✅ Write FactPayments.csv
with open(os.path.join(OUTPUT_DIR, 'FactPayments.csv'), 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fact_rows[0].keys())
    writer.writeheader()
    writer.writerows(fact_rows)

print(f"✅ FactPayments.csv created with {len(fact_rows)} rows")
print("🎉 Base ETL complete — next we'll enrich with pacs.002 and camt.054")