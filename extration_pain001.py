import os
from lxml import etree
import pandas as pd

INPUT_DIR = "synthetic_iso20022"
OUTPUT_DIR = "extraction_iso20022"
os.makedirs(OUTPUT_DIR, exist_ok=True)
NS = {"ns": "urn:iso:std:iso:20022:tech:xsd:pain.001.001.12"}

def get_text(node, path):
    elem = node.find(path, namespaces=NS)
    return elem.text if elem is not None else None

rows = []

for filename in os.listdir(INPUT_DIR):
    if not filename.startswith("pain001") or not filename.endswith(".xml"):
        continue

    filepath = os.path.join(INPUT_DIR, filename)
    print(f"📥 Parsing {filepath}")
    tree = etree.parse(filepath)
    root = tree.getroot()

    # --- Group Header ---
    msg_id = get_text(root, ".//ns:GrpHdr/ns:MsgId")
    cre_dt_tm = get_text(root, ".//ns:GrpHdr/ns:CreDtTm")
    nb_of_txs = get_text(root, ".//ns:GrpHdr/ns:NbOfTxs")
    ctrl_sum = get_text(root, ".//ns:GrpHdr/ns:CtrlSum")
    initiating_party_name = get_text(root, ".//ns:GrpHdr/ns:InitgPty/ns:Nm")

    # --- Payment Info ---
    payment_info_id = get_text(root, ".//ns:PmtInf/ns:PmtInfId")
    payment_method = get_text(root, ".//ns:PmtInf/ns:PmtMtd")
    requested_execution_date = get_text(root, ".//ns:PmtInf/ns:ReqdExctnDt")

    debtor_name = get_text(root, ".//ns:PmtInf/ns:Dbtr/ns:Nm")
    debtor_iban = get_text(root, ".//ns:PmtInf/ns:DbtrAcct/ns:Id/ns:IBAN")
    debtor_bic = get_text(root, ".//ns:PmtInf/ns:DbtrAgt/ns:FinInstnId/ns:BIC")

    # --- Transactions ---
    for tx in root.findall(".//ns:CdtTrfTxInf", namespaces=NS):
        instr_id = get_text(tx, "./ns:PmtId/ns:InstrId")
        end_to_end_id = get_text(tx, "./ns:PmtId/ns:EndToEndId")

        amt_elem = tx.find("./ns:Amt/ns:InstdAmt", namespaces=NS)
        amount = float(amt_elem.text) if amt_elem is not None else None
        currency = amt_elem.get("Ccy") if amt_elem is not None else None

        creditor_name = get_text(tx, "./ns:Cdtr/ns:Nm")
        creditor_iban = get_text(tx, "./ns:CdtrAcct/ns:Id/ns:IBAN")
        creditor_bic = get_text(tx, "./ns:CdtrAgt/ns:FinInstnId/ns:BIC")

        # Creditor Postal Address
        creditor_street = get_text(tx, "./ns:Cdtr/ns:PstlAdr/ns:StrtNm")
        creditor_building_number = get_text(tx, "./ns:Cdtr/ns:PstlAdr/ns:BldgNb")
        creditor_town = get_text(tx, "./ns:Cdtr/ns:PstlAdr/ns:TwnNm")
        creditor_country = get_text(tx, "./ns:Cdtr/ns:PstlAdr/ns:Ctry")

        purpose_code = get_text(tx, "./ns:Purp/ns:Cd")
        remittance = get_text(tx, "./ns:RmtInf/ns:Ustrd")

        rows.append({
            # Group Header
            "MessageId": msg_id,
            "CreationDateTime": cre_dt_tm,
            "NumberOfTransactions": int(nb_of_txs) if nb_of_txs else None,
            "ControlSum": float(ctrl_sum) if ctrl_sum else None,
            "InitiatingPartyName": initiating_party_name,

            # Payment Info
            "PaymentInformationId": payment_info_id,
            "PaymentMethod": payment_method,
            "RequestedExecutionDate": requested_execution_date,

            # Transaction Level
            "InstructionId": instr_id,
            "EndToEndId": end_to_end_id,
            "Amount": amount,
            "Currency": currency,

            # Debtor
            "DebtorName": debtor_name,
            "DebtorIBAN": debtor_iban,
            "DebtorBIC": debtor_bic,

            # Creditor
            "CreditorName": creditor_name,
            "CreditorIBAN": creditor_iban,
            "CreditorBIC": creditor_bic,
            "CreditorStreet": creditor_street,
            "CreditorBuildingNumber": creditor_building_number,
            "CreditorTown": creditor_town,
            "CreditorCountry": creditor_country,

            # Other
            "PurposeCode": purpose_code,
            "RemittanceInformation": remittance,
            "SourceFile": filename
        })

# --- Final table ---
df = pd.DataFrame(rows)
df.sort_values(by=["CreationDateTime", "MessageId"], inplace=True)

output_csv = os.path.join(OUTPUT_DIR, "pain001_aggregated.csv")
df.to_csv(output_csv, index=False)
print(f"✅ Aggregated {len(df)} transactions with Group Header + Address fields → {output_csv}")