"""Adapter (Yapısal Kalıp) — dil modeli bağımsızlığı.

Target   -> IDilModeli
Adapter  -> ClaudeAdapter
Adaptee  -> anthropic.Anthropic (Anthropic Python SDK istemcisi)

Asistan yalnızca IDilModeli'ni ve bu modüldeki sağlayıcıdan bağımsız veri
tiplerini (AracCagrisi, ModelYaniti) bilir. SDK'nın mesaj/blok formatı
ClaudeAdapter içinde çevrilir. Böylece:
  - asistan kodu SDK değişikliklerinden etkilenmez,
  - testlerde ve API anahtarı olmadan aynı arayüzü uygulayan
    CevrimdisiDilModeli kullanılabilir.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AracTanimi:
    ad: str
    aciklama: str
    girdi_semasi: dict[str, Any]


@dataclass(frozen=True)
class AracCagrisi:
    cagri_id: str
    ad: str
    girdi: dict[str, Any]


@dataclass(frozen=True)
class AracSonucu:
    cagri_id: str
    icerik: str
    hata: bool = False


@dataclass
class ModelYaniti:
    metin: str
    arac_cagrilari: list[AracCagrisi] = field(default_factory=list)
    reddedildi: bool = False
    # Sağlayıcıya özgü ham içerik; konuşma geçmişine aynen geri gönderilir.
    ham_icerik: Any = None


@dataclass
class Konusma:
    """Sağlayıcıdan bağımsız konuşma geçmişi."""

    kullanici_mesaji: str
    adimlar: list[tuple[ModelYaniti, list[AracSonucu]]] = field(default_factory=list)


class DilModeliHatasi(Exception):
    """Model çağrısı başarısız olduğunda (ağ, kimlik doğrulama vb.)."""


# [Adapter: Target]
class IDilModeli(ABC):
    @abstractmethod
    def yanit_uret(self, sistem: str, konusma: Konusma, araclar: list[AracTanimi]) -> ModelYaniti:
        """Konuşmanın bir sonraki adımını üretir."""


# [Adapter: Adapter]
class ClaudeAdapter(IDilModeli):
    """IDilModeli arayüzünü Anthropic SDK'sına (Adaptee) uyarlar."""

    MODEL = "claude-opus-5-5"

    def __init__(self, istemci: Any | None = None, model: str = MODEL) -> None:
        if istemci is None:
            import anthropic  # isteğe bağlı bağımlılık: yalnızca gerçek modelde gerekir

            # Kimlik bilgisi ortamdan okunur (ANTHROPIC_API_KEY); kodda anahtar tutulmaz.
            istemci = anthropic.Anthropic()
        self._istemci = istemci  # Adaptee
        self._model = model

    def yanit_uret(self, sistem: str, konusma: Konusma, araclar: list[AracTanimi]) -> ModelYaniti:
        import anthropic

        try:
            yanit = self._istemci.beta.messages.create(
                model=self._model,
                max_tokens=16000,
                system=sistem,
                messages=self._mesajlara_cevir(konusma),
                tools=[self._araca_cevir(a) for a in araclar],
                output_config={"effort": "medium"},
                # Güvenlik sınıflandırıcısı isteği reddederse sunucu tarafında yedek modele geçilir.
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
            )
        except anthropic.AuthenticationError as e:
            raise DilModeliHatasi("API anahtarı geçersiz veya tanımlı değil (ANTHROPIC_API_KEY).") from e
        except anthropic.RateLimitError as e:
            raise DilModeliHatasi("İstek sınırı aşıldı, biraz sonra tekrar deneyin.") from e
        except anthropic.APIStatusError as e:
            raise DilModeliHatasi(f"API hatası ({e.status_code}): {e.message}") from e
        except anthropic.APIConnectionError as e:
            raise DilModeliHatasi("Ağ bağlantısı kurulamadı.") from e

        return self._yanittan_cevir(yanit)

    # --- Çeviri katmanı (Adapter'ın asıl işi) ---

    @staticmethod
    def _araca_cevir(arac: AracTanimi) -> dict[str, Any]:
        return {
            "name": arac.ad,
            "description": arac.aciklama,
            "input_schema": arac.girdi_semasi,
            "strict": True,
        }

    @staticmethod
    def _mesajlara_cevir(konusma: Konusma) -> list[dict[str, Any]]:
        mesajlar: list[dict[str, Any]] = [{"role": "user", "content": konusma.kullanici_mesaji}]
        for model_yaniti, sonuclar in konusma.adimlar:
            # Ham içerik (düşünce blokları dahil) değiştirilmeden geri gönderilir.
            mesajlar.append({"role": "assistant", "content": model_yaniti.ham_icerik})
            if sonuclar:
                mesajlar.append({
                    "role": "user",
                    "content": [
                        {"type": "tool_result", "tool_use_id": s.cagri_id, "content": s.icerik, "is_error": s.hata}
                        for s in sonuclar
                    ],
                })
        return mesajlar

    @staticmethod
    def _yanittan_cevir(yanit: Any) -> ModelYaniti:
        metin = "".join(b.text for b in yanit.content if b.type == "text")
        cagrilar = [
            AracCagrisi(cagri_id=b.id, ad=b.name, girdi=dict(b.input))
            for b in yanit.content
            if b.type == "tool_use"
        ]
        return ModelYaniti(
            metin=metin,
            arac_cagrilari=cagrilar,
            reddedildi=yanit.stop_reason == "refusal",
            ham_icerik=yanit.content,
        )


