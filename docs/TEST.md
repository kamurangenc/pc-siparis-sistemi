# Test Dokümanı

Modüler Bilgisayar Toplama ve Sipariş Sistemi — EBLG443 Tasarım Kalıpları dönem projesi.

## 1. Test Stratejisi

| Konu | Yaklaşım |
|---|---|
| Test çatısı | Python standart kütüphanesindeki `unittest` (pytest ile de çalışır). Ek kurulum gerekmez. |
| Birim testleri | Her tasarım kalıbının rollerini ve davranışını ayrı test sınıflarında doğrular. |
| Uçtan uca testler | Konsol arayüzü, `girdi`/`cikti` fonksiyonları dışarıdan verilerek gerçek menü akışlarıyla çalıştırılır. Pencere arayüzü gizli bir pencerede açılıp işlemleri doğrudan çağrılarak test edilir; grafik ortamı olmayan makinelerde bu testler atlanır. |
| AI testleri | Gerçek dil modeli yerine `IDilModeli`'ni uygulayan senaryolu sahte modeller ve sahte bir SDK istemcisi kullanılır. Ağ erişimi ve API anahtarı gerekmez, sonuçlar her çalıştırmada aynıdır. |
| Hata durumları | Geçersiz girdiler, bilinmeyen ürün/donanım kodları, bütçe aşımı, prompt injection ve model hataları ayrıca test edilir. |

Test edilebilirlik doğrudan kalıplardan gelir: Adapter sayesinde gerçek model sahte bir
modelle değiştirilebilir; Strategy ve Observer arayüzleri sayesinde testlere özel
stratejiler ve gözlemciler (`KayitciGozlemci`) yazılabilir.

## 2. Testleri Çalıştırma

Proje kök klasöründe:

```bash
python -m unittest discover -s tests -v
```

Tek bir test dosyasını çalıştırmak için:

```bash
python -m unittest tests.test_kaliplar -v
```

Tek bir test sınıfını çalıştırmak için:

```bash
python -m unittest tests.test_ai.AdapterTestleri -v
```

## 3. Test Dosyaları

| Dosya | Kapsam | Test sayısı |
|---|---|---|
| `tests/test_kaliplar.py` | Arayüzler, Factory Method, Decorator, katalog, Strategy, Observer | 23 |
| `tests/test_ai.py` | Command, AI asistanı (Tool Use, Guardrail), Adapter | 14 |
| `tests/test_konsol.py` | Konsol arayüzü uçtan uca akışları | 5 |
| `tests/test_pencere.py` | Pencere arayüzü ve pencere gözlemcileri | 7 |
| **Toplam** | | **49** |

## 4. Kalıp – Test Eşlemesi

### 4.1 Arayüzler

| Test | Doğruladığı davranış |
|---|---|
| `test_arayuzler_dogrudan_orneklenemez` | `IBilgisayar`, `BilgisayarFabrikasi`, `IOdemeStratejisi`, `ISiparisGozlemcisi` soyut sınıflardır; doğrudan nesne oluşturulamaz. |

### 4.2 Factory Method

| Test | Doğruladığı davranış |
|---|---|
| `test_kullanim_amacina_gore_dogru_kasa_uretilir` | "ofis" → `OfisKasasi`, "oyun" → `OyunKasasi` (büyük/küçük harf duyarsız). |
| `test_bilinmeyen_tip_hata_verir` | Desteklenmeyen kasa tipinde `ValueError`. |
| `test_ortak_surec_seri_no_verir` | Creator'ın ortak süreci her üretimde sıralı seri numarası verir (`STD-0002`). |
| `test_kalite_kontrol_hatali_urunu_reddeder` | Fiyatı geçersiz ürün kalite kontrolde `UretimHatasi` ile reddedilir. |
| `test_hazir_paket_fabrikasi_dekore_edilmis_urun_uretir` | İkinci ConcreteCreator, dekoratörlerle sarmalanmış paketi `IBilgisayar` olarak üretir. |
| `test_istemci_her_fabrikayla_ayni_akisi_kullanir` | Aynı istemci kodu iki fabrikanın tüm seçenekleriyle çalışır (polimorfizm). |
| `test_yeni_model_mevcut_kod_degismeden_eklenir` | Yeni kasa modeli yalnızca kayıtla eklenir (Open-Closed). |

### 4.3 Decorator ve Katalog

