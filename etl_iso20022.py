import os
import glob
import csv
import xml.etree.ElementTree as ET
from datetime import datetime
import pandas as pd

# ========================
# CONFIG
# ========================
BASE_DIR = 'data'
OUTPUT_DIR = 'output'
os.makedirs(OUTPUT_DIR, exist_ok=True)

pain001_dir = os.path.join(BASE_DIR, 'ISO20022_pain001')
pacs008_dir = os.path.join(BASE_DIR, 'ISO20022_pacs008')
pacs002_dir = os.path.join(BASE_DIR, 'ISO20022_pacs002')
camt054_dir = os.path.join(BASE_DIR, 'ISO20022_camt054')

# ========================
# HELPERS
# ========================
def parse_datetime(dt_str):
    """Parse ISO datetime with or without timezone Z."""
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str.replace('Z', ''))
    except Exception:
        return None

def extract_amount_currency(tx, ns):
    """
    Robust amount extractor that handles:
      - <IntrBkSttlmAmt Ccy="...">123</IntrBkSttlmAmt>
      - <InstdAmt Ccy="...">123</InstdAmt>
      - <Amt Ccy="...">123</Amt>
      - <Amt><InstdAmt Ccy="...">123</InstdAmt></Amt>
    Returns (amount_str or None, currency_str or None)
    """
    # 1) Preferred: settlement amount
    el = tx.find('.//ns:IntrBkSttlmAmt', ns)
    if el is not None and el.text and el.attrib.get('Ccy'):
        return el.text.strip(), el.attrib.get('Ccy').strip()

    # 2) Instructed amount (standalone)
    el = tx.find('.//ns:InstdAmt', ns)
    if el is not None and el.text and el.attrib.get('Ccy'):
        return el.text.strip(), el.attrib.get('Ccy').strip()

    # 3) Parent <Amt> that itself has Ccy/text
    el = tx.find('.//ns:Amt', ns)
    if el is not None:
        # 3a) If Amt contains InstdAmt child, use that
        child = el.find('.//ns:InstdAmt', ns)
        if child is not None and child.text and child.attrib.get('Ccy'):
            return child.text.strip(), child.attrib.get('Ccy').strip()
        # 3b) Else if Amt itself has value/ccy
        if el.text and el.attrib.get('Ccy'):
            return el.text.strip(), el.attrib.get('Ccy').strip()

    return None, None

def extract_debtor_triplet(root, tx, ns):
    """
    Prefer debtor data at transaction level; fallback to message level.
    Returns (name, iban, country)
    """
    name = (tx.findtext('.//ns:Dbtr/ns:Nm', namespaces=ns)
            or root.findtext('.//ns:Dbtr/ns:Nm', namespaces=ns))
    iban = (tx.findtext('.//ns:DbtrAcct/ns:Id/ns:IBAN', namespaces=ns)
            or root.findtext('.//ns:DbtrAcct/ns:Id/ns:IBAN', namespaces=ns))
    ctry = (tx.findtext('.//ns:Dbtr/ns:PstlAdr/ns:Ctry', namespaces=ns)
            or root.findtext('.//ns:Dbtr/ns:PstlAdr/ns:Ctry', namespaces=ns))
    return name, iban, ctry

# ========================
# DIM PARTY + PURPOSE LOOKUP
# ========================
parties = {}
party_counter = 1
purpose_lookup = {}  # EndToEndId (normalized) -> PurposeCode

def get_or_create_party(name, iban, country):
    global party_counter
    key = (name or '', iban or '')
    if key not in parties:
        parties[key] = {
            'PartyID': f'P{party_counter:05d}',
            'Name': name,
            'IBAN': iban,
            'CountryCode': country
        }
        party_counter += 1
    return parties[key]['PartyID']

print("Extracting parties and purpose codes from pain.001 ...")

