#!/usr/bin/env python3
"""
Kvittoinhämtare - Automatiserad insamling av kvitton för bokföring

Detta script samlar kvitton från:
- Gmail (e-postbilagor)
- Banktransaktioner (CSV-export)
- Leverantörsportaler (valfritt)

Användning:
    python collect_receipts.py [--days-back 30] [--config config.json]

Alternativt:
    python collect_receipts.py --interactive  (interaktiv läge)
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Importera connectors
sys.path.append(os.path.dirname(__file__))
from connectors.gmail_connector import GmailConnector
from connectors.bank_connector import BankConnector
from connectors.supplier_connector import SupplierConnector


class ReceiptCollector:
    """Huvudklass för att samla kvitton från alla källor"""

    def __init__(self, config_path: str = 'config.json'):
        """
        Initierar receipt collector

        Args:
            config_path: Sökväg till konfigurationsfil
        """
        self.config_path = config_path
        self.config = self._load_config()

        # Initiera connectors
        self.gmail_connector = None
        self.bank_connector = None
        self.supplier_connectors = []

    def _load_config(self) -> Dict:
        """Laddar konfiguration från fil"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️  Kunde inte läsa config fil: {e}")
                return self._default_config()
        else:
            print(f"ℹ️  Config fil finns inte: {self.config_path}")
            print("   Använder standardkonfiguration")
            return self._default_config()

    def _default_config(self) -> Dict:
        """Returnerar standardkonfiguration"""
        return {
            'output_dir': 'output',
            'gmail': {
                'enabled': True,
                'credentials_path': 'credentials.json',
                'token_path': 'token.pickle'
            },
            'bank': {
                'enabled': True,
                'csv_directory': 'bank_exports'
            },
            'suppliers': {
                'enabled': False,
                'connectors': []
            }
        }

    def collect_from_gmail(self, days_back: int = 30) -> Dict:
        """
        Samlar kvitton från Gmail

        Args:
            days_back: Antal dagar bakåt att söka

        Returns:
            Dict med statistik
        """
        if not self.config['gmail']['enabled']:
            print("ℹ️  Gmail inaktiverad i config")
            return {'messages': 0, 'files': 0}

        output_dir = os.path.join(self.config['output_dir'], 'gmail')
        os.makedirs(output_dir, exist_ok=True)

        self.gmail_connector = GmailConnector(
            credentials_path=self.config['gmail']['credentials_path'],
            token_path=self.config['gmail']['token_path']
        )

        return self.gmail_connector.collect_receipts(output_dir, days_back)

    def collect_from_bank(self) -> Dict:
        """
        Samlar transaktioner från bank CSV-filer

        Returns:
            Dict med statistik
        """
        if not self.config['bank']['enabled']:
            print("ℹ️  Bank inaktiverad i config")
            return {'total_transactions': 0, 'business_expenses': 0, 'files': 0}

        csv_dir = self.config['bank']['csv_directory']

        if not os.path.exists(csv_dir):
            print(f"⚠️  Bank CSV katalog finns inte: {csv_dir}")
            print(f"💡 Skapa katalogen och lägg dina bank-exporter där")
            return {'total_transactions': 0, 'business_expenses': 0, 'files': 0}

        # Hitta alla CSV-filer i katalogen
        csv_files = list(Path(csv_dir).glob('*.csv'))

        if not csv_files:
            print(f"⚠️  Inga CSV-filer hittades i {csv_dir}")
            return {'total_transactions': 0, 'business_expenses': 0, 'files': 0}

        csv_paths = [str(f) for f in csv_files]

        output_dir = os.path.join(self.config['output_dir'], 'bank')
        os.makedirs(output_dir, exist_ok=True)

        self.bank_connector = BankConnector()
        return self.bank_connector.collect_receipts(csv_paths, output_dir)

    def collect_from_suppliers(self) -> Dict:
        """
        Samlar kvitton från leverantörsportaler

        Returns:
            Dict med statistik
        """
        if not self.config['suppliers']['enabled']:
            print("ℹ️  Leverantörsportaler inaktiverade i config")
            return {'total_files': 0}

        print("\n🔗 Leverantörsportaler")
        print("=" * 50)
        print("⚠️  Leverantörsintegrationer kräver manuell konfiguration")
        print("💡 Se dokumentation för hur du konfigurerar leverantörer")

        return {'total_files': 0}

    def collect_all(self, days_back: int = 30) -> Dict:
        """
        Samlar kvitton från alla källor

        Args:
            days_back: Antal dagar bakåt att söka

        Returns:
            Dict med total statistik
        """
        print("🧾 KVITTOINHÄMTARE")
        print("=" * 70)
        print(f"📅 Datum: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📁 Output: {self.config['output_dir']}")
        print(f"🔍 Söker {days_back} dagar bakåt")
        print("=" * 70)

        total_stats = {
            'gmail': {},
            'bank': {},
            'suppliers': {}
        }

        # Gmail
        print("\n")
        try:
            total_stats['gmail'] = self.collect_from_gmail(days_back)
        except Exception as e:
            print(f"❌ Fel vid Gmail-insamling: {e}")
            total_stats['gmail'] = {'messages': 0, 'files': 0, 'error': str(e)}

        # Bank
        print("\n")
        try:
            total_stats['bank'] = self.collect_from_bank()
        except Exception as e:
            print(f"❌ Fel vid bankinsamling: {e}")
            total_stats['bank'] = {'total_transactions': 0, 'business_expenses': 0, 'files': 0, 'error': str(e)}

        # Leverantörer
        print("\n")
        try:
            total_stats['suppliers'] = self.collect_from_suppliers()
        except Exception as e:
            print(f"❌ Fel vid leverantörsinsamling: {e}")
            total_stats['suppliers'] = {'total_files': 0, 'error': str(e)}

        # Sammanfattning
        print("\n")
        print("=" * 70)
        print("📊 SAMMANFATTNING")
        print("=" * 70)
        print(f"📧 Gmail:")
        print(f"   - Meddelanden: {total_stats['gmail'].get('messages', 0)}")
        print(f"   - Kvitton: {total_stats['gmail'].get('files', 0)}")
        print(f"\n🏦 Bank:")
        print(f"   - Transaktioner: {total_stats['bank'].get('total_transactions', 0)}")
        print(f"   - Företagsutgifter: {total_stats['bank'].get('business_expenses', 0)}")
        print(f"\n🔗 Leverantörer:")
        print(f"   - Kvitton: {total_stats['suppliers'].get('total_files', 0)}")

        total_files = (
            total_stats['gmail'].get('files', 0) +
            total_stats['bank'].get('files', 0) +
            total_stats['suppliers'].get('total_files', 0)
        )

        print(f"\n✅ Totalt {total_files} filer sparade i {self.config['output_dir']}/")
        print("=" * 70)

        return total_stats

    def interactive_mode(self):
        """Interaktiv läge för att konfigurera och köra insamling"""
        print("🧾 KVITTOINHÄMTARE - Interaktivt Läge")
        print("=" * 70)

        # Fråga om Gmail
        use_gmail = input("\n📧 Vill du hämta kvitton från Gmail? (j/n): ").lower().strip() == 'j'

        # Fråga om Bank
        use_bank = input("🏦 Vill du bearbeta bank CSV-filer? (j/n): ").lower().strip() == 'j'

        if use_bank:
            bank_csv_dir = input("   Katalog med bank CSV-filer (default: bank_exports): ").strip()
            if not bank_csv_dir:
                bank_csv_dir = 'bank_exports'

            # Skapa katalogen om den inte finns
            os.makedirs(bank_csv_dir, exist_ok=True)

            if not list(Path(bank_csv_dir).glob('*.csv')):
                print(f"   ⚠️  Inga CSV-filer i {bank_csv_dir}")
                print(f"   💡 Lägg dina bank-exporter där och kör igen")
                use_bank = False

        # Fråga om antal dagar
        days_input = input("\n🔍 Hur många dagar bakåt vill du söka? (default: 30): ").strip()
        days_back = int(days_input) if days_input.isdigit() else 30

        # Uppdatera config
        self.config['gmail']['enabled'] = use_gmail
        self.config['bank']['enabled'] = use_bank
        if use_bank:
            self.config['bank']['csv_directory'] = bank_csv_dir

        # Kör insamling
        print("\n🚀 Startar insamling...")
        self.collect_all(days_back)


