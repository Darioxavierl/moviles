# Marco Teórico Completo: Simulaciones 5G NR para UAV
## Guía de Referencia para Informe Académico

---

## 📋 Contenido de Este Repositorio

Este conjunto de documentos proporciona la fundamentación teórica completa para cuatro simulaciones 5G NR enfocadas en comunicaciones con vehículos aéreos no tripulados (UAV). Cada documento es independiente pero parte de un framework unificado.

---

## 📁 Estructura de Documentos

### 1. **THEORETICAL_FRAMEWORK_01_INTERFERENCE.md** 
**Tema:** Análisis de Interferencia en Escenarios Densos

#### Contenido Clave:
- Configuración de banda 5G NR n78 (3.55-3.7 GHz)
- MIMO 4×4 Massive
- Control de potencia en bucle abierto (3GPP TS 38.213)
- Cálculo de path loss mediante ray tracing
- Modelos de ruido térmico
- SINR y capacidad Shannon

#### Simulación Asociada: `interference.py`
```python
# Escanarios implementados:
  • Sparse (5 UAVs):   Baja interferencia
  • Dense (15 UAVs):   Alta interferencia multivía
```

#### Métricas de Salida:
- Throughput promedio por UAV (Mbps)
- SINR distribuciones por nivel de interferencia
- Path loss en dB
- Comparación Sparse vs Dense

#### Referencias Normativas:
- 3GPP TS 38.104 (Bandas y especificaciones)
- 3GPP TS 38.213 (Control de potencia)
- 3GPP TS 38.875 (Beamforming y modelos de canal)

---

### 2. **THEORETICAL_FRAMEWORK_02_MOBILITY.md**
**Tema:** Análisis Comparativo de Patrones de Movilidad UAV

#### Contenido Clave:
- Modelos de trayectorias: Hover vs Circuito
- Variabilidad de distancia TX-RX vs Throughput
- Métrica de Fairness de Jain
- Análisis de throughput espacial
- Visibilidad LoS/NLoS por ruta

#### Simulación Asociada: `mobility.py`
```python
# Rutas implementadas:
  • Ruta A (Hover):     Oscilación pequeña, estable
  • Ruta B (Circuito):  Circuito rectangular, variable
```

#### Métricas de Salida:
- Throughput promedio y desviación estándar
- Fairness (F de Jain) por ruta
- Variación de distancia gNB-UAV
- Throughput vs posición en ruta

#### Referencias Normativas:
- 3GPP TR 36.777 (UAV support en LTE)
- 3GPP TS 36.300 (Arquitectura E-UTRA)
- ITU-R P.1411 (Modelos de propagación)

---

### 3. **THEORETICAL_FRAMEWORK_02_MIMO_BEAMFORMING.md**
**Tema:** Técnicas MIMO Avanzadas de Beamforming

#### Contenido Clave:
- Descomposición SVD (Singular Value Decomposition)
- MRC Beamforming (Maximum Ratio Combining)
- Zero Forcing Precoding
- Comparación teórica de las 3 técnicas
- Cálculo dinámico de streams activos

#### Simulación Asociada: `mimo_beam.py`
```python
# Técnicas implementadas:
  • SVD Multi-Stream:   Adaptativo (1-4 streams)
  • MRC Beamforming:    Fijo (1 stream con diversidad)
  • Zero Forcing:       Fijo (4 streams siempre)
  
# Configuraciones:
  • MIMO 2×2:           4 antenas TX/RX
  • MIMO 4×4:           16 antenas TX/RX (Massive)
  • MIMO 4×2 Asimétrico: 16 antenas TX, 4 RX
```

#### Métricas de Salida:
- Throughput comparativo por técnica
- Número de streams activos (SVD)
- Ganancia relativa vs MRC
- Tabla de configuraciones

#### Referencias Normativas:
- 3GPP TS 38.875 (Beamforming 3D)
- 3GPP TS 38.201 (Servicios NR)
- 3GPP TS 38.211 (Procedimientos de capa física)

---

### 4. **THEORETICAL_FRAMEWORK_03_HEIGHT_ANALYSIS.md**
**Tema:** Efectos de Altitud en Propagación 5G NR

#### Contenido Clave:
- Relación altura vs. visibilidad (LoS probability)
- Variación de path loss con altura
- Modelos ITU-R P.1411 y 3GPP TS 38.901
- Zona óptima de operación
- Compromiso cobertura vs. throughput

