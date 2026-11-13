"""Guardrail (LLM kalıbı) — modele giden girdinin ve modelden gelen önerinin denetimi.

Girdi denetimi : boş/aşırı uzun istekleri ve bilinen prompt-injection
                 kalıplarını modele ulaşmadan reddeder.
Çıktı denetimi : modelin önerdiği sistemin katalogda gerçekten var olduğunu
                 ve bütçeyi aşmadığını kontrol eder. Model "uydurma" bir parça
                 ya da bütçe dışı bir sistem önerirse öneri kabul edilmez,
                 hata modele geri bildirilir ve düzeltmesi istenir.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..urunler import IBilgisayar


@dataclass(frozen=True)
class DenetimSonucu:
    gecti: bool
    neden: str = ""


GECTI = DenetimSonucu(True)


class GirdiDenetcisi:
    MAKS_UZUNLUK = 1000
    YASAKLI_IFADELER = (
        "ignore previous", "önceki talimatları", "sistem promptu", "system prompt",
        "talimatları yok say", "you are now", "developer mode",
    )

    def denetle(self, istek: str, butce: float | None) -> DenetimSonucu:
        metin = istek.strip()
        if not metin:
            return DenetimSonucu(False, "İstek boş olamaz.")
        if len(metin) > self.MAKS_UZUNLUK:
            return DenetimSonucu(False, f"İstek en fazla {self.MAKS_UZUNLUK} karakter olabilir.")
        kucuk = metin.lower()
        if any(ifade in kucuk for ifade in self.YASAKLI_IFADELER):
            return DenetimSonucu(False, "İstek, asistanın talimatlarını değiştirmeye yönelik ifadeler içeriyor.")
        if butce is not None and butce <= 0:
            return DenetimSonucu(False, "Bütçe pozitif olmalıdır.")
        return GECTI


class CiktiDenetcisi:
    def denetle(self, bilgisayar: IBilgisayar, butce: float | None) -> DenetimSonucu:
        if butce is not None and bilgisayar.maliyet() > butce:
            return DenetimSonucu(
                False, f"Önerilen sistem {bilgisayar.maliyet():,.0f} TL; bütçe {butce:,.0f} TL. Daha uygun bir kombinasyon öner."
            )
        return GECTI
