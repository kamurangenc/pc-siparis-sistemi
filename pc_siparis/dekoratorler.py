"""Decorator (Yapısal Kalıp) — saf GoF nesne kompozisyonu (Python @ dekoratörü değil).

Component          -> IBilgisayar
ConcreteComponent  -> OfisKasasi, OyunKasasi
Decorator          -> DonanimDecorator
ConcreteDecorator  -> RamYukseltmeDecorator, SiviSogutmaDecorator, EkSsdDecorator

Her dekoratör bir IBilgisayar nesnesini sarmalar ve maliyet/parça listesine
kendi katkısını ekler. Böylece her kombinasyon için alt sınıf açmaya gerek kalmaz.
"""
from __future__ import annotations

from abc import ABC

from .urunler import IBilgisayar


# [Decorator: Decorator]
class DonanimDecorator(IBilgisayar, ABC):
    """Decorator: sarmalanan bileşene çağrıları iletir, alt sınıflar ekleme yapar.

    Alt sınıflar yalnızca EK_ACIKLAMA, EK_FIYAT ve EK_PARCA tanımlayarak
    yeni bir donanım ekleyebilir; gerekirse metotları override edebilir.
    """

    EK_ACIKLAMA: str = ""
    EK_FIYAT: float = 0.0
    EK_PARCA: str = ""

    def __init__(self, bilgisayar: IBilgisayar) -> None:
        self._bilgisayar = bilgisayar

    def aciklama(self) -> str:
        return f"{self._bilgisayar.aciklama()} + {self.EK_ACIKLAMA}"

    def maliyet(self) -> float:
        return self._bilgisayar.maliyet() + self.EK_FIYAT

    def parca_listesi(self) -> list[str]:
        return [*self._bilgisayar.parca_listesi(), self.EK_PARCA]


# [Decorator: ConcreteDecorator]
class RamYukseltmeDecorator(DonanimDecorator):
    EK_ACIKLAMA = "16 GB Ek RAM"
    EK_FIYAT = 2_500.0
    EK_PARCA = "Ek RAM: 16 GB DDR5"


# [Decorator: ConcreteDecorator]
class SiviSogutmaDecorator(DonanimDecorator):
    EK_ACIKLAMA = "Sıvı Soğutma"
    EK_FIYAT = 4_000.0
    EK_PARCA = "Soğutma: 240 mm AIO Sıvı Soğutma"


# [Decorator: ConcreteDecorator]
class EkSsdDecorator(DonanimDecorator):
    EK_ACIKLAMA = "1 TB Ek SSD"
    EK_FIYAT = 3_000.0
    EK_PARCA = "Ek Depolama: 1 TB NVMe SSD"
