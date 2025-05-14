import pandas as pd

# API URL (tarihi güncel tut!)
url = "https://data.cityofchicago.org/resource/ijzp-q8t2.json?$where=date>'2024-05-01T00:00:00.000'&$limit=1000"


# API'den JSON oku
df = pd.read_json(url)

# İlk 5 satırı göster
print(df.head())

# CSV olarak kaydet
df.to_csv('Crimes_Last_7_Days.csv', index=False)

print("Son 7 gün verisi 'Crimes_Last_7_Days.csv' dosyasına kaydedildi!")
