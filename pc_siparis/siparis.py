"""Sipariş motoru: Strategy kalıbının Context rolü.

SiparisIsleyici; ödemeyi kendisine verilen IOdemeStratejisi'ne devreder
(Strategy) ve aşama değişikliklerini SiparisTakipMerkezi üzerinden yayınlar
(Observer). Hangi kasa/donanım olduğunu bilmez; yalnızca IBilgisayar ile çalışır.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass

from .odeme import IOdemeStratejisi, OdemeSonucu
from .takip import SiparisDurumu, SiparisTakipMerkezi
from .urunler import IBilgisayar
from .para import tl


@dataclass(frozen=True)
class Siparis:
    """Tamamlanmış bir siparişin özeti."""

    siparis_no: int
    urun_aciklamasi: str
    parcalar: tuple[str, ...]
    odeme: OdemeSonucu


# [Strategy: Context]
class SiparisIsleyici:
    """Siparişi tamamlar: ödeme (Strategy) + aşama bildirimleri (Observer)."""

    _no_sayaci = itertools.count(1001)

    def __init__(self, odeme_stratejisi: IOdemeStratejisi, takip_merkezi: SiparisTakipMerkezi) -> None:
        self._odeme_stratejisi = odeme_stratejisi
        self._takip_merkezi = takip_merkezi

    def odeme_stratejisi_degistir(self, strateji: IOdemeStratejisi) -> None:
        """Strateji çalışma anında değiştirilebilir."""
        self._odeme_stratejisi = strateji

    def siparisi_tamamla(self, bilgisayar: IBilgisayar) -> Siparis:
        siparis_no = next(self._no_sayaci)
        odeme = self._odeme_stratejisi.ode(bilgisayar.maliyet())
        siparis = Siparis(
            siparis_no=siparis_no,
            urun_aciklamasi=bilgisayar.aciklama(),
            parcalar=tuple(bilgisayar.parca_listesi()),
            odeme=odeme,
        )
        self._takip_merkezi.durum_guncelle(
            siparis_no, SiparisDurumu.ODEME_ALINDI, f"{odeme.yontem}: {tl(odeme.odenen_tutar, 2)}"
        )
        return siparis

    def montaj_surecini_yurut(self, siparis: Siparis) -> None:
        """Montaj → test → kargo aşamalarını sırayla yayınlar."""
        self._takip_merkezi.durum_guncelle(
            siparis.siparis_no, SiparisDurumu.MONTAJDA, f"{len(siparis.parcalar)} parça monte ediliyor"
        )
        self._takip_merkezi.durum_guncelle(
            siparis.siparis_no, SiparisDurumu.TESTTE, "Stres ve sıcaklık testleri"
        )
        self._takip_merkezi.durum_guncelle(siparis.siparis_no, SiparisDurumu.KARGODA)
