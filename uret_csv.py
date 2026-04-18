import csv
import random
import re
import unicodedata
from pathlib import Path

GIRIS_CSV = "akademisyenler.csv"

TR_MAP = str.maketrans(
    "çğıöşüÇĞİÖŞÜ",
    "cgiosуCGIOSU".replace("у", "u")  
)

def tr_temizle(metin: str) -> str:
    metin = metin.translate(TR_MAP)
    metin = unicodedata.normalize("NFKD", metin)
    metin = metin.encode("ascii", "ignore").decode("ascii")
    return metin

def username_uret(ad_soyad: str) -> str:
    temiz = tr_temizle(ad_soyad).lower()
    parcalar = temiz.split()
    return "_".join(parcalar)

def shortname_uret(ad_soyad: str) -> str:
    temiz = tr_temizle(ad_soyad).title().replace(" ", "")
    return f"DemoCourse{temiz}"

def fullname_course_uret(ad_soyad: str) -> str:
    return f"Demo Course {ad_soyad.title()}"

def isim_parcala(ad_soyad: str):
    parcalar = ad_soyad.strip().split()
    if len(parcalar) == 1:
        return parcalar[0].title(), ""
    soyad = parcalar[-1].title()
    isim = " ".join(parcalar[:-1]).title()
    return isim, soyad

import unicodedata as _ud

def _norm(metin: str) -> str:
    metin = _ud.normalize("NFC", metin)
    metin = metin.replace("i\u0307", "i").replace("I\u0307", "I")
    for fr, to in [
        ("İ","I"),("ı","I"),("Ğ","G"),("ğ","G"),
        ("Ş","S"),("ş","S"),("Ü","U"),("ü","U"),
        ("Ö","O"),("ö","O"),("Ç","C"),("ç","C"),
        ("Â","A"),("â","A"),("Î","I"),("î","I"),
        ("Û","U"),("û","U"),
    ]:
        metin = metin.replace(fr, to)
    metin = _ud.normalize("NFD", metin)
    metin = metin.encode("ascii", "ignore").decode("ascii")
    return metin.upper().strip()

