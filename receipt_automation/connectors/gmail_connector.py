"""
Gmail Connector - Hämtar kvitton från Gmail
Använder Gmail API för att söka efter kvitton och extrahera bilagor
"""

import os
import base64
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
import re

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

class GmailConnector:
    """Hanterar anslutning till Gmail och extrahering av kvitton"""

    # Vanliga söktermer för kvitton på svenska och engelska
    RECEIPT_KEYWORDS = [
        'kvitto',
        'faktura',
        'invoice',
        'receipt',
        'order confirmation',
        'orderbekräftelse',
        'betalningsbekräftelse',
        'purchase confirmation'
    ]

    # Vanliga avsändare som skickar kvitton
    COMMON_SENDERS = [
        'noreply',
        'receipt',
        'order',
        'invoice',
        'kvitto',
        'faktura',
        'swish',
        'paypal',
        'stripe',
        'klarna'
    ]

    def __init__(self, credentials_path: str = 'credentials.json', token_path: str = 'token.pickle'):
        """
        Initierar Gmail connector

        Args:
            credentials_path: Sökväg till Gmail API credentials JSON
            token_path: Sökväg där access token sparas
        """
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = None

    def authenticate(self) -> bool:
        """
        Autentiserar med Gmail API

        Returns:
            True om autentisering lyckades, annars False
        """
        creds = None

        # Ladda sparad token om den finns
        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)

        # Om ingen giltig token finns, få ny
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    print(f"❌ Kunde inte hitta credentials fil: {self.credentials_path}")
                    print("📝 Se README för instruktioner om hur du skapar Gmail API credentials")
                    return False

                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)

            # Spara token för framtida körningar
            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)

        try:
            self.service = build('gmail', 'v1', credentials=creds)
            return True
        except HttpError as error:
            print(f"❌ Ett fel uppstod vid anslutning till Gmail: {error}")
            return False

    def search_receipts(self, days_back: int = 30, custom_query: Optional[str] = None) -> List[Dict]:
        """
        Söker efter kvitton i Gmail

        Args:
            days_back: Antal dagar bakåt att söka
            custom_query: Valfri custom Gmail sökfråga

        Returns:
            Lista med meddelanden som innehåller kvitton
        """
        if not self.service:
            print("❌ Inte ansluten till Gmail. Kör authenticate() först.")
            return []

        # Bygg sökfråga
        if custom_query:
            query = custom_query
        else:
            # Skapa datum för sökning
            after_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y/%m/%d')

            # Bygg query med keywords
            keyword_query = ' OR '.join([f'"{keyword}"' for keyword in self.RECEIPT_KEYWORDS])
            query = f'after:{after_date} ({keyword_query}) has:attachment'

        print(f"🔍 Söker efter kvitton med query: {query}")

        try:
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=100
            ).execute()

            messages = results.get('messages', [])
            print(f"✅ Hittade {len(messages)} meddelanden")

            return messages

        except HttpError as error:
            print(f"❌ Ett fel uppstod vid sökning: {error}")
            return []

    def get_message_details(self, message_id: str) -> Optional[Dict]:
        """
        Hämtar detaljer om ett meddelande

        Args:
            message_id: Gmail meddelande ID

        Returns:
            Dict med meddelandedetaljer eller None
        """
        if not self.service:
            return None

        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()

            return message

        except HttpError as error:
            print(f"❌ Kunde inte hämta meddelande {message_id}: {error}")
            return None

    def extract_attachments(self, message: Dict, output_dir: str) -> List[str]:
        """
        Extraherar bilagor från ett meddelande

        Args:
            message: Gmail meddelande dict
            output_dir: Katalog där bilagor ska sparas

        Returns:
            Lista med sökvägar till sparade filer
        """
        if not self.service:
            return []

        saved_files = []
        message_id = message['id']

        # Extrahera metadata från headers
        headers = message['payload'].get('headers', [])
        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
        date_str = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')
        sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown')

        # Parse datum
        try:
            # Försök extrahera datum från email header
            date_match = re.search(r'\d{1,2}\s+\w+\s+\d{4}', date_str)
            if date_match:
                date_obj = datetime.strptime(date_match.group(), '%d %b %Y')
            else:
                date_obj = datetime.now()
        except:
            date_obj = datetime.now()

        date_prefix = date_obj.strftime('%Y-%m-%d')

        # Rensa subject för filnamn (ta bort specialtecken)
        safe_subject = re.sub(r'[^\w\s-]', '', subject)[:50]
        safe_subject = re.sub(r'\s+', '_', safe_subject)

        # Gå igenom alla parts av meddelandet
        parts = message['payload'].get('parts', [])

        # Hantera fall där hela payload är bilagan
        if not parts and 'body' in message['payload'] and message['payload']['body'].get('attachmentId'):
            parts = [message['payload']]

        for part in self._get_all_parts(message['payload']):
            if part.get('filename'):
                filename = part['filename']

                # Hoppa över om inte PDF, PNG, JPG eller vanliga kvittoformat
                if not any(filename.lower().endswith(ext) for ext in ['.pdf', '.png', '.jpg', '.jpeg']):
                    continue

                attachment_id = part['body'].get('attachmentId')
                if attachment_id:
                    try:
                        attachment = self.service.users().messages().attachments().get(
                            userId='me',
                            messageId=message_id,
                            id=attachment_id
                        ).execute()

                        data = attachment['data']
                        file_data = base64.urlsafe_b64decode(data)

                        # Skapa unikt filnamn
                        file_ext = Path(filename).suffix
                        new_filename = f"{date_prefix}_{safe_subject}_{filename}"
                        file_path = os.path.join(output_dir, new_filename)

                        # Se till att filnamnet är unikt
                        counter = 1
                        while os.path.exists(file_path):
                            new_filename = f"{date_prefix}_{safe_subject}_{counter}{file_ext}"
                            file_path = os.path.join(output_dir, new_filename)
                            counter += 1

                        # Spara filen
                        with open(file_path, 'wb') as f:
                            f.write(file_data)

                        saved_files.append(file_path)
                        print(f"  📄 Sparade: {new_filename}")

                    except HttpError as error:
                        print(f"  ❌ Kunde inte ladda ner bilaga: {error}")

        return saved_files

    def _get_all_parts(self, payload: Dict) -> List[Dict]:
        """
        Rekursivt hämtar alla parts från ett meddelande (inklusive nested parts)

        Args:
            payload: Message payload

        Returns:
            Lista med alla parts
        """
        parts = []

        if 'parts' in payload:
            for part in payload['parts']:
                parts.append(part)
                parts.extend(self._get_all_parts(part))
        else:
            parts.append(payload)

        return parts

    def collect_receipts(self, output_dir: str, days_back: int = 30) -> Dict[str, int]:
        """
        Samlar alla kvitton från Gmail

        Args:
            output_dir: Katalog där kvitton ska sparas
            days_back: Antal dagar bakåt att söka

        Returns:
            Dict med statistik (antal meddelanden, antal filer)
        """
        print("📧 Gmail Kvittoinhämtning")
        print("=" * 50)

        # Skapa output directory om den inte finns
        os.makedirs(output_dir, exist_ok=True)

        # Autentisera
        print("🔐 Autentiserar med Gmail...")
        if not self.authenticate():
            return {'messages': 0, 'files': 0}

        # Sök efter kvitton
        messages = self.search_receipts(days_back=days_back)

        if not messages:
            print("ℹ️  Inga kvitton hittades")
            return {'messages': 0, 'files': 0}

        # Extrahera bilagor från varje meddelande
        total_files = 0
        print(f"\n📥 Extraherar bilagor från {len(messages)} meddelanden...")

        for i, msg in enumerate(messages, 1):
            message_details = self.get_message_details(msg['id'])
            if message_details:
                print(f"\n[{i}/{len(messages)}] Bearbetar meddelande...")
                files = self.extract_attachments(message_details, output_dir)
                total_files += len(files)

        print(f"\n✅ Klart! Sparade {total_files} kvitton från {len(messages)} meddelanden")
        print(f"📁 Kvitton sparade i: {output_dir}")

        return {
            'messages': len(messages),
            'files': total_files
        }


if __name__ == '__main__':
    # Test av Gmail connector
    connector = GmailConnector()
    stats = connector.collect_receipts('output/gmail_receipts', days_back=30)
    print(f"\n📊 Statistik: {stats}")
