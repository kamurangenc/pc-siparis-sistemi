"""Command (Davranışsal Kalıp) + LLM Tool Use kalıbı.

Command          -> IArac
ConcreteCommand  -> KatalogListeleAraci, FiyatHesaplaAraci, OneriSunAraci
Invoker          -> AracYurutucu
Receiver         -> BilgisayarFabrikasi, DonanimKatalogu
Client           -> DonanimOneriAsistani (asistan.py)

Dil modeli bir aracı adıyla ve JSON girdisiyle "ister". Her istek bir komut
nesnesi tarafından yürütülür; AracYurutucu komutları adlarına göre çağırır,
hangi alıcıya (fabrika, katalog) gittiklerini bilmez. Yeni bir araç eklemek
asistanı veya yürütücüyü değiştirmez (if/else yok).
"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any

from ..fabrika import BilgisayarFabrikasi
from ..katalog import DonanimKatalogu
from ..urunler import IBilgisayar
from .dil_modeli import AracCagrisi, AracSonucu, AracTanimi
from ..para import tl


class AracHatasi(Exception):
    """Aracın girdisi geçersizse; mesajı modele hata sonucu olarak döner."""


# [Command: Command]
class IArac(ABC):
    ad: str
    aciklama: str
    girdi_semasi: dict[str, Any]

    def tanim(self) -> AracTanimi:
        return AracTanimi(self.ad, self.aciklama, self.girdi_semasi)

    @abstractmethod
    def calistir(self, girdi: dict[str, Any]) -> str:
        """Komutu yürütür; modele dönecek metni (JSON) verir."""


def _sistem_kur(fabrika: BilgisayarFabrikasi, katalog: DonanimKatalogu, kasa: str, donanimlar: list[str]) -> IBilgisayar:
    """Fabrika (Factory Method) + katalog (Decorator) ile gerçek ürünü oluşturur."""
    try:
        bilgisayar = fabrika.bilgisayar_olustur(kasa)
        for kod in donanimlar:
            bilgisayar = katalog.ekle(bilgisayar, kod)
    except ValueError as e:
        raise AracHatasi(str(e)) from e
    return bilgisayar


_KASA_DONANIM_SEMASI = {
    "kasa": {"type": "string", "description": "Temel kasa kodu (katalog_listele çıktısındaki 'kasalar')."},
    "donanimlar": {
        "type": "array",
        "items": {"type": "string"},
        "description": "Eklenecek donanım kodları (katalog_listele çıktısındaki 'donanimlar').",
    },
}


# [Command: ConcreteCommand]
class KatalogListeleAraci(IArac):
    ad = "katalog_listele"
    aciklama = "Satıştaki temel kasaları ve ek donanımları fiyatlarıyla listeler. Öneriden önce çağır."
    girdi_semasi = {"type": "object", "properties": {}, "required": [], "additionalProperties": False}

    def __init__(self, fabrika: BilgisayarFabrikasi, katalog: DonanimKatalogu) -> None:
        self._fabrika = fabrika  # Receiver
        self._katalog = katalog  # Receiver

    def calistir(self, girdi: dict[str, Any]) -> str:
        kasalar = {}
        for kod in self._fabrika.secenekler():
            pc = self._fabrika.bilgisayar_olustur(kod)
            kasalar[kod] = {"ad": pc.aciklama(), "fiyat_tl": pc.maliyet(), "parcalar": pc.parca_listesi()}
        donanimlar = {d.kod: {"ad": d.aciklama, "fiyat_tl": d.fiyat, "parca": d.parca} for d in self._katalog.tum_bilgiler()}
        return json.dumps({"kasalar": kasalar, "donanimlar": donanimlar}, ensure_ascii=False)


# [Command: ConcreteCommand]
class FiyatHesaplaAraci(IArac):
    ad = "fiyat_hesapla"
    aciklama = "Bir kasa + donanım kombinasyonunun toplam fiyatını ve parça listesini hesaplar."
    girdi_semasi = {
        "type": "object",
        "properties": _KASA_DONANIM_SEMASI,
        "required": ["kasa", "donanimlar"],
        "additionalProperties": False,
    }

    def __init__(self, fabrika: BilgisayarFabrikasi, katalog: DonanimKatalogu, butce: float | None = None) -> None:
        self._fabrika, self._katalog, self._butce = fabrika, katalog, butce

    def calistir(self, girdi: dict[str, Any]) -> str:
        pc = _sistem_kur(self._fabrika, self._katalog, girdi["kasa"], girdi["donanimlar"])
        sonuc = {"aciklama": pc.aciklama(), "toplam_tl": pc.maliyet(), "parcalar": pc.parca_listesi()}
        if self._butce is not None:
            sonuc["butce_tl"] = self._butce
            sonuc["butceye_uygun"] = pc.maliyet() <= self._butce
            if pc.maliyet() > self._butce:
                raise AracHatasi(f"Toplam {tl(pc.maliyet(), 0)}, bütçe ({tl(self._butce, 0)}) aşılıyor.")
        return json.dumps(sonuc, ensure_ascii=False)


# [Command: ConcreteCommand]
class OneriSunAraci(IArac):
    """Son öneriyi yapılandırılmış biçimde teslim eder (serbest metin ayrıştırmaya gerek kalmaz)."""

    ad = "oneri_sun"
    aciklama = "Müşteriye sunulacak nihai öneriyi teslim eder. Konuşmayı bitirmek için en son bunu çağır."
    girdi_semasi = {
        "type": "object",
        "properties": {
            **_KASA_DONANIM_SEMASI,
            "gerekce": {"type": "string", "description": "Seçimin kısa, Türkçe gerekçesi."},
        },
        "required": ["kasa", "donanimlar", "gerekce"],
        "additionalProperties": False,
    }

    def __init__(self, fabrika: BilgisayarFabrikasi, katalog: DonanimKatalogu) -> None:
        self._fabrika, self._katalog = fabrika, katalog
        self.son_oneri: tuple[IBilgisayar, str] | None = None

    def calistir(self, girdi: dict[str, Any]) -> str:
        pc = _sistem_kur(self._fabrika, self._katalog, girdi["kasa"], girdi["donanimlar"])
        self.son_oneri = (pc, girdi["gerekce"])
        return json.dumps({"durum": "kaydedildi", "toplam_tl": pc.maliyet()}, ensure_ascii=False)


# [Command: Invoker]
class AracYurutucu:
    """Komutları adlarına göre çağırır; hataları modele dönecek sonuca çevirir."""

    def __init__(self, araclar: list[IArac]) -> None:
        self._araclar = {a.ad: a for a in araclar}

    def tanimlar(self) -> list[AracTanimi]:
        return [a.tanim() for a in self._araclar.values()]

    def yurut(self, cagri: AracCagrisi) -> AracSonucu:
        arac = self._araclar.get(cagri.ad)
        if arac is None:
            return AracSonucu(cagri.cagri_id, f"Bilinmeyen araç: {cagri.ad}", hata=True)
        try:
            return AracSonucu(cagri.cagri_id, arac.calistir(cagri.girdi))
        except (AracHatasi, KeyError, TypeError) as e:
            return AracSonucu(cagri.cagri_id, f"Hata: {e}", hata=True)
