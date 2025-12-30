# SC-FDM Implementation - Documentación Completa

## Resumen de Cambios

Este documento describe la implementación de **SC-FDM (Single Carrier - Frequency Division Multiplexing)** con precodificación DFT y análisis CCDF de PAPR en el simulador OFDM-LTE.

### Cambios Principales

#### 1. **Nuevo Módulo: DFT Precoding** (`core/dft_precoding.py`)

Se implementó un nuevo módulo con las siguientes clases:

- **`DFTPrecodifier`**: Realiza la transformada DFT (Discrete Fourier Transform) en los símbolos QAM
  - Tamaño M configurable (igual al número de subportadoras de datos)
  - Normalización 1/√M para conservar energía
  - Activable/desactivable dinámicamente
  
- **`SC_FDMPrecodifier`**: Interfaz de alto nivel para precodificación SC-FDM
  - Encapsula la lógica de DFT precoding
  - Maneja el mapeo a subportadoras de datos
  - Compatible con el pipeline de modulación existente

#### 2. **Modificaciones al Modulador OFDM** (`core/modulator.py`)

Se agregó soporte para SC-FDM:

```python
# Inicializar modulador con SC-FDM
modulator = OFDMModulator(config, mode='lte', enable_sc_fdm=True)

# O dinamicamente:
modulator.set_sc_fdm_enabled(True)  # Activar
modulator.set_sc_fdm_enabled(False) # Desactivar
```

**Flujo de modulación con SC-FDM**:
1. Convertir bits a símbolos QAM
2. **[Nuevo]** Aplicar DFT precodificación al conjunto de datos
3. Mapear a subportadoras LTE (con pilotos, DC nulo, guardias)
4. Aplicar IFFT
5. Agregar prefijo cíclico

#### 3. **Sistema OFDM Mejorado** (`core/ofdm_system.py`)

- Se agregó parámetro `enable_sc_fdm` en `OFDMSystem.__init__()`
- Nuevo método: `calculate_papr_without_cp()` - Calcula PAPR sin prefijo cíclico
- Almacenamiento de PAPR:
  - `papr_values_ofdm`: PAPR de transmisiones OFDM estándar
  - `papr_values_sc_fdm`: PAPR de transmisiones SC-FDM
- Los valores se acumulan durante múltiples transmisiones para análisis CCDF

#### 4. **Análisis PAPR y CCDF** (`utils/signal_processing.py`)

Nueva clase `PAPRAnalyzer` con métodos:

- **`calculate_ccdf(papr_values_db)`**: Genera la CCDF (Complementary CDF)
  - Retorna: P(PAPR > x) vs x[dB]
  - Uso típico: `ccdf_data = PAPRAnalyzer.calculate_ccdf(papr_values)`
  
- **`plot_papr_ccdf()`**: Grafica CCDF en escala logarítmica

- **`plot_papr_ccdf_comparison()`**: Compara CCDF entre OFDM y SC-FDM

- **`get_papr_statistics()`**: Retorna estadísticas (media, mediana, std, percentiles)

#### 5. **Interfaz Gráfica Mejorada** (`gui/main_window.py`)

**Nuevo control en parámetros LTE**:
```
┌─────────────────────────────┐
│ Parámetros LTE              │
│ ─────────────────────────────│
│ Modulación: [QPSK        ▼] │
│ Ancho de banda: [5       ▼] │
│ Δf (kHz): [15.0          ▼] │
│ Prefijo Cíclico: [normal ▼] │
│ SC-FDM: [☑ Habilitar SC-FDM]│  ← NUEVO
└─────────────────────────────┘
```

**Nueva gráfica de resultados**:
- **Arriba izquierda**: Constelación TX
- **Arriba derecha**: Constelación RX
- **Centro**: CCDF de PAPR (P(PAPR > x) vs x[dB])
  - Opcionalmente compara OFDM vs SC-FDM cuando ambos datos están disponibles
- **Abajo**: Estadísticas de PAPR (media, mediana, max, min, desv. est., quartiles)

## Uso del Switch SC-FDM

### En la GUI

1. Abrir el simulador: `python main.py`
2. En el panel izquierdo, sección "Parámetros LTE"
3. Marcar/desmarcar checkbox "Habilitar SC-FDM"
4. Los parámetros se actualizan automáticamente
5. La información muestra si SC-FDM está habilitado o deshabilitado

### En código

```python
from core.ofdm_system import OFDMSystem
from config.lte_params import LTEConfig

# Crear sistema con SC-FDM
config = LTEConfig(bandwidth=5.0, modulation='QPSK')
system = OFDMSystem(config, channel_type='awgn', enable_sc_fdm=True)

# Transmitir
bits = np.random.randint(0, 2, 1000)
results = system.transmit(bits, snr_db=10.0)

# Acceder a PAPR
papr_values = system.papr_values_sc_fdm  # Lista de PAPR acumulados
```

## Cálculo de PAPR y CCDF

### PAPR Sin Prefijo Cíclico

El PAPR (Peak-to-Average Power Ratio) se calcula como:

```
PAPR = Potencia Pico / Potencia Promedio
     = max(|x[n]|²) / E[|x[n]|²]
```

**Importante**: Se calcula SIN prefijo cíclico, solo sobre la parte útil del símbolo OFDM (N muestras después de descartar el CP). Esto es más representativo del PAPR real de la señal modulada.