for file in glob.glob(os.path.join(pain001_dir, '*.xml')):
    tree = ET.parse(file)
    root = tree.getroot()
    ns = {'ns': root.tag.split('}')[0].strip('{')}

    # Debtor at message level
    dbtr_name = root.find('.//ns:Dbtr/ns:Nm', ns)
    dbtr_iban = root.find('.//ns:DbtrAcct/ns:Id/ns:IBAN', ns)
    dbtr_country = root.find('.//ns:Dbtr/ns:PstlAdr/ns:Ctry', ns)
    get_or_create_party(
        dbtr_name.text if dbtr_name is not None else None,
        dbtr_iban.text if dbtr_iban is not None else None,
        dbtr_country.text if dbtr_country is not None else None
    )

    # Creditors + PurposeCode per transaction
    for cdt in root.findall('.//ns:CdtTrfTxInf', ns):
        cdtr_name = cdt.find('.//ns:Cdtr/ns:Nm', ns)
        cdtr_iban = cdt.find('.//ns:CdtrAcct/ns:Id/ns:IBAN', ns)
        cdtr_country = cdt.find('.//ns:Cdtr/ns:PstlAdr/ns:Ctry', ns)
        get_or_create_party(
            cdtr_name.text if cdtr_name is not None else None,
            cdtr_iban.text if cdtr_iban is not None else None,
            cdtr_country.text if cdtr_country is not None else None
        )

        end_to_end = cdt.findtext('.//ns:PmtId/ns:EndToEndId', namespaces=ns)
        purpose_cd = cdt.findtext('.//ns:Purp/ns:Cd', namespaces=ns)
        if end_to_end and purpose_cd:
            purpose_lookup[(end_to_end or '').strip().upper()] = purpose_cd.strip()

with open(os.path.join(OUTPUT_DIR, 'DimParty.csv'), 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['PartyID', 'Name', 'IBAN', 'CountryCode'])
    writer.writeheader()
    writer.writerows(parties.values())

print(f"DimParty.csv created with {len(parties)} rows")
print(f"PurposeCode lookup entries: {len(purpose_lookup)}")

# ========================
# FACT PAYMENTS - PACS.008
# ========================
print("Extracting transactions from pacs.008 ...")

fact_rows = []

for file in glob.glob(os.path.join(pacs008_dir, '*.xml')):
    tree = ET.parse(file)
    root = tree.getroot()
    ns = {'ns': root.tag.split('}')[0].strip('{')}

    msg_id = root.findtext('.//ns:GrpHdr/ns:MsgId', namespaces=ns)
    payment_date_str = root.findtext('.//ns:GrpHdr/ns:CreDtTm', namespaces=ns)
    payment_date = parse_datetime(payment_date_str)

    for tx in root.findall('.//ns:CdtTrfTxInf', ns):
        instr_id = tx.findtext('.//ns:PmtId/ns:InstrId', namespaces=ns)
        end_to_end = tx.findtext('.//ns:PmtId/ns:EndToEndId', namespaces=ns)
        norm_end = (end_to_end or '').strip().upper()

        # Amount & Currency (robust)
        amount, currency = extract_amount_currency(tx, ns)

        # Debtor (prefer tx-level, fallback to message-level); guarantees a PartyID
        debtor_name, debtor_iban, debtor_country = extract_debtor_triplet(root, tx, ns)
        debtor_id = get_or_create_party(debtor_name, debtor_iban, debtor_country)

        # Creditor
        cdtr_name = tx.findtext('.//ns:Cdtr/ns:Nm', namespaces=ns)
        cdtr_iban = tx.findtext('.//ns:CdtrAcct/ns:Id/ns:IBAN', namespaces=ns)
        cdtr_country = tx.findtext('.//ns:Cdtr/ns:PstlAdr/ns:Ctry', namespaces=ns)
        creditor_id = get_or_create_party(cdtr_name, cdtr_iban, cdtr_country)

        # Agents, Purpose, Charges
        debtor_bic = tx.findtext('.//ns:DbtrAgt/ns:FinInstnId/ns:BICFI', namespaces=ns) \
                      or root.findtext('.//ns:DbtrAgt/ns:FinInstnId/ns:BICFI', namespaces=ns)
        creditor_bic = tx.findtext('.//ns:CdtrAgt/ns:FinInstnId/ns:BICFI', namespaces=ns)

        purpose_code = tx.findtext('.//ns:Purp/ns:Cd', namespaces=ns)
        if not purpose_code and norm_end in purpose_lookup:
            purpose_code = purpose_lookup[norm_end]

        fact_rows.append({
            'PaymentID': f"{msg_id}-{instr_id}",
            'MsgId': msg_id,
            'InstrId': instr_id,
            'EndToEndId': end_to_end,
            'PaymentDate': payment_date.isoformat() if payment_date else None,
            'SettlementDate': None,
            'Amount': amount,
            'CurrencyCode': currency,
            'DebtorID': debtor_id,
            'CreditorID': creditor_id,
            'DebtorAgentBIC': debtor_bic,
            'CreditorAgentBIC': creditor_bic,
            'PurposeCode': purpose_code,
            'StatusCode': None,
            'ProcessingTimeMinutes': None
        })

