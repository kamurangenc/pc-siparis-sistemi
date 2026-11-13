"""Donanım kataloğu: kod → ConcreteDecorator eşlemesi.

Konsol arayüzü ve AI asistanı donanımları bu katalog üzerinden ekler.
Yeni bir donanım için DonanimDecorator alt sınıfı yazıp `kaydet` çağırmak yeterlidir.
"""
from __future__ import annotations

from dataclasses import dataclass

from .dekoratorler import DonanimDecorator, EkSsdDecorator, RamYukseltmeDecorator, SiviSogutmaDecorator
from .urunler import IBilgisayar


@dataclass(frozen=True)
class DonanimBilgisi:
    kod: str
    aciklama: str
    fiyat: float
    parca: str


class DonanimKatalogu:
    def __init__(self) -> None:
        self._donanimlar: dict[str, type[DonanimDecorator]] = {
            "ram": RamYukseltmeDecorator,
            "sivi_sogutma": SiviSogutmaDecorator,
            "ek_ssd": EkSsdDecorator,
        }

    def kaydet(self, kod: str, dekorator: type[DonanimDecorator]) -> None:
        self._donanimlar[kod] = dekorator

    def kodlar(self) -> list[str]:
        return list(self._donanimlar)

    def bilgi(self, kod: str) -> DonanimBilgisi:
        d = self._sinif(kod)
        return DonanimBilgisi(kod, d.EK_ACIKLAMA, d.EK_FIYAT, d.EK_PARCA)

    def tum_bilgiler(self) -> list[DonanimBilgisi]:
        return [self.bilgi(k) for k in self._donanimlar]

    def ekle(self, bilgisayar: IBilgisayar, kod: str) -> IBilgisayar:
        """Bilgisayarı ilgili donanım dekoratörüyle sarmalar."""
        return self._sinif(kod)(bilgisayar)

    def _sinif(self, kod: str) -> type[DonanimDecorator]:
        try:
            return self._donanimlar[kod]
        except KeyError:
            raise ValueError(f"Bilinmeyen donanım: '{kod}'. Geçerli: {', '.join(self._donanimlar)}") from None
