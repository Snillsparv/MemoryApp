# 🧾 Kvittoinhämtare - Automatiserad Bokföring

Ett system för att automatiskt samla in kvitton och transaktioner från olika källor för företagsbokföring.

## 📋 Översikt

Systemet kan hämta kvitton från:
- **📧 Gmail**: Automatisk extraktion av PDF-kvitton från email
- **🏦 Banker**: Bearbetning av CSV-exporter från svenska banker (SEB, Swedbank, Handelsbanken, Nordea)
- **🔗 Leverantörer**: Ramverk för att hämta kvitton från leverantörsportaler (valfritt)

Alla kvitton sparas som PDF-filer i en organiserad mappstruktur, sorterade efter datum och avsändare.

## 🚀 Snabbstart

### 1. Installation

```bash
# Installera Python-beroenden
pip install -r requirements.txt
```

### 2. Gmail-konfiguration (VIKTIGT!)

För att hämta kvitton från Gmail behöver du aktivera Gmail API:

#### Steg-för-steg Gmail API Setup:

1. **Gå till Google Cloud Console**
   - Öppna: https://console.cloud.google.com/

2. **Skapa ett nytt projekt**
   - Klicka på projekt-dropdown längst upp
   - Välj "New Project"
   - Namnge projektet (t.ex. "Kvittoinhämtare")
   - Klicka "Create"

3. **Aktivera Gmail API**
   - Gå till: https://console.cloud.google.com/apis/library
   - Sök efter "Gmail API"
   - Klicka på "Gmail API"
   - Klicka "Enable"

4. **Skapa OAuth 2.0 Credentials**
   - Gå till: https://console.cloud.google.com/apis/credentials
   - Klicka "Create Credentials" → "OAuth client ID"
   - Om du inte konfigurerat OAuth consent screen:
     - Klicka "Configure Consent Screen"
     - Välj "External" (om du inte har Google Workspace)
     - Fyll i:
       - App name: "Kvittoinhämtare"
       - User support email: Din email
       - Developer contact: Din email
     - Klicka "Save and Continue"
     - På Scopes-sidan, klicka "Save and Continue" (vi lägger till scopes senare)
     - På Test users, lägg till din email
     - Klicka "Save and Continue"
   - Välj "Desktop app" som application type
   - Namnge den (t.ex. "Desktop client")
   - Klicka "Create"

5. **Ladda ner credentials**
   - Klicka på nedladdningsikonen (⬇️) för din nya OAuth 2.0 Client
   - Spara filen som `credentials.json` i `receipt_automation/` katalogen

6. **Första inloggningen**
   - Första gången du kör scriptet kommer en webbläsare att öppnas
   - Logga in med ditt Gmail-konto
   - Godkänn behörigheterna (read-only access till Gmail)
   - En `token.pickle` fil skapas för framtida körningar

### 3. Bank CSV-export

#### SEB:
1. Logga in på https://seb.se/
2. Gå till ditt företagskonto
3. Välj "Kontoutdrag" eller "Transaktioner"
4. Välj datumperiod (t.ex. senaste månaden)
5. Exportera som CSV
6. Spara filen i `receipt_automation/bank_exports/`

#### Swedbank:
1. Logga in på https://www.swedbank.se/
2. Gå till företagskontot
3. Välj "Ladda ner transaktioner"
4. Välj format: CSV eller Excel
5. Spara filen i `receipt_automation/bank_exports/`

#### Handelsbanken:
1. Logga in på https://www.handelsbanken.se/
2. Gå till Företag → Konton
3. Välj konto och "Exportera"
4. Välj CSV-format
5. Spara filen i `receipt_automation/bank_exports/`

#### Nordea:
1. Logga in på https://www.nordea.se/
2. Välj företagskonto
3. Gå till "Transaktioner"
4. Klicka "Ladda ner" → CSV
5. Spara filen i `receipt_automation/bank_exports/`

### 4. Kör kvittoinhämtaren

