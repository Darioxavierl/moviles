# Marco Teórico: Técnicas MIMO de Beamforming y Precoding
## Simulación: `mimo_beam.py`

---

## 1. BASE TEÓRICA 5G NR - MIMO

### 1.1 Massive MIMO en 5G

**3GPP TS 38.875 - Study on 3D beamforming and Channel Models for RAN Enhancement**

5G NR introduce **Massive MIMO** como diferenciador clave:

```
Massive MIMO = Múltiples antenas en TX y RX
              para gain, directividad y multiplexación

Configuraciones en simulación:
  • SISO:      1×1   (sin antenas, sin beamforming)
  • MIMO 2x2:  2×2   (4 antenas, 2 streams máx)
  • MIMO 4x4:  4×4   (16 antenas, 4 streams máx) ← Massive
  • MIMO 4x2:  4×4 TX, 2×2 RX (16 TX, 4 RX) ← Asimétrico
```

**Ventajas:**
1. **Ganancia de Array:** `G = 10·log₁₀(M)` donde M = número antenas
   - 4×4: `G ≈ 12 dB` de ganancia pura
2. **Multiplexación Espacial:** Enviar múltiples streams en paralelo
3. **Beamforming:** Concentrar potencia en dirección de usuario
4. **Diversidad:** Combinar señales de múltiples rutas

**Referencia:** 3GPP TS 38.875, Seción 6

---

### 1.2 Descomposición en Valores Singulares (SVD)

**Fundamento Matemático:**

```
H = U · Σ · V^H    (Descomposición SVD)

Donde:
  H    = Matriz de canal [Nᵣₓ × Nₜₓ] (compleja)
  U    = Matriz unitaria [Nᵣₓ × Nᵣₓ] (vectores propios de H·H^H)
  Σ    = Matriz diagonal [Nᵣₓ × Nₜₓ] (valores singulares σᵢ ≥ 0)
  V^H  = Matriz unitaria conjugada traspuesta [Nₜₓ × Nₜₓ]
```

**Interpretación Física:**

```
σᵢ = Ganancia de canal para stream i-ésimo
    • σ₁ ≥ σ₂ ≥ σ₃ ≥ ... (ordenados en descenso)
    • σᵢ = 0 → Canal muerto (sin comunicación en ese eje)

Número de streams activos = rank(H) = número de σᵢ significativos
```

**Ejemplo canal 4×4:**
```
σ = [1.5, 1.2, 0.8, 0.1]  → 4 streams (débil el 4to)
σ = [1.5, 1.2, 0.02, 0]   → 2 streams (solo 1,2 son significativos)
```

---

## 2. TRES TÉCNICAS IMPLEMENTADAS

### 2.1 SVD Multi-Stream Beamforming

#### **Concepto:**

```
Precoding TX:  W = V[:, 0:r]           (primeras r columnas de V)
Combining RX:  U = U[:, 0:r]           (primeras r columnas de U)
Canal efectivo: H_eff = U^H @ H @ W   (debería ser diagonal)
```

#### **Física:**

```
Los vectores singulares V y U apuntan en direcciones donde el canal
transmite información SIN INTERFERENCIA ENTRE STREAMS.

V ← Dirección óptima en el espacio TX
U ← Dirección óptima en el espacio RX

Cuando aplicas W y U, transformas el canal H en diagonal:

       ┌                        ┐
H_eff =│ σ₁  0    0    0    │  
       │ 0   σ₂  0    0    │  ← Streams desacoplados
       │ 0   0   σ₃  0    │
       │ 0   0   0   σ₄  │
       └                        ┘

Cada stream siente solo su singular value, SIN crosstalk.
```

#### **Ventajas:**
- ✅ **Dinámico:** Adapta r (número de streams) al rank del canal
- ✅ **Óptimo:** Máxima capacidad teórica
- ✅ **Acoplamiento nulo:** Cada stream es independiente

#### **Número de Streams:**

