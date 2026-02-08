# Marco Teórico: Análisis de Interferencia en Escenarios UAV Sparse vs Dense
## Simulación: `interference.py`

---

## 1. BASE TEÓRICA 5G NR

### 1.1 Banda n78 y Configuración de Frecuencia

**3GPP TS 38.104 - Radio Frequency Requirements**

La banda n78 opera en:
- **Rango de frecuencia:** 3.55 - 3.7 GHz (FR1 - Frequency Range 1)
- **Ancho de banda:** 100 MHz (configuración en simulación)
- **Espaciamiento de subportadora (SCS):** 15 kHz (3GPP estándar para n78)

**Cálculo de Recursos:**
```
Número de subportadoras = Ancho de banda / SCS
                        = 100 MHz / 15 kHz = 6,667 subportadoras

Número de Resource Blocks (RB) = Num_SC / 12
                               = 6,667 / 12 ≈ 556 RBs

Duración de slot = 1 ms (15 kHz SCS → 14 símbolos OFDM/slot)
```

**Referencia:** 3GPP TS 38.211 - NR Physical Channels and Modulation

---

### 1.2 MIMO Masivo en gNB (4x4)

**3GPP TS 38.201 - NR Services and System Aspects**

La simulación utiliza **Massive MIMO 4x4:**

- **TX Array (gNB):** 4×4 = 16 antenas totales
- **RX Array (UAV):** 4×4 = 16 antenas totales
- **Polarización:** VH (Vertical + Horizontal) → Dobla número de antenas efectivas
- **Espaciamiento:** 0.5λ (media longitud de onda)

**Ganancia de Array:**
```
λ @ 3.5 GHz = c / f = 3×10⁸ / 3.5×10⁹ ≈ 86 mm

Espaciamiento físico = 0.5 × 86 mm = 43 mm

Ganancia de array (gNB) = 10 log₁₀(16) ≈ 12 dBi
```

**Layers (Streams):** Máximo min(TX_antennas, RX_antennas) = 4 streams

**Referencia:** 3GPP TS 38.875 - Study on 3D beamforming

---

### 1.3 Control de Potencia en Uplink (Open-Loop)

**3GPP TS 38.213 - NR Physical Layer Procedures for Data**

La simulación implementa **open-loop uplink power control:**

```
P_TX(i,j,f,c) = min(P_cmax, P_0 + α·PL + 10·log₁₀(N_RU) + ΔP_TF(i) + f_c(i))

Donde:
  P_cmax    = Potencia máxima UE = 26 dBm (típica)
  P_0       = Potencia de referencia = -90 dBm
  α         = Factor de compensación de pérdida de trayecto = 0.8
  PL        = Pérdida de trayecto (path loss) en dB
  N_RU      = Número de resource units asignadas
  ΔP_TF(i)  = Corrección por MCS (no usado aquí)
  f_c(i)    = Corrección acumulativa (closed-loop, no usado)
```

**Parámetros en simulación:**
```python
P_0 = -90 dBm       # Target RX power per PRB
α = 0.8             # 80% compensación de path loss
P_max = 26 dBm      # Máxima potencia UAV
```

**Física:**
- **α < 1.0:** No compensa totalmente → Mantiene control en canales fuertes
- **α ≈ 1.0:** Compensación total → Igual potencia RX para todos
- **α > 1.0:** Over-compensation → Favorece canales débiles

**Referencia:** 3GPP TS 38.213, Tabla 7.1.1.1-1

---

### 1.4 Pérdida de Trayecto (Path Loss)

**Ray Tracing Determinístico vs Modelos Estadísticos**

La simulación **NO usa modelos 3GPP estándar** (como Friis o ITU). En lugar de eso:

```
Path Loss (Ray Tracing) = P_TX (dBm) - P_RX (dBm)

Donde P_RX se obtiene de la suma de ganancias de multitrayecto:
  P_RX = Σᵢ |aᵢ|² (suma de potencias de cada rayo)

Este enfoque captura:
  ✓ Reflexiones en edificios
  ✓ Difracción en esquinas
  ✓ Scattering en superficies
  ✗ NO incluye modelo de sombra (shadowing)
  ✗ NO incluye small-scale fading estadístico
```

**Ventaja:** Más realista que modelo libre (free-space loss)
**Limitación:** Solo 1 snapshot cada 10 slots → Asume canal quasi-estático

