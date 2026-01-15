#!/usr/bin/env python3
"""
Organize Receipts - Intelligent kvittomatchning och organisering

Detta script:
1. Läser CSV-fil från banken (alla transaktioner)
2. Hämtar kvitton från Gmail
3. Matchar kvitton med transaktioner (belopp + datum)
4. Skapar "kvitto" för transaktioner utan PDF
5. Numrerar allt sekventiellt: 001_2025_01_01_Beskrivning.pdf

Användning:
    python organize_receipts.py --csv bank_exports/december_2025.csv
    python organize_receipts.py --csv bank_exports/december_2025.csv --skip-gmail
"""

import os
import sys
import json
import argparse
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import re

# Importera connectors
sys.path.append(os.path.dirname(__file__))
from connectors.gmail_connector import GmailConnector
from connectors.bank_connector import BankConnector


class ReceiptMatcher:
    """Matchar banktransaktioner med kvitton"""

    def __init__(self, tolerance_days: int = 3, amount_tolerance: float = 0.01):
        """
        Args:
            tolerance_days: Antal dagar före/efter transaktion att söka kvitto
            amount_tolerance: Tolerans för belopp (för att hantera avrundning)
        """
        self.tolerance_days = tolerance_days
        self.amount_tolerance = amount_tolerance

    def match_receipts(
        self,
        transactions: List[Dict],
        receipts: List[Dict]
    ) -> List[Dict]:
        """
        Matchar transaktioner med kvitton

        Args:
            transactions: Lista med banktransaktioner
            receipts: Lista med kvitton (från Gmail)

        Returns:
            Lista med transaktioner + matchade kvitton
        """
        matched_transactions = []
        used_receipts = set()

        for transaction in transactions:
            match = self._find_best_match(transaction, receipts, used_receipts)

            if match:
                used_receipts.add(match['index'])
                transaction['receipt_file'] = match['file_path']
                transaction['match_confidence'] = match['confidence']
                transaction['match_type'] = 'gmail'
            else:
                transaction['receipt_file'] = None
                transaction['match_confidence'] = 0.0
                transaction['match_type'] = 'bank_only'

            matched_transactions.append(transaction)

        return matched_transactions

    def _find_best_match(
        self,
        transaction: Dict,
        receipts: List[Dict],
        used_receipts: set
    ) -> Optional[Dict]:
        """
        Hittar bästa matchning för en transaktion

        Args:
            transaction: Banktransaktion
            receipts: Lista med tillgängliga kvitton
            used_receipts: Set med redan använda kvitton

        Returns:
            Dict med match-info eller None
        """
        best_match = None
        best_score = 0.0

        trans_date = transaction['date']
        trans_amount = abs(transaction['amount'])
        trans_desc = transaction['description'].lower()

        for i, receipt in enumerate(receipts):
            if i in used_receipts:
                continue

            # Beräkna match-score
            score = self._calculate_match_score(
                trans_date, trans_amount, trans_desc,
                receipt
            )

            if score > best_score and score > 0.5:  # Minst 50% match
                best_score = score
                best_match = {
                    'index': i,
                    'file_path': receipt['file_path'],
                    'confidence': score
                }

        return best_match

    def _calculate_match_score(
        self,
        trans_date: datetime,
        trans_amount: float,
        trans_desc: str,
        receipt: Dict
    ) -> float:
        """
        Beräknar match-score mellan transaktion och kvitto

        Returns:
            Score mellan 0.0 och 1.0
        """
        score = 0.0

        # Datum-matchning (viktigast)
        receipt_date = receipt.get('date')
        if receipt_date:
            days_diff = abs((trans_date - receipt_date).days)
            if days_diff <= self.tolerance_days:
                # Perfekt match = 1.0, varje dag = -0.2
                date_score = max(0.0, 1.0 - (days_diff * 0.2))
                score += date_score * 0.6  # 60% vikt på datum

        # Belopp-matchning (om tillgänglig i kvitto)
        receipt_amount = receipt.get('amount')
        if receipt_amount and receipt_amount > 0:
            amount_diff = abs(trans_amount - receipt_amount)
            if amount_diff <= self.amount_tolerance:
                score += 0.3  # 30% vikt på belopp

        # Text-matchning (enkel keyword-baserad)
        receipt_text = receipt.get('description', '').lower()

        # Extrahera keywords från transaktion
        trans_keywords = set(re.findall(r'\w+', trans_desc))
        receipt_keywords = set(re.findall(r'\w+', receipt_text))

        # Gemensamma keywords
        common_keywords = trans_keywords & receipt_keywords
        if trans_keywords and len(common_keywords) > 0:
            keyword_score = len(common_keywords) / len(trans_keywords)
            score += keyword_score * 0.1  # 10% vikt på text

        return score


