"""Etkileşimli konsol arayüzü (istemci katmanı).

Arayüz kalıpların istemcisidir; somut sınıfları değil soyutlamaları kullanır:
  - Ürünü her zaman bir BilgisayarFabrikasi'ndan alır (standart ya da hazır paket),
  - donanımları DonanimKatalogu üzerinden (Decorator) ekler,
  - ödeme yöntemini IOdemeStratejisi olarak seçip SiparisIsleyici'ye verir,
  - sipariş aşamalarını Observer panelleri ekrana basar.
`girdi` ve `cikti` dışarıdan verilebildiği için arayüz otomatik test edilebilir.
"""
from __future__ import annotations

from typing import Callable

from .ai import DilModeliHatasi, DonanimOneriAsistani, IDilModeli, OneriHatasi, varsayilan_dil_modeli
from .fabrika import BilgisayarFabrikasi, HazirPaketFabrikasi, StandartSistemFabrikasi
from .katalog import DonanimKatalogu
from .odeme import HavaleOdemeStratejisi, IOdemeStratejisi, KrediKartiOdemeStratejisi
from .siparis import SiparisIsleyici
from .takip import MusteriBildirimPaneli, SiparisTakipMerkezi, TeknikServisPaneli
from .urunler import IBilgisayar


class _Cikis(Exception):
    """Kullanıcı girdiyi kapattığında (Ctrl+Z / Ctrl+D) menüden çıkmak için."""


