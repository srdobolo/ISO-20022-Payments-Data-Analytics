# file: generate_pain001.py
from typing import Optional, List, Dict
from xml.etree.ElementTree import Element, SubElement, ElementTree, register_namespace
from xml.dom import minidom
from datetime import datetime, date
from decimal import Decimal
from io import BytesIO
import uuid

# Namespace para pain.001.001.09
PAIN001_NS = "urn:iso:std:iso:20022:tech:xsd:pain.001.001.09"

# Registar o namespace como *default* (evita ns0:)
register_namespace('', PAIN001_NS)

# ------------ Helpers ------------

def _el(parent, tag, text: Optional[str] = None, attrib: Optional[Dict[str, str]] = None, ns: str = PAIN001_NS):
    """Cria elemento com namespace default e texto opcional."""
    e = SubElement(parent, f"{{{ns}}}{tag}", attrib or {})
    if text is not None:
        e.text = text
    return e

def _sum_amounts(transfers: List[dict]) -> Decimal:
    total = Decimal("0.00")
    for t in transfers:
        total += Decimal(str(t["amount"]))
    return total

def _serialize_with_decl(root: Element) -> bytes:
    """Serializa com declaração XML usando ElementTree.write -> BytesIO (compat amplo)."""
    bio = BytesIO()
    ElementTree(root).write(bio, encoding="utf-8", xml_declaration=True, method="xml")
    return bio.getvalue()

def _pretty(xml_bytes: bytes) -> bytes:
    """Indentação bonita (compatível 3.9+)."""
    dom = minidom.parseString(xml_bytes)
    pretty = dom.toprettyxml(indent="  ", encoding="utf-8")
    return pretty

# ------------ Gerador ------------

