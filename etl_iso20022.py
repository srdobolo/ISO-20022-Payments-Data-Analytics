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
    """Robust amount & currency extraction."""
    el = tx.find('.//ns:IntrBkSttlmAmt', ns)
    if el is not None and el.text and el.attrib.get('Ccy'):
        return el.text.strip(), el.attrib.get('Ccy').strip()

    el = tx.find('.//ns:InstdAmt', ns)
    if el is not None and el.text and el.attrib.get('Ccy'):
        return el.text.strip(), el.attrib.get('Ccy').strip()

    el = tx.find('.//ns:Amt', ns)
    if el is not None:
        child = el.find('.//ns:InstdAmt', ns)
        if child is not None and child.text and child.attrib.get('Ccy'):
            return child.text.strip(), child.attrib.get('Ccy').strip()
        if el.text and el.attrib.get('Ccy'):
            return el.text.strip(), el.attrib.get('Ccy').strip()

    return None, None

def extract_debtor_triplet(root, tx, ns):
    """Prefer debtor data at transaction level; fallback to message level."""
    name = (tx.findtext('.//ns:Dbtr/ns:Nm', namespaces=ns)
            or root.findtext('.//ns:Dbtr/ns:Nm', namespaces=ns))
    iban = (tx.findtext('.//ns:DbtrAcct/ns:Id/ns:IBAN', namespaces=ns)
            or root.findtext('.//ns:DbtrAcct/ns:Id/ns:IBAN', namespaces=ns))
    ctry = (tx.findtext('.//ns:Dbtr/ns:PstlAdr/ns:Ctry', namespaces=ns)
            or root.findtext('.//ns:Dbtr/ns:PstlAdr/ns:Ctry', namespaces=ns))
    return name, iban, ctry

def build_hourly_dim_from_series(series: pd.Series):
    """
    Build ISO 8601 hourly DateTime dimension from datetime series.
    Output includes full DateTime, Date, Time, Hour, Minute, Year, Month, MonthName, Day, WeekNumber.
    """
    series = pd.to_datetime(series, errors='coerce', utc=True).dropna().dt.tz_localize(None)
    if series.empty:
        return pd.DataFrame(columns=[
            'DateTime','Date','Time','Hour','Minute','Year','Month','MonthName','Day','WeekNumber'
        ])
    start = series.min().floor('H')
    end = series.max().ceil('H')
    hourly = pd.date_range(start=start, end=end, freq='H')

    dim = pd.DataFrame({'DateTime': hourly.strftime('%Y-%m-%dT%H:%M:%S')})  # ✅ ISO 8601
    dim['Date'] = hourly.date
    dim['Time'] = hourly.strftime('%H:%M')
    dim['Hour'] = hourly.hour
    dim['Minute'] = hourly.minute
    dim['Year'] = hourly.year
    dim['Month'] = hourly.month
    dim['MonthName'] = hourly.strftime('%B')
    dim['Day'] = hourly.day
    dim['WeekNumber'] = hourly.isocalendar().week
    return dim

# ========================
# ROLE-PLAYING PARTY DIMS + PURPOSE LOOKUP
# ========================
debtors = {}
creditors = {}
debtor_counter = 1
creditor_counter = 1
purpose_lookup = {}

def get_or_create_debtor(name, iban, country):
    global debtor_counter
    key = (name or '', iban or '')
    if key not in debtors:
        debtors[key] = {
            'PartyID': f'D{debtor_counter:05d}',
            'Name': name,
            'IBAN': iban,
            'CountryCode': country
        }
        debtor_counter += 1
    return debtors[key]['PartyID']

def get_or_create_creditor(name, iban, country):
    global creditor_counter
    key = (name or '', iban or '')
    if key not in creditors:
        creditors[key] = {
            'PartyID': f'C{creditor_counter:05d}',
            'Name': name,
            'IBAN': iban,
            'CountryCode': country
        }
        creditor_counter += 1
    return creditors[key]['PartyID']

print("Extracting parties and purpose codes from pain.001 ...")

