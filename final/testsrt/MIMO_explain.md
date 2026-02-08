# 📊 RESUMEN TÉCNICO DE LAS 3 TÉCNICAS EN MIMO_BEAM.PY

## 1. SVD MULTI-STREAM BEAMFORMING (Línea 428)

```
MATEMÁTICA:
  H = U · Σ · V^H (Descomposición SVD)
  TX Precoding: W = V[:, 0:r]  (primeras r columnas de V)
  RX Combining: U_keep = U[:, 0:r]  (primeras r columnas de U)
  Canal efectivo: H_eff = U^H @ H @ W  (debería ser diagonal)
```

### ¿Qué es?
- ✅ Sí es **Beamforming + Multiplexación Espacial**
- Usa **múltiples vectores singulares** simultáneamente
- **Dinámico**: Calcula el rango del canal para cada subportadora

### Streams:
- **1 a max_layers** (depende del rango del canal)
- Para 4x4: máx 4 streams
- La simulación calcula `num_streams` automáticamente por subportadora

### Cálculo en el código:
```python
# Línea 189-207: Determina rango del canal
rank = sum(S > threshold)  # Cuántos singular values significativos

# Línea 446-470: Para cada subportadora k
for k in range(num_subcarriers):
  W, U_keep, S_keep, num_streams = svd_multistream_beamforming(Hk)
  H_eff = U^H @ H @ W  # Aplicar precoding
  
  # Extraer ganancia de cada stream del diagonal de H_eff
  h_eff_diagonal = diag(H_eff)  # [num_streams]
  
  # Dividir potencia entre streams activos
  SINR_i = |h_i|² * (P_TX / num_streams) / N
```

### Ventaja: 
Adapta número de streams automáticamente según calidad del canal

---

## 2. MRC BEAMFORMING (Línea 477)

```
MATEMÁTICA:
  TX Beamforming: w_tx = conj(H^T) / ||H||  (Matched Filter)
  RX Beamforming: w_rx = conj(H) / ||H||   (Maximum Ratio Combining)
  Canal efectivo: h_eff = w_rx^H @ H @ w_tx  (scalar, 1 stream)
```

### ¿Qué es?
- ✅ Sí es **Beamforming + Diversidad**
- Solo **1 stream** (transmite un único símbolo)
- Pero recibe señal con **TX + RX diversity**

### Streams: 
⚠️ **Siempre 1**

### Cálculo en el código:
```python
# Línea 309-328: Funciones MRC
w_tx = sum(H conjugated) / norm  # Suma coherente de todas RX antennas en TX
w_rx = sum(H^T conjugated) / norm # Suma coherente de todas TX antennas en RX

# Línea 487-500: Para cada subportadora k
for k in range(num_subcarriers):
  w_tx = mrc_beamforming_tx(Hk)
  w_rx = mrc_beamforming_rx(Hk)
  
  # Canal efectivo ESCALAR (1 dato)
  h_eff = w_rx^H @ H @ w_tx  # Solo 1 número
  
  # Sin división de potencia (1 stream = potencia completa)
  SINR = |h_eff|² * P_TX / N
```

### Ventaja: 
✅ Robusto, simple, no requiere cálculos complejos

---

## 3. ZERO FORCING PRECODING (Línea 513)

```
MATEMÁTICA:
  TX Precoding: W = H^H(HH^H)^-1  (Invierte canal)
  Canal efectivo: H_eff = H @ W   (cancela ISI)
  Debería ser: H_eff ≈ I (matriz identidad)
```

### ¿Qué es?
- ✅ Sí es **Multiplexación Espacial** pura (sin la parte "adaptiva" de SVD)
- **Siempre max_layers streams** (no adapta al rango)
- **Cancela Inter-Stream Interference (ISI)**

### Streams: 
⚠️ **Fijo: max_layers**
- Para 4x4: siempre 4 streams
- Para 2x2: siempre 2 streams
- Aunque algunos canales sean débiles

### Cálculo en el código:
```python
# Línea 331-343: Zero Forcing
W = H^H @ inv(H @ H^H)  # Pseudo-inversa

# Línea 519-550: Para cada subportadora k
for k in range(num_subcarriers):
  W = zero_forcing_precoding(Hk)
  H_eff = H @ W  # Aplica precoding
  
  # Extraer ganancia de cada stream del diagonal
  h_eff_diagonal = diag(H_eff)  # [max_layers]
  
  # Dividir potencia entre MAX_LAYERS (siempre!)
  SINR_i = |h_i|² * (P_TX / max_layers) / N
```