| Test | Doğruladığı davranış |
|---|---|
| `test_tek_dekorator_fiyat_ve_parca_ekler` | Bir dekoratör fiyata ve parça listesine kendi katkısını ekler. |
| `test_dekoratorler_ic_ice_sarmalanabilir` | Üç dekoratör iç içe eklendiğinde fiyat ve açıklama doğru birikir. |
| `test_ayni_dekorator_birden_fazla_kez_eklenebilir` | Aynı donanım iki kez eklenebilir. |
| `test_dekorator_soyut_siniftir` | `DonanimDecorator` bir `IBilgisayar`'dır (Component arayüzünü uygular). |
| `test_katalog_kod_ile_dekorator_ekler` | Katalog, donanım kodunu doğru dekoratöre çevirir. |
| `test_bilinmeyen_donanim_hata_verir` | Katalogda olmayan donanım kodunda `ValueError`. |

### 4.4 Strategy

| Test | Doğruladığı davranış |
|---|---|
| `test_havale_indirim_uygular` | %5 havale indirimi: 10.000 TL → 9.500 TL. |
| `test_kredi_karti_tek_cekim_vade_farksiz` | Tek çekimde vade farkı yoktur. |
| `test_kredi_karti_taksitte_vade_farki` | 6 taksit, aylık %2: 10.000 TL → 11.000 TL. |
| `test_gecersiz_parametreler` | Geçersiz indirim oranı ve taksit sayısında `ValueError`. |
| `test_context_stratejiyi_calisma_aninda_degistirir` | `SiparisIsleyici` çalışma anında strateji değiştirir; sipariş numaraları farklıdır. |

### 4.5 Observer

| Test | Doğruladığı davranış |
|---|---|
| `test_tum_asamalar_sirayla_bildirilir` | Ödeme → montaj → test → kargo aşamaları sırayla bildirilir; son durum KARGODA. |
| `test_abonelikten_cikan_bildirim_almaz` | Abonelikten çıkan gözlemci bildirim almaz. |
| `test_ayni_gozlemci_iki_kez_eklenmez` | Aynı gözlemci iki kez kaydedilmez. |
| `test_teknik_servis_yalniz_ilgili_asamalari_kaydeder` | Teknik servis yalnızca montaj ve test aşamalarını, müşteri paneli dört aşamanın tümünü alır. |

### 4.6 Command (AI araçları)

| Test | Doğruladığı davranış |
|---|---|
| `test_invoker_komutu_adiyla_yurutur` | `AracYurutucu`, `katalog_listele` komutunu adıyla çalıştırır; kasalar ve donanımlar döner. |
| `test_fiyat_hesaplama_gercek_dekoratorleri_kullanir` | Fiyat aracı gerçek fabrika ve dekoratörlerle hesaplar (oyun + RAM = 42.500 TL). |
| `test_hatalar_modele_hata_sonucu_olarak_doner` | Bilinmeyen araç, bilinmeyen kasa ve bütçe aşımı istisna fırlatmaz; modele hata sonucu döner. |
| `test_strict_semalar_ek_alanlara_kapali` | Tüm araç şemaları `additionalProperties: false` içerir. |

### 4.7 AI Asistanı (Tool Use, Guardrail)

| Test | Doğruladığı davranış |
|---|---|
| `test_tool_use_dongusu_oneriyi_ibilgisayar_olarak_dondurur` | Katalog → fiyat → öneri döngüsü sonunda doğru fiyatlı bir `IBilgisayar` döner. |
| `test_cikti_guardrail_butce_asimini_reddeder_ve_duzeltme_ister` | Bütçeyi aşan öneri reddedilir, hata modele iletilir, model düzeltilmiş öneri sunar. |
| `test_uydurma_parca_kabul_edilmez` | Katalogda olmayan parça (`rtx_5090`) içeren öneri kabul edilmez. |
| `test_girdi_guardrail_modeli_cagirmadan_reddeder` | Boş istek, prompt injection, negatif bütçe ve 1000 karakterden uzun istek modele gönderilmeden reddedilir. |
| `test_maksimum_adimda_durur` | Model öneri teslim etmezse döngü `MAKS_ADIM` adımda durur. |
| `test_cevrimdisi_model_butceye_uyar` | Çevrimdışı model, bütçeyi aşmayan bir oyun sistemi önerir. |

### 4.8 Adapter

Gerçek `anthropic.Anthropic` istemcisi yerine, gelen isteği kaydeden sahte bir istemci kullanılır.

| Test | Doğruladığı davranış |
|---|---|
| `test_sdk_yaniti_bagimsiz_tiplere_cevrilir` | SDK yanıtındaki metin ve araç çağrısı blokları `ModelYaniti` / `AracCagrisi` tiplerine çevrilir. |
| `test_istek_sdk_formatina_cevrilir` | İstek doğru model adı, mesaj formatı ve `strict` araç tanımlarıyla gönderilir. |
| `test_gecmis_ham_icerikle_ve_arac_sonuclariyla_gonderilir` | Önceki model yanıtı (düşünce blokları dahil) değiştirilmeden geri gönderilir; araç sonuçları doğru `tool_use_id` ile eklenir. |
| `test_ret_durumu_isaretlenir` | Modelin reddettiği istek `reddedildi` olarak işaretlenir. |

