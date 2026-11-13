"""Otomatik testler (unittest; pytest ile de çalışır).

Çalıştırma:  python -m unittest discover -s tests -v
"""
import io
import unittest
from contextlib import redirect_stdout

from pc_siparis import (
    BilgisayarFabrikasi,
    DonanimDecorator,
    DonanimKatalogu,
    HazirPaketFabrikasi,
    UretimHatasi,
    EkSsdDecorator,
    HavaleOdemeStratejisi,
    IBilgisayar,
    IOdemeStratejisi,
    ISiparisGozlemcisi,
    KrediKartiOdemeStratejisi,
    MusteriBildirimPaneli,
    OfisKasasi,
    OyunKasasi,
    RamYukseltmeDecorator,
    SiparisDurumu,
    SiparisIsleyici,
    SiparisTakipMerkezi,
    SiviSogutmaDecorator,
    StandartSistemFabrikasi,
    TeknikServisPaneli,
)


def sessiz(fn, *args, **kwargs):
    """Demo çıktılarını test çıktısından gizler."""
    with redirect_stdout(io.StringIO()):
        return fn(*args, **kwargs)


class ArayuzTestleri(unittest.TestCase):
    def test_arayuzler_dogrudan_orneklenemez(self):
        for arayuz in (IBilgisayar, BilgisayarFabrikasi, IOdemeStratejisi, ISiparisGozlemcisi):
            with self.subTest(arayuz=arayuz.__name__):
                with self.assertRaises(TypeError):
                    arayuz()


class FactoryMethodTestleri(unittest.TestCase):
    def setUp(self):
        self.fabrika = StandartSistemFabrikasi()

    def test_kullanim_amacina_gore_dogru_kasa_uretilir(self):
        self.assertIsInstance(self.fabrika.bilgisayar_olustur("ofis"), OfisKasasi)
        self.assertIsInstance(self.fabrika.bilgisayar_olustur("OYUN"), OyunKasasi)

    def test_bilinmeyen_tip_hata_verir(self):
        with self.assertRaises(ValueError):
            self.fabrika.bilgisayar_olustur("sunucu")

    def test_ortak_surec_seri_no_verir(self):
        self.fabrika.siparis_icin_hazirla("ofis")
        self.fabrika.siparis_icin_hazirla("oyun")
        self.assertEqual(self.fabrika.son_seri_no, "STD-0002")

    def test_kalite_kontrol_hatali_urunu_reddeder(self):
        class FiyatsizKasa(OfisKasasi):
            def maliyet(self):
                return 0

        self.fabrika.kasa_kaydet("bozuk", FiyatsizKasa)
        with self.assertRaises(UretimHatasi):
            self.fabrika.siparis_icin_hazirla("bozuk")

    def test_hazir_paket_fabrikasi_dekore_edilmis_urun_uretir(self):
        paket = HazirPaketFabrikasi().siparis_icin_hazirla("yayinci")
        self.assertIsInstance(paket, IBilgisayar)
        self.assertEqual(paket.maliyet(), 40_000 + 2_500 + 4_000)
        self.assertIn("Sıvı Soğutma", paket.aciklama())

    def test_istemci_her_fabrikayla_ayni_akisi_kullanir(self):
        # Polimorfizm: istemci yalnızca soyut Creator'ı bilir.
        for fabrika in (StandartSistemFabrikasi(), HazirPaketFabrikasi()):
            with self.subTest(fabrika=type(fabrika).__name__):
                for kod in fabrika.secenekler():
                    self.assertIsInstance(fabrika.siparis_icin_hazirla(kod), IBilgisayar)

    def test_yeni_model_mevcut_kod_degismeden_eklenir(self):
        class IsIstasyonu(OfisKasasi):
            def aciklama(self):
                return "İş İstasyonu"

        self.fabrika.kasa_kaydet("istasyon", IsIstasyonu)
        pc = sessiz(self.fabrika.siparis_icin_hazirla, "istasyon")
        self.assertEqual(pc.aciklama(), "İş İstasyonu")


class DecoratorTestleri(unittest.TestCase):
    def test_tek_dekorator_fiyat_ve_parca_ekler(self):
        pc = RamYukseltmeDecorator(OfisKasasi())
        self.assertEqual(pc.maliyet(), 15_000 + 2_500)
        self.assertIn("Ek RAM: 16 GB DDR5", pc.parca_listesi())
        self.assertEqual(len(pc.parca_listesi()), len(OfisKasasi().parca_listesi()) + 1)

    def test_dekoratorler_ic_ice_sarmalanabilir(self):
        pc = EkSsdDecorator(SiviSogutmaDecorator(RamYukseltmeDecorator(OyunKasasi())))
        self.assertEqual(pc.maliyet(), 40_000 + 2_500 + 4_000 + 3_000)
        self.assertEqual(pc.aciklama(), "Oyun Kasası + 16 GB Ek RAM + Sıvı Soğutma + 1 TB Ek SSD")
        self.assertIsInstance(pc, IBilgisayar)

    def test_ayni_dekorator_birden_fazla_kez_eklenebilir(self):
        pc = RamYukseltmeDecorator(RamYukseltmeDecorator(OfisKasasi()))
        self.assertEqual(pc.maliyet(), 15_000 + 2 * 2_500)

    def test_dekorator_soyut_siniftir(self):
        self.assertTrue(issubclass(DonanimDecorator, IBilgisayar))


