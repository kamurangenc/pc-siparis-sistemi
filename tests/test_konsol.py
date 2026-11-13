"""Konsol arayüzü uçtan uca testleri (girdi/çıktı enjekte edilerek)."""
import io
import unittest
from contextlib import redirect_stdout

from pc_siparis.ai import CevrimdisiDilModeli
from pc_siparis.konsol import KonsolUygulamasi


def calistir(girdiler, **kwargs):
    akis = iter(girdiler)
    cikti = []

    def girdi(_soru):
        try:
            return next(akis)
        except StopIteration:
            raise EOFError from None

    uygulama = KonsolUygulamasi(girdi=girdi, cikti=cikti.append, **kwargs)
    with redirect_stdout(io.StringIO()) as panel_ciktisi:  # Observer panelleri print kullanır
        uygulama.calistir()
    return uygulama, "\n".join(cikti), panel_ciktisi.getvalue()


class KonsolTestleri(unittest.TestCase):
    def test_kendin_topla_havale_ile_siparis(self):
        # ad, menü=1, kasa=oyun, donanım=1(ram), bitti, ödeme=havale, çıkış
        uyg, cikti, paneller = calistir(["Ali", "1", "oyun", "1", "0", "1", "0"])
        self.assertEqual(len(uyg._siparisler), 1)
        self.assertEqual(uyg._siparisler[0].odeme.odenen_tutar, round(42_500 * 0.95, 2))
        self.assertIn("Kargoya verildi", paneller)

    def test_hazir_paket_kredi_karti_taksit(self):
        uyg, _, _ = calistir(["Ayşe", "2", "ogrenci", "0", "2", "6", "0"])
        self.assertEqual(uyg._siparisler[0].odeme.odenen_tutar, 18_000 * 1.10)

    def test_ai_onerisi_onaylanip_siparis_edilir(self):
        uyg, cikti, _ = calistir(
            ["Can", "3", "oyun ve video kurgu", "60000", "1", "1", "0"],
            dil_modeli=CevrimdisiDilModeli(),
        )
        self.assertIn("Gerekçe:", cikti)
        self.assertEqual(len(uyg._siparisler), 1)
        self.assertLessEqual(uyg._siparisler[0].odeme.liste_fiyati, 60_000)

    def test_gecersiz_secim_tekrar_sorulur(self):
        _, cikti, _ = calistir(["Ali", "9", "0"])
        self.assertIn("Geçersiz seçim", cikti)

    def test_girdi_kapanirsa_duzgun_cikar(self):
        uyg, cikti, _ = calistir(["Ali", "1"])
        self.assertIn("Toplam 0 sipariş", cikti)


if __name__ == "__main__":
    unittest.main()
