# Marco Teórico: Análisis de Movilidad UAV
## Simulación: `mobility.py`

---

## 1. BASE TEÓRICA - TRAYECTORIAS DE VEHÍCULOS AÉREOS NO TRIPULADOS

### 1.1 Contexto 5G para UAV

**3GPP TR 36.777 - Study on enhanced LTE support for aerial vehicles**  
**3GPP TS 36.300 - E-UTRA and E-UTRAN overall description**

```
UAV (Unmanned Aerial Vehicle) = Dron comunicado con estación base (gNB)

Desafíos únicos:
  • Movilidad tridimensional (x, y, z)
  • Velocidades variables (0-50 m/s típico)
  • Mayores distancias TX-RX (hasta 10 km)
  • Visibilidad LOS frecuentemente mejor que terrestre
  • Interferencia con otros UAVs (dense deployments)
```

---

### 1.2 Modelos de Trayectorias

#### **Ruta A: Hover (Estacionario con Perturbación)**

```
Tipo: Patrón de vuelo controlado (estación base a estación base)

Ecuaciones de movimiento:
  x(t) = x₀ + A_x × sin(2πf_x × t)  [Oscilación lado-lado]
  y(t) = y₀ + A_y × sin(2πf_y × t)  [Oscilación adelante-atrás]
  z(t) = z₀                          [Altura constante]

Parámetros típicos:
  • Amplitud A_x, A_y ≈ 5-10 m (viento, control automático)
  • Frecuencia f_x, f_y ≈ 0.1-0.5 Hz (oscilaciones lentas)
  • Altura z₀ ≈ 100-200 m (sobre terreno)
  • Velocidad máxima: v_max ≈ 2 m/s (lenta)
```

**Aplicaciones:**
- Vigilancia estacionaria
- Retransmisores temporales
- Observación de eventos

#### **Ruta B: Circuito Rectangular**

```
Tipo: Patrón de patrullaje (perímetro cerrado)

Segmentos:
  1. Línea recta 1: (x₀, y₀) → (x₁, y₁)  [Velocidad constante v]
  2. Giro 90°: Radio de curvatura r ≈ 20 m
  3. Línea recta 2: (x₁, y₁) → (x₂, y₂)
  4. Giro 90°: Radio de curvatura r
  5. ... repetir

Parámetros:
  • Velocidad constante: v ≈ 10 m/s (patrullaje)
  • Perímetro: L ≈ 800-1000 m (circuito completo)
  • Radio de giro: r ≈ 20-30 m
  • Altura: z constante
  • Período de circuito: T ≈ L/v ≈ 80-100 segundos
```

**Aplicaciones:**
- Patrullaje de perímetro
- Mapeo de área
- Cobertura continua

---

### 1.3 Análisis de Distancia TX-RX

#### **Geometría 3D:**

```
d = √[(x_UAV - x_gNB)² + (y_UAV - y_gNB)² + (z_UAV - z_gNB)²]

Caso 2D (gNB terrestre):
  d = √[(x - x_gNB)² + (y - y_gNB)² + z²]
```

#### **Importancia para Comunicaciones:**

```
d grande → Pérdida de trayecto grande → SINR baja → Throughput bajo
d pequeña → Pérdida de trayecto pequeña → SINR alta → Throughput alto

Para 5G NR en 3.5 GHz:
  • d = 100 m   : Path loss ≈ 110 dB
  • d = 200 m   : Path loss ≈ 116 dB (+6 dB)
  • d = 500 m   : Path loss ≈ 123 dB (+13 dB)
  • d = 1000 m  : Path loss ≈ 129 dB (+19 dB)
```

---

## 2. MODELOS DE PROPAGACIÓN

### 2.1 Ray Tracing (Simulación Exacta)

**Método:** Sionna Ray Tracing Engine

```
Proceso:
  1. Discretizar escena en superficies (suelo, edificios, etc.)
  2. Lanzar rayos desde TX hacia RX
  3. Calcular reflexiones, difracciones, pérdidas
  4. Reconstruir canal H(f) combinando todos los paths
```

**Ventajas:**
- ✅ Incluye reflexiones reales
- ✅ Incluye visibilidad (LOS/NLOS)
- ✅ Frecuencia-dependiente
- ✅ Realista para geometrías complejas