### Desventaja: 
🚨 Puede usar streams "muertos" (canales muy débiles) → Desperdicia potencia

---

## 🔄 COMPARACIÓN RÁPIDA

| Aspecto | SVD Multi-Stream | MRC | Zero Forcing |
|---------|------------------|-----|--------------|
| **Tipo** | Beamforming + Multiplexación Espacial | Beamforming + Diversidad | Multiplexación Espacial |
| **Streams** | **Dinámico** (1 a max_layers) | **1 siempre** | **max_layers siempre** |
| **Técnica TX** | Precoding (V matrix) | Matched Filter | Pseudo-inversa (cancela ISI) |
| **Técnica RX** | Combining (U matrix) | MRC | Diagonal extraction |
| **Throughput** | Alto (adapta streams) | Medio (1 stream) | Alto (más streams) |
| **Robustez** | Media (adapta) | Alta (simple) | Baja (usa streams débiles) |
| **Complejidad** | Alta (SVD) | Baja (suma simple) | Media (matriz inversa) |
| **Potencia/Stream** | P_TX / num_streams | P_TX (completa) | P_TX / max_layers |

---

## 📈 EN LA SIMULACIÓN (para 4x4)

### Ejemplo: Subportadora k con rango 3

#### SVD:
```
num_streams = 3 (detectado automáticamente)
SINR_1 = |σ₁|² * (P/3) / N  ← Stream 1
SINR_2 = |σ₂|² * (P/3) / N  ← Stream 2
SINR_3 = |σ₃|² * (P/3) / N  ← Stream 3
TP_total = log₂(1+SINR₁) + log₂(1+SINR₂) + log₂(1+SINR₃)
```

#### MRC:
```
num_streams = 1 (fijo)
SINR_único = |h_eff_mrc|² * P / N  ← 1 solo dato
TP_total = log₂(1+SINR_único)
```

#### Zero Forcing:
```
num_streams = 4 (fijo, aunque rango es 3)
SINR_1 = |h₁|² * (P/4) / N  ← Stream 1 (bueno)
SINR_2 = |h₂|² * (P/4) / N  ← Stream 2 (bueno)
SINR_3 = |h₃|² * (P/4) / N  ← Stream 3 (bueno)
SINR_4 = |h₄|² * (P/4) / N  ← Stream 4 (muy débil, desperdicia potencia!)
TP_total = log₂(1+SINR₁) + log₂(1+SINR₂) + log₂(1+SINR₃) + log₂(1+SINR₄)
```

---

## ✅ RESPUESTAS DIRECTAS A PREGUNTAS CLAVE

1. **¿SVD es beamforming + multiplexación?** 
   - ✅ SÍ

2. **¿ZF es eso?** 
   - ✅ SÍ, pero sin adaptar streams (siempre usa max_layers)

3. **¿MRC es beamforming + diversidad?** 
   - ✅ SÍ, pero solo 1 stream

4. **Cuántos streams:** 
   - SVD = dinámico (1 a max_layers)
   - MRC = 1 (siempre)
   - ZF = max_layers (siempre)

5. **Cómo se calcula:** 
   - SVD: Línea 446 (cálculo en cada subportadora, adapta num_streams)
   - MRC: Línea 487 (cálculo simple, siempre 1 stream)
   - ZF: Línea 519 (usa max_layers fijo)

---

## 📚 REFERENCIAS EN CÓDIGO

- **SVD Multistream function:** `svd_multistream_beamforming()` (línea 175)
- **SVD Beamforming function:** `svd_beamforming()` (línea 250)
- **MRC TX function:** `mrc_beamforming_tx()` (línea 309)
- **MRC RX function:** `mrc_beamforming_rx()` (línea 318)
- **Zero Forcing function:** `zero_forcing_precoding()` (línea 331)
- **Main simulation:** `run_mimo_simulation()` (línea 345)

---

## 🎯 CONCLUSIÓN

**Para máximo throughput:** SVD Multi-Stream (adapta automáticamente)  
**Para máxima robustez:** MRC (simple y confiable)  
**Para multiplexación pura:** Zero Forcing (pero puede desperdiciar potencia en streams débiles)

