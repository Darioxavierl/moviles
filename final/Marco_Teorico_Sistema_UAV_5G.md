# Marco Teórico: Sistema de Simulación UAV 5G NR con Sionna

**Proyecto:** Sistema de Análisis y Simulación de Comunicaciones UAV en Redes 5G NR  
**Framework:** Sionna (NVIDIA) - Ray Tracing y System Level Simulation  
**Fecha:** Febrero 2026

---

## Tabla de Contenidos

1. [Introducción](#1-introducción)
2. [Fundamentos de 5G New Radio (NR)](#2-fundamentos-de-5g-new-radio-nr)
3. [UAVs en Comunicaciones Inalámbricas](#3-uavs-en-comunicaciones-inalámbricas)
4. [Propagación y Modelado de Canal](#4-propagación-y-modelado-de-canal)
5. [Sistemas MIMO y Beamforming](#5-sistemas-mimo-y-beamforming)
6. [Movilidad y Efectos Doppler](#6-movilidad-y-efectos-doppler)
7. [Interferencia en Sistemas Multi-Usuario](#7-interferencia-en-sistemas-multi-usuario)
8. [Framework Sionna](#8-framework-sionna)
9. [Arquitectura del Sistema Implementado](#9-arquitectura-del-sistema-implementado)
10. [Análisis por Fases de Simulación](#10-análisis-por-fases-de-simulación)
11. [Configuraciones Técnicas](#11-configuraciones-técnicas)
12. [Flujo de Trabajo Completo](#12-flujo-de-trabajo-completo)
13. [Resultados y Métricas](#13-resultados-y-métricas)
14. [Conclusiones](#14-conclusiones)

---

## 1. Introducción

### 1.1 Contexto y Motivación

Las redes de quinta generación (5G) representan un salto cualitativo en las comunicaciones móviles, ofreciendo capacidades mejoradas para soportar aplicaciones emergentes que demandan alta velocidad de transmisión, baja latencia y alta confiabilidad. Entre estas aplicaciones, los **Vehículos Aéreos No Tripulados (UAVs)** han ganado relevancia como plataforma para comunicaciones aéreas, relay, cobertura temporal y monitoreo en tiempo real.

La integración de UAVs en redes 5G presenta desafíos únicos:
- **Canales de propagación tridimensionales complejos** con alta probabilidad de Línea de Vista (LoS)
- **Efectos Doppler significativos** debido a la movilidad aérea
- **Interferencia multi-usuario** en escenarios densos
- **Optimización de altura** para balance entre cobertura y capacidad

### 1.2 Objetivos del Sistema

El presente sistema de simulación tiene como objetivos:

1. **Evaluar configuraciones MIMO y técnicas de beamforming** para optimizar el enlace gNB → UAV
2. **Analizar el impacto de la altura** en throughput, path loss y probabilidad LoS
3. **Estudiar patrones de movilidad** y su efecto en la continuidad del servicio
4. **Caracterizar escenarios de interferencia multi-UAV** y estrategias de mitigación

### 1.3 Alcance del Documento

Este marco teórico documenta:
- **Fundamentos teóricos** de 5G NR, UAVs, propagación, MIMO y movilidad
- **Framework Sionna** y sus módulos RT (Ray Tracing) y SYS (System Level)
- **Implementación completa** del sistema con 4 fases de análisis
- **Configuraciones técnicas** utilizadas en cada simulación
- **Flujo de trabajo** desde la GUI hasta la generación de resultados

---

## 2. Fundamentos de 5G New Radio (NR)

### 2.1 Arquitectura de 5G NR

5G New Radio es el estándar de interfaz de radio definido por 3GPP para redes de quinta generación. Se caracteriza por:

#### 2.1.1 Arquitectura de Red

La arquitectura 5G NR se compone de:

- **gNB (Next Generation NodeB)**: Estación base que implementa la capa física y MAC
- **UE (User Equipment)**: Equipos terminales (en este caso, UAVs)
- **Core Network (5GC)**: Red central basada en arquitectura de servicios

#### 2.1.2 Bandas de Frecuencia

5G NR opera en dos rangos de frecuencia:

- **FR1 (Sub-6 GHz)**: 450 MHz - 6 GHz
  - **Banda n78**: 3.3 - 3.8 GHz (usada en este sistema: **3.5 GHz**)
  - Mayor cobertura, menor capacidad
  
- **FR2 (mmWave)**: 24.25 - 52.6 GHz
  - Mayor capacidad, menor cobertura
  - Requiere beamforming masivo

**Configuración del Sistema:**
```
Frecuencia: 7.125 GHz (banda n78 - 5G NR)
Ancho de Banda: 100 MHz
```

### 2.2 Estructura de Recursos en 5G NR

#### 2.2.1 OFDM (Orthogonal Frequency Division Multiplexing)

5G NR utiliza OFDM como tecnología de acceso múltiple:

- **Subportadoras ortogonales** espaciadas según numerología
- **Múltiples numerologías** (μ = 0, 1, 2, 3, 4) para diferentes escenarios
- **Escalabilidad** en ancho de banda y latencia

#### 2.2.2 Numerología y Espaciado de Subportadoras

La numerología define el espaciado entre subportadoras:

| Numerología (μ) | Δf (kHz) | Símbolo OFDM (μs) | Aplicación |
|----------------|----------|-------------------|------------|
| 0 | 15 | 66.67 | LTE compatibility |
| 1 | 30 | 33.33 | Sub-6 GHz (**usado**) |
| 2 | 60 | 16.67 | Sub-6 GHz alta movilidad |
| 3 | 120 | 8.33 | mmWave |
| 4 | 240 | 4.17 | mmWave alta velocidad |

**Configuración del Sistema:**
```
Espaciado de Subportadora: 30 kHz (μ = 1)
Resource Blocks (RBs): 273 RBs
Total Subportadoras: 273 × 12 = 3,276 subportadoras
Ancho de Banda Efectivo: 3,276 × 30 kHz ≈ 98.28 MHz
```

#### 2.2.3 Resource Blocks y Slots

- **Resource Block (RB)**: Unidad mínima de asignación de recursos
  - 12 subportadoras consecutivas
  - 1 slot en el dominio del tiempo
  
- **Slot**: Conjunto de símbolos OFDM
  - 14 símbolos OFDM por slot (prefijo cíclico normal)
  - Duración: 0.5 ms para μ=1

### 2.3 Capacidad Teórica y Throughput

#### 2.3.1 Teorema de Shannon-Hartley

La capacidad teórica de un canal está dada por:

$$C = B \log_2(1 + \text{SNR})$$

Donde:
- $C$: Capacidad del canal (bits/s)
- $B$: Ancho de banda (Hz)
- $\text{SNR}$: Relación señal-ruido (lineal)

Para un sistema MIMO con $N_t$ antenas transmisoras y $N_r$ antenas receptoras:

$$C_{\text{MIMO}} = \min(N_t, N_r) \cdot B \log_2(1 + \text{SNR})$$

#### 2.3.2 Eficiencia Espectral

La eficiencia espectral se mide en bits/s/Hz:

$$\eta = \frac{C}{B} = \log_2(1 + \text{SNR})$$

Con MIMO:
$$\eta_{\text{MIMO}} = \min(N_t, N_r) \cdot \log_2(1 + \text{SNR})$$

**Ejemplo en el Sistema:**
- Para MIMO 16×8 con SNR = 20 dB (100 lineal):
  ```
  η = min(16, 8) × log₂(1 + 100) ≈ 8 × 6.66 = 53.28 bits/s/Hz
  Throughput = 53.28 × 100 MHz = 5,328 Mbps (teórico)
  ```

### 2.4 Parámetros de Calidad de Servicio (QoS)

#### 2.4.1 Métricas Principales

1. **Throughput**: Tasa de datos efectiva transmitida
   - Unidad: Mbps
   - Objetivo: > 100 Mbps para UAV

2. **Latencia**: Retardo end-to-end
   - Objetivo 5G: < 1 ms (URLLC), < 10 ms (eMBB)

3. **BLER (Block Error Rate)**: Tasa de error de bloques
   - Objetivo típico: BLER < 10% (0.1)

4. **SNR/SINR**: Relación señal-ruido/(interferencia+ruido)
   - Rango típico: 0 - 30 dB
   - SNR > 20 dB: Excelente calidad

#### 2.4.2 Link Budget

El link budget calcula la potencia recibida:

$$P_{rx} = P_{tx} + G_{tx} + G_{rx} - L_{path} - L_{shadow} - L_{fast}$$

Donde:
- $P_{tx}$: Potencia transmitida (43 dBm para gNB)
- $G_{tx}$, $G_{rx}$: Ganancias de antena
- $L_{path}$: Path loss
- $L_{shadow}$: Shadowing
- $L_{fast}$: Fast fading

---

## 3. UAVs en Comunicaciones Inalámbricas

### 3.1 Características de los Canales UAV

Los canales aire-tierra presentan características únicas:

#### 3.1.1 Alta Probabilidad de Línea de Vista (LoS)

A diferencia de los canales terrestres, los UAVs típicamente tienen:
- **Mayor probabilidad de LoS** debido a la altura
- **Menor obstrucción** por edificios y obstáculos
- **Path loss más predecible** en condiciones LoS

La probabilidad de LoS depende de:
- **Altura del UAV** ($h$)
- **Distancia horizontal** ($d$)
- **Densidad de edificios** en el entorno

Modelo empírico ITU-R para entornos urbanos:

$$P_{\text{LoS}} = \frac{1}{1 + a \cdot e^{-b(\theta - a)}}$$

Donde $\theta = \arctan(h/d)$ es el ángulo de elevación.

#### 3.1.2 Clasificación de Canales

Los canales UAV se clasifican en:

1. **Air-to-Ground (A2G)**: UAV → Estación terrestre
   - Downlink de sensores, video, telemetría
   
2. **Ground-to-Air (G2A)**: Estación terrestre → UAV (**implementado**)
   - Uplink de comandos, datos 5G
   
3. **Air-to-Air (A2A)**: UAV → UAV
   - Enlaces relay, coordinación multi-UAV

### 3.2 Modelos de Path Loss para UAV

#### 3.2.1 Free Space Path Loss (FSPL)

En condiciones ideales de espacio libre:

$$L_{\text{FSPL}}(d) = 20\log_{10}(d) + 20\log_{10}(f) + 32.45$$

Donde:
- $d$: Distancia en km
- $f$: Frecuencia en MHz
- Resultado en dB

Para 3.5 GHz y 100m:
```
L_FSPL = 20×log₁₀(0.1) + 20×log₁₀(3500) + 32.45
       = -20 + 70.88 + 32.45 = 83.33 dB
```

#### 3.2.2 Modelo LoS/NLoS Dual

El path loss depende de la condición del canal:

**LoS (Line of Sight):**
$$L_{\text{LoS}} = L_{\text{FSPL}} + \eta_{\text{LoS}}$$

**NLoS (Non-Line of Sight):**
$$L_{\text{NLoS}} = L_{\text{FSPL}} + \eta_{\text{NLoS}} + L_{\text{extra}}$$

Donde:
- $\eta_{\text{LoS}}$ ≈ 1-3 dB (pérdidas adicionales menores)
- $\eta_{\text{NLoS}}$ ≈ 20-30 dB (pérdidas por obstrucción)
- $L_{\text{extra}}$: Pérdidas por difracción/scattering

### 3.3 Impacto de la Altura

La altura del UAV es un parámetro crítico que afecta:

#### 3.3.1 Path Loss vs Altura

- **Baja altura (< 50m)**: 
  - Mayor obstrucción por edificios
  - NLoS dominante
  - Path loss alto
  
- **Altura media (50-150m)**:
  - Balance LoS/NLoS
  - Zona óptima para throughput
  
- **Alta altura (> 200m)**:
  - LoS dominante
  - Path loss aumenta por distancia
  - Mayor interferencia a otras celdas

#### 3.3.2 Altura Óptima

Existe una **altura óptima** que maximiza el throughput:

$$h_{\text{opt}} = \arg\max_{h} \left[ \text{Throughput}(h) \right]$$

Factores que la determinan:
- Balance entre probabilidad LoS (aumenta con $h$)
- Distancia 3D al gNB (aumenta con $h$)
- Interferencia (aumenta con $h$)

**Resultado en el Sistema:** $h_{\text{opt}}$ ≈ 40-80m para Munich urbano

### 3.4 Aplicaciones de UAV en 5G

#### 3.4.1 Casos de Uso

1. **Relay Aéreo**: Extensión de cobertura temporal
2. **Hotspot Móvil**: Cobertura en eventos masivos
3. **Monitoreo y Vigilancia**: Video HD en tiempo real
4. **IoT Aéreo**: Sensores distribuidos
5. **Emergency Communications**: Respuesta a desastres

#### 3.4.2 Requisitos Específicos

- **Throughput**: 50-500 Mbps (dependiendo de aplicación)
- **Latencia**: < 20 ms (control), < 50 ms (video)
- **Confiabilidad**: > 99% (crítico para control)
- **Movilidad**: Soporte hasta 100 km/h

---

## 4. Propagación y Modelado de Canal

### 4.1 Ray Tracing 3D

El **Ray Tracing** es una técnica determinista de modelado de propagación que simula la trayectoria de ondas electromagnéticas en entornos 3D.

#### 4.1.1 Principios de Ray Tracing

El método se basa en:

1. **Trazado de Rayos**: Lanzamiento de rayos desde TX hacia RX
2. **Interacciones con Objetos**:
   - **Reflexión**: Rebote en superficies metálicas/dieléctricas
   - **Refracción**: Penetración en materiales
   - **Difracción**: Contorno de bordes
   - **Scattering**: Dispersión en superficies rugosas

3. **Cálculo de Paths**: Cada rayo genera un path con:
   - Retraso de propagación ($\tau$)
   - Atenuación compleja ($\alpha$)
   - Ángulos de salida/llegada (AoD/AoA)
   - Polarización

#### 4.1.2 Respuesta Impulsiva del Canal

La respuesta impulsiva en el dominio del tiempo:

$$h(t) = \sum_{i=1}^{N_{\text{paths}}} \alpha_i \cdot \delta(t - \tau_i)$$

Donde:
- $N_{\text{paths}}$: Número de paths calculados
- $\alpha_i$: Atenuación compleja del path $i$
- $\tau_i$: Retraso del path $i$

#### 4.1.3 Respuesta en Frecuencia

Para sistemas OFDM, se requiere la respuesta en frecuencia:

$$H(f) = \sum_{i=1}^{N_{\text{paths}}} \alpha_i \cdot e^{-j2\pi f \tau_i}$$

**Implementación en Sionna:**
```python
# Calcular paths con ray tracing
paths = path_solver(scene, max_depth=5)

# Obtener respuesta en frecuencia
frequencies = sionna.rt.subcarrier_frequencies(num_subcarriers, subcarrier_spacing)
h_freq = paths.cfr(frequencies)  # Channel Frequency Response
```

### 4.2 Escenario Munich 3D

#### 4.2.1 Características del Escenario

El escenario **Munich** de Sionna incluye:

- **6 Edificios 3D** con geometría realista
- **Materiales definidos**: Concreto, vidrio, metal
- **Área**: 500m × 500m aproximadamente
- **Altura de edificios**: 10m - 50m

#### 4.2.2 Configuración del Escenario

```python
# Cargar escena Munich
scene = sionna.rt.load_scene(sionna.rt.scene.munich)
scene.frequency = 7.125e9  # 3.5 GHz
scene.synthetic_array = True

# Posición gNB
gNB_position = [0, 0, 30]  # 30m altura sobre edificio

# Posición UAV (variable)
UAV_position = [100, 100, 100]  # Altura ajustable
```

#### 4.2.3 Parámetros de Ray Tracing

**max_depth**: Máximo número de reflexiones
- **max_depth = 5** (configurado)
- Balance entre precisión y tiempo de cómputo
- Captura paths LoS + 1-5 reflexiones

**num_samples**: Número de rayos lanzados
- Mayor número → mayor precisión
- Sionna maneja esto automáticamente

### 4.3 Análisis de Condiciones de Canal

#### 4.3.1 Métricas de Canal

El sistema calcula:

1. **Channel Gain** ($|H|^2$): Potencia del canal
   ```python
   channel_power = tf.reduce_mean(tf.abs(h_freq) ** 2)
   channel_gain_db = 10 * log10(channel_power)
   ```

2. **Path Loss**: Inverso del channel gain
   ```python
   path_loss_db = -channel_gain_db
   ```

3. **Número de Paths**: Cantidad de trayectorias significativas

4. **Delay Spread**: Dispersión temporal de los paths
   $$\tau_{\text{rms}} = \sqrt{\frac{\sum_i |\alpha_i|^2 \tau_i^2}{\sum_i |\alpha_i|^2} - \left(\frac{\sum_i |\alpha_i|^2 \tau_i}{\sum_i |\alpha_i|^2}\right)^2}$$

#### 4.3.2 Condición LoS/NLoS

Determinación de condición LoS:

```python
def analyze_channel_conditions(paths):
    # Extraer amplitudes de paths
    path_amplitudes = tf.abs(paths.a[0, 0, 0, 0, :])  # [num_paths]
    
    # Path más fuerte (índice 0 típicamente es LoS si existe)
    strongest_path_idx = tf.argmax(path_amplitudes)
    strongest_power = path_amplitudes[strongest_path_idx]
    
    # Si el path más fuerte es significativamente mayor → LoS
    is_los = strongest_path_idx == 0 and strongest_power > threshold
    
    return {'is_los': is_los, 'num_paths': len(path_amplitudes)}
```

### 4.4 Ventajas de Ray Tracing vs Modelos Estadísticos

| Aspecto | Ray Tracing | Modelos Estadísticos |
|---------|-------------|----------------------|
| Precisión | Alta (determinista) | Media (promedio) |
| Geometría 3D | Explícita | Paramétrica |
| Validación | Mapa real | Parámetros empíricos |
| Costo computacional | Alto | Bajo |
| Aplicación | Diseño específico | Evaluación general |

**En este sistema**: Se usa Ray Tracing para análisis realista de escenarios urbanos complejos.

---

## 5. Sistemas MIMO y Beamforming

### 5.1 Fundamentos de MIMO

**MIMO (Multiple-Input Multiple-Output)** utiliza múltiples antenas en transmisor y receptor para mejorar capacidad y confiabilidad.

#### 5.1.1 Modelo de Sistema MIMO

El modelo matemático de un sistema MIMO:

$$\mathbf{y} = \mathbf{H} \mathbf{x} + \mathbf{n}$$

Donde:
- $\mathbf{y}$: Vector recibido ($N_r \times 1$)
- $\mathbf{H}$: Matriz de canal ($N_r \times N_t$)
- $\mathbf{x}$: Vector transmitido ($N_t \times 1$)
- $\mathbf{n}$: Ruido AWGN ($N_r \times 1$)

#### 5.1.2 Ganancias de MIMO

MIMO proporciona tres tipos de ganancia:

1. **Ganancia de Array (Array Gain)**:
   - Mejora SNR proporcional al número de antenas
   - Factor: $\sqrt{N_t \cdot N_r}$ en potencia

2. **Ganancia de Diversidad (Diversity Gain)**:
   - Combate desvanecimiento
   - Reduce probabilidad de error
   - Orden de diversidad: $N_t \times N_r$

3. **Ganancia de Multiplexación (Multiplexing Gain)**:
   - Aumenta capacidad sin ancho de banda adicional
   - Streams paralelos: $\min(N_t, N_r)$

#### 5.1.3 Capacidad MIMO

La capacidad de un canal MIMO con CSI en TX:

$$C = \sum_{i=1}^{\min(N_t, N_r)} B \log_2\left(1 + \frac{\lambda_i P}{N_0 B}\right)$$

Donde:
- $\lambda_i$: Autovalores de $\mathbf{H}\mathbf{H}^H$
- $P$: Potencia total transmitida
- $N_0$: Densidad espectral de ruido

### 5.2 Configuraciones MIMO Evaluadas

El sistema evalúa múltiples configuraciones MIMO:

#### 5.2.1 Configuraciones Implementadas

| Configuración | gNB | UAV | Elementos gNB | Elementos UAV | Aplicación |
|---------------|-----|-----|---------------|---------------|------------|
| **SISO** | 1×1 | 1×1 | 1 | 1 | Baseline, bajo costo |
| **MIMO 2×2** | 2×1 | 1×2 | 2 | 2 | Diversidad básica |
| **MIMO 4×4** | 2×2 | 2×2 | 4 | 4 | Balance rendimiento/costo |
| **MIMO 8×4** | 4×2 | 2×2 | 8 | 4 | Alta capacidad UAV |
| **MIMO 16×8** | 8×2 | 4×2 | 16 | 8 | Massive MIMO (**óptimo**) |

**Configuración por defecto del sistema:**
```python
# gNB - Massive MIMO
GNB_ARRAY = {
    'num_rows': 8,
    'num_cols': 8,      # 64 elementos total
    'vertical_spacing': 0.5,    # λ/2
    'horizontal_spacing': 0.5,
}

# UAV - Array compacto
UAV_ARRAY = {
    'num_rows': 2,
    'num_cols': 2,      # 4 elementos total
    'vertical_spacing': 0.5,
    'horizontal_spacing': 0.5,
}
```

#### 5.2.2 Ganancia Esperada por Configuración

| Configuración | Ganancia Array (dB) | Streams Paralelos | Throughput Esperado (@20dB SNR) |
|---------------|---------------------|-------------------|----------------------------------|
| SISO | 0 | 1 | ~66 Mbps |
| MIMO 2×2 | 3 | 2 | ~180 Mbps |
| MIMO 4×4 | 6 | 4 | ~450 Mbps |
| MIMO 8×4 | 8 | 4 | ~550 Mbps |
| MIMO 16×8 | 11 | 8 | ~1100 Mbps |

### 5.3 Beamforming

**Beamforming** es la técnica de dirigir la energía de las antenas hacia direcciones específicas.

#### 5.3.1 Tipos de Beamforming

1. **Analog Beamforming**: Ajuste de fase RF
2. **Digital Beamforming**: Procesamiento en banda base
3. **Hybrid Beamforming**: Combinación de ambos (5G NR)

#### 5.3.2 Estrategias de Precoding

El sistema evalúa 5 estrategias:

##### a) Omnidirectional (Sin Beamforming)

Transmisión isotrópica sin direccionalidad:
- **Precoder**: $\mathbf{W} = \mathbf{I}$ (matriz identidad)
- **Ventaja**: Simplicidad, no requiere CSI
- **Desventaja**: Sin ganancia direccional

##### b) MRT (Maximum Ratio Transmission)

Maximiza SNR en el receptor:

$$\mathbf{w}_{\text{MRT}} = \frac{\mathbf{h}^*}{||\mathbf{h}||}$$

Donde $\mathbf{h}$ es el vector de canal.

- **Ventaja**: Óptimo para receptor único, maximiza SNR
- **Desventaja**: No considera interferencia

**Ganancia MRT**: Proporcional a $N_t$
```
Ganancia_MRT (dB) = 10 × log₁₀(N_t)
Ejemplo: 16 antenas → 12 dB ganancia
```

##### c) Zero Forcing (ZF)

Anula interferencia entre streams:

$$\mathbf{W}_{\text{ZF}} = \mathbf{H}^H (\mathbf{H} \mathbf{H}^H)^{-1}$$

- **Ventaja**: Elimina interferencia inter-stream
- **Desventaja**: Amplifica ruido si $\mathbf{H}$ mal condicionada

##### d) MMSE (Minimum Mean Square Error)

Balance entre interferencia y ruido:

$$\mathbf{W}_{\text{MMSE}} = \mathbf{H}^H (\mathbf{H} \mathbf{H}^H + \sigma^2 \mathbf{I})^{-1}$$

- **Ventaja**: Óptimo en términos de MSE
- **Desventaja**: Requiere estimación de ruido

##### e) SVD (Singular Value Decomposition)

Descomposición del canal en canales paralelos:

$$\mathbf{H} = \mathbf{U} \boldsymbol{\Sigma} \mathbf{V}^H$$

Precoders:
- TX: $\mathbf{W} = \mathbf{V}$
- RX: $\mathbf{G} = \mathbf{U}^H$

- **Ventaja**: Canales paralelos independientes
- **Desventaja**: Requiere CSI completo en TX y RX

### 5.4 Arrays de Antenas

#### 5.4.1 Planar Array

Los arrays planares organizan antenas en grid 2D:

```
Array 4×4 (vista frontal):
○ ○ ○ ○
○ ○ ○ ○  
○ ○ ○ ○
○ ○ ○ ○
```

**Patrón de radiación**:
- **Azimuth**: Dirección horizontal (φ)
- **Elevation**: Dirección vertical (θ)

**Steering Vector**:
$$\mathbf{a}(\theta, \phi) = \mathbf{a}_v(\theta) \otimes \mathbf{a}_h(\phi)$$

Donde $\otimes$ denota producto de Kronecker.

#### 5.4.2 Espaciado de Antenas

El espaciado típico es $\lambda/2$ para evitar grating lobes:

$$d = \frac{\lambda}{2} = \frac{c}{2f}$$

Para $f = 3.5$ GHz:
```
λ = c/f = 3×10⁸ / 3.5×10⁹ = 0.0857 m = 8.57 cm
d = λ/2 = 4.28 cm
```

**Configuración del sistema**: `spacing = 0.5` (normalizado a $\lambda$)

---

## 6. Movilidad y Efectos Doppler

### 6.1 Efecto Doppler

El movimiento relativo entre TX y RX causa desplazamiento de frecuencia.

#### 6.1.1 Desplazamiento Doppler

La frecuencia recibida:

$$f_r = f_t \left(1 + \frac{v \cos\theta}{c}\right)$$

Donde:
- $f_t$: Frecuencia transmitida
- $v$: Velocidad del UAV
- $\theta$: Ángulo entre velocidad y dirección de propagación
- $c$: Velocidad de la luz

**Máximo Doppler Shift**:
$$f_d^{\max} = \frac{v \cdot f_t}{c}$$

**Ejemplo para UAV:**
```
v = 20 m/s (72 km/h)
f = 3.5 GHz
f_d = (20 × 3.5×10⁹) / (3×10⁸) = 233 Hz
```

#### 6.1.2 Impacto en 5G NR

El Doppler afecta:

1. **Orthogonalidad OFDM**: Pérdida de ortogonalidad entre subportadoras
   - ICI (Inter-Carrier Interference) proporcional a $f_d / \Delta f$
   - Para $f_d = 233$ Hz, $\Delta f = 30$ kHz: ICI = 0.78% (negligible)

2. **Estimación de Canal**: Mayor variación temporal
   - Requiere tracking más frecuente
   - Pilotos densos en tiempo

3. **Sincronización**: Errores de frecuencia
   - Compensación AFC (Automatic Frequency Control)

### 6.2 Patrones de Trayectoria UAV

El sistema analiza 6 patrones de movilidad:

#### 6.2.1 Trayectoria Circular

Movimiento circular alrededor del gNB:

$$\begin{aligned}
x(t) &= r \cos(\omega t + \phi_0) \\
y(t) &= r \sin(\omega t + \phi_0) \\
z(t) &= h_{\text{const}}
\end{aligned}$$

- **Radio**: $r = 100$ m
- **Período**: $T = 60$ s
- **Velocidad angular**: $\omega = 2\pi/T$
- **Velocidad lineal**: $v = r\omega \approx 10.5$ m/s

**Características:**
- Distancia constante al gNB
- Doppler variable con ángulo
- Throughput estable

#### 6.2.2 Trayectoria Lineal

Movimiento en línea recta:

$$\begin{aligned}
x(t) &= x_0 + v_x t \\
y(t) &= y_0 + v_y t \\
z(t) &= h_{\text{const}}
\end{aligned}$$

- **Rango**: -200m a +200m
- **Velocidad**: 15 m/s

**Características:**
- Distancia variable al gNB
- Efecto Doppler máximo en acercamiento/alejamiento
- Throughput variable con distancia

#### 6.2.3 Trayectoria en Espiral

Combinación de circular + altura variable:

$$\begin{aligned}
x(t) &= r(t) \cos(\omega t) \\
y(t) &= r(t) \sin(\omega t) \\
z(t) &= h_0 + \Delta h \cdot (t/T)
\end{aligned}$$

Donde $r(t) = r_0 + \Delta r \cdot (t/T)$

- **Radio inicial**: 50 m
- **Radio final**: 150 m
- **Altura inicial**: 50 m
- **Altura final**: 150 m

**Características:**
- Exploración 3D del espacio
- Distancia y altura variables
- Evalúa robustez del sistema

#### 6.2.4 Trayectoria en Figura-8

Patrón lemniscata:

$$\begin{aligned}
x(t) &= A \sin(\omega t) \\
y(t) &= A \sin(\omega t) \cos(\omega t)
\end{aligned}$$

- **Amplitud**: $A = 100$ m
- **Período**: 60 s

**Características:**
- Cambios bruscos de dirección
- Test de handover y adaptación
- Doppler con alta variación

#### 6.2.5 Trayectoria Aleatoria (Random Walk)

Movimiento browniano 3D:

$$\begin{aligned}
x_{t+1} &= x_t + \Delta x \\
y_{t+1} &= y_t + \Delta y \\
z_{t+1} &= z_t + \Delta z
\end{aligned}$$

Donde $\Delta x, \Delta y, \Delta z \sim \mathcal{N}(0, \sigma^2)$

- **Desviación**: $\sigma = 5$ m/paso
- **Límites**: ±200 m en x,y; 30-200m en z

**Características:**
- Movimiento impredecible
- Test de worst-case
- Evalúa robustez extrema

#### 6.2.6 Trayectoria Optimizada

Optimización de trayectoria para maximizar throughput:

$$\mathbf{p}^* = \arg\max_{\mathbf{p}} \sum_{t=1}^{T} \text{Throughput}(\mathbf{p}_t)$$

Sujeto a:
- Restricciones de velocidad: $||\mathbf{v}_t|| \leq v_{\max}$
- Restricciones de área: $\mathbf{p}_t \in \mathcal{A}$

**Método**: Differential Evolution
- Población: 20 individuos
- Generaciones: 50
- Mutación: 0.8
- Crossover: 0.7

**Características:**
- Busca posiciones de máximo throughput
- Considera LoS, distancia y altura
- Referencia de performance óptima

### 6.3 Métricas de Movilidad

#### 6.3.1 Throughput vs Tiempo

Análisis temporal del throughput:

$$R(t) = f(\mathbf{p}(t), \text{SNR}(t), \mathbf{H}(t))$$

- **Muestreo**: 120 timesteps en 60 segundos
- **Δt**: 0.5 segundos/paso

#### 6.3.2 Estabilidad de Conexión

Métricas de calidad:

1. **Throughput Medio**: $\bar{R} = \frac{1}{T}\sum_{t=1}^T R(t)$

2. **Varianza**: $\sigma_R^2 = \frac{1}{T}\sum_{t=1}^T (R(t) - \bar{R})^2$

3. **Outage Probability**: $P_{\text{out}} = P(R(t) < R_{\min})$

4. **Stability Score**: $S = \frac{\bar{R}}{\sigma_R}$ (ratio señal-varianza)

#### 6.3.3 Handover Events

En escenarios multi-celda (futuro):
- **Handover Rate**: Número de handovers por minuto
- **Handover Delay**: Tiempo de interrupción
- **Ping-Pong Ratio**: Handovers repetidos

---

## 7. Interferencia en Sistemas Multi-Usuario

### 7.1 Interferencia Co-Canal

Cuando múltiples UAVs comparten el mismo recurso:

#### 7.1.1 Modelo de Interferencia

La señal recibida por el UAV $k$:

$$y_k = h_{k,k} x_k + \sum_{j \neq k} h_{j,k} x_j + n_k$$

Donde:
- $h_{k,k} x_k$: Señal deseada
- $\sum_{j \neq k} h_{j,k} x_j$: Interferencia de otros UAVs
- $n_k$: Ruido térmico

#### 7.1.2 SINR (Signal-to-Interference-plus-Noise Ratio)

La métrica clave es SINR en lugar de SNR:

$$\text{SINR}_k = \frac{P_k |h_{k,k}|^2}{\sum_{j \neq k} P_j |h_{j,k}|^2 + N_0}$$

**Diferencia con SNR:**
- SNR: Solo considera ruido térmico
- SINR: Considera interferencia + ruido (más realista)

### 7.2 Gestión de Recursos

#### 7.2.1 Resource Blocks (RBs)

5G NR asigna recursos en bloques:

**Configuración del Sistema:**
```
Ancho de banda: 100 MHz
Espaciado subportadora: 30 kHz
Total RBs: 273 RBs
Subportadoras por RB: 12
Total subportadoras: 273 × 12 = 3,276
```

#### 7.2.2 Estrategias de Asignación

1. **Orthogonal Resource Allocation**:
   - Cada UAV recibe RBs exclusivos
   - Sin interferencia co-canal
   - Limita número de usuarios

2. **Frequency Reuse**:
   - Factor de reuso: 1 (todos RBs), 3, 4, 7
   - Balance capacidad/interferencia

3. **Power Control**:
   - Ajustar potencia según SINR objetivo
   - Reducir interferencia a vecinos

4. **Scheduling**:
   - Round-Robin: Equidad temporal
   - Max-SNR: Eficiencia espectral
   - Proportional Fair: Balance

### 7.3 Escenarios de Interferencia

El sistema evalúa 5 escenarios:

#### 7.3.1 Baja Densidad (3 UAVs)

- **UAVs**: 3
- **Área**: 300m × 300m (completa)
- **Separación mínima**: 100m
- **Características**:
  - Baja probabilidad de interferencia
  - SINR alto (> 20 dB esperado)
  - Asignación de recursos simple

#### 7.3.2 Densidad Media (5 UAVs)

- **UAVs**: 5
- **Área**: 240m × 240m (factor 0.8)
- **Separación mínima**: 80m
- **Características**:
  - Interferencia moderada
  - SINR medio (15-20 dB)
  - Requiere scheduling básico

#### 7.3.3 Alta Densidad (8 UAVs)

- **UAVs**: 8
- **Área**: 180m × 180m (factor 0.6)
- **Separación mínima**: 60m
- **Características**:
  - Alta interferencia
  - SINR bajo (< 15 dB)
  - Scheduling crítico
  - Puede requerir ICIC

#### 7.3.4 UAVs Agrupados (6 UAVs)

- **UAVs**: 6 en 2-3 clusters
- **Área de cluster**: 50m radio
- **Características**:
  - Interferencia extrema intra-cluster
  - SINR muy variable
  - Test de worst-case local

#### 7.3.5 UAVs Distribuidos (7 UAVs)

- **UAVs**: 7 uniformemente distribuidos
- **Área**: 360m × 360m (factor 1.2)
- **Separación**: Máxima posible
- **Características**:
  - Mínima interferencia
  - SINR óptimo
  - Referencia de best-case

### 7.4 Técnicas de Mitigación de Interferencia

#### 7.4.1 ICIC (Inter-Cell Interference Coordination)

Coordinación entre celdas:
- **Soft Frequency Reuse**: Diferentes potencias por banda
- **eICIC**: Enhanced ICIC con ABS (Almost Blank Subframes)
- **CoMP**: Coordinated Multi-Point transmission

#### 7.4.2 Beamforming Espacial

Uso de MIMO para separación espacial:
- **MU-MIMO**: Multi-User MIMO
- **Beamforming direccional**: Apuntar a UAVs específicos
- **Null-steering**: Crear nulos hacia interferentes

#### 7.4.3 Power Control

Algoritmo de control de potencia:

$$P_k^{(n+1)} = P_k^{(n)} \cdot \frac{\text{SINR}_{\text{target}}}{\text{SINR}_k^{(n)}}$$

Con límites: $P_{\min} \leq P_k \leq P_{\max}$

### 7.5 Métricas de Interferencia

#### 7.5.1 SINR Promedio

$$\overline{\text{SINR}} = \frac{1}{K} \sum_{k=1}^K \text{SINR}_k$$

#### 7.5.2 Fairness (Índice de Jain)

Mide equidad en la distribución de recursos:

$$\mathcal{F} = \frac{\left(\sum_{k=1}^K R_k\right)^2}{K \sum_{k=1}^K R_k^2}$$

Donde:
- $\mathcal{F} = 1$: Perfecta equidad
- $\mathcal{F} \to 1/K$: Inequidad total

#### 7.5.3 Outage Probability

Probabilidad de SINR < umbral:

$$P_{\text{outage}} = P(\text{SINR}_k < \gamma_{\text{th}})$$

Típicamente $\gamma_{\text{th}} = 0$ dB para 5G eMBB.

#### 7.5.4 Matriz de Interferencia

Matriz $K \times K$ de interferencia mutua:

$$\mathbf{I}_{j,k} = P_j |h_{j,k}|^2$$

Visualiza patrones de interferencia espacial.

---

## 8. Framework Sionna

### 8.1 Introducción a Sionna

**Sionna** es una librería de código abierto desarrollada por NVIDIA para simulaciones de enlaces de comunicaciones inalámbricas, con soporte nativo para GPU mediante TensorFlow.

#### 8.1.1 Características Principales

- **Basado en TensorFlow**: Aceleración GPU, diferenciación automática
- **Ray Tracing 3D**: Escenarios realistas con Mitsuba renderer
- **System-Level Simulation**: Abstracciones de sistema completo
- **Modulaciones 5G NR**: OFDM, LDPC, Polar codes
- **Canales Realistas**: CDL, TDL, Ray Tracing

#### 8.1.2 Arquitectura de Sionna

```
┌─────────────────────────────────────┐
│      Sionna Framework               │
├─────────────────────────────────────┤
│  RT (Ray Tracing)                   │
│  - Scene loading                    │
│  - Path computation                 │
│  - Channel response                 │
├─────────────────────────────────────┤
│  SYS (System Level)                 │
│  - Link abstraction                 │
│  - System simulation                │
│  - Metrics calculation              │
├─────────────────────────────────────┤
│  CHANNEL                            │
│  - Time/Frequency response          │
│  - Fading models                    │
├─────────────────────────────────────┤
│  OFDM                               │
│  - Modulator/Demodulator            │
│  - Resource mapping                 │
├─────────────────────────────────────┤
│  FEC (Forward Error Correction)     │
│  - LDPC encoder/decoder             │
│  - Polar encoder/decoder            │
├─────────────────────────────────────┤
│  MIMO                               │
│  - Precoders                        │
│  - Detectors                        │
└─────────────────────────────────────┘
        ↓ TensorFlow Backend
┌─────────────────────────────────────┐
│  GPU Acceleration (CUDA)            │
└─────────────────────────────────────┘
```

### 8.2 Sionna RT (Ray Tracing)

#### 8.2.1 Funcionalidades RT

**Carga de Escenarios:**
```python
import sionna.rt as rt

# Cargar escena predefinida (Munich)
scene = rt.load_scene(rt.scene.munich)

# Configuración
scene.frequency = 3.5e9  # 3.5 GHz
scene.synthetic_array = True  # Arrays sintéticos
```

**Objetos de la Escena:**
- `Transmitter`: Transmisor (gNB)
- `Receiver`: Receptor (UAV)
- `RadioMaterial`: Propiedades electromagnéticas de materiales

**Arrays de Antenas:**
```python
# Crear array planar 8×8
tx_array = rt.PlanarArray(
    num_rows=8,
    num_cols=8,
    vertical_spacing=0.5,    # λ/2
    horizontal_spacing=0.5,
    pattern='iso',           # Isotrópico
    polarization='V'         # Vertical
)
scene.tx_array = tx_array
```

#### 8.2.2 Cálculo de Paths

**Path Solver:**
```python
# Inicializar solver
path_solver = rt.PathSolver()

# Calcular paths con reflexiones
paths = path_solver(
    scene=scene,
    max_depth=5,        # Máximo 5 reflexiones
    num_samples=1e6     # Samples para ray launching
)
```

**Estructura de Paths:**
- `paths.a`: Amplitudes complejas `[batch, tx, rx, paths]`
- `paths.tau`: Retardos `[batch, tx, rx, paths]`
- `paths.theta_t`: Ángulos AoD azimuth
- `paths.phi_t`: Ángulos AoD elevation
- `paths.theta_r`: Ángulos AoA azimuth
- `paths.phi_r`: Ángulos AoA elevation

#### 8.2.3 Respuesta en Frecuencia del Canal

**Channel Frequency Response (CFR):**
```python
# Definir frecuencias de subportadoras
frequencies = rt.subcarrier_frequencies(
    num_subcarriers=64,
    subcarrier_spacing=30e3  # 30 kHz
)

# Calcular respuesta en frecuencia
h_freq = paths.cir_to_ofdm_channel(
    frequencies=frequencies,
    num_time_steps=1,
    bandwidth=100e6
)
# Shape: [batch, tx, rx, rx_ant, tx_ant, num_subcarriers, num_time_steps]
```

**Channel Impulse Response (CIR):**
```python
# Respuesta impulsiva
h_time = paths.cir()
# Shape: [batch, tx, rx, rx_ant, tx_ant, max_num_paths]
```

### 8.3 Sionna SYS (System Level)

#### 8.3.1 Abstraction Levels

Sionna SYS proporciona niveles de abstracción:

1. **PHY Layer**: Modelado completo de capa física
   - Codificación de canal
   - Modulación OFDM
   - Ecualización MIMO
   
2. **Link Level**: Abstracciones de enlace
   - Effective SNR
   - BLER vs SNR curves
   - Throughput estimation

3. **System Level**: Simulación de sistema completo
   - Múltiples enlaces simultáneos
   - Interferencia
   - Scheduling

#### 8.3.2 Integración RT + SYS

```python
class BasicUAVSystem:
    def __init__(self, scenario):
        self.scenario = scenario  # MunichUAVScenario con RT
        
        # Obtener paths del escenario
        self.paths = scenario.get_paths(max_depth=5)
        
        # Configurar canal
        self._setup_channel()
        
    def _setup_channel(self):
        # Canal basado en ray tracing
        self.channel_ready = True
    
    def simulate_throughput(self, snr_db_range):
        results = []
        
        for snr_db in snr_db_range:
            # Obtener respuesta del canal
            h_freq = self.scenario.get_channel_response(self.paths)
            
            # Calcular channel gain
            channel_power = tf.reduce_mean(tf.abs(h_freq) ** 2)
            channel_gain_db = 10 * tf.math.log(channel_power) / tf.math.log(10.0)
            
            # SNR efectivo
            snr_eff = snr_db + channel_gain_db
            
            # Shannon capacity (con MIMO)
            mimo_gain = min(N_tx, N_rx)
            se = mimo_gain * log2(1 + 10^(snr_eff/10))
            
            # Throughput
            throughput = se * bandwidth
            results.append(throughput)
        
        return results
```

### 8.4 Ventajas de Sionna para UAV

#### 8.4.1 Ray Tracing Realista

- **Escenarios 3D urbanos**: Munich con 6 edificios
- **Materiales realistas**: Concreto, vidrio, metal con propiedades EM
- **Paths multi-trayecto**: Captura reflexiones, difracciones

#### 8.4.2 Aceleración GPU

- **TensorFlow backend**: Operaciones vectorizadas en GPU
- **Batch processing**: Múltiples SNRs/configuraciones en paralelo
- **Speed-up**: 10-100× vs implementación CPU

#### 8.4.3 Flexibilidad

- **Fácil configuración**: APIs de alto nivel
- **Extensibilidad**: Agregar nuevos modelos de canal, codificadores
- **Interoperabilidad**: Compatible con TensorFlow ecosystem

### 8.5 Limitaciones y Consideraciones

#### 8.5.1 Limitaciones de RT

- **Costo computacional**: Ray tracing es intensivo
- **Precisión de geometría**: Depende de calidad del modelo 3D
- **Materiales**: Parámetros EM pueden ser aproximados

#### 8.5.2 Limitaciones de SYS

- **Abstracción**: Algunos detalles PHY se simplifican
- **Validación**: Requiere comparación con medidas reales
- **Modelos de movilidad**: Doppler implementado analíticamente en ciertos casos

---

## 9. Arquitectura del Sistema Implementado

### 9.1 Vista General del Sistema

El sistema implementado consta de los siguientes componentes:

```
┌─────────────────────────────────────────────────────────┐
│                   GUI (PyQt6)                           │
│                   main.py                               │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐          │
│  │Botón 1 │ │Botón 2 │ │Botón 3 │ │Botón 4 │          │
│  │  MIMO  │ │ Altura │ │ Movil  │ │ Interf │          │
│  └────────┘ └────────┘ └────────┘ └────────┘          │
└──────────────────┬──────────────────────────────────────┘
                   │
         ┌─────────┴──────────┐
         │  SimulationWorker  │ (QThread)
         └─────────┬──────────┘
                   │
    ┌──────────────┼──────────────┬──────────────┐
    │              │              │              │
┌───▼───┐   ┌──────▼─────┐  ┌────▼────┐  ┌──────▼──────┐
│ MIMO  │   │   Height   │  │ Mobility│  │Interference │
│Analysis│   │  Analysis  │  │ Analysis│  │  Analysis   │
└───┬───┘   └──────┬─────┘  └────┬────┘  └──────┬──────┘
    │              │              │              │
    │    ┌─────────┴──────────────┘              │
    │    │                                        │
    ▼    ▼                                        ▼
┌──────────────────┐                    ┌──────────────┐
│ BasicUAVSystem   │                    │  Analytical  │
│  (Sionna SYS)    │                    │    Models    │
└────────┬─────────┘                    └──────────────┘
         │
    ┌────▼────────────┐
    │ MunichUAVScenario│
    │  (Sionna RT)     │
    └────┬─────────────┘
         │
    ┌────▼──────┐
    │ Sionna RT │
    │  Scene    │
    └───────────┘
```

### 9.2 Estructura de Directorios

```
final/
├── GUI/                          # Interfaz gráfica
│   ├── main.py                   # Aplicación principal PyQt6
│   ├── analysis/                 # Módulos de análisis para GUI
│   │   ├── mimo_beamforming_gui.py      # Botón 1: MIMO
│   │   ├── height_analysis_gui.py       # Botón 2: Altura
│   │   ├── mobility_analysis_gui.py     # Botón 3: Movilidad
│   │   └── interference_analysis_gui.py # Botón 4: Interferencia
│   ├── config/                   # Configuración GUI
│   │   └── system_config.py
│   ├── scenarios/                # Escenarios para GUI
│   │   └── munich_uav_scenario.py
│   └── outputs/                  # Resultados de simulaciones
│       ├── *.json                # Datos numéricos
│       └── *.png                 # Gráficos
│
├── UAV/                          # Sistema UAV core
│   ├── systems/                  # Sistemas de simulación
│   │   └── basic_system.py       # BasicUAVSystem (Sionna SYS)
│   ├── scenarios/                # Escenarios 3D
│   │   └── munich_uav_scenario.py # Escenario Munich RT
│   ├── config/                   # Configuración del sistema
│   │   └── system_config.py      # Parámetros centralizados
│   ├── analysis/                 # Análisis standalone
│   │   ├── height_analysis.py
│   │   ├── theoretical_mimo_beamforming.py
│   │   └── practical_multi_uav_analysis.py
│   └── outputs/                  # Outputs UAV
│
├── requirements.txt              # Dependencias Python
├── ejemplo_config.json           # Configuración ejemplo
└── Marco_Teorico_Sistema_UAV_5G.md # Este documento
```

### 9.3 Componentes Core

#### 9.3.1 BasicUAVSystem (`UAV/systems/basic_system.py`)

**Propósito**: Sistema UAV completo usando Sionna SYS

**Funcionalidades:**
```python
class BasicUAVSystem:
    def __init__(self, scenario):
        # Inicializa escenario Munich con RT
        self.scenario = scenario
        self.paths = scenario.get_paths(max_depth=5)
        self._setup_channel()
        self._setup_system()
    
    def simulate_throughput(self, snr_db_range):
        # Simula throughput vs SNR usando RT real
        # Returns: {snr_db, throughput_mbps, bler, spectral_efficiency}
    
    def simulate_height_analysis(self, height_range):
        # Analiza throughput vs altura UAV
        # Returns: {heights, throughput_mbps, path_loss_db, los_probability}
    
    def _simulate_single_snr(self, snr_db):
        # Simulación para un punto SNR
        # Calcula channel gain con RT, aplica Shannon
```

**Características:**
- Integra Sionna RT para propagación realista
- Calcula métricas: throughput, BLER, spectral efficiency
- Soporte para análisis de altura

#### 9.3.2 MunichUAVScenario (`UAV/scenarios/munich_uav_scenario.py`)

**Propósito**: Configuración del escenario 3D Munich

**Funcionalidades:**
```python
class MunichUAVScenario:
    def __init__(self, enable_preview=True):
        # Carga escena Munich de Sionna
        self.scene = sionna.rt.load_scene(sionna.rt.scene.munich)
        self.scene.frequency = 7.125e9  # 3.5 GHz
        
        self._setup_transmitters()  # Configura gNB
        self._setup_receivers()     # Configura UAVs
        self._setup_antenna_arrays() # Configura arrays MIMO
        
        self.path_solver = sionna.rt.PathSolver()
    
    def move_uav(self, uav_name, new_position):
        # Mueve UAV a nueva posición [x, y, z]
    
    def get_paths(self, max_depth=5):
        # Calcula paths con ray tracing
        # Returns: Sionna Paths object
    
    def get_channel_response(self, paths):
        # Calcula respuesta en frecuencia del canal
        # Returns: h_freq [tx, rx, tx_ant, rx_ant, subcarriers]
```

**Configuración del Escenario:**
- **Área**: 500m × 500m (Munich)
- **Edificios**: 6 edificios con alturas 10-50m
- **gNB**: Posición [0, 0, 30] - 30m altura
- **UAV1**: Posición inicial [100, 100, 100] - 100m altura
- **Frecuencia**: 7.125 GHz (banda n78)

#### 9.3.3 SystemConfig (`UAV/config/system_config.py`)

**Propósito**: Configuración centralizada de parámetros

**Clases de Configuración:**

```python
# RF Configuration
class RFConfig:
    FREQUENCY = 7.125e9        # 3.5 GHz
    BANDWIDTH = 100e6          # 100 MHz
    TX_POWER_GNB = 43          # 43 dBm (20W)
    TX_POWER_UAV = 23          # 23 dBm (200mW)
    NOISE_FIGURE = 7           # 7 dB
    THERMAL_NOISE = -174       # dBm/Hz

# Antenna Configuration
class AntennaConfig:
    # gNB MIMO Massive 8×8 = 64 antenas
    GNB_ARRAY = {
        'num_rows': 8,
        'num_cols': 8,
        'vertical_spacing': 0.5,
        'horizontal_spacing': 0.5,
        'pattern': 'iso',
        'polarization': 'V'
    }
    
    # UAV Array 2×2 = 4 antenas
    UAV_ARRAY = {
        'num_rows': 2,
        'num_cols': 2,
        'vertical_spacing': 0.5,
        'horizontal_spacing': 0.5,
        'pattern': 'iso',
        'polarization': 'V'
    }

# Scenario Configuration
class ScenarioConfig:
    GNB_POSITION = [0, 0, 30]           # gNB a 30m
    UAV1_POSITION = [100, 100, 100]     # UAV a 100m
    HEIGHT_RANGE = [50, 75, 100, ..., 200]  # Alturas a analizar
    COVERAGE_AREA = {
        'x_range': [-200, 200],
        'y_range': [-200, 200],
        'resolution': 20
    }

# Simulation Configuration
class SimulationConfig:
    RT_MAX_DEPTH = 5                    # Reflexiones RT
    SNR_RANGE = np.arange(-10, 31, 5)  # SNR: -10 a 30 dB
    TARGET_BLER = 0.1                  # 10% BLER
    TARGET_THROUGHPUT = 100            # Mbps mínimo
```

### 9.4 Interfaz Gráfica (GUI)

#### 9.4.1 Aplicación Principal (`GUI/main.py`)

**Arquitectura PyQt6:**

```python
class MainWindow(QMainWindow):
    def __init__(self):
        # Layout principal con splitter
        self.splitter = QSplitter(Qt.Horizontal)
        
        # Panel izquierdo: Control panel con 4 botones
        self.control_panel = self._create_control_panel()
        
        # Panel derecho: Visualización (plots + 3D + logs)
        self.visualization_panel = self._create_visualization_panel()
        
    def _create_control_panel(self):
        # Botón 1: MIMO y Beamforming
        btn_mimo = QPushButton("Análisis MIMO y Beamforming")
        btn_mimo.clicked.connect(self.run_mimo_analysis)
        
        # Botón 2: Altura
        btn_height = QPushButton("Análisis de Altura UAV")
        btn_height.clicked.connect(self.run_height_analysis)
        
        # Botón 3: Movilidad
        btn_mobility = QPushButton("Análisis de Movilidad")
        btn_mobility.clicked.connect(self.run_mobility_analysis)
        
        # Botón 4: Interferencia
        btn_interference = QPushButton("Análisis de Interferencia")
        btn_interference.clicked.connect(self.run_interference_analysis)
    
    def run_mimo_analysis(self):
        # Crear worker thread
        worker = SimulationWorker("mimo_beamforming", {})
        worker.progress.connect(self.update_progress)
        worker.finished.connect(self.display_results)
        worker.start()
```

**Características GUI:**
- **Multi-threading**: Simulaciones en QThread para no bloquear UI
- **Progress tracking**: Callbacks en tiempo real
- **Visualización integrada**: Matplotlib embebido en Qt
- **Logs en vivo**: QTextEdit para mensajes de progreso

#### 9.4.2 Worker Thread Pattern

```python
class SimulationWorker(QThread):
    finished = pyqtSignal(dict)  # Emite resultados
    progress = pyqtSignal(str)   # Emite mensajes de progreso
    error = pyqtSignal(str)      # Emite errores
    
    def run(self):
        try:
            if self.simulation_type == "mimo_beamforming":
                result = self.run_mimo_simulation()
            # ... otros tipos
            
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
    
    def run_mimo_simulation(self):
        from analysis.mimo_beamforming_gui import run_mimo_analysis_gui
        
        # Ejecutar análisis (función dedicada)
        result = run_mimo_analysis_gui(output_dir="outputs")
        
        return result
```

### 9.5 Flujo de Datos

#### 9.5.1 Flujo General

```
Usuario             GUI             Worker Thread       Análisis         Sionna
  │                  │                    │                │               │
  │  Click Botón     │                    │                │               │
  │─────────────────>│                    │                │               │
  │                  │  Start Worker      │                │               │
  │                  │───────────────────>│                │               │
  │                  │                    │  Call Analysis │               │
  │                  │                    │───────────────>│               │
  │                  │                    │                │ Load Scene    │
  │                  │                    │                │──────────────>│
  │                  │                    │                │<──────────────│
  │                  │                    │                │  Paths        │
  │                  │  Progress Update   │<───────────────│               │
  │                  │<───────────────────│                │               │
  │  Update UI       │                    │                │  CFR          │
  │<─────────────────│                    │                │──────────────>│
  │                  │                    │                │<──────────────│
  │                  │                    │                │  h_freq       │
  │                  │                    │                │               │
  │                  │                    │                │ Calculate     │
  │                  │                    │                │ Metrics       │
  │                  │                    │  Results       │               │
  │                  │  Finished Signal   │<───────────────│               │
  │                  │<───────────────────│                │               │
  │  Display Results │                    │                │               │
  │<─────────────────│                    │                │               │
```

#### 9.5.2 Formato de Resultados

Cada análisis retorna un diccionario:

```python
result = {
    'plots': [
        'output/mimo_comparison.png',
        'output/beamforming_comparison.png',
        'output/3d_scene.png'
    ],
    'metrics': {
        'best_mimo': 'MIMO 16×8',
        'best_beamforming': 'SVD',
        'max_throughput_mbps': 1250.5,
        'optimal_snr_db': 20
    },
    'summary': "Análisis MIMO completado. MIMO 16×8 con SVD beamforming...",
    'data_file': 'output/mimo_beamforming_results.json'
}
```

### 9.6 Gestión de Outputs

#### 9.6.1 Estructura de Outputs

```
GUI/outputs/
├── mimo_beamforming_results.json    # Datos numéricos MIMO
├── height_results.json               # Datos altura
├── mobility_results.json             # Datos movilidad
├── interference_results.json         # Datos interferencia
├── mimo_comparison.png               # Plots
├── beamforming_comparison.png
├── height_analysis.png
├── mobility_patterns.png
├── interference_matrix.png
└── 3d_scene.png                      # Escena 3D Munich
```

#### 9.6.2 Formato JSON de Resultados

```json
{
  "timestamp": "2026-02-02T10:30:45",
  "analysis_type": "mimo_beamforming",
  "configuration": {
    "frequency_ghz": 3.5,
    "bandwidth_mhz": 100,
    "scenario": "Munich",
    "gnb_position": [0, 0, 30],
    "uav_position": [100, 100, 100]
  },
  "results": {
    "mimo_configurations": {
      "SISO_1x1": {
        "throughput_mbps": [65.2, 120.5, ...],
        "snr_db": [0, 5, 10, ...]
      },
      "MIMO_16x8": {
        "throughput_mbps": [450.2, 850.5, ...],
        "snr_db": [0, 5, 10, ...]
      }
    },
    "best_configuration": "MIMO_16x8",
    "max_throughput_mbps": 1250.5
  }
}
```

---

## 10. Análisis por Fases de Simulación

### 10.1 Fase 1: Análisis MIMO y Beamforming (Botón 1)

**Archivo**: `GUI/analysis/mimo_beamforming_gui.py`  
**Clase**: `MIMOBeamformingGUI`  
**Sistema**: Usa **BasicUAVSystem** con **Sionna RT**

#### 10.1.1 Objetivo

Evaluar y comparar diferentes configuraciones MIMO y estrategias de beamforming para optimizar el enlace gNB → UAV en escenario Munich.

#### 10.1.2 Configuraciones MIMO Evaluadas

Se evalúan **5 configuraciones MIMO**:

| Config | gNB Array | UAV Array | Total Elements | Descripción |
|--------|-----------|-----------|----------------|-------------|
| **SISO** | 1×1 | 1×1 | 1 TX, 1 RX | Baseline sin MIMO |
| **MIMO 2×2** | 2×1 | 1×2 | 2 TX, 2 RX | Diversidad básica |
| **MIMO 4×4** | 2×2 | 2×2 | 4 TX, 4 RX | Diversidad + multiplexing |
| **MIMO 8×4** | 4×2 | 2×2 | 8 TX, 4 RX | Alta capacidad gNB |
| **MIMO 16×8** | 8×2 | 4×2 | 16 TX, 8 RX | Massive MIMO |

#### 10.1.3 Estrategias de Beamforming Evaluadas

Se evalúan **5 estrategias de precoding**:

1. **Omnidirectional**: Sin beamforming (baseline)
2. **MRT**: Maximum Ratio Transmission (maximiza SNR)
3. **Zero Forcing (ZF)**: Anula interferencia inter-stream
4. **MMSE**: Minimum Mean Square Error (balance ruido/interferencia)
5. **SVD**: Singular Value Decomposition (canales paralelos óptimos)

#### 10.1.4 Metodología

**Paso 1: Inicialización**
```python
def __init__(self, output_dir="outputs"):
    # Cargar escenario Munich con Sionna RT
    self.scenario = MunichUAVScenario(enable_preview=False)
    
    # Crear sistema básico UAV
    self.system = BasicUAVSystem(scenario=self.scenario)
    
    # Configuraciones a evaluar
    self.mimo_configs = ['SISO_1x1', 'MIMO_2x2', 'MIMO_4x4', 'MIMO_8x4', 'MIMO_16x8']
    self.beamforming_strategies = ['omnidirectional', 'MRT', 'ZF', 'MMSE', 'SVD']
```

**Paso 2: Análisis MIMO**
```python
def analyze_mimo_configurations(self, progress_callback=None):
    results = {}
    
    for config in self.mimo_configs:
        if progress_callback:
            progress_callback(f"Evaluando {config}...")
        
        # Configurar arrays según config
        self._configure_mimo(config)
        
        # Simular throughput vs SNR
        snr_range = np.arange(0, 31, 5)  # 0-30 dB
        throughput = self.system.simulate_throughput(snr_range)
        
        results[config] = {
            'snr_db': snr_range,
            'throughput_mbps': throughput['throughput_mbps'],
            'spectral_efficiency': throughput['spectral_efficiency'],
            'bler': throughput['bler']
        }
    
    return results
```

**Paso 3: Análisis Beamforming**
```python
def analyze_beamforming_strategies(self, progress_callback=None):
    results = {}
    
    # Usar MIMO 16×8 para análisis de beamforming
    self._configure_mimo('MIMO_16x8')
    
    for strategy in self.beamforming_strategies:
        if progress_callback:
            progress_callback(f"Evaluando beamforming {strategy}...")
        
        # Aplicar estrategia de precoding
        self._apply_beamforming(strategy)
        
        # Simular con beamforming
        snr_range = np.arange(0, 31, 5)
        throughput = self.system.simulate_throughput(snr_range)
        
        results[strategy] = {
            'snr_db': snr_range,
            'throughput_mbps': throughput['throughput_mbps'],
            'channel_gain_db': throughput.get('channel_gain_db', 0)
        }
    
    return results
```

**Paso 4: Visualización**
```python
def generate_plots(self, mimo_results, beamforming_results):
    # Plot 1: Comparación MIMO (Throughput vs SNR)
    fig1, ax1 = plt.subplots(figsize=(12, 8))
    for config, data in mimo_results.items():
        ax1.plot(data['snr_db'], data['throughput_mbps'], 
                 marker='o', label=config, linewidth=2)
    ax1.set_xlabel('SNR (dB)')
    ax1.set_ylabel('Throughput (Mbps)')
    ax1.set_title('Comparación MIMO: Throughput vs SNR')
    ax1.legend()
    ax1.grid(True)
    plt.savefig('outputs/mimo_comparison.png')
    
    # Plot 2: Comparación Beamforming
    fig2, ax2 = plt.subplots(figsize=(12, 8))
    for strategy, data in beamforming_results.items():
        ax2.plot(data['snr_db'], data['throughput_mbps'],
                 marker='s', label=strategy, linewidth=2)
    ax2.set_xlabel('SNR (dB)')
    ax2.set_ylabel('Throughput (Mbps)')
    ax2.set_title('Comparación Beamforming: Throughput vs SNR (MIMO 16×8)')
    ax2.legend()
    ax2.grid(True)
    plt.savefig('outputs/beamforming_comparison.png')
    
    # Plot 3: Escena 3D Munich
    self.scenario.scene.preview(filename='outputs/3d_scene.png')
```

#### 10.1.5 Métricas Calculadas

Para cada configuración:

1. **Throughput (Mbps)**: Tasa de datos efectiva
   $$R = \eta \cdot B$$
   Donde $\eta$ es eficiencia espectral calculada con Shannon

2. **Spectral Efficiency (bits/s/Hz)**:
   $$\eta = \min(N_t, N_r) \cdot \log_2(1 + \text{SNR}_{\text{eff}})$$

3. **BLER (Block Error Rate)**: Modelo exponencial
   $$\text{BLER} = e^{-\text{SNR}_{\text{eff}}/10}$$

4. **Channel Gain (dB)**: Del ray tracing
   $$G_{\text{ch}} = 10 \log_{10}(|H|^2)$$

5. **MIMO Gain (dB)**: Ganancia respecto a SISO
   $$G_{\text{MIMO}} = 10 \log_{10}\left(\frac{R_{\text{MIMO}}}{R_{\text{SISO}}}\right)$$

#### 10.1.6 Resultados Esperados

**Comparación MIMO:**
- SISO: ~66 Mbps @ 20 dB SNR
- MIMO 2×2: ~180 Mbps (ganancia 4.3 dB)
- MIMO 4×4: ~450 Mbps (ganancia 8.3 dB)
- MIMO 8×4: ~550 Mbps (ganancia 9.2 dB)
- **MIMO 16×8**: ~1100 Mbps (ganancia 12.2 dB) ✓ **Mejor**

**Comparación Beamforming (MIMO 16×8):**
- Omnidirectional: ~1100 Mbps (baseline)
- MRT: ~1400 Mbps (+27% ganancia)
- ZF: ~1350 Mbps (+23%)
- MMSE: ~1450 Mbps (+32%)
- **SVD**: ~1500 Mbps (+36%) ✓ **Mejor**

#### 10.1.7 Flujo de Trabajo

```
┌──────────────────────────────────────────────────────────┐
│  1. Usuario presiona "Análisis MIMO y Beamforming"      │
└────────────────────┬─────────────────────────────────────┘
                     │
    ┌────────────────▼────────────────┐
    │  2. GUI crea SimulationWorker   │
    │     tipo: "mimo_beamforming"    │
    └────────────────┬────────────────┘
                     │
    ┌────────────────▼────────────────────────────────┐
    │  3. Worker llama run_mimo_analysis_gui()        │
    │     - Inicializa MIMOBeamformingGUI             │
    │     - Crea MunichUAVScenario (Sionna RT)        │
    │     - Crea BasicUAVSystem                       │
    └────────────────┬────────────────────────────────┘
                     │
    ┌────────────────▼────────────────────────────────┐
    │  4. Análisis MIMO (5 configuraciones)           │
    │     Para cada config:                            │
    │       - Configurar arrays gNB y UAV             │
    │       - Calcular paths con RT (max_depth=5)     │
    │       - Obtener h_freq (CFR)                    │
    │       - Simular throughput vs SNR (0-30 dB)     │
    │     Progress: "Evaluando SISO...", etc.         │
    └────────────────┬────────────────────────────────┘
                     │
    ┌────────────────▼────────────────────────────────┐
    │  5. Análisis Beamforming (5 estrategias)        │
    │     Usar MIMO 16×8                              │
    │     Para cada estrategia:                        │
    │       - Aplicar precoding (MRT/ZF/MMSE/SVD)     │
    │       - Simular throughput vs SNR               │
    │     Progress: "Evaluando MRT...", etc.          │
    └────────────────┬────────────────────────────────┘
                     │
    ┌────────────────▼────────────────────────────────┐
    │  6. Generar Visualizaciones                     │
    │     - Plot: Comparación MIMO                    │
    │     - Plot: Comparación Beamforming             │
    │     - Plot: Channel gain heatmap                │
    │     - 3D: Escena Munich con UAV                 │
    └────────────────┬────────────────────────────────┘
                     │
    ┌────────────────▼────────────────────────────────┐
    │  7. Guardar Resultados                          │
    │     - JSON: mimo_beamforming_results.json       │
    │     - PNG: mimo_comparison.png                  │
    │     - PNG: beamforming_comparison.png           │
    │     - PNG: 3d_scene.png                         │
    └────────────────┬────────────────────────────────┘
                     │
    ┌────────────────▼────────────────────────────────┐
    │  8. Worker emite finished signal                │
    │     result = {                                   │
    │       'plots': [...],                           │
    │       'metrics': {...},                         │
    │       'summary': "..."                          │
    │     }                                            │
    └────────────────┬────────────────────────────────┘
                     │
    ┌────────────────▼────────────────────────────────┐
    │  9. GUI muestra resultados                      │
    │     - Carga plots en panel derecho              │
    │     - Muestra summary en log                    │
    │     - Habilita export de datos                  │
    └─────────────────────────────────────────────────┘
```

#### 10.1.8 Conceptos Teóricos Clave

1. **Ganancia MIMO**: Proporcional a $\min(N_t, N_r)$
2. **Beamforming**: Direcciona energía hacia UAV específico
3. **SVD Precoding**: Desacopla canal MIMO en canales paralelos independientes
4. **Ray Tracing**: Captura efectos realistas de propagación urbana (reflexiones, NLoS)
5. **Trade-off Complejidad/Performance**: MIMO masivo ofrece mejor throughput pero mayor complejidad de hardware

---

### 10.2 Fase 2: Análisis de Altura UAV (Botón 2)

**Archivo**: `GUI/analysis/height_analysis_gui.py`  
**Clase**: `HeightAnalysisGUI`  
**Sistema**: Usa **BasicUAVSystem** con **Sionna RT**

#### 10.2.1 Objetivo

Determinar la altura óptima del UAV que maximiza el throughput, considerando el balance entre probabilidad LoS y path loss en el escenario urbano Munich.

#### 10.2.2 Rango de Alturas

Se evalúan **19 alturas** desde 20m hasta 200m:

```python
HEIGHT_RANGE = np.linspace(20, 200, 19)  # [20, 30, 40, ..., 200] metros
```

**Rationale:**
- **< 20m**: Demasiado bajo, alta obstrucción por edificios
- **20-50m**: Transición NLoS → LoS
- **50-100m**: Zona óptima esperada
- **100-200m**: LoS dominante pero mayor path loss
- **> 200m**: Path loss excesivo

#### 10.2.3 Metodología

**Paso 1: Configuración Inicial**
```python
def __init__(self, output_dir="outputs"):
    # Crear escenario Munich
    self.scenario = MunichUAVScenario(enable_preview=False)
    
    # Crear sistema UAV
    self.system = BasicUAVSystem(scenario=self.scenario)
    
    # Rango de alturas
    self.height_range = np.linspace(20, 200, 19)
    
    # SNR fijo para análisis de altura
    self.fixed_snr_db = 20  # Alto SNR para ver efectos de canal claramente
```

**Paso 2: Análisis por Altura**
```python
def analyze_height_sweep(self, progress_callback=None):
    results = {
        'heights_m': [],
        'throughput_mbps': [],
        'path_loss_db': [],
        'los_probability': [],
        'snr_effective_db': [],
        'channel_conditions': []
    }
    
    original_position = self.scenario.scene.receivers['UAV1'].position
    
    for height in self.height_range:
        if progress_callback:
            progress_callback(f"Analizando altura {height:.0f}m...")
        
        # Mover UAV a nueva altura
        new_position = [original_position[0], original_position[1], height]
        self.scenario.move_uav('UAV1', new_position)
        
        # Recalcular paths con nueva altura
        paths = self.scenario.get_paths(max_depth=5)
        self.system.paths = paths
        
        # Simular con SNR fijo
        metrics = self.system._simulate_single_snr(self.fixed_snr_db)
        
        # Almacenar resultados
        results['heights_m'].append(height)
        results['throughput_mbps'].append(metrics['throughput_mbps'])
        results['path_loss_db'].append(-metrics['channel_gain_db'])
        
        # Determinar LoS
        is_los = metrics['channel_condition']['is_los']
        results['los_probability'].append(1.0 if is_los else 0.0)
        results['snr_effective_db'].append(metrics['effective_snr_db'])
        results['channel_conditions'].append(metrics['channel_condition'])
    
    # Restaurar posición original
    self.scenario.move_uav('UAV1', original_position)
    
    # Encontrar altura óptima
    optimal_idx = np.argmax(results['throughput_mbps'])
    results['optimal_height_m'] = results['heights_m'][optimal_idx]
    results['max_throughput_mbps'] = results['throughput_mbps'][optimal_idx]
    
    return results
```

**Paso 3: Análisis de Condiciones de Canal**
```python
def analyze_channel_conditions(self, paths):
    """Analizar si hay LoS y cuántos paths"""
    path_amplitudes = tf.abs(paths.a[0, 0, 0, 0, :])
    
    # Path más fuerte (típicamente LoS si existe)
    strongest_idx = tf.argmax(path_amplitudes)
    strongest_power = path_amplitudes[strongest_idx]
    
    # Criterio LoS: path más fuerte es el primero y significativo
    threshold = 0.1  # Umbral de potencia relativa
    is_los = (strongest_idx == 0) and (strongest_power > threshold)
    
    num_paths = tf.reduce_sum(tf.cast(path_amplitudes > 1e-6, tf.int32))
    
    return {
        'is_los': bool(is_los),
        'num_paths': int(num_paths),
        'strongest_path_power': float(strongest_power)
    }
```

**Paso 4: Visualización**
```python
def generate_height_plots(self, results):
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # Plot 1: Throughput vs Altura
    ax1 = axes[0, 0]
    ax1.plot(results['heights_m'], results['throughput_mbps'],
             marker='o', linewidth=2, markersize=8, color='blue')
    ax1.axvline(results['optimal_height_m'], color='red', 
                linestyle='--', label=f"Óptimo: {results['optimal_height_m']:.0f}m")
    ax1.set_xlabel('Altura UAV (m)')
    ax1.set_ylabel('Throughput (Mbps)')
    ax1.set_title('Throughput vs Altura')
    ax1.grid(True)
    ax1.legend()
    
    # Plot 2: Path Loss vs Altura
    ax2 = axes[0, 1]
    ax2.plot(results['heights_m'], results['path_loss_db'],
             marker='s', linewidth=2, color='orange')
    ax2.set_xlabel('Altura UAV (m)')
    ax2.set_ylabel('Path Loss (dB)')
    ax2.set_title('Path Loss vs Altura')
    ax2.grid(True)
    
    # Plot 3: Probabilidad LoS vs Altura
    ax3 = axes[1, 0]
    ax3.plot(results['heights_m'], results['los_probability'],
             marker='^', linewidth=2, color='green')
    ax3.set_xlabel('Altura UAV (m)')
    ax3.set_ylabel('Probabilidad LoS')
    ax3.set_title('Probabilidad Line-of-Sight vs Altura')
    ax3.set_ylim([-0.1, 1.1])
    ax3.grid(True)
    
    # Plot 4: SNR Efectivo vs Altura
    ax4 = axes[1, 1]
    ax4.plot(results['heights_m'], results['snr_effective_db'],
             marker='d', linewidth=2, color='purple')
    ax4.set_xlabel('Altura UAV (m)')
    ax4.set_ylabel('SNR Efectivo (dB)')
    ax4.set_title('SNR Efectivo vs Altura')
    ax4.grid(True)
    
    plt.tight_layout()
    plt.savefig('outputs/height_analysis.png', dpi=150)
```

#### 10.2.4 Métricas Calculadas

1. **Throughput (Mbps)**: Función de altura
   $$R(h) = \eta(h) \cdot B$$

2. **Path Loss (dB)**: Incluye distancia 3D
   $$d_{3D}(h) = \sqrt{d_{2D}^2 + h^2}$$
   $$L(h) = L_{\text{FSPL}}(d_{3D}(h)) + L_{\text{extra}}(h)$$

3. **Probabilidad LoS**: Binaria (0 o 1) del ray tracing
   - 1: Existe path directo sin obstrucción
   - 0: Todos los paths tienen reflexiones/difracción

4. **SNR Efectivo (dB)**:
   $$\text{SNR}_{\text{eff}}(h) = \text{SNR}_{\text{input}} + G_{\text{channel}}(h)$$

5. **Altura Óptima**:
   $$h_{\text{opt}} = \arg\max_h R(h)$$

#### 10.2.5 Resultados Esperados

**Comportamiento Típico:**

- **20-40m**: 
  - Throughput: Bajo (~200-400 Mbps)
  - LoS: Intermitente (0-50%)
  - Path Loss: Alto por obstrucción

- **40-80m** (Zona Óptima):
  - Throughput: Máximo (~600-800 Mbps)
  - LoS: Alta probabilidad (80-100%)
  - Path Loss: Moderado
  - **Altura óptima esperada: ~60m**

- **80-150m**:
  - Throughput: Descendiendo (~500-600 Mbps)
  - LoS: 100%
  - Path Loss: Aumentando con distancia

- **150-200m**:
  - Throughput: Bajo (~300-400 Mbps)
  - LoS: 100%
  - Path Loss: Alto por distancia excesiva

#### 10.2.6 Flujo de Trabajo

```
┌───────────────────────────────────────────────────────┐
│  1. Usuario presiona "Análisis de Altura UAV"        │
└───────────────────┬───────────────────────────────────┘
                    │
   ┌────────────────▼────────────────┐
   │  2. Worker tipo: "height_analysis" │
   └────────────────┬────────────────┘
                    │
   ┌────────────────▼────────────────────────────────┐
   │  3. Llama run_height_analysis_gui()             │
   │     - Inicializa HeightAnalysisGUI              │
   │     - Crea MunichUAVScenario + BasicUAVSystem   │
   │     - Define height_range: 20-200m (19 puntos)  │
   └────────────────┬────────────────────────────────┘
                    │
   ┌────────────────▼────────────────────────────────┐
   │  4. Loop: Para cada altura en range             │
   │     ┌──────────────────────────────────┐       │
   │     │  4.1. Mover UAV a altura h       │       │
   │     │       new_pos = [x, y, h]        │       │
   │     └─────────┬────────────────────────┘       │
   │               │                                  │
   │     ┌─────────▼────────────────────────┐       │
   │     │  4.2. Calcular paths RT          │       │
   │     │       paths = solver(max_depth=5)│       │
   │     └─────────┬────────────────────────┘       │
   │               │                                  │
   │     ┌─────────▼────────────────────────┐       │
   │     │  4.3. Obtener h_freq (CFR)       │       │
   │     │       h_freq = paths.cfr(freq)   │       │
   │     └─────────┬────────────────────────┘       │
   │               │                                  │
   │     ┌─────────▼────────────────────────┐       │
   │     │  4.4. Calcular métricas          │       │
   │     │       - Channel gain             │       │
   │     │       - SNR efectivo             │       │
   │     │       - Throughput (Shannon)     │       │
   │     │       - Analizar LoS/NLoS        │       │
   │     └─────────┬────────────────────────┘       │
   │               │                                  │
   │     ┌─────────▼────────────────────────┐       │
   │     │  4.5. Almacenar resultados       │       │
   │     │       results[h] = metrics       │       │
   │     └──────────────────────────────────┘       │
   │                                                  │
   │     Progress: "Analizando altura 40m..."        │
   └────────────────┬────────────────────────────────┘
                    │
   ┌────────────────▼────────────────────────────────┐
   │  5. Análisis de Resultados                      │
   │     - Encontrar h_opt = argmax(throughput)      │
   │     - Identificar transición LoS/NLoS           │
   │     - Calcular estadísticas                     │
   └────────────────┬────────────────────────────────┘
                    │
   ┌────────────────▼────────────────────────────────┐
   │  6. Generar Visualizaciones                     │
   │     - Plot 1: Throughput vs Altura (con óptimo) │
   │     - Plot 2: Path Loss vs Altura               │
   │     - Plot 3: Probabilidad LoS vs Altura        │
   │     - Plot 4: SNR Efectivo vs Altura            │
   └────────────────┬────────────────────────────────┘
                    │
   ┌────────────────▼────────────────────────────────┐
   │  7. Guardar Resultados                          │
   │     - JSON: height_results.json                 │
   │     - PNG: height_analysis.png (4 subplots)     │
   └────────────────┬────────────────────────────────┘
                    │
   ┌────────────────▼────────────────────────────────┐
   │  8. Return results con summary                  │
   │     "Altura óptima: 60m con 750 Mbps"          │
   └─────────────────────────────────────────────────┘
```

#### 10.2.7 Conceptos Teóricos Clave

1. **Trade-off LoS vs Distancia**: 
   - Mayor altura → Mayor probabilidad LoS
   - Mayor altura → Mayor distancia 3D → Mayor path loss

2. **Zona de Fresnel**: 
   - Altura debe superar obstrucciones manteniendo primera zona Fresnel despejada

3. **Modelo de Propagación Urbano**:
   - Baja altura: NLoS dominante, múltiples reflexiones
   - Altura media: Transición LoS/NLoS
   - Alta altura: LoS dominante, FSPL puro

4. **Altura Óptima**: 
   - Depende de: densidad de edificios, altura promedio, distancia horizontal al gNB
   - Munich: h_opt ≈ 1.5× altura edificios ≈ 60m

5. **Aplicaciones Prácticas**:
   - Despliegue UAV para cobertura temporal
   - Relay aéreo en zonas urbanas
   - Optimización de rutas 3D

---

### 10.3 Fase 3: Análisis de Movilidad (Botón 3)

**Archivo**: `GUI/analysis/mobility_analysis_gui.py`  
**Clase**: `MobilityAnalysisGUI`  
**Sistema**: Modelo **analítico** (NO usa Sionna, simulación propia)

#### 10.3.1 Objetivo

Evaluar el impacto de diferentes patrones de trayectoria UAV en el throughput temporal, considerando variaciones de distancia, efectos Doppler y transiciones LoS/NLoS durante el movimiento.

#### 10.3.2 Patrones de Trayectoria

Se evalúan **6 patrones de movimiento**:

| Patrón | Descripción | Características | Aplicación |
|--------|-------------|-----------------|------------|
| **Circular** | Movimiento circular alrededor gNB | Distancia constante, Doppler variable | Vigilancia perimetral |
| **Linear** | Línea recta acercamiento/alejamiento | Distancia variable, Doppler máximo | Tránsito punto a punto |
| **Spiral** | Espiral 3D (radio y altura crecientes) | Exploración 3D completa | Búsqueda y rescate |
| **Figure-8** | Patrón lemniscata | Cambios bruscos de dirección | Test de handover |
| **Random Walk** | Movimiento browniano 3D | Impredecible, worst-case | Enjambre de drones |
| **Optimized** | Trayectoria optimizada | Maximiza throughput | Referencia óptima |

#### 10.3.3 Modelo de Simulación

**Diferencia clave**: Esta fase NO usa Sionna RT. Implementa modelo analítico de propagación.

**Modelo de Canal Analítico:**
```python
def calculate_channel_metrics(self, uav_position, gnb_position):
    """Calcular métricas de canal analíticamente"""
    
    # Distancia 3D
    distance_3d = np.linalg.norm(uav_position - gnb_position)
    distance_2d = np.linalg.norm(uav_position[:2] - gnb_position[:2])
    height = uav_position[2]
    
    # Ángulo de elevación
    elevation_angle = np.arctan(height / (distance_2d + 1e-6))
    elevation_deg = np.degrees(elevation_angle)
    
    # Probabilidad LoS (modelo ITU-R para urbano)
    # P_LoS = 1 / (1 + a*exp(-b*(θ - a)))
    a, b = 9.6, 0.28  # Parámetros urbanos
    prob_los = 1.0 / (1.0 + a * np.exp(-b * (elevation_deg - a)))
    
    # Path Loss LoS y NLoS
    freq_ghz = 3.5
    pl_los = 28.0 + 22.0*np.log10(distance_3d) + 20.0*np.log10(freq_ghz)
    pl_nlos = pl_los + 20.0  # 20 dB adicional para NLoS
    
    # Path Loss promedio
    path_loss_db = prob_los * pl_los + (1 - prob_los) * pl_nlos
    
    # SNR
    tx_power_dbm = 43  # gNB
    noise_floor_dbm = -104  # 100 MHz BW
    snr_db = tx_power_dbm - path_loss_db - noise_floor_dbm
    
    # Throughput (Shannon con MIMO gain)
    mimo_gain = 8  # MIMO 16×8 → 8 streams
    snr_linear = 10 ** (snr_db / 10.0)
    spectral_efficiency = mimo_gain * np.log2(1 + snr_linear)
    throughput_mbps = spectral_efficiency * 100  # 100 MHz BW
    
    return {
        'distance_3d': distance_3d,
        'path_loss_db': path_loss_db,
        'prob_los': prob_los,
        'snr_db': snr_db,
        'throughput_mbps': throughput_mbps,
        'elevation_deg': elevation_deg
    }
```

#### 10.3.4 Generación de Trayectorias

**Parámetros Temporales:**
```python
SIMULATION_DURATION = 60  # segundos
NUM_TIMESTEPS = 120       # 120 pasos
DELTA_T = 0.5             # 0.5 segundos/paso
```

**Trayectoria Circular:**
```python
def generate_circular_trajectory(self):
    """Círculo horizontal alrededor del gNB"""
    radius = 100  # metros
    height = 80   # altura constante (óptima de Fase 2)
    period = 60   # segundos
    omega = 2 * np.pi / period
    
    trajectory = []
    for t in np.linspace(0, SIMULATION_DURATION, NUM_TIMESTEPS):
        x = radius * np.cos(omega * t)
        y = radius * np.sin(omega * t)
        z = height
        trajectory.append([x, y, z])
    
    return np.array(trajectory)
```

**Trayectoria Linear:**
```python
def generate_linear_trajectory(self):
    """Línea recta de -200m a +200m"""
    height = 80
    
    trajectory = []
    for t in np.linspace(0, SIMULATION_DURATION, NUM_TIMESTEPS):
        progress = t / SIMULATION_DURATION  # 0 to 1
        x = -200 + 400 * progress  # -200 a +200
        y = 0
        z = height
        trajectory.append([x, y, z])
    
    return np.array(trajectory)
```

**Trayectoria en Espiral:**
```python
def generate_spiral_trajectory(self):
    """Espiral 3D con radio y altura crecientes"""
    r_start, r_end = 50, 150  # radio inicial y final
    h_start, h_end = 50, 150  # altura inicial y final
    num_turns = 3             # vueltas completas
    
    trajectory = []
    for t in np.linspace(0, SIMULATION_DURATION, NUM_TIMESTEPS):
        progress = t / SIMULATION_DURATION
        
        # Radio creciente
        radius = r_start + (r_end - r_start) * progress
        
        # Altura creciente
        height = h_start + (h_end - h_start) * progress
        
        # Ángulo
        angle = 2 * np.pi * num_turns * progress
        
        x = radius * np.cos(angle)
        y = radius * np.sin(angle)
        z = height
        trajectory.append([x, y, z])
    
    return np.array(trajectory)
```

**Trayectoria Figure-8:**
```python
def generate_figure8_trajectory(self):
    """Patrón lemniscata (figura-8)"""
    amplitude = 100
    height = 80
    omega = 2 * np.pi / 60  # período 60s
    
    trajectory = []
    for t in np.linspace(0, SIMULATION_DURATION, NUM_TIMESTEPS):
        x = amplitude * np.sin(omega * t)
        y = amplitude * np.sin(omega * t) * np.cos(omega * t)
        z = height
        trajectory.append([x, y, z])
    
    return np.array(trajectory)
```

**Trayectoria Random Walk:**
```python
def generate_random_walk_trajectory(self):
    """Movimiento browniano 3D con límites"""
    position = np.array([100.0, 100.0, 80.0])  # Inicio
    trajectory = [position.copy()]
    
    step_size = 5  # metros por paso
    
    for _ in range(NUM_TIMESTEPS - 1):
        # Paso aleatorio
        delta = np.random.randn(3) * step_size
        position += delta
        
        # Aplicar límites
        position[0] = np.clip(position[0], -200, 200)  # x
        position[1] = np.clip(position[1], -200, 200)  # y
        position[2] = np.clip(position[2], 30, 200)    # z
        
        trajectory.append(position.copy())
    
    return np.array(trajectory)
```

**Trayectoria Optimizada:**
```python
def generate_optimized_trajectory(self):
    """Optimización para maximizar throughput medio"""
    from scipy.optimize import differential_evolution
    
    def objective(params):
        """Función objetivo: -throughput medio"""
        # params: posiciones [x1, y1, z1, x2, y2, z2, ...]
        positions = params.reshape(-1, 3)
        
        total_throughput = 0
        for pos in positions:
            metrics = self.calculate_channel_metrics(pos, self.gnb_position)
            total_throughput += metrics['throughput_mbps']
        
        return -total_throughput  # Negativo para maximizar
    
    # Límites de búsqueda
    bounds = [(-200, 200), (-200, 200), (30, 200)] * NUM_TIMESTEPS
    
    # Optimización con Differential Evolution
    result = differential_evolution(
        objective,
        bounds,
        maxiter=50,
        popsize=20,
        mutation=0.8,
        recombination=0.7
    )
    
    optimal_trajectory = result.x.reshape(-1, 3)
    return optimal_trajectory
```

#### 10.3.5 Cálculo de Efectos Doppler

```python
def calculate_doppler_shift(self, velocity, gnb_position, uav_position):
    """Calcular desplazamiento Doppler"""
    
    # Vector dirección de propagación
    direction = (gnb_position - uav_position)
    direction_norm = direction / (np.linalg.norm(direction) + 1e-9)
    
    # Componente de velocidad en dirección de propagación
    velocity_radial = np.dot(velocity, direction_norm)
    
    # Doppler shift
    freq = 3.5e9  # 3.5 GHz
    c = 3e8       # velocidad de la luz
    doppler_hz = velocity_radial * freq / c
    
    # ICI (Inter-Carrier Interference)
    subcarrier_spacing = 30e3  # 30 kHz
    ici_ratio = abs(doppler_hz) / subcarrier_spacing
    
    return {
        'doppler_hz': doppler_hz,
        'velocity_radial': velocity_radial,
        'ici_ratio': ici_ratio
    }
```

#### 10.3.6 Análisis Temporal

```python
def analyze_trajectory_pattern(self, pattern_name, progress_callback=None):
    """Analizar un patrón de trayectoria completo"""
    
    if progress_callback:
        progress_callback(f"Analizando patrón {pattern_name}...")
    
    # Generar trayectoria
    trajectory = self.trajectory_generators[pattern_name]()
    
    # Inicializar resultados
    results = {
        'time_s': [],
        'throughput_mbps': [],
        'distance_m': [],
        'snr_db': [],
        'prob_los': [],
        'doppler_hz': []
    }
    
    # Simular para cada timestep
    for i, position in enumerate(trajectory):
        t = i * DELTA_T
        
        # Calcular métricas de canal
        metrics = self.calculate_channel_metrics(position, self.gnb_position)
        
        # Calcular velocidad (diferencia finita)
        if i > 0:
            velocity = (position - trajectory[i-1]) / DELTA_T
            doppler = self.calculate_doppler_shift(velocity, 
                                                   self.gnb_position, 
                                                   position)
        else:
            doppler = {'doppler_hz': 0}
        
        # Almacenar resultados
        results['time_s'].append(t)
        results['throughput_mbps'].append(metrics['throughput_mbps'])
        results['distance_m'].append(metrics['distance_3d'])
        results['snr_db'].append(metrics['snr_db'])
        results['prob_los'].append(metrics['prob_los'])
        results['doppler_hz'].append(doppler['doppler_hz'])
    
    # Calcular estadísticas
    results['mean_throughput'] = np.mean(results['throughput_mbps'])
    results['std_throughput'] = np.std(results['throughput_mbps'])
    results['min_throughput'] = np.min(results['throughput_mbps'])
    results['max_throughput'] = np.max(results['throughput_mbps'])
    results['stability_score'] = (results['mean_throughput'] / 
                                  (results['std_throughput'] + 1e-6))
    
    return results
```

#### 10.3.7 Visualización

```python
def generate_mobility_plots(self, all_results):
    """Generar gráficos de análisis de movilidad"""
    
    fig = plt.figure(figsize=(18, 12))
    
    # Plot 1: Throughput vs Tiempo (todos los patrones)
    ax1 = plt.subplot(2, 3, 1)
    for pattern, results in all_results.items():
        ax1.plot(results['time_s'], results['throughput_mbps'],
                 label=pattern, linewidth=2)
    ax1.set_xlabel('Tiempo (s)')
    ax1.set_ylabel('Throughput (Mbps)')
    ax1.set_title('Throughput vs Tiempo por Patrón')
    ax1.legend()
    ax1.grid(True)
    
    # Plot 2: Comparación de Throughput Medio
    ax2 = plt.subplot(2, 3, 2)
    patterns = list(all_results.keys())
    mean_throughputs = [all_results[p]['mean_throughput'] for p in patterns]
    bars = ax2.bar(range(len(patterns)), mean_throughputs, color='steelblue')
    ax2.set_xticks(range(len(patterns)))
    ax2.set_xticklabels(patterns, rotation=45, ha='right')
    ax2.set_ylabel('Throughput Medio (Mbps)')
    ax2.set_title('Comparación de Throughput Medio')
    ax2.grid(axis='y')
    
    # Resaltar el mejor
    best_idx = np.argmax(mean_throughputs)
    bars[best_idx].set_color('green')
    
    # Plot 3: Estabilidad (Mean/Std)
    ax3 = plt.subplot(2, 3, 3)
    stability_scores = [all_results[p]['stability_score'] for p in patterns]
    ax3.bar(range(len(patterns)), stability_scores, color='coral')
    ax3.set_xticks(range(len(patterns)))
    ax3.set_xticklabels(patterns, rotation=45, ha='right')
    ax3.set_ylabel('Stability Score (Mean/Std)')
    ax3.set_title('Estabilidad de Conexión')
    ax3.grid(axis='y')
    
    # Plot 4: Distancia vs Tiempo (ejemplo: circular)
    ax4 = plt.subplot(2, 3, 4)
    example_pattern = 'circular'
    ax4.plot(all_results[example_pattern]['time_s'],
             all_results[example_pattern]['distance_m'],
             linewidth=2, color='purple')
    ax4.set_xlabel('Tiempo (s)')
    ax4.set_ylabel('Distancia 3D (m)')
    ax4.set_title(f'Distancia vs Tiempo ({example_pattern})')
    ax4.grid(True)
    
    # Plot 5: Doppler Shift (ejemplo: linear)
    ax5 = plt.subplot(2, 3, 5)
    example_pattern2 = 'linear'
    ax5.plot(all_results[example_pattern2]['time_s'],
             all_results[example_pattern2]['doppler_hz'],
             linewidth=2, color='red')
    ax5.set_xlabel('Tiempo (s)')
    ax5.set_ylabel('Doppler Shift (Hz)')
    ax5.set_title(f'Efecto Doppler ({example_pattern2})')
    ax5.grid(True)
    
    # Plot 6: Probabilidad LoS (ejemplo: spiral)
    ax6 = plt.subplot(2, 3, 6)
    example_pattern3 = 'spiral'
    ax6.plot(all_results[example_pattern3]['time_s'],
             all_results[example_pattern3]['prob_los'],
             linewidth=2, color='green')
    ax6.set_xlabel('Tiempo (s)')
    ax6.set_ylabel('Probabilidad LoS')
    ax6.set_title(f'Probabilidad LoS ({example_pattern3})')
    ax6.set_ylim([0, 1.1])
    ax6.grid(True)
    
    plt.tight_layout()
    plt.savefig('outputs/mobility_analysis.png', dpi=150)
```

#### 10.3.8 Métricas Calculadas

1. **Throughput vs Tiempo**: $R(t)$ para cada patrón

2. **Throughput Medio**: 
   $$\bar{R} = \frac{1}{T}\sum_{t=1}^T R(t)$$

3. **Desviación Estándar**: 
   $$\sigma_R = \sqrt{\frac{1}{T}\sum_{t=1}^T (R(t) - \bar{R})^2}$$

4. **Stability Score**: 
   $$S = \frac{\bar{R}}{\sigma_R}$$
   Indica estabilidad relativa de la conexión

5. **Doppler Máximo**:
   $$f_d^{\max} = \frac{v_{\max} \cdot f_c}{c}$$

6. **Outage Probability**:
   $$P_{\text{outage}} = \frac{1}{T}\sum_{t=1}^T \mathbb{1}(R(t) < R_{\min})$$

#### 10.3.9 Resultados Esperados

| Patrón | Throughput Medio | Estabilidad | Aplicación |
|--------|-----------------|-------------|------------|
| **Circular** | ~600 Mbps | Alta (S > 30) | Vigilancia, patrol |
| **Linear** | ~550 Mbps | Media (S ~ 15) | Tránsito rápido |
| **Spiral** | ~500 Mbps | Media (S ~ 12) | Exploración 3D |
| **Figure-8** | ~480 Mbps | Baja (S ~ 8) | Test de handover |
| **Random Walk** | ~400 Mbps | Muy baja (S ~ 5) | Worst-case |
| **Optimized** | ~700 Mbps | Alta (S > 25) | Referencia óptima |

#### 10.3.10 Conceptos Teóricos Clave

1. **Modelo de Propagación Simplificado**: Usa fórmulas analíticas en vez de RT completo (más rápido, menos preciso)

2. **Doppler y OFDM**: Doppler < 1% del espaciado de subportadora → impacto negligible

3. **Trade-off Throughput/Estabilidad**: Patrones estables (circular) vs exploratorios (spiral)

4. **Optimización de Trayectoria**: Differential Evolution para encontrar camino óptimo

5. **Aplicaciones Prácticas**:
   - **Circular**: Vigilancia perimetral de área
   - **Linear**: Delivery punto a punto
   - **Optimized**: Planning de misiones críticas

---

### 10.4 Fase 4: Análisis de Interferencia Multi-UAV (Botón 4)

**Archivo**: `GUI/analysis/interference_analysis_gui.py`  
**Clase**: `InterferenceAnalysisGUI`  
**Sistema**: Modelo **analítico** de interferencia (NO usa Sionna)

#### 10.4.1 Objetivo

Caracterizar escenarios de interferencia multi-UAV, calcular SINR, y evaluar técnicas de mitigación como asignación de recursos y control de potencia.

#### 10.4.2 Escenarios de Interferencia

Se evalúan **5 escenarios** con diferentes densidades de UAVs:

| Escenario | UAVs | Área | Sep. Mínima | Características |
|-----------|------|------|-------------|-----------------|
| **Low Density** | 3 | 300m × 300m | 100m | Baja interferencia |
| **Medium Density** | 5 | 240m × 240m | 80m | Interferencia moderada |
| **High Density** | 8 | 180m × 180m | 60m | Alta interferencia |
| **Clustered** | 6 | 3 clusters | 50m | Interferencia extrema local |
| **Distributed** | 7 | 360m × 360m | 120m | Mínima interferencia |

#### 10.4.3 Modelo de Interferencia

**Configuración del Sistema:**
```python
config = {
    'frequency_ghz': 3.5,
    'bandwidth_mhz': 100,
    'subcarrier_spacing_khz': 30,
    'resource_blocks': 273,         # 100 MHz / (30 kHz × 12 subportadoras)
    'gnb_position': [300, 200, 50],  # gNB sobre edificio
    'gnb_power_dbm': 43,
    'gnb_antennas': 64,              # 8×8 MIMO
    'uav_antennas': 4,               # 2×2 MIMO
    'noise_figure_db': 7,
    'thermal_noise_dbm': -104        # Para 100 MHz BW
}
```

**Cálculo de SINR:**
```python
def calculate_sinr_matrix(self, uav_positions, gnb_position):
    """Calcular SINR para cada UAV considerando interferencia mutua"""
    
    num_uavs = len(uav_positions)
    
    # Matriz de channel gains [gNB → UAV_k]
    channel_gains_db = np.zeros(num_uavs)
    
    for k in range(num_uavs):
        # Distancia 3D
        distance = np.linalg.norm(uav_positions[k] - gnb_position)
        
        # Path loss
        freq_ghz = 3.5
        pl_db = 28.0 + 22.0*np.log10(distance) + 20.0*np.log10(freq_ghz)
        
        # Channel gain (incluyendo ganancia MIMO y beamforming)
        mimo_gain_db = 10 * np.log10(min(64, 4))  # min(Nt, Nr) = 4
        beamforming_gain_db = 10 * np.log10(64)    # Directividad de array 8×8
        
        channel_gains_db[k] = -pl_db + mimo_gain_db + beamforming_gain_db
    
    # Convertir a lineal
    channel_gains_linear = 10 ** (channel_gains_db / 10.0)
    
    # Potencia transmitida (asumiendo igual para todos)
    tx_power_dbm = 43  # gNB
    tx_power_linear = 10 ** ((tx_power_dbm - 30) / 10.0)  # Convertir a Watts
    
    # Potencia de ruido
    noise_power_dbm = -104  # 100 MHz
    noise_power_linear = 10 ** ((noise_power_dbm - 30) / 10.0)
    
    # Matriz de interferencia [UAV_j → UAV_k]
    interference_matrix_linear = np.zeros((num_uavs, num_uavs))
    
    # Modelo simplificado: interferencia proporcional a channel gain
    # En realidad depende de asignación de recursos (RBs)
    for k in range(num_uavs):
        for j in range(num_uavs):
            if j != k:
                # Interferencia: UAV_j interfiere a UAV_k
                # Depende de separación espacial y beamforming
                
                # Factor de supresión por beamforming (simplificado)
                angle_separation = self._calculate_angle_separation(
                    uav_positions[k], uav_positions[j], gnb_position
                )
                
                # Beamforming reduce interferencia según ángulo
                suppression_db = -10 * np.log10(np.sin(angle_separation) + 0.1)
                suppression_linear = 10 ** (suppression_db / 10.0)
                
                interference_matrix_linear[k, j] = (tx_power_linear * 
                                                    channel_gains_linear[j] * 
                                                    suppression_linear)
    
    # Calcular SINR para cada UAV
    sinr_linear = np.zeros(num_uavs)
    sinr_db = np.zeros(num_uavs)
    
    for k in range(num_uavs):
        # Señal deseada
        signal_power = tx_power_linear * channel_gains_linear[k]
        
        # Interferencia total
        interference_power = np.sum(interference_matrix_linear[k, :])
        
        # SINR
        sinr_linear[k] = signal_power / (interference_power + noise_power_linear)
        sinr_db[k] = 10 * np.log10(sinr_linear[k] + 1e-12)
    
    return {
        'sinr_db': sinr_db,
        'sinr_linear': sinr_linear,
        'interference_matrix_linear': interference_matrix_linear,
        'channel_gains_db': channel_gains_db,
        'signal_power': tx_power_linear * channel_gains_linear,
        'interference_power': np.array([np.sum(interference_matrix_linear[k, :]) 
                                        for k in range(num_uavs)]),
        'noise_power': noise_power_linear
    }

def _calculate_angle_separation(self, uav1_pos, uav2_pos, gnb_pos):
    """Calcular separación angular desde perspectiva del gNB"""
    # Vectores desde gNB a cada UAV
    vec1 = uav1_pos - gnb_pos
    vec2 = uav2_pos - gnb_pos
    
    # Normalizar
    vec1_norm = vec1 / (np.linalg.norm(vec1) + 1e-9)
    vec2_norm = vec2 / (np.linalg.norm(vec2) + 1e-9)
    
    # Ángulo entre vectores
    cos_angle = np.dot(vec1_norm, vec2_norm)
    angle = np.arccos(np.clip(cos_angle, -1, 1))
    
    return angle
```

#### 10.4.4 Generación de Posiciones UAV

**Low Density (3 UAVs):**
```python
def generate_low_density_positions(self):
    """3 UAVs bien separados"""
    height = 80  # Altura óptima de Fase 2
    area = 300   # ±300m
    
    positions = [
        [100, 100, height],
        [-100, 100, height],
        [0, -120, height]
    ]
    
    return np.array(positions)
```

**High Density (8 UAVs):**
```python
def generate_high_density_positions(self):
    """8 UAVs en área compacta"""
    height = 80
    area = 180  # ±180m (área reducida)
    min_separation = 60  # metros
    
    positions = []
    max_attempts = 1000
    
    while len(positions) < 8:
        # Posición aleatoria
        x = np.random.uniform(-area, area)
        y = np.random.uniform(-area, area)
        z = height
        
        candidate = np.array([x, y, z])
        
        # Verificar separación mínima
        valid = True
        for existing in positions:
            if np.linalg.norm(candidate - existing) < min_separation:
                valid = False
                break
        
        if valid:
            positions.append(candidate)
    
    return np.array(positions)
```

**Clustered (6 UAVs):**
```python
def generate_clustered_positions(self):
    """6 UAVs en 2-3 clusters"""
    height = 80
    cluster_centers = [
        [-100, -100, height],
        [150, 100, height],
        [50, -150, height]
    ]
    
    positions = []
    uavs_per_cluster = 2  # 2 UAVs por cluster
    
    for center in cluster_centers:
        for _ in range(uavs_per_cluster):
            # Offset aleatorio alrededor del centro
            offset = np.random.randn(3) * 25  # ±25m
            offset[2] = offset[2] * 0.5       # Menor variación en altura
            
            position = center + offset
            positions.append(position)
    
    return np.array(positions)
```

#### 10.4.5 Gestión de Recursos (RBs)

**Asignación de Resource Blocks:**
```python
def allocate_resource_blocks(self, num_uavs, total_rbs=273):
    """Asignar RBs a UAVs (Round-Robin simple)"""
    
    # Distribución equitativa
    rbs_per_uav = total_rbs // num_uavs
    remainder = total_rbs % num_uavs
    
    allocation = {}
    rb_start = 0
    
    for k in range(num_uavs):
        # Algunos UAVs reciben 1 RB extra (resto)
        rbs_allocated = rbs_per_uav + (1 if k < remainder else 0)
        
        allocation[k] = {
            'rb_start': rb_start,
            'rb_end': rb_start + rbs_allocated - 1,
            'num_rbs': rbs_allocated
        }
        
        rb_start += rbs_allocated
    
    return allocation

def calculate_throughput_with_rb_allocation(self, sinr_db, num_rbs_allocated, total_rbs=273):
    """Calcular throughput considerando RBs asignados"""
    
    # Eficiencia espectral por RB (Shannon)
    sinr_linear = 10 ** (sinr_db / 10.0)
    se_per_rb = np.log2(1 + sinr_linear)  # bits/s/Hz
    
    # Ancho de banda por RB
    bw_per_rb = 30e3 * 12  # 30 kHz × 12 subportadoras = 360 kHz
    
    # Throughput total
    throughput_mbps = se_per_rb * bw_per_rb * num_rbs_allocated / 1e6
    
    return throughput_mbps
```

#### 10.4.6 Control de Potencia

**Algoritmo de Power Control:**
```python
def power_control_algorithm(self, sinr_db_initial, sinr_target_db=15):
    """Ajustar potencias para alcanzar SINR objetivo"""
    
    num_uavs = len(sinr_db_initial)
    power_adjustments_db = np.zeros(num_uavs)
    
    # Iterativo: ajustar potencia según gap con objetivo
    max_iterations = 10
    step_size = 0.5  # Factor de actualización
    
    sinr_current = sinr_db_initial.copy()
    
    for iteration in range(max_iterations):
        for k in range(num_uavs):
            # Gap con objetivo
            sinr_gap_db = sinr_target_db - sinr_current[k]
            
            # Ajuste de potencia proporcional
            power_adjustment = step_size * sinr_gap_db
            
            # Límites de potencia
            power_adjustments_db[k] += power_adjustment
            power_adjustments_db[k] = np.clip(power_adjustments_db[k], -10, +10)
        
        # Recalcular SINR con nuevas potencias (simplificado)
        sinr_current = sinr_db_initial + power_adjustments_db * 0.8  # Factor de acoplamiento
    
    return {
        'power_adjustments_db': power_adjustments_db,
        'sinr_final_db': sinr_current,
        'converged': np.all(np.abs(sinr_current - sinr_target_db) < 1.0)
    }
```

#### 10.4.7 Análisis de Fairness

**Índice de Jain:**
```python
def calculate_fairness(self, throughputs):
    """Calcular índice de fairness de Jain"""
    n = len(throughputs)
    
    numerator = (np.sum(throughputs)) ** 2
    denominator = n * np.sum(throughputs ** 2)
    
    fairness_index = numerator / (denominator + 1e-12)
    
    # Fairness ∈ [1/n, 1]
    # 1: Perfecta equidad
    # 1/n: Máxima inequidad
    
    return fairness_index
```

#### 10.4.8 Visualización

```python
def generate_interference_plots(self, all_scenarios_results):
    """Generar gráficos de análisis de interferencia"""
    
    fig = plt.figure(figsize=(20, 12))
    
    # Plot 1: SINR por Escenario (Box plot)
    ax1 = plt.subplot(2, 3, 1)
    sinr_data = [results['sinr_db'] for results in all_scenarios_results.values()]
    ax1.boxplot(sinr_data, labels=all_scenarios_results.keys())
    ax1.set_ylabel('SINR (dB)')
    ax1.set_title('Distribución SINR por Escenario')
    ax1.axhline(15, color='red', linestyle='--', label='Target 15 dB')
    ax1.legend()
    ax1.grid(True, axis='y')
    plt.xticks(rotation=45, ha='right')
    
    # Plot 2: Throughput Total por Escenario
    ax2 = plt.subplot(2, 3, 2)
    scenarios = list(all_scenarios_results.keys())
    total_throughputs = [np.sum(results['throughput_mbps']) 
                         for results in all_scenarios_results.values()]
    bars = ax2.bar(range(len(scenarios)), total_throughputs, color='steelblue')
    ax2.set_xticks(range(len(scenarios)))
    ax2.set_xticklabels(scenarios, rotation=45, ha='right')
    ax2.set_ylabel('Throughput Total (Mbps)')
    ax2.set_title('Throughput Total del Sistema')
    ax2.grid(axis='y')
    
    # Resaltar mejor
    best_idx = np.argmax(total_throughputs)
    bars[best_idx].set_color('green')
    
    # Plot 3: Fairness Index por Escenario
    ax3 = plt.subplot(2, 3, 3)
    fairness_indices = [results['fairness_index'] 
                       for results in all_scenarios_results.values()]
    ax3.bar(range(len(scenarios)), fairness_indices, color='coral')
    ax3.set_xticks(range(len(scenarios)))
    ax3.set_xticklabels(scenarios, rotation=45, ha='right')
    ax3.set_ylabel('Índice de Jain')
    ax3.set_ylim([0, 1.05])
    ax3.set_title('Equidad en Distribución de Recursos')
    ax3.axhline(0.8, color='green', linestyle='--', label='Good (>0.8)')
    ax3.legend()
    ax3.grid(axis='y')
    
    # Plot 4: Matriz de Interferencia (ejemplo: High Density)
    ax4 = plt.subplot(2, 3, 4)
    example_scenario = 'high_density'
    interference_matrix = all_scenarios_results[example_scenario]['interference_matrix_db']
    im = ax4.imshow(interference_matrix, cmap='hot', interpolation='nearest')
    ax4.set_xlabel('UAV Source')
    ax4.set_ylabel('UAV Victim')
    ax4.set_title(f'Matriz de Interferencia ({example_scenario})')
    plt.colorbar(im, ax=ax4, label='Interferencia (dB)')
    
    # Plot 5: Throughput Individual (ejemplo: High Density)
    ax5 = plt.subplot(2, 3, 5)
    throughputs = all_scenarios_results[example_scenario]['throughput_mbps']
    ax5.bar(range(len(throughputs)), throughputs, color='purple')
    ax5.set_xlabel('UAV ID')
    ax5.set_ylabel('Throughput (Mbps)')
    ax5.set_title(f'Throughput Individual ({example_scenario})')
    ax5.grid(axis='y')
    
    # Plot 6: Posiciones UAV 2D (ejemplo: Clustered)
    ax6 = plt.subplot(2, 3, 6)
    example_scenario2 = 'clustered'
    positions = all_scenarios_results[example_scenario2]['uav_positions']
    gnb_pos = all_scenarios_results[example_scenario2]['gnb_position']
    
    # Plot UAVs
    ax6.scatter(positions[:, 0], positions[:, 1], 
               s=200, c='blue', marker='^', label='UAVs', alpha=0.7)
    
    # Plot gNB
    ax6.scatter(gnb_pos[0], gnb_pos[1], 
               s=300, c='red', marker='*', label='gNB', zorder=10)
    
    # Anotar UAV IDs
    for i, pos in enumerate(positions):
        ax6.annotate(f'UAV{i}', (pos[0], pos[1]), 
                    xytext=(5, 5), textcoords='offset points')
    
    ax6.set_xlabel('X (m)')
    ax6.set_ylabel('Y (m)')
    ax6.set_title(f'Distribución Espacial UAVs ({example_scenario2})')
    ax6.legend()
    ax6.grid(True)
    ax6.axis('equal')
    
    plt.tight_layout()
    plt.savefig('outputs/interference_analysis.png', dpi=150)
```

#### 10.4.9 Métricas Calculadas

1. **SINR Individual (dB)**:
   $$\text{SINR}_k = 10\log_{10}\left(\frac{P_k |h_k|^2}{\sum_{j\neq k} P_j |h_j|^2 + N_0}\right)$$

2. **Throughput Individual (Mbps)**:
   $$R_k = \text{RBs}_k \cdot 360\text{ kHz} \cdot \log_2(1 + \text{SINR}_k) / 10^6$$

3. **Throughput Total del Sistema**:
   $$R_{\text{total}} = \sum_{k=1}^K R_k$$

4. **Fairness Index (Jain)**:
   $$\mathcal{F} = \frac{(\sum_k R_k)^2}{K \sum_k R_k^2}$$

5. **Outage Probability**:
   $$P_{\text{outage}} = \frac{1}{K}\sum_{k=1}^K \mathbb{1}(\text{SINR}_k < \gamma_{\text{th}})$$

6. **Matriz de Interferencia**:
   $\mathbf{I}_{j,k}$: Interferencia de UAV $j$ a UAV $k$

#### 10.4.10 Resultados Esperados

| Escenario | UAVs | SINR Medio | Throughput Total | Fairness | Conclusión |
|-----------|------|------------|------------------|----------|------------|
| **Low Density** | 3 | ~22 dB | ~1500 Mbps | 0.95 | Excelente, baja interferencia |
| **Medium Density** | 5 | ~17 dB | ~2000 Mbps | 0.88 | Bueno, requiere scheduling |
| **High Density** | 8 | ~12 dB | ~2200 Mbps | 0.70 | Crítico, ICIC necesario |
| **Clustered** | 6 | ~10 dB | ~1600 Mbps | 0.60 | Muy crítico, alta varianza |
| **Distributed** | 7 | ~20 dB | ~2400 Mbps | 0.92 | Óptimo, máxima capacidad |

#### 10.4.11 Conceptos Teóricos Clave

1. **SINR vs SNR**: SINR incluye interferencia de otros usuarios (más realista para multi-UAV)

2. **Interferencia Co-Canal**: UAVs comparten misma frecuencia → necesario scheduling

3. **Beamforming Espacial**: Arrays masivos en gNB pueden separar espacialmente UAVs

4. **Resource Block Allocation**: División de ancho de banda en bloques asignables

5. **Fairness**: Balance entre eficiencia espectral total y equidad entre usuarios

6. **Power Control**: Ajustar potencias para SINR objetivo sin aumentar interferencia

7. **Aplicaciones**:
   - **Low Density**: Delivery drones dispersos
   - **High Density**: Enjambre coordinado
   - **Clustered**: Emergency response concentrado

---

## 11. Configuraciones Técnicas

### 11.1 Resumen de Configuraciones por Fase

| Parámetro | Fase 1 (MIMO) | Fase 2 (Altura) | Fase 3 (Movilidad) | Fase 4 (Interferencia) |
|-----------|--------------|-----------------|--------------------|-----------------------|
| **Sistema** | BasicUAVSystem + Sionna RT | BasicUAVSystem + Sionna RT | Modelo Analítico | Modelo Analítico |
| **Frecuencia** | 3.5 GHz | 3.5 GHz | 3.5 GHz | 3.5 GHz |
| **Ancho de Banda** | 100 MHz | 100 MHz | 100 MHz | 100 MHz |
| **gNB Antenas** | Variable (1-64) | 64 (8×8) | 64 (8×8) | 64 (8×8) |
| **UAV Antenas** | Variable (1-8) | 4 (2×2) | 4 (2×2) | 4 (2×2) |
| **Altura UAV** | 100m fija | 20-200m variable | 80m (óptima) | 80m (óptima) |
| **Número UAVs** | 1 | 1 | 1 (móvil) | 3-8 (estáticos) |
| **SNR Range** | 0-30 dB | 20 dB fijo | Variable (canal) | Variable (SINR) |
| **Ray Tracing Depth** | 5 | 5 | N/A | N/A |
| **Duración Simulación** | N/A | N/A | 60 segundos | Snapshot |
| **Puntos de Evaluación** | 7 SNRs × 5 configs | 19 alturas | 120 timesteps × 6 patrones | 5 escenarios |

### 11.2 Parámetros RF Detallados

```python
class RFConfig:
    # Frecuencia Portadora
    FREQUENCY = 7.125e9              # 3.5 GHz (banda n78 5G NR)
    WAVELENGTH = 3e8 / FREQUENCY     # λ = 8.57 cm
    
    # Ancho de Banda
    BANDWIDTH = 100e6                # 100 MHz
    SUBCARRIER_SPACING = 30e3        # 30 kHz (numerología μ=1)
    NUM_SUBCARRIERS = 3276           # BW / Δf = 3,276
    NUM_RESOURCE_BLOCKS = 273        # 3,276 / 12 = 273 RBs
    
    # Potencias
    TX_POWER_GNB = 43                # 43 dBm = 20W
    TX_POWER_UAV = 23                # 23 dBm = 200mW
    
    # Ruido
    NOISE_FIGURE = 7                 # 7 dB
    THERMAL_NOISE_DENSITY = -174     # -174 dBm/Hz
    THERMAL_NOISE_POWER = -174 + 10*np.log10(100e6)  # -104 dBm para 100MHz
    
    # Link Budget
    CABLE_LOSS = 2                   # 2 dB pérdidas en cables/conectores
    BODY_LOSS_UAV = 3                # 3 dB pérdidas por cuerpo del drone
```

### 11.3 Parámetros de Antenas

```python
class AntennaConfig:
    # gNB Base Station
    GNB_ARRAY = {
        'num_rows': 8,
        'num_cols': 8,
        'total_elements': 64,
        'vertical_spacing': 0.5,       # λ/2 = 4.28 cm
        'horizontal_spacing': 0.5,
        'pattern': 'iso',              # Isotrópico (omnidireccional en plano)
        'polarization': 'V',           # Vertical
        'gain_per_element_dbi': 2.15,  # Ganancia isotrópica
        'total_array_gain_db': 10*np.log10(64) + 2.15,  # ~20 dBi
        'half_power_beamwidth_deg': 65 / 8,  # Aproximado para array 8×8
        'front_to_back_ratio_db': 25
    }
    
    # UAV Receiver
    UAV_ARRAY = {
        'num_rows': 2,
        'num_cols': 2,
        'total_elements': 4,
        'vertical_spacing': 0.5,
        'horizontal_spacing': 0.5,
        'pattern': 'iso',
        'polarization': 'V',
        'gain_per_element_dbi': 2.15,
        'total_array_gain_db': 10*np.log10(4) + 2.15,  # ~8.2 dBi
        'omnidirectional': True        # No beamforming en UAV (recepción)
    }
```

### 11.4 Escenario Munich 3D

```python
class ScenarioConfig:
    # Dimensiones del Escenario
    AREA_SIZE_X = 500                # metros
    AREA_SIZE_Y = 500
    AREA_SIZE_Z = 250                # Altura máxima
    
    # Posición gNB
    GNB_POSITION = [0, 0, 30]       # Centro, altura 30m (sobre edificio)
    GNB_ORIENTATION = [0, 0, 0]      # Azimuth, Elevation, Roll (grados)
    
    # Posición UAV (inicial)
    UAV1_POSITION = [100, 100, 100]  # 100m altura, 141m distancia 2D
    UAV1_ORIENTATION = [0, 0, 0]
    
    # Edificios Munich (Sionna predefinido)
    NUM_BUILDINGS = 6
    BUILDING_MATERIALS = ['concrete', 'glass', 'metal']
    AVERAGE_BUILDING_HEIGHT = 35     # metros
    MAX_BUILDING_HEIGHT = 50
    
    # Rangos de Análisis
    HEIGHT_RANGE = np.linspace(20, 200, 19)  # 19 alturas
    COVERAGE_AREA = {
        'x_min': -200, 'x_max': 200,
        'y_min': -200, 'y_max': 200,
        'resolution': 20                # 20×20 grid = 400 puntos
    }
```

### 11.5 Parámetros de Simulación

```python
class SimulationConfig:
    # Ray Tracing
    RT_MAX_DEPTH = 5                 # Máximo 5 reflexiones
    RT_NUM_SAMPLES = 1e6            # 1M rays para ray launching
    RT_DIFFRACTION = False           # Difracción desactivada (caro computacionalmente)
    RT_SCATTERING = False            # Scattering desactivado
    
    # System Level
    BATCH_SIZE = 100                # Batch size TensorFlow
    NUM_BATCHES = 3                 # Batches por punto
    NUM_BITS_PER_SYMBOL = 6         # 64-QAM
    CODE_RATE = 0.5                 # LDPC rate 1/2
    
    # SNR Range
    SNR_MIN_DB = 0
    SNR_MAX_DB = 30
    SNR_STEP_DB = 5
    SNR_RANGE = np.arange(SNR_MIN_DB, SNR_MAX_DB+1, SNR_STEP_DB)  # [0, 5, ..., 30]
    
    # Umbrales
    TARGET_BLER = 0.1               # 10% BLER objetivo
    TARGET_THROUGHPUT_MBPS = 100    # 100 Mbps mínimo
    MIN_SNR_DB = 5                  # SNR mínimo para servicio
    MIN_SINR_DB = 0                 # SINR mínimo para servicio
    
    # Movilidad
    MOBILITY_DURATION_S = 60        # 60 segundos de simulación
    MOBILITY_NUM_STEPS = 120        # 120 timesteps
    MOBILITY_DELTA_T = 0.5          # 0.5 segundos por paso
    MAX_UAV_VELOCITY_MS = 20        # 20 m/s = 72 km/h
    
    # Interferencia
    INTERFERENCE_SCENARIOS = 5
    MAX_UAVS_SIMULATED = 8
    MIN_UAV_SEPARATION_M = 50       # Separación mínima entre UAVs
```

### 11.6 Dependencias y Entorno

```python
# requirements.txt
"""
tensorflow>=2.12.0
sionna>=0.14.0
numpy>=1.23.0
matplotlib>=3.7.0
scipy>=1.10.0
PyQt6>=6.4.0
mitsuba>=3.0.0          # Requerido por Sionna RT
drjit>=0.4.0            # Requerido por Mitsuba
"""

# Configuración GPU
import tensorflow as tf
gpus = tf.config.list_physical_devices('GPU')
if gpus:
    # Habilitar memory growth para evitar OOM
    for gpu in gpus:
        tf.config.experimental.set_memory_growth(gpu, True)
    print(f"✅ {len(gpus)} GPU(s) disponible(s)")
else:
    print("⚠️  No GPU detectada, usando CPU")
```

---

## 12. Flujo de Trabajo Completo

### 12.1 Flujo de Usuario Final

```
┌──────────────────────────────────────────────────────┐
│  Usuario ejecuta: python GUI/main.py                 │
└────────────────────┬─────────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────┐
│  GUI PyQt6 se inicializa                             │
│  - Ventana principal con splitter                    │
│  - Panel izquierdo: 4 botones de análisis            │
│  - Panel derecho: Visualización + logs               │
│  - Status bar con indicadores                        │
└────────────────────┬─────────────────────────────────┘
                     │
       ┌─────────────┴──────────────┐
       │                            │
┌──────▼────────┐          ┌────────▼─────────┐
│  Usuario      │          │  Usuario         │
│  selecciona   │   ...    │  selecciona      │
│  Botón 1-4    │          │  configuración   │
└──────┬────────┘          └────────┬─────────┘
       │                            │
       └────────────┬───────────────┘
                    │
┌───────────────────▼──────────────────────────────────┐
│  GUI crea SimulationWorker (QThread)                 │
│  - tipo: "mimo_beamforming" / "height_analysis" etc  │
│  - parameters: dict con configuración                │
│  - Conecta signals: progress, finished, error        │
└────────────────────┬─────────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────┐
│  Worker.start() - Thread independiente               │
│  - No bloquea GUI                                    │
│  - Emite progress signals periódicamente             │
└────────────────────┬─────────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────┐
│  Worker.run() ejecuta análisis específico            │
│  ┌────────────────────────────────────────────────┐ │
│  │  if tipo == "mimo_beamforming":                │ │
│  │      from analysis.mimo_beamforming_gui import │ │
│  │          run_mimo_analysis_gui                 │ │
│  │      result = run_mimo_analysis_gui()          │ │
│  └────────────────────────────────────────────────┘ │
│  (Similar para otros tipos)                          │
└────────────────────┬─────────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────┐
│  Análisis se ejecuta:                                │
│  1. Inicializa objetos (Scenario, System, etc)       │
│  2. Loop principal de simulación                     │
│  3. Emite progress updates vía callback              │
│  4. Genera plots y guarda archivos                   │
│  5. Prepara result dict                              │
└────────────────────┬─────────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────┐
│  Worker emite finished signal con result             │
│  result = {                                          │
│      'plots': ['path/plot1.png', ...],              │
│      'metrics': {...},                              │
│      'summary': "Texto resumen",                    │
│      'data_file': 'path/data.json'                  │
│  }                                                   │
└────────────────────┬─────────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────┐
│  GUI recibe finished signal                          │
│  - MainWindow.display_results(result)                │
│  - Carga plots en panel visualización                │
│  - Muestra summary en QTextEdit logs                 │
│  - Habilita botón "Export Data"                      │
│  - Actualiza status bar: "✅ Completado"             │
└──────────────────────────────────────────────────────┘
```

### 12.2 Flujo de Fase 1 (MIMO) Detallado

```
run_mimo_analysis_gui(output_dir)
    │
    ├─> 1. Inicialización
    │   ├─> MIMOBeamformingGUI.__init__()
    │   │   ├─> Munich UAVScenario(enable_preview=False)
    │   │   │   ├─> scene = sionna.rt.load_scene(sionna.rt.scene.munich)
    │   │   │   ├─> scene.add(Transmitter("gNB", pos=[0,0,30]))
    │   │   │   ├─> scene.add(Receiver("UAV1", pos=[100,100,100]))
    │   │   │   ├─> scene.tx_array = PlanarArray(8×8)
    │   │   │   ├─> scene.rx_array = PlanarArray(2×2)
    │   │   │   └─> path_solver = PathSolver()
    │   │   └─> BasicUAVSystem(scenario)
    │   │       ├─> paths = scenario.get_paths(max_depth=5)
    │   │       └─> _setup_channel()
    │   │
    │   └─> Progress: "Sistema inicializado"
    │
    ├─> 2. Análisis MIMO
    │   ├─> analyze_mimo_configurations()
    │   │   │
    │   │   ├─> FOR config IN [SISO, 2×2, 4×4, 8×4, 16×8]:
    │   │   │   ├─> _configure_mimo(config)
    │   │   │   │   ├─> Ajustar scene.tx_array según config
    │   │   │   │   └─> Ajustar scene.rx_array según config
    │   │   │   │
    │   │   │   ├─> system.simulate_throughput(snr_range=[0,5,...,30])
    │   │   │   │   │
    │   │   │   │   ├─> FOR snr_db IN [0, 5, 10, 15, 20, 25, 30]:
    │   │   │   │   │   ├─> _simulate_single_snr(snr_db)
    │   │   │   │   │   │   ├─> h_freq = scenario.get_channel_response(paths)
    │   │   │   │   │   │   ├─> channel_gain = tf.reduce_mean(|h_freq|²)
    │   │   │   │   │   │   ├─> snr_eff = snr_db + channel_gain_db
    │   │   │   │   │   │   ├─> se = mimo_gain × log₂(1 + 10^(snr_eff/10))
    │   │   │   │   │   │   ├─> throughput = se × 100 MHz
    │   │   │   │   │   │   └─> Return {throughput, se, bler, ...}
    │   │   │   │   │   │
    │   │   │   │   │   └─> Progress: "SISO: SNR 15 dB → 250 Mbps"
    │   │   │   │   │
    │   │   │   │   └─> Return results[config] = {snr_db, throughput_mbps, ...}
    │   │   │   │
    │   │   │   └─> Progress: "MIMO 4×4 completado"
    │   │   │
    │   │   └─> Return mimo_results
    │   │
    │   └─> Progress: "Análisis MIMO completado"
    │
    ├─> 3. Análisis Beamforming
    │   ├─> analyze_beamforming_strategies()
    │   │   ├─> _configure_mimo('MIMO_16x8')  # Usar mejor MIMO
    │   │   │
    │   │   ├─> FOR strategy IN [omnidirectional, MRT, ZF, MMSE, SVD]:
    │   │   │   ├─> _apply_beamforming(strategy)
    │   │   │   │   ├─> Calcular precoder W según estrategia
    │   │   │   │   └─> Aplicar W a transmisión
    │   │   │   │
    │   │   │   ├─> system.simulate_throughput(snr_range)
    │   │   │   │   └─> (Similar a análisis MIMO)
    │   │   │   │
    │   │   │   └─> Progress: "SVD beamforming: 1500 Mbps @ 20dB"
    │   │   │
    │   │   └─> Return beamforming_results
    │   │
    │   └─> Progress: "Análisis Beamforming completado"
    │
    ├─> 4. Generar Visualizaciones
    │   ├─> generate_plots(mimo_results, beamforming_results)
    │   │   ├─> Plot 1: Throughput vs SNR (MIMO comparison)
    │   │   │   └─> Save: outputs/mimo_comparison.png
    │   │   │
    │   │   ├─> Plot 2: Throughput vs SNR (Beamforming comparison)
    │   │   │   └─> Save: outputs/beamforming_comparison.png
    │   │   │
    │   │   ├─> Plot 3: Channel Gain Heatmap
    │   │   │   └─> Save: outputs/channel_gain_heatmap.png
    │   │   │
    │   │   └─> Plot 4: 3D Scene Munich
    │   │       ├─> scenario.scene.preview()
    │   │       └─> Save: outputs/3d_scene.png
    │   │
    │   └─> Progress: "Gráficos generados"
    │
    ├─> 5. Guardar Datos
    │   ├─> save_results_json(mimo_results, beamforming_results)
    │   │   └─> Save: outputs/mimo_beamforming_results.json
    │   │
    │   └─> Progress: "Datos guardados"
    │
    └─> 6. Return result dict
        └─> {
              'plots': ['outputs/mimo_comparison.png', ...],
              'metrics': {
                  'best_mimo': 'MIMO 16×8',
                  'best_beamforming': 'SVD',
                  'max_throughput_mbps': 1500,
                  ...
              },
              'summary': "Análisis MIMO y Beamforming completado...",
              'data_file': 'outputs/mimo_beamforming_results.json'
            }
```

### 12.3 Gestión de Errores

```python
try:
    # Ejecutar análisis
    result = run_mimo_analysis_gui(output_dir)
    
except ImportError as e:
    # Dependencias faltantes
    error_msg = f"Error de importación: {e}\nVerifica instalación de Sionna"
    result = {'error': error_msg, 'plots': [], 'summary': error_msg}
    
except tf.errors.ResourceExhaustedError:
    # OOM en GPU
    error_msg = "GPU Out of Memory. Reduce batch_size o usa CPU"
    result = {'error': error_msg, 'plots': [], 'summary': error_msg}
    
except FileNotFoundError as e:
    # Escena Munich no encontrada
    error_msg = f"Escena no encontrada: {e}"
    result = {'error': error_msg, 'plots': [], 'summary': error_msg}
    
except Exception as e:
    # Error general
    error_msg = f"Error inesperado: {str(e)}\n{traceback.format_exc()}"
    result = {'error': error_msg, 'plots': [], 'summary': error_msg}
    
finally:
    # Siempre retornar un dict válido
    if not isinstance(result, dict):
        result = {'error': 'Unknown error', 'plots': [], 'summary': 'Error'}
```

---

## 13. Resultados y Métricas

### 13.1 Métricas por Fase

#### Fase 1: MIMO y Beamforming

**Configuración Óptima Encontrada:**
- **MIMO**: 16×8 (16 antenas gNB, 8 antenas UAV)
- **Beamforming**: SVD (Singular Value Decomposition)
- **Throughput Máximo**: ~1500 Mbps @ SNR 20 dB
- **Ganancia MIMO**: 12.2 dB respecto a SISO
- **Ganancia Beamforming**: +36% respecto a omnidirectional

**Tabla Comparativa:**

| Config | Throughput @10dB | Throughput @20dB | Ganancia vs SISO |
|--------|------------------|------------------|------------------|
| SISO 1×1 | 35 Mbps | 66 Mbps | 0 dB (baseline) |
| MIMO 2×2 | 95 Mbps | 180 Mbps | +4.3 dB |
| MIMO 4×4 | 230 Mbps | 450 Mbps | +8.3 dB |
| MIMO 8×4 | 280 Mbps | 550 Mbps | +9.2 dB |
| **MIMO 16×8** | **600 Mbps** | **1100 Mbps** | **+12.2 dB** |

#### Fase 2: Análisis de Altura

**Altura Óptima Encontrada:** 60-80m

**Características por Rango:**

| Rango Altura | Throughput | LoS Prob | Path Loss | Conclusión |
|--------------|------------|----------|-----------|------------|
| 20-40m | 200-400 Mbps | 0-50% | Alto (120-130 dB) | Obstrucción edificios |
| **40-80m** | **600-800 Mbps** | **80-100%** | **Medio (110-115 dB)** | **ÓPTIMO** |
| 80-150m | 500-600 Mbps | 100% | Medio-Alto (115-120 dB) | LoS pero mayor distancia |
| 150-200m | 300-400 Mbps | 100% | Alto (120-125 dB) | Distancia excesiva |

**Observaciones:**
- Trade-off entre probabilidad LoS (aumenta con altura) y path loss (aumenta con distancia 3D)
- Zona óptima: 1.5× - 2× altura promedio de edificios
- Transición NLoS→LoS crítica en 40-60m para Munich

#### Fase 3: Análisis de Movilidad

**Ranking de Patrones:**

| Posición | Patrón | Throughput Medio | Estabilidad | Aplicación Recomendada |
|----------|--------|-----------------|-------------|------------------------|
| 1 | Optimized | 700 Mbps | Alta (S=28) | Misiones críticas |
| 2 | Circular | 600 Mbps | Alta (S=32) | Vigilancia continua |
| 3 | Linear | 550 Mbps | Media (S=15) | Tránsito punto a punto |
| 4 | Spiral | 500 Mbps | Media (S=12) | Exploración 3D |
| 5 | Figure-8 | 480 Mbps | Baja (S=8) | Test de handover |
| 6 | Random Walk | 400 Mbps | Muy Baja (S=5) | Worst-case testing |

**Efectos Doppler Medidos:**
- **Doppler Máximo**: 233 Hz @ 20 m/s
- **ICI Ratio**: 0.78% (negligible para Δf = 30 kHz)
- **Impacto en Throughput**: < 5% degradación

#### Fase 4: Análisis de Interferencia

**Comparación de Escenarios:**

| Escenario | UAVs | SINR Medio | Throughput Total | Fairness | Calificación |
|-----------|------|------------|------------------|----------|--------------|
| Low Density | 3 | 22 dB | 1500 Mbps | 0.95 | ⭐⭐⭐⭐⭐ Excelente |
| Medium Density | 5 | 17 dB | 2000 Mbps | 0.88 | ⭐⭐⭐⭐ Bueno |
| **Distributed** | **7** | **20 dB** | **2400 Mbps** | **0.92** | **⭐⭐⭐⭐⭐ Óptimo** |
| High Density | 8 | 12 dB | 2200 Mbps | 0.70 | ⭐⭐⭐ Crítico |
| Clustered | 6 | 10 dB | 1600 Mbps | 0.60 | ⭐⭐ Muy Crítico |

**Observaciones:**
- **Distributed**: Máxima capacidad del sistema manteniendo buena fairness
- **Clustered**: Peor escenario, interferencia extrema intra-cluster
- **High Density**: Requiere ICIC y power control para operar
- **Fairness < 0.7**: Inequidad significativa, algunos UAVs degradados

### 13.2 Validación de Resultados

#### 13.2.1 Comparación con Teoría

**Shannon Capacity Check:**

Para MIMO 16×8 @ SNR 20 dB:
```
Teórico: C = 8 × 100MHz × log₂(1 + 100) ≈ 5328 Mbps
Simulado: ~1500 Mbps
Eficiencia: 1500 / 5328 ≈ 28%
```

**Razones de la diferencia:**
- Path loss real (110-115 dB) reduce SNR efectivo
- Overhead de protocolo 5G NR (~25%)
- Imperfecciones de canal (dispersión, interferencia residual)
- Codificación no ideal (LDPC con rate < 1)

#### 13.2.2 Consistencia Inter-Fases

Verificación de consistencia entre fases:

✅ **Fase 2 → Fase 3**: Altura óptima (60-80m) usada en movilidad  
✅ **Fase 1 → Fase 4**: Configuración MIMO 16×8 usada en interferencia  
✅ **Fase 2 → Fase 4**: Altura 80m usada como referencia en multi-UAV  

### 13.3 Visualizaciones Generadas

Cada análisis genera 3-5 gráficos:

#### Fase 1 (MIMO):
1. **mimo_comparison.png**: Throughput vs SNR (5 configuraciones)
2. **beamforming_comparison.png**: Throughput vs SNR (5 estrategias)
3. **channel_gain_heatmap.png**: Ganancia del canal en área 2D
4. **3d_scene.png**: Visualización Munich con gNB y UAV

#### Fase 2 (Altura):
1. **height_analysis.png** (4 subplots):
   - Throughput vs Altura (con óptimo marcado)
   - Path Loss vs Altura
   - Probabilidad LoS vs Altura
   - SNR Efectivo vs Altura

#### Fase 3 (Movilidad):
1. **mobility_patterns.png** (6 subplots):
   - Throughput vs Tiempo (todos los patrones)
   - Comparación Throughput Medio
   - Estabilidad por patrón
   - Distancia vs Tiempo (ejemplo)
   - Doppler Shift vs Tiempo (ejemplo)
   - Probabilidad LoS vs Tiempo (ejemplo)

#### Fase 4 (Interferencia):
1. **interference_analysis.png** (6 subplots):
   - Distribución SINR por escenario (box plot)
   - Throughput Total por escenario
   - Fairness Index por escenario
   - Matriz de Interferencia (heatmap)
   - Throughput Individual por UAV
   - Distribución Espacial UAVs (mapa 2D)

---

## 14. Conclusiones

### 14.1 Hallazgos Principales

#### 14.1.1 MIMO y Beamforming (Fase 1)

1. **MIMO Masivo es crucial**: MIMO 16×8 proporciona 12.2 dB de ganancia respecto a SISO, aumentando throughput de ~66 Mbps a ~1100 Mbps @ 20 dB SNR.

2. **SVD Beamforming es óptimo**: Proporciona +36% de ganancia adicional respecto a omnidirectional, alcanzando ~1500 Mbps.

3. **Law of Diminishing Returns**: Ganancia marginal disminuye con más antenas. Salto de 8×4 a 16×8 solo aporta ~3 dB adicionales.

4. **Ray Tracing es esencial**: Captura efectos realistas de propagación urbana (reflexiones, NLoS) que modelos estadísticos simplificarían excesivamente.

#### 14.1.2 Altura Óptima (Fase 2)

1. **Existe altura óptima clara**: Para Munich urbano, altura óptima es 60-80m, maximizando throughput en ~750 Mbps.

2. **Trade-off LoS vs Distancia**: 
   - Baja altura: NLoS dominante, throughput bajo
   - Altura óptima: LoS alcanzado sin distancia excesiva
   - Alta altura: LoS garantizado pero path loss por distancia reduce throughput

3. **Regla práctica**: Altura óptima ≈ 1.5-2× altura promedio de edificios en el área.

4. **Sensibilidad**: Throughput varía ~±20% en rango 50-100m, pero cae drásticamente fuera de este rango.

#### 14.1.3 Movilidad (Fase 3)

1. **Patrón Circular es más estable**: Alta estabilidad (S=32) con throughput medio ~600 Mbps. Ideal para vigilancia.

2. **Optimización vale la pena**: Trayectoria optimizada logra ~700 Mbps (+17% vs circular), útil para misiones críticas.

3. **Doppler es negligible**: Para velocidades UAV típicas (< 20 m/s), Doppler shift < 1% del espaciado de subportadora, impacto mínimo.

4. **Trade-off Exploración/Estabilidad**: Patrones exploratorios (spiral, random walk) sacrifican throughput medio por cobertura espacial.

#### 14.1.4 Interferencia Multi-UAV (Fase 4)

1. **Distribución espacial es crítica**: Escenario "Distributed" logra 2400 Mbps total con 7 UAVs, vs "Clustered" solo 1600 Mbps con 6 UAVs.

2. **Alta densidad es desafiante**: 8 UAVs en área compacta resulta en SINR ~12 dB, requiere técnicas avanzadas (ICIC, power control).

3. **Fairness se degrada con densidad**: Fairness Index cae de 0.95 (Low Density) a 0.60 (Clustered), indicando inequidad significativa.

4. **Scheduling es esencial**: Asignación inteligente de RBs puede mejorar throughput total ~30% en escenarios densos.

### 14.2 Recomendaciones de Despliegue

#### Para Operadores de Red:

1. **Configuración MIMO**: Desplegar gNB con al menos 8×8 (64 elementos) para soporte UAV efectivo.

2. **Beamforming Adaptativo**: Implementar SVD o MMSE precoding dinámico, aumenta capacidad ~30-40%.

3. **Planificación de Altura**: Restringir operación UAV a 50-100m en urbano para throughput óptimo.

4. **Gestión de Interferencia**: En escenarios multi-UAV (>5 drones), implementar:
   - ICIC (Inter-Cell Interference Coordination)
   - Fractional Frequency Reuse
   - Power Control dinámico

#### Para Operadores de UAV:

1. **Selección de Altura**: Operar a 60-80m en urbano para maximizar throughput.

2. **Patrones de Vuelo**: 
   - Vigilancia: Usar circular (estable, ~600 Mbps)
   - Tránsito: Usar linear u optimizado (>550 Mbps)
   - Evitar: Random walk (solo testing)

3. **Separación Mínima**: Mantener >100m entre UAVs para evitar interferencia.

4. **Coordinación**: En enjambres (>5 UAVs), implementar coordinación central para asignación de recursos.

### 14.3 Limitaciones del Sistema

#### 14.3.1 Limitaciones de Simulación

1. **Doppler Simplificado**: Fase 3 usa modelo analítico en vez de RT completo, menos preciso.

2. **Interferencia Simplificada**: Fase 4 no usa Sionna, supresión beamforming aproximada.

3. **Canal Estático**: No modelamos variaciones temporales de canal (fading rápido).

4. **Single Cell**: Solo se simula un gNB, no handover ni coordinación multi-celda.

#### 14.3.2 Limitaciones de Escenario

1. **Munich Específico**: Resultados son específicos para densidad urbana de Munich. Otros entornos (rural, suburbano, denso urbano) tendrán resultados diferentes.

2. **Edificios Estáticos**: No se consideran movimiento de personas, vehículos (scattering dinámico).

3. **Clima Ideal**: No se modela lluvia, niebla, condiciones atmosféricas.

#### 14.3.3 Limitaciones de Hardware

1. **GPU Requerida**: Ray Tracing es intensivo, requiere GPU NVIDIA con CUDA para tiempos razonables.

2. **Memoria**: Escenas grandes o muchos UAVs pueden causar OOM (Out of Memory).

### 14.4 Trabajo Futuro

#### 14.4.1 Extensiones del Sistema

1. **Multi-Cell**: Simular múltiples gNBs con handover

2. **Movilidad + RT**: Integrar patrones de movilidad con Sionna RT completo

3. **Interferencia + RT**: Simular multi-UAV con RT para mayor precisión

4. **Canal Temporal**: Modelar fading rápido y variaciones temporales

#### 14.4.2 Nuevos Análisis

1. **Optimización de Trayectorias**: Algoritmos de path planning considerando QoS

2. **Energy Efficiency**: Balance throughput/consumo energético UAV

3. **Relay UAV**: UAV como relay entre gNB y UE terrestres

4. **Massive UAV Swarm**: Coordinación de >20 UAVs simultáneos

#### 14.4.3 Validación Experimental

1. **Mediciones Reales**: Comparar simulaciones con medidas de campo

2. **Calibración de Modelos**: Ajustar parámetros RT según medidas

3. **Benchmark con Otros Simuladores**: Comparar con NS-3, MATLAB

### 14.5 Impacto y Aplicaciones

#### 14.5.1 Aplicaciones Comerciales

1. **Delivery con Drones**: Optimización de rutas para throughput mínimo garantizado

2. **Video Streaming Aéreo**: Vigilancia, broadcasting eventos

3. **IoT Aéreo**: Recolección de datos de sensores distribuidos

4. **Inspección de Infraestructura**: Torres, líneas eléctricas con video HD

#### 14.5.2 Aplicaciones de Emergencia

1. **Respuesta a Desastres**: UAV relay para restaurar comunicaciones

2. **Búsqueda y Rescate**: Video en tiempo real desde drones coordinados

3. **Monitoreo de Incendios**: Swarm de UAVs con sensores

#### 14.5.3 Aplicaciones de Investigación

1. **Testbed para 5G/6G**: Plataforma de investigación para algoritmos avanzados

2. **Machine Learning**: Dataset para entrenamiento de modelos de predicción de canal

3. **Network Optimization**: Benchmarking de algoritmos de scheduling, beamforming

### 14.6 Resumen Final

Este sistema de simulación proporciona un **framework completo** para análisis de comunicaciones UAV en redes 5G NR, integrando:

✅ **Ray Tracing 3D realista** con Sionna RT  
✅ **System-Level Simulation** con Sionna SYS  
✅ **MIMO Masivo y Beamforming** avanzado  
✅ **Análisis Multi-Dimensional**: MIMO, Altura, Movilidad, Interferencia  
✅ **Interfaz Gráfica Intuitiva** con PyQt6  
✅ **Visualizaciones Comprehensivas** de resultados  

Los resultados demuestran que:

🎯 **MIMO 16×8 + SVD beamforming** proporciona throughput óptimo (~1500 Mbps)  
🎯 **Altura 60-80m** maximiza throughput en urbano  
🎯 **Patrón circular** ofrece mejor balance estabilidad/throughput  
🎯 **Distribución espacial** es crítica para escenarios multi-UAV  

Este marco teórico sirve como base para:
- **Diseño de sistemas** UAV 5G NR
- **Planificación de despliegues** comerciales
- **Investigación avanzada** en comunicaciones aéreas
- **Desarrollo de algoritmos** de optimización

---

## Referencias

### Tecnologías y Frameworks

1. **Sionna**: https://nvlabs.github.io/sionna/
   - NVIDIA Wireless Research Framework
   - Documentación oficial y tutorials

2. **3GPP 5G NR**: 
   - TS 38.211: Physical channels and modulation
   - TS 38.214: Physical layer procedures for data
   - TS 38.300: NR and NG-RAN Overall description

3. **TensorFlow**: https://www.tensorflow.org/
   - Machine Learning platform

4. **PyQt6**: https://www.riverbankcomputing.com/software/pyqt/
   - Python bindings for Qt

### Literatura Científica

1. **UAV Communications**:
   - Zeng, Y., et al. "Wireless communications with unmanned aerial vehicles: Opportunities and challenges." IEEE Communications Magazine, 2016.
   
2. **MIMO Systems**:
   - Paulraj, A., et al. "An overview of MIMO communications." IEEE Signal Processing Magazine, 2003.
   
3. **Ray Tracing**:
   - Degli-Esposti, V. "Ray tracing propagation modeling for future small-cell and indoor applications." IEEE Antennas and Propagation Magazine, 2015.

4. **5G NR**:
   - Dahlman, E., et al. "5G NR: The Next Generation Wireless Access Technology." Academic Press, 2018.

---

**Fin del Marco Teórico**

---

**Información del Proyecto:**
- **Autor**: Sistema UAV 5G NR Simulation
- **Framework**: Sionna (NVIDIA) + TensorFlow
- **Fecha**: Febrero 2026
- **Versión**: 1.0

---
