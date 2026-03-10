import csv
from pathlib import Path

giris = "akademisyenler.csv"
cikis = "akademisyenler_temiz.csv"

goruldu = set()
satirlar = []

with open(giris, encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        isim = row["ad_soyad"].strip()
        if isim not in goruldu:
            goruldu.add(isim)
            satirlar.append(row)

with open(cikis, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=["bolum", "unvan", "ad_soyad", "email"])
    writer.writeheader()
    writer.writerows(satirlar)

print(f"Oncesi: {len(goruldu) + (sum(1 for _ in open(giris, encoding='utf-8-sig')) - 1 - len(satirlar))} satir")
print(f"Sonrasi: {len(satirlar)} satir")
print(f"Silinen: {sum(1 for _ in open(giris, encoding='utf-8-sig')) - 1 - len(satirlar)} tekrar")
print(f"Kaydedildi: {cikis}")