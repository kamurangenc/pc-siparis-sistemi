"""Para biçimlendirme: tutarları Türkçe yazımla gösterir (ör. 46.500,00 TL)."""


def tl(tutar: float, ondalik: int = 2) -> str:
    metin = f"{tutar:,.{ondalik}f}"
    return metin.replace(",", "_").replace(".", ",").replace("_", ".") + " TL"
