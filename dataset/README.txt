ISO 20022 Synthetic Dataset (Version .001.09)

Structure (grouped per day):
  YYYY-MM-DD/
    pain001_YYYY-MM-DD.xml (pain.001.001.09)
    pacs008_YYYY-MM-DD.xml (pacs.008.001.09)
    pacs002_YYYY-MM-DD.xml (pacs.002.001.09)
    camt054_YYYY-MM-DD.xml (camt.054.001.09)

Date Range: 2025-09-21 .. 2025-10-04
Transactions per day: ~380
Total transactions: ~5320

Linking Keys:
- InstrId and EndToEndId are consistent across pain.001 -> pacs.008 -> pacs.002 -> camt.054 entries
- Use these to join during ETL

Suggested Power BI ETL Steps:
1) Get Data -> XML -> select a file (e.g., pacs008_YYYY-MM-DD.xml)
2) In Power Query, expand nodes to reach CdtTrfTxInf (for pacs.008, pain.001), OrgnlGrpInfAndSts/TxInfAndSts (pacs.002), and Ntfctn/Ntry (camt.054).
3) Create queries for each message type and add columns:
   - pacs.008: MsgId, CreDtTm, IntrBkSttlmAmt@Ccy, IntrBkSttlmAmt (value), IntrBkSttlmDt, Dbtr/Cdtr info, Debtor/Creditor BICs, Purp/Cd, EndToEndId, InstrId, ChrgBr
   - pain.001: InstdAmt@Ccy, InstdAmt, Cdtr data, EndToEndId, InstrId, ReqdExctnDt
   - pacs.002: TxSts (ACSP/RJCT/etc), OrgnlInstrId, OrgnlEndToEndId, OrgnlMsgId
   - camt.054: Ntry/Amt@Ccy, Ntry/Amt, Ntry/ValDt, TxDtls/Refs/EndToEndId and InstrId
4) Create a star schema:
   - FactPayments (from pacs.008) with Amount, Currency, Settlement Date, Debtor/Creditor IDs, Purpose, BICs
   - DimParty (Debtor & Creditor), DimCurrency, DimPurpose, DimStatus, DimDate
5) Build dashboards:
   - Overview: KPIs, trends, maps by country, purpose breakdown
   - Operations: corridor flows by BIC, processing times (pain->pacs->camt)
   - Reconciliation: pain vs pacs vs camt matching by EndToEndId/InstrId
   - Compliance: high-value, purpose codes, corridors
   - Analytics: forecasting, anomalies

Notes:
- All company names, BICs, IBANs are synthetic (for demo only).
- Status distribution in pacs.002 skews toward ACSP with some RJCT/PDNG.
- Amounts are randomly distributed with occasional high values.
