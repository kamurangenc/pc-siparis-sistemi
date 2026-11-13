"""Donanım öneri asistanı — Tool Use döngüsü (ReAct benzeri: düşün → araç çağır → gözlemle).

Asistan, müşterinin serbest metinle anlattığı ihtiyaca ve bütçesine göre
katalogdan bir sistem önerir. Önerilen sistem mevcut kalıplarla kurulur:
temel kasa Factory Method ile üretilir, donanımlar Decorator ile eklenir.
Dönen nesne sıradan bir IBilgisayar'dır; sipariş akışı (Strategy, Observer)
değişmeden çalışır.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..fabrika import BilgisayarFabrikasi, StandartSistemFabrikasi
from ..katalog import DonanimKatalogu
from ..urunler import IBilgisayar
from .araclar import AracYurutucu, FiyatHesaplaAraci, KatalogListeleAraci, OneriSunAraci
from .dil_modeli import AracSonucu, IDilModeli, Konusma
from .guardrail import CiktiDenetcisi, GirdiDenetcisi

SISTEM_TALIMATI = """\
Sen bir bilgisayar mağazasının donanım danışmanısın. Müşterinin ihtiyacına ve bütçesine \
uygun sistemi yalnızca mağaza kataloğundan seçersin.

Çalışma şeklin:
1. Önce katalog_listele aracıyla güncel kasaları ve donanımları öğren.
2. Aday kombinasyonların fiyatını fiyat_hesapla ile doğrula. Katalogda olmayan bir parça önerme.
3. Bütçe verilmişse toplam fiyat bütçeyi aşmamalı. Bütçe içinde ihtiyaca en uygun sistemi seç.
4. Kararını oneri_sun aracıyla teslim et; gerekçeyi Türkçe ve 1-2 cümle yaz.

Bilgisayar seçimi dışındaki konulara girme; böyle bir istekte en uygun temel sistemi öner \
ve gerekçede yalnızca donanım danışmanlığı yaptığını belirt."""


class OneriHatasi(Exception):
    """Asistan geçerli bir öneri üretemediğinde."""


@dataclass(frozen=True)
class OneriSonucu:
    bilgisayar: IBilgisayar
    gerekce: str
    adim_sayisi: int


class DonanimOneriAsistani:
    MAKS_ADIM = 8

    def __init__(
        self,
        model: IDilModeli,
        fabrika: BilgisayarFabrikasi | None = None,
        katalog: DonanimKatalogu | None = None,
    ) -> None:
        self._model = model
        self._fabrika = fabrika or StandartSistemFabrikasi()
        self._katalog = katalog or DonanimKatalogu()
        self._girdi_denetcisi = GirdiDenetcisi()
        self._cikti_denetcisi = CiktiDenetcisi()

    def oner(self, istek: str, butce: float | None = None) -> OneriSonucu:
        denetim = self._girdi_denetcisi.denetle(istek, butce)
        if not denetim.gecti:
            raise OneriHatasi(denetim.neden)

        oneri_araci = OneriSunAraci(self._fabrika, self._katalog)
        yurutucu = AracYurutucu([
            KatalogListeleAraci(self._fabrika, self._katalog),
            FiyatHesaplaAraci(self._fabrika, self._katalog, butce),
            oneri_araci,
        ])
        mesaj = istek.strip() + (f"\n\nBütçem: {butce:,.0f} TL" if butce else "\n\nBütçe belirtilmedi.")
        konusma = Konusma(kullanici_mesaji=mesaj)

        for adim in range(1, self.MAKS_ADIM + 1):
            yanit = self._model.yanit_uret(SISTEM_TALIMATI, konusma, yurutucu.tanimlar())
            if yanit.reddedildi:
                raise OneriHatasi("Model bu isteği yanıtlamayı reddetti.")
            if not yanit.arac_cagrilari:
                raise OneriHatasi("Model bir öneri teslim etmeden durdu." + (f" Yanıt: {yanit.metin}" if yanit.metin else ""))

            sonuclar: list[AracSonucu] = []
            for cagri in yanit.arac_cagrilari:
                sonuc = yurutucu.yurut(cagri)
                if cagri.ad == OneriSunAraci.ad and not sonuc.hata:
                    sonuc = self._oneriyi_denetle(oneri_araci, sonuc, butce)
                sonuclar.append(sonuc)
            konusma.adimlar.append((yanit, sonuclar))

            if oneri_araci.son_oneri is not None:
                bilgisayar, gerekce = oneri_araci.son_oneri
                return OneriSonucu(bilgisayar, gerekce, adim)

        raise OneriHatasi(f"{self.MAKS_ADIM} adımda geçerli bir öneri üretilemedi.")

    def _oneriyi_denetle(self, oneri_araci: OneriSunAraci, sonuc: AracSonucu, butce: float | None) -> AracSonucu:
        """Çıktı guardrail'i: geçmezse öneri silinir, model düzeltmeye yönlendirilir."""
        bilgisayar, _ = oneri_araci.son_oneri
        denetim = self._cikti_denetcisi.denetle(bilgisayar, butce)
        if denetim.gecti:
            return sonuc
        oneri_araci.son_oneri = None
        return AracSonucu(sonuc.cagri_id, f"Öneri reddedildi: {denetim.neden}", hata=True)
