# Dataset Structure

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

## Structure of an ISO 20022 Message Name

```bash
<business area>.<message identifier>.<variant>.<version>
```

## Business Area Codes

- pain - PAyment INitiation - Used between customer → bank for initiating payments (e.g., bulk credit transfers, direct debits).
- pacs - PAyment Clearing and Settlement - Used between financial institutions (bank ↔ bank) for interbank payment processing.
- camt - CAsh Management - Used for account reporting, statements, notifications, and reconciliations.
- reda - Reference Data - Used for exchanging static reference data like business party info.
- auth - Authorities - Messages exchanged with regulatory or supervisory authorities.

## Common Message Identifiers

- pain.001 - Customer Credit Transfer Initiation - Used by corporates/customers to instruct their bank to make credit transfers (e.g., salary batches, supplier payments).
- pacs.008 - FI to FI Customer Credit Transfer - Used between banks to move the actual funds (interbank leg) after initiation.
- pacs.002 - FI to FI Payment Status Report - Provides status updates about interbank payment messages (e.g., accepted, rejected, pending).
- camt.054 - Bank to Customer Debit/Credit Notification - Provides reports of credits and debits booked on the account — often used for automated reconciliation by corporates.