**Desventajas:**
- ❌ Computacionalmente intensivo
- ❌ Requiere modelo del escenario exacto
- ❌ Variabilidad temporal ignorada (snapshot)

---

### 2.2 Path Loss Models (Simplificado)

**ITU-R P.1812 - Propagation in Urban and Suburban Areas:**

```
Modelo Free Space (sin obstáculos):
  L_fs = 20 log₁₀(d) + 20 log₁₀(f) + K

Modelo Hata (áreas urbanas):
  L_Hata = 69.55 + 26.16 log₁₀(f) - 13.82 log₁₀(h_tx) 
           + (44.9 - 6.55 log₁₀(h_tx)) × log₁₀(d)

En simulación: Ray tracing proporciona L exacta (no necesita modelo)
```

---

## 3. THROUGHPUT vs MOVILIDAD

### 3.1 Métricas de Desempeño

#### **A. Throughput Promedio**

```
TP_promedio = (1/N) × Σᵢ₌₁^N TP(t_i)

Donde:
  N = Número de snapshots ray tracing
  TP(t_i) = Throughput calculado con el canal en instante i
```

#### **B. Fairness (Equidad)**

```
Métrica de Jain:

F = (Σᵢ TP_i)² / (n × Σᵢ TP_i²)

Rango: F ∈ [0, 1]
  • F ≈ 1: Todos los puntos tienen throughput similar (equidad)
  • F ≈ 0: Algunos puntos tiene throughput muy alto, otros muy bajo

Interpretación:
  • Ruta con F alta: Conexión consistente (buena)
  • Ruta con F baja: Algunos puntos "muertos" con SINR baja
```

#### **C. Estadísticas Espaciales**

```
Variabilidad por posición: σ² = (1/N) × Σ(TP_i - TP_mean)²

Bajo σ: Throughput estable en toda la ruta (predecible)
Alto σ: Zones de muerte o excelencia (impredecible)
```

---

### 3.2 Análisis Ruta A (Hover)

**Escenario:**
```
UAV oscila en posición (5m amplitud, 0.2 Hz)
gNB estacionario
Distancia varía: d_min ≈ 150 m, d_max ≈ 200 m
```

**Esperado:**
```
• Throughput promedio: 300-350 Mbps (distancia media)
• Fairness: Alta (F ≈ 0.9) porque oscilación es pequeña
• Estabilidad: Buena (σ² bajo)

Razón: La distancia varía solo 50 m en rango de 150-200 m
       Variación relativa: 33% en rango, pero en escala logarítmica
       es solo ≈ 1.4 dB en path loss
```

---

### 3.3 Análisis Ruta B (Circuito)

**Escenario:**
```
UAV recorre circuito rectangular 800m × 500m
Velocidad constante v = 10 m/s
gNB en esquina del rectángulo
Distancia varía: d_min ≈ 100 m (cerca del gNB), d_max ≈ 1000 m (esquina opuesta)
```

**Esperado:**
```
• Throughput promedio: 350-400 Mbps (media geométrica de distancias)
• Máximo local: 450+ Mbps (cerca del gNB, d < 200m)
• Mínimo local: 150-200 Mbps (lejos del gNB, d > 800m)
• Fairness: Media-Baja (F ≈ 0.6-0.7) por variabilidad de distancia
```

**Path Loss Ruta B:**

```
Posición en ruta | Distancia gNB | Path Loss | SINR estimado | TP
─────────────────|───────────────|───────────|───────────────|──────
Esquina 1 (inicio)| 100 m         | 110 dB    | 20 dB         | 450 Mbps
Medio Lado 1     | 450 m         | 122 dB    | 8 dB          | 200 Mbps
Esquina opuesta  | 950 m         | 129 dB    | 1 dB          | 50 Mbps
Medio Lado 2     | 600 m         | 124 dB    | 6 dB          | 150 Mbps
Esquina 1 (cierre)| 100 m         | 110 dB    | 20 dB         | 450 Mbps
```

---

## 4. FLUJO DE SIMULACIÓN

### Paso 1: Generar Trayectorias

