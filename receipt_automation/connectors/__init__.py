"""
Receipt Automation Connectors

Detta paket innehåller connectors för olika källor:
- gmail_connector: Hämtar kvitton från Gmail
- bank_connector: Bearbetar CSV-exporter från banker
- supplier_connector: Ramverk för leverantörsportaler
"""

from .gmail_connector import GmailConnector
from .bank_connector import BankConnector
from .supplier_connector import SupplierConnector

__all__ = ['GmailConnector', 'BankConnector', 'SupplierConnector']
