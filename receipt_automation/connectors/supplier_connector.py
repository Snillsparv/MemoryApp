"""
Supplier Connector - Ramverk för att hämta kvitton från leverantörsportaler

Detta är en bas-klass och exempel-implementationer för vanliga leverantörer.
För att lägga till fler leverantörer, skapa en subklass av SupplierConnector.
"""

import os
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from abc import ABC, abstractmethod

# Selenium för web scraping (installeras via requirements.txt)
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("⚠️  Selenium inte installerat. Kör: pip install selenium")


class SupplierConnector(ABC):
    """Bas-klass för leverantörsanslutningar"""

    def __init__(self, headless: bool = True):
        """
        Initierar connector

        Args:
            headless: Kör webbläsare i headless mode (ingen GUI)
        """
        self.headless = headless
        self.driver = None

    def _init_driver(self):
        """Initierar Selenium WebDriver"""
        if not SELENIUM_AVAILABLE:
            raise ImportError("Selenium krävs för supplier connector. Kör: pip install selenium")

        options = Options()
        if self.headless:
            options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

        # Konfigurera download directory
        prefs = {
            "download.default_directory": os.path.abspath("temp_downloads"),
            "download.prompt_for_download": False,
        }
        options.add_experimental_option("prefs", prefs)

        self.driver = webdriver.Chrome(options=options)

    def _close_driver(self):
        """Stänger WebDriver"""
        if self.driver:
            self.driver.quit()
            self.driver = None

    @abstractmethod
    def login(self, username: str, password: str) -> bool:
        """
        Loggar in på leverantörsportalen

        Args:
            username: Användarnamn
            password: Lösenord

        Returns:
            True om inloggning lyckades
        """
        pass

    @abstractmethod
    def download_receipts(self, output_dir: str, days_back: int = 30) -> List[str]:
        """
        Laddar ner kvitton från portalen

        Args:
            output_dir: Katalog där kvitton ska sparas
            days_back: Antal dagar bakåt att hämta

        Returns:
            Lista med sökvägar till nedladdade filer
        """
        pass

    def collect_receipts(self, username: str, password: str, output_dir: str, days_back: int = 30) -> Dict[str, int]:
        """
        Komplett process för att samla kvitton

        Args:
            username: Användarnamn
            password: Lösenord
            output_dir: Katalog där kvitton ska sparas
            days_back: Antal dagar bakåt att hämta

        Returns:
            Dict med statistik
        """
        print(f"🔗 {self.__class__.__name__} - Kvittoinhämtning")
        print("=" * 50)

        try:
            self._init_driver()

            print("🔐 Loggar in...")
            if not self.login(username, password):
                print("❌ Inloggning misslyckades")
                return {'files': 0}

            print("📥 Laddar ner kvitton...")
            files = self.download_receipts(output_dir, days_back)

            print(f"✅ Laddade ner {len(files)} kvitton")

            return {'files': len(files)}

        except Exception as e:
            print(f"❌ Ett fel uppstod: {e}")
            return {'files': 0}

        finally:
            self._close_driver()


class AWSConnector(SupplierConnector):
    """Exempel: AWS (Amazon Web Services) kvitton"""

    def __init__(self, headless: bool = True):
        super().__init__(headless)
        self.base_url = "https://console.aws.amazon.com/billing/home"

    def login(self, username: str, password: str) -> bool:
        """Loggar in på AWS Console"""
        try:
            self.driver.get(self.base_url)
            time.sleep(2)

            # AWS har komplex inloggning, detta är en förenklad version
            # I verkligheten skulle du behöva hantera MFA, olika konto-typer, etc.

            print("⚠️  AWS-inloggning kräver manuell implementation")
            print("💡 Rekommendation: Ladda ner fakturor manuellt från AWS Console")
            print("   eller använd AWS Cost and Usage Reports API")

            return False

        except Exception as e:
            print(f"❌ Fel vid inloggning: {e}")
            return False

    def download_receipts(self, output_dir: str, days_back: int = 30) -> List[str]:
        """Laddar ner AWS-fakturor"""
        # AWS fakturor kräver specifik implementation med AWS SDK
        # Detta är bara en placeholder
        return []


