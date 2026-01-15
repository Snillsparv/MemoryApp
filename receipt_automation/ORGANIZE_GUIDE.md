# 📋 Kvittoorganisering - Komplett Guide

Detta är det **smarta systemet** som matchar dina banktransaktioner med kvitton och organiserar allt i numrerad ordning!

## 🎯 Vad gör systemet?

1. **Läser din bank CSV** - Alla transaktioner (både in- och utbetalningar)
2. **Sorterar efter datum** - Tidigast först
3. **Hämtar kvitton från Gmail** - Alla PDF/bilder från email
4. **Matchar intelligent** - Kopplar transaktioner till kvitton baserat på datum + belopp
5. **Genererar saknade kvitton** - Skapar HTML-kvitton för transaktioner utan PDF
6. **Numrerar allt** - Från 001 och uppåt i datumordning

## 📁 Resultat

Du får en mapp med alla kvitton numrerade så här:

```
organized_receipts/
├── 001_2025_01_01_Swish_betalning.pdf      ← Matchat från Gmail
├── 002_2025_01_03_ICA_Kvantum.html         ← Genererat från bank
├── 003_2025_01_05_Telia.pdf                ← Matchat från Gmail
├── 004_2025_01_07_Loneinsattning.html      ← Inbetalning (genererat)
├── 005_2025_01_10_AWS_Invoice.pdf          ← Matchat från Gmail
...
└── _summary.csv                             ← Översikt över alla transaktioner
```

## 🚀 Snabbstart

### Steg 1: Hämta Gmail-kvitton först

```bash
# Gå till receipt_automation mappen
cd receipt_automation

# Hämta kvitton från Gmail (kräver credentials.json!)
python collect_receipts.py --interactive
```

Detta skapar `output/gmail/` med alla kvitton från din email.

### Steg 2: Organisera med din bank CSV

```bash
# Organisera kvitton baserat på CSV-filen
python organize_receipts.py --csv bank_exports/december_2025.csv
```

Klart! Kolla i `organized_receipts/` mappen.

## 📖 Detaljerade Instruktioner

### Komplett arbetsflöde:

```bash
# 1. Hämta Gmail-kvitton
python collect_receipts.py

# 2. Lägg din bank CSV i bank_exports/
# (t.ex. bank_exports/december_2025.csv)

# 3. Organisera allt
python organize_receipts.py --csv bank_exports/december_2025.csv --gmail output/gmail --output organized_receipts
```

### Om du bara har bank CSV (ingen Gmail):

```bash
# Genererar HTML-kvitton för ALLA transaktioner
python organize_receipts.py --csv bank_exports/december_2025.csv --skip-gmail
```

## ⚙️ Avancerade Alternativ

### Specificera bank (om auto-detektion misslyckas)

```bash
python organize_receipts.py --csv bank_exports/december_2025.csv --bank seb
```

Stödda banker: `seb`, `swedbank`, `handelsbanken`, `nordea`

### Ändra output-mapp

```bash
python organize_receipts.py --csv bank_exports/december_2025.csv --output bokforing_december_2025
```

### Använd Gmail-kvitton från annan mapp

```bash
python organize_receipts.py --csv bank_exports/december_2025.csv --gmail ~/Downloads/kvitton
```

## 🔍 Hur fungerar matchningen?

Systemet matchar transaktioner med kvitton baserat på:

1. **Datum** (viktigast) - Kvittot måste vara inom ±3 dagar från transaktionen
2. **Belopp** (om tillgängligt) - Måste matcha ungefär
3. **Text** (bonus) - Gemensamma nyckelord ger högre match-säkerhet

**Match-exempel:**
- Transaktion: `2025-01-15, -299 kr, "Swish betalning"`
- Kvitto: `2025-01-15_Swish_Receipt.pdf`
- ✅ **Matchning: 95%** (samma datum, innehåller "swish")

**Ingen match-exempel:**
- Transaktion: `2025-01-20, -500 kr, "Telia Mobil"`
- Inget kvitto hittat inom ±3 dagar
- 🏦 **Genererar HTML-kvitto från bankhändelsen**

## 📊 Sammanfattningsfil (_summary.csv)