# [Adapter: Target'ı uygulayan alternatif (çevrimdışı) model]
class CevrimdisiDilModeli(IDilModeli):
    """API anahtarı olmadan çalışan kural tabanlı model.

    Gerçek bir LLM değildir; aynı araç çağırma akışını deterministik olarak
    taklit eder. Testlerde ve anahtar tanımlı değilken kullanılır.
    """

    ANAHTAR_KELIMELER = {
        "ram": ("ram", "bellek", "çoklu görev", "render", "yayın"),
        "sivi_sogutma": ("soğutma", "sessiz", "overclock", "yayın", "render"),
        "ek_ssd": ("ssd", "depolama", "arşiv", "video", "kurgu", "oyun kütüphanesi"),
    }
    OYUN_KELIMELERI = ("oyun", "yayın", "render", "kurgu", "video", "grafik", "3d")

    def yanit_uret(self, sistem: str, konusma: Konusma, araclar: list[AracTanimi]) -> ModelYaniti:
        istek = konusma.kullanici_mesaji.lower()
        adim = len(konusma.adimlar)
        if adim == 0:
            return self._cagri("c1", "katalog_listele", {})
        if adim == 1:
            kasa = "oyun" if any(k in istek for k in self.OYUN_KELIMELERI) else "ofis"
            donanimlar = [kod for kod, kelimeler in self.ANAHTAR_KELIMELER.items() if any(k in istek for k in kelimeler)]
            self._taslak = (kasa, donanimlar)
            return self._cagri("c2", "fiyat_hesapla", {"kasa": kasa, "donanimlar": donanimlar})
        kasa, donanimlar = self._taslak
        son_sonuc = konusma.adimlar[-1][1][0]
        if son_sonuc.hata and donanimlar:
            # Guardrail reddettiyse (ör. bütçe aşımı) en pahalı donanımı çıkarıp yeniden dener.
            donanimlar = donanimlar[:-1]
            self._taslak = (kasa, donanimlar)
            return self._cagri(f"c{adim + 1}", "fiyat_hesapla", {"kasa": kasa, "donanimlar": donanimlar})
        if son_sonuc.hata and kasa == "oyun":
            kasa = "ofis"
            self._taslak = (kasa, donanimlar)
            return self._cagri(f"c{adim + 1}", "fiyat_hesapla", {"kasa": kasa, "donanimlar": donanimlar})
        return self._cagri(
            f"c{adim + 1}",
            "oneri_sun",
            {"kasa": kasa, "donanimlar": donanimlar, "gerekce": "İstekteki anahtar kelimelere göre seçildi (çevrimdışı mod)."},
        )

    @staticmethod
    def _cagri(cagri_id: str, ad: str, girdi: dict[str, Any]) -> ModelYaniti:
        cagri = AracCagrisi(cagri_id, ad, girdi)
        return ModelYaniti(metin="", arac_cagrilari=[cagri], ham_icerik=[cagri])


