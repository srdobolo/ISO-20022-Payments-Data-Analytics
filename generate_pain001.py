import os
import random
import uuid
from datetime import datetime, timedelta, UTC
from faker import Faker
from lxml import etree

# Initialize Faker for realistic names, addresses, BICs, etc.
fake = Faker()
Faker.seed(42)

# Output folder for generated XML files
OUTPUT_DIR = "synthetic_iso20022"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Common ISO 20022 lists
PURPOSE_CODES = ["SALA", "SUPP", "TAXS", "TRAD", "DIVD", "INTC", "GOVT", "PENS"]
CURRENCIES = ["EUR", "USD", "GBP", "CHF", "PLN", "CAD", "JPY"]

# Approximate exchange rates to EUR (for amount scaling)
CURRENCY_RATES = {
    "EUR": 1.0,
    "USD": 0.92,
    "GBP": 1.17,
    "CHF": 1.05,
    "PLN": 0.22,
    "CAD": 0.68,
    "JPY": 0.0062
}

# Purpose-specific EUR ranges
PURPOSE_AMOUNT_RANGES = {
    "PENS": (500, 5000),
    "SALA": (870, 10000)
}

# -----------------------------
# Helper Functions
# -----------------------------
def random_date(start, end):
    """Generate a random datetime between two datetimes."""
    return start + timedelta(seconds=random.randint(0, int((end - start).total_seconds())))

def make_iban(country="DE"):
    """Generate a pseudo-random IBAN (not checksum-valid but structurally plausible)."""
    return f"{country}{random.randint(10,99)}{fake.bban()}"

def iso_now():
    """Generate a timezone-aware ISO 8601 UTC timestamp without microseconds."""
    return datetime.now(UTC).replace(microsecond=0).isoformat()

def random_amount_for_purpose(purpose, currency):
    """
    Generate a realistic amount for a given purpose code,
    scaled to the target currency using approximate FX rates.
    """
    # Select EUR amount range based on purpose
    if purpose in PURPOSE_AMOUNT_RANGES:
        min_eur, max_eur = PURPOSE_AMOUNT_RANGES[purpose]
    else:
        min_eur, max_eur = 5, 10000

    eur_amount = random.uniform(min_eur, max_eur)
    rate = CURRENCY_RATES.get(currency, 1.0)
    converted = eur_amount / rate
    return round(converted, 2), eur_amount

