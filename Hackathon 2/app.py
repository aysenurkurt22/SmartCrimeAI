from flask import Flask, render_template, jsonify, request, send_from_directory
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import openrouteservice
from openrouteservice import convert

# Flask uygulaması
app = Flask(__name__)

# Dash uygulaması
dash_app = dash.Dash(__name__, server=app, url_base_pathname='/dashboard/')

# Veri yükleme
def load_data():
    df = pd.read_csv('Crimes_Last_7_Days.csv')
    df['DATE'] = pd.to_datetime(df['date'])
    df['HOUR'] = pd.to_datetime(df['date']).dt.hour
    return df

df = load_data()

# Favori bölgeler (demo için dosyada tutuluyor)
FAVORITES_FILE = 'favorites.json'
def load_favorites():
    try:
        with open(FAVORITES_FILE, 'r') as f:
            return json.load(f)
    except:
        return []
def save_favorites(favs):
    with open(FAVORITES_FILE, 'w') as f:
        json.dump(favs, f)

# Örnek mahalle listesi (isim ve merkez koordinat)
MAHALLELER = [
    {"isim": "Avondale", "lat": 41.9414, "lon": -87.7028},
    {"isim": "Lincoln Park", "lat": 41.9214, "lon": -87.6513},
    {"isim": "Hyde Park", "lat": 41.7943, "lon": -87.5907},
    {"isim": "Englewood", "lat": 41.7754, "lon": -87.6417},
    {"isim": "Loop", "lat": 41.8837, "lon": -87.6325},
    {"isim": "Lake View", "lat": 41.9417, "lon": -87.6536},
    {"isim": "West Town", "lat": 41.8917, "lon": -87.6722},
    {"isim": "Wicker Park", "lat": 41.9087, "lon": -87.6776},
    {"isim": "Bucktown", "lat": 41.9217, "lon": -87.6803},
    {"isim": "Logan Square", "lat": 41.9234, "lon": -87.7092},
    {"isim": "River North", "lat": 41.8927, "lon": -87.6340},
    {"isim": "Gold Coast", "lat": 41.9094, "lon": -87.6277},
    {"isim": "Old Town", "lat": 41.9117, "lon": -87.6378},
    {"isim": "Wrigleyville", "lat": 41.9491, "lon": -87.6567},
    {"isim": "Andersonville", "lat": 41.9796, "lon": -87.6695}
]

# Harita (tıklanabilir, mahalle merkezleri de marker olarak)
map_fig = go.Figure()
map_fig.add_trace(go.Scattermapbox(
    lat=df['latitude'],
    lon=df['longitude'],
    mode='markers',
    marker=dict(size=2, color='red', opacity=0.2),
    text=df['primary_type'],
    hoverinfo='text',
    name='Suç Noktaları'))
map_fig.add_trace(go.Scattermapbox(
    lat=[m['lat'] for m in MAHALLELER],
    lon=[m['lon'] for m in MAHALLELER],
    mode='markers+text',
    marker=dict(size=14, color='blue'),
    text=[m['isim'] for m in MAHALLELER],
    textposition='top right',
    name='Mahalleler'))
map_fig.update_layout(
    mapbox=dict(
        style="open-street-map",
        center=dict(lat=df['latitude'].mean(), lon=df['longitude'].mean()),
        zoom=10
    ),
    margin={"r":0,"t":30,"l":0,"b":0},
    title='Bölge Seçmek için Haritaya Tıklayın veya Mahalle Seçin'
)

# Ana sayfa
@app.route('/')
def home():
    return render_template('index.html')

# API endpoint'leri
@app.route('/api/crime_stats')
def crime_stats():
    try:
        stats = {
            'total_crimes': int(len(df)),
            'arrest_rate': float(df['arrest'].mean()),
            'crime_types': df['primary_type'].value_counts().head(10).to_dict(),
            'hourly_distribution': df.groupby('HOUR')['arrest'].mean().to_dict()
        }
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ORS client
ORS_API_KEY = "5b3ce3597851110001cf6248c0ed247f8d8d4788b91ddb7ac77b2f3a"
ors_client = openrouteservice.Client(key=ORS_API_KEY)