# Write FactPayments initial
with open(os.path.join(OUTPUT_DIR, 'FactPayments.csv'), 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fact_rows[0].keys())
    writer.writeheader()
    writer.writerows(fact_rows)

print(f"FactPayments.csv created with {len(fact_rows)} rows")

# ========================
# ENRICH WITH PACS.002 (normalized EndToEndId)
# ========================
print("Enriching FactPayments with pacs.002 ...")

index_by_endtoend = { (row['EndToEndId'] or '').strip().upper(): row
                      for row in fact_rows if row['EndToEndId'] }

for file in glob.glob(os.path.join(pacs002_dir, '*.xml')):
    tree = ET.parse(file)
    root = tree.getroot()
    ns = {'ns': root.tag.split('}')[0].strip('{')}

    for tx in root.findall('.//ns:TxInfAndSts', ns):
        org_endtoend = (tx.findtext('.//ns:OrgnlEndToEndId', namespaces=ns) or '').strip().upper()
        tx_status = tx.findtext('.//ns:TxSts', namespaces=ns)
        accpt_time_str = tx.findtext('.//ns:AccptncDtTm', namespaces=ns)

        if org_endtoend in index_by_endtoend:
            row = index_by_endtoend[org_endtoend]
            if tx_status:
                row['StatusCode'] = tx_status
            if accpt_time_str:
                accpt_time = parse_datetime(accpt_time_str)
                row['SettlementDate'] = accpt_time.isoformat()
                if row['PaymentDate']:
                    payment_dt = datetime.fromisoformat(row['PaymentDate'])
                    diff = (accpt_time - payment_dt).total_seconds() / 60
                    row['ProcessingTimeMinutes'] = round(diff, 2)

# Rewrite FactPayments after pacs.002
with open(os.path.join(OUTPUT_DIR, 'FactPayments.csv'), 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fact_rows[0].keys())
    writer.writeheader()
    writer.writerows(fact_rows)

print("FactPayments.csv enriched with pacs.002")

# ========================
# ENRICH WITH CAMT.054 (normalized EndToEndId)
# ========================
print("Reconciling payments with camt.054 ...")

