import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV, StratifiedKFold
from sklearn.preprocessing import LabelEncoder
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, confusion_matrix, ConfusionMatrixDisplay, roc_auc_score, roc_curve, precision_score, recall_score, f1_score, classification_report
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from imblearn.over_sampling import SMOTE
import folium
import ast
import shap
from sklearn.cluster import DBSCAN

print("Kod başladı...")

# VERİ YÜKLE
df = pd.read_csv('Crimes_Last_7_Days.csv')

# location kolonundan latitude ve longitude çıkar
def extract_lat(row):
    try: 
        val = ast.literal_eval(row)['latitude']
        return float(val)
    except: 
        return np.nan

def extract_lon(row):
    try: 
        val = ast.literal_eval(row)['longitude']
        return float(val)
    except: 
        return np.nan

df['latitude'] = df['location'].apply(extract_lat)
df['longitude'] = df['location'].apply(extract_lon)

# Koordinatları temizle
df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')

# Kullanılacak kolonlar
cols_needed = ['date', 'primary_type', 'location_description', 'arrest', 'latitude', 'longitude']
df = df[cols_needed]

# Gelişmiş özellik mühendisliği
df['DATE'] = pd.to_datetime(df['date'])
df['HOUR'] = df['DATE'].dt.hour
df['DAY_OF_WEEK'] = df['DATE'].dt.dayofweek
df['MONTH'] = df['DATE'].dt.month
df['IS_WEEKEND'] = df['DAY_OF_WEEK'].isin([5, 6]).astype(int)
df['IS_NIGHT'] = ((df['HOUR'] >= 22) | (df['HOUR'] <= 4)).astype(int)

# Lokasyon özelliklerini zenginleştirme
df['LOCATION_CATEGORY'] = df['location_description'].str.split().str[0]
df['LOCATION_DETAIL'] = df['location_description'].str.split().str[1:].str.join(' ')

# Eksik doldurma
imputer = SimpleImputer(strategy='most_frequent')
df['location_description'] = imputer.fit_transform(df[['location_description']]).ravel()

# Encode
le_loc = LabelEncoder()
le_type = LabelEncoder()
df['LOCATION_CODE'] = le_loc.fit_transform(df['location_description'])
df['PRIMARY_CODE'] = le_type.fit_transform(df['primary_type'])

# Korelasyon heatmap
corr = df[['HOUR', 'LOCATION_CODE', 'PRIMARY_CODE', 'IS_WEEKEND', 'IS_NIGHT']].corr()
plt.figure(figsize=(12, 8))
sns.heatmap(corr, annot=True, cmap='coolwarm')
plt.title('Gelişmiş Korelasyon Matrisi')
plt.savefig('correlation_heatmap.png')
plt.close()

# Özellik ve hedef
X = df[['HOUR', 'LOCATION_CODE', 'PRIMARY_CODE', 'IS_WEEKEND', 'IS_NIGHT']]
y = df['arrest']

# Train-test
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# SMOTE
sm = SMOTE(random_state=42)
X_res, y_res = sm.fit_resample(X_train, y_train)

# MODELLER
models = {
    'Random Forest': RandomForestClassifier(class_weight='balanced'),
    'AdaBoost': AdaBoostClassifier(),
    'Gradient Boost': GradientBoostingClassifier(),
    'KNN': KNeighborsClassifier(),
    'Naive Bayes': GaussianNB()
}

# Hiperparametre optimizasyonu için parametre grid'leri
param_grids = {
    'Random Forest': {
        'n_estimators': [100, 200],
        'max_depth': [10, 20],
        'min_samples_split': [2, 5]
    },
    'AdaBoost': {
        'n_estimators': [50, 100],
        'learning_rate': [0.1, 1.0]
    },
    'Gradient Boost': {
        'n_estimators': [100, 200],
        'learning_rate': [0.1, 0.5]
    },
    'KNN': {
        'n_neighbors': [3, 5, 7],
        'weights': ['uniform', 'distance']
    }
}

results = {}
best_models = {}

