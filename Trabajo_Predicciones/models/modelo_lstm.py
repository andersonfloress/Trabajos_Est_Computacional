import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# 1. Cargar y preparar datos
df = pd.read_csv("C:\\Users\\pc\\Downloads\\datos_filtrados_2020_2023.csv")
df = df[df['enfermedad'].str.contains('DENGUE', case=False)]
df['fecha'] = pd.to_datetime(df['ano'].astype(str) + '-W' + df['semana'].astype(str) + '-1', format='%Y-W%W-%w')
casos_semanales = df.groupby('fecha').size().reset_index(name='casos')
casos_semanales.set_index('fecha', inplace=True)

# 2. Escalar datos (LSTM funciona mejor con valores entre 0 y 1)
scaler = MinMaxScaler(feature_range=(0,1))
casos_scaled = scaler.fit_transform(casos_semanales)

# 3. Crear secuencias para LSTM
def crear_secuencias(data, pasos=4):
    X, y = [], []
    for i in range(len(data)-pasos):
        X.append(data[i:i+pasos])
        y.append(data[i+pasos])
    return np.array(X), np.array(y)

pasos_tiempo = 4  
X, y = crear_secuencias(casos_scaled, pasos=pasos_tiempo)

# 4. Dividir en entrenamiento y test (80%-20%)
limite = int(len(X)*0.8)
X_train, X_test = X[:limite], X[limite:]
y_train, y_test = y[:limite], y[limite:]

# 5. Crear modelo LSTM
modelo = Sequential()
modelo.add(LSTM(50, activation='relu', input_shape=(pasos_tiempo, 1)))
modelo.add(Dense(1))
modelo.compile(optimizer='adam', loss='mse')

# 6. Entrenar modelo
early_stop = EarlyStopping(monitor='loss', patience=10, restore_best_weights=True)
modelo.fit(X_train, y_train, epochs=100, batch_size=16, verbose=0, callbacks=[early_stop])

# 7. Predecir sobre test y para 12 semanas futuras
pred_test = modelo.predict(X_test)
pred_test_inversa = scaler.inverse_transform(pred_test)

# Predicción iterativa para 12 semanas futuras
entrada_pred = casos_scaled[-pasos_tiempo:].reshape(1, pasos_tiempo, 1)
pred_futuro = []
for _ in range(12):
    pred = modelo.predict(entrada_pred)
    pred_futuro.append(pred[0,0])
    entrada_pred = np.append(entrada_pred[:,1:,:],[[[pred[0,0]]]], axis=1)

pred_futuro_inversa = scaler.inverse_transform(np.array(pred_futuro).reshape(-1,1))

# 8. Graficar resultados
fechas_test = casos_semanales.index[limite+pasos_tiempo:]
fechas_futuras = pd.date_range(start=casos_semanales.index[-1] + pd.Timedelta(weeks=1), periods=12, freq='W')

plt.figure(figsize=(12,6))
plt.plot(casos_semanales.index, casos_semanales['casos'], label='Casos reales')
plt.plot(fechas_test, pred_test_inversa, label='Predicción LSTM (test)', color='orange')
plt.plot(fechas_futuras, pred_futuro_inversa, label='Predicción LSTM (futuro)', color='red')
plt.title('Predicción de casos semanales de dengue con LSTM')
plt.xlabel('Fecha')
plt.ylabel('Casos')
plt.legend()
plt.grid()
plt.show()

# 9. Imprimir datos en consola
print("\n🔹 Predicciones LSTM para las próximas 12 semanas:")
for fecha, prediccion in zip(fechas_futuras, pred_futuro_inversa):
    print(f"{fecha.date()}: {int(prediccion[0])} casos estimados")

# Guardar predicciones futuras en CSV
df_predicciones_lstm = pd.DataFrame({
    'fecha': fechas_futuras,
    'prediccion_casos': pred_futuro_inversa.flatten().astype(int)
})
df_predicciones_lstm.to_csv("Trabajo_Predicciones/models/predicciones_lstm_futuro.csv", index=False)

# 10. Métrica simple: error medio absoluto (MAE) en test
mae = np.mean(np.abs(pred_test_inversa - scaler.inverse_transform(y_test)))
print(f"\n🔹 Error Medio Absoluto (MAE) en test: {mae:.2f} casos")

# Guardar MAE en CSV
df_mae = pd.DataFrame({
    'metrica': ['MAE'],
    'valor': [mae]
})
df_mae.to_csv("Trabajo_Predicciones/models/metrica_mae_lstm.csv", index=False)

fechas_test = casos_semanales.index[limite+pasos_tiempo:]
df_predicciones_test = pd.DataFrame({
    'fecha': fechas_test,
    'prediccion_casos': pred_test_inversa.flatten().astype(int),
    'casos_reales': scaler.inverse_transform(y_test).flatten().astype(int)
})
df_predicciones_test.to_csv("Trabajo_Predicciones/models/predicciones_lstm_test.csv", index=False)

# 11. Calcular métricas completas en test
y_test_inversa = scaler.inverse_transform(y_test)

rmse_lstm = np.sqrt(mean_squared_error(y_test_inversa, pred_test_inversa))
mae_lstm = mean_absolute_error(y_test_inversa, pred_test_inversa)
mape_lstm = np.mean(np.abs((y_test_inversa - pred_test_inversa) / y_test_inversa)) * 100
r2_lstm = r2_score(y_test_inversa, pred_test_inversa)

print("\n🔹 Métricas de evaluación del modelo LSTM:")
print(f"RMSE: {rmse_lstm:.2f}")
print(f"MAE: {mae_lstm:.2f}")
print(f"MAPE: {mape_lstm:.2f}%")
print(f"R²: {r2_lstm:.4f}")

# Guardar métricas en CSV
metricas_lstm_df = pd.DataFrame({
    'RMSE': [rmse_lstm],
    'MAE': [mae_lstm],
    'MAPE (%)': [mape_lstm],
    'R2': [r2_lstm]
})
metricas_lstm_df.to_csv("Trabajo_Predicciones/models/metricas_lstm.csv", index=False)