```python
# Línea 189-207 en mimo_beam.py
rank = sum(S > 0.0001 * max(S))  # Cuántos σᵢ son significativos

Para 4×4 Massive MIMO:
  • Mejor caso (LOS perfecto): rank = 4 (4 streams)
  • Caso típico (fading): rank = 2-3 (2-3 streams)
  • Caso degradado (obstáculos): rank = 1-2 (1-2 streams)
```

#### **Cálculo SINR:**

```
SINR_i = (P_TX / Nᵣ) × σᵢ² / N

Donde:
  P_TX = Potencia TX total
  Nᵣ = Número de streams activos (dinámico!)
  σᵢ = Valor singular i-ésimo
  N = Potencia de ruido
```

#### **Ecuación Capacidad:**

```
C = Σᵢ₌₁^Nᵣ log₂(1 + SINR_i) × B

Sumatorio sobre todos los streams activos.
Máxima throughput cuando se usan todos los streams significativos.
```

**Referencia:** Forouzan, F., et al. (2016). "MIMO Wireless Communications"

---

### 2.2 MRC Beamforming (Maximum Ratio Combining)

#### **Concepto:**

```
Solo 1 stream transmitido, pero con diversidad TX y RX.

TX Beamforming:  w_tx = conj(H^T) / ||H||  (Matched Filter)
RX Combining:    w_rx = conj(H) / ||H||    (MRC)

Canal efectivo:  h_eff = w_rx^H @ H @ w_tx  (escalar)
```

#### **Física:**

```
MRC alinea fase de todas las antenas RX con la señal llegada:

Antena RX1: φ₁ ────────┐
Antena RX2: φ₂ ────┐   │
Antena RX3: φ₃ ──┐ │   │  ┌────> Suma coherente (constructiva)
Antena RX4: φ₄ ─┐ │ │   │  │

Desfases corregidos:
  w_rx = [e^(-jφ₁), e^(-jφ₂), e^(-jφ₃), e^(-jφ₄)]

Resultado: Todas las señales suman en fase → SINR máximo
```

#### **Ventajas:**
- ✅ **Robusto:** Funciona con cualquier canal
- ✅ **Simple:** Solo sumas conjugadas, sin SVD
- ✅ **Diversidad:** Combina múltiples antenas

#### **Desventajas:**
- ❌ **Solo 1 stream:** No multiplexación espacial
- ❌ **Subóptimo:** Usa solo 1 dirección del canal

#### **Cálculo SINR:**

```
SINR_MRC = P_TX × ||H||² / N

Ganancia de array factor: ||H||² ≈ 16 (para 4×4 con LOS)
                          × factor de fading

Típicamente: SINR_MRC > SINR_SVD_por_stream (porque sin compartir potencia)
             Pero: SINR_SVD_total > SINR_MRC_total (por múltiples streams)
```

**Referencia:** Proakis, J. G. (2000). "Digital Communications"

---

### 2.3 Zero Forcing (ZF) Precoding

#### **Concepto:**

```
Precoding TX: W = H^H (H·H^H)⁻¹

Objetivo: Invertir el canal para enviar streams descorrelados
          (eliminar Inter-Stream Interference - ISI)

Canal resultante: H_eff = H @ W ≈ I (matriz identidad)
```

#### **Física:**

```
Si no hubiera ruido:
  H_eff = H @ W = H @ H^H (H·H^H)⁻¹
        = (H @ H^H) @ (H @ H^H)⁻¹  = I ✓

Con ruido amplificado (por eso "Zero Forcing" es subóptimo):
  W "invierte" el canal pero amplifica ruido en direcciones débiles.
```

#### **Diferencia con SVD:**

| Aspecto | SVD | Zero Forcing |
|---------|-----|--------------|
| Streams | Dinámico (1-4) | **Fijo** (siempre 4) |
| Adaptación | Sí (rank del canal) | No |
| Eficiencia | Usa solo streams buenos | **Usa streams débiles** |
| Amplificación de ruido | Minimal | **Alta** |
| Throughput | Óptimo | Subóptimo |