class KatalogTestleri(unittest.TestCase):
    def test_katalog_kod_ile_dekorator_ekler(self):
        katalog = DonanimKatalogu()
        pc = katalog.ekle(katalog.ekle(OfisKasasi(), "ram"), "ek_ssd")
        self.assertEqual(pc.maliyet(), 15_000 + 2_500 + 3_000)

    def test_bilinmeyen_donanim_hata_verir(self):
        with self.assertRaises(ValueError):
            DonanimKatalogu().ekle(OfisKasasi(), "rgb_fan")


class StrategyTestleri(unittest.TestCase):
    def test_havale_indirim_uygular(self):
        self.assertEqual(HavaleOdemeStratejisi(0.05).odeme_tutari_hesapla(10_000), 9_500)

    def test_kredi_karti_tek_cekim_vade_farksiz(self):
        self.assertEqual(KrediKartiOdemeStratejisi(1).odeme_tutari_hesapla(10_000), 10_000)

    def test_kredi_karti_taksitte_vade_farki(self):
        # 6 taksit -> 5 ek ay x %2 = %10
        self.assertEqual(KrediKartiOdemeStratejisi(6, 0.02).odeme_tutari_hesapla(10_000), 11_000)

    def test_gecersiz_parametreler(self):
        with self.assertRaises(ValueError):
            HavaleOdemeStratejisi(1.5)
        with self.assertRaises(ValueError):
            KrediKartiOdemeStratejisi(0)

    def test_context_stratejiyi_calisma_aninda_degistirir(self):
        isleyici = SiparisIsleyici(HavaleOdemeStratejisi(0.10), SiparisTakipMerkezi())
        s1 = sessiz(isleyici.siparisi_tamamla, OfisKasasi())
        isleyici.odeme_stratejisi_degistir(KrediKartiOdemeStratejisi(1))
        s2 = sessiz(isleyici.siparisi_tamamla, OfisKasasi())
        self.assertEqual(s1.odeme.odenen_tutar, 13_500)
        self.assertEqual(s2.odeme.odenen_tutar, 15_000)
        self.assertNotEqual(s1.siparis_no, s2.siparis_no)


class KayitciGozlemci(ISiparisGozlemcisi):
    def __init__(self):
        self.olaylar = []

    def guncelle(self, siparis_no, durum, detay):
        self.olaylar.append((siparis_no, durum))


class ObserverTestleri(unittest.TestCase):
    def setUp(self):
        self.takip = SiparisTakipMerkezi()
        self.kayitci = KayitciGozlemci()
        self.takip.abone_ekle(self.kayitci)

    def test_tum_asamalar_sirayla_bildirilir(self):
        isleyici = SiparisIsleyici(HavaleOdemeStratejisi(), self.takip)
        siparis = sessiz(isleyici.siparisi_tamamla, OyunKasasi())
        sessiz(isleyici.montaj_surecini_yurut, siparis)
        self.assertEqual([d for _, d in self.kayitci.olaylar], list(SiparisDurumu))
        self.assertEqual(self.takip.durum_getir(siparis.siparis_no), SiparisDurumu.KARGODA)

    def test_abonelikten_cikan_bildirim_almaz(self):
        self.takip.abone_cikar(self.kayitci)
        sessiz(self.takip.durum_guncelle, 1, SiparisDurumu.MONTAJDA)
        self.assertEqual(self.kayitci.olaylar, [])

    def test_ayni_gozlemci_iki_kez_eklenmez(self):
        self.takip.abone_ekle(self.kayitci)
        sessiz(self.takip.durum_guncelle, 1, SiparisDurumu.MONTAJDA)
        self.assertEqual(len(self.kayitci.olaylar), 1)

    def test_teknik_servis_yalniz_ilgili_asamalari_kaydeder(self):
        servis, musteri = TeknikServisPaneli(), MusteriBildirimPaneli("Test")
        self.takip.abone_ekle(servis)
        self.takip.abone_ekle(musteri)
        for durum in SiparisDurumu:
            sessiz(self.takip.durum_guncelle, 7, durum)
        self.assertEqual(len(servis.is_kayitlari), 2)
        self.assertEqual(len(musteri.bildirimler), 4)


if __name__ == "__main__":
    unittest.main()
