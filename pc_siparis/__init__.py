"""Modüler Bilgisayar Toplama ve Sipariş Sistemi.

Zorunlu GoF kalıpları:
    - Factory Method (yaratımsal) : fabrika.py
    - Decorator      (yapısal)    : dekoratorler.py
    - Strategy       (davranışsal): odeme.py + siparis.py
    - Observer       (davranışsal): takip.py
AI asistanında ek kalıplar (ai/ paketi):
    - Adapter (yapısal), Command (davranışsal)
    - LLM kalıpları: Tool Use, Guardrail
"""
from .dekoratorler import DonanimDecorator, EkSsdDecorator, RamYukseltmeDecorator, SiviSogutmaDecorator
from .fabrika import BilgisayarFabrikasi, HazirPaketFabrikasi, PaketTarifi, StandartSistemFabrikasi, UretimHatasi
from .katalog import DonanimBilgisi, DonanimKatalogu
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
    "BilgisayarFabrikasi", "StandartSistemFabrikasi", "HazirPaketFabrikasi", "PaketTarifi", "UretimHatasi",
    "DonanimDecorator", "RamYukseltmeDecorator", "SiviSogutmaDecorator", "EkSsdDecorator",
    "DonanimKatalogu", "DonanimBilgisi",
    "IOdemeStratejisi", "HavaleOdemeStratejisi", "KrediKartiOdemeStratejisi", "OdemeSonucu",
    "SiparisIsleyici", "Siparis",
    "SiparisTakipMerkezi", "ISiparisGozlemcisi", "MusteriBildirimPaneli", "TeknikServisPaneli",
    "SiparisDurumu",
]
