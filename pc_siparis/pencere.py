"""Pencere arayüzü (tkinter) — kalıpların ikinci istemcisi.

Konsol arayüzüyle aynı soyutlamaları kullanır; çekirdek sınıflarda hiçbir
değişiklik yapılmadan eklenmiştir:
  - Ürün her zaman bir BilgisayarFabrikasi'ndan alınır (Factory Method),
  - donanımlar DonanimKatalogu ile sarmalanır (Decorator),
  - ödeme IOdemeStratejisi olarak seçilir (Strategy),
  - sipariş aşamalarını yeni pencere panelleri gösterir (Observer: yeni ConcreteObserver'lar),
  - AI sekmesi DonanimOneriAsistani'nı kullanır (Adapter, Command, Tool Use, Guardrail).
"""
from __future__ import annotations

import queue
import threading
import tkinter as tk
from tkinter import ttk
from typing import Callable

from .ai import DilModeliHatasi, DonanimOneriAsistani, IDilModeli, OneriHatasi, varsayilan_dil_modeli
from .fabrika import BilgisayarFabrikasi, HazirPaketFabrikasi, StandartSistemFabrikasi
from .katalog import DonanimKatalogu
from .odeme import HavaleOdemeStratejisi, IOdemeStratejisi, KrediKartiOdemeStratejisi
from .siparis import SiparisIsleyici
from .takip import ISiparisGozlemcisi, SiparisDurumu, SiparisTakipMerkezi
from .urunler import IBilgisayar

RENK_ARKA = "#F4F6FA"
RENK_VURGU = "#1F3864"
RENK_BASARI = "#2E7D32"
RENK_HATA = "#C62828"
RENK_PASIF = "#B0B7C3"
YAZI = ("Segoe UI", 10)
YAZI_KALIN = ("Segoe UI", 10, "bold")
YAZI_BASLIK = ("Segoe UI", 15, "bold")


def _tl(tutar: float) -> str:
    return f"{tutar:,.2f} TL".replace(",", "X").replace(".", ",").replace("X", ".")


# --------------------------------------------------------------------------- Observer

class _MetinPaneli(ISiparisGozlemcisi):
    """Bildirimleri salt okunur bir Text bileşenine yazan ortak taban."""

    def __init__(self, metin: tk.Text) -> None:
        self._metin = metin
        self.kayitlar: list[str] = []

    def _yaz(self, satir: str) -> None:
        self.kayitlar.append(satir)
        self._metin.configure(state="normal")
        self._metin.insert("end", satir + "\n")
        self._metin.see("end")
        self._metin.configure(state="disabled")


# [Observer: ConcreteObserver]
class PencereMusteriPaneli(_MetinPaneli):
    def __init__(self, metin: tk.Text, ad_getir: Callable[[], str]) -> None:
        super().__init__(metin)
        self._ad_getir = ad_getir

    def guncelle(self, siparis_no: int, durum: SiparisDurumu, detay: str) -> None:
        self._yaz(f"Sayın {self._ad_getir()}, #{siparis_no} numaralı siparişiniz: {durum.value}")


# [Observer: ConcreteObserver]
class PencereTeknikServisPaneli(_MetinPaneli):
    ILGILI_DURUMLAR = {SiparisDurumu.MONTAJDA, SiparisDurumu.TESTTE}

    def guncelle(self, siparis_no: int, durum: SiparisDurumu, detay: str) -> None:
        if durum in self.ILGILI_DURUMLAR:
            self._yaz(f"#{siparis_no} → {durum.name}" + (f" | {detay}" if detay else ""))


# [Observer: ConcreteObserver]
class SiparisDurumGostergesi(ISiparisGozlemcisi):
    """Aşama göstergesi: ulaşılan aşamaları yeşile boyar."""

    def __init__(self, etiketler: dict[SiparisDurumu, tk.Label]) -> None:
        self._etiketler = etiketler
        self.son_durum: SiparisDurumu | None = None

    def sifirla(self) -> None:
        self.son_durum = None
        for etiket in self._etiketler.values():
            etiket.configure(bg=RENK_PASIF)

    def guncelle(self, siparis_no: int, durum: SiparisDurumu, detay: str) -> None:
        if durum == SiparisDurumu.ODEME_ALINDI:
            self.sifirla()
        self.son_durum = durum
        self._etiketler[durum].configure(bg=RENK_BASARI)


# --------------------------------------------------------------------------- Uygulama

