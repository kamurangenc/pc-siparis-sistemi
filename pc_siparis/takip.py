"""Observer (Davranışsal Kalıp) — sipariş durum takibi.

Subject           -> SiparisTakipMerkezi
Observer          -> ISiparisGozlemcisi
ConcreteObserver  -> MusteriBildirimPaneli, TeknikServisPaneli

Sipariş durumu (montaj, test, kargo ...) değiştiğinde takip merkezi kayıtlı
tüm gözlemcileri haberdar eder. Takip merkezi somut panelleri tanımaz;
yalnızca ISiparisGozlemcisi arayüzüne bağımlıdır. Dilin/kütüphanenin hazır
bir Observer yapısı kullanılmamıştır.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum


class SiparisDurumu(Enum):
    """Bir siparişin geçebileceği aşamalar (sırası önemlidir)."""

    ODEME_ALINDI = "Ödeme alındı"
    MONTAJDA = "Montaj aşamasında"
    TESTTE = "Test aşamasında"
    KARGODA = "Kargoya verildi"


# [Observer: Observer]
class ISiparisGozlemcisi(ABC):
    """Sipariş durum değişikliklerinden haberdar olmak isteyen yapıların arayüzü."""

    @abstractmethod
    def guncelle(self, siparis_no: int, durum: SiparisDurumu, detay: str) -> None:
        """Takip merkezi tarafından durum değiştiğinde çağrılır."""


# [Observer: Subject]
class SiparisTakipMerkezi:
    """Gözlemci kaydını tutar ve durum değişikliklerini yayınlar."""

    def __init__(self) -> None:
        self._gozlemciler: list[ISiparisGozlemcisi] = []
        self._durumlar: dict[int, SiparisDurumu] = {}

    def abone_ekle(self, gozlemci: ISiparisGozlemcisi) -> None:
        if gozlemci not in self._gozlemciler:
            self._gozlemciler.append(gozlemci)

    def abone_cikar(self, gozlemci: ISiparisGozlemcisi) -> None:
        if gozlemci in self._gozlemciler:
            self._gozlemciler.remove(gozlemci)

    def durum_getir(self, siparis_no: int) -> SiparisDurumu | None:
        return self._durumlar.get(siparis_no)

    def durum_guncelle(self, siparis_no: int, durum: SiparisDurumu, detay: str = "") -> None:
        self._durumlar[siparis_no] = durum
        self._bildir(siparis_no, durum, detay)

    def _bildir(self, siparis_no: int, durum: SiparisDurumu, detay: str) -> None:
        # Kopya üzerinde dolaşılır: bildirim sırasında abonelik değişse de güvenli.
        for gozlemci in list(self._gozlemciler):
            gozlemci.guncelle(siparis_no, durum, detay)


# [Observer: ConcreteObserver]
class MusteriBildirimPaneli(ISiparisGozlemcisi):
    """Müşteriye gösterilen sade durum bildirimleri."""

    def __init__(self, musteri_adi: str) -> None:
        self.musteri_adi = musteri_adi
        self.bildirimler: list[str] = []

    def guncelle(self, siparis_no: int, durum: SiparisDurumu, detay: str) -> None:
        mesaj = f"Sayın {self.musteri_adi}, #{siparis_no} numaralı siparişiniz: {durum.value}"
        self.bildirimler.append(mesaj)
        print(f"  [Müşteri Paneli] {mesaj}")


# [Observer: ConcreteObserver]
class TeknikServisPaneli(ISiparisGozlemcisi):
    """Teknik servisin iş takibi: yalnızca montaj ve test aşamalarıyla ilgilenir."""

    ILGILI_DURUMLAR = {SiparisDurumu.MONTAJDA, SiparisDurumu.TESTTE}

    def __init__(self) -> None:
        self.is_kayitlari: list[str] = []

    def guncelle(self, siparis_no: int, durum: SiparisDurumu, detay: str) -> None:
        if durum not in self.ILGILI_DURUMLAR:
            return
        kayit = f"#{siparis_no} -> {durum.name}" + (f" | {detay}" if detay else "")
        self.is_kayitlari.append(kayit)
        print(f"  [Teknik Servis] {kayit}")