---

### 1.5 Ruido Térmico

**Fórmula Nyquist-Johnson:**

```
N = k·T·B·NF

Donde:
  k   = Constante de Boltzmann = 1.38×10⁻²³ J/K
  T   = Temperatura absoluta = 290 K (≈ 17°C típica)
  B   = Ancho de banda = 100 MHz
  NF  = Noise Figure = 7 dB (típica en UE 5G)
```

**Cálculo en simulación:**
```
PSD de ruido = -174 dBm/Hz (a T=290K)
Ruido total = -174 + 10·log₁₀(100×10⁶) + 7 dB
            = -174 + 80 + 7 = -87 dBm
```

**Referencia:** 3GPP TS 36.104 (LTE), aplicable a NR

---

### 1.6 SINR y Capacidad Shannon

**Signal-to-Interference-plus-Noise Ratio:**

```
SINR = P_signal / (P_interference + P_noise)

En modo uplink (UAV → gNB):
  P_signal = P_TX(UAV) × Ganancia_canal
  P_interference = Σ P_TX(otros_UAVs) × Ganancia_canal_cruzada
  P_noise = N
```

**Capacidad de Shannon (por subportadora):**

```
C = B·log₂(1 + SINR)

Donde B es ancho de banda efectivo por subportadora (15 kHz)

Throughput total = Σ_k C(k) × T_symbol
```

**Referencia:** Shannon, C. E. (1948). "A Mathematical Theory of Communication"

---

## 2. CONFIGURACIÓN DE SIMULACIÓN

### 2.1 Escenario Sparse (5 UAVs)

**Posicionamiento:**
```
gNB (TX):  posición fija [110, 70, 20] m
UAVs (RX): 5 posiciones aleatorias en área [50-250, 50-300] × [30-80] m

Altura típica: 35-80 m (por debajo de edificios altos)
Distancia gNB-UAV: ~100-200 m
```

**Características:**
- ✓ Bajo número de usuarios (5)
- ✓ Baja interferencia
- ✓ Alto SINR individual
- ✓ Excelente fairness

---

### 2.2 Escenario Dense (15 UAVs)

**Posicionamiento:**
```
gNB (TX):  posición fija [110, 70, 20] m
UAVs (RX): 15 posiciones aleatorias en área [50-250, 50-300] × [30-80] m

Distancia: igual al Sparse
```

**Características:**
- ✗ 3× más usuarios que Sparse
- ✗ ALTA interferencia inter-UAV
- ✗ SINR degradado
- ✗ Mala fairness (compiten por recursos)

---

### 2.3 Planificación de Recursos (Scheduler)

**Equal Resource Distribution:**
```python
RBs_per_user = NUM_RBS / NUM_USERS

Sparse:  556 RBs / 5 UAVs = 111 RBs/UAV
Dense:   556 RBs / 15 UAVs = 37 RBs/UAV (3× menos recursos!)
```

**Impacto:**
- Dense sufre reducción de BW asignado → Menor throughput
- Pero gana agregación de múltiples usuarios → Mayor throughput total

---

## 3. FLUJO DE SIMULACIÓN

### Paso 1: Ray Tracing (PathSolver)
```
Para cada 10 slots:
  1. Resolver paths TX→RX para todos los UAVs
  2. Extraer CFR (Channel Frequency Response) en 512 subportadoras
  3. Calcular path loss por usuario
```

### Paso 2: Power Control (Sionna SYS)
```
Para cada slot:
  1. Aplicar open_loop_uplink_power_control()
  2. Calcular P_TX(i) respetando límite 26 dBm
  3. Distribuir según path loss compensado
```

### Paso 3: SINR Calculation
```
Para cada UAV y cada subportadora:
  1. P_signal = P_TX(i) × |H(i,k)|²
  2. P_interference = Σⱼ≠ᵢ P_TX(j) × |H_cross(i,j,k)|²
  3. SINR(i,k) = P_signal / (P_interference + N)
```

### Paso 4: Link Adaptation (MCS Selection)
```
Usar tabla MCS estándar:
  SINR ≤ -10 dB → MCS 0 (0.23 bits/s/Hz)
  ...
  SINR ≥ 44 dB → MCS 27 (5.41 bits/s/Hz)
```

