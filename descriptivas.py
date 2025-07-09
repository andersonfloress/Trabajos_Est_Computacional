import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Configuración de la página
st.set_page_config(page_title="Análisis de Electricidad", layout="centered")
st.title("ENAHO Análisis de Datos de Electricidad ")

# Sección para cargar archivo CSV
st.header("Cargar archivo CSV")
uploaded_file = st.file_uploader("Carga tu archivo CSV con las columnas: P1121, P112A, P1172$02", type=["csv"])

if uploaded_file:
    df = pd.read_csv(
        uploaded_file,
        sep=",",
        na_values=["", "  ", "   ", "    "],
        keep_default_na=False
    )

    # Reemplazar espacios en blanco por NaN
    df = df.replace(r'^\s+$', np.nan, regex=True)

    expected_columns = ['P1121', 'P112A', 'P1172$02']
    if all(col in df.columns for col in expected_columns):
        df = df[expected_columns].copy()

        # Convertir a numérico y manejar errores
        df['P1121'] = pd.to_numeric(df['P1121'], errors='coerce')
        df['P112A'] = pd.to_numeric(df['P112A'], errors='coerce')
        df['P1172$02'] = pd.to_numeric(df['P1172$02'], errors='coerce')

        total_filas = df.shape[0]
        vacios_p1121 = df['P1121'].isna().sum()
        vacios_p112a = df['P112A'].isna().sum()
        vacios_p1172 = df['P1172$02'].isna().sum()
        
        tiene_p1121_valido = df['P1121'].notna()
        es_sin_electricidad = df['P1121'] == 0
        es_con_electricidad = df['P1121'] == 1
        tiene_p112a_valido = df['P112A'].notna()
        
        # Condición para filtrar filas válidas para análisis
        condicion_final = (
            tiene_p1121_valido & 
            (es_sin_electricidad | (es_con_electricidad & tiene_p112a_valido))
        )
        
        df_clean = df[condicion_final].copy()
        
        filas_eliminadas = total_filas - df_clean.shape[0]

        # Llenar valores NaN en gasto mensual con 0
        df_clean['P1172$02'] = df_clean['P1172$02'].fillna(0)

        st.header("Paso 1: Limpieza de datos y detección de outliers")
        st.markdown(f"""
        - Total de filas originales: **{total_filas}**
        - Vacíos encontrados en P1121: **{vacios_p1121}**
        - Vacíos encontrados en P112A: **{vacios_p112a}**
        - Vacíos encontrados en P1172$02: **{vacios_p1172}**
        - **Filas finales para análisis: {df_clean.shape[0]}**
        """)

        # Función para detectar outliers usando el método IQR
        def detectar_outliers(series):
            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1
            lim_inf = q1 - 1.5 * iqr
            lim_sup = q3 + 1.5 * iqr
            return series[(series < lim_inf) | (series > lim_sup)]

        outliers_p1172 = detectar_outliers(df_clean['P1172$02'].dropna())

        st.markdown("### Resumen de Outliers Detectados")
        st.markdown(f"""
        - Outliers en **P1172$02 (gasto mensual)**: {len(outliers_p1172)} {'Ninguno' if len(outliers_p1172) == 0 else ''}
        """)

        valores_p1121 = df_clean['P1121'].value_counts().sort_index()

        if 'step' not in st.session_state:
            st.session_state.step = 1

        def next_step():
            st.session_state.step += 1

        # Mostrar análisis estadístico y visualizaciones después de avanzar pasos
        if st.session_state.step >= 2:
            st.header("Paso 2: Estadísticas descriptivas")

            st.subheader("Tipo de Alumbrado (P1121)")
            conteo_p1121 = df_clean['P1121'].value_counts().sort_index()

            tabla_p1121 = pd.DataFrame({
                'Valor': [0, 1],
                'Descripción': ['Sin electricidad', 'Con electricidad'],
                'Cantidad': [conteo_p1121.get(0, 0), conteo_p1121.get(1, 0)]
            })
            st.table(tabla_p1121)

            # Gráfico de barras para tipo de alumbrado
            fig, ax = plt.subplots()
            sns.barplot(x='Descripción', y='Cantidad', data=tabla_p1121, ax=ax)
            ax.set_title("Distribución del Tipo de Alumbrado")
            ax.set_xlabel("Tipo de Alumbrado")
            ax.set_ylabel("Número de Hogares")
            plt.xticks(rotation=45)
            st.pyplot(fig)

            st.markdown("""
            ¿Qué muestra este gráfico?  
            - Compara la cantidad de hogares con y sin electricidad para alumbrado.  
            """)

            st.subheader("Tipo de Conexión Eléctrica (P112A)")
            st.write("*Nota: Solo se considera para hogares con electricidad*")

            df_con_electricidad = df_clean[df_clean['P1121'] == 1]

            if len(df_con_electricidad) > 0:
                labels_p112a = {1: 'Exclusivo', 2: 'Colectivo', 3: 'Otro'}
                conteo_p112a = df_con_electricidad['P112A'].value_counts().sort_index()

                tabla_p112a = pd.DataFrame({
                    'Valor': [1, 2, 3],
                    'Descripción': ['Exclusivo', 'Colectivo', 'Otro'],
                    'Cantidad': [conteo_p112a.get(1, 0), conteo_p112a.get(2, 0), conteo_p112a.get(3, 0)]
                })
                st.table(tabla_p112a)

                # Gráfico de barras para tipo de conexión
                fig, ax = plt.subplots()
                sns.barplot(x='Descripción', y='Cantidad', data=tabla_p112a, ax=ax)
                ax.set_title("Distribución del Tipo de Conexión Eléctrica")
                ax.set_xlabel("Tipo de Conexión")
                ax.set_ylabel("Número de Hogares")
                plt.xticks(rotation=45)
                st.pyplot(fig)

                st.markdown("""
                ¿Qué muestra este gráfico?  
                - Indica cómo se distribuyen los tipos de conexión eléctrica entre los hogares con electricidad.  
                """)

            else:
                st.write("No hay hogares con electricidad en los datos.")

            st.subheader("Gasto Mensual en Electricidad (P1172$02)")
            stats = df_clean['P1172$02'].describe(percentiles=[0.25, 0.5, 0.75]).to_dict()
            stats['varianza'] = df_clean['P1172$02'].var()

            resumen = pd.DataFrame({
                'Estadística': ['Recuento', 'Promedio', 'Desviación estándar', 'Valor mínimo', 'Primer cuartil (25%)', 'Mediana (50%)', 'Tercer cuartil (75%)', 'Valor máximo', 'Varianza'],
                'Valor': [
                    int(stats['count']),
                    round(stats['mean'], 2),
                    round(stats['std'], 2),
                    stats['min'],
                    stats['25%'],
                    stats['50%'],
                    stats['75%'],
                    stats['max'],
                    round(stats['varianza'], 2)
                ]
            })
            st.table(resumen)

            # Histograma del gasto mensual
            fig1, ax1 = plt.subplots()
            sns.histplot(df_clean['P1172$02'], kde=False, bins=30, ax=ax1, color='skyblue')
            ax1.set_title("Histograma del Gasto Mensual en Electricidad")
            ax1.set_xlabel("Gasto Mensual (S/)")
            ax1.set_ylabel("Número de Hogares")
            st.pyplot(fig1)

            st.markdown("""
            ¿Qué muestra este gráfico?  
            - Muestra la frecuencia de los diferentes niveles de gasto mensual en electricidad entre los hogares.  
            """)

            # Boxplot del gasto mensual
            fig2, ax2 = plt.subplots()
            sns.boxplot(x=df_clean['P1172$02'], ax=ax2, color='lightgreen')
            ax2.set_title("Boxplot del Gasto Mensual en Electricidad")
            ax2.set_xlabel("Gasto Mensual (S/)")
            st.pyplot(fig2)

            st.markdown("""
            ¿Qué nos muestra este gráfico?  
            - La línea dentro de la caja indica la mediana del gasto.  
            - La caja representa el rango donde se encuentra el 50% central de los datos (entre el primer y tercer cuartil).  
            - Las líneas que salen de la caja (bigotes) muestran la variabilidad fuera del rango intercuartílico.  
            - Los puntos fuera de los bigotes son valores atípicos (outliers).  
            """)

        if st.session_state.step >= 3:
            st.header("Paso 3: Visualizaciones adicionales")

            st.subheader("Distribución del Tipo de Alumbrado (P1121)")
            fig, ax = plt.subplots()
            labels_pie = {0: 'Sin electricidad', 1: 'Con electricidad'}
            counts_p1121 = df_clean['P1121'].map(labels_pie).value_counts()
            counts_p1121.plot.pie(autopct='%1.1f%%', ax=ax, legend=True)
            ax.set_ylabel("")
            ax.set_title("Distribución del Tipo de Alumbrado")
            ax.legend(title="Tipo de Alumbrado", loc="best")
            st.pyplot(fig)

            if len(df_con_electricidad) > 0:
                st.subheader("Distribución del Tipo de Conexión Eléctrica (P112A)")
                fig, ax = plt.subplots()
                labels_p112a = {1: 'Exclusivo', 2: 'Colectivo', 3: 'Otro'}
                counts_p112a = df_con_electricidad['P112A'].map(labels_p112a).value_counts()
                counts_p112a = counts_p112a.reindex(labels_p112a.values(), fill_value=0)
                counts_p112a = counts_p112a[counts_p112a > 0]
                counts_p112a.plot.pie(autopct='%1.1f%%', ax=ax, legend=True)
                ax.set_ylabel("")
                ax.set_title("Distribución del Tipo de Conexión Eléctrica")
                ax.legend(title="Tipo de Conexión", loc="best")
                st.pyplot(fig)
            else:
                st.write("No hay hogares con electricidad para mostrar la distribución de P112A.")

            st.subheader("Mapa de calor del Gasto Mensual en Electricidad (P1172$02)")
            pivot_table = df_clean.pivot_table(
                index='P1121',
                columns='P112A',
                values='P1172$02',
                aggfunc='mean'
            )

            pivot_table = pivot_table.reindex(columns=[1, 2, 3])

            fig, ax = plt.subplots(figsize=(8, 4))
            sns.heatmap(pivot_table, annot=True, fmt=".2f", cmap="YlGnBu", cbar_kws={'label': 'Gasto promedio'}, ax=ax)
            ax.set_xlabel("Tipo de Conexión Eléctrica (P112A)")
            ax.set_ylabel("Tipo de Alumbrado (P1121)")
            ax.set_title("Gasto Promedio Mensual según Tipo de Alumbrado y Conexión")

            y_labels_map = {0: 'Sin electricidad (0)', 1: 'Con electricidad (1)'}
            x_labels_map = {1: 'Exclusivo (1)', 2: 'Colectivo (2)', 3: 'Otro (3)'}
            ax.set_yticklabels([y_labels_map[i] for i in pivot_table.index], rotation=0)
            ax.set_xticklabels([x_labels_map[i] for i in pivot_table.columns], rotation=45)

            st.pyplot(fig)

        if st.session_state.step >= 4:
            st.header("Paso 4: Storytelling")

            total_hogares = len(df_clean)
            hogares_con_electricidad = (df_clean['P1121'] == 1).sum()
            hogares_sin_electricidad = (df_clean['P1121'] == 0).sum()

            pct_con_electricidad = (hogares_con_electricidad / total_hogares) * 100
            pct_sin_electricidad = (hogares_sin_electricidad / total_hogares) * 100

            gasto_promedio_total = df_clean['P1172$02'].mean()
            if hogares_con_electricidad > 0:
                gasto_promedio_con_electricidad = df_clean[df_clean['P1121'] == 1]['P1172$02'].mean()
            else:
                gasto_promedio_con_electricidad = 0

            if hogares_sin_electricidad > 0:
                gasto_promedio_sin_electricidad = df_clean[df_clean['P1121'] == 0]['P1172$02'].mean()
            else:
                gasto_promedio_sin_electricidad = 0

            if hogares_con_electricidad > 0:
                tipos_conexion_counts = df_clean[df_clean['P1121'] == 1]['P112A'].value_counts(normalize=True) * 100
                tipo_exclusivo = tipos_conexion_counts.get(1, 0)
                tipo_colectivo = tipos_conexion_counts.get(2, 0)
                tipo_otro = tipos_conexion_counts.get(3, 0)
            else:
                tipo_exclusivo = tipo_colectivo = tipo_otro = 0

            # Narrativa final basada en los datos procesados
            st.markdown(f"""
            ## ¿Qué nos dicen los datos sobre el acceso a la electricidad en los hogares peruanos?

            ### Hogares con y sin electricidad
            De los {total_hogares:,} hogares analizados, **casi {pct_con_electricidad:.1f}%** tienen acceso a electricidad para alumbrado, lo que significa que pueden iluminar sus casas con energía eléctrica. Sin embargo, **un {pct_sin_electricidad:.1f}%** todavía vive sin este servicio básico, lo que afecta su calidad de vida y oportunidades.

            ### ¿Cómo se conectan a la electricidad los hogares que sí la tienen?
            Entre los hogares con electricidad, la mayoría usa conexiones **exclusivas** (es decir, una conexión propia), mientras que otros usan conexiones **colectivas** o de otro tipo. Esto influye en la manera como consumen y pagan la electricidad.

            ### ¿Cuánto gastan en electricidad?
            El gasto promedio mensual es de S/ {gasto_promedio_total:.2f}. Los hogares con electricidad gastan, en promedio, S/ {gasto_promedio_con_electricidad:.2f} al mes, mientras que los hogares sin electricidad tienen un gasto cercano a cero, lo que refleja su falta de acceso.

            ### ¿Por qué es importante esta información?
            La falta de electricidad afecta la educación, la seguridad, la salud y las actividades económicas en las familias. El hecho de que aún haya un porcentaje importante sin acceso indica que es necesario continuar con programas que lleven electricidad a todos los hogares, especialmente en zonas rurales y vulnerables.

            ### En resumen:
            - La mayoría de los hogares en Perú ya cuenta con electricidad para alumbrado, pero no todos.
            - Hay diferentes tipos de conexiones, y eso puede influir en el consumo y gasto.
            - Entender quién tiene y quién no tiene electricidad ayuda a diseñar mejores políticas públicas.
            - Los datos muestran una oportunidad clara para mejorar el acceso y apoyar a las familias que aún no cuentan con este servicio básico.

            Con estos gráficos y datos, podemos ver no solo números, sino las historias de millones de hogares peruanos y su relación con la electricidad, un recurso vital para el desarrollo.
            """)


        if st.session_state.step < 4:
            st.button("Mostrar siguiente análisis", on_click=next_step)

    else:
        st.error("El archivo no contiene todas las columnas requeridas: P1121, P112A, P1172$02")
else:
    st.info("Por favor, carga un archivo CSV para comenzar el análisis.")

