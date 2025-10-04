import os
import glob
import csv
import xml.etree.ElementTree as ET
from datetime import datetime
import pandas as pd

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
print("Extracting parties from pain.001 ...")

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

# Write all unique parties into DimParty.csv
with open(os.path.join(OUTPUT_DIR, 'DimParty.csv'), 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['PartyID', 'Name', 'IBAN', 'CountryCode'])
    writer.writeheader()
    writer.writerows(parties.values())

print(f"DimParty.csv created with {len(parties)} rows")

# ---------- STEP 2: FactPayments from pacs.008 ----------
print("Extracting transactions from pacs.008 ...")

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

# Write FactPayments.csv
with open(os.path.join(OUTPUT_DIR, 'FactPayments.csv'), 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fact_rows[0].keys())
    writer.writeheader()
    writer.writerows(fact_rows)

print(f"FactPayments.csv created with {len(fact_rows)} rows")
print("Base ETL complete — next we'll enrich with pacs.002 and camt.054")

# ---------- STEP 3: Enrich FactPayments with pacs.002 ----------
print("Enriching FactPayments with pacs.002 ...")

pacs002_dir = os.path.join(BASE_DIR, 'ISO20022_pacs002')

# We load the existing FactPayments into a dictionary for easy lookup
fact_dict = {row['PaymentID']: row for row in fact_rows}

# We'll also index by (MsgId, EndToEndId) for fast matching
index_by_msg_end = {}
for row in fact_rows:
    index_by_msg_end[(row['MsgId'], row['EndToEndId'])] = row

# Loop over all pacs.002 XML files
for file in glob.glob(os.path.join(pacs002_dir, '*.xml')):
    tree = ET.parse(file)
    root = tree.getroot()
    ns = {'ns': root.tag.split('}')[0].strip('{')}

    # Extract the original message ID (corresponding to pacs.008 MsgId)
    org_msgid = root.findtext('.//ns:OrgnlMsgId', namespaces=ns)

    # Loop through each transaction status record
    for tx in root.findall('.//ns:TxInfAndSts', ns):
        org_endtoend = tx.findtext('.//ns:OrgnlEndToEndId', namespaces=ns)
        tx_status = tx.findtext('.//ns:TxSts', namespaces=ns)
        accpt_time_str = tx.findtext('.//ns:AccptncDtTm', namespaces=ns)

        # Match to FactPayments by MsgId + EndToEndId
        key = (org_msgid, org_endtoend)
        if key in index_by_msg_end:
            payment_row = index_by_msg_end[key]

            # Enrich status code
            if tx_status:
                payment_row['StatusCode'] = tx_status

            # Enrich settlement date & processing time
            if accpt_time_str:
                accpt_time = parse_datetime(accpt_time_str)
                payment_row['SettlementDate'] = accpt_time.isoformat()

                # Compute processing time in minutes if PaymentDate exists
                if payment_row['PaymentDate']:
                    payment_dt = datetime.fromisoformat(payment_row['PaymentDate'])
                    diff_minutes = (accpt_time - payment_dt).total_seconds() / 60
                    payment_row['ProcessingTimeMinutes'] = round(diff_minutes, 2)

# Rewrite the enriched FactPayments.csv
with open(os.path.join(OUTPUT_DIR, 'FactPayments.csv'), 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fact_rows[0].keys())
    writer.writeheader()
    writer.writerows(fact_rows)

print(f"FactPayments.csv enriched with pacs.002 statuses for {len(fact_rows)} transactions")

# ---------- STEP 4: Enrich FactPayments with camt.054 ----------
print("Reconciling payments with camt.054 ...")

camt054_dir = os.path.join(BASE_DIR, 'ISO20022_camt054')

# Reuse the index we built earlier: (MsgId, EndToEndId) → row
# But for camt.054 we match only by EndToEndId
index_by_endtoend = {row['EndToEndId']: row for row in fact_rows if row['EndToEndId']}

