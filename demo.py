"""Komut dosyası demo: dört kalıbın birlikte çalıştığı uçtan uca sipariş senaryosu.

Çalıştırma:  python demo.py
"""
from pc_siparis import (
    BilgisayarFabrikasi,
    EkSsdDecorator,
    HavaleOdemeStratejisi,
    IBilgisayar,
    KrediKartiOdemeStratejisi,
    MusteriBildirimPaneli,
    RamYukseltmeDecorator,
    Siparis,
    SiparisIsleyici,
    SiparisTakipMerkezi,
    SiviSogutmaDecorator,
    StandartSistemFabrikasi,
    TeknikServisPaneli,
)
from pc_siparis.para import tl


def siparis_ozeti_yazdir(siparis: Siparis) -> None:
    print(f"\n  Sipariş #{siparis.siparis_no}: {siparis.urun_aciklamasi}")
    for parca in siparis.parcalar:
        print(f"    - {parca}")
    o = siparis.odeme
    print(f"  Liste fiyatı : {tl(o.liste_fiyati, 2)}")
    print(f"  Ödenen ({o.yontem}): {tl(o.odenen_tutar, 2)}  ({o.aciklama})\n")


def main() -> None:
    # Observer: takip merkezi ve gözlemciler
    takip = SiparisTakipMerkezi()
    takip.abone_ekle(MusteriBildirimPaneli("Ayşe Yılmaz"))
    takip.abone_ekle(TeknikServisPaneli())

    # Factory Method: istemci yalnızca soyut Creator'ı tanır
    fabrika: BilgisayarFabrikasi = StandartSistemFabrikasi()

    print("=== Senaryo 1: Oyun kasası + RAM + sıvı soğutma, havale ile ===")
    pc: IBilgisayar = fabrika.siparis_icin_hazirla("oyun")
    print(f"[Fabrika] {pc.aciklama()} üretildi (seri no: {fabrika.son_seri_no})")
    # Decorator: donanımlar çalışma anında sarmalanır
    pc = SiviSogutmaDecorator(RamYukseltmeDecorator(pc))

    # Strategy: ödeme algoritması dışarıdan verilir
    isleyici = SiparisIsleyici(HavaleOdemeStratejisi(indirim_orani=0.05), takip)
    siparis = isleyici.siparisi_tamamla(pc)
    siparis_ozeti_yazdir(siparis)
    isleyici.montaj_surecini_yurut(siparis)

    print("\n=== Senaryo 2: Ofis kasası + ek SSD, kredi kartı 6 taksit ===")
    pc = EkSsdDecorator(fabrika.siparis_icin_hazirla("ofis"))
    isleyici.odeme_stratejisi_degistir(KrediKartiOdemeStratejisi(taksit_sayisi=6))
    siparis = isleyici.siparisi_tamamla(pc)
    siparis_ozeti_yazdir(siparis)
    isleyici.montaj_surecini_yurut(siparis)


if __name__ == "__main__":
    main()