def generate_pain001_xml(
    debtor_name: str,
    debtor_iban: str,
    debtor_bic: str,
    requested_exec_date: date,
    transfers: List[dict],
    message_id: Optional[str] = None,
    payment_info_id: Optional[str] = None,
    created_datetime_utc: Optional[datetime] = None,
    payment_method: str = "TRF",
) -> bytes:
    """
    transfers: lista de dicts com, por ex.:
      {
        "instr_id": "INST-20250921-00000",
        "end_to_end_id": "E2E-20250921-00000",
        "amount": 1027874.86,          # numérico ou string
        "currency": "GBP",
        "svc_level": "NURG",           # ex.: "SEPA", "NURG"
        "instr_prty": "NORM",          # ex.: "HIGH"/"NORM"
        "ultimate_debtor": "Corp_Initiator_01_00",
        "creditor_name": "Peter Dubois",
        "creditor_address": {          # opcional
            "StrtNm": "Musterstrasse",
            "BldgNb": "22",
            "TwnNm": "Berlin",
            "Ctry": "DE"
        },
        "creditor_iban": "DE7133045310603257969962",
        "creditor_bic": "HYVEDEMMXXX",
        "remittance_info": "Ref 2025-09-0000",
        "purpose_code": "SERV"
      }
    """
    # IDs e contagens
    msg_id = message_id or "PAIN-{date}-{debtor}-{sufx}".format(
        date=datetime.utcnow().strftime('%Y-%m-%d'),
        debtor=debtor_name.replace(' ', '_'),
        sufx=uuid.uuid4().hex[:8],
    )
    pmt_inf_id = payment_info_id or "PMTINF-{stamp}".format(
        stamp=datetime.utcnow().strftime('%Y-%m-%d-%H%M%S')
    )
    nb_txs = str(len(transfers))
    ctrl_sum = "{:.2f}".format(_sum_amounts(transfers))
    created_ts = (created_datetime_utc or datetime.utcnow()).replace(microsecond=0).isoformat() + "Z"

    # Raiz
    Document = Element("{%s}Document" % PAIN001_NS)
    # (não precisamos de Document.set("xmlns", ...) porque register_namespace já força default xmlns)

    # CstmrCdtTrfInitn
    CstmrCdtTrfInitn = _el(Document, "CstmrCdtTrfInitn")

    # ---- GrpHdr ----
    GrpHdr = _el(CstmrCdtTrfInitn, "GrpHdr")
    _el(GrpHdr, "MsgId", msg_id)
    _el(GrpHdr, "CreDtTm", created_ts)
    _el(GrpHdr, "NbOfTxs", nb_txs)
    _el(GrpHdr, "CtrlSum", ctrl_sum)
    InitgPty = _el(GrpHdr, "InitgPty")
    _el(InitgPty, "Nm", debtor_name)

    # ---- PmtInf ----
    PmtInf = _el(CstmrCdtTrfInitn, "PmtInf")
    _el(PmtInf, "PmtInfId", pmt_inf_id)
    _el(PmtInf, "PmtMtd", payment_method)
    _el(PmtInf, "ReqdExctnDt", requested_exec_date.isoformat())

    Dbtr = _el(PmtInf, "Dbtr")
    _el(Dbtr, "Nm", debtor_name)

    DbtrAcct = _el(PmtInf, "DbtrAcct")
    Id = _el(DbtrAcct, "Id")
    _el(Id, "IBAN", debtor_iban)

    DbtrAgt = _el(PmtInf, "DbtrAgt")
    FinInstnId = _el(DbtrAgt, "FinInstnId")
    _el(FinInstnId, "BIC", debtor_bic)

    # ---- CdtTrfTxInf* ----
    for i, t in enumerate(transfers):
        tx = _el(PmtInf, "CdtTrfTxInf")

        # PmtId
        PmtId = _el(tx, "PmtId")
        _el(PmtId, "InstrId", t.get("instr_id") or "INST-{date}-{n:05d}".format(date=requested_exec_date.strftime('%Y%m%d'), n=i))
        _el(PmtId, "EndToEndId", t.get("end_to_end_id") or "E2E-{date}-{n:05d}".format(date=requested_exec_date.strftime('%Y%m%d'), n=i))

        # PmtTpInf
        if t.get("svc_level") or t.get("instr_prty"):
            PmtTpInf = _el(tx, "PmtTpInf")
            if t.get("svc_level"):
                SvcLvl = _el(PmtTpInf, "SvcLvl")
                _el(SvcLvl, "Cd", t["svc_level"])
            if t.get("instr_prty"):
                _el(PmtTpInf, "InstrPrty", t["instr_prty"])

        # Amount
        Amt = _el(tx, "Amt")
        _el(
            Amt,
            "InstdAmt",
            "{:.2f}".format(Decimal(str(t["amount"]))),
            attrib={"Ccy": t.get("currency", "EUR")},
        )

        # Ultimate Debtor (opcional)
        if t.get("ultimate_debtor"):
            UltmtDbtr = _el(tx, "UltmtDbtr")
            _el(UltmtDbtr, "Nm", t["ultimate_debtor"])

        # Creditor Agent
        if t.get("creditor_bic"):
            CdtrAgt = _el(tx, "CdtrAgt")
            FinInstnId2 = _el(CdtrAgt, "FinInstnId")
            _el(FinInstnId2, "BIC", t["creditor_bic"])

        # Creditor + endereço opcional
        Cdtr = _el(tx, "Cdtr")
        _el(Cdtr, "Nm", t["creditor_name"])
        addr = t.get("creditor_address")
        if isinstance(addr, dict) and any(addr.get(k) for k in ("StrtNm", "BldgNb", "TwnNm", "Ctry")):
            PstlAdr = _el(Cdtr, "PstlAdr")
            if addr.get("StrtNm"):
                _el(PstlAdr, "StrtNm", addr["StrtNm"])
            if addr.get("BldgNb"):
                _el(PstlAdr, "BldgNb", addr["BldgNb"])
            if addr.get("TwnNm"):
                _el(PstlAdr, "TwnNm", addr["TwnNm"])
            if addr.get("Ctry"):
                _el(PstlAdr, "Ctry", addr["Ctry"])

        # Creditor Account
        CdtrAcct = _el(tx, "CdtrAcct")
        Id2 = _el(CdtrAcct, "Id")
        _el(Id2, "IBAN", t["creditor_iban"])

        # Remittance Info (Ustrd)
        if t.get("remittance_info"):
            RmtInf = _el(tx, "RmtInf")
            _el(RmtInf, "Ustrd", t["remittance_info"])

        # Purpose
        if t.get("purpose_code"):
            Purp = _el(tx, "Purp")
            _el(Purp, "Cd", t["purpose_code"])

    # Serializar com declaração e indentar
    raw = _serialize_with_decl(Document)
    return _pretty(raw)

# ------------ Exemplo (igual ao teu formato) ------------
if __name__ == "__main__":
    transfers = [
        {
            "instr_id": "INST-20250921-00000",
            "end_to_end_id": "E2E-20250921-00000",
            "amount": 1027874.86,
            "currency": "GBP",
            "svc_level": "NURG",
            "instr_prty": "NORM",
            "ultimate_debtor": "Corp_Initiator_01_00",
            "creditor_name": "Peter Dubois",
            "creditor_address": {
                "StrtNm": "Musterstrasse",
                "BldgNb": "22",
                "TwnNm": "Berlin",
                "Ctry": "DE",
            },
            "creditor_iban": "DE7133045310603257969962",
            "creditor_bic": "HYVEDEMMXXX",
            "remittance_info": "Ref 2025-09-0000",
            "purpose_code": "SERV",
        }
    ]

    created_dt = datetime(2025, 9, 21, 8, 0, 0)  # 2025-09-21T08:00:00Z
    msg_id = "PAIN-2025-09-21-Global_Finance_SpA-97dab3c3"
    pmtinf_id = "PMTINF-2025-09-21-165141"

    xml_bytes = generate_pain001_xml(
        debtor_name="Global Finance SpA",
        debtor_iban="SE6510619244403548659086",
        debtor_bic="NDEASESSXXX",
        requested_exec_date=date(2025, 9, 21),
        transfers=transfers,
        message_id=msg_id,
        payment_info_id=pmtinf_id,
        created_datetime_utc=created_dt,
    )

    with open("pain001_sample.xml", "wb") as f:
        f.write(xml_bytes)

    print("Gerado: pain001_sample.xml")