# Loop over all camt.054 XML files
for file in glob.glob(os.path.join(camt054_dir, '*.xml')):
    tree = ET.parse(file)
    root = tree.getroot()
    ns = {'ns': root.tag.split('}')[0].strip('{')}

    # Each Ntry corresponds to one statement entry (credit or debit)
    for entry in root.findall('.//ns:Ntry', ns):
        booking_date_str = entry.findtext('.//ns:BookgDt/ns:Dt', namespaces=ns)
        booking_date = parse_datetime(booking_date_str) if booking_date_str else None

        amount_el = entry.find('.//ns:Amt', ns)
        amount_val = amount_el.text if amount_el is not None else None
        currency_val = amount_el.attrib.get('Ccy') if amount_el is not None else None

        # EndToEndId may be nested deep inside NtryDtls
        end_to_end_el = entry.find('.//ns:EndToEndId', ns)
        if end_to_end_el is None:
            continue  # No matchable reference

        end_to_end_id = end_to_end_el.text

        # Match to payment by EndToEndId
        if end_to_end_id in index_by_endtoend:
            payment_row = index_by_endtoend[end_to_end_id]

            # If SettlementDate was missing, fill it from camt.054
            if not payment_row['SettlementDate'] and booking_date:
                payment_row['SettlementDate'] = booking_date.isoformat()

                # Recompute processing time if possible
                if payment_row['PaymentDate']:
                    payment_dt = datetime.fromisoformat(payment_row['PaymentDate'])
                    diff_minutes = (booking_date - payment_dt).total_seconds() / 60
                    payment_row['ProcessingTimeMinutes'] = round(diff_minutes, 2)

            # You could also reconcile amounts here if needed:
            # e.g., check if payment_row['Amount'] == amount_val

# Rewrite the enriched FactPayments.csv again
with open(os.path.join(OUTPUT_DIR, 'FactPayments.csv'), 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fact_rows[0].keys())
    writer.writeheader()
    writer.writerows(fact_rows)

print("FactPayments.csv reconciled with camt.054")

print("Generating dimension tables ...")

# Load final FactPayments (enriched with pacs.002 + camt.054)
fact_df = pd.read_csv(os.path.join(OUTPUT_DIR, 'FactPayments.csv'), dtype=str)

# ================= DimStatus =================
status_codes = (
    fact_df['StatusCode']
    .dropna()
    .drop_duplicates()
    .sort_values()
)

dim_status = pd.DataFrame({
    'StatusCode': status_codes,
    'Description': status_codes  # you can replace with full descriptions later
})

dim_status.to_csv(os.path.join(OUTPUT_DIR, 'DimStatus.csv'), index=False)
print(f"✅ DimStatus.csv created with {len(dim_status)} rows")

# ================= DimCurrency =================
currency_codes = (
    fact_df['CurrencyCode']
    .dropna()
    .drop_duplicates()
    .sort_values()
)

dim_currency = pd.DataFrame({
    'CurrencyCode': currency_codes,
    'CurrencyName': currency_codes,   # You could map these to actual names (e.g., EUR → Euro)
    'CurrencySymbol': ''              # You could enrich this from a static mapping
})

dim_currency.to_csv(os.path.join(OUTPUT_DIR, 'DimCurrency.csv'), index=False)
print(f"✅ DimCurrency.csv created with {len(dim_currency)} rows")

# ================= DimPurposeCode =================
purpose_codes = (
    fact_df['PurposeCode']
    .dropna()
    .drop_duplicates()
    .sort_values()
)

dim_purpose = pd.DataFrame({
    'PurposeCode': purpose_codes,
    'Description': purpose_codes  # You can enrich with ISO 20022 purpose descriptions
})

dim_purpose.to_csv(os.path.join(OUTPUT_DIR, 'DimPurposeCode.csv'), index=False)
print(f"DimPurposeCode.csv created with {len(dim_purpose)} rows")

# ================= DimDate =================
# Collect all unique dates from PaymentDate and SettlementDate
date_cols = ['PaymentDate', 'SettlementDate']
all_dates = pd.to_datetime(
    fact_df[date_cols].values.ravel('K'),
    errors='coerce'
).dropna().normalize().drop_duplicates().sort_values()

# Generate date attributes
dim_date = pd.DataFrame({'Date': all_dates})
dim_date['Year'] = dim_date['Date'].dt.year
dim_date['MonthNumber'] = dim_date['Date'].dt.month
dim_date['Month'] = dim_date['Date'].dt.strftime('%B')
dim_date['Quarter'] = dim_date['Date'].dt.quarter
dim_date['Day'] = dim_date['Date'].dt.day
dim_date['WeekNumber'] = dim_date['Date'].dt.isocalendar().week

dim_date.to_csv(os.path.join(OUTPUT_DIR, 'DimDate.csv'), index=False, date_format='%Y-%m-%d')
print(f"DimDate.csv created with {len(dim_date)} rows")

print("All supporting dimension tables generated.")