for file in glob.glob(os.path.join(pain001_dir, '*.xml')):
    tree = ET.parse(file)
    root = tree.getroot()
    ns = {'ns': root.tag.split('}')[0].strip('{')}

    # Debtor (message level)
    dbtr_name = root.find('.//ns:Dbtr/ns:Nm', ns)
    dbtr_iban = root.find('.//ns:DbtrAcct/ns:Id/ns:IBAN', ns)
    dbtr_country = root.find('.//ns:Dbtr/ns:PstlAdr/ns:Ctry', ns)
    get_or_create_debtor(
        dbtr_name.text if dbtr_name is not None else None,
        dbtr_iban.text if dbtr_iban is not None else None,
        dbtr_country.text if dbtr_country is not None else None
    )

    # Creditors per transaction + PurposeCode lookup
    for cdt in root.findall('.//ns:CdtTrfTxInf', ns):
        cdtr_name = cdt.find('.//ns:Cdtr/ns:Nm', ns)
        cdtr_iban = cdt.find('.//ns:CdtrAcct/ns:Id/ns:IBAN', ns)
        cdtr_country = cdt.find('.//ns:Cdtr/ns:PstlAdr/ns:Ctry', ns)
        get_or_create_creditor(
            cdtr_name.text if cdtr_name is not None else None,
            cdtr_iban.text if cdtr_iban is not None else None,
            cdtr_country.text if cdtr_country is not None else None
        )

        end_to_end = cdt.findtext('.//ns:PmtId/ns:EndToEndId', namespaces=ns)
        purpose_cd = cdt.findtext('.//ns:Purp/ns:Cd', namespaces=ns)
        if end_to_end and purpose_cd:
            purpose_lookup[(end_to_end or '').strip().upper()] = purpose_cd.strip()

# Write separate party dims
with open(os.path.join(OUTPUT_DIR, 'DimParty_Debtor.csv'), 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['PartyID', 'Name', 'IBAN', 'CountryCode'])
    writer.writeheader()
    writer.writerows(debtors.values())

with open(os.path.join(OUTPUT_DIR, 'DimParty_Creditor.csv'), 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['PartyID', 'Name', 'IBAN', 'CountryCode'])
    writer.writeheader()
    writer.writerows(creditors.values())

print(f"DimParty_Debtor.csv rows: {len(debtors)}")
print(f"DimParty_Creditor.csv rows: {len(creditors)}")
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

        # Amount & Currency
        amount, currency = extract_amount_currency(tx, ns)

        # Debtor (prefer tx-level)
        debtor_name, debtor_iban, debtor_country = extract_debtor_triplet(root, tx, ns)
        debtor_id = get_or_create_debtor(debtor_name, debtor_iban, debtor_country)

        # Creditor
        cdtr_name = tx.findtext('.//ns:Cdtr/ns:Nm', namespaces=ns)
        cdtr_iban = tx.findtext('.//ns:CdtrAcct/ns:Id/ns:IBAN', namespaces=ns)
        cdtr_country = tx.findtext('.//ns:Cdtr/ns:PstlAdr/ns:Ctry', namespaces=ns)
        creditor_id = get_or_create_creditor(cdtr_name, cdtr_iban, cdtr_country)

        # Agents, Purpose, Status init
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
# ENRICH WITH PACS.002
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
# ENRICH WITH CAMT.054
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
# DIMENSIONS
# ========================
print("Generating dimension tables ...")

fact_df = pd.read_csv(os.path.join(OUTPUT_DIR, 'FactPayments.csv'), dtype=str)

# DimStatus
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

# DimPurposeCode
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

# ========================
# DimDateTime (Payment & Settlement) - ISO 8601
# ========================
pay_datetime_series = pd.to_datetime(fact_df['PaymentDate'], errors='coerce', utc=True)
dim_datetime_payment = build_hourly_dim_from_series(pay_datetime_series)
dim_datetime_payment.to_csv(os.path.join(OUTPUT_DIR, 'DimDateTime_Payment.csv'), index=False)

settl_datetime_series = pd.to_datetime(fact_df['SettlementDate'], errors='coerce', utc=True)
dim_datetime_settlement = build_hourly_dim_from_series(settl_datetime_series)
dim_datetime_settlement.to_csv(os.path.join(OUTPUT_DIR, 'DimDateTime_Settlement.csv'), index=False)

print("ETL complete. Generated:")
print(" - FactPayments.csv")
print(" - DimParty_Debtor.csv")
print(" - DimParty_Creditor.csv")
print(" - DimStatus.csv")
print(" - DimCurrency.csv")
print(" - DimPurposeCode.csv")
print(" - DimDateTime_Payment.csv")
print(" - DimDateTime_Settlement.csv")