_RAW_UNI = [
    ("Abdullah Gül Üniversitesi", "Kayseri"),
    ("Acıbadem Mehmet Ali Aydınlar Üniversitesi", "İstanbul"),
    ("Ada Kent Üniversitesi", "Kıbrıs"),
    ("Adana Alparslan Türkeş Bilim Ve Teknoloji Üniversitesi", "Adana"),
    ("Adıyaman Üniversitesi", "Adıyaman"),
    ("Afyon Kocatepe Üniversitesi", "Afyonkarahisar"),
    ("Afyonkarahisar Sağlık Bilimleri Üniversitesi", "Afyonkarahisar"),
    ("Akdeniz Karpaz Üniversitesi", "Kıbrıs"),
    ("Akdeniz Üniversitesi", "Antalya"),
    ("Aksaray Üniversitesi", "Aksaray"),
    ("Alanya Alaaddin Keykubat Üniversitesi", "Antalya"),
    ("Alanya Üniversitesi", "Antalya"),
    ("Altınbaş Üniversitesi", "İstanbul"),
    ("Amasya Üniversitesi", "Amasya"),
    ("Anadolu Üniversitesi", "Eskişehir"),
    ("Ankara Bilim Üniversitesi", "Ankara"),
    ("Ankara Hacı Bayram Veli Üniversitesi", "Ankara"),
    ("Ankara Medipol Üniversitesi", "Ankara"),
    ("Ankara Müzik Ve Güzel Sanatlar Üniversitesi", "Ankara"),
    ("Ankara Sosyal Bilimler Üniversitesi", "Ankara"),
    ("Ankara Yıldırım Beyazıt Üniversitesi", "Ankara"),
    ("Ankara Üniversitesi", "Ankara"),
    ("Antalya Belek Üniversitesi", "Antalya"),
    ("Antalya Bilim Üniversitesi", "Antalya"),
    ("Ardahan Üniversitesi", "Ardahan"),
    ("Artvin Çoruh Üniversitesi", "Artvin"),
    ("Atatürk Üniversitesi", "Erzurum"),
    ("Ataşehir Adıgüzel Meslek Yüksekokulu", "İstanbul"),
    ("Atılım Üniversitesi", "Ankara"),
    ("Avrasya Üniversitesi", "Trabzon"),
    ("Aydın Adnan Menderes Üniversitesi", "Aydın"),
    ("Ağrı İbrahim Çeçen Üniversitesi", "Ağrı"),
    ("Bahçeşehir Kıbrıs Üniversitesi", "Kıbrıs"),
    ("Bahçeşehir Üniversitesi", "İstanbul"),
    ("Balıkesir Üniversitesi", "Balıkesir"),
    ("Bandırma Onyedi Eylül Üniversitesi", "Balıkesir"),
    ("Bartın Üniversitesi", "Bartın"),
    ("Batman Üniversitesi", "Batman"),
    ("Bayburt Üniversitesi", "Bayburt"),
    ("Başkent Üniversitesi", "Ankara"),
    ("Beykoz Üniversitesi", "İstanbul"),
    ("Bilecik Şeyh Edebali Üniversitesi", "Bilecik"),
    ("Bingöl Üniversitesi", "Bingöl"),
    ("Biruni Üniversitesi", "İstanbul"),
    ("Bitlis Eren Üniversitesi", "Bitlis"),
    ("Bolu Abant İzzet Baysal Üniversitesi", "Bolu"),
    ("Boğaziçi Üniversitesi", "İstanbul"),
    ("Burdur Mehmet Akif Ersoy Üniversitesi", "Burdur"),
    ("Bursa Teknik Üniversitesi", "Bursa"),
    ("Bursa Uludağ Üniversitesi", "Bursa"),
    ("Dicle Üniversitesi", "Diyarbakır"),
    ("Dokuz Eylül Üniversitesi", "İzmir"),
    ("Doğu Akdeniz Üniversitesi", "Kıbrıs"),
    ("Doğuş Üniversitesi", "İstanbul"),
    ("Düzce Üniversitesi", "Düzce"),
    ("Ege Üniversitesi", "İzmir"),
    ("Erciyes Üniversitesi", "Kayseri"),
    ("Erzincan Binali Yıldırım Üniversitesi", "Erzincan"),
    ("Erzurum Teknik Üniversitesi", "Erzurum"),
    ("Eskişehir Osmangazi Üniversitesi", "Eskişehir"),
    ("Eskişehir Teknik Üniversitesi", "Eskişehir"),
    ("Fatih Sultan Mehmet Vakıf Üniversitesi", "İstanbul"),
    ("Fenerbahçe Üniversitesi", "İstanbul"),
    ("Fırat Üniversitesi", "Elazığ"),
    ("Galatasaray Üniversitesi", "İstanbul"),
    ("Gazi Üniversitesi", "Ankara"),
    ("Gaziantep Üniversitesi", "Gaziantep"),
    ("Gaziantep İslam Bilim Ve Teknoloji Üniversitesi", "Gaziantep"),
    ("Gebze Teknik Üniversitesi", "Kocaeli"),
    ("Giresun Üniversitesi", "Giresun"),
    ("Girne Amerikan Üniversitesi", "Kıbrıs"),
    ("Girne Üniversitesi", "Kıbrıs"),
    ("Gümüşhane Üniversitesi", "Gümüşhane"),
    ("Hacettepe Üniversitesi", "Ankara"),
    ("Hakkari Üniversitesi", "Hakkari"),
    ("Haliç Üniversitesi", "İstanbul"),
    ("Harran Üniversitesi", "Şanlıurfa"),
    ("Hasan Kalyoncu Üniversitesi", "Gaziantep"),
    ("Hatay Mustafa Kemal Üniversitesi", "Hatay"),
    ("Hitit Üniversitesi", "Çorum"),
    ("Isparta Uygulamalı Bilimler Üniversitesi", "Isparta"),
    ("Iğdır Üniversitesi", "Iğdır"),
    ("Işık Üniversitesi", "İstanbul"),
    ("Kadir Has Üniversitesi", "İstanbul"),
    ("Kafkas Üniversitesi", "Kars"),
    ("Kahramanmaraş Sütçü İmam Üniversitesi", "Kahramanmaraş"),
    ("Kahramanmaraş İstiklal Üniversitesi", "Kahramanmaraş"),
    ("Kapadokya Üniversitesi", "Nevşehir"),
    ("Karabük Üniversitesi", "Karabük"),
    ("Karadeniz Teknik Üniversitesi", "Trabzon"),
    ("Karamanoğlu Mehmetbey Üniversitesi", "Karaman"),
    ("Kastamonu Üniversitesi", "Kastamonu"),
    ("Kayseri Üniversitesi", "Kayseri"),
    ("Kıbrıs Aydın Üniversitesi", "Kıbrıs"),
    ("Kıbrıs Batı Üniversitesi", "Kıbrıs"),
    ("Kıbrıs İlim Üniversitesi", "Kıbrıs"),
    ("Kırıkkale Üniversitesi", "Kırıkkale"),
    ("Kırklareli Üniversitesi", "Kırklareli"),
    ("Kırşehir Ahi Evran Üniversitesi", "Kırşehir"),
    ("Kilis 7 Aralık Üniversitesi", "Kilis"),
    ("Kocaeli Sağlık Ve Teknoloji Üniversitesi", "Kocaeli"),
    ("Kocaeli Üniversitesi", "Kocaeli"),
    ("Konya Gıda Ve Tarım Üniversitesi", "Konya"),
    ("Konya Teknik Üniversitesi", "Konya"),
    ("Koç Üniversitesi", "İstanbul"),
    ("Kto Karatay Üniversitesi", "Konya"),
    ("Kütahya Dumlupınar Üniversitesi", "Kütahya"),
    ("Kütahya Sağlık Bilimleri Üniversitesi", "Kütahya"),
    ("Lefke Avrupa Üniversitesi", "Kıbrıs"),
    ("Malatya Turgut Özal Üniversitesi", "Malatya"),
    ("Maltepe Üniversitesi", "İstanbul"),
    ("Manisa Celal Bayar Üniversitesi", "Manisa"),
    ("Manisa Celâl Bayar Üniversitesi", "Manisa"),
    ("Mardin Artuklu Üniversitesi", "Mardin"),
    ("Marmara Üniversitesi", "İstanbul"),
    ("Mef Üniversitesi", "İstanbul"),
    ("Mersin Üniversitesi", "Mersin"),
    ("Milli Savunma Üniversitesi", "Ankara"),
    ("Mudanya Üniversitesi", "Bursa"),
    ("Munzur Üniversitesi", "Tunceli"),
    ("Muğla Sıtkı Koçman Üniversitesi", "Muğla"),
    ("Muş Alparslan Üniversitesi", "Muş"),
    ("Necmettin Erbakan Üniversitesi", "Konya"),
    ("Nevşehir Hacı Bektaş Veli Üniversitesi", "Nevşehir"),
    ("Niğde Ömer Halisdemir Üniversitesi", "Niğde"),
    ("Nuh Naci Yazgan Üniversitesi", "Kayseri"),
    ("Ondokuz Mayıs Üniversitesi", "Samsun"),
    ("Ordu Üniversitesi", "Ordu"),
    ("Orta Doğu Teknik Üniversitesi", "Ankara"),
    ("Osmaniye Korkut Ata Üniversitesi", "Osmaniye"),
    ("Ostim Teknik Üniversitesi", "Ankara"),
    ("Pamukkale Üniversitesi", "Denizli"),
    ("Piri Reis Üniversitesi", "İstanbul"),
    ("Recep Tayyip Erdoğan Üniversitesi", "Rize"),
    ("Sabancı Üniversitesi", "İstanbul"),
    ("Sakarya Uygulamalı Bilimler Üniversitesi", "Sakarya"),
    ("Sakarya Üniversitesi", "Sakarya"),
    ("Samsun Üniversitesi", "Samsun"),
    ("Sağlık Bilimleri Üniversitesi", "İstanbul"),
    ("Selçuk Üniversitesi", "Konya"),
    ("Siirt Üniversitesi", "Siirt"),
    ("Sinop Üniversitesi", "Sinop"),
    ("Sivas Bilim Ve Teknoloji Üniversitesi", "Sivas"),
    ("Sivas Cumhuriyet Üniversitesi", "Sivas"),
    ("Süleyman Demirel Üniversitesi", "Isparta"),
    ("Tarsus Üniversitesi", "Mersin"),
    ("Ted Üniversitesi", "Ankara"),
    ("Tekirdağ Namık Kemal Üniversitesi", "Tekirdağ"),
    ("Tobb Ekonomi Ve Teknoloji Üniversitesi", "Ankara"),
    ("Tokat Gaziosmanpaşa Üniversitesi", "Tokat"),
    ("Toros Üniversitesi", "Mersin"),
    ("Trabzon Üniversitesi", "Trabzon"),
    ("Trakya Üniversitesi", "Edirne"),
    ("Türk Alman Üniversitesi", "İstanbul"),
    ("Türk-Alman Üniversitesi", "İstanbul"),
    ("Türk Hava Kurumu Üniversitesi", "Ankara"),
    ("Ufuk Üniversitesi", "Ankara"),
    ("Uluslararası Final Üniversitesi", "Kıbrıs"),
    ("Uluslararası Kıbrıs Üniversitesi", "Kıbrıs"),
    ("Uşak Üniversitesi", "Uşak"),
    ("Van Yüzüncü Yıl Üniversitesi", "Van"),
    ("Yakın Doğu Üniversitesi", "Kıbrıs"),
    ("Yalova Üniversitesi", "Yalova"),
    ("Yaşar Üniversitesi", "İzmir"),
    ("Yeditepe Üniversitesi", "İstanbul"),
    ("Yıldız Teknik Üniversitesi", "İstanbul"),
    ("Yozgat Bozok Üniversitesi", "Yozgat"),
    ("Yüksek İhtisas Üniversitesi", "Ankara"),
    ("Zonguldak Bülent Ecevit Üniversitesi", "Zonguldak"),
    ("Çanakkale Onsekiz Mart Üniversitesi", "Çanakkale"),
    ("Çankaya Üniversitesi", "Ankara"),
    ("Çankırı Karatekin Üniversitesi", "Çankırı"),
    ("Çukurova Üniversitesi", "Adana"),
    ("Özyeğin Üniversitesi", "İstanbul"),
    ("Üsküdar Üniversitesi", "İstanbul"),
    ("İhsan Doğramacı Bilkent Üniversitesi", "Ankara"),
    ("İnönü Üniversitesi", "Malatya"),
    ("İskenderun Teknik Üniversitesi", "Hatay"),
    ("İstanbul 29 Mayıs Üniversitesi", "İstanbul"),
    ("İstanbul Arel Üniversitesi", "İstanbul"),
    ("İstanbul Atlas Üniversitesi", "İstanbul"),
    ("İstanbul Aydın Üniversitesi", "İstanbul"),
    ("İstanbul Beykent Üniversitesi", "İstanbul"),
    ("İstanbul Bilgi Üniversitesi", "İstanbul"),
    ("İstanbul Esenyurt Üniversitesi", "İstanbul"),
    ("İstanbul Galata Üniversitesi", "İstanbul"),
    ("İstanbul Gedik Üniversitesi", "İstanbul"),
    ("İstanbul Gelişim Üniversitesi", "İstanbul"),
    ("İstanbul Kent Üniversitesi", "İstanbul"),
    ("İstanbul Kültür Üniversitesi", "İstanbul"),
    ("İstanbul Medeniyet Üniversitesi", "İstanbul"),
    ("İstanbul Medipol Üniversitesi", "İstanbul"),
    ("İstanbul Nişantaşı Üniversitesi", "İstanbul"),
    ("İstanbul Okan Üniversitesi", "İstanbul"),
    ("İstanbul Rumeli Üniversitesi", "İstanbul"),
    ("İstanbul Sabahattin Zaim Üniversitesi", "İstanbul"),
    ("İstanbul Sağlık Ve Teknoloji Üniversitesi", "İstanbul"),
    ("İstanbul Teknik Üniversitesi", "İstanbul"),
    ("İstanbul Ticaret Üniversitesi", "İstanbul"),
    ("İstanbul Topkapı Üniversitesi", "İstanbul"),
    ("İstanbul Yeni Yüzyıl Üniversitesi", "İstanbul"),
    ("İstanbul Üniversitesi", "İstanbul"),
    ("İstanbul Üniversitesi-Cerrahpaşa", "İstanbul"),
    ("İstinye Üniversitesi", "İstanbul"),
    ("İzmir Bakırçay Üniversitesi", "İzmir"),
    ("İzmir Demokrasi Üniversitesi", "İzmir"),
    ("İzmir Ekonomi Üniversitesi", "İzmir"),
    ("İzmir Katip Çelebi Üniversitesi", "İzmir"),
    ("İzmir Konak Meslek Yüksekokulu", "İzmir"),
    ("İzmir Yüksek Teknoloji Enstitüsü", "İzmir"),
    ("Şırnak Üniversitesi", "Şırnak"),
]