### CCDF (Complementary Cumulative Distribution Function)

La CCDF representa: **P(PAPR > x)** = Probabilidad de que PAPR exceda un valor x

**Interpretación**:
- Eje X: Valor de PAPR en dB
- Eje Y: Probabilidad (escala logarítmica)
- Ejemplo: Si P(PAPR > 6dB) = 0.1, significa que 10% de los símbolos tienen PAPR > 6dB

### Ventaja de SC-FDM

SC-FDM reduce significativamente el PAPR comparado con OFDM:

```
OFDM estándar:  PAPR medio ~8-10 dB, máximo ~12-15 dB
SC-FDM:         PAPR medio ~4-6 dB,  máximo ~8-10 dB
```

Esto es porque SC-FDM produce una envolvente de amplitud más uniforme (similar a una portadora única).

## Tests

Se crearon dos suites de tests:

### `tests/test_dft_precoding.py`
- Test de configuración DFT
- Test de energía (Parseval)
- Test de mapeo correcto
- Test de activación/desactivación dinámica
- Test de integración con modulador OFDM

### `tests/test_papr_ccdf.py`
- Test de cálculo CCDF
- Test de monotonidad CCDF
- Test de condiciones límite
- Test de estadísticas PAPR
- Test de almacenamiento de PAPR en sistema
- Test de comparación OFDM vs SC-FDM

**Ejecutar tests**:
```bash
python -m pytest tests/test_dft_precoding.py -v
python -m pytest tests/test_papr_ccdf.py -v
```

## Validación de Imagen

El sistema mantiene 100% de compatibilidad con transmisión y reconstrucción de imágenes:

1. SC-FDM puede activarse/desactivarse sin afectar la decodificación
2. Las imágenes se transmiten correctamente tanto con OFDM como con SC-FDM
3. El BER se reporta correctamente en ambos casos

**Script de prueba**: `test_sc_fdm_integration.py`
```bash
python test_sc_fdm_integration.py
```

## Arquitectura de Datos - Almacenamiento PAPR

```
OFDMSystem
├── papr_values_ofdm[]     # Lista de PAPR para OFDM estándar
├── papr_values_sc_fdm[]   # Lista de PAPR para SC-FDM
└── transmit()
    ├── calculate_papr_without_cp()
    ├── → papr_info_no_cp
    │   ├── papr_values (lista de PAPR por símbolo)
    │   ├── papr_mean
    │   ├── papr_max/min/std
    │   └── num_symbols
    └── → append to papr_values_[ofdm|sc_fdm]

# Después de múltiples transmisiones:
ccdf = PAPRAnalyzer.calculate_ccdf(system.papr_values_ofdm)
# → {'papr_x': [...], 'ccdf_y': [...]}

plot = PAPRAnalyzer.plot_papr_ccdf_comparison(
    system.papr_values_ofdm,
    system.papr_values_sc_fdm
)
```

## Cambios en Archivos

### Nuevos Archivos
- `core/dft_precoding.py` - Módulo de precodificación DFT
- `tests/test_dft_precoding.py` - Tests para DFT
- `tests/test_papr_ccdf.py` - Tests para PAPR/CCDF
- `test_sc_fdm_integration.py` - Script de integración

### Archivos Modificados
- `core/modulator.py` - Soporte SC-FDM en OFDMModulator
- `core/ofdm_system.py` - Cálculo PAPR sin CP, almacenamiento PAPR
- `gui/main_window.py` - Switch SC-FDM, gráfica CCDF
- `utils/signal_processing.py` - Clase PAPRAnalyzer

## Notas Técnicas

### Normalización DFT

Se usa normalización 1/√M:
```python
DFT[k] = (1/√M) * Σ_{n=0}^{M-1} x[n] * exp(-j*2π*k*n/M)
```

Esto asegura que la energía se conserva (Teorema de Parseval):
```
Σ|x[n]|² = Σ|X[k]|²
```

### Tamaño M de DFT

M = número de subportadoras de datos (sin pilotos, DC, guardias)

Para configuración LTE estándar (5 MHz, N=512):
- Datos: ~249 subportadoras
- Pilotos: ~41 subportadoras
- DC + guardias: ~222 subportadoras
- **M = 249**

### Modo SC-FDM vs OFDM

El switch dinámico permite:
1. Comparar rendimiento BER en el mismo canal
2. Analizar reducción de PAPR
3. Verificar compatibilidad de formato

Internamente:
- `enable_sc_fdm=True`: Aplica DFT antes de mapeo
- `enable_sc_fdm=False`: Mapeo directo sin DFT (OFDM estándar)

## Compatibilidad

- ✓ Python 3.11+
- ✓ NumPy, SciPy, Matplotlib
- ✓ PyQt6
- ✓ Todos los esquemas de modulación (QPSK, 16-QAM, 64-QAM)
- ✓ Todos los anchos de banda (1.25, 2.5, 5, 10, 15, 20 MHz)
- ✓ Canales AWGN y Rayleigh
- ✓ Transmisión de imágenes

## Referencias

1. 3GPP TS 36.211 - Physical Channels and Modulation (LTE Uplink)
2. "Single Carrier FDMA for Uplink Wireless Transmission" - Myung, H. G. et al.
3. "PAPR Reduction in OFDM and OFDMA Systems" - Jiang, T. & Wu, Y.