# --- Rota haritası için başlangıçta boş ve tıklama ile seçim ---
# Chicago sınırları için geniş bir grid oluştur
import numpy as np
lat_grid = np.linspace(df['latitude'].min(), df['latitude'].max(), 50)
lon_grid = np.linspace(df['longitude'].min(), df['longitude'].max(), 50)
mesh_lat, mesh_lon = np.meshgrid(lat_grid, lon_grid)
transparent_points_lat = mesh_lat.flatten()
transparent_points_lon = mesh_lon.flatten()

initial_map = go.Figure()
# Suç noktaları
initial_map.add_trace(go.Scattermapbox(
    lat=df['latitude'],
    lon=df['longitude'],
    mode='markers',
    marker=dict(size=2, color='red', opacity=0.2),
    text=df['primary_type'],
    hoverinfo='text',
    name='Suç Noktaları'))
# Şeffaf grid (tüm harita tıklanabilir olsun diye)
initial_map.add_trace(go.Scattermapbox(
    lat=transparent_points_lat,
    lon=transparent_points_lon,
    mode='markers',
    marker=dict(size=15, color='rgba(0,0,0,0)'),
    hoverinfo='none',
    name='Tıklanabilir Grid',
    showlegend=False
))
initial_map.update_layout(
    mapbox=dict(
        style="open-street-map",
        center=dict(lat=df['latitude'].mean(), lon=df['longitude'].mean()),
        zoom=10
    ),
    margin={"r":0,"t":30,"l":0,"b":0},
    title='Başlangıç ve Varış Noktalarını Seçin'
)

# --- Kişiselleştirilmiş tavsiye callback'i ---
@dash_app.callback(
    Output('advice-msg', 'children'),
    Input('get-advice-btn', 'n_clicks'),
    State('advice-mahalle', 'value'),
    State('advice-hour', 'value')
)
def get_advice(n_clicks, mahalle_idx, hour):
    if n_clicks == 0 or mahalle_idx is None or hour is None:
        return ''
    
    m = MAHALLELER[mahalle_idx]
    lat, lon = m['lat'], m['lon']
    
    crimes_near = df[((df['latitude'] - lat).abs() < 0.01) & ((df['longitude'] - lon).abs() < 0.01) & (df['HOUR'] == hour)]
    total = len(crimes_near)
    
    if total == 0:
        return f"{m['isim']} bölgesinde saat {hour}:00 civarında son 7 günde suç kaydı yok. Görece güvenli."
    
    top_type = crimes_near['primary_type'].value_counts().idxmax()
    return f"{m['isim']} bölgesinde saat {hour}:00 civarında {total} suç işlendi. En sık görülen suç: {top_type}. Dikkatli olun!"


# crime_map.html dosyasını sunmak için route ekle
@app.route('/crime_map.html')
def serve_crime_map():
    return send_from_directory('static', 'crime_map.html')

