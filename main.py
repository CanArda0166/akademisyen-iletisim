import csv
import time
import re
import logging
import sys
import unicodedata
from pathlib import Path
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait

CONFIG = {
    "cikti_csv": "akademisyenler.csv",
    "headless": False,
    "sayfa_bekleme": 1.5,
    "max_sayfa": 9999,
}

ANA_URL = "https://akademik.yok.gov.tr/AkademikArama/"

CSV_SUTUNLAR = [
    "temel_alan", "bilim_alani", "unvan", "ad_soyad", "email",
    "universite", "fakulte", "bolum", "anabilim_dali",
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("tarama.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)


def site_temizle(metin):
    metin = unicodedata.normalize("NFC", metin)
    metin = metin.replace("i\u0307", "i")
    metin = metin.replace("I\u0307", "I")
    return metin.strip()


def site_upper(metin):
    s = site_temizle(metin)
    for fr, to in [
        ("ğ","G"),("Ğ","G"),("ş","S"),("Ş","S"),
        ("ü","U"),("Ü","U"),("ö","O"),("Ö","O"),
        ("ç","C"),("Ç","C"),("ı","I"),("İ","I"),("i","I"),
    ]:
        s = s.replace(fr, to)
    return s.upper()


def tr_title(s):
    s = site_temizle(s)
    kelimeler = []
    for w in s.split():
        if w:
            kelimeler.append(w[0].upper() + w[1:].lower())
    return " ".join(kelimeler)


def unvan_normalize(ham):
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


def driver_olustur(headless):
    opt = webdriver.ChromeOptions()
    if headless:
        opt.add_argument("--headless=new")
    opt.add_argument("--no-sandbox")
    opt.add_argument("--disable-dev-shm-usage")
    opt.add_argument("--window-size=1920,1080")
    opt.add_argument("--lang=tr")
    try:
        d = webdriver.Chrome(service=Service(), options=opt)
    except Exception:
        from webdriver_manager.chrome import ChromeDriverManager
        d = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opt)
    d.set_page_load_timeout(30)
    return d


def bekle(driver, saniye):
    try:
        WebDriverWait(driver, 15).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
    except Exception:
        pass
    time.sleep(saniye)


def hata_sayfasi_mi(driver):
    try:
        metin = driver.find_element(By.TAG_NAME, "body").text
        return "zgünüz" in metin or "zaman aşımı" in metin
    except Exception:
        return False


def kart_parse_et(kart_html):
    soup = BeautifulSoup(kart_html, "html.parser")

    ad_soyad = ""
    for a in soup.find_all("a", href=True):
        if "AkademisyenGorevOgrenimBilgileri" in a["href"] and a.get_text(strip=True):
            ad_soyad = site_temizle(a.get_text(strip=True))
            break
    if not ad_soyad:
        return None

    email = ""
    for a in soup.find_all("a", href=True):
        if a["href"].startswith("mailto:"):
            email = a["href"][7:].strip()
            break

    unvan = ""
    h4 = soup.find("h4")
    if h4:
        h6_unvan = h4.find_previous_sibling("h6")
        if h6_unvan:
            unvan = unvan_normalize(h6_unvan.get_text(strip=True))

    universite = fakulte = bolum = anabilim_dali = ""
    if h4:
        h6_kurum = h4.find_next_sibling("h6")
        if h6_kurum:
            parcalar = [p.strip() for p in h6_kurum.get_text().split("/") if p.strip()]
            if len(parcalar) >= 1:
                universite = tr_title(parcalar[0])
            if len(parcalar) >= 2:
                fakulte = tr_title(parcalar[1])
            if len(parcalar) >= 3:
                bolum = tr_title(parcalar[2])
            if len(parcalar) >= 4:
                anabilim_dali = tr_title(parcalar[3])

    temel_alan = ""
    span_success = soup.find("span", class_="label-success")
    if span_success:
        a = span_success.find("a")
        if a:
            temel_alan = site_temizle(a.get_text(strip=True)).replace(" Temel Alanı", "").strip()

    bilim_alani = ""
    span_primary = soup.find("span", class_="label-primary")
    if span_primary:
        a = span_primary.find("a", class_="anahtarKelime")
        if a:
            bilim_alani = site_temizle(a.get_text(strip=True))

    return {
        "temel_alan": temel_alan,
        "bilim_alani": bilim_alani,
        "unvan": unvan,
        "ad_soyad": ad_soyad,
        "email": email,
        "universite": universite,
        "fakulte": fakulte,
        "bolum": bolum,
        "anabilim_dali": anabilim_dali,
    }


def sayfa_karti_topla(driver):
    html = driver.find_element(By.TAG_NAME, "body").get_attribute("innerHTML")
    soup = BeautifulSoup(html, "html.parser")
    kartlar = []
    goruldu = set()

    for tr in soup.find_all("tr", id=re.compile(r"^authorInfo_")):
        isim = ""
        for a in tr.find_all("a", href=True):
            if "AkademisyenGorevOgrenimBilgileri" in a["href"] and a.get_text(strip=True):
                isim = a.get_text(strip=True)
                break
        if not isim or isim in goruldu:
            continue
        goruldu.add(isim)
        sonuc = kart_parse_et(str(tr))
        if sonuc:
            kartlar.append(sonuc)

    return kartlar


def sonraki_sayfa_url(driver, mevcut_sayfa):
    try:
        linkler = driver.find_elements(By.XPATH, "//ul[contains(@class,'pagination')]//a")
        for link in linkler:
            if link.text.strip() == str(mevcut_sayfa + 1):
                return link.get_attribute("href")
        for link in linkler:
            if link.text.strip() in ("\u00bb", ">>", ">", "Next", "Sonraki"):
                return link.get_attribute("href")
    except Exception:
        pass
    return None


def alan_tara(driver, csv_yazar, max_sayfa, email_zorunlu=False):
    toplam = 0
    sayfa = 1

    while sayfa <= max_sayfa:
        if hata_sayfasi_mi(driver):
            log.warning(f"SESSION HATASI! Sayfa {sayfa}")
            print(f"\nSunucu session timeout! Sayfa {sayfa}'e gidin ve ENTER'a basin.")
            input("[ENTER] -> devam: ")
            bekle(driver, CONFIG["sayfa_bekleme"])
            if hata_sayfasi_mi(driver):
                break

        log.info(f"Sayfa {sayfa} -- {driver.current_url[:80]}")
        kayitlar = sayfa_karti_topla(driver)

        if not kayitlar:
            time.sleep(2)
            kayitlar = sayfa_karti_topla(driver)

        if kayitlar:
            yazilacak = [r for r in kayitlar if r.get("email", "").strip()] if email_zorunlu else kayitlar
            if email_zorunlu and len(yazilacak) < len(kayitlar):
                log.info(f"Email yok, atlanan: {len(kayitlar) - len(yazilacak)}")
            for r in yazilacak:
                csv_yazar.writerow(r)
            toplam += len(yazilacak)
            log.info(f"{len(yazilacak)} kayit yazildi (toplam: {toplam})")
        else:
            log.warning("Kayit bulunamadi.")

        sonraki = sonraki_sayfa_url(driver, sayfa)
        if not sonraki:
            log.info("Son sayfa.")
            break

        while True:
            try:
                driver.get(sonraki)
                bekle(driver, CONFIG["sayfa_bekleme"])
                break
            except Exception as e:
                log.warning(f"Sayfa yuklenemedi, 10sn sonra tekrar: {e}")
                time.sleep(10)
        sayfa += 1

    return toplam


def main():
    log.info("YOK Akademik Scraper basliyor...")
    driver = driver_olustur(CONFIG["headless"])

    email_zorunlu = input("Email olmayan kisiler dahil edilsin mi? (e/h): ").strip().lower() != "e"

    csv_yolu = Path(CONFIG["cikti_csv"])
    mod = input("Yeni baslat (n) / mevcut CSV'ye devam et (d): ").strip().lower()
    if mod == "d":
        csv_dosya = csv_yolu.open("a", newline="", encoding="utf-8-sig")
        csv_yazar = csv.DictWriter(csv_dosya, fieldnames=CSV_SUTUNLAR)
        log.info("Append modu")
    else:
        csv_dosya = csv_yolu.open("w", newline="", encoding="utf-8-sig")
        csv_yazar = csv.DictWriter(csv_dosya, fieldnames=CSV_SUTUNLAR)
        csv_yazar.writeheader()
        log.info("Yeni CSV")

    try:
        driver.get(ANA_URL)
        bekle(driver, CONFIG["sayfa_bekleme"])

        print("\nTarayicida istediginiz bilim alani sayfasina gidin.")
        print("Sayfa yuklendikten sonra ENTER'a basin.")

        toplam_kayit = 0
        while True:
            input("\n[ENTER] -> Bu sayfayi tara (Ctrl+C ile cik): ")
            bekle(driver, CONFIG["sayfa_bekleme"])
            log.info(f"Tarama basliyor: {driver.current_url[:80]}")

            n = alan_tara(driver, csv_yazar, CONFIG["max_sayfa"], email_zorunlu)
            toplam_kayit += n
            log.info(f"Bu alan bitti: {n} kayit")

            devam = input("\nBaska bir alan taramak ister misiniz? (e/h): ").strip().lower()
            if devam != "e":
                break
            print("Yeni alana gidin, hazir olunca ENTER.")

        log.info(f"TAMAM! Toplam {toplam_kayit} kayit -> {csv_yolu.absolute()}")

    except KeyboardInterrupt:
        log.info("Durduruldu.")
    except Exception as e:
        log.exception(f"Hata: {e}")
    finally:
        csv_dosya.close()
        driver.quit()


if __name__ == "__main__":
    main()