#### Simulación Asociada: `height.py`
```python
# Rango de alturas analizado:
  50 m   → Zona baja (obstáculos)
  50-300 m → Zona óptima
  300-500 m → Zona de transición
  500-1000 m → Zona alta (cobertura amplia pero débil)
```

#### Métricas de Salida:
- Throughput vs. altura (Mbps)
- Path loss vs. altura (dB)
- Probabilidad LoS vs. altura
- SINR vs. altura
- Tabla comparativa por banda de altura

#### Referencias Normativas:
- 3GPP TS 38.901 (Modelos de canal para 5G)
- ITU-R P.1411 (Propagación indoor/outdoor)
- ITU-R P.1812 (Propagación urbana y suburbana)

---

## 🎯 Cómo Usar Este Framework para tu Informe

### Paso 1: Introducción Teórica
```
Sección 1 de cada documento proporciona:
  • Base de 5G NR específica para el tema
  • Ecuaciones fundamentales
  • Contexto normativo 3GPP/ITU-R
```

### Paso 2: Detalles Técnicos
```
Secciones 2-4 contienen:
  • Ecuaciones de propagación
  • Modelos matemáticos
  • Explicaciones de cálculos en simulación
```

### Paso 3: Configuración de Simulación
```
Secciones 4-5 describen:
  • Cómo se implementa cada técnica
  • Flujo de ray tracing
  • Parámetros específicos (BW, TX Power, etc.)
```

### Paso 4: Resultados Esperados
```
Secciones 5-6 incluyen:
  • Tablas de resultados típicos
  • Gráficos esperados
  • Rangos de valores realistas
```

### Paso 5: Limitaciones
```
Sección 7 (final) enumera:
  • Simplificaciones vs. realidad
  • Asunciones importantes
  • Validez del modelo
```

---

## 📊 Flujo Recomendado para Informe Académico

### Capítulo 1: Fundamentos 5G NR
**Fuente:** THEORETICAL_FRAMEWORK_01_INTERFERENCE.md (Sección 1)
- Especificación Band n78
- Arquitectura MIMO 4×4
- Conceptos de SINR y throughput

### Capítulo 2: Propagación y Ray Tracing
**Fuente:** Todos los marcos (Sección 2)
- Modelos de propagación
- Free space vs. path loss real
- Ray tracing en Sionna

### Capítulo 3: Análisis de Interferencia
**Fuente:** THEORETICAL_FRAMEWORK_01_INTERFERENCE.md (Secciones 3-6)
- Introducir escenarios Sparse vs. Dense
- Mostrar impacto de interferencia
- Comparar resultados de simulación

### Capítulo 4: Optimización de Movilidad
**Fuente:** THEORETICAL_FRAMEWORK_02_MOBILITY.md (Secciones 3-6)
- Modelos de trayectorias
- Análisis de fairness
- Recomendaciones de rutas

### Capítulo 5: Técnicas Avanzadas MIMO
**Fuente:** THEORETICAL_FRAMEWORK_02_MIMO_BEAMFORMING.md (Secciones 2-4)
- Comparación SVD vs. MRC vs. Zero Forcing
- Dinámico vs. fijo número de streams
- Resultados experimentales

### Capítulo 6: Altura Óptima Operacional
**Fuente:** THEORETICAL_FRAMEWORK_03_HEIGHT_ANALYSIS.md (Secciones 3-7)
- Relación altura-propagación
- Zona óptima de operación
- Matriz de decisión

### Capítulo 7: Conclusiones
**Fuente:** Todas las secciones de limitaciones
- Validez de modelos
- Trabajo futuro
- Recomendaciones

---

## 🔑 Conceptos Clave Unificados

### A. Configuración Común

```
Banda:              5G NR Band n78 (3.55-3.7 GHz)
Ancho de banda:     100 MHz
Subportadoras:      556 (15 kHz spacing)
MIMO:               4×4 Massive
TX Power:           26 dBm (200 mW)
Ruido Figura:       7 dB
```

### B. Métricas Principales

```
1. Path Loss (dB):      Atenuación de señal por distancia
                        L = 20 log₁₀(d) + 20 log₁₀(f) + K
                        
2. SINR (dB):          Relación señal-a-interferencia+ruido
                        SINR = P_signal / (P_interference + P_noise)
                        
3. Throughput (Mbps):  Capacidad Shannon por canal
                        TP = Σ log₂(1 + SINR_i) × BW
                        
4. Fairness:           Equidad de recursos (Jain)
                        F = (Σ TP_i)² / (N × Σ TP_i²)
```

### C. Factores Críticos