# [Adapter: Adapter]
class GeminiAdapter(IDilModeli):
    """IDilModeli arayüzünü Google Gen AI SDK'sına (Adaptee: google.genai.Client) uyarlar.

    Asistan, araçlar ve guardrail'ler değişmeden kalır; yalnızca bu çeviri katmanı
    eklenerek model sağlayıcısı değiştirilmiştir.
    """

    VARSAYILAN_MODEL = "gemini-3.6-flash"
    ZAMAN_ASIMI_MS = 60_000

    def __init__(self, istemci: Any | None = None, model: str | None = None) -> None:
        import os

        if istemci is None:
            from google import genai  # isteğe bağlı bağımlılık
            from google.genai import types

            # Anahtar ortamdan okunur (GEMINI_API_KEY veya GOOGLE_API_KEY); kodda anahtar tutulmaz.
            istemci = genai.Client(http_options=types.HttpOptions(timeout=self.ZAMAN_ASIMI_MS))
        self._istemci = istemci  # Adaptee
        self._model = model or os.environ.get("GEMINI_MODEL") or self.VARSAYILAN_MODEL

    @property
    def model_adi(self) -> str:
        return self._model

    def yanit_uret(self, sistem: str, konusma: Konusma, araclar: list[AracTanimi]) -> ModelYaniti:
        from google.genai import errors, types

        ayarlar = types.GenerateContentConfig(
            system_instruction=sistem,
            tools=[types.Tool(function_declarations=[self._araca_cevir(a) for a in araclar])] if araclar else None,
            # Araç döngüsünü asistan yönetir; SDK'nın otomatik araç çağırması kapatılır.
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )
        try:
            yanit = self._istemci.models.generate_content(
                model=self._model, contents=self._mesajlara_cevir(konusma), config=ayarlar
            )
        except errors.ClientError as e:
            if e.code == 429:
                raise DilModeliHatasi("İstek sınırı aşıldı, biraz sonra tekrar deneyin.") from e
            if e.code in (400, 401, 403) and "key" in str(e.message).lower():
                raise DilModeliHatasi("Gemini API anahtarı geçersiz (GEMINI_API_KEY).") from e
            raise DilModeliHatasi(f"Gemini API hatası ({e.code}): {e.message}") from e
        except errors.APIError as e:
            raise DilModeliHatasi(f"Gemini sunucu hatası ({e.code}): {e.message}") from e
        except OSError as e:
            raise DilModeliHatasi("Ağ bağlantısı kurulamadı.") from e
        return self._yanittan_cevir(yanit)

    # --- Çeviri katmanı ---

    @staticmethod
    def _araca_cevir(arac: AracTanimi) -> Any:
        from google.genai import types

        return types.FunctionDeclaration(
            name=arac.ad, description=arac.aciklama, parameters_json_schema=arac.girdi_semasi
        )

    @staticmethod
    def _mesajlara_cevir(konusma: Konusma) -> list[Any]:
        from google.genai import types

        icerikler = [types.Content(role="user", parts=[types.Part(text=konusma.kullanici_mesaji)])]
        for model_yaniti, sonuclar in konusma.adimlar:
            # Modelin içeriği (thought signature'lar dahil) değiştirilmeden geri gönderilir.
            icerikler.append(model_yaniti.ham_icerik)
            if sonuclar:
                adlar = {c.cagri_id: c.ad for c in model_yaniti.arac_cagrilari}
                parcalar = []
                for s in sonuclar:
                    parca = types.Part.from_function_response(
                        name=adlar.get(s.cagri_id, ""),
                        response={"error": s.icerik} if s.hata else {"result": s.icerik},
                    )
                    if not s.cagri_id.startswith("yerel-"):
                        parca.function_response.id = s.cagri_id
                    parcalar.append(parca)
                icerikler.append(types.Content(role="user", parts=parcalar))
        return icerikler

    @staticmethod
    def _yanittan_cevir(yanit: Any) -> ModelYaniti:
        from google.genai import types

        aday = yanit.candidates[0] if yanit.candidates else None
        engellendi = bool(getattr(yanit, "prompt_feedback", None) and yanit.prompt_feedback.block_reason)
        if aday is None or aday.content is None:
            return ModelYaniti(metin="", reddedildi=True)
        parcalar = aday.content.parts or []
        metin = "".join(p.text for p in parcalar if p.text and not p.thought)
        cagrilar = [
            # Eski modeller çağrı kimliği döndürmeyebilir; o durumda yerel bir kimlik üretilir.
            AracCagrisi(cagri_id=p.function_call.id or f"yerel-{i}", ad=p.function_call.name, girdi=dict(p.function_call.args or {}))
            for i, p in enumerate(parcalar)
            if p.function_call
        ]
        return ModelYaniti(
            metin=metin,
            arac_cagrilari=cagrilar,
            reddedildi=engellendi or aday.finish_reason == types.FinishReason.SAFETY,
            ham_icerik=aday.content,
        )


def varsayilan_dil_modeli() -> tuple[IDilModeli, str]:
    """Ortama göre modeli seçer: Gemini anahtarı → Gemini, Anthropic anahtarı → Claude,
    hiçbiri yoksa çevrimdışı model.

    Konsol ve pencere arayüzü aynı seçimi kullanır; dönen metin kullanıcıya gösterilir.
    """
    import os

    if os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"):
        try:
            model = GeminiAdapter()
            return model, f"Gemini modeli kullanılıyor ({model.model_adi})"
        except ImportError:
            return CevrimdisiDilModeli(), "google-genai paketi kurulu değil (pip install -r requirements.txt) — çevrimdışı model kullanılıyor"
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            return ClaudeAdapter(), "Claude modeli kullanılıyor"
        except ImportError:
            return CevrimdisiDilModeli(), "anthropic paketi kurulu değil (pip install -r requirements.txt) — çevrimdışı model kullanılıyor"
    return CevrimdisiDilModeli(), "GEMINI_API_KEY tanımlı değil — çevrimdışı kural tabanlı model kullanılıyor"
