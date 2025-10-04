ISO 20022 Enhanced Heavy-Load Synthetic Dataset (.001.09)

Scope:
- 14 daily folders (2025-09-21 .. 2025-10-04)
- ~1150 transactions/day (~16100 total)
- Message types: pain.001.001.09, pacs.008.001.09, pacs.002.001.09, camt.054.001.09
- Linked by InstrId and EndToEndId across all messages

Variability Highlights:
- Multiple PmtInf groups per pain.001 to vary Debtors and PmtMtd
- Varied InitgPty at GrpHdr, and UltmtDbtr per transaction to simulate on-behalf initiators
- PmtMtd mixed: TRF, CHK, TRA, DD
- PmtTpInf varied per transaction via SvcLvl (SEPA/URGP/NURG/PRPT) and InstrPrty (HIGH/NORM)
- Diverse currencies (EUR, USD, GBP, CHF, JPY, CAD, AUD, SEK)
- Multiple countries across EU/US/CH/SE/IE
- Realistic ChargeBearer distributions based on payment type
- Status patterns in pacs.002 segmented by amount and type with realistic rejection reasons
- Amounts sampled from retail/SME/business/treasury distributions

ETL Tips (Power BI):
1) Get Data > XML; create a query per message type.
2) Expand to nodes: 
   - pain.001: CstmrCdtTrfInitn/GrpHdr, PmtInf, PmtInf/CdtTrfTxInf
   - pacs.008: FIToFICstmrCdtTrf/GrpHdr, CdtTrfTxInf
   - pacs.002: FIToFIPmtStsRpt/OrgnlGrpInfAndSts/TxInfAndSts
   - camt.054: BkToCstmrDbtCdtNtfctn/Ntfctn/Ntry and Ntry/NtryDtls/TxDtls/Refs
3) Join on InstrId and EndToEndId (pain -> pacs -> pacs.002 -> camt.054).
4) Build star schema: FactPayments (from pacs.008), with dimensions for Date, Party (Debtor/Creditor), Currency, Purpose, Status, Method (PmtMtd), Type (SvcLvl/InstrPrty).
5) Use ChargeBearer, BICs, Countries for corridor & fee analysis. 
6) KPIs: volume, value, rejection rate, processing time (pain->pacs->camt), high-value flows, corridor heatmaps.

Note:
- This is a synthetic dataset for analytics/ETL practice only and may not satisfy all scheme-level validations.