Systemet skapar också en `_summary.csv` fil med översikt:

```csv
number,date,description,amount,source,match_type,filename
001,2025-01-01,Swish betalning,-299.00,seb_csv,gmail,001_2025_01_01_Swish_betalning.pdf
002,2025-01-03,ICA Kvantum,-450.50,seb_csv,bank_only,002_2025_01_03_ICA_Kvantum.html
003,2025-01-05,Loneinsattning,+25000.00,seb_csv,bank_only,003_2025_01_05_Loneinsattning.html
...
```

Perfect för att importera till Excel/bokföringssystem!

## 💡 Tips & Tricks

### Månatligt arbetsflöde

```bash
# 1. I början av månaden: Hämta förra månadens Gmail-kvitton
python collect_receipts.py --days-back 31

# 2. Exportera bank CSV från banken
# Spara som: bank_exports/2025_01.csv

# 3. Organisera
python organize_receipts.py --csv bank_exports/2025_01.csv --output bokforing/2025_01

# 4. Öppna bokforing/2025_01/ och gå igenom kvittona i nummerordning!
```

### Kontrollera matchningar

Kolla `_summary.csv` filen:
- `match_type: gmail` = Matchat kvitto från email
- `match_type: bank_only` = Genererat från bankhändelse

Om många transaktioner är `bank_only`, kanske du behöver:
- Hämta Gmail-kvitton längre tillbaka (`--days-back 60`)
- Logga in manuellt på leverantörsportaler för saknade kvitton

### Kombinera flera månader

```bash
# Hämta Gmail för hela kvartalet
python collect_receipts.py --days-back 90

# Organisera varje månad separat
python organize_receipts.py --csv bank_exports/2025_01.csv --output Q1/januari
python organize_receipts.py --csv bank_exports/2025_02.csv --output Q1/februari
python organize_receipts.py --csv bank_exports/2025_03.csv --output Q1/mars
```

## 🎨 Anpassa HTML-kvitton

HTML-kvitton som genereras för transaktioner utan PDF ser ut så här:

```
╔════════════════════════════════╗
║       BANK KVITTO             ║
║  Genererat från transaktion   ║
╠════════════════════════════════╣
║ Datum:       2025-01-15       ║
║ Beskrivning: Telia Mobil      ║
║ Källa:       SEB CSV          ║
║                                ║
║         -500.00 kr            ║
╚════════════════════════════════╝
```

Du kan öppna dem i webbläsare och skriva ut som PDF om du behöver!

## ❓ Felsökning

### "Kunde inte hitta CSV-fil"
**Lösning:** Kontrollera att sökvägen är korrekt:
```bash
ls bank_exports/
python organize_receipts.py --csv bank_exports/DIN_FIL.csv
```

### "Inga transaktioner hittades"
**Lösning:** CSV-filen kanske har fel format eller är tom. Prova:
```bash
python organize_receipts.py --csv bank_exports/din_fil.csv --bank seb
```

### "Många transaktioner är bank_only"
**Lösning:** Det är normalt! Betyder bara att kvitton inte hittades i Gmail. Du kan:
1. Hämta Gmail längre tillbaka: `python collect_receipts.py --days-back 60`
2. Manuellt ladda ner saknade kvitton från leverantörsportaler
3. Behålla HTML-kvittona (bankhändelsen räcker ofta för bokföring)

### "Match-confidence är låg"
**Lösning:** Systemet är försiktigt med matchning. Om du ser misslyckade matchningar i `_summary.csv`, kan du manuellt:
1. Flytta rätt kvitto från `output/gmail/` till `organized_receipts/`
2. Byt namn till rätt nummer

## 🔒 Säkerhet

- Alla filer bearbetas lokalt på din dator
- Ingen data skickas till externa servrar
- Bank CSV och kvitton stannar på din dator
- Gmail API har read-only åtkomst

**OBS:** Dela ALDRIG:
- `credentials.json`
- `token.pickle`
- Dina bank CSV-filer
- Output-kvitton (innehåller känslig info)

---

**Lycka till med bokföringen! 📊✨**

Har du frågor eller problem? Se den fullständiga README.md eller kontakta support.