#### **Cálculo SINR:**

```
SINR_ZF_i = (P_TX / Nₛₜᵣₑₐₘₛ) × |diagonal(H_eff)_i|² / (N × amplificación_ruido)

Problema: Si σ₄ es muy pequeño, la inversa de H·H^H amplifica
          la componente asociada → Ruido muy alto en stream 4.
```

#### **Amplificación de Ruido:**

```
Gain amplificación = ||W||² / ||W_scaled||²

Para matrices mal condicionadas:
  κ(H) = σ₁/σₙ >> 1 → Amplificación >> 1 (malo!)
  κ(H) = σ₁/σₙ ≈ 1  → Amplificación ≈ 1 (bueno)

Ejemplo: κ = 100 → Amplificación de ruido 100× en algunos streams
```

**Referencia:** Goldsmith, A. (2005). "Wireless Communications"

---

## 3. CONFIGURACIONES MIMO EN SIMULACIÓN

### 3.1 Configuración MIMO 4×4

```python
class MIMO_Configuration:
    tx_rows = 4, tx_cols = 4    # 16 antenas TX
    rx_rows = 4, rx_cols = 4    # 16 antenas RX
    max_layers = min(16, 16) = 4  # Máximo 4 streams paralelos
```

**Canales posibles:**
```
• LOS (Line-of-Sight):      rank = 4 (4 streams activos)
• NLOS (sin visibilidad):   rank = 2-3
• Deep fade:                rank = 1

Típicamente indoor: rank ≈ 2-3
Típicamente outdoor LOS: rank = 4
```

### 3.2 Polarización VH (Vertical + Horizontal)

```
Cada antena física recibe:
  • Componente Vertical (V)
  • Componente Horizontal (H)

Efecto en simulación: Dobla el número de canales decorrelados
  
  Antenas efectivas = 4×4 × 2 (polarización) = 128 "rays" visuales
  Pero rank aún limitado por dimensionalidad espacial = 4
```

---

## 4. FLUJO DE SIMULACIÓN

### Paso 1: Ray Tracing

```
Para cada configuración MIMO:
  1. Resolver paths gNB (TX) ↔ UAV (RX)
  2. Extraer CFR (Channel Frequency Response)
  3. Canal H[Nrx, Ntx] ← promedio sobre subportadoras
```

### Paso 2: SVD Beamforming

```python
# Línea 446-470
for k in range(num_subcarriers):
    Hk = CFR_en_subportadora_k  # Matriz compleja
    W, U, S, rank = svd_multistream_beamforming(Hk)
    H_eff = U^H @ Hk @ W
    
    # Extraer ganancias
    h_diag = diag(H_eff)  # [σ₁, σ₂, σ₃, ...]
    
    # SINR por stream
    SINR_i = (P/rank) × |σ_i|² / N
```

### Paso 3: MRC Beamforming

```python
# Línea 487-500
for k in range(num_subcarriers):
    Hk = CFR_en_subportadora_k
    w_tx = mrc_beamforming_tx(Hk)
    w_rx = mrc_beamforming_rx(Hk)
    
    h_eff = w_rx^H @ Hk @ w_tx  # Escalar
    SINR = P × |h_eff|² / N
```

### Paso 4: Zero Forcing

```python
# Línea 519-550
for k in range(num_subcarriers):
    Hk = CFR_en_subportadora_k
    W = zero_forcing_precoding(Hk)
    H_eff = Hk @ W
    
    # SIEMPRE usa 4 streams (fijo!)
    h_diag = diag(H_eff)  # [h₁, h₂, h₃, h₄]
    
    SINR_i = (P/4) × |h_i|² / (N × amplificación)
```

### Paso 5: Throughput

