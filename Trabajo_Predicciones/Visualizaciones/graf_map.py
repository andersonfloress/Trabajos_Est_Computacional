import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt

# 1. Cargar el GeoJSON
geo_path = "Trabajo_Predicciones/Visualizaciones/pe.json" 
peru_map = gpd.read_file(geo_path)

# 2. Cargar los datos CSV
df = pd.read_csv("Trabajo_Predicciones/models/casos_departamento.csv")

# 3. Normalizar nombres
df['Departamento'] = df['Departamento'].str.strip().str.lower()
peru_map['name'] = peru_map['name'].str.strip().str.lower()

# 4. Merge (left merge para mantener todos los departamentos)
merged = peru_map.merge(df, how='left', left_on='name', right_on='Departamento')

# Rellenar NaN con 0
merged['Total'] = merged['Total'].fillna(0)
merged['Graves'] = merged['Graves'].fillna(0)

# 5. Crear gráfico
fig, ax = plt.subplots(figsize=(12, 12))

# Mapa de calor de casos totales
merged.plot(
    column='Total',
    ax=ax,
    legend=True,
    cmap='OrRd',
    edgecolor='black',
    linewidth=0.8
)

# 6. Agregar círculos proporcionales para casos graves + etiquetas
for idx, row in merged.iterrows():
    if row['geometry'].geom_type in ['Polygon', 'MultiPolygon']:
        centroid = row['geometry'].centroid
        # Dibuja el círculo proporcional
        plt.scatter(
            centroid.x, centroid.y,
            s=row['Graves'] * 0.05, 
            color='blue',
            alpha=0.6,
            edgecolor='k',
            linewidth=0.5,
            zorder=5
        )
        # Etiqueta con número de casos graves
        plt.text(
            centroid.x, centroid.y + 0.3,  
            f"{int(row['Graves'])}",
            fontsize=8,
            ha='center',
            va='bottom',
            color='blue',
            weight='bold',
            zorder=6
        )

# 7. Etiquetas de departamentos
for idx, row in merged.iterrows():
    centroid = row['geometry'].centroid
    plt.text(
        centroid.x, centroid.y,
        row['name'].capitalize(),
        fontsize=7,
        ha='center',
        va='center',
        color='black',
        alpha=0.7
    )

plt.title("Casos Totales y Graves por Departamento en Perú", fontsize=15)
plt.axis('off')
plt.tight_layout()
plt.savefig("Trabajo_Predicciones/Visualizaciones/heatmap_peru.png", dpi=300)
plt.show()
