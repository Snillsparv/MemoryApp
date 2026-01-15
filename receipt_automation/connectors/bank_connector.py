"""
Bank Connector - Hämtar transaktioner och kvitton från svenska banker

Eftersom banker inte har publika API:er för privatkunder, finns det flera alternativ:
1. Manuell export av CSV/PDF från banken (enklast)
2. Open Banking API via aggregator (Tink, Nordigen) (kräver registrering)
3. Web scraping (komplext och fragilt)

Detta script stödjer framförallt alternativ 1 och har ramverk för alternativ 2.
"""

import os
import csv
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import json

class BankConnector:
    """Hanterar import av banktransaktioner från CSV/PDF filer"""

    # Mappning av svenska banker och deras CSV-format
    BANK_FORMATS = {
        'seb': {
            'delimiter': ';',
            'encoding': 'latin1',
            'columns': {
                'date': 'Bokföringsdatum',
                'description': 'Text',
                'amount': 'Belopp',
                'balance': 'Saldo'
            }
        },
        'swedbank': {
            'delimiter': ';',
            'encoding': 'utf-8',
            'columns': {
                'date': 'Datum',
                'description': 'Beskrivning',
                'amount': 'Belopp',
                'balance': 'Saldo'
            }
        },
        'handelsbanken': {
            'delimiter': ';',
            'encoding': 'latin1',
            'columns': {
                'date': 'Datum',
                'description': 'Text',
                'amount': 'Belopp',
                'balance': 'Saldo'
            }
        },
        'nordea': {
            'delimiter': '\t',
            'encoding': 'utf-8',
            'columns': {
                'date': 'Bokföringsdatum',
                'description': 'Transaktion',
                'amount': 'Belopp',
                'balance': 'Saldo'
            }
        }
    }

    # Keywords som indikerar företagsutgifter
    BUSINESS_KEYWORDS = [
        'swish',
        'stripe',
        'paypal',
        'aws',
        'google cloud',
        'microsoft',
        'dropbox',
        'github',
        'adobe',
        'office',
        'domain',
        'hosting',
        'serverspace',
        'linode',
        'digitalocean',
        'material',
        'verktyg',
        'kontorsmaterial',
        'bränsle',
        'parkering',
        'telia',
        'telenor',
        'three'
    ]

    def __init__(self):
        """Initierar bank connector"""
        pass

    def parse_csv_export(self, csv_path: str, bank: str = 'auto') -> List[Dict]:
        """
        Parsar en CSV-export från banken

        Args:
            csv_path: Sökväg till CSV-filen
            bank: Bankens namn ('seb', 'swedbank', etc.) eller 'auto' för automatisk detektion

        Returns:
            Lista med transaktioner
        """
        if not os.path.exists(csv_path):
            print(f"❌ Kunde inte hitta fil: {csv_path}")
            return []

        # Auto-detektera bank om inte specificerad
        if bank == 'auto':
            bank = self._detect_bank(csv_path)
            if bank:
                print(f"🏦 Detekterade bank: {bank.upper()}")
            else:
                print("⚠️  Kunde inte detektera bank automatiskt, försöker generisk parsing")

        # Hämta format för banken
        format_config = self.BANK_FORMATS.get(bank, None)

        if not format_config:
            print(f"⚠️  Okänt bankformat: {bank}, använder generisk parsing")
            return self._parse_generic_csv(csv_path)

        # Parsa CSV med bankens format
        transactions = []

        try:
            with open(csv_path, 'r', encoding=format_config['encoding']) as f:
                reader = csv.DictReader(f, delimiter=format_config['delimiter'])

                for row in reader:
                    try:
                        # Extrahera fält baserat på bankens kolumnnamn
                        cols = format_config['columns']

                        date_str = row.get(cols['date'], '')
                        description = row.get(cols['description'], '')
                        amount_str = row.get(cols['amount'], '0')

                        # Rensa och parsa belopp (hantera både komma och punkt som decimaltecken)
                        amount_str = amount_str.replace(' ', '').replace(',', '.')
                        amount = float(amount_str)

                        # Parsa datum
                        transaction_date = self._parse_date(date_str)

                        if transaction_date and description:
                            transactions.append({
                                'date': transaction_date,
                                'description': description.strip(),
                                'amount': amount,
                                'source': f"{bank}_csv",
                                'is_business': self._is_business_expense(description)
                            })

                    except (ValueError, KeyError) as e:
                        # Hoppa över rader som inte kan parsas
                        continue

            print(f"✅ Parsade {len(transactions)} transaktioner från {bank.upper()}")

        except Exception as e:
            print(f"❌ Fel vid parsing av CSV: {e}")
            return []

        return transactions

    def _detect_bank(self, csv_path: str) -> Optional[str]:
        """
        Försöker detektera vilken bank en CSV-fil kommer från

        Args:
            csv_path: Sökväg till CSV-filen

        Returns:
            Banknamn eller None
        """
        # Läs första raderna av filen
        try:
            with open(csv_path, 'rb') as f:
                first_bytes = f.read(1000)

            # Försök olika encodings
            for encoding in ['utf-8', 'latin1', 'cp1252']:
                try:
                    content = first_bytes.decode(encoding)

                    # Kolla efter bank-specifika markörer
                    if 'SEB' in content or 'Skandinaviska Enskilda Banken' in content:
                        return 'seb'
                    elif 'Swedbank' in content:
                        return 'swedbank'
                    elif 'Handelsbanken' in content:
                        return 'handelsbanken'
                    elif 'Nordea' in content:
                        return 'nordea'

                except UnicodeDecodeError:
                    continue

        except Exception as e:
            print(f"⚠️  Kunde inte läsa fil för detektion: {e}")

        return None

    def _parse_generic_csv(self, csv_path: str) -> List[Dict]:
        """
        Generisk CSV-parser för okända format

        Args:
            csv_path: Sökväg till CSV-filen

        Returns:
            Lista med transaktioner
        """
        transactions = []

        # Försök olika delimiters och encodings
        for delimiter in [';', ',', '\t']:
            for encoding in ['utf-8', 'latin1', 'cp1252']:
                try:
                    with open(csv_path, 'r', encoding=encoding) as f:
                        reader = csv.reader(f, delimiter=delimiter)
                        rows = list(reader)

                        if len(rows) < 2:
                            continue

                        # Försök hitta kolumner med datum, beskrivning och belopp
                        header = rows[0]

                        # Enkel heuristik för att hitta kolumner
                        date_col = None
                        desc_col = None
                        amount_col = None

                        for i, col in enumerate(header):
                            col_lower = col.lower()
                            if 'datum' in col_lower or 'date' in col_lower:
                                date_col = i
                            elif 'beskrivning' in col_lower or 'text' in col_lower or 'description' in col_lower:
                                desc_col = i
                            elif 'belopp' in col_lower or 'amount' in col_lower:
                                amount_col = i

                        if date_col is not None and desc_col is not None and amount_col is not None:
                            print(f"✅ Hittade kolumner: Datum={date_col}, Beskrivning={desc_col}, Belopp={amount_col}")

                            for row in rows[1:]:
                                if len(row) <= max(date_col, desc_col, amount_col):
                                    continue

                                try:
                                    date_str = row[date_col]
                                    description = row[desc_col]
                                    amount_str = row[amount_col].replace(' ', '').replace(',', '.')
                                    amount = float(amount_str)

                                    transaction_date = self._parse_date(date_str)

                                    if transaction_date and description:
                                        transactions.append({
                                            'date': transaction_date,
                                            'description': description.strip(),
                                            'amount': amount,
                                            'source': 'generic_csv',
                                            'is_business': self._is_business_expense(description)
                                        })

                                except (ValueError, IndexError):
                                    continue

                            if transactions:
                                print(f"✅ Parsade {len(transactions)} transaktioner")
                                return transactions

                except Exception:
                    continue

        print("❌ Kunde inte parsa CSV-filen")
        return []

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """
        Parsar datum från olika format

        Args:
            date_str: Datum som sträng

        Returns:
            datetime objekt eller None
        """
        # Vanliga svenska datumformat
        formats = [
            '%Y-%m-%d',
            '%Y/%m/%d',
            '%d-%m-%Y',
            '%d/%m/%Y',
            '%d.%m.%Y',
            '%Y%m%d'
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue

        return None

    def _is_business_expense(self, description: str) -> bool:
        """
        Enkel heuristik för att avgöra om en transaktion är företagsrelaterad

        Args:
            description: Transaktionsbeskrivning

        Returns:
            True om troligen företagsutgift
        """
        description_lower = description.lower()

        for keyword in self.BUSINESS_KEYWORDS:
            if keyword in description_lower:
                return True

        return False

    def filter_business_expenses(self, transactions: List[Dict], min_amount: float = 0) -> List[Dict]:
        """
        Filtrerar ut troliga företagsutgifter

        Args:
            transactions: Lista med transaktioner
            min_amount: Minsta belopp att inkludera (negativt för utgifter)

        Returns:
            Filtrerad lista med transaktioner
        """
        filtered = [
            t for t in transactions
            if t['is_business'] and t['amount'] <= min_amount
        ]

        print(f"📊 Filtrerade {len(filtered)} troliga företagsutgifter av {len(transactions)} transaktioner")

        return filtered

    def export_to_csv(self, transactions: List[Dict], output_path: str):
        """
        Exporterar transaktioner till CSV

        Args:
            transactions: Lista med transaktioner
            output_path: Sökväg där CSV ska sparas
        """
        if not transactions:
            print("⚠️  Inga transaktioner att exportera")
            return

        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                fieldnames = ['date', 'description', 'amount', 'source', 'is_business']
                writer = csv.DictWriter(f, fieldnames=fieldnames)

                writer.writeheader()
                for transaction in transactions:
                    writer.writerow({
                        'date': transaction['date'].strftime('%Y-%m-%d'),
                        'description': transaction['description'],
                        'amount': transaction['amount'],
                        'source': transaction['source'],
                        'is_business': transaction['is_business']
                    })

            print(f"✅ Exporterade {len(transactions)} transaktioner till {output_path}")

        except Exception as e:
            print(f"❌ Fel vid export: {e}")

    def collect_receipts(self, csv_files: List[str], output_dir: str) -> Dict[str, int]:
        """
        Samlar transaktioner från CSV-filer

        Args:
            csv_files: Lista med sökvägar till CSV-filer
            output_dir: Katalog där resultat ska sparas

        Returns:
            Dict med statistik
        """
        print("🏦 Bank Transaktionsinhämtning")
        print("=" * 50)

        os.makedirs(output_dir, exist_ok=True)

        all_transactions = []

        for csv_file in csv_files:
            print(f"\n📄 Bearbetar: {csv_file}")
            transactions = self.parse_csv_export(csv_file)
            all_transactions.extend(transactions)

        if all_transactions:
            # Filtrera företagsutgifter
            business_expenses = self.filter_business_expenses(all_transactions)

            # Exportera till CSV
            output_file = os.path.join(output_dir, f'bank_transactions_{datetime.now().strftime("%Y%m%d")}.csv')
            self.export_to_csv(business_expenses, output_file)

            return {
                'total_transactions': len(all_transactions),
                'business_expenses': len(business_expenses),
                'files': 1
            }
        else:
            print("⚠️  Inga transaktioner hittades")
            return {'total_transactions': 0, 'business_expenses': 0, 'files': 0}


if __name__ == '__main__':
    # Test av bank connector
    connector = BankConnector()

    # Exempel: Parsa en CSV-fil från banken
    # transactions = connector.parse_csv_export('path/to/bank_export.csv', bank='seb')
    # connector.export_to_csv(transactions, 'output/transactions.csv')

    print("💡 Bank Connector redo!")
    print("\n📖 Användning:")
    print("1. Exportera transaktioner som CSV från din banks hemsida")
    print("2. Använd parse_csv_export() för att läsa in transaktionerna")
    print("3. Använd filter_business_expenses() för att filtrera företagsutgifter")
    print("4. Spara resultatet med export_to_csv()")