# -----------------------------
# Main XML Generation Function
# -----------------------------
def generate_pain001(file_idx=1, n_transactions=50):
    ns = {None: "urn:iso:std:iso:20022:tech:xsd:pain.001.001.12"}
    root = etree.Element("Document", nsmap=ns)
    cstmr = etree.SubElement(root, "CstmrCdtTrfInitn")

    # === Group Header ===
    grp_hdr = etree.SubElement(cstmr, "GrpHdr")
    msg_id = f"MSG{file_idx}-{uuid.uuid4().hex[:8]}"
    etree.SubElement(grp_hdr, "MsgId").text = msg_id
    etree.SubElement(grp_hdr, "CreDtTm").text = iso_now()
    etree.SubElement(grp_hdr, "NbOfTxs").text = str(n_transactions)

    # Control sum in EUR
    total_control_sum_eur = 0.0

    # Debtor name (also used for InitiatingPartyName)
    debtor_name = fake.name()
    initg_party = etree.SubElement(grp_hdr, "InitgPty")
    etree.SubElement(initg_party, "Nm").text = debtor_name

    # === Payment Information block ===
    pmt_inf = etree.SubElement(cstmr, "PmtInf")
    pmt_inf_id = f"PMT-{uuid.uuid4().hex[:6]}"
    etree.SubElement(pmt_inf, "PmtInfId").text = pmt_inf_id
    etree.SubElement(pmt_inf, "PmtMtd").text = "TRF"

    exec_dt = random_date(datetime(2023, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC))
    etree.SubElement(pmt_inf, "ReqdExctnDt").text = exec_dt.date().isoformat()

    # Debtor
    dbtr = etree.SubElement(pmt_inf, "Dbtr")
    etree.SubElement(dbtr, "Nm").text = debtor_name

    dbtr_acct = etree.SubElement(pmt_inf, "DbtrAcct")
    dbtr_id = etree.SubElement(dbtr_acct, "Id")
    etree.SubElement(dbtr_id, "IBAN").text = make_iban("DE")

    dbtr_agt = etree.SubElement(pmt_inf, "DbtrAgt")
    fin = etree.SubElement(dbtr_agt, "FinInstnId")
    etree.SubElement(fin, "BIC").text = fake.swift8()

    # === Transactions ===
    for i in range(n_transactions):
        cdt_trf = etree.SubElement(pmt_inf, "CdtTrfTxInf")

        # Payment Identifiers
        pmt_id = etree.SubElement(cdt_trf, "PmtId")
        instr_id = f"INSTR-{i+1}"
        end_to_end_id = f"E2E-{uuid.uuid4().hex[:10]}"
        etree.SubElement(pmt_id, "InstrId").text = instr_id
        etree.SubElement(pmt_id, "EndToEndId").text = end_to_end_id

        # PurposeCode first, to determine amount range
        purpose_code = random.choice(PURPOSE_CODES)

        # Currency & Amount
        currency = random.choice(CURRENCIES)
        amount_value, eur_equivalent = random_amount_for_purpose(purpose_code, currency)
        total_control_sum_eur += eur_equivalent

        amt = etree.SubElement(cdt_trf, "Amt")
        etree.SubElement(amt, "InstdAmt", Ccy=currency).text = f"{amount_value:.2f}"

        # Creditor
        cdtr = etree.SubElement(cdt_trf, "Cdtr")
        etree.SubElement(cdtr, "Nm").text = fake.name()

        pstl = etree.SubElement(cdtr, "PstlAdr")
        etree.SubElement(pstl, "StrtNm").text = fake.street_name()
        etree.SubElement(pstl, "BldgNb").text = str(random.randint(1, 200))
        etree.SubElement(pstl, "TwnNm").text = fake.city()

        # IBAN determines CreditorCountry
        country_code = random.choice(["FR", "ES", "IT", "PT", "NL", "BE", "DE", "PL", "GB"])
        creditor_iban = make_iban(country_code)
        etree.SubElement(pstl, "Ctry").text = country_code

        cdtr_acct = etree.SubElement(cdt_trf, "CdtrAcct")
        cdtr_id = etree.SubElement(cdtr_acct, "Id")
        etree.SubElement(cdtr_id, "IBAN").text = creditor_iban

        cdtr_agt = etree.SubElement(cdt_trf, "CdtrAgt")
        fin2 = etree.SubElement(cdtr_agt, "FinInstnId")
        etree.SubElement(fin2, "BIC").text = fake.swift8()

        # Purpose & Remittance
        etree.SubElement(etree.SubElement(cdt_trf, "Purp"), "Cd").text = purpose_code
        rmt_inf = etree.SubElement(cdt_trf, "RmtInf")
        etree.SubElement(rmt_inf, "Ustrd").text = fake.text(max_nb_chars=40)

    # Set Control Sum in EUR
    etree.SubElement(grp_hdr, "CtrlSum").text = f"{total_control_sum_eur:.2f}"

    # Write XML to file
    filename = os.path.join(OUTPUT_DIR, f"pain001_{file_idx}.xml")
    tree = etree.ElementTree(root)
    tree.write(filename, pretty_print=True, xml_declaration=True, encoding="UTF-8")
    return filename

# -----------------------------
# Batch Generation Example
# -----------------------------
if __name__ == "__main__":
    for idx in range(1, 6):
        n_tx = random.randint(10, 120)
        file_path = generate_pain001(idx, n_tx)
        print(f"✅ Generated {file_path} with {n_tx} transactions.")
