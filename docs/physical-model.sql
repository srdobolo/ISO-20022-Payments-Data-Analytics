-- ===========================================
-- PHYSICAL MODEL - ISO 20022 Payments Data Analytics
-- ===========================================

-- Drop existing tables if needed (be careful in prod)
DROP TABLE IF EXISTS FactPayments;
DROP TABLE IF EXISTS DimParty_Debtor;
DROP TABLE IF EXISTS DimParty_Creditor;
DROP TABLE IF EXISTS DimCurrency;
DROP TABLE IF EXISTS DimPurposeCode;
DROP TABLE IF EXISTS DimStatus;
DROP TABLE IF EXISTS DimDateTime_Payment;
DROP TABLE IF EXISTS DimDateTime_Settlement;

-- ============================
-- DIMENSIONS
-- ============================

CREATE TABLE DimParty_Debtor (
    PartyID        VARCHAR(50) PRIMARY KEY,
    Name           VARCHAR(255),
    IBAN           VARCHAR(34),
    CountryCode    CHAR(2)
);

CREATE TABLE DimParty_Creditor (
    PartyID        VARCHAR(50) PRIMARY KEY,
    Name           VARCHAR(255),
    IBAN           VARCHAR(34),
    CountryCode    CHAR(2)
);

CREATE TABLE DimCurrency (
    CurrencyCode   VARCHAR(3) PRIMARY KEY,
    CurrencyName   VARCHAR(100),
    CurrencySymbol VARCHAR(10)
);

CREATE TABLE DimPurposeCode (
    PurposeCode    VARCHAR(10) PRIMARY KEY,
    Description    VARCHAR(255)
);

CREATE TABLE DimStatus (
    StatusCode     VARCHAR(10) PRIMARY KEY,
    Description    VARCHAR(255)
);

CREATE TABLE DimDateTime_Payment (
    DateTime       TIMESTAMP PRIMARY KEY,
    Date           DATE NOT NULL,
    Time           TIME NOT NULL,
    Hour           INT,
    Minute         INT,
    Year           INT,
    Month          INT,
    MonthName      VARCHAR(20),
    Day            INT,
    WeekNumber     INT
);

CREATE TABLE DimDateTime_Settlement (
    DateTime       TIMESTAMP PRIMARY KEY,
    Date           DATE NOT NULL,
    Time           TIME NOT NULL,
    Hour           INT,
    Minute         INT,
    Year           INT,
    Month          INT,
    MonthName      VARCHAR(20),
    Day            INT,
    WeekNumber     INT
);

-- ============================
-- FACT TABLE
-- ============================

CREATE TABLE FactPayments (
    PaymentID              VARCHAR(100) PRIMARY KEY,
    MsgId                  VARCHAR(100),
    InstrId                VARCHAR(100),
    EndToEndId             VARCHAR(100),
    PaymentDate            TIMESTAMP,
    SettlementDate         TIMESTAMP,
    Amount                 DECIMAL(18,2),
    CurrencyCode           VARCHAR(3),
    DebtorID               VARCHAR(50),
    CreditorID             VARCHAR(50),
    DebtorAgentBIC         VARCHAR(11),
    CreditorAgentBIC       VARCHAR(11),
    PurposeCode            VARCHAR(10),
    StatusCode             VARCHAR(10),
    ProcessingTimeMinutes  DECIMAL(10,2),

    FOREIGN KEY (CurrencyCode) REFERENCES DimCurrency (CurrencyCode),
    FOREIGN KEY (DebtorID) REFERENCES DimParty_Debtor (PartyID),
    FOREIGN KEY (CreditorID) REFERENCES DimParty_Creditor (PartyID),
    FOREIGN KEY (PurposeCode) REFERENCES DimPurposeCode (PurposeCode),
    FOREIGN KEY (StatusCode) REFERENCES DimStatus (StatusCode),
    FOREIGN KEY (PaymentDate) REFERENCES DimDateTime_Payment (DateTime),
    FOREIGN KEY (SettlementDate) REFERENCES DimDateTime_Settlement (DateTime)
);

-- ============================
-- Indexes for performance
-- ============================

CREATE INDEX idx_factpayments_currency ON FactPayments (CurrencyCode);
CREATE INDEX idx_factpayments_debtor ON FactPayments (DebtorID);
CREATE INDEX idx_factpayments_creditor ON FactPayments (CreditorID);
CREATE INDEX idx_factpayments_paymentdate ON FactPayments (PaymentDate);
CREATE INDEX idx_factpayments_settlementdate ON FactPayments (SettlementDate);
CREATE INDEX idx_factpayments_status ON FactPayments (StatusCode);
CREATE INDEX idx_factpayments_purpose ON FactPayments (PurposeCode);-- ===========================================
-- PHYSICAL MODEL - ISO 20022 Payments Data Analytics
-- ===========================================