class PencereUygulamasi:
    TAKSITLER = ("1", "3", "6", "9", "12")

    def __init__(self, kok: tk.Tk, dil_modeli: IDilModeli | None = None, senkron: bool = False) -> None:
        self.kok = kok
        self._dil_modeli = dil_modeli
        self._senkron = senkron  # testlerde AI çağrısı iş parçacığı olmadan yürütülür
        self._katalog = DonanimKatalogu()
        self._fabrikalar: dict[str, BilgisayarFabrikasi] = {}
        self._fabrikalar["standart"] = StandartSistemFabrikasi()
        self._fabrikalar["paket"] = HazirPaketFabrikasi(self._fabrikalar["standart"])
        self._takip = SiparisTakipMerkezi()
        self._temel: IBilgisayar | None = None
        self._bilgisayar: IBilgisayar | None = None
        self._kuyruk: queue.Queue = queue.Queue()
        self.siparisler: list = []

        kok.title("Modüler Bilgisayar Toplama ve Sipariş Sistemi")
        kok.geometry("1240x740")
        kok.minsize(1100, 660)
        kok.configure(bg=RENK_ARKA)
        self._stil_kur()
        self._arayuzu_kur()

        self.musteri_paneli = PencereMusteriPaneli(self._musteri_metni, lambda: self.ad_var.get().strip() or "Müşteri")
        self.servis_paneli = PencereTeknikServisPaneli(self._servis_metni)
        self.durum_gostergesi = SiparisDurumGostergesi(self._asama_etiketleri)
        for gozlemci in (self.musteri_paneli, self.servis_paneli, self.durum_gostergesi):
            self._takip.abone_ekle(gozlemci)
        self._odeme_onizle()

    # ----------------------------------------------------------- kurulum

    def _stil_kur(self) -> None:
        stil = ttk.Style(self.kok)
        stil.theme_use("clam")
        stil.configure(".", font=YAZI, background=RENK_ARKA)
        stil.configure("TLabelframe", background=RENK_ARKA)
        stil.configure("TLabelframe.Label", font=YAZI_KALIN, foreground=RENK_VURGU, background=RENK_ARKA)
        stil.configure("TNotebook.Tab", font=YAZI_KALIN, padding=(12, 4))
        stil.configure("Vurgu.TButton", font=YAZI_KALIN, foreground="white", background=RENK_VURGU, padding=8)
        stil.map("Vurgu.TButton", background=[("active", "#2B4C86"), ("disabled", RENK_PASIF)])
        stil.configure("Fiyat.TLabel", font=("Segoe UI", 13, "bold"), foreground=RENK_VURGU)

    def _arayuzu_kur(self) -> None:
        ust = tk.Frame(self.kok, bg=RENK_VURGU)
        ust.pack(fill="x")
        tk.Label(ust, text="Modüler Bilgisayar Toplama ve Sipariş Sistemi", font=YAZI_BASLIK,
                 fg="white", bg=RENK_VURGU).pack(side="left", padx=16, pady=10)
        self.ad_var = tk.StringVar(value="")
        tk.Entry(ust, textvariable=self.ad_var, font=YAZI, width=22).pack(side="right", padx=(4, 16))
        tk.Label(ust, text="Müşteri adı:", font=YAZI, fg="white", bg=RENK_VURGU).pack(side="right")

        govde = ttk.Frame(self.kok, padding=12)
        govde.pack(fill="both", expand=True)
        for i, agirlik in enumerate((4, 4, 5)):
            govde.columnconfigure(i, weight=agirlik, uniform="sutun")
        govde.rowconfigure(0, weight=1)

        self._urun_sutunu(govde).grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self._sistem_sutunu(govde).grid(row=0, column=1, sticky="nsew", padx=8)
        self._takip_sutunu(govde).grid(row=0, column=2, sticky="nsew", padx=(8, 0))

        self.durum_var = tk.StringVar(value="Bir kasa, hazır paket seçin ya da AI asistanından öneri alın.")
        self._durum_cubugu = tk.Label(self.kok, textvariable=self.durum_var, anchor="w", font=YAZI,
                                      bg="#E3E8F0", fg="#333", padx=12, pady=6)
        self._durum_cubugu.pack(fill="x", side="bottom")

    def _urun_sutunu(self, ebeveyn) -> ttk.Frame:
        cerceve = ttk.LabelFrame(ebeveyn, text="1. Ürün Seçimi", padding=8)
        defter = ttk.Notebook(cerceve)
        defter.pack(fill="both", expand=True)
        self._secim_vars: dict[str, tk.StringVar] = {}
        for tur, baslik in (("standart", "Temel Kasa"), ("paket", "Hazır Paket")):
            defter.add(self._fabrika_sekmesi(defter, tur), text=baslik)
        defter.add(self._ai_sekmesi(defter), text="AI Asistanı")
        return cerceve

    def _fabrika_sekmesi(self, ebeveyn, tur: str) -> ttk.Frame:
        """Factory Method istemcisi: her fabrika için aynı sekme kodu çalışır."""
        sekme = ttk.Frame(ebeveyn, padding=10)
        fabrika = self._fabrikalar[tur]
        secenekler = fabrika.secenekler()
        var = tk.StringVar(value=next(iter(secenekler)))
        self._secim_vars[tur] = var
        for kod, aciklama in secenekler.items():
            ttk.Radiobutton(sekme, text=aciklama, value=kod, variable=var).pack(anchor="w", pady=4)
        ttk.Button(sekme, text="Seç ve Üret", style="Vurgu.TButton",
                   command=lambda: self.kaynak_sec(tur, var.get())).pack(anchor="w", pady=(12, 0))
        return sekme

    def _ai_sekmesi(self, ebeveyn) -> ttk.Frame:
        sekme = ttk.Frame(ebeveyn, padding=10)
        ttk.Label(sekme, text="İhtiyacınızı anlatın:").pack(anchor="w")
        self._istek_metni = tk.Text(sekme, height=5, wrap="word", font=YAZI, relief="solid", bd=1)
        self._istek_metni.insert("1.0", "Video kurgu yapıp oyun oynayacağım, sessiz olsun.")
        self._istek_metni.pack(fill="x", pady=(2, 8))
        satir = ttk.Frame(sekme)
        satir.pack(fill="x")
        ttk.Label(satir, text="Bütçe (TL):").pack(side="left")
        self.butce_var = tk.StringVar(value="50000")
        ttk.Entry(satir, textvariable=self.butce_var, width=12).pack(side="left", padx=6)
        self._ai_dugmesi = ttk.Button(sekme, text="Öneri Al", style="Vurgu.TButton",
                                      command=self._ai_dugmesine_basildi)
        self._ai_dugmesi.pack(anchor="w", pady=10)
        self.gerekce_var = tk.StringVar(value="")
        ttk.Label(sekme, textvariable=self.gerekce_var, wraplength=330, foreground="#444").pack(anchor="w")
        self.model_var = tk.StringVar(value="Model, ilk öneride seçilir.")
        ttk.Label(sekme, textvariable=self.model_var, wraplength=330, foreground="#777",
                  font=("Segoe UI", 9, "italic")).pack(anchor="w", side="bottom")
        return sekme

    def _sistem_sutunu(self, ebeveyn) -> ttk.Frame:
        cerceve = ttk.Frame(ebeveyn)
        sistem = ttk.LabelFrame(cerceve, text="2. Sistem ve Ek Donanım", padding=8)
        sistem.pack(fill="both", expand=True)
        self.aciklama_var = tk.StringVar(value="Henüz ürün seçilmedi")
        ttk.Label(sistem, textvariable=self.aciklama_var, font=YAZI_KALIN, wraplength=330).pack(anchor="w")
        self._parca_listesi = tk.Listbox(sistem, height=8, font=YAZI, relief="solid", bd=1, activestyle="none")
        self._parca_listesi.pack(fill="both", expand=True, pady=6)
        self.fiyat_var = tk.StringVar(value="Liste fiyatı: —")
        ttk.Label(sistem, textvariable=self.fiyat_var, style="Fiyat.TLabel").pack(anchor="w", pady=(0, 6))
        for bilgi in self._katalog.tum_bilgiler():
            ttk.Button(sistem, text=f"+ {bilgi.aciklama}  ({_tl(bilgi.fiyat)})",
                       command=lambda k=bilgi.kod: self.donanim_ekle(k)).pack(fill="x", pady=2)
        ttk.Button(sistem, text="Ek donanımları kaldır", command=self.donanimlari_sifirla).pack(fill="x", pady=(6, 0))

        odeme = ttk.LabelFrame(cerceve, text="3. Ödeme", padding=8)
        odeme.pack(fill="x", pady=(10, 0))
        self.yontem_var = tk.StringVar(value="havale")
        self.taksit_var = tk.StringVar(value="1")
        ttk.Radiobutton(odeme, text="Havale / EFT (%5 indirim)", value="havale", variable=self.yontem_var,
                        command=self._odeme_onizle).pack(anchor="w")
        kart = ttk.Frame(odeme)
        kart.pack(anchor="w", fill="x")
        ttk.Radiobutton(kart, text="Kredi kartı — taksit:", value="kart", variable=self.yontem_var,
                        command=self._odeme_onizle).pack(side="left")
        self._taksit_kutusu = ttk.Combobox(kart, textvariable=self.taksit_var, values=self.TAKSITLER,
                                           width=4, state="readonly")
        self._taksit_kutusu.pack(side="left", padx=6)
        self._taksit_kutusu.bind("<<ComboboxSelected>>", lambda _e: self._odeme_onizle())
        self.odenecek_var = tk.StringVar(value="")
        ttk.Label(odeme, textvariable=self.odenecek_var, font=YAZI_KALIN).pack(anchor="w", pady=6)
        ttk.Button(odeme, text="Siparişi Tamamla", style="Vurgu.TButton",
                   command=self.siparisi_tamamla).pack(fill="x")
        return cerceve

    def _takip_sutunu(self, ebeveyn) -> ttk.Frame:
        cerceve = ttk.LabelFrame(ebeveyn, text="4. Sipariş Takibi", padding=8)
        asamalar = tk.Frame(cerceve, bg=RENK_ARKA)
        asamalar.pack(fill="x", pady=(0, 8))
        self._asama_etiketleri: dict[SiparisDurumu, tk.Label] = {}
        for i, (durum, ad) in enumerate(zip(SiparisDurumu, ("Ödeme", "Montaj", "Test", "Kargo"))):
            asamalar.columnconfigure(i, weight=1)
            etiket = tk.Label(asamalar, text=ad, font=YAZI_KALIN, fg="white", bg=RENK_PASIF, pady=6)
            etiket.grid(row=0, column=i, sticky="ew", padx=2)
            self._asama_etiketleri[durum] = etiket

        def metin_kutusu(baslik: str) -> tk.Text:
            ttk.Label(cerceve, text=baslik, font=YAZI_KALIN, foreground=RENK_VURGU).pack(anchor="w", pady=(6, 2))
            metin = tk.Text(cerceve, height=8, wrap="word", font=("Segoe UI", 9), relief="solid", bd=1,
                            state="disabled", bg="white")
            metin.pack(fill="both", expand=True)
            return metin

        self._musteri_metni = metin_kutusu("Müşteri Bildirimleri")
        self._servis_metni = metin_kutusu("Teknik Servis Paneli")
        self.siparis_sayisi_var = tk.StringVar(value="Verilen sipariş: 0")
        ttk.Label(cerceve, textvariable=self.siparis_sayisi_var, font=YAZI_KALIN).pack(anchor="e", pady=(6, 0))
        return cerceve

    # ----------------------------------------------------------- işlemler

    def kaynak_sec(self, tur: str, kod: str) -> None:
        fabrika = self._fabrikalar[tur]
        bilgisayar = fabrika.siparis_icin_hazirla(kod)
        self._sistemi_ayarla(bilgisayar, temel=True)
        self._durum(f"Üretildi: {bilgisayar.aciklama()} (seri no: {fabrika.son_seri_no})")

    def donanim_ekle(self, kod: str) -> None:
        if self._bilgisayar is None:
            return self._durum("Önce bir kasa veya paket seçin.", hata=True)
        self._sistemi_ayarla(self._katalog.ekle(self._bilgisayar, kod))
        self._durum(f"Eklendi: {self._katalog.bilgi(kod).aciklama}")

    def donanimlari_sifirla(self) -> None:
        if self._temel is not None:
            self._sistemi_ayarla(self._temel)
            self._durum("Ek donanımlar kaldırıldı.")

    def odeme_ayarla(self, yontem: str, taksit: int = 1) -> None:
        self.yontem_var.set(yontem)
        self.taksit_var.set(str(taksit))
        self._odeme_onizle()

    def odeme_stratejisi(self) -> IOdemeStratejisi:
        """Strategy seçimi: Context (SiparisIsleyici) yalnızca arayüzü görür."""
        stratejiler: dict[str, Callable[[], IOdemeStratejisi]] = {
            "havale": lambda: HavaleOdemeStratejisi(0.05),
            "kart": lambda: KrediKartiOdemeStratejisi(int(self.taksit_var.get())),
        }
        return stratejiler[self.yontem_var.get()]()

    def siparisi_tamamla(self) -> None:
        if self._bilgisayar is None:
            return self._durum("Sipariş için önce bir sistem seçin.", hata=True)
        isleyici = SiparisIsleyici(self.odeme_stratejisi(), self._takip)
        siparis = isleyici.siparisi_tamamla(self._bilgisayar)
        isleyici.montaj_surecini_yurut(siparis)
        self.siparisler.append(siparis)
        self.siparis_sayisi_var.set(f"Verilen sipariş: {len(self.siparisler)}")
        o = siparis.odeme
        self._durum(f"Sipariş #{siparis.siparis_no} tamamlandı — {o.yontem}: {_tl(o.odenen_tutar)} ({o.aciklama})")

    def ai_oneri_al(self, istek: str, butce: float | None) -> None:
        if self._dil_modeli is None:
            self._dil_modeli, aciklama = varsayilan_dil_modeli()
            self.model_var.set(aciklama)
        asistan = DonanimOneriAsistani(self._dil_modeli, self._fabrikalar["standart"], self._katalog)
        self._ai_dugmesi.configure(state="disabled")
        self._durum("Asistan düşünüyor...")

        def calis() -> None:
            try:
                self._kuyruk.put(("tamam", asistan.oner(istek, butce)))
            except (OneriHatasi, DilModeliHatasi) as e:
                self._kuyruk.put(("hata", str(e)))
            except Exception as e:  # pencere hiçbir hatada "düşünüyor" durumunda takılı kalmamalı
                self._kuyruk.put(("hata", f"Beklenmeyen hata ({type(e).__name__}): {e}"))

        if self._senkron:
            calis()
            self._kuyrugu_isle()
        else:
            threading.Thread(target=calis, daemon=True).start()
            self.kok.after(100, self._kuyrugu_isle)

    # ----------------------------------------------------------- yardımcılar

    def _ai_dugmesine_basildi(self) -> None:
        metin = self.butce_var.get().strip().replace(".", "").replace(",", "")
        butce = float(metin) if metin.isdigit() else None
        self.ai_oneri_al(self._istek_metni.get("1.0", "end").strip(), butce)

    def _kuyrugu_isle(self) -> None:
        """İş parçacığından gelen sonucu ana iş parçacığında arayüze uygular (tkinter iş parçacığı güvenli değildir)."""
        try:
            tur, veri = self._kuyruk.get_nowait()
        except queue.Empty:
            self.kok.after(100, self._kuyrugu_isle)
            return
        self._ai_dugmesi.configure(state="normal")
        if tur == "hata":
            self.gerekce_var.set("")
            self._durum(f"Öneri alınamadı: {veri}", hata=True)
            return
        self._sistemi_ayarla(veri.bilgisayar, temel=True)
        self.gerekce_var.set(f"Gerekçe: {veri.gerekce}")
        self._durum(f"Asistan önerisi hazır ({veri.adim_sayisi} adım). İsterseniz donanım ekleyip sipariş verin.")

    def _sistemi_ayarla(self, bilgisayar: IBilgisayar, temel: bool = False) -> None:
        if temel:
            self._temel = bilgisayar
        self._bilgisayar = bilgisayar
        self.aciklama_var.set(bilgisayar.aciklama())
        self._parca_listesi.delete(0, "end")
        for parca in bilgisayar.parca_listesi():
            self._parca_listesi.insert("end", f"  {parca}")
        self.fiyat_var.set(f"Liste fiyatı: {_tl(bilgisayar.maliyet())}")
        self._odeme_onizle()

    def _odeme_onizle(self) -> None:
        self._taksit_kutusu.configure(state="readonly" if self.yontem_var.get() == "kart" else "disabled")
        if self._bilgisayar is None:
            self.odenecek_var.set("Ödenecek tutar: —")
            return
        tutar = self.odeme_stratejisi().odeme_tutari_hesapla(self._bilgisayar.maliyet())
        self.odenecek_var.set(f"Ödenecek tutar: {_tl(tutar)}")

    def _durum(self, mesaj: str, hata: bool = False) -> None:
        self.durum_var.set(mesaj)
        self._durum_cubugu.configure(fg=RENK_HATA if hata else "#333")


def calistir() -> None:
    kok = tk.Tk()
    PencereUygulamasi(kok)
    kok.mainloop()
