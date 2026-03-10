import csv
import time
import re
import logging
import sys
from pathlib import Path
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ============================================================
CONFIG = {
    "cikti_csv": "akademisyenler.csv",
    "headless": False,
    "sayfa_bekleme": 1.5,   # Dusuk tut: session timeout geciktirmek icin
    "max_sayfa": 9999,
}

ANA_URL = "https://akademik.yok.gov.tr/AkademikArama/"

UNVAN_LISTESI = [
    "Prof. Dr.",
    "Do\u00e7. Dr.",         # Doç. Dr.
    "Dr. \u00d6\u011fr. \u00dcyesi",  # Dr. Öğr. Üyesi
    "Ar\u015f. G\u00f6r. Dr.",        # Arş. Gör. Dr.
    "Ar\u015f. G\u00f6r.",            # Arş. Gör.
    "\u00d6\u011fr. G\u00f6r. Dr.",   # Öğr. Gör. Dr.
    "\u00d6\u011fr. G\u00f6r.",       # Öğr. Gör.
    "Uzman Dr.",
    "Uzman",
    "Prof.",
    "Do\u00e7.",              # Doç.
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


def driver_olustur(headless):
    opt = webdriver.ChromeOptions()
    if headless:
        opt.add_argument("--headless=new")
    opt.add_argument("--no-sandbox")
    opt.add_argument("--disable-dev-shm-usage")
    opt.add_argument("--window-size=1920,1080")
    opt.add_argument("--lang=tr")
    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=opt
    )


def bekle(driver, saniye):
    try:
        WebDriverWait(driver, 15).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
    except Exception:
        pass
    time.sleep(saniye)


def hata_sayfasi_mi(driver):
    """Sunucu session hatasi sayfasini dondurduysa True."""
    try:
        metin = driver.find_element(By.TAG_NAME, "body").text
        return "zg\u00fcn\u00fcz" in metin or "zaman a\u015f\u0131m\u0131" in metin
    except Exception:
        return False


def kart_parse_et(kart_html, bilim_alani):
    soup = BeautifulSoup(kart_html, "html.parser")

    email = ""
    for a in soup.find_all("a", href=True):
        if a["href"].startswith("mailto:"):
            email = a["href"][7:].strip()
            break

    ad_soyad = ""
    for a in soup.find_all("a", href=True):
        if "AkademisyenGorevOgrenimBilgileri" in a["href"] and a.get_text(strip=True):
            ad_soyad = a.get_text(strip=True)
            break

    if not ad_soyad:
        return None
    unvan = ""
    h4 = soup.find("h4")
    if h4:
        onceki = h4.find_previous_sibling("h6")
        if onceki:
            ham = onceki.get_text(strip=True).upper()
            if "PROF" in ham and "DR" in ham:
                unvan = "Prof. Dr."
            elif "DOÇ" in ham or ("DOC" in ham and "DR" in ham):
                unvan = "Doç. Dr."
            elif "ÖĞR" in ham or "OGR" in ham:
                if "DR" in ham:
                    unvan = "Dr. Öğr. Üyesi"
                else:
                    unvan = "Öğr. Gör."
            elif "ARAŞ" in ham or "ARS" in ham:
                if "DR" in ham:
                    unvan = "Arş. Gör. Dr."
                else:
                    unvan = "Arş. Gör."
            elif "UZMAN" in ham:
                unvan = "Uzman"
            elif "PROF" in ham:
                unvan = "Prof. Dr."
            else:
                unvan = onceki.get_text(strip=True).title()

    return {"bolum": bilim_alani, "unvan": unvan, "ad_soyad": ad_soyad, "email": email}

def sayfa_karti_topla(driver, bilim_alani):
    html = driver.find_element(By.TAG_NAME, "body").get_attribute("innerHTML")
    soup = BeautifulSoup(html, "html.parser")
    kartlar = []
    profil_pattern = re.compile(r"AkademisyenGorevOgrenimBilgileri")
    goruldu = set()
    for link in soup.find_all("a", href=profil_pattern):
        isim = link.get_text(strip=True)
        if not isim or isim in goruldu:
            continue
        goruldu.add(isim)
        kap = link.parent
        for _ in range(8):
            if kap is None:
                break
            if kap.find("a", href=re.compile(r"^mailto:")):
                break
            kap = kap.parent

        if kap:
            sonuc = kart_parse_et(str(kap), bilim_alani)
            if sonuc:
                kartlar.append(sonuc)
    return kartlar
def sonraki_sayfa_url(driver, mevcut_sayfa):
    try:
        linkler = driver.find_elements(
            By.XPATH, "//ul[contains(@class,'pagination')]//a"
        )
        for link in linkler:
            if link.text.strip() == str(mevcut_sayfa + 1):
                return link.get_attribute("href")
        for link in linkler:
            t = link.text.strip()
            if t in ("\u00bb", ">>", ">", "Next", "Sonraki"):
                return link.get_attribute("href")
    except Exception:
        pass
    return None