-- Drop existing tables if needed (be careful in prod)
DROP TABLE IF EXISTS FactPayments;
DROP TABLE IF EXISTS DimParty_Debtor;
DROP TABLE IF EXISTS DimParty_Creditor;
DROP TABLE IF EXISTS DimCurrency;
DROP TABLE IF EXISTS DimPurposeCode;
DROP TABLE IF EXISTS DimStatus;
DROP TABLE IF EXISTS DimDateTime_Payment;
DROP TABLE IF EXISTS DimDateTime_Settlement;

-- ============================
-- DIMENSIONS
-- ============================

CREATE TABLE DimParty_Debtor (
    PartyID        VARCHAR(50) PRIMARY KEY,
    Name           VARCHAR(255),
    IBAN           VARCHAR(34),
    CountryCode    CHAR(2)
);

CREATE TABLE DimParty_Creditor (
    PartyID        VARCHAR(50) PRIMARY KEY,
    Name           VARCHAR(255),
    IBAN           VARCHAR(34),
    CountryCode    CHAR(2)
);

CREATE TABLE DimCurrency (
    CurrencyCode   VARCHAR(3) PRIMARY KEY,
    CurrencyName   VARCHAR(100),
    CurrencySymbol VARCHAR(10)
);

CREATE TABLE DimPurposeCode (
    PurposeCode    VARCHAR(10) PRIMARY KEY,
    Description    VARCHAR(255)
);

CREATE TABLE DimStatus (
    StatusCode     VARCHAR(10) PRIMARY KEY,
    Description    VARCHAR(255)
);

CREATE TABLE DimDateTime_Payment (
    DateTime       TIMESTAMP PRIMARY KEY,
    Date           DATE NOT NULL,
    Time           TIME NOT NULL,
    Hour           INT,
    Minute         INT,
    Year           INT,
    Month          INT,
    MonthName      VARCHAR(20),
    Day            INT,
    WeekNumber     INT
);

CREATE TABLE DimDateTime_Settlement (
    DateTime       TIMESTAMP PRIMARY KEY,
    Date           DATE NOT NULL,
    Time           TIME NOT NULL,
    Hour           INT,
    Minute         INT,
    Year           INT,
    Month          INT,
    MonthName      VARCHAR(20),
    Day            INT,
    WeekNumber     INT
);

-- ============================
-- FACT TABLE
-- ============================

CREATE TABLE FactPayments (
    PaymentID              VARCHAR(100) PRIMARY KEY,
    MsgId                  VARCHAR(100),
    InstrId                VARCHAR(100),
    EndToEndId             VARCHAR(100),
    PaymentDate            TIMESTAMP,
    SettlementDate         TIMESTAMP,
    Amount                 DECIMAL(18,2),
    CurrencyCode           VARCHAR(3),
    DebtorID               VARCHAR(50),
    CreditorID             VARCHAR(50),
    DebtorAgentBIC         VARCHAR(11),
    CreditorAgentBIC       VARCHAR(11),
    PurposeCode            VARCHAR(10),
    StatusCode             VARCHAR(10),
    ProcessingTimeMinutes  DECIMAL(10,2),

    FOREIGN KEY (CurrencyCode) REFERENCES DimCurrency (CurrencyCode),
    FOREIGN KEY (DebtorID) REFERENCES DimParty_Debtor (PartyID),
    FOREIGN KEY (CreditorID) REFERENCES DimParty_Creditor (PartyID),
    FOREIGN KEY (PurposeCode) REFERENCES DimPurposeCode (PurposeCode),
    FOREIGN KEY (StatusCode) REFERENCES DimStatus (StatusCode),
    FOREIGN KEY (PaymentDate) REFERENCES DimDateTime_Payment (DateTime),
    FOREIGN KEY (SettlementDate) REFERENCES DimDateTime_Settlement (DateTime)
);

-- ============================
-- Indexes for performance
-- ============================

CREATE INDEX idx_factpayments_currency ON FactPayments (CurrencyCode);
CREATE INDEX idx_factpayments_debtor ON FactPayments (DebtorID);
CREATE INDEX idx_factpayments_creditor ON FactPayments (CreditorID);
CREATE INDEX idx_factpayments_paymentdate ON FactPayments (PaymentDate);
CREATE INDEX idx_factpayments_settlementdate ON FactPayments (SettlementDate);
CREATE INDEX idx_factpayments_status ON FactPayments (StatusCode);
CREATE INDEX idx_factpayments_purpose ON FactPayments (PurposeCode);
-- ===========================================
-- PHYSICAL MODEL - ISO 20022 Payments Data Analytics
-- ===========================================

