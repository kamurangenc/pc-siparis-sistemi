"""Factory Method (Yaratımsal Kalıp).

Creator          -> BilgisayarFabrikasi
ConcreteCreator  -> StandartSistemFabrikasi
Product          -> IBilgisayar
ConcreteProduct  -> OfisKasasi, OyunKasasi

İstemci yalnızca BilgisayarFabrikasi ve IBilgisayar soyutlamalarını bilir;
somut kasa sınıflarına doğrudan bağımlı değildir.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from .urunler import IBilgisayar, OfisKasasi, OyunKasasi


# [Factory Method: Creator]
class BilgisayarFabrikasi(ABC):
    """Creator: kasa üretim sürecini tanımlar, somut üretimi alt sınıfa bırakır."""

    @abstractmethod
    def bilgisayar_olustur(self, kullanim_amaci: str) -> IBilgisayar:
        """Factory Method: kullanım amacına göre temel kasa üretir."""

    def siparis_icin_hazirla(self, kullanim_amaci: str) -> IBilgisayar:
        """Şablon işlem: üretimi factory method'a devreder, ortak adımları yürütür."""
        bilgisayar = self.bilgisayar_olustur(kullanim_amaci)
        print(f"[Fabrika] {bilgisayar.aciklama()} üretildi.")
        return bilgisayar


# [Factory Method: ConcreteCreator]
class StandartSistemFabrikasi(BilgisayarFabrikasi):
    """ConcreteCreator: standart kasa modellerini üretir.

    if/else yerine kayıt tablosu kullanılır; yeni bir model eklemek için
    yalnızca `kasa_kaydet` çağrılması yeterlidir (Open-Closed).
    """

    def __init__(self) -> None:
        self._modeller: dict[str, type[IBilgisayar]] = {
            "ofis": OfisKasasi,
            "oyun": OyunKasasi,
        }

    def kasa_kaydet(self, kullanim_amaci: str, kasa_sinifi: type[IBilgisayar]) -> None:
        self._modeller[kullanim_amaci.lower()] = kasa_sinifi

    def desteklenen_modeller(self) -> list[str]:
        return sorted(self._modeller)

    def bilgisayar_olustur(self, kullanim_amaci: str) -> IBilgisayar:
        try:
            kasa_sinifi = self._modeller[kullanim_amaci.lower()]
        except KeyError:
            raise ValueError(
                f"Bilinmeyen kasa tipi: '{kullanim_amaci}'. "
                f"Desteklenenler: {', '.join(self.desteklenen_modeller())}"
            ) from None
        return kasa_sinifi()
