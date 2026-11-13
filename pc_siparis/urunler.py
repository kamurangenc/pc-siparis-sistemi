"""Ürün / Bileşen katmanı.

Factory Method  -> Product (IBilgisayar), ConcreteProduct (OfisKasasi, OyunKasasi)
Decorator       -> Component (IBilgisayar), ConcreteComponent (OfisKasasi, OyunKasasi)

IBilgisayar her iki kalıpta da ortak arayüzdür: fabrika bu tipte nesne üretir,
dekoratörler de bu tipteki nesneleri sarmalar.
"""
from __future__ import annotations

from abc import ABC, abstractmethod


# [Factory Method: Product] [Decorator: Component]
class IBilgisayar(ABC):
    """Tüm kasaların ve donanım dekoratörlerinin uyduğu ortak arayüz."""

    @abstractmethod
    def aciklama(self) -> str:
        """Kısa, okunabilir ürün açıklaması."""

    @abstractmethod
    def maliyet(self) -> float:
        """Toplam fiyat (TL)."""

    @abstractmethod
    def parca_listesi(self) -> list[str]:
        """Sistemdeki tüm parçaların listesi."""


# [Factory Method: ConcreteProduct] [Decorator: ConcreteComponent]
class OfisKasasi(IBilgisayar):
    """Ofis kullanımına yönelik temel kasa."""

    TEMEL_FIYAT = 15_000.0

    def aciklama(self) -> str:
        return "Ofis Kasası"

    def maliyet(self) -> float:
        return self.TEMEL_FIYAT

    def parca_listesi(self) -> list[str]:
        return [
            "İşlemci: Intel Core i3",
            "RAM: 8 GB DDR4",
            "Depolama: 256 GB SSD",
            "Ekran Kartı: Dahili",
        ]


# [Factory Method: ConcreteProduct] [Decorator: ConcreteComponent]
class OyunKasasi(IBilgisayar):
    """Oyun kullanımına yönelik temel kasa."""

    TEMEL_FIYAT = 40_000.0

    def aciklama(self) -> str:
        return "Oyun Kasası"

    def maliyet(self) -> float:
        return self.TEMEL_FIYAT

    def parca_listesi(self) -> list[str]:
        return [
            "İşlemci: AMD Ryzen 7",
            "RAM: 16 GB DDR5",
            "Depolama: 1 TB NVMe SSD",
            "Ekran Kartı: RTX 4070",
        ]
