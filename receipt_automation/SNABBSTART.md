# 🚀 Snabbstart - Kvittoinhämtare

Kom igång på 5 minuter!

## Steg 1: Installera beroenden

```bash
cd receipt_automation
pip install -r requirements.txt
```

## Steg 2: Konfigurera Gmail (5-10 minuter)

### A. Skapa Gmail API Credentials

1. Gå till: https://console.cloud.google.com/
2. Skapa nytt projekt → Namnge det "Kvittoinhämtare"
3. Aktivera Gmail API:
   - https://console.cloud.google.com/apis/library
   - Sök "Gmail API" → Enable
4. Skapa OAuth credentials:
   - https://console.cloud.google.com/apis/credentials
   - Create Credentials → OAuth client ID
   - Konfigurera consent screen (External)
   - Välj "Desktop app"
5. Ladda ner credentials → Spara som `credentials.json` här i denna mapp

### B. Första inloggningen

Första gången du kör scriptet kommer en webbläsare öppnas där du loggar in med Gmail. Detta skapar en `token.pickle` fil som används vid framtida körningar.

## Steg 3: Förbered bank CSV-filer (Valfritt)

Om du vill bearbeta banktransaktioner:

1. Logga in på din banks hemsida
2. Exportera transaktioner som CSV (senaste månaden)
3. Lägg CSV-filen i mappen `bank_exports/`

**Stödda banker:**
- SEB
- Swedbank
- Handelsbanken
- Nordea

## Steg 4: Kör!

```bash
# Interaktivt läge (bäst första gången)
python collect_receipts.py --interactive

# Eller direkt
python collect_receipts.py

# Hämta från senaste 60 dagarna
python collect_receipts.py --days-back 60
```

## 🎉 Klart!

Alla kvitton finns nu i `output/` mappen:
- `output/gmail/` - Kvitton från email
- `output/bank/` - Bearbetade banktransaktioner

## 📅 Månadsvis användning

Kör detta i början av varje månad:

```bash
python collect_receipts.py --days-back 31
```

## ❓ Problem?

Se den fullständiga README.md för felsökning och avancerade inställningar.

### Vanliga problem:

**"Kunde inte hitta credentials fil"**
→ Du glömde ladda ner credentials.json från Google Cloud Console

**"Authentication failed"**
→ Ta bort token.pickle och försök igen

**"Inga CSV-filer"**
→ Lägg dina bank-exporter i `bank_exports/` mappen

---

**Lycka till! 📊✨**