UNI_SEHIR_NORM = {_norm(uni): sehir for uni, sehir in _RAW_UNI}

def sehir_cikar(universite: str) -> str:
    k = _norm(universite)
    if k in UNI_SEHIR_NORM:
        return UNI_SEHIR_NORM[k]
    for tablo_k, sehir in UNI_SEHIR_NORM.items():
        if k in tablo_k or tablo_k in k:
            return sehir
    parcalar = universite.strip().split()
    return parcalar[0] if parcalar else ""

SIFATLAR = [
    "happy","sunny","brave","cool","fast","wise","calm","kind",
    "bold","fair","free","glad","neat","safe","warm","wild",
    "blue","dark","gold","jade","lime","pink","red","soft",
    "crazy","dizzy","fancy","funny","fuzzy","giant","great",
    "icy","jolly","jumpy","lazy","lemon","light","lucky","magic",
    "mighty","misty","noble","odd","orange","pale","proud","quick",
    "quiet","rapid","rusty","shiny","silly","sleek","slim","sly",
    "smart","snowy","spicy","super","sweet","swift","tidy","tiny",
    "tough","tricky","true","ultra","vivid","wacky","witty","zesty",
]
ISIMLER = [
    "fish","bird","leaf","moon","star","wind","wolf","bear",
    "lion","frog","duck","deer","hawk","crab","clam","wasp",
    "rose","tree","rock","lake","hill","rain","snow","seed",
    "ant","bat","bee","bug","cat","cod","cow","doe","dog","eel",
    "elk","fly","fox","gnu","hen","hog","jay","koi","owl","pig",
    "ram","rat","ray","yak","apex","arch","atom","axle","bell",
    "bolt","bone","book","boot","box","bud","cake","cane","cape",
    "card","cave","chip","clay","clip","cloak","cloud","club",
    "coal","coil","coin","cord","core","cork","corn","cove","curl",
    "dart","dawn","dew","dial","dice","disk","dome","door","dot",
    "drum","dune","dust","edge","ember","fame","fern","fire","flag",
    "flame","flare","flask","flint","floor","flow","foam","fold",
    "font","ford","fork","form","fort","frost","gale","gate","gem",
    "glow","glue","gong","grain","grape","grass","grid","gust",
]

