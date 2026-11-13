# Modüler Bilgisayar Toplama ve Sipariş Sistemi

EBLG443 Tasarım Kalıpları — Dönem Projesi · Python 3.10+ (`abc.ABC`)

Temel kasaları fabrika üzerinden üreten, ek donanımları çalışma anında
sarmalayan, ödeme algoritmalarını değiştirilebilir kılan ve montaj/kargo
aşamalarını ilgili panellere bildiren nesne yönelimli bir sipariş motoru.

## Kullanılan GoF Kalıpları

| Kalıp | Grup | Dosya | Çözdüğü problem |
|---|---|---|---|
| Factory Method | Yaratımsal | `pc_siparis/fabrika.py` | İstemcinin somut kasa sınıflarına bağımlılığı |
| Decorator | Yapısal | `pc_siparis/dekoratorler.py` | Donanım kombinasyonlarında sınıf patlaması |
| Strategy | Davranışsal | `pc_siparis/odeme.py`, `pc_siparis/siparis.py` | Ödeme yöntemleri için if/else zinciri |
| Observer | Davranışsal | `pc_siparis/takip.py` | Sipariş akışının bildirim modüllerine bağımlılığı |

Kodda her rol, sınıfın üstünde `# [Kalıp: Rol]` yorumuyla işaretlidir.
Ayrıntılı rol tablosu ve UML diyagramları: [docs/KALIP_HARITASI.md](docs/KALIP_HARITASI.md).

## Proje Yapısı

```
pc_siparis/
  urunler.py       IBilgisayar, OfisKasasi, OyunKasasi
  fabrika.py       BilgisayarFabrikasi, StandartSistemFabrikasi
  dekoratorler.py  DonanimDecorator ve somut donanım dekoratörleri
  odeme.py         IOdemeStratejisi ve somut ödeme stratejileri
  takip.py         SiparisTakipMerkezi, ISiparisGozlemcisi, paneller
  siparis.py       SiparisIsleyici (Strategy Context)
tests/
  test_kaliplar.py
main.py            Uçtan uca demo
```

## Çalıştırma

Harici bağımlılık yoktur (yalnızca Python standart kütüphanesi).

```bash
python main.py
```

## Testler

Testler standart `unittest` çatısıyla yazılmıştır (pytest ile de çalışır):

```bash
python -m unittest discover -s tests -v
```

## Genişletme Örnekleri

- **Yeni kasa modeli:** `IBilgisayar`'dan türeyen sınıf yaz, `fabrika.kasa_kaydet("ad", Sinif)` ile kaydet.
- **Yeni donanım:** `DonanimDecorator`'dan türet, `EK_ACIKLAMA / EK_FIYAT / EK_PARCA` tanımla.
- **Yeni ödeme yöntemi:** `IOdemeStratejisi`'ni uygula, `SiparisIsleyici`'ye ver.
- **Yeni bildirim kanalı:** `ISiparisGozlemcisi`'ni uygula, `takip.abone_ekle(...)` ile kaydet.

Hiçbirinde mevcut sınıfların değiştirilmesi gerekmez (Open-Closed).

## Kaynaklar ve Beyan

- Harici kütüphane kullanılmamıştır.
- Geliştirme sürecinde yapay zekâ kod asistanından (Claude Code) yararlanılmıştır.