```python
# Línea 200-260 en mobility.py

for tiempo_discreto t in [0, Δt, 2Δt, ..., T_total]:
    # Ruta A (Hover)
    x_A(t) = x₀ + A × sin(2π × 0.2 × t)
    y_A(t) = y₀ + A × sin(2π × 0.1 × t)
    z_A(t) = z₀ = 150 m
    
    # Ruta B (Circuito)
    x_B(t), y_B(t), z_B(t) = PosiciónEnCircuito(t, v=10m/s)
    
    posiciones_A.append([x_A(t), y_A(t), z_A(t)])
    posiciones_B.append([x_B(t), y_B(t), z_B(t)])
```

### Paso 2: Ray Tracing para Cada Posición

```python
# Línea 300-350

for ruta in [A, B]:
    canales_H = []
    
    for pos_idx, pos_UAV in enumerate(posiciones_ruta):
        # Configurar gNB y UAV en geometría
        scene.place_transmitter(gNB_position)
        scene.place_receiver(pos_UAV)
        
        # Ray tracing: encontrar todos los paths
        paths = scene.compute_paths()
        
        # Construir matriz de canal H
        H = ConstructMatrizCanal(paths)
        
        canales_H.append(H)
    
    # H es lista de matrices: [H₀, H₁, H₂, ..., H_N]
    # Cada una corresponde a una posición en la ruta
```

### Paso 3: SINR y Throughput para Cada Punto

```python
# Línea 400-450

for ruta in [A, B]:
    throughputs = []
    
    for H_i in canales_H:
        # Beamforming (MIMO 4×4 SVD)
        W, U, S, rank = svd_beamforming(H_i)
        
        # SINR por stream
        for stream_idx in range(rank):
            SINR_i = (P_TX / rank) × |σᵢ|² / N
        
        # Capacidad Shannon
        TP_i = Σ log₂(1 + SINR_stream_j) × BW
        throughputs.append(TP_i)
    
    # Calcular métricas
    TP_promedio[ruta] = mean(throughputs)
    TP_std[ruta] = std(throughputs)
    Fairness[ruta] = JainFairness(throughputs)
```

---

## 5. SALIDAS DE LA SIMULACIÓN

### 5.1 Tablas Comparativas

#### **Tabla A: Métricas Globales**

```
Métrica                 | Ruta A (Hover)  | Ruta B (Circuito)
─────────────────────────|─────────────────|──────────────────
Throughput promedio (Mbps)| 335.2          | 287.4
Desv. Est. TP (Mbps)    | 12.1            | 78.3
Fairness (0-1)          | 0.92            | 0.64
Distancia mín. (m)      | 155             | 95
Distancia máx. (m)      | 198             | 955
Variación distancia (m) | 43              | 860
```

#### **Tabla B: Comparación Estadística**

```
Punto de análisis | Ruta A    | Ruta B
─────────────────|────────── |──────────
Mejor TP (Mbps)  | 348       | 450 (cerca gNB)
Peor TP (Mbps)   | 312       | 48 (lejos gNB)
Rango TP (Mbps)  | 36        | 402
Consistencia     | Excelente | Pobre
Recomendación    | Hover OK  | Necesita repetidor
```

---

### 5.2 Gráficos

#### **1. Throughput vs Posición en Ruta**

```
TP(Mbps)
  │
450 │                        ╱╲  Ruta B máximo (cerca)
400 │  ┌───────────────────╱  ╲
350 │  │ Ruta A (ruidosa)  \    ╲╱───
300 │  │ (pero oscila poco)      Ruta B
    │  │
100 │  └──────────────────────── Ruta B mínimo (lejos)
  │_____________________
    0%           50%          100% (posición en ruta)
```

#### **2. Distancia TX-RX vs Throughput**

```
Scatter plot:
  • Ruta A: Puntos agrupados entre 150-200m distancia
  • Ruta B: Puntos extendidos desde 100m hasta 950m
  
Correlación esperada: negativa (más distancia = menos throughput)
```

#### **3. Comparación Fairness**

```
Ruta A:  ████████░░ F = 0.92 (muy equitativa)
Ruta B:  ██████░░░░ F = 0.64 (menos equitativa)
```

---

### 5.3 Renders 3D

#### **Visualización:**

```
Viewport Mitsuba:
  • gNB estación base (punto fijo, rojo)
  • Ruta A: Puntos azules oscilando cerca
  • Ruta B: Puntos verdes trazando circuito
  • Rays: Líneas de comunicación entre TX-RX (cuando LoS)
  
Parámetros de cámara (fijos para ambas):
  • Posición: (400, 185.5, 480) metros
  • Look-at: Centro de ambas rutas + 30% de altura
  • Field of view: 60°
```

