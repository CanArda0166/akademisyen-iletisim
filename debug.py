import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import re
from webdriver_manager.chrome import ChromeDriverManager

opt = webdriver.ChromeOptions()
opt.add_argument("--window-size=1920,1080")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opt)

driver.get("https://akademik.yok.gov.tr/AkademikArama/")
time.sleep(3)

print("Bilgisayar Muhendisligi sayfasina gidin, sonra ENTER.")
input("[ENTER]: ")
time.sleep(2)

html = driver.find_element(By.TAG_NAME, "body").get_attribute("innerHTML")
soup = BeautifulSoup(html, "html.parser")

profil_pattern = re.compile(r"AkademisyenGorevOgrenimBilgileri")
goruldu = set()
kart_sayisi = 0

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

    print(f"\n{'='*60}")
    print(f"ISIM: {isim}")
    print(f"KONTEYNER TAG: {kap.name if kap else 'None'}, CLASS: {kap.get('class') if kap else ''}")
    print("--- HAM HTML (ilk 1500 karakter) ---")
    print(str(kap)[:1500] if kap else "YOK")

    kart_sayisi += 1
    if kart_sayisi >= 3:
        break

driver.quit()