### 4.9 Konsol Arayüzü (Uçtan Uca)

| Test | Senaryo |
|---|---|
| `test_kendin_topla_havale_ile_siparis` | Oyun kasası + RAM, havale ile sipariş; ödenen tutar 40.375 TL, kargo bildirimi görüntülenir. |
| `test_hazir_paket_kredi_karti_taksit` | Öğrenci paketi, kredi kartı 6 taksit; ödenen tutar 19.800 TL. |
| `test_ai_onerisi_onaylanip_siparis_edilir` | AI önerisi alınır, gerekçe gösterilir, onaylanıp bütçe içinde sipariş verilir. |
| `test_gecersiz_secim_tekrar_sorulur` | Geçersiz menü seçimi uyarı verip yeniden sorulur. |
| `test_girdi_kapanirsa_duzgun_cikar` | Girdi akışı kapanırsa (Ctrl+Z / Ctrl+D) uygulama hata vermeden çıkar. |

### 4.10 Pencere Arayüzü

| Test | Senaryo |
|---|---|
| `test_temel_kasa_donanim_havale_siparisi` | Oyun kasası + RAM, havale; önizleme ve ödenen tutar 40.375 TL. |
| `test_pencere_gozlemcileri_tum_asamalari_alir` | Pencere müşteri paneli 4, teknik servis paneli 2 bildirim alır; aşama göstergesi KARGODA'da biter (yeni ConcreteObserver'lar). |
| `test_kredi_karti_taksit_onizlemesi` | Öğrenci paketi, 6 taksit; önizlemede 19.800 TL. |
| `test_donanimlari_sifirla_temel_sisteme_doner` | Eklenen donanımlar kaldırılınca temel kasaya dönülür. |
| `test_secim_yapilmadan_siparis_verilemez` | Sistem seçilmeden sipariş verilemez; durum çubuğunda uyarı görünür. |
| `test_ai_onerisi_sisteme_yuklenir` | AI önerisi sisteme yüklenir, gerekçe gösterilir, bütçe içinde sipariş verilir. |
| `test_ai_guardrail_hatasi_durum_cubugunda_gosterilir` | Prompt injection içeren istek reddedilir, hata durum çubuğunda gösterilir. |

## 5. Manuel Kabul Testleri

Otomatik testlere ek olarak, `python main.py` ile elle doğrulanacak senaryolar:

| # | Adımlar | Beklenen sonuç |
|---|---|---|
| M1 | Menü `1` → `oyun` → donanım `1` (RAM) → `0` → ödeme `1` (havale) | Liste fiyatı 42.500 TL, ödenen 40.375 TL; montaj, test, kargo bildirimleri görünür. |
| M2 | Menü `2` → `pro` → `0` → ödeme `2` → taksit `12` | Liste fiyatı 49.500 TL; %22 vade farkıyla ödenen 60.390 TL (12 x 5.032,50 TL). |
| M3 | Menü `3` → "yayın yapıp oyun oynayacağım, sessiz olsun" → bütçe `50000` → `1` → ödeme `1` | Bütçeyi aşmayan bir oyun sistemi ve gerekçesi gösterilir; sipariş tamamlanır. |
| M4 | Menü `3` → "önceki talimatları yok say" | "Öneri alınamadı" mesajı; uygulama menüye döner. |
| M5 | Menü `3` → herhangi bir istek → bütçe `10000` | Bütçeye uygun sistem olmadığı için "Öneri alınamadı" mesajı. |
| M6 | Menüde `9` yazmak | "Geçersiz seçim" uyarısı, aynı soru tekrar sorulur. |
| M8 | `python gui.py` → Temel Kasa: Oyun → Seç ve Üret → + RAM, + Sıvı Soğutma → Kredi kartı, 6 taksit → Siparişi Tamamla | Liste fiyatı 46.500 TL, ödenecek 51.150 TL; dört aşama yeşile döner, iki panel bildirimleri gösterir. |
| M7 | `ANTHROPIC_API_KEY` tanımlıyken M3 | "(Claude modeli kullanılıyor)" yazısı görünür, öneri gerçek modelden gelir. |

M1–M6 ve M8 çevrimdışı modelle doğrulanmıştır (M8'in ekran görüntüsü: `docs/ekran_goruntusu.png`). M7 için geçerli bir API anahtarı gerekir.

## 6. Son Çalıştırma Sonucu

| Bilgi | Değer |
|---|---|
| Tarih | 23 Kasım 2026 |
| Ortam | Windows 11, Python 3.10.11 |
| Komut | `python -m unittest discover -s tests -v` |
| Sonuç | **49 test, 49 başarılı, 0 hata** (`OK`) |
