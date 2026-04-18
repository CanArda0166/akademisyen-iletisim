import csv
import unicodedata
from pathlib import Path

GIRIS = "akademisyenler.csv"
CIKIS = "akademisyenler_temiz.csv"

def site_temizle(metin):
    metin = unicodedata.normalize("NFC", metin)
    metin = metin.replace("i\u0307", "i")
    metin = metin.replace("I\u0307", "I")
    return metin.strip()

def site_upper(metin):
    s = site_temizle(metin)
    for fr, to in [
        ("\u011f","G"),("\u011e","G"),("\u015f","S"),("\u015e","S"),
        ("\u00fc","U"),("\u00dc","U"),("\u00f6","O"),("\u00d6","O"),
        ("\u00e7","C"),("\u00c7","C"),("\u0131","I"),("\u0130","I"),
    ]:
        s = s.replace(fr, to)
    return s.upper()

def unvan_duzelt(ham):
    ham = ham.split("(")[0].strip()
    s = site_upper(ham)
    if s == "PROFESOR":
        return "Prof. Dr."
    if s == "DOCENT":
        return "Doç. Dr."
    if s == "DOKTOR OGRETIM UYESI":
        return "Dr. Öğr. Üyesi"
    if s == "ARASTIRMA GOREVLISI":
        return "Arş. Gör."
    if s == "OGRETIM GOREVLISI":
        return "Öğr. Gör."
    if s == "DOKTOR":
        return "Dr."
    return site_temizle(ham)

satirlar = []
with open(GIRIS, encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    sutunlar = reader.fieldnames
    for row in reader:
        row["unvan"] = unvan_duzelt(row.get("unvan", ""))
        satirlar.append(row)

with open(CIKIS, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=sutunlar)
    writer.writeheader()
    writer.writerows(satirlar)

print(f"Tamam! {len(satirlar)} kayit -> {CIKIS}")