class BankReceiptGenerator:
    """Genererar kvitton från banktransaktioner"""

    def __init__(self):
        pass

    def generate_receipt(
        self,
        transaction: Dict,
        output_path: str,
        format: str = 'html'
    ) -> str:
        """
        Genererar ett kvitto från en banktransaktion

        Args:
            transaction: Banktransaktion
            output_path: Sökväg där kvittot ska sparas
            format: 'html' eller 'txt'

        Returns:
            Sökväg till genererat kvitto
        """
        if format == 'html':
            return self._generate_html_receipt(transaction, output_path)
        else:
            return self._generate_text_receipt(transaction, output_path)

    def _generate_html_receipt(self, transaction: Dict, output_path: str) -> str:
        """Genererar HTML-kvitto"""

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: 'Courier New', monospace;
            max-width: 600px;
            margin: 40px auto;
            padding: 20px;
            border: 2px solid #333;
            background: #fff;
        }}
        .header {{
            text-align: center;
            border-bottom: 2px dashed #333;
            padding-bottom: 20px;
            margin-bottom: 20px;
        }}
        .title {{
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        .subtitle {{
            font-size: 14px;
            color: #666;
        }}
        .content {{
            margin: 20px 0;
        }}
        .row {{
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }}
        .label {{
            font-weight: bold;
            color: #333;
        }}
        .value {{
            color: #000;
        }}
        .amount {{
            font-size: 20px;
            font-weight: bold;
            text-align: center;
            margin: 20px 0;
            padding: 15px;
            background: #f5f5f5;
            border: 1px solid #ddd;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 2px dashed #333;
            font-size: 12px;
            color: #666;
        }}
        .amount.negative {{
            color: #d32f2f;
        }}
        .amount.positive {{
            color: #388e3c;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="title">BANK KVITTO</div>
        <div class="subtitle">Genererat från banktransaktion</div>
    </div>

    <div class="content">
        <div class="row">
            <span class="label">Datum:</span>
            <span class="value">{transaction['date'].strftime('%Y-%m-%d')}</span>
        </div>

        <div class="row">
            <span class="label">Beskrivning:</span>
            <span class="value">{transaction['description']}</span>
        </div>

        <div class="row">
            <span class="label">Källa:</span>
            <span class="value">{transaction.get('source', 'Bank CSV')}</span>
        </div>
    </div>

    <div class="amount {'negative' if transaction['amount'] < 0 else 'positive'}">
        {transaction['amount']:+.2f} kr
    </div>

    <div class="footer">
        <p>Detta kvitto är genererat automatiskt från banktransaktion</p>
        <p>Genererat: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
</body>
</html>"""

        # Spara HTML-fil
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return output_path

    def _generate_text_receipt(self, transaction: Dict, output_path: str) -> str:
        """Genererar text-kvitto"""

        text_content = f"""
========================================
           BANK KVITTO
========================================

Datum:        {transaction['date'].strftime('%Y-%m-%d')}
Beskrivning:  {transaction['description']}
Belopp:       {transaction['amount']:+.2f} kr
Källa:        {transaction.get('source', 'Bank CSV')}

========================================
Genererat från banktransaktion
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
========================================
"""

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text_content)

        return output_path


class ReceiptOrganizer:
    """Organiserar och numrerar kvitton baserat på transaktioner"""

    def __init__(self, output_dir: str = 'organized_receipts'):
        """
        Args:
            output_dir: Katalog där organiserade kvitton sparas
        """
        self.output_dir = output_dir
        self.matcher = ReceiptMatcher()
        self.generator = BankReceiptGenerator()

    def organize(
        self,
        csv_file: str,
        gmail_receipts_dir: Optional[str] = None,
        bank: str = 'auto'
    ) -> Dict:
        """
        Organiserar kvitton baserat på CSV-fil

        Args:
            csv_file: Sökväg till bank CSV-fil
            gmail_receipts_dir: Katalog med Gmail-kvitton (eller None för att hoppa över)
            bank: Banknamn för CSV-parsing

        Returns:
            Dict med statistik
        """
        print("📋 KVITTOORGANISERING")
        print("=" * 70)

        # Skapa output directory
        os.makedirs(self.output_dir, exist_ok=True)

        # 1. Läs banktransaktioner
        print("\n🏦 Läser banktransaktioner...")
        bank_connector = BankConnector()
        transactions = bank_connector.parse_csv_export(csv_file, bank=bank)

        if not transactions:
            print("❌ Inga transaktioner hittades i CSV-filen")
            return {'total': 0, 'matched': 0, 'generated': 0}

        # Sortera efter datum (tidigast först)
        transactions.sort(key=lambda t: t['date'])
        print(f"✅ Hittade {len(transactions)} transaktioner")

        # 2. Läs Gmail-kvitton (om tillgängliga)
        gmail_receipts = []
        if gmail_receipts_dir and os.path.exists(gmail_receipts_dir):
            print(f"\n📧 Läser Gmail-kvitton från {gmail_receipts_dir}...")
            gmail_receipts = self._load_gmail_receipts(gmail_receipts_dir)
            print(f"✅ Hittade {len(gmail_receipts)} Gmail-kvitton")
        else:
            print("\n⚠️  Hoppar över Gmail-kvitton (ingen katalog angiven)")

        # 3. Matcha transaktioner med kvitton
        if gmail_receipts:
            print("\n🔍 Matchar transaktioner med kvitton...")
            matched_transactions = self.matcher.match_receipts(transactions, gmail_receipts)

            matched_count = sum(1 for t in matched_transactions if t['match_type'] == 'gmail')
            print(f"✅ Matchade {matched_count} av {len(transactions)} transaktioner")
        else:
            matched_transactions = transactions
            for t in matched_transactions:
                t['receipt_file'] = None
                t['match_type'] = 'bank_only'

        # 4. Generera och kopiera kvitton med numrering
        print("\n📁 Organiserar kvitton...")
        stats = self._organize_receipts(matched_transactions)

        # 5. Spara sammanfattning
        self._save_summary(matched_transactions)

        print("\n" + "=" * 70)
        print("📊 SAMMANFATTNING")
        print("=" * 70)
        print(f"Totalt transaktioner:     {stats['total']}")
        print(f"Matchade med Gmail:       {stats['matched']}")
        print(f"Genererade från bank:     {stats['generated']}")
        print(f"\n✅ Alla kvitton sparade i: {self.output_dir}/")
        print("=" * 70)

        return stats

    def _load_gmail_receipts(self, gmail_dir: str) -> List[Dict]:
        """Läser alla Gmail-kvitton från katalog"""
        receipts = []

        for file_path in Path(gmail_dir).glob('*'):
            if file_path.is_file() and file_path.suffix.lower() in ['.pdf', '.png', '.jpg', '.jpeg']:
                # Försök extrahera datum från filnamn (format: YYYY-MM-DD_...)
                filename = file_path.stem
                date_match = re.match(r'(\d{4})-(\d{2})-(\d{2})', filename)

                receipt_date = None
                if date_match:
                    try:
                        receipt_date = datetime(
                            int(date_match.group(1)),
                            int(date_match.group(2)),
                            int(date_match.group(3))
                        )
                    except ValueError:
                        pass

                receipts.append({
                    'file_path': str(file_path),
                    'filename': file_path.name,
                    'date': receipt_date,
                    'description': filename,
                    'amount': None  # Kan inte extrahera från filnamn enkelt
                })

        return receipts

    def _organize_receipts(self, transactions: List[Dict]) -> Dict:
        """Organiserar kvitton med numrering"""
        stats = {
            'total': len(transactions),
            'matched': 0,
            'generated': 0
        }

        for i, transaction in enumerate(transactions, start=1):
            # Skapa filnamn
            number = f"{i:03d}"
            date_str = transaction['date'].strftime('%Y_%m_%d')

            # Rensa beskrivning för filnamn
            description = re.sub(r'[^\w\s-]', '', transaction['description'])
            description = re.sub(r'\s+', '_', description)[:50]

            if transaction['match_type'] == 'gmail' and transaction['receipt_file']:
                # Kopiera matchat kvitto
                source_path = transaction['receipt_file']
                extension = Path(source_path).suffix

                target_filename = f"{number}_{date_str}_{description}{extension}"
                target_path = os.path.join(self.output_dir, target_filename)

                shutil.copy2(source_path, target_path)
                stats['matched'] += 1

                print(f"  [{i:03d}] ✅ Gmail: {target_filename}")

            else:
                # Generera kvitto från banktransaktion
                target_filename = f"{number}_{date_str}_{description}.html"
                target_path = os.path.join(self.output_dir, target_filename)

                self.generator.generate_receipt(transaction, target_path, format='html')
                stats['generated'] += 1

                print(f"  [{i:03d}] 🏦 Bank:  {target_filename}")

        return stats

    def _save_summary(self, transactions: List[Dict]):
        """Sparar sammanfattning som CSV"""
        import csv

        summary_path = os.path.join(self.output_dir, '_summary.csv')

        with open(summary_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['number', 'date', 'description', 'amount', 'source', 'match_type', 'filename']
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            writer.writeheader()
            for i, t in enumerate(transactions, start=1):
                number = f"{i:03d}"
                date_str = t['date'].strftime('%Y_%m_%d')
                description = re.sub(r'[^\w\s-]', '', t['description'])
                description = re.sub(r'\s+', '_', description)[:50]

                if t['match_type'] == 'gmail':
                    extension = Path(t['receipt_file']).suffix
                    filename = f"{number}_{date_str}_{description}{extension}"
                else:
                    filename = f"{number}_{date_str}_{description}.html"

                writer.writerow({
                    'number': number,
                    'date': t['date'].strftime('%Y-%m-%d'),
                    'description': t['description'],
                    'amount': t['amount'],
                    'source': t.get('source', 'unknown'),
                    'match_type': t['match_type'],
                    'filename': filename
                })

        print(f"\n📄 Sammanfattning sparad: {summary_path}")


def main():
    """Huvudfunktion"""
    parser = argparse.ArgumentParser(
        description='Organisera kvitton baserat på banktransaktioner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exempel:
  # Organisera med Gmail-matchning
  python organize_receipts.py --csv bank_exports/december_2025.csv --gmail output/gmail

  # Endast bank CSV (ingen matchning)
  python organize_receipts.py --csv bank_exports/december_2025.csv --skip-gmail

  # Specificera bank
  python organize_receipts.py --csv bank_exports/december_2025.csv --bank seb
        """
    )

    parser.add_argument(
        '--csv',
        type=str,
        required=True,
        help='Sökväg till bank CSV-fil'
    )

    parser.add_argument(
        '--gmail',
        type=str,
        default='output/gmail',
        help='Katalog med Gmail-kvitton (default: output/gmail)'
    )

    parser.add_argument(
        '--skip-gmail',
        action='store_true',
        help='Hoppa över Gmail-matchning'
    )

    parser.add_argument(
        '--output',
        type=str,
        default='organized_receipts',
        help='Output-katalog för organiserade kvitton (default: organized_receipts)'
    )

    parser.add_argument(
        '--bank',
        type=str,
        default='auto',
        help='Banknamn: seb, swedbank, handelsbanken, nordea, eller auto (default: auto)'
    )

    args = parser.parse_args()

    # Kolla att CSV-filen finns
    if not os.path.exists(args.csv):
        print(f"❌ Kunde inte hitta CSV-fil: {args.csv}")
        sys.exit(1)

    # Skapa organizer
    organizer = ReceiptOrganizer(output_dir=args.output)

    # Kör organisering
    gmail_dir = None if args.skip_gmail else args.gmail
    stats = organizer.organize(args.csv, gmail_dir, bank=args.bank)

    print(f"\n🎉 Klart! Kolla i {args.output}/ för dina organiserade kvitton!")


if __name__ == '__main__':
    main()
