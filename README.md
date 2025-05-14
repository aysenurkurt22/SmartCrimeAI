# 🧠 SmartCrimeAI – AI Tabanlı Suç Haritası ve Rota Risk Analizi

SmartCrimeAI, Chicago Polis Departmanı'nın son 7 günlük suç verilerini kullanarak suç noktalarını harita üzerinde işaretleyen ve kullanıcıların belirlediği rotalara göre yapay zekâ destekli risk analizi yapan bir şehir güvenliği uygulamasıdır. Uygulama, rota üzerindeki riskli bölgeleri renklendirir ve güvenli alternatifler sunar. Makine öğrenmesi tabanlı model ile rota boyunca karşılaşılabilecek suç riski tahminlenir.

## 🚀 Özellikler

- 🗺️ Suç noktalarını interaktif haritada gösterir  
- 🚦 Rotaları risk düzeyine göre renklendirir (yeşil, sarı, kırmızı)  
- 🤖 ML modeliyle rota üzerindeki risk skorunu tahmin eder (`model.pkl`)  
- 📊 Tutuklama oranı, saatlik yoğunluk, suç türü gibi analiz grafiklerini sunar  
- 📁 Son 7 güne ait veriyi CSV formatında işler ve günceller

## 🛠️ Kullanılan Teknolojiler

- Python (Flask)
- Pandas, NumPy, Scikit-learn
- Folium, OpenRouteService API
- HTML + Jinja2 (şablonlama)
- JSON, CSV dosya yönetimi

## 📁 Proje Yapısı

Hackathon/
├── app.py                  # Flask sunucusunu başlatan ana dosya
├── smartcrimeai_pipeline.py  # Rota risk analizi ve harita işlemlerini yürüten ana modül
├── model.pkl              # Eğitilmiş makine öğrenmesi modeli (risk tahmini için)
├── Crimes_Last_7_Days.csv # Chicago'nun son 7 güne ait suç verileri
├── get_last7days.py       # Dış veri kaynağından son suç kayıtlarını çeken yardımcı betik
├── templates/             # HTML tabanlı kullanıcı arayüz şablonları (Jinja2 ile çalışır)
├── static/                # CSS, JavaScript ve görsel dosyaları
├── arrest_trend.png       # Tutuklama eğilimlerini gösteren grafik
├── crime_types.png        # Suç türü dağılım grafiği
├── hourly_arrest_rate.png # Saatlik suç yoğunluğu grafiği