for file in glob.glob(os.path.join(camt054_dir, '*.xml')):
    tree = ET.parse(file)
    root = tree.getroot()
    ns = {'ns': root.tag.split('}')[0].strip('{')}

    for entry in root.findall('.//ns:Ntry', ns):
        booking_date_str = entry.findtext('.//ns:BookgDt/ns:Dt', namespaces=ns)
        booking_date = parse_datetime(booking_date_str) if booking_date_str else None

        end_to_end_el = entry.find('.//ns:EndToEndId', ns)
        if end_to_end_el is None:
            continue
        end_to_end_id = (end_to_end_el.text or '').strip().upper()

        if end_to_end_id in index_by_endtoend:
            row = index_by_endtoend[end_to_end_id]
            if not row['SettlementDate'] and booking_date:
                row['SettlementDate'] = booking_date.isoformat()
                if row['PaymentDate']:
                    payment_dt = datetime.fromisoformat(row['PaymentDate'])
                    diff = (booking_date - payment_dt).total_seconds() / 60
                    row['ProcessingTimeMinutes'] = round(diff, 2)

# Final FactPayments write
with open(os.path.join(OUTPUT_DIR, 'FactPayments.csv'), 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fact_rows[0].keys())
    writer.writeheader()
    writer.writerows(fact_rows)

print("FactPayments.csv reconciled with camt.054")

# ========================
# DIMENSION TABLES
# ========================
print("Generating dimension tables ...")

fact_df = pd.read_csv(os.path.join(OUTPUT_DIR, 'FactPayments.csv'), dtype=str)

# DimStatus with mapping
status_mapping = {
    "ACSC": "Accepted Settlement Completed — Transaction has been completed successfully",
    "ACSP": "Accepted Settlement in Process — Transaction is being processed and will be settled"
}
dim_status = fact_df[['StatusCode']].dropna().drop_duplicates().sort_values(by='StatusCode')
dim_status['Description'] = dim_status['StatusCode'].map(status_mapping).fillna(dim_status['StatusCode'])
dim_status.to_csv(os.path.join(OUTPUT_DIR, 'DimStatus.csv'), index=False)

# DimCurrency
dim_currency = fact_df[['CurrencyCode']].dropna().drop_duplicates().sort_values(by='CurrencyCode')
dim_currency['CurrencyName'] = dim_currency['CurrencyCode']
dim_currency['CurrencySymbol'] = ''
dim_currency.to_csv(os.path.join(OUTPUT_DIR, 'DimCurrency.csv'), index=False)

# DimPurposeCode with mapping
purpose_mapping = {
    "DIVD": "Dividends",
    "EDUC": "Education",
    "GOVT": "Government Payments",
    "LOAN": "Loan",
    "PENS": "Pension",
    "ROYA": "Royalties",
    "SALA": "Salary",
    "SERV": "Services",
    "SUPP": "Supplier Payment",
    "TAXS": "Taxes"
}
dim_purpose = fact_df[['PurposeCode']].dropna().drop_duplicates().sort_values(by='PurposeCode')
dim_purpose['Description'] = dim_purpose['PurposeCode'].map(purpose_mapping).fillna(dim_purpose['PurposeCode'])
dim_purpose.to_csv(os.path.join(OUTPUT_DIR, 'DimPurposeCode.csv'), index=False)

# DimDate
date_cols = ['PaymentDate', 'SettlementDate']
dates_series = pd.to_datetime(
    pd.Series(fact_df[date_cols].values.ravel('K')),
    errors='coerce',
    utc=True
)
dates_series = dates_series.dt.tz_localize(None)
dates_series = dates_series.dropna().dt.normalize().drop_duplicates().sort_values()

dim_date = pd.DataFrame({'Date': dates_series})
dim_date['Year'] = dim_date['Date'].dt.year
dim_date['MonthNumber'] = dim_date['Date'].dt.month
dim_date['Month'] = dim_date['Date'].dt.strftime('%B')
dim_date['Quarter'] = dim_date['Date'].dt.quarter
dim_date['Day'] = dim_date['Date'].dt.day
dim_date['WeekNumber'] = dim_date['Date'].dt.isocalendar().week
dim_date.to_csv(os.path.join(OUTPUT_DIR, 'DimDate.csv'), index=False, date_format='%Y-%m-%d')

print("ETL complete. All tables are ready in the 'output' folder.")