def alan_tara(driver, bilim_alani, csv_yazar, max_sayfa):
    toplam = 0
    sayfa = 1

    while sayfa <= max_sayfa:
        if hata_sayfasi_mi(driver):
            log.warning(f"  SESSION HATASI! Sayfa {sayfa} yuklenemedi.")
            print(f"\n{'='*60}")
            print(f"Sunucu session timeout! Tarayicida sayfa {sayfa}'e gidin:")
            print("  1) Anasayfaya gidin")
            print("  2) Muhendislik > Bilgisayar linkine tiklayin")
            print(f"  3) Sayfalamadan {sayfa}. sayfaya gidin")
            print("Hazir olunca ENTER'a basin.")
            input("[ENTER] -> devam: ")
            bekle(driver, CONFIG["sayfa_bekleme"])
            if hata_sayfasi_mi(driver):
                log.error("Hala hata sayfasi, atlaniyor.")
                break

        log.info(f"  Sayfa {sayfa} -- {driver.current_url[:80]}")
        kayitlar = sayfa_karti_topla(driver, bilim_alani)

        if not kayitlar:
            time.sleep(2)
            kayitlar = sayfa_karti_topla(driver, bilim_alani)

        if not kayitlar:
            log.warning("  Kayit bulunamadi, atlaniyor.")
        else:
            for r in kayitlar:
                csv_yazar.writerow(r)
            toplam += len(kayitlar)
            log.info(f"  --> {len(kayitlar)} kayit (toplam: {toplam})")

        sonraki = sonraki_sayfa_url(driver, sayfa)
        if not sonraki:
            log.info("  Son sayfa.")
            break

        driver.get(sonraki)
        bekle(driver, CONFIG["sayfa_bekleme"])
        sayfa += 1

    return toplam
def main():
    log.info("YOK Akademik Scraper v4 basliyor...")
    driver = driver_olustur(CONFIG["headless"])

    csv_yolu = Path(CONFIG["cikti_csv"])

    mod = input("Yeni baslat (n) mi, yoksa mevcut CSV'ye devam et (d) mi? [n/d]: ").strip().lower()
    if mod == "d":
        csv_dosya = csv_yolu.open("a", newline="", encoding="utf-8-sig")
        csv_yazar = csv.DictWriter(csv_dosya, fieldnames=["bolum", "unvan", "ad_soyad", "email"])
        log.info("Mevcut CSV'ye ekleniyor (append modu)")
    else:
        csv_dosya = csv_yolu.open("w", newline="", encoding="utf-8-sig")
        csv_yazar = csv.DictWriter(csv_dosya, fieldnames=["bolum", "unvan", "ad_soyad", "email"])
        csv_yazar.writeheader()
        log.info("Yeni CSV olusturuluyor")

    try:
        driver.get(ANA_URL)
        bekle(driver, CONFIG["sayfa_bekleme"])
        log.info(f"Ana sayfa: {driver.current_url}")

        print(f"\n{'='*60}")
        print("ADIM 1: Tarayicida 'Muhendislik' linkine tiklayin.")
        input("ENTER -> Muhendislik sayfasi hazir: ")
        bekle(driver, CONFIG["sayfa_bekleme"])

        try:
            adet = int(input("Kac bilim alani taranacak? [1]: ").strip() or "1")
        except ValueError:
            adet = 1

        toplam_kayit = 0
        for i in range(adet):
            if i > 0:
                print("\nMuhendislik sayfasina geri donun ve sonraki alani secin.")
                input("ENTER -> hazir: ")
                bekle(driver, CONFIG["sayfa_bekleme"])

            alan_adi = input(f"\nAlan {i+1} CSV'de ne yazsin? Ornek: Bilgisayar Muhendisligi\n> ").strip()
            if not alan_adi:
                alan_adi = f"Alan_{i+1}"

            print(f"Tarayicida ilgili bilim alani linkine tiklayin.")
            input("ENTER -> bilim alani sayfasi hazir: ")
            bekle(driver, CONFIG["sayfa_bekleme"])
            log.info(f"Tarama basliyor: {driver.current_url[:80]}")

            n = alan_tara(driver, alan_adi, csv_yazar, CONFIG["max_sayfa"])
            toplam_kayit += n
            log.info(f"OK '{alan_adi}' bitti: {n} kayit")

        print(f"\n{'='*60}")
        log.info(f"TAMAMLANDI! Toplam {toplam_kayit} kayit -> {csv_yolu.absolute()}")

    except KeyboardInterrupt:
        log.info("Kullanici durdurdu.")
    except Exception as e:
        log.exception(f"Hata: {e}")
    finally:
        csv_dosya.close()
        driver.quit()


if __name__ == "__main__":
    main()