# 🕐 Tiempos Estimados de Ejecución

## Barrido SNR con Todas las Modulaciones

### Configuración Utilizada
- **Imagen**: 450×450 pixeles = 4,860,000 bits
- **Modulaciones**: 3 (QPSK, 16-QAM, 64-QAM)
- **Tiempo por transmisión**: ~37 segundos (para 4.86M bits con 1 iteración)

### Tabla de Tiempos Estimados

| SNR Range | Iteraciones/SNR | Tiempo Estimado | Ejemplo |
|-----------|-----------------|-----------------|---------|
| 3 valores | 2 iteraciones   | ~3.7 min (220s) | 0-10 paso 5 |
| 3 valores | 5 iteraciones   | ~9.2 min (550s) | 0-10 paso 5 |
| 3 valores | 10 iteraciones  | ~18.4 min       | 0-10 paso 5 |
| 5 valores | 2 iteraciones   | ~6.2 min (370s) | 0-20 paso 5 |
| 5 valores | 5 iteraciones   | ~15.5 min       | 0-20 paso 5 |
| 5 valores | 10 iteraciones  | ~31 min         | 0-20 paso 5 |
| 11 valores| 5 iteraciones   | ~34 min         | 0-50 paso 5 |

### Fórmula General
```
Tiempo (segundos) ≈ 37 × (# SNRs) × (# iteraciones) × 3 modulaciones
```

### Ejemplo de Cálculo
Para barrido 0-20 dB con paso 5 (5 valores) y 10 iteraciones:
- Total operaciones: 5 SNRs × 10 iteraciones × 3 modulaciones = 150
- Tiempo ≈ 37 × 150 / 3600 ≈ 1.54 horas

## Recomendaciones

### Para Pruebas Rápidas (< 5 min)
```
SNR: 0-10 dB, paso 5 (3 valores)
Iteraciones: 2
Tiempo total: ~3.7 minutos
```

### Para Resultados Aceptables (< 30 min)
```
SNR: 0-20 dB, paso 5 (5 valores)
Iteraciones: 5
Tiempo total: ~15.5 minutos
```

### Para Resultados de Calidad (< 1 hora)
```
SNR: 0-30 dB, paso 5 (7 valores)
Iteraciones: 5
Tiempo total: ~21.7 minutos
```

## Barra de Progreso

Ahora la barra de progreso se actualiza constantemente mostrando:
- Porcentaje completado (0-100%)
- Modulación actual (QPSK, 16-QAM, 64-QAM)
- Valor SNR actual
- Número de iteración actual

Ejemplo:
```
[45%] 16-QAM - SNR: 10.0 dB, Iter: 3/10
```

## Tips de Optimización

1. **Primero prueba rápido**: Haz barrido 0-10 con 2 iteraciones (3.7 min)
2. **Luego refina**: Si necesitas más precisión, aumenta iteraciones
3. **Guarda gráficas**: Una vez obtengas buenos resultados, guardalos
4. **Reutiliza datos**: Los datos se guardan en los tabs de resultados

## ¿Está colgado?

Si la barra de progreso no se mueve en 10 minutos:
1. Verifica que la imagen esté cargada
2. Revisa los parámetros SNR
3. Si todo está bien, simplemente espera - podría estar procesando aún
4. Usa recursos del sistema para monitorear CPU/RAM si es necesario