```bash
# Interaktivt läge (rekommenderas för första gången)
python collect_receipts.py --interactive

# Eller kör direkt med standardinställningar
python collect_receipts.py

# Hämta från senaste 60 dagarna
python collect_receipts.py --days-back 60
```

## 📁 Filstruktur

```
receipt_automation/
├── collect_receipts.py          # Huvudscript - kör detta!
├── requirements.txt             # Python-beroenden
├── README.md                    # Denna fil
├── config.json                  # Konfigurationsfil (skapas automatiskt)
├── credentials.json             # Gmail API credentials (du skapar denna)
├── token.pickle                 # Gmail access token (skapas automatiskt)
│
├── connectors/                  # Källkodsmoduler
│   ├── gmail_connector.py      # Gmail integration
│   ├── bank_connector.py       # Bank CSV-parsing
│   └── supplier_connector.py   # Leverantörsintegrationer
│
├── bank_exports/                # Lägg dina bank CSV-filer här
│   ├── seb_export.csv
│   └── swedbank_transactions.csv
│
└── output/                      # Här sparas alla kvitton
    ├── gmail/                   # Kvitton från Gmail
    │   ├── 2024-01-15_AWS_Invoice_December.pdf
    │   ├── 2024-01-10_Stripe_Receipt.pdf
    │   └── ...
    └── bank/                    # Bearbetade banktransaktioner
        └── bank_transactions_20240115.csv
```

## ⚙️ Konfiguration

Konfigurationsfilen `config.json` skapas automatiskt vid första körningen. Du kan redigera den för att anpassa inställningar:

```json
{
  "output_dir": "output",
  "gmail": {
    "enabled": true,
    "credentials_path": "credentials.json",
    "token_path": "token.pickle"
  },
  "bank": {
    "enabled": true,
    "csv_directory": "bank_exports"
  },
  "suppliers": {
    "enabled": false,
    "connectors": []
  }
}
```

## 🔍 Hur det fungerar

### Gmail-insamling

Scriptet söker automatiskt efter email med:
- Keywords: "kvitto", "faktura", "invoice", "receipt", "orderbekräftelse"
- PDF eller bild-bilagor
- Vanliga avsändare: Swish, PayPal, Stripe, AWS, etc.

Alla hittade kvitton sparas som:
```
YYYY-MM-DD_Ämnesrad_original_filnamn.pdf
```

### Bank-bearbetning

- Läser CSV-exporter från svenska banker
- Detekterar automatiskt bankformat (SEB, Swedbank, Handelsbanken, Nordea)
- Filtrerar troliga företagsutgifter baserat på keywords
- Skapar en sammanställd CSV med alla transaktioner

### Leverantörsportaler (Avancerat)

För leverantörer som AWS, Stripe, etc. finns det tre alternativ:

1. **Rekommenderat**: Använd deras API
   - Stripe: https://stripe.com/docs/api/invoices
   - AWS: Använd Cost and Usage Reports

2. **Manuell nedladdning**: Ladda ner kvitton manuellt från portalen

3. **Custom integration**: Implementera egen connector (se `supplier_connector.py`)

## 📊 Exempel på körning

