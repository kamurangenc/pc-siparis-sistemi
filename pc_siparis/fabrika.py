"""Factory Method (Yaratımsal Kalıp).

Creator          -> BilgisayarFabrikasi
ConcreteCreator  -> StandartSistemFabrikasi, HazirPaketFabrikasi
Product          -> IBilgisayar
ConcreteProduct  -> OfisKasasi, OyunKasasi (ve dekore edilmiş paketler)

İstemci (konsol arayüzü, AI asistanı) yalnızca BilgisayarFabrikasi ve
IBilgisayar soyutlamalarını bilir. Hangi fabrika verilirse verilsin aynı
akışla seçenekleri listeler ve ürün alır; somut sınıflara bağımlı değildir.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from .dekoratorler import DonanimDecorator, EkSsdDecorator, RamYukseltmeDecorator, SiviSogutmaDecorator
from .urunler import IBilgisayar, OfisKasasi, OyunKasasi
from .para import tl


class UretimHatasi(Exception):
    """Üretilen ürün kalite kontrolünden geçemediğinde fırlatılır."""


# [Factory Method: Creator]
class BilgisayarFabrikasi(ABC):
    """Creator: üretim sürecini tanımlar, hangi ürünün üretileceğini alt sınıfa bırakır.

    `siparis_icin_hazirla` tüm fabrikalar için ortak süreçtir (üret → kalite
    kontrol → seri numarası). Değişen tek adım `bilgisayar_olustur`'dur.
    """

    def __init__(self) -> None:
        self._seri_sayaci = 0

    @abstractmethod
    def bilgisayar_olustur(self, secim: str) -> IBilgisayar:
        """Factory Method: seçime göre ürün üretir."""

    @abstractmethod
    def secenekler(self) -> dict[str, str]:
        """Bu fabrikanın üretebildiği seçenekler: {kod: açıklama}."""

    def siparis_icin_hazirla(self, secim: str) -> IBilgisayar:
        """Ortak üretim süreci; somut ürünü factory method'dan alır."""
        bilgisayar = self.bilgisayar_olustur(secim)
        self._kalite_kontrol(bilgisayar)
        self._seri_sayaci += 1
        self.son_seri_no = f"{self.SERI_ON_EKI}-{self._seri_sayaci:04d}"
        return bilgisayar

    SERI_ON_EKI = "PC"

    @staticmethod
    def _kalite_kontrol(bilgisayar: IBilgisayar) -> None:
        if bilgisayar.maliyet() <= 0:
            raise UretimHatasi(f"{bilgisayar.aciklama()}: geçersiz fiyat.")
        if not bilgisayar.parca_listesi():
            raise UretimHatasi(f"{bilgisayar.aciklama()}: parça listesi boş.")


# [Factory Method: ConcreteCreator]
class StandartSistemFabrikasi(BilgisayarFabrikasi):
    """Kullanım amacına göre temel (donanımsız) kasa üretir.

    if/else yerine kayıt tablosu kullanılır; yeni bir model eklemek için
    yalnızca `kasa_kaydet` çağrılması yeterlidir (Open-Closed).
    """

    SERI_ON_EKI = "STD"

    def __init__(self) -> None:
        super().__init__()
        self._modeller: dict[str, type[IBilgisayar]] = {
            "ofis": OfisKasasi,
            "oyun": OyunKasasi,
        }

    def kasa_kaydet(self, kod: str, kasa_sinifi: type[IBilgisayar]) -> None:
        self._modeller[kod.lower()] = kasa_sinifi

    def secenekler(self) -> dict[str, str]:
        return {kod: f"{sinif().aciklama()} ({tl(sinif().maliyet(), 0)})" for kod, sinif in self._modeller.items()}

    def bilgisayar_olustur(self, secim: str) -> IBilgisayar:
        try:
            kasa_sinifi = self._modeller[secim.lower()]
        except KeyError:
            raise ValueError(
                f"Bilinmeyen kasa tipi: '{secim}'. Desteklenenler: {', '.join(self._modeller)}"
            ) from None
        return kasa_sinifi()


@dataclass(frozen=True)
class PaketTarifi:
    aciklama: str
    temel_kasa: str
    donanimlar: tuple[type[DonanimDecorator], ...]


# [Factory Method: ConcreteCreator]
class HazirPaketFabrikasi(BilgisayarFabrikasi):
    """Önceden yapılandırılmış paketler üretir (temel kasa + donanım dekoratörleri).

    Ürettiği nesne yine bir IBilgisayar'dır; istemci standart kasa mı yoksa
    dekore edilmiş paket mi aldığını bilmek zorunda değildir.
    """

    SERI_ON_EKI = "PKT"

    def __init__(self, temel_fabrika: StandartSistemFabrikasi | None = None) -> None:
        super().__init__()
        self._temel_fabrika = temel_fabrika or StandartSistemFabrikasi()
        self._paketler: dict[str, PaketTarifi] = {
            "ogrenci": PaketTarifi("Öğrenci Paketi", "ofis", (EkSsdDecorator,)),
            "yayinci": PaketTarifi("Yayıncı Paketi", "oyun", (RamYukseltmeDecorator, SiviSogutmaDecorator)),
            "pro": PaketTarifi(
                "Pro Paket", "oyun", (RamYukseltmeDecorator, SiviSogutmaDecorator, EkSsdDecorator)
            ),
        }

    def paket_kaydet(self, kod: str, tarif: PaketTarifi) -> None:
        self._paketler[kod.lower()] = tarif

    def secenekler(self) -> dict[str, str]:
        secenekler = {}
        for kod, tarif in self._paketler.items():
            pc = self.bilgisayar_olustur(kod)
            secenekler[kod] = f"{tarif.aciklama} ({tl(pc.maliyet(), 0)}): {pc.aciklama()}"
        return secenekler

    def bilgisayar_olustur(self, secim: str) -> IBilgisayar:
        try:
            tarif = self._paketler[secim.lower()]
        except KeyError:
            raise ValueError(f"Bilinmeyen paket: '{secim}'. Desteklenenler: {', '.join(self._paketler)}") from None
        bilgisayar = self._temel_fabrika.bilgisayar_olustur(tarif.temel_kasa)
        for donanim in tarif.donanimlar:
            bilgisayar = donanim(bilgisayar)
        return bilgisayar
