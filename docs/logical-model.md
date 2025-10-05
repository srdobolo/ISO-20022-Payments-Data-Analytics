# Logical Data Model

This document defines the logical data model for the ISO 20022 Payments Data Analytics project.
It specifies the entities, attributes, keys, and relationships required to support analytical dashboards in Power BI and other BI tools.

## FactPayments

| Attribute             | Data Type           | Key | Description                                                 |
| --------------------- | ------------------- | --- | ----------------------------------------------------------- |
| **PaymentID**         | VARCHAR             | PK  | Unique identifier per transaction (e.g., `MsgId-InstrId`)   |
| MsgId                 | VARCHAR             |     | Message identifier from pacs.008                            |
| InstrId               | VARCHAR             |     | Instruction identifier                                      |
| EndToEndId            | VARCHAR             |     | End-to-end reference linking pain.001 → pacs.008 → camt.054 |
| PaymentDate           | DATETIME (ISO 8601) | FK  | Links to DimDateTime_Payment                                |
| SettlementDate        | DATETIME (ISO 8601) | FK  | Links to DimDateTime_Settlement                             |
| Amount                | DECIMAL(18,2)       |     | Transaction amount                                          |
| CurrencyCode          | VARCHAR(3)          | FK  | ISO 4217 currency code (e.g., EUR, USD)                     |
| DebtorID              | VARCHAR             | FK  | Links to DimParty_Debtor                                    |
| CreditorID            | VARCHAR             | FK  | Links to DimParty_Creditor                                  |
| DebtorAgentBIC        | VARCHAR(11)         |     | BIC of debtor’s bank                                        |
| CreditorAgentBIC      | VARCHAR(11)         |     | BIC of creditor’s bank                                      |
| PurposeCode           | VARCHAR(4)          | FK  | ISO 20022 Purpose Code (e.g., SALA, SUPP)                   |
| StatusCode            | VARCHAR(4)          | FK  | ISO 20022 Status Code (e.g., ACSP, RJCT)                    |
| ProcessingTimeMinutes | DECIMAL(10,2)       |     | Derived: settlement − payment time in minutes               |

## DimParty_Debtor

| Attribute   | Data Type | Key | Description                                 |
| ----------- | --------- | --- | ------------------------------------------- |
| PartyID     | VARCHAR   | PK  | Unique ID for debtor entity                 |
| Name        | VARCHAR   |     | Name of debtor (individual or organization) |
| IBAN        | VARCHAR   |     | Debtor account IBAN                         |
| CountryCode | CHAR(2)   |     | ISO country code of debtor                  |

## DimParty_Creditor

| Attribute   | Data Type | Key | Description                                   |
| ----------- | --------- | --- | --------------------------------------------- |
| PartyID     | VARCHAR   | PK  | Unique ID for creditor entity                 |
| Name        | VARCHAR   |     | Name of creditor (individual or organization) |
| IBAN        | VARCHAR   |     | Creditor account IBAN                         |
| CountryCode | CHAR(2)   |     | ISO country code of creditor                  |

## DimCurrency

| Attribute      | Data Type  | Key | Description               |
| -------------- | ---------- | --- | ------------------------- |
| CurrencyCode   | VARCHAR(3) | PK  | ISO 4217 currency code    |
| CurrencyName   | VARCHAR    |     | Full name of the currency |
| CurrencySymbol | VARCHAR    |     | Symbol (€, $, £)          |

## DimPurposeCode

| Attribute   | Data Type  | Key | Description                                      |
| ----------- | ---------- | --- | ------------------------------------------------ |
| PurposeCode | VARCHAR(4) | PK  | ISO 20022 Purpose Code                           |
| Description | VARCHAR    |     | Human-readable explanation (e.g., SALA = Salary) |

## DimStatus

| Attribute   | Data Type  | Key | Description                              |
| ----------- | ---------- | --- | ---------------------------------------- |
| StatusCode  | VARCHAR(4) | PK  | ISO 20022 Status Code (e.g., ACSP, RJCT) |
| Description | VARCHAR    |     | Meaning of the status                    |

## DimDateTime_Payment

| Attribute  | Data Type           | Key | Description                            |
| ---------- | ------------------- | --- | -------------------------------------- |
| DateTime   | DATETIME (ISO 8601) | PK  | Unique timestamp (to minute precision) |
| Date       | DATE                |     | Calendar date                          |
| Time       | TIME                |     | Time of day                            |
| Hour       | INT                 |     | Hour (0–23)                            |
| Minute     | INT                 |     | Minute (0–59)                          |
| Year       | INT                 |     | Calendar year                          |
| Month      | INT                 |     | Month number (1–12)                    |
| MonthName  | VARCHAR             |     | Month name (January, February, etc.)   |
| Day        | INT                 |     | Day of month                           |
| WeekNumber | INT                 |     | ISO week number                        |

## DimDateTime_Settlement

| Attribute  | Data Type           | Key | Description                            |
| ---------- | ------------------- | --- | -------------------------------------- |
| DateTime   | DATETIME (ISO 8601) | PK  | Unique timestamp (to minute precision) |
| Date       | DATE                |     | Calendar date                          |
| Time       | TIME                |     | Time of day                            |
| Hour       | INT                 |     | Hour (0–23)                            |
| Minute     | INT                 |     | Minute (0–59)                          |
| Year       | INT                 |     | Calendar year                          |
| Month      | INT                 |     | Month number (1–12)                    |
| MonthName  | VARCHAR             |     | Month name (January, February, etc.)   |
| Day        | INT                 |     | Day of month                           |
| WeekNumber | INT                 |     | ISO week number                        |