```
| Factor | Rango | Impacto |
|--------|-------|---------|
| Distancia gNB-UAV | 50-1000m | Path loss logarítmico |
| Altura UAV | 50-500m | LoS probability, distance 3D |
| Número streams | 1-4 | Multiplexación espacial |
| Visibilidad | LoS/NLoS | ±3-10 dB en path loss |
| Interferencia | Sparse/Dense | ±15-25 dB en SINR |
```

---

## 📈 Datos Típicos de Referencia

### Interferencia (interference.py)

```
Escenario Sparse (5 UAVs):
  Throughput promedio:    450-500 Mbps
  SINR promedio:          12-15 dB
  Std desviación:         ±20-50 Mbps

Escenario Dense (15 UAVs):
  Throughput promedio:    200-250 Mbps
  SINR promedio:          5-8 dB
  Std desviación:         ±50-100 Mbps
  Degradación:            ≈50-60% vs Sparse
```

### Movilidad (mobility.py)

```
Ruta A (Hover):
  Throughput promedio:    335 Mbps
  Fairness:              0.92 (excelente)
  Variabilidad:          Baja (σ = ±12 Mbps)

Ruta B (Circuito):
  Throughput promedio:    287 Mbps
  Fairness:              0.64 (media)
  Variabilidad:          Alta (σ = ±78 Mbps)
  Zona mejor:            Cerca del gNB (450 Mbps)
  Zona peor:             Lejos del gNB (48 Mbps)
```

### MIMO Beamforming (mimo_beam.py)

```
Configuración MIMO 4×4:
  SVD Multi-Stream:      550 Mbps (referencia óptima)
  MRC Single-Stream:     450 Mbps (93% vs SVD)
  Zero Forcing:          520 Mbps (95% vs SVD)

Número de streams:
  Típico LOS:            3-4 streams activos
  Típico NLOS:           2-3 streams activos
  Degradado:             1-2 streams activos
```

### Height Analysis (height.py)

```
Altura óptima:          200-300 m
  TP en zona óptima:     250-300 Mbps
  Fairness:              0.85-0.95

Altura baja (<100m):    TP degradado (obstáculos)
Altura alta (>500m):    TP degradado (distancia 3D)
```

---

## 🔗 Referencias Cruzadas Rápidas

| Pregunta | Documento | Sección |
|----------|-----------|---------|
| ¿Qué es path loss? | Interference | 2.2 |
| ¿Cómo afecta la altura? | Height | 1.2 |
| ¿Cuál técnica es mejor? | MIMO | 2 |
| ¿Qué ruta elegir? | Mobility | 6.2 |
| ¿Cuánta interferencia? | Interference | 6 |
| ¿Cómo funciona SVD? | MIMO | 2.1 |

---

## 📝 Citaciones 3GPP/ITU-R

Todos los documentos incluyen referencias normativas que puedes citar directamente:

```
Cita formato académico:

[1] 3GPP TS 38.901, "Study on channel model for frequencies from 0.5 to 100 GHz," 
    Release 15, March 2019.

[2] ITU-R P.1411, "Propagation data and prediction methods for the planning of 
    indoor radiocommunication systems in the frequency range 300 MHz to 100 GHz," 
    ITU, 2019.

[3] 3GPP TS 38.213, "NR; Physical layer procedures for control," Release 15, 
    March 2019.
```

---

## 🚀 Próximos Pasos

1. **Lee THEORETICAL_FRAMEWORK_01_INTERFERENCE.md** para fundamentos 5G
2. **Revisa resultados de simulación** contra valores esperados en cada documento
3. **Estructura tu informe** siguiendo el flujo de 7 capítulos propuesto
4. **Cita normativas 3GPP/ITU-R** directamente desde las secciones de referencias
5. **Incluye gráficos de simulación** junto a explicaciones teóricas

---

## 📚 Documentos Incluidos

- ✅ THEORETICAL_FRAMEWORK_01_INTERFERENCE.md (800 líneas)
- ✅ THEORETICAL_FRAMEWORK_02_MOBILITY.md (750 líneas)
- ✅ THEORETICAL_FRAMEWORK_02_MIMO_BEAMFORMING.md (850 líneas)
- ✅ THEORETICAL_FRAMEWORK_03_HEIGHT_ANALYSIS.md (720 líneas)
- ✅ THEORETICAL_FRAMEWORK_README.md (este archivo)

**Total:** ~3,920 líneas de documentación técnica

---

**Última actualización:** Febrero 2026  
**Versión:** 1.0  
**Simulador:** Sionna 1.2.1  
**Normativas:** 3GPP Release 15, ITU-R 2019