```
TP_SVD = Σᵢ log₂(1 + SINR_SVD_i) × BW_base

TP_MRC = 1 × log₂(1 + SINR_MRC) × BW_base

TP_ZF = Σᵢ₌₁⁴ log₂(1 + SINR_ZF_i) × BW_base
```

---

## 5. SALIDAS Y MÉTRICAS

### 5.1 Tabla Comparativa

```
Columnas:
  Config          | TX  | RX  | SVD Str | SVD(Mbps) | MRC(Mbps) | ZF(Mbps) | Gain
  MIMO 2x2        | 4   | 4   | 2/2     | 450       | 380       | 430      | 0.96
  MIMO 4x4        | 16  | 16  | 3/4     | 550       | 450       | 520      | 0.95
  MIMO 4x2 Asym   | 16  | 4   | 2/2     | 480       | 420       | 470      | 0.98
```

### 5.2 SINR Promedio

```
Por técnica:
  SVD:  Promedio de SINR de todos los streams
  MRC:  SINR del único stream
  ZF:   Promedio de SINR (incluyendo streams débiles con ruido)
```

### 5.3 Gráficos

1. **Throughput Comparison**
   - Tres barras por configuración (SVD, MRC, ZF)
   - Valor en Mbps sobre cada barra

2. **Configuration Specs Table**
   - TX antennas, RX antennas, Max layers

3. **3D Ray Tracing Render**
   - Última configuración procesada
   - Posición TX, RX, rays visuales

---

## 6. RESULTADOS ESPERADOS

### Para MIMO 4×4 (Massive MIMO):

```
SVD Multi-Stream:
  • Throughput: 540-580 Mbps
  • Streams activos: 3-4
  • Distribución de potencia: Eficiente (según σᵢ)
  
MRC Single-Stream:
  • Throughput: 420-480 Mbps
  • Solo 1 stream: Menos throughput pero simple
  • Diversidad: Excelente por combinar 16 antenas
  
Zero Forcing:
  • Throughput: 500-550 Mbps
  • Streams fijos: 4 (aunque algunos débiles)
  • Amplificación de ruido: Degrada SINR en streams débiles
```

### Comparación:

```
SVD > Zero Forcing > MRC

Razón:
  1. SVD adapta número de streams (no usa débiles)
  2. MRC sacrifica multiplexación por robustez
  3. ZF intenta 4 streams pero amplifica ruido
```

---

## 7. LIMITACIONES

| Aspecto | Limitación |
|---------|------------|
| **Rank del canal** | Limitado por dimensiones espaciales, no por teoría |
| **SISO sin sentido** | Las 3 técnicas son equivalentes (1 stream) |
| **Fading** | Solo ray tracing snapshot, sin variabilidad temporal |
| **Feedback** | Precoding asume CSI perfecto en TX (no realista) |
| **Antenna coupling** | Ignora pérdidas entre antenas cercanas |

---

## 8. REFERENCIAS

1. **3GPP TS 38.875** - Study on 3D beamforming and Channel Models for RAN Enhancement
2. **3GPP TS 38.201** - NR; Services and system aspects
3. Goldsmith, A. (2005). "Wireless Communications". Stanford University Press.
4. Forouzan, F., et al. (2016). "MIMO Wireless Communications". Cambridge University Press.
5. Proakis, J. G. (2000). "Digital Communications" (4th ed.). McGraw-Hill.
6. Tse, D., & Viswanath, P. (2005). "Fundamentals of Wireless Communication". Cambridge University Press.
7. Rusek, F., et al. (2013). "Scaling Up MIMO: Opportunities and Challenges with Very Large Arrays". IEEE Signal Processing Magazine, 30(1), 40-60.
8. Sionna Documentation: https://nvlabs.github.io/sionna/

---

**Última actualización:** Febrero 2026  
**Simulador:** mimo_beam.py  
**Técnicas:** SVD Multi-Stream, MRC, Zero Forcing  
**Configuraciones:** MIMO 2×2, 4×4, 4×2 Asimétrico