class StripeConnector(SupplierConnector):
    """Exempel: Stripe kvitton och fakturor"""

    def __init__(self, headless: bool = True):
        super().__init__(headless)
        self.base_url = "https://dashboard.stripe.com/login"

    def login(self, username: str, password: str) -> bool:
        """Loggar in på Stripe Dashboard"""
        try:
            self.driver.get(self.base_url)
            time.sleep(2)

            print("⚠️  Stripe-inloggning kräver manuell implementation")
            print("💡 Rekommendation: Använd Stripe API istället")
            print("   Se: https://stripe.com/docs/api/invoices/list")

            return False

        except Exception as e:
            print(f"❌ Fel vid inloggning: {e}")
            return False

    def download_receipts(self, output_dir: str, days_back: int = 30) -> List[str]:
        """Laddar ner Stripe-fakturor"""
        # Stripe har ett utmärkt API för att hämta fakturor
        # Detta bör implementeras med Stripe API istället för web scraping
        return []


class GenericSupplierConnector(SupplierConnector):
    """
    Generisk connector som kan konfigureras för olika leverantörer
    med liknande portalstrukturer
    """

    def __init__(self, config: Dict, headless: bool = True):
        """
        Args:
            config: Dict med konfiguration för portalen
                {
                    'name': 'Leverantörsnamn',
                    'login_url': 'https://...',
                    'username_field': 'id eller name för username-fält',
                    'password_field': 'id eller name för password-fält',
                    'submit_button': 'id eller name för login-knapp',
                    'receipts_url': 'URL till kvittossida efter inloggning',
                    'download_selectors': ['CSS selector för nedladdningslänkar']
                }
        """
        super().__init__(headless)
        self.config = config

    def login(self, username: str, password: str) -> bool:
        """Generisk inloggning"""
        try:
            self.driver.get(self.config['login_url'])
            time.sleep(2)

            # Hitta och fyll i användarnamn
            username_field = self.driver.find_element(By.NAME, self.config['username_field'])
            username_field.send_keys(username)

            # Hitta och fyll i lösenord
            password_field = self.driver.find_element(By.NAME, self.config['password_field'])
            password_field.send_keys(password)

            # Klicka på login-knapp
            submit_button = self.driver.find_element(By.NAME, self.config['submit_button'])
            submit_button.click()

            time.sleep(3)

            # Enkel verifiering att vi är inloggade
            if self.driver.current_url != self.config['login_url']:
                print(f"✅ Inloggad på {self.config['name']}")
                return True
            else:
                print(f"❌ Inloggning misslyckades på {self.config['name']}")
                return False

        except Exception as e:
            print(f"❌ Fel vid inloggning: {e}")
            return False

    def download_receipts(self, output_dir: str, days_back: int = 30) -> List[str]:
        """Generisk nedladdning av kvitton"""
        files = []

        try:
            # Navigera till kvittossida
            self.driver.get(self.config['receipts_url'])
            time.sleep(2)

            # Hitta nedladdningslänkar
            for selector in self.config.get('download_selectors', []):
                try:
                    links = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    print(f"  Hittade {len(links)} nedladdningslänkar")

                    for link in links[:10]:  # Begränsa till 10 senaste
                        try:
                            link.click()
                            time.sleep(1)
                        except Exception as e:
                            print(f"  ⚠️  Kunde inte klicka på länk: {e}")

                except NoSuchElementException:
                    print(f"  ⚠️  Kunde inte hitta element med selector: {selector}")

            # Här skulle man flytta nedladdade filer från temp_downloads till output_dir
            # och returnera listan med filer

        except Exception as e:
            print(f"❌ Fel vid nedladdning: {e}")

        return files


def create_supplier_config_template() -> Dict:
    """
    Skapar en mall för leverantörskonfiguration

    Returns:
        Dict med konfigurationsmall
    """
    return {
        'name': 'Leverantörsnamn',
        'login_url': 'https://portal.leverantor.se/login',
        'username_field': 'email',  # name eller id för username-fält
        'password_field': 'password',  # name eller id för password-fält
        'submit_button': 'login-button',  # name eller id för login-knapp
        'receipts_url': 'https://portal.leverantor.se/receipts',
        'download_selectors': [
            'a.download-receipt',  # CSS selector för nedladdningslänkar
            'button[data-action="download"]'
        ]
    }


if __name__ == '__main__':
    print("🔗 Supplier Connector Framework")
    print("=" * 50)
    print("\n💡 Detta är ett ramverk för att hämta kvitton från leverantörsportaler")
    print("\n📖 För att använda:")
    print("1. För vanliga leverantörer med API: Använd deras API istället (rekommenderat)")
    print("2. För portaler utan API: Skapa en konfiguration för GenericSupplierConnector")
    print("3. För komplexa portaler: Skapa en egen subklass av SupplierConnector")
    print("\n⚠️  OBS: Web scraping är fragilt och kan sluta fungera om portalen ändras")
    print("💡 Rekommendation: Använd API:er där det är möjligt, annars ladda ner kvitton manuellt")