# Dash layout (sade, sadece suç haritası ve analizler)
dash_app.layout = html.Div([
    html.Div([
        html.H1('Suç Analiz Dashboard', style={
            'textAlign': 'center',
            'color': '#1a237e',
            'fontFamily': 'Poppins, sans-serif',
            'fontWeight': '700',
            'marginBottom': '30px'
        }),
        html.Div([
            html.A('Ana Sayfaya Dön', href='/', style={
                'display': 'inline-block',
                'padding': '10px 20px',
                'backgroundColor': '#1a237e',
                'color': 'white',
                'textDecoration': 'none',
                'borderRadius': '5px',
                'marginBottom': '20px'
            })
        ], style={'textAlign': 'center'})
    ], style={'padding': '20px', 'backgroundColor': 'white', 'borderRadius': '10px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'}),
    
    # Navigasyon Bölümü
    html.Div([
        html.H2('Güvenli Rota Planlayıcı', style={
            'textAlign': 'center',
            'color': '#1a237e',
            'fontFamily': 'Poppins, sans-serif',
            'fontWeight': '600',
            'marginBottom': '20px'
        }),
        html.Div([
            html.Div([
                html.H4('Başlangıç Mahallesi', style={'fontFamily': 'Poppins, sans-serif', 'fontWeight': '500'}),
                dcc.Dropdown(
                    id='start-mahalle',
                    options=[{'label': m['isim'], 'value': i} for i, m in enumerate(MAHALLELER)],
                    placeholder='Başlangıç mahallesini seçin',
                    style={'width': '100%', 'marginBottom': '20px'}
                ),
            ], style={'marginBottom': '20px'}),
            html.Div([
                html.H4('Varış Mahallesi', style={'fontFamily': 'Poppins, sans-serif', 'fontWeight': '500'}),
                dcc.Dropdown(
                    id='end-mahalle',
                    options=[{'label': m['isim'], 'value': i} for i, m in enumerate(MAHALLELER)],
                    placeholder='Varış mahallesini seçin',
                    style={'width': '100%', 'marginBottom': '20px'}
                ),
            ], style={'marginBottom': '20px'}),
            html.Button('Rota Hesapla', id='calculate-route-btn', n_clicks=0, style={
                'padding': '10px 20px',
                'backgroundColor': '#1a237e',
                'color': 'white',
                'border': 'none',
                'borderRadius': '5px',
                'cursor': 'pointer',
                'width': '100%'
            }),
            html.Div(id='route-info', style={'marginTop': '20px', 'fontFamily': 'Poppins, sans-serif'})
        ], style={'padding': '20px', 'backgroundColor': 'white', 'borderRadius': '10px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'})
    ], style={'marginTop': '20px', 'marginBottom': '20px'}),
    
    # Harita
    html.Div([
        dcc.Graph(id='route-map', figure=initial_map, config={'scrollZoom': True}, style={'height': '500px'}),
    ], style={'backgroundColor': 'white', 'borderRadius': '10px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.1)', 'padding': '20px'}),
    
    html.Div([
        html.Div([
            html.Label('Mahalle Seç:', style={'fontFamily': 'Poppins, sans-serif', 'fontWeight': '500'}),
            dcc.Dropdown(
                id='mahalle-dropdown',
                options=[{'label': m['isim'], 'value': i} for i, m in enumerate(MAHALLELER)],
                placeholder='Mahalle seçin',
                style={'width': '40%', 'display': 'inline-block', 'marginRight': '20px'}
            ),
            html.Span('veya', style={'marginRight': '20px', 'fontFamily': 'Poppins, sans-serif'}),
            html.Label('Koordinatlar:', style={'fontFamily': 'Poppins, sans-serif', 'fontWeight': '500'}),
            dcc.Input(id='fav-lat', type='number', placeholder='Enlem', style={'width': '15%', 'padding': '8px', 'borderRadius': '5px', 'border': '1px solid #ddd'}),
            dcc.Input(id='fav-lon', type='number', placeholder='Boylam', style={'width': '15%', 'marginLeft': '10px', 'padding': '8px', 'borderRadius': '5px', 'border': '1px solid #ddd'}),
        ], style={'textAlign': 'center', 'marginBottom': '20px', 'marginTop': '10px', 'backgroundColor': 'white', 'borderRadius': '10px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.1)', 'padding': '20px'})
    ]),
    
    html.Div([
        html.Div([
            html.Label('E-posta:', style={'marginLeft': '20px', 'fontFamily': 'Poppins, sans-serif', 'fontWeight': '500'}),
            dcc.Input(id='fav-email', type='email', placeholder='mail@ornek.com', style={'width': '30%', 'padding': '8px', 'borderRadius': '5px', 'border': '1px solid #ddd'}),
            html.Button('Favori Ekle', id='add-fav-btn', n_clicks=0, style={
                'marginLeft': '20px',
                'padding': '8px 20px',
                'backgroundColor': '#1a237e',
                'color': 'white',
                'border': 'none',
                'borderRadius': '5px',
                'cursor': 'pointer'
            }),
            html.Div(id='fav-add-msg', style={'marginTop': '10px', 'color': 'green', 'fontFamily': 'Poppins, sans-serif'})
        ], style={'textAlign': 'center', 'marginBottom': '30px', 'backgroundColor': 'white', 'borderRadius': '10px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.1)', 'padding': '20px'})
    ]),
    
    html.Div([
        html.H4('Favori Bölgeleriniz', style={'fontFamily': 'Poppins, sans-serif', 'fontWeight': '600', 'color': '#1a237e'}),
        html.Ul(id='fav-list', style={'textAlign': 'center', 'listStyle': 'none', 'fontFamily': 'Poppins, sans-serif'})
    ], style={'backgroundColor': 'white', 'borderRadius': '10px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.1)', 'padding': '20px'}),
    
    html.Hr(style={'margin': '40px 0'}),
    
    html.Div([
        html.H2('Kişiselleştirilmiş Güvenlik Tavsiyesi', style={
            'textAlign': 'center',
            'marginTop': '40px',
            'marginBottom': '20px',
            'fontFamily': 'Poppins, sans-serif',
            'fontWeight': '700',
            'color': '#1a237e'
        }),
        html.Div([
            html.Label('Mahalleler:', style={'fontFamily': 'Poppins, sans-serif', 'fontWeight': '500'}),
            dcc.Dropdown(
            id='advice-mahalle',
            options=[{'label': m['isim'], 'value': i} for i, m in enumerate(MAHALLELER)],
            placeholder='Bir mahalle seçin',
            style={'width': '40%', 'display': 'inline-block', 'marginRight': '20px'}
            ),
            html.Label('Saat:', style={'marginLeft': '20px', 'fontFamily': 'Poppins, sans-serif', 'fontWeight': '500'}),
            dcc.Input(id='advice-hour', type='number', min=0, max=23, placeholder='Saat (0-23)', style={'width': '10%', 'padding': '8px', 'borderRadius': '5px', 'border': '1px solid #ddd'}),
            html.Button('Tavsiye Al', id='get-advice-btn', n_clicks=0, style={
                'marginLeft': '20px',
                'padding': '8px 20px',
                'backgroundColor': '#1a237e',
                'color': 'white',
                'border': 'none',
                'borderRadius': '5px',
                'cursor': 'pointer'
            }),
            html.Div(id='advice-msg', style={'marginTop': '10px', 'color': '#1a237e', 'fontFamily': 'Poppins, sans-serif'})
        ], style={'textAlign': 'center', 'marginBottom': '30px', 'backgroundColor': 'white', 'borderRadius': '10px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.1)', 'padding': '20px'})
    ])
], style={'padding': '20px', 'backgroundColor': '#f8f9fa', 'minHeight': '100vh'})