# Model eğitimi ve değerlendirme
for name, model in models.items():
    print(f"\n{name} modeli eğitiliyor...")
    
    # Hiperparametre optimizasyonu
    if name in param_grids:
        grid_search = GridSearchCV(
            model,
            param_grids[name],
            cv=5,
            scoring='f1',
            n_jobs=-1
        )
        grid_search.fit(X_res, y_res)
        best_model = grid_search.best_estimator_
        print(f"En iyi parametreler: {grid_search.best_params_}")
    else:
        best_model = model.fit(X_res, y_res)
    
    best_models[name] = best_model
    
    # Cross-validation
    cv_scores = cross_val_score(best_model, X_res, y_res, cv=5, scoring='f1')
    print(f"Cross-validation F1 scores: {cv_scores}")
    print(f"Ortalama F1 score: {cv_scores.mean():.3f} (+/- {cv_scores.std() * 2:.3f})")
    
    # Test seti üzerinde değerlendirme
    y_pred = best_model.predict(X_test)
    results[name] = {
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred),
        'recall': recall_score(y_test, y_pred),
        'f1': f1_score(y_test, y_pred)
    }
    
    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm)
    disp.plot()
    plt.title(f"Confusion Matrix - {name}")
    plt.savefig(f"confusion_matrix_{name.replace(' ','_')}.png")
    plt.close()
    
    # ROC Curve
    if hasattr(best_model, "predict_proba"):
        y_score = best_model.predict_proba(X_test)[:,1]
        fpr, tpr, _ = roc_curve(y_test, y_score)
        plt.plot(fpr, tpr, label=f'{name} (AUC={roc_auc_score(y_test, y_score):.2f})')

# ROC toplu
plt.plot([0,1], [0,1], 'k--')
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('ROC Curve')
plt.legend()
plt.savefig('roc_curve.png')
plt.close()

# Model karşılaştırma grafiği
metrics = ['accuracy', 'precision', 'recall', 'f1']
fig, axes = plt.subplots(2, 2, figsize=(15, 10))
axes = axes.ravel()

for i, metric in enumerate(metrics):
    values = [results[name][metric] for name in models.keys()]
    axes[i].bar(models.keys(), values)
    axes[i].set_title(f'{metric.capitalize()} Comparison')
    axes[i].set_ylim(0, 1)
    plt.setp(axes[i].xaxis.get_majorticklabels(), rotation=45)

plt.tight_layout()
plt.savefig('model_comparison.png')
plt.close()

# Feature importance (Random Forest)
rf_model = best_models['Random Forest']
importances = rf_model.feature_importances_
feat_names = X.columns
plt.figure(figsize=(10, 6))
plt.barh(feat_names, importances)
plt.title('Feature Importance (Random Forest)')
plt.savefig('feature_importance.png')
plt.close()

# SHAP değerleri
explainer = shap.TreeExplainer(rf_model)
shap_values = explainer.shap_values(X_test)
plt.figure(figsize=(10, 6))
shap.summary_plot(shap_values, X_test)
plt.savefig('shap_summary.png')
plt.close()

# HARİTA
crime_map = folium.Map(location=[41.8781, -87.6298], zoom_start=11)

# Suç noktalarını haritada göster (örnek olarak ilk 1000 nokta)
for _, row in df.dropna(subset=['latitude','longitude']).head(1000).iterrows():
    folium.CircleMarker(
        [float(row['latitude']), float(row['longitude'])],
        radius=2,
        color='red',
        fill=True,
        popup=f"Suç Tipi: {row['primary_type']}<br>Lokasyon: {row['location_description']}"
    ).add_to(crime_map)

# Kümelenme analizi
coords = df[['latitude', 'longitude']].dropna().values
clustering = DBSCAN(eps=0.01, min_samples=5).fit(coords)

# Kümeleri haritada göster
unique_labels = set(clustering.labels_)
for label in unique_labels:
    if label != -1:  # Gürültü noktalarını hariç tut
        mask = clustering.labels_ == label
        cluster_points = coords[mask]
        center_lat = np.mean(cluster_points[:, 0])
        center_lon = np.mean(cluster_points[:, 1])
        
        folium.CircleMarker(
            location=[float(center_lat), float(center_lon)],
            radius=10,
            color='blue',
            fill=True,
            popup=f'Küme {label}: {sum(mask)} nokta'
        ).add_to(crime_map)

crime_map.save('crime_map.html')

# Zaman serisi analizi
plt.figure(figsize=(15, 6))
df.groupby('DATE')['arrest'].mean().plot()
plt.title('Günlük Tutuklama Oranı Trendi')
plt.savefig('arrest_trend.png')
plt.close()

# Suç tipi dağılımı
plt.figure(figsize=(12, 6))
df['primary_type'].value_counts().head(10).plot(kind='bar')
plt.title('En Sık İşlenen 10 Suç Tipi')
plt.savefig('crime_types.png')
plt.close()

# Saatlik dağılım
plt.figure(figsize=(12, 6))
df.groupby('HOUR')['arrest'].mean().plot(kind='bar')
plt.title('Saatlik Tutuklama Oranı')
plt.savefig('hourly_arrest_rate.png')
plt.close()

print("\n📊 Tüm analizler ve görseller tamamlandı!")
print("\nModel Performans Özeti:")
for name, metrics in results.items():
    print(f"\n{name}:")
    for metric, value in metrics.items():
        print(f"{metric}: {value:.3f}")