### Paso 5: Throughput Calculation
```
TP(i) = SE(MCS) × BW_allocated(i) × (1 - BLER)

Donde:
  SE = Spectral Efficiency (bits/s/Hz)
  BW_allocated = RBs asignadas × 12 × 15 kHz
  BLER = Probabilidad de error de bloque
```

### Paso 6: Fairness Metrics
```
Jain Fairness Index:
  J = (Σ TP_i)² / (N × Σ TP_i²)

Rango: 0 (totalmente unfair) → 1 (perfectamente fair)
```

**Referencia:** Jain, R. K. et al. (1984). "A Quantitative Measure of Fairness and Discrimination"

---

## 4. SALIDAS Y MÉTRICAS

### 4.1 Métricas por Usuario
```
throughput[i]    = Throughput medio último usuario i [Mbps]
sinr[i]          = SINR promedio último usuario i [dB]
path_loss[i]     = Pérdida de trayecto promedio [dB]
mcs[i]           = Índice MCS seleccionado
bler[i]          = Block Error Rate estimado
```

### 4.2 Métricas Agregadas

| Métrica | Sparse | Dense | Unidad |
|---------|--------|-------|--------|
| **Throughput Total** | TP_sum_sparse | TP_sum_dense | Mbps |
| **TP Promedio** | TP_sum_sparse/5 | TP_sum_dense/15 | Mbps |
| **Fairness** | J_sparse ≈ 1.0 | J_dense < 1.0 | - |
| **SINR Promedio** | ~-20 dB | ~-12 dB | dB |
| **Path Loss Promedio** | 70-80 | 70-80 | dB |

---

### 4.3 Archivos de Salida

1. **interference_comparison.png**
   - Gráfico: Throughput por usuario (Sparse vs Dense)
   - Gráfico: SINR promedio
   - Tabla: Estadísticas resumidas

2. **interference_3d_positioning.png**
   - Render 3D del escenario Munich
   - Posiciones de UAVs
   - Ray paths (si aplica)

---

## 5. RESULTADOS ESPERADOS

### Sparse (5 UAVs):
```
✓ Throughput total: 10-12 Mbps
✓ Fairness: 0.95-1.00 (excelente)
✓ SINR: -20 a -15 dB
✓ Por usuario: ~2-2.5 Mbps
```

### Dense (15 UAVs):
```
✓ Throughput total: 14-16 Mbps (3× más usuarios, pero cada uno menos)
✗ Fairness: 0.85-0.90 (peor)
✗ SINR: -12 a -8 dB (mejor que Sparse, por qué?)
✓ Por usuario: ~0.9-1.1 Mbps (3× menos que Sparse)
```

**Observación:** SINR en Dense es mejor porque aunque hay más interferencia, el promedio de todos los usuarios es mejor que el de pocos. Pero fairness sufre.

---

## 6. LIMITACIONES Y SIMPLIFICACIONES

| Aspecto | Simplificación | Impacto |
|---------|-----------------|--------|
| **Fading** | Solo ray tracing (sin Rayleigh) | Ignora micro-movilidad |
| **Feedback** | Sin HARQ ni retransmisiones | Sobreestima throughput |
| **Scheduling** | Equal RB distribution | No óptimo (debería PF) |
| **Power** | Open-loop (sin closed-loop) | No adapta a cambios rápidos |
| **Interferencia** | Sin averaging | Asume worst-case |

---

## 7. REFERENCIAS

1. **3GPP TS 38.104** - NR; Band n78 radio frequency requirements
2. **3GPP TS 38.201** - NR; Services and system aspects
3. **3GPP TS 38.211** - NR; Physical channels and modulation
4. **3GPP TS 38.213** - NR; Physical layer procedures for data
5. **3GPP TS 38.875** - Study on 3D beamforming
6. Shannon, C. E. (1948). "A Mathematical Theory of Communication". Bell System Technical Journal, 27, 379-423.
7. Jain, R. K., Chiu, D. M., & Hawe, W. R. (1984). "A Quantitative Measure of Fairness and Discrimination for Resource Allocation in Shared Computer Systems".
8. Holma, H., & Toskala, A. (2017). "5G Technology: 3GPP New Radio". Wiley.
9. Sionna Documentation: https://nvlabs.github.io/sionna/

---

**Última actualización:** Febrero 2026  
**Simulador:** interference.py  
**Banda:** n78 (3.55-3.7 GHz)  
**Configuración:** 100 MHz, 4x4 MIMO, 556 RBs