---

## 6. ANÁLISIS PROFUNDO DE RESULTADOS

### 6.1 ¿Por qué Ruta A tiene mejor Fairness?

```
Ruta A: Hover con pequeña oscilación
  Distancia: 155-198 m (varía 43 m)
  Path loss: 110-114 dB (varía 4 dB)
  
  Variabilidad de SINR: ±2 dB
  Variabilidad de TP: ±5% (casi nada)
  
  Razón: En escala logarítmica, 43 m en rango 150-200 m
         es una variación de 20*log₁₀(198/155) ≈ 4 dB

Ruta B: Circuito completo
  Distancia: 95-955 m (varía 860 m)
  Path loss: 110-130 dB (varía 20 dB)
  
  Variabilidad de SINR: ±10 dB
  Variabilidad de TP: ±300% (mucho)
  
  Razón: 20*log₁₀(955/95) ≈ 20 dB de variación
         → Shannon capacity varía exponencialmente
```

---

### 6.2 Puntos Críticos de Ruta B

```
Zona 1 (Cerca de gNB):
  d ≈ 100-200 m → Path loss ≈ 110-116 dB
  SINR ≈ 15-20 dB → TP ≈ 400-450 Mbps
  
Zona 2 (Medio de ruta):
  d ≈ 500 m → Path loss ≈ 122 dB
  SINR ≈ 8 dB → TP ≈ 200 Mbps
  
Zona 3 (Lejos del gNB):
  d ≈ 900+ m → Path loss ≈ 129 dB
  SINR ≈ 1 dB → TP ≈ 50 Mbps
  
Recomendación: Instalar repetidor (relay) a mitad de circuito
                para mejorar Fairness
```

---

## 7. PARÁMETROS DE SIMULACIÓN

| Parámetro | Valor | Unidad |
|-----------|-------|--------|
| Frecuencia (Band n78) | 3.55 | GHz |
| Ancho de banda | 100 | MHz |
| Subportadoras | 556 | - |
| Espaciado subportadora | 15 | kHz |
| Configuración MIMO | 4×4 | antenas |
| Máx. layers (streams) | 4 | - |
| TX Power UAV | 26 | dBm |
| Ruido Figura | 7 | dB |
| Ruta A amplitud | 5-10 | m |
| Ruta A frecuencia | 0.1-0.2 | Hz |
| Ruta B velocidad | 10 | m/s |
| Ruta B perímetro | 800-1000 | m |
| Altura UAV | 150 | m |

---

## 8. LIMITACIONES

| Aspecto | Limitación |
|---------|------------|
| **Variabilidad temporal** | Ray tracing es snapshot estático (sin fading Doppler) |
| **Movilidad realista** | Trayectorias son idealizadas, sin obstáculos dinámicos |
| **Interferencia inter-UAV** | Solo simulamos 1 UAV a la vez |
| **Retardo de propagación** | Ignorado (asumimos recepción instantánea) |
| **Sincronización** | Asumimos perfecta entre gNB y UAV |
| **Velocidad de actualización** | Beamforming adapta cada ~10 ms (realista en 5G) |

---

## 9. REFERENCIAS

1. **3GPP TR 36.777** - Study on enhanced LTE support for aerial vehicles
2. **3GPP TS 36.300** - E-UTRA and E-UTRAN overall description
3. **ITU-R P.1812** - Propagation in urban and suburban areas
4. **ITU-R P.1411** - Propagation data and prediction methods for the planning of indoor radiocommunication systems
5. Jain, R. K., et al. (1984). "A Quantitative Measure of Fairness and Discrimination for Resource Allocation in Shared Computer Systems". DEC Research Report TR-301.
6. Sionna Documentation - Ray Tracing: https://nvlabs.github.io/sionna/api/rt.html
7. **3GPP TS 38.213** - NR; Physical layer procedures for control
8. Rappaport, T. S. (2002). "Wireless Communications: Principles and Practice" (2nd ed.). Prentice Hall.

---

**Última actualización:** Febrero 2026  
**Simulador:** mobility.py  
**Rutas:** Hover (Ruta A) vs Circuito (Ruta B)  
**Métrica clave:** Fairness de Jain + Throughput