def sifre_uret() -> str:
    s = random.choice(SIFATLAR)
    i = random.choice(ISIMLER)
    n = random.randint(10, 99)
    return f"{s}{i}{n}"

def main():
    giris = Path(GIRIS_CSV)
    if not giris.exists():
        print(f"HATA: {GIRIS_CSV} bulunamadi!")
        return

    satirlar = []
    with open(giris, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            satirlar.append(row)

    print(f"{len(satirlar)} kayit okundu.")

    goruldu_email = set()
    goruldu_username = set()

    courses_satirlar = []
    enrollment_satirlar = []
    profs_satirlar = []

    atlanan = 0
    for row in satirlar:
        email = row.get("email", "").strip()
        ad_soyad = row.get("ad_soyad", "").strip()

        if not ad_soyad:
            atlanan += 1
            continue

        if email and email in goruldu_email:
            print(f"  ATLANDI (duplicate email): {ad_soyad} <{email}>")
            atlanan += 1
            continue
        if email:
            goruldu_email.add(email)

        base_username = username_uret(ad_soyad)
        username = base_username
        sayac = 2
        while username in goruldu_username:
            username = f"{base_username}{sayac}"
            sayac += 1
        goruldu_username.add(username)

        sifre = sifre_uret()
        shortname = shortname_uret(ad_soyad)
        fullname_course = fullname_course_uret(ad_soyad)
        isim, soyad = isim_parcala(ad_soyad)
        sehir = sehir_cikar(row.get("universite", ""))
        unvan = row.get("unvan", "").strip()
        universite = row.get("universite", "").strip()
        fakulte = row.get("fakulte", "").strip()
        bolum = row.get("bolum", "").strip()

        courses_satirlar.append({
            "fullname": fullname_course,
            "shortname": shortname,
            "category": 24,
            "templatecourse": "MasterDemoCourse",
        })

        enrollment_satirlar.append({
            "username": username,
            "firstname": isim,
            "lastname": soyad,
            "email": email,
            "course1": shortname,
            "role1": "editingteacher",
            "course2": shortname,
            "role2": "student",
            "country": "TR",
            "city": sehir,
            "institution": universite,
            "profile_field_faculty": fakulte,
            "department": bolum,
            "profile_field_credit_balance": 1000,
            "password": sifre,
            "emailstop": 1,
            "profile_field_title": unvan,
        })

        fullname_prof = f"{unvan} {ad_soyad.title()}".strip()
        profs_satirlar.append({
            "username": username,
            "email": email,
            "fullname": fullname_prof,
            "temp_password": sifre,
            "lang_preference": "TR",
            "country": "Türkiye",
            "city": sehir,
            "university": universite,
            "faculty": fakulte,
            "department": bolum,
        })

    with open("courses.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["fullname","shortname","category","templatecourse"])
        w.writeheader()
        w.writerows(courses_satirlar)

    with open("UserCreationAndEnrollment.csv", "w", newline="", encoding="utf-8-sig") as f:
        fields = ["username","firstname","lastname","email","course1","role1",
                  "course2","role2","country","city","institution",
                  "profile_field_faculty","department","profile_field_credit_balance",
                  "password","emailstop","profile_field_title"]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(enrollment_satirlar)

    with open("profs.csv", "w", newline="", encoding="utf-8-sig") as f:
        fields = ["username","email","fullname","temp_password","lang_preference",
                  "country","city","university","faculty","department"]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(profs_satirlar)

    print(f"\nTamamlandi!")
    print(f"  Yazilan : {len(courses_satirlar)} kayit")
    print(f"  Atlanan : {atlanan}")
    print(f"  -> courses.csv")
    print(f"  -> UserCreationAndEnrollment.csv")
    print(f"  -> profs.csv")

if __name__ == "__main__":
    main()