```bash
$ python collect_receipts.py

🧾 KVITTOINHÄMTARE
======================================================================
📅 Datum: 2024-01-15 14:30:00
📁 Output: output
🔍 Söker 30 dagar bakåt
======================================================================

📧 Gmail Kvittoinhämtning
==================================================
🔐 Autentiserar med Gmail...
🔍 Söker efter kvitton med query: after:2023/12/16 ("kvitto" OR "faktura" OR "invoice" OR "receipt") has:attachment
✅ Hittade 23 meddelanden

📥 Extraherar bilagor från 23 meddelanden...

[1/23] Bearbetar meddelande...
  📄 Sparade: 2024-01-10_AWS_Invoice_December_2023.pdf
  📄 Sparade: 2024-01-10_AWS_Tax_Invoice.pdf

[2/23] Bearbetar meddelande...
  📄 Sparade: 2024-01-08_Stripe_Receipt_inv_123456.pdf

...

✅ Klart! Sparade 45 kvitton från 23 meddelanden
📁 Kvitton sparade i: output/gmail

🏦 Bank Transaktionsinhämtning
==================================================

📄 Bearbetar: bank_exports/seb_january.csv
🏦 Detekterade bank: SEB
✅ Parsade 156 transaktioner från SEB

📊 Filtrerade 23 troliga företagsutgifter av 156 transaktioner
✅ Exporterade 23 transaktioner till output/bank/bank_transactions_20240115.csv

======================================================================
📊 SAMMANFATTNING
======================================================================
📧 Gmail:
   - Meddelanden: 23
   - Kvitton: 45

🏦 Bank:
   - Transaktioner: 156
   - Företagsutgifter: 23

🔗 Leverantörer:
   - Kvitton: 0

✅ Totalt 46 filer sparade i output/
======================================================================
```

## 🔒 Säkerhet & Integritet

- **Gmail**: Scriptet har endast READ-ONLY access till din Gmail
- **Credentials**: `credentials.json` och `token.pickle` innehåller känslig information - dela INTE dessa filer
- **Lokalt**: All data bearbetas lokalt på din dator
- **Ingen cloud**: Inget skickas till externa servrar (förutom Google API för Gmail)

### Rekommendationer:
- Lägg till `.gitignore` för att inte committa credentials:
  ```
  credentials.json
  token.pickle
  config.json
  bank_exports/
  output/
  ```

## 🐛 Felsökning

### Problem: "Kunde inte hitta credentials fil"
**Lösning**: Du har inte skapat Gmail API credentials än. Följ steg 2 i Snabbstart.

### Problem: "Gmail authentication misslyckades"
**Lösning**:
1. Ta bort `token.pickle`
2. Kör scriptet igen
3. Logga in på nytt i webbläsaren

### Problem: "Inga CSV-filer hittades"
**Lösning**: Lägg dina bank CSV-exporter i `bank_exports/` katalogen.

### Problem: "Kunde inte parsa CSV-filen"
**Lösning**:
1. Kolla att filen är en riktig CSV (inte Excel .xlsx)
2. Försök specificera bank manuellt i koden
3. Öppna ett issue på GitHub med exempel på CSV-strukturen

### Problem: Bank-transaktioner känns inte igen som företagsutgifter
**Lösning**: Du kan lägga till fler keywords i `bank_connector.py` under `BUSINESS_KEYWORDS`.

## 🎯 Tips & Tricks

1. **Månadsvis körning**: Kör scriptet i början av varje månad för föregående månad
   ```bash
   python collect_receipts.py --days-back 31
   ```

2. **Backup**: Backupa `output/` katalogen regelbundet

3. **Kategorisering**: Efter inhämtning, organisera kvittona manuellt i underkategorier om behövs

4. **Integration med bokföringssystem**: Du kan enkelt bygga vidare på detta för att importera till Fortnox, Visma, etc.

5. **Automatisering**: Lägg till i crontab för automatisk månadsvis körning:
   ```bash
   # Kör den 1:a varje månad kl 09:00
   0 9 1 * * cd /path/to/receipt_automation && python collect_receipts.py --days-back 31
   ```

## 🚀 Framtida förbättringar

Möjliga förbättringar:
- [ ] OCR för att extrahera strukturerad data från PDF-kvitton
- [ ] Integration med Fortnox/Visma API
- [ ] Open Banking integration för realtidstransaktioner
- [ ] Web-gränssnitt för enklare användning
- [ ] Automatisk kategorisering av utgifter med AI
- [ ] Mobil app för att skanna papperskvitton
- [ ] E-faktura (Svefaktura) support

## 📝 Licens

Fri att använda och modifiera för personligt och företagsbruk.

## 🤝 Support

Om du stöter på problem eller har frågor, skapa ett issue på GitHub eller kontakta utvecklaren.

---

**Lycka till med din bokföring! 📊✨**
