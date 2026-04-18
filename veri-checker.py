import pandas as pd

# Dosya listesi
dosyalar = ['dosya1.csv', 'dosya2.csv', 'dosya3.csv', 'dosya4.csv','dosya5.csv']

liste = []

for dosya in dosyalar:
    # Dosyayı oku (sütun adının 'email' olduğunu varsayıyoruz)
    df = pd.read_csv(dosya)
    
    # Sadece email sütununu al ve temizle
    # strip() boşlukları siler, lower() küçük harf yapar
    df['email'] = df['email'].astype(str).str.strip().str.lower()
    
    # Hangi dosyadan geldiğini not et
    df['kaynak'] = dosya
    
    # Sadece ilgili sütunları listeye ekle
    liste.append(df[['email', 'kaynak']])

# Tüm verileri birleştir
tum_mailler = pd.concat(liste, ignore_index=True)

# Yinelenenleri bul (keep=False tüm kopyaları gösterir)
tekrarlar = tum_mailler[tum_mailler.duplicated(subset=['email'], keep=False)]

if tekrarlar.empty:
    print("Harika! Tüm dosyalardaki e-postalar benzersiz.")
else:
    print("Aşağıdaki e-postalar birden fazla kez veya farklı dosyalarda bulunuyor:")
    # E-postaya göre sıralayarak yan yana görmeyi sağla
    print(tekrarlar.sort_values(by='email'))

# İsterseniz bu listeyi Excel olarak kaydedebilirsiniz
# tekrarlar.to_excel("tekrarlanan_mailler.xlsx", index=False)