def main():
    """Huvudfunktion"""
    parser = argparse.ArgumentParser(
        description='Automatiserad kvittoinhämtning för bokföring',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exempel:
  python collect_receipts.py                    # Kör med standardinställningar
  python collect_receipts.py --days-back 60     # Hämta från senaste 60 dagarna
  python collect_receipts.py --interactive      # Interaktivt läge
  python collect_receipts.py --config my.json   # Använd annan config-fil

Första gången:
  1. Kör: python collect_receipts.py --interactive
  2. Följ instruktionerna för att konfigurera Gmail
  3. Lägg dina bank CSV-filer i bank_exports/
        """
    )

    parser.add_argument(
        '--days-back',
        type=int,
        default=30,
        help='Antal dagar bakåt att söka (default: 30)'
    )

    parser.add_argument(
        '--config',
        type=str,
        default='config.json',
        help='Sökväg till konfigurationsfil (default: config.json)'
    )

    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Kör i interaktivt läge'
    )

    args = parser.parse_args()

    # Skapa collector
    collector = ReceiptCollector(config_path=args.config)

    # Kör interaktivt eller normalt läge
    if args.interactive:
        collector.interactive_mode()
    else:
        collector.collect_all(days_back=args.days_back)


if __name__ == '__main__':
    main()
