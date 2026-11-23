"""Strategy (Davranışsal Kalıp) — ödeme algoritmaları.

Context           -> SiparisIsleyici (siparis.py)
Strategy          -> IOdemeStratejisi
ConcreteStrategy  -> HavaleOdemeStratejisi, KrediKartiOdemeStratejisi

Her ödeme yöntemi kendi sınıfında kapsüllenir; SiparisIsleyici if/else
kullanmadan, kendisine verilen stratejiye ödemeyi devreder.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from .para import tl


@dataclass(frozen=True)
class OdemeSonucu:
    """Bir ödeme işleminin sonucu (değer nesnesi)."""

    yontem: str
    liste_fiyati: float
    odenen_tutar: float
    aciklama: str


# [Strategy: Strategy]
class IOdemeStratejisi(ABC):
    """Tüm ödeme algoritmalarının ortak arayüzü."""

    @abstractmethod
    def odeme_tutari_hesapla(self, liste_fiyati: float) -> float:
        """Ödeme yöntemine göre müşterinin ödeyeceği tutar."""

    @abstractmethod
    def ode(self, liste_fiyati: float) -> OdemeSonucu:
        """Ödemeyi gerçekleştirir ve sonucu döndürür."""


# [Strategy: ConcreteStrategy]
class HavaleOdemeStratejisi(IOdemeStratejisi):
    """Havale/EFT ile ödeme: liste fiyatı üzerinden indirim uygulanır."""

    def __init__(self, indirim_orani: float = 0.05) -> None:
        if not 0 <= indirim_orani < 1:
            raise ValueError("İndirim oranı 0 ile 1 arasında olmalıdır.")
        self._indirim_orani = indirim_orani

    def odeme_tutari_hesapla(self, liste_fiyati: float) -> float:
        return round(liste_fiyati * (1 - self._indirim_orani), 2)

    def ode(self, liste_fiyati: float) -> OdemeSonucu:
        tutar = self.odeme_tutari_hesapla(liste_fiyati)
        return OdemeSonucu(
            yontem="Havale",
            liste_fiyati=liste_fiyati,
            odenen_tutar=tutar,
            aciklama=f"%{self._indirim_orani * 100:g} havale indirimi uygulandı.",
        )


# [Strategy: ConcreteStrategy]
class KrediKartiOdemeStratejisi(IOdemeStratejisi):
    """Kredi kartı ile ödeme: taksit sayısına göre vade farkı eklenebilir."""

    def __init__(self, taksit_sayisi: int = 1, aylik_vade_farki: float = 0.02) -> None:
        if taksit_sayisi < 1:
            raise ValueError("Taksit sayısı en az 1 olmalıdır.")
        self._taksit_sayisi = taksit_sayisi
        self._aylik_vade_farki = aylik_vade_farki

    def odeme_tutari_hesapla(self, liste_fiyati: float) -> float:
        # Tek çekimde vade farkı yoktur; her ek taksit için vade farkı eklenir.
        oran = self._aylik_vade_farki * (self._taksit_sayisi - 1)
        return round(liste_fiyati * (1 + oran), 2)

    def ode(self, liste_fiyati: float) -> OdemeSonucu:
        tutar = self.odeme_tutari_hesapla(liste_fiyati)
        if self._taksit_sayisi == 1:
            detay = "Tek çekim."
        else:
            aylik = round(tutar / self._taksit_sayisi, 2)
            detay = f"{self._taksit_sayisi} taksit x {tl(aylik, 2)}."
        return OdemeSonucu(
            yontem="Kredi Kartı",
            liste_fiyati=liste_fiyati,
            odenen_tutar=tutar,
            aciklama=detay,
        )