-- Drop existing tables if needed (be careful in prod)
DROP TABLE IF EXISTS FactPayments;
DROP TABLE IF EXISTS DimParty_Debtor;
DROP TABLE IF EXISTS DimParty_Creditor;
DROP TABLE IF EXISTS DimCurrency;
DROP TABLE IF EXISTS DimPurposeCode;
DROP TABLE IF EXISTS DimStatus;
DROP TABLE IF EXISTS DimDateTime_Payment;
DROP TABLE IF EXISTS DimDateTime_Settlement;

-- ============================
-- DIMENSIONS
-- ============================

CREATE TABLE DimParty_Debtor (
    PartyID        VARCHAR(50) PRIMARY KEY,
    Name           VARCHAR(255),
    IBAN           VARCHAR(34),
    CountryCode    CHAR(2)
);

CREATE TABLE DimParty_Creditor (
    PartyID        VARCHAR(50) PRIMARY KEY,
    Name           VARCHAR(255),
    IBAN           VARCHAR(34),
    CountryCode    CHAR(2)
);

CREATE TABLE DimCurrency (
    CurrencyCode   VARCHAR(3) PRIMARY KEY,
    CurrencyName   VARCHAR(100),
    CurrencySymbol VARCHAR(10)
);

CREATE TABLE DimPurposeCode (
    PurposeCode    VARCHAR(10) PRIMARY KEY,
    Description    VARCHAR(255)
);

CREATE TABLE DimStatus (
    StatusCode     VARCHAR(10) PRIMARY KEY,
    Description    VARCHAR(255)
);

CREATE TABLE DimDateTime_Payment (
    DateTime       TIMESTAMP PRIMARY KEY,
    Date           DATE NOT NULL,
    Time           TIME NOT NULL,
    Hour           INT,
    Minute         INT,
    Year           INT,
    Month          INT,
    MonthName      VARCHAR(20),
    Day            INT,
    WeekNumber     INT
);

CREATE TABLE DimDateTime_Settlement (
    DateTime       TIMESTAMP PRIMARY KEY,
    Date           DATE NOT NULL,
    Time           TIME NOT NULL,
    Hour           INT,
    Minute         INT,
    Year           INT,
    Month          INT,
    MonthName      VARCHAR(20),
    Day            INT,
    WeekNumber     INT
);

-- ============================
-- FACT TABLE
-- ============================

CREATE TABLE FactPayments (
    PaymentID              VARCHAR(100) PRIMARY KEY,
    MsgId                  VARCHAR(100),
    InstrId                VARCHAR(100),
    EndToEndId             VARCHAR(100),
    PaymentDate            TIMESTAMP,
    SettlementDate         TIMESTAMP,
    Amount                 DECIMAL(18,2),
    CurrencyCode           VARCHAR(3),
    DebtorID               VARCHAR(50),
    CreditorID             VARCHAR(50),
    DebtorAgentBIC         VARCHAR(11),
    CreditorAgentBIC       VARCHAR(11),
    PurposeCode            VARCHAR(10),
    StatusCode             VARCHAR(10),
    ProcessingTimeMinutes  DECIMAL(10,2),

    FOREIGN KEY (CurrencyCode) REFERENCES DimCurrency (CurrencyCode),
    FOREIGN KEY (DebtorID) REFERENCES DimParty_Debtor (PartyID),
    FOREIGN KEY (CreditorID) REFERENCES DimParty_Creditor (PartyID),
    FOREIGN KEY (PurposeCode) REFERENCES DimPurposeCode (PurposeCode),
    FOREIGN KEY (StatusCode) REFERENCES DimStatus (StatusCode),
    FOREIGN KEY (PaymentDate) REFERENCES DimDateTime_Payment (DateTime),
    FOREIGN KEY (SettlementDate) REFERENCES DimDateTime_Settlement (DateTime)
);

-- ============================
-- Indexes for performance
-- ============================

CREATE INDEX idx_factpayments_currency ON FactPayments (CurrencyCode);
CREATE INDEX idx_factpayments_debtor ON FactPayments (DebtorID);
CREATE INDEX idx_factpayments_creditor ON FactPayments (CreditorID);
CREATE INDEX idx_factpayments_paymentdate ON FactPayments (PaymentDate);
CREATE INDEX idx_factpayments_settlementdate ON FactPayments (SettlementDate);
CREATE INDEX idx_factpayments_status ON FactPayments (StatusCode);
CREATE INDEX idx_factpayments_purpose ON FactPayments (PurposeCode);