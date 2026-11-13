"""Modüler Bilgisayar Toplama ve Sipariş Sistemi.

Kullanılan GoF kalıpları:
    - Factory Method (yaratımsal) : fabrika.py
    - Decorator      (yapısal)    : dekoratorler.py
    - Strategy       (davranışsal): odeme.py + siparis.py
    - Observer       (davranışsal): takip.py
"""
from .dekoratorler import DonanimDecorator, EkSsdDecorator, RamYukseltmeDecorator, SiviSogutmaDecorator
from .fabrika import BilgisayarFabrikasi, StandartSistemFabrikasi
from .odeme import HavaleOdemeStratejisi, IOdemeStratejisi, KrediKartiOdemeStratejisi, OdemeSonucu
from .siparis import Siparis, SiparisIsleyici
from .takip import (
    ISiparisGozlemcisi,
    MusteriBildirimPaneli,
    SiparisDurumu,
    SiparisTakipMerkezi,
    TeknikServisPaneli,
)
from .urunler import IBilgisayar, OfisKasasi, OyunKasasi

__all__ = [
    "IBilgisayar", "OfisKasasi", "OyunKasasi",
    "BilgisayarFabrikasi", "StandartSistemFabrikasi",
    "DonanimDecorator", "RamYukseltmeDecorator", "SiviSogutmaDecorator", "EkSsdDecorator",
    "IOdemeStratejisi", "HavaleOdemeStratejisi", "KrediKartiOdemeStratejisi", "OdemeSonucu",
    "SiparisIsleyici", "Siparis",
    "SiparisTakipMerkezi", "ISiparisGozlemcisi", "MusteriBildirimPaneli", "TeknikServisPaneli",
    "SiparisDurumu",
]