# Harita tıklaması veya mahalle seçimi ile koordinat inputlarını doldur
@dash_app.callback(
    Output('fav-lat', 'value'),
    Output('fav-lon', 'value'),
    Output('advice-lat', 'value'),
    Output('advice-lon', 'value'),
    Output('map-coord-msg', 'children'),
    Output('select-map', 'figure'),
    Input('select-map', 'clickData'),
    Input('mahalle-dropdown', 'value'),
    State('fav-lat', 'value'),
    State('fav-lon', 'value'),
    prevent_initial_call=True
)
def fill_coords(clickData, mahalle_idx, prev_lat, prev_lon):
    ctx = dash.callback_context
    fig = go.Figure(map_fig)  # Her zaman suç noktaları ve mahalleler trace'leriyle başla
    lat, lon, msg = None, None, ''
    if ctx.triggered and ctx.triggered[0]['prop_id'].startswith('select-map') and clickData:
        lat = clickData['points'][0]['lat']
        lon = clickData['points'][0]['lon']
        msg = f'Seçilen koordinatlar: {lat:.4f}, {lon:.4f}'
    elif ctx.triggered and ctx.triggered[0]['prop_id'].startswith('mahalle-dropdown') and mahalle_idx is not None:
        m = MAHALLELER[mahalle_idx]
        lat, lon = m['lat'], m['lon']
        msg = f'Seçilen mahalle: {m["isim"]} ({m["lat"]:.4f}, {m["lon"]:.4f})'
    else:
        lat, lon = prev_lat, prev_lon
    # Seçili noktayı haritada göster
    if lat is not None and lon is not None:
        fig.add_trace(go.Scattermapbox(
            lat=[lat], lon=[lon],
            mode='markers',
            marker=dict(size=18, color='green'),
            name='Seçili Nokta'
        ))
    return lat, lon, lat, lon, msg, fig

