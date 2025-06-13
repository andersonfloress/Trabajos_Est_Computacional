import pandas as pd

# Cargar el dataset original
df = pd.read_csv("C:\\Users\\pc\\Downloads\\datos_abiertos_vigilancia_dengue_2000_2023.csv")

# Filtrar solo las filas con 'año' entre 2020 y 2023
df_filtrado = df[(df['ano'] >= 2020) & (df['ano'] <= 2023)]

# Guardar el nuevo archivo CSV con los datos filtrados (sin agrupar)
df_filtrado.to_csv("C:\\Users\\pc\\Downloads\\datos_filtrados_2020_2023_00.csv", index=False, encoding='utf-8')
print("Archivo guardado como 'datos_filtrados_2020_2023.csv'")

# Agrupar por departamento y año, y contar los casos
casos_por_departamento_ano = df_filtrado.groupby(['departamento', 'ano']).size().reset_index(name='total_casos')

# Guardar a un nuevo CSV con casos agrupados
casos_por_departamento_ano.to_csv("Trabajo_Predicciones\\Procesamiento\\casos_departamentos_2020_2023.csv", index=False)
print("Archivo guardado como 'casos_por_departamento_ano_2020_2023.csv'")
