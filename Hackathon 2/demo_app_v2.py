import streamlit as st
import folium
from streamlit_folium import st_folium
import openrouteservice
import pandas as pd
import joblib
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
from flask import Flask, render_template, jsonify, request, send_from_directory


demo_app = Flask(__name__)

@demo_app.route('/demo')
def demo_page():
    return render_template('demo.html')

# 🔁 Modeli yükle
model = joblib.load("/Users/behra/Desktop/hackathonyeni/Hackathon/model.pkl")

# 🌍 Streamlit ayarları
st.set_page_config(layout="wide")
st.title("🛡️ GüvenliRota AI – Rotalı Risk Analizi")
st.markdown("Haritada başlangıç ve bitiş noktası seç, AI sana rota üzerindeki riskli bölgeleri göstersin.")

# 🚀 Kullanıcıdan ek veriler (sidebar)
st.sidebar.header("🔍 Risk Tahmin Parametreleri")
kamera_var = st.sidebar.selectbox("Kamera Var mı?", [0, 1], index=1)
isik_var = st.sidebar.selectbox("Işık Var mı?", [0, 1], index=1)
durak_uzakligi_m = st.sidebar.slider("Durak Uzaklığı (m)", 0, 500, 150)
sokak_tipi_label = st.sidebar.selectbox("Sokak Tipi", ["cadde", "tenha", "ara"])
zaman_dilimi_label = st.sidebar.selectbox("Zaman Dilimi", ["sabah", "öğle", "akşam", "gece"])
hafta_gunu_label = st.sidebar.selectbox("Gün", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])

# 🔢 Encode işlemleri
sokak_tipi = {"cadde": 0, "tenha": 1, "ara": 2}[sokak_tipi_label]
zaman_dilimi = {"sabah": 0, "öğle": 1, "akşam": 2, "gece": 3}[zaman_dilimi_label]
hafta_gunu = {"Monday": 0, "Tuesday": 1, "Wednesday": 2,
              "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6}[hafta_gunu_label]

# 🔁 Oturum bilgisi
if "start_point" not in st.session_state:
    st.session_state.start_point = None
if "end_point" not in st.session_state:
    st.session_state.end_point = None

# 🗺️ Harita oluştur
m = folium.Map(location=[37.7648, 30.5563], zoom_start=14)
m.add_child(folium.LatLngPopup())

# 📌 Legend kutusu (açıklama)
legend_html = '''
     <div style="
     position: fixed;
     bottom: 50px;
     left: 50px;
     width: 200px;
     height: 90px;
     background-color: white;
     border:2px solid grey;
     z-index:9999;
     font-size:14px;
     padding: 10px;
     ">
     <b>🔍 Rota Risk Seviyeleri</b><br>
     <i style="color:green;">🟢 Güvenli</i><br>
     <i style="color:orange;">🟠 Orta Risk</i><br>
     <i style="color:red;">🔴 Tehlikeli</i>
     </div>
'''
m.get_root().html.add_child(folium.Element(legend_html))

# 📍 Harita tıklama işlemi
st.markdown("📍 Haritadan iki nokta seç: ilk tıklama → Başlangıç, ikinci tıklama → Varış")
st_data = st_folium(m, width=1000, height=600)

if st_data and st_data.get("last_clicked"):
    clicked = st_data["last_clicked"]
    latlng = (clicked["lat"], clicked["lng"])
    if not st.session_state.start_point:
        st.session_state.start_point = latlng
    elif not st.session_state.end_point:
        st.session_state.end_point = latlng

# 📌 İşaretler
if st.session_state.start_point:
    folium.Marker(st.session_state.start_point, popup="Başlangıç", icon=folium.Icon(color="green")).add_to(m)
if st.session_state.end_point:
    folium.Marker(st.session_state.end_point, popup="Varış", icon=folium.Icon(color="red")).add_to(m)

# 🚦 Rota ve risk analizi
if st.session_state.start_point and st.session_state.end_point:
    coords = [
        (st.session_state.start_point[1], st.session_state.start_point[0]),
        (st.session_state.end_point[1], st.session_state.end_point[0])
    ]
    try:
        client = openrouteservice.Client(key="5b3ce3597851110001cf6248318d7dddac82470286da3307a86266db")
        route = client.directions(coords, profile='foot-walking', format='geojson')
        coordinates = route["features"][0]["geometry"]["coordinates"]

        # Her 5. noktada risk tahmini
        risk_scores = []
        for i, point in enumerate(coordinates[::5]):
            lon, lat = point
            df = pd.DataFrame([{
                "lat": lat,
                "lon": lon,
                "kamera_var": kamera_var,
                "isik_var": isik_var,
                "durak_uzakligi_m": durak_uzakligi_m,
                "sokak_tipi_encoded": sokak_tipi,
                "zaman_dilimi_encoded": zaman_dilimi,
                "hafta_gunu_encoded": hafta_gunu
            }])
            risk = model.predict(df)[0]
            risk_scores.append(risk)

        # Ortalama risk hesapla
        ortalama_risk = round(sum(risk_scores) / len(risk_scores)) if risk_scores else 0
        renk = {0: "green", 1: "orange", 2: "red"}[ortalama_risk]

        # Rota çizimi
        folium.PolyLine(
            locations=[(lat, lon) for lon, lat in coordinates],
            color=renk,
            weight=8,
            opacity=0.8,
            tooltip=f"Rota Riski: {'Güvenli' if ortalama_risk==0 else 'Orta Risk' if ortalama_risk==1 else 'Tehlikeli'}"
        ).add_to(m)

        st.success(f"✅ Rota oluşturuldu. Ortalama Risk: {['Güvenli', 'Orta Risk', 'Tehlikeli'][ortalama_risk]}")
    except Exception as e:
        st.error(f"🚫 Rota alınamadı: {e}")

    st_folium(m, width=1000, height=600)

# 🔄 Reset butonu
if st.sidebar.button("Sıfırla"):
    st.session_state.start_point = None
    st.session_state.end_point = None
    st.experimental_rerun()