# Rota hesaplama callback'i
@dash_app.callback(
    Output('route-map', 'figure'),
    Output('route-info', 'children'),
    Input('calculate-route-btn', 'n_clicks'),
    State('start-mahalle', 'value'),
    State('end-mahalle', 'value')
)
def calculate_route(n_clicks, start_mahalle_idx, end_mahalle_idx):
    if n_clicks == 0 or start_mahalle_idx is None or end_mahalle_idx is None:
        return initial_map, html.Div('Lütfen başlangıç ve varış mahallelerini seçin.', style={'color': 'red'})
    
    try:
        # Mahalle koordinatlarını al
        start_mahalle = MAHALLELER[start_mahalle_idx]
        end_mahalle = MAHALLELER[end_mahalle_idx]
        
        # Alternatif rotaları iste
        coords = [(start_mahalle['lon'], start_mahalle['lat']), (end_mahalle['lon'], end_mahalle['lat'])]
        route = ors_client.directions(coords, profile='driving-car', format='geojson')
        # Her rota için risk ve mesafe hesapla (tek rota)
        feature = route['features'][0]
        route_coords = feature['geometry']['coordinates']
        risk_scores = []
        for lon, lat in route_coords:
            close_crimes = df[((df['latitude']-lat).abs() < 0.01) & ((df['longitude']-lon).abs() < 0.01)]
            risk_scores.append(len(close_crimes))
        avg_risk = sum(risk_scores) / len(risk_scores)
        distance = feature['properties']['segments'][0]['distance']
        duration = feature['properties']['segments'][0]['duration']
        # Risk seviyesini belirle (eşikler güncellendi)
        if avg_risk < 3:
            risk_level = 'Düşük Risk'
            color = 'green'
        elif avg_risk < 10:
            risk_level = 'Orta Risk'
            color = 'orange'
        else:
            risk_level = 'Yüksek Risk'
            color = 'red'
        # Harita güncelleme
        fig = go.Figure(initial_map)
        fig.add_trace(go.Scattermapbox(
            lat=[start_mahalle['lat'], end_mahalle['lat']],
            lon=[start_mahalle['lon'], end_mahalle['lon']],
            mode='markers+text',
            marker=dict(size=14, color=['blue', 'red']),
            text=[start_mahalle['isim'], end_mahalle['isim']],
            textposition='top center',
            name='Başlangıç ve Varış'
        ))
        lats, lons = zip(*[(lat, lon) for lon, lat in route_coords])
        fig.add_trace(go.Scattermapbox(
            lat=lats,
            lon=lons,
            mode='lines',
            line=dict(width=5, color=color),
            name=f'Rota ({risk_level})'
        ))
        info = html.Div([
            html.H4(f'Rota: {risk_level}', style={'color': color}),
            html.P(f'Başlangıç: {start_mahalle["isim"]}'),
            html.P(f'Varış: {end_mahalle["isim"]}'),
            html.P(f'Ortalama Risk Skoru: {avg_risk:.1f}'),
            html.P(f'Toplam Mesafe: {distance/1000:.1f} km'),
            html.P(f'Tahmini Süre: {duration/60:.0f} dakika')
        ])
        return fig, info
    except Exception as e:
        return initial_map, html.Div(f'Hata: {str(e)}', style={'color': 'red'})

if __name__ == '__main__':
    app.run(debug=True) 