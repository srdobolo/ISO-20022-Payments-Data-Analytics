# ISO20022 Payments Dashboard

## 1. Executive Summary

## 2. 📑 Index

- [1. Executive Summary](#1-executive-summary )
- [3. Business Fundamentals]
- [4. Dataset Structure]
- [5. Functional Requirements]
- [6. Non-Functional Requirements]
- [5. User Roles]
- [6. Objectives]
- [7. Mission & Core Values]
- [8. Team Structure & User Roles]
- [9. Requirements]
- [10. Entities and Atributes with Data Types]
- [11. Entities Relational Diagram]
- [12. Relational Database]
- [13. Data Seeding]
- [14. SQL Simple Queries]
- [15. SQL Advanced Queries]

## 3. Business Fundamentals

### 3.1 Structure of an ISO 20022 Message Name

```bash
<business area>.<message identifier>.<variant>.<version>
```

### 3.2 Business Area Codes

- pain - PAyment INitiation - Used between customer → bank for initiating payments (e.g., bulk credit transfers, direct debits).
- pacs - PAyment Clearing and Settlement - Used between financial institutions (bank ↔ bank) for interbank payment processing.
- camt - CAsh Management - Used for account reporting, statements, notifications, and reconciliations.
- reda - Reference Data - Used for exchanging static reference data like business party info.
- auth - Authorities - Messages exchanged with regulatory or supervisory authorities.

### 3.3 Common Message Identifiers

- pain.001 - Customer Credit Transfer Initiation - Used by corporates/customers to instruct their bank to make credit transfers (e.g., salary batches, supplier payments).
- pacs.008 - FI to FI Customer Credit Transfer - Used between banks to move the actual funds (interbank leg) after initiation.
- pacs.002 - FI to FI Payment Status Report - Provides status updates about interbank payment messages (e.g., accepted, rejected, pending).
- camt.054 - Bank to Customer Debit/Credit Notification - Provides reports of credits and debits booked on the account — often used for automated reconciliation by corporates.

## 4. Dataset Structure

```bash
/ISO20022_Sample_Data/
│
├── pain001/
│   ├── pain001_2025-09-21.xml
│   ├── pain001_2025-09-22.xml
│   └── ...
│
├── pacs008/
│   ├── pacs008_2025-09-21.xml
│   ├── pacs008_2025-09-22.xml
│   └── ...
│
├── pacs002/
│   ├── pacs002_2025-09-21.xml
│   ├── pacs002_2025-09-22.xml
│   └── ...
│
├── camt054/
│   ├── camt054_2025-09-21.xml
│   ├── camt054_2025-09-22.xml
│   └── ...
│
└── README.txt
```

## 5. Functional Requirements

This section defines the functional requirements for the ISO 20022 Payments Analytics project. The system must support the extraction, transformation, loading, and analysis of ISO 20022 payment messages (pain.001, pacs.008, pacs.002, camt.054) into a Power BI dashboard that enables operational, regulatory, and strategic insights.

### 5.1 ETL and Data Processing

- FR1: The system must ingest ISO 20022 XML files (pain.001, pacs.008, pacs.002, camt.054) from the designated data folders.
- FR2: The system must extract key fields from each file type, including identifiers (MsgId, EndToEndId), amounts, dates, BICs, PurposeCode, and StatusCode.
- FR3: The system must normalize dates to ISO 8601 format (YYYY-MM-DDTHH:MM:SS) for PaymentDate and SettlementDate fields.
- FR4: The ETL pipeline must enrich payment records by joining pacs.008 with pacs.002 and camt.054 using EndToEndId to populate settlement date and status information.
- FR5: The ETL must generate a star schema with:
    1. One Fact table: FactPayments
    2. Multiple Dimension tables: Parties (Debtor, Creditor), Currency, Purpose, Status, DateTime (Payment, Settlement)
- FR6: Each table must be exported in .csv format for ingestion into Power BI.

### 5.2 Data Model

- FR7: The FactPayments table must contain one row per transaction, identified by a unique PaymentID (MsgId + InstrId).
- FR8: DimParty tables must maintain distinct keys for Debtor and Creditor to support dual relationships.
- FR9: DimDateTime_Payment and DimDateTime_Settlement must provide temporal granularity down to the minute, with ISO 8601 DateTime as the primary key.
- FR10: All dimension tables must have unique primary keys and be linked to the fact table through foreign keys.

### 5.3 Dashboard Features

- FR11: The system must provide 5 Power BI pages:
    1. Payments Overview — KPIs, trends, maps, and top purpose codes.
    2. Operational Monitoring — daily processing metrics, delays, status breakdown.
    3. Reconciliation — pain.001 vs camt.054 matching via EndToEndId.
    4. Regulatory/Compliance — filters by PurposeCode, corridor analysis, missing data detection.
    5. Advanced Analytics — time-series forecasting, anomaly detection.
- FR12: Each dashboard must support filters for date, currency, status, and purpose.
- FR13: Drill-through navigation must allow users to trace a transaction through its lifecycle: pain.001 → pacs.008 → pacs.002 → camt.054.

### 5.4 Security & Access

- FR14: Row-level security (RLS) must be configurable to restrict data by business unit or region.
- FR15: Different user roles (Executive, Operations, Finance, Compliance, Data Science) must have tailored permissions for viewing, filtering, or exporting reports.

## 6. Non-Functional Requirements

This section defines the performance, security, and operational constraints for the ISO 20022 Payments Analytics project.

### 6.1 Performance

- NFR1: The ETL process must be able to process and transform at least 50,000 XML transactions within 15 minutes, ensuring scalability for high-volume payment datasets.
- NFR2: Power BI dashboards must load and respond to user interactions (filters, slicers, drill-downs) in under 5 seconds for datasets up to 1 million transactions.
- NFR3: Data transformations must be efficient and optimized to avoid redundant parsing of XML nodes.

### 6.2 Data Refresh & Availability

- NFR4: The ETL pipeline must support scheduled data refreshes (e.g., daily or hourly) to keep dashboards up to date with new ISO 20022 files.
- NFR5: Dashboards must maintain at least 99.5% availability during business hours.
- NFR6: The solution must allow incremental refresh in Power BI to avoid full dataset reloads when only new files are added.

### 6.3 Scalability

- NFR7: The system must support scaling to millions of payment records without requiring structural changes to the data model.
- NFR8: The ETL must be modular so that new ISO 20022 message types (e.g., pacs.009) can be integrated with minimal code changes.

### 6.4 Security & Compliance

- NFR9: All files and processed data must comply with GDPR and ISO 27001 standards.
- NFR10: Sensitive identifiers (e.g., IBANs, names) must be masked or pseudonymized in non-production environments.
- NFR11: Access to dashboards must be controlled through Azure AD / Microsoft 365 authentication with role-based access control.

### 6.5 Maintainability

- NFR12: All ETL scripts must be version-controlled (e.g., Git) and documented.
- NFR13: The data model must be self-describing, with consistent naming conventions and metadata for each table and field.
- NFR14: The solution must be easily maintainable by BI developers with standard Python (for ETL) and Power BI skills, without requiring niche technologies.

### 6.6 Reliability & Error Handling

- NFR15: The ETL process must include error logging and validation, flagging malformed XML files or missing required fields.
- NFR16: Failures during extraction or transformation must not corrupt existing outputs; partial failures should be isolated and logged.
- NFR17: The system must provide clear reprocessing mechanisms for failed files without manual data correction.

## 7. Technical Architecture

### 7.1 Technical Architecture Overview

                  ┌────────────────────┐
                  │   Pain.001 XML     │
                  └─────────┬──────────┘
                            │
                  ┌────────────────────┐
                  │   Pacs.008 XML     │
                  └─────────┬──────────┘
                            │
                  ┌────────────────────┐
                  │   Pacs.002 XML     │
                  └─────────┬──────────┘
                            │
                  ┌────────────────────┐
                  │   Camt.054 XML     │
                  └─────────┬──────────┘
                            │
                            ▼
                  ┌──────────────────────────────┐
                  │        Python ETL            │
                  │ - XML parsing (ElementTree)  │
                  │ - Fact & Dim generation      │
                  │ - DateTime role dimensions   │
                  └─────────┬────────────────────┘
                            │
                            ▼
             ┌─────────────────────────────────────┐
             │        Power BI Data Model          │
             │ FactPayments + Dim tables          │
             │ Role-playing dimensions for dates  │
             └─────────┬──────────────────────────┘
                            │
                            ▼
          ┌───────────────────────────────────────────┐
          │            Power BI Dashboards            │
          │ - Payments Overview                       │
          │ - Operational Monitoring                  │
          │ - Reconciliation                          │
          │ - Regulatory / Compliance                 │
          │ - Advanced Analytics                      │
          └───────────────────────────────────────────┘

### 7.2 Technology Stack

| Component                 | Technology / Tool                                                               |
| ------------------------- | ------------------------------------------------------------------------------- |
| **ETL**                   | Python 3.7+ with `xml.etree.ElementTree`, `pandas`                              |
| **File Ingestion**        | Local directory / secure network drive (scalable to Azure Data Lake)            |
| **Storage (Transformed)** | CSV files (Fact + Dim tables), easily replaceable with relational DB (e.g. SQL) |
| **Data Modeling (ERD)**   | [**Mermaid.js**](https://mermaid.js.org/) — for ER diagrams in Markdown/GitHub  |
| **BI Layer**              | Microsoft Power BI (Desktop + Service)                                          |
| **Access Control**        | Azure Active Directory (Azure AD) roles + Power BI Row-Level Security (RLS)     |
| **Version Control**       | GitHub or Azure DevOps for ETL scripts and documentation                        |

### 7.3 Data Model Principles

- Star Schema — One central Fact table (FactPayments) and multiple Dimension tables (Party, Currency, Status, Purpose, DateTime).
- Role-Playing Dimensions — Separate DimDateTime_Payment and DimDateTime_Settlement to avoid ambiguous date relationships.
- Surrogate Keys — Debtors and Creditors use separate IDs (Dxxxxx / Cxxxxx) to prevent relationship conflicts.
- ISO 8601 Datetime Format — All DateTime fields stored in UTC ISO 8601 format (e.g., 2025-09-21T08:00:00Z).

## 8. User Roles

| Role                            | Dashboard Pages                                                 | Typical Actions                                                                                                                    | Access                                                                      |
|----------------------------------|------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **1. Executive / Management**   | 🟡 Page 1: Payments Overview                                    | • View KPIs, trends, top corridors. • Drill into high-value transactions.                                                      | ✅ View-only (Power BI App or dashboard link)                                |
| **2. Operations Team**          | 🟢 Page 2: Operational Monitoring 🧾 Page 3: Reconciliation | • Monitor daily transactions & delays. • Investigate operational bottlenecks. • Drill through EndToEndId timelines.        | ✅ Viewer role with **date / currency / status filters**                     |
| **3. Finance & Reconciliation** | 🧾 Page 3: Reconciliation                                       | • Match pain.001 vs camt.054. • Resolve unmatched transactions. • Export reports to Excel if needed.                       | ✅ Viewer + Export permissions                                               |
| **4. Compliance / Regulatory**  | 🕵 Page 4: Regulatory / Compliance                              | • Filter by PurposeCode, corridor. • Identify missing LEI or structured remittance. • Export filtered lists for reporting. | ✅ Viewer + Export; may have access to specific RLS (e.g., by jurisdiction). |
| **5. Data Science / Analytics** | 📈 Page 5: Advanced Analytics                                   | • Develop forecasts, anomaly detection. • Run custom Power BI or Python models.                                                | ✅ Contributor or shared dataset access                                      |

## 9. Modelo Relacional Final (Power BI)

### Fact Table

```sql
FactPayments (
    PaymentID              VARCHAR PRIMARY KEY,
    MsgId                  VARCHAR,
    InstrId                VARCHAR,
    EndToEndId            VARCHAR,
    PaymentDate           DATETIME,  -- ISO 8601 (e.g. 2025-09-21T09:00:00)
    SettlementDate        DATETIME,  -- ISO 8601
    Amount                 DECIMAL(18,2),
    CurrencyCode          VARCHAR,
    DebtorID              VARCHAR,
    CreditorID            VARCHAR,
    DebtorAgentBIC       VARCHAR,
    CreditorAgentBIC     VARCHAR,
    PurposeCode          VARCHAR,
    StatusCode           VARCHAR,
    ProcessingTimeMinutes DECIMAL(10,2)
);
```

### Dimensions

```sql
DimParty_Debtor (
    PartyID       VARCHAR PRIMARY KEY,
    Name          VARCHAR,
    IBAN          VARCHAR,
    CountryCode   VARCHAR(2)
);
```

```sql
DimParty_Creditor (
    PartyID       VARCHAR PRIMARY KEY,
    Name          VARCHAR,
    IBAN          VARCHAR,
    CountryCode   VARCHAR(2)
);
```

```sql
DimCurrency (
    CurrencyCode    VARCHAR PRIMARY KEY,
    CurrencyName    VARCHAR,
    CurrencySymbol  VARCHAR
);
```

```sql
DimPurposeCode (
    PurposeCode   VARCHAR PRIMARY KEY,
    Description   TEXT
);
```

```sql
DimStatus (
    StatusCode    VARCHAR PRIMARY KEY,
    Description   TEXT
);
```

```sql
DimDateTime_Payment (
    DateTime     DATETIME PRIMARY KEY,  -- ISO 8601 (e.g. 2025-09-21T09:00:00)
    Date         DATE,
    Time         TIME,
    Hour         INTEGER,
    Minute       INTEGER,
    Year         INTEGER,
    Month        INTEGER,
    MonthName    VARCHAR,
    Day          INTEGER,
    WeekNumber   INTEGER
);
```

```sql
DimDateTime_Settlement (
    DateTime     DATETIME PRIMARY KEY,  -- ISO 8601
    Date         DATE,
    Time         TIME,
    Hour         INTEGER,
    Minute       INTEGER,
    Year         INTEGER,
    Month        INTEGER,
    MonthName    VARCHAR,
    Day          INTEGER,
    WeekNumber   INTEGER
);
```

## Logical Relationships

```sql
ALTER TABLE FactPayments
    ADD FOREIGN KEY (CurrencyCode) REFERENCES DimCurrency(CurrencyCode);

ALTER TABLE FactPayments
    ADD FOREIGN KEY (DebtorID) REFERENCES DimParty_Debtor(PartyID);

ALTER TABLE FactPayments
    ADD FOREIGN KEY (CreditorID) REFERENCES DimParty_Creditor(PartyID);

ALTER TABLE FactPayments
    ADD FOREIGN KEY (PurposeCode) REFERENCES DimPurposeCode(PurposeCode);

ALTER TABLE FactPayments
    ADD FOREIGN KEY (StatusCode) REFERENCES DimStatus(StatusCode);

ALTER TABLE FactPayments
    ADD FOREIGN KEY (PaymentDate) REFERENCES DimDateTime_Payment(DateTime);

ALTER TABLE FactPayments
    ADD FOREIGN KEY (SettlementDate) REFERENCES DimDateTime_Settlement(DateTime);
```