class KonsolUygulamasi:
    TAKSIT_SECENEKLERI = ("1", "3", "6", "9", "12")

    def __init__(
        self,
        dil_modeli: IDilModeli | None = None,
        girdi: Callable[[str], str] = input,
        cikti: Callable[[str], None] = print,
    ) -> None:
        self._girdi = girdi
        self._cikti = cikti
        self._dil_modeli = dil_modeli
        self._katalog = DonanimKatalogu()
        self._standart_fabrika = StandartSistemFabrikasi()
        self._paket_fabrikasi = HazirPaketFabrikasi(self._standart_fabrika)
        self._takip = SiparisTakipMerkezi()
        self._siparisler: list = []

    # ------------------------------------------------------------------ akış

    def calistir(self) -> None:
        try:
            self._cikti("=== Modüler Bilgisayar Toplama ve Sipariş Sistemi ===")
            ad = self._sor("Adınız: ").strip() or "Misafir"
            self._takip.abone_ekle(MusteriBildirimPaneli(ad))
            self._takip.abone_ekle(TeknikServisPaneli())
            menu = {
                "1": ("Kendi sistemimi toplamak istiyorum", self._kendin_topla),
                "2": ("Hazır paketlerden seçmek istiyorum", self._paket_sec),
                "3": ("AI asistanından öneri almak istiyorum", self._ai_onerisi),
                "0": ("Çıkış", None),
            }
            while True:
                secim = self._secim_yap("\nNe yapmak istersiniz?", {k: v[0] for k, v in menu.items()})
                islem = menu[secim][1]
                if islem is None:
                    break
                bilgisayar = islem()
                if bilgisayar is not None:
                    self._siparis_ver(bilgisayar)
        except _Cikis:
            pass
        self._cikti(f"\nToplam {len(self._siparisler)} sipariş verildi. İyi günler!")

    def _kendin_topla(self) -> IBilgisayar:
        bilgisayar = self._fabrikadan_al(self._standart_fabrika, "Temel kasa seçin:")
        return self._donanim_ekle(bilgisayar)

    def _paket_sec(self) -> IBilgisayar:
        bilgisayar = self._fabrikadan_al(self._paket_fabrikasi, "Hazır paket seçin:")
        return self._donanim_ekle(bilgisayar)

    def _fabrikadan_al(self, fabrika: BilgisayarFabrikasi, baslik: str) -> IBilgisayar:
        """Factory Method istemcisi: hangi fabrika verilirse verilsin aynı akış."""
        secim = self._secim_yap(baslik, fabrika.secenekler())
        bilgisayar = fabrika.siparis_icin_hazirla(secim)
        self._cikti(f"Üretildi: {bilgisayar.aciklama()} (seri no: {fabrika.son_seri_no})")
        return bilgisayar

    def _donanim_ekle(self, bilgisayar: IBilgisayar) -> IBilgisayar:
        secenekler = {str(i): f"{d.aciklama} (+{d.fiyat:,.0f} TL)" for i, d in enumerate(self._katalog.tum_bilgiler(), 1)}
        kodlar = {str(i): kod for i, kod in enumerate(self._katalog.kodlar(), 1)}
        secenekler["0"] = "Bitti, siparişe geç"
        while True:
            self._cikti(f"\nMevcut sistem: {bilgisayar.aciklama()} — {bilgisayar.maliyet():,.2f} TL")
            secim = self._secim_yap("Ek donanım eklemek ister misiniz?", secenekler)
            if secim == "0":
                return bilgisayar
            bilgisayar = self._katalog.ekle(bilgisayar, kodlar[secim])

    def _ai_onerisi(self) -> IBilgisayar | None:
        model = self._dil_modeli_sec()
        istek = self._sor("İhtiyacınızı anlatın (ör. 'video kurgu ve oyun, sessiz olsun'): ")
        butce_metni = self._sor("Bütçeniz (TL, boş bırakılabilir): ").strip().replace(".", "").replace(",", "")
        butce = float(butce_metni) if butce_metni.isdigit() else None
        self._cikti("Asistan düşünüyor...")
        try:
            oneri = DonanimOneriAsistani(model, self._standart_fabrika, self._katalog).oner(istek, butce)
        except (OneriHatasi, DilModeliHatasi) as e:
            self._cikti(f"Öneri alınamadı: {e}")
            return None
        self._sistemi_goster(oneri.bilgisayar)
        self._cikti(f"Gerekçe: {oneri.gerekce}")
        onay = self._secim_yap("Bu sistemi sipariş etmek ister misiniz?", {"1": "Evet", "2": "Hayır, menüye dön"})
        return oneri.bilgisayar if onay == "1" else None

    def _dil_modeli_sec(self) -> IDilModeli:
        if self._dil_modeli is None:
            self._dil_modeli, aciklama = varsayilan_dil_modeli()
            self._cikti(f"({aciklama})")
        return self._dil_modeli

    def _odeme_sec(self) -> IOdemeStratejisi:
        """Strategy seçimi: kullanıcı seçer, Context yalnızca arayüzü görür."""
        yontemler: dict[str, tuple[str, Callable[[], IOdemeStratejisi]]] = {
            "1": ("Havale/EFT (%5 indirim)", lambda: HavaleOdemeStratejisi(0.05)),
            "2": ("Kredi kartı", self._kredi_karti_stratejisi),
        }
        secim = self._secim_yap("Ödeme yöntemi:", {k: v[0] for k, v in yontemler.items()})
        return yontemler[secim][1]()

    def _kredi_karti_stratejisi(self) -> IOdemeStratejisi:
        secenekler = {t: ("Tek çekim" if t == "1" else f"{t} taksit (aylık %2 vade farkı)") for t in self.TAKSIT_SECENEKLERI}
        return KrediKartiOdemeStratejisi(int(self._secim_yap("Taksit sayısı:", secenekler)))

    def _siparis_ver(self, bilgisayar: IBilgisayar) -> None:
        self._sistemi_goster(bilgisayar)
        isleyici = SiparisIsleyici(self._odeme_sec(), self._takip)
        siparis = isleyici.siparisi_tamamla(bilgisayar)
        o = siparis.odeme
        self._cikti(f"Ödenen ({o.yontem}): {o.odenen_tutar:,.2f} TL — {o.aciklama}")
        isleyici.montaj_surecini_yurut(siparis)
        self._siparisler.append(siparis)

    # --------------------------------------------------------------- yardımcılar

    def _sistemi_goster(self, bilgisayar: IBilgisayar) -> None:
        self._cikti(f"\n{bilgisayar.aciklama()}")
        for parca in bilgisayar.parca_listesi():
            self._cikti(f"  - {parca}")
        self._cikti(f"  Liste fiyatı: {bilgisayar.maliyet():,.2f} TL")

    def _sor(self, soru: str) -> str:
        try:
            return self._girdi(soru)
        except (EOFError, KeyboardInterrupt):
            raise _Cikis from None

    def _secim_yap(self, baslik: str, secenekler: dict[str, str]) -> str:
        self._cikti(baslik)
        for kod, aciklama in secenekler.items():
            self._cikti(f"  [{kod}] {aciklama}")
        while True:
            secim = self._sor("> ").strip().lower()
            if secim in secenekler:
                return secim
            self._cikti(f"Geçersiz seçim. Seçenekler: {', '.join(secenekler)}")
