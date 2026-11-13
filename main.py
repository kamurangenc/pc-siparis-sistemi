"""Etkileşimli uygulama giriş noktası.

Çalıştırma:  python main.py
AI asistanı için (isteğe bağlı): ANTHROPIC_API_KEY ortam değişkeni tanımlanmalı
ve `pip install -r requirements.txt` ile anthropic paketi kurulmalıdır.
"""
from pc_siparis.konsol import KonsolUygulamasi

if __name__ == "__main__":
    KonsolUygulamasi().calistir()
