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


