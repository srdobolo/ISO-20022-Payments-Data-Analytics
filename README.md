# ISO20022 Payments Dashboard

## 1. Resume

## 2. 📑 Index

- [1. Resume](#1-resume )
- [4. Objectives]
- [5. Fundamentals]
- [6. Dataset Structure]
- [7. Mission & Core Values]
- [8. Team Structure & User Roles]
- [9. Requirements]
- [10. Entities and Atributes with Data Types]
- [11. Entities Relational Diagram]
- [12. Relational Database]
- [13. Data Seeding]
- [14. SQL Simple Queries]
- [15. SQL Advanced Queries]

## User Roles

| Role                            | Dashboard Pages                                                 | Typical Actions                                                                                                                    | Access                                                                      |
|----------------------------------|------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **1. Executive / Management**   | 🟡 Page 1: Payments Overview                                    | • View KPIs, trends, top corridors. <br>• Drill into high-value transactions.                                                      | ✅ View-only (Power BI App or dashboard link)                                |
| **2. Operations Team**          | 🟢 Page 2: Operational Monitoring <br>🧾 Page 3: Reconciliation | • Monitor daily transactions & delays. <br>• Investigate operational bottlenecks. <br>• Drill through EndToEndId timelines.        | ✅ Viewer role with **date / currency / status filters**                     |
| **3. Finance & Reconciliation** | 🧾 Page 3: Reconciliation                                       | • Match pain.001 vs camt.054. <br>• Resolve unmatched transactions. <br>• Export reports to Excel if needed.                       | ✅ Viewer + Export permissions                                               |
| **4. Compliance / Regulatory**  | 🕵 Page 4: Regulatory / Compliance                              | • Filter by PurposeCode, corridor. <br>• Identify missing LEI or structured remittance. <br>• Export filtered lists for reporting. | ✅ Viewer + Export; may have access to specific RLS (e.g., by jurisdiction). |
| **5. Data Science / Analytics** | 📈 Page 5: Advanced Analytics                                   | • Develop forecasts, anomaly detection. <br>• Run custom Power BI or Python models.                                                | ✅ Contributor or shared dataset access                                      |

## Fundamentals

### Structure of an ISO 20022 Message Name

```bash
<business area>.<message identifier>.<variant>.<version>
```

### Business Area Codes

- pain - PAyment INitiation - Used between customer → bank for initiating payments (e.g., bulk credit transfers, direct debits).
- pacs - PAyment Clearing and Settlement - Used between financial institutions (bank ↔ bank) for interbank payment processing.
- camt - CAsh Management - Used for account reporting, statements, notifications, and reconciliations.
- reda - Reference Data - Used for exchanging static reference data like business party info.
- auth - Authorities - Messages exchanged with regulatory or supervisory authorities.

### Common Message Identifiers

- pain.001 - Customer Credit Transfer Initiation - Used by corporates/customers to instruct their bank to make credit transfers (e.g., salary batches, supplier payments).
- pacs.008 - FI to FI Customer Credit Transfer - Used between banks to move the actual funds (interbank leg) after initiation.
- pacs.002 - FI to FI Payment Status Report - Provides status updates about interbank payment messages (e.g., accepted, rejected, pending).
- camt.054 - Bank to Customer Debit/Credit Notification - Provides reports of credits and debits booked on the account — often used for automated reconciliation by corporates.

## Dataset Structure

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

## 🧠 Modelo Relacional Final (Power BI)

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



