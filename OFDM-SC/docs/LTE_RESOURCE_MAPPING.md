# Mapeo de Recursos LTE - Documentación Técnica

## Tabla de Contenidos

1. [Introducción](#introducción)
2. [Estructura de Recursos LTE](#estructura-de-recursos-lte)
3. [Arquitectura del Sistema](#arquitectura-del-sistema)
4. [Detalles de Implementación](#detalles-de-implementación)
5. [Matemática Subyacente](#matemática-subyacente)
6. [Ejemplos de Uso](#ejemplos-de-uso)
7. [Futuras Extensiones](#futuras-extensiones)

---

## Introducción

Este documento detalla la implementación de mapeo de subportadoras siguiendo el estándar LTE 3GPP TS 36.211. 

### ¿Por qué LTE?

En comunicaciones multipath (realistas):
1. **Simple mapping** (secuencial) no proporciona pilotos conocidos
2. Sin pilotos, el receptor no puede estimar el canal
3. Sin estimación, no hay equalizacion efectiva
4. Resultado: Alto BER en canales complejos

**Solución LTE**: Enviar símbolos conocidos (pilotos) en posiciones fijas → receptor puede estimar canal → mejorar BER

---

## Estructura de Recursos LTE

### Grid de Subportadoras

En una símbolo OFDM con N=512 FFT:

```
Índice:    0...105  |  106...256...405  |  406...511
Tipo:      Guard    |  Útil + DC        |  Guard
Cantidad:  106      |  300 (incl DC)    |  106
```

### Distribución Detallada (300 subportadoras útiles)

```python
# Configuración estándar para 5 MHz
N = 512                          # FFT size
Nc = 300                         # Subportadoras útiles

# Guardias (simétricas)
num_guard_left = (512 - 300) // 2   = 106
num_guard_right = 512 - 300 - 106   = 106

# DC
dc_index = 512 // 2              = 256

# Dentro de útiles (106 a 405)
pilot_spacing = 6                # LTE estándar
# Pilotos en: 111, 117, 123, ..., 399 (cada 6)
# Total pilotos: 300 / 6 = 50

# Datos: 299 - 50 = 249 (todas excepto pilotos)
```

### Mapeo Visual

```
Freqency (subcarriers):
┌──────────────┬──────────────────────────┬──────────────┐
│ Guard (106)  │      Útiles (300)        │ Guard (106)  │
├──────────────┼──────────────────────────┼──────────────┤
│   [0-105]    │    [106-256-405]         │  [406-511]   │
│     0 dB     │  DC  Pilotos Datos       │    0 dB      │
│              │    (1)  (50)   (249)     │              │
└──────────────┴──────────────────────────┴──────────────┘
               ↑                          ↑
            f=0 (start)              f=N-1 (end)
```

### Patron de Pilotos

En rango útil [106, 405]:

```
Posición relativa:  0   1   2   3   4   5   6   7   8   9...
Tipo:              D   D   D   P   D   D   D   P   D   D...
                      (P = Pilot cada 6)

Índices LTE:
111 (106+5), 117, 123, 129, ..., 399
```

---

## Arquitectura del Sistema

### Diagrama de Flujo - Transmisor OFDM

```
Input Bits
    ↓
┌─────────────────────┐
│   QAM Modulator     │  (Bits → QAM symbols)
└────────┬────────────┘
         ↓
      QAM Symbols (249 máx para 5MHz)
         ↓
┌─────────────────────────────────────────┐
│      ResourceMapper (NUEVO)              │
│  ─────────────────────────────────────  │
│  1. Añade pilotos conocidos (50)        │
│  2. Null en DC (1)                      │
│  3. Null en guardias (212)               │
│  4. Datos en posiciones restantes (249) │
└────────┬────────────────────────────────┘
         ↓
    Grid 512 muestras
    (249 datos + 50 pilotos + 1 DC + 212 guardias)
         ↓
┌─────────────────────┐
│   IFFT (512)        │
└────────┬────────────┘
         ↓
   Muestras tiempo
         ↓
┌─────────────────────┐
│   Añadir CP         │
└────────┬────────────┘
         ↓
    Señal OFDM (576 muestras)
```

### Clase LTEResourceGrid

```python
class LTEResourceGrid:
    """
    Gestiona clasificación de subportadoras
    
    Atributos:
        N: Tamaño FFT
        Nc: Subportadoras útiles
        dc_index: Índice DC (N/2)
        pilot_spacing: Espaciado pilotos (6)
        subcarrier_types: Dict k → tipo ('data'|'pilot'|'dc'|'guard')
    """
    
    def get_subcarrier_type(k) → str
    def get_data_indices() → ndarray
    def get_pilot_indices() → ndarray
    def get_guard_indices() → ndarray
    def get_statistics() → Dict
```

**Ejemplo**:
```python
grid = LTEResourceGrid(N=512, Nc=300)

# Clasificación
grid.get_subcarrier_type(256)        # 'dc'
grid.get_subcarrier_type(111)        # 'pilot'
grid.get_subcarrier_type(150)        # 'data'
grid.get_subcarrier_type(50)         # 'guard'

# Estadísticas
stats = grid.get_statistics()
# {
#   'total_subcarriers': 512,
#   'useful_subcarriers': 300,
#   'data_subcarriers': 249,
#   'pilot_subcarriers': 50,
#   'guard_subcarriers': 212,
#   'dc_subcarriers': 1,
# }
```

### Clase PilotPattern

```python
class PilotPattern:
    """
    Genera pilotos determinísticos para estimación de canal
    
    Características:
    - Determinista: mismo cell_id → mismos pilotos
    - QPSK: (1+1j)/√2 (potencia unitaria)
    - PN sequence: basado en cell_id
    """
    
    def generate_pilots(num_pilots) → ndarray
```

**Ejemplo**:
```python
pilot_gen = PilotPattern(cell_id=0)
pilots = pilot_gen.generate_pilots(50)  # Array de 50 símbolos QPSK

# Mismo cell_id → mismos pilotos (reproducible)
pilot_gen2 = PilotPattern(cell_id=0)
pilots2 = pilot_gen2.generate_pilots(50)
assert np.allclose(pilots, pilots2)  # ✓
```

### Clase ResourceMapper

```python
class ResourceMapper:
    """
    Mapea símbolos QAM a grid LTE
    
    Proceso:
    1. Crea grid de 512 complejos (ceros)
    2. Coloca datos en índices de datos
    3. Coloca pilotos en índices de pilotos
    4. Deja DC y guardias en cero
    5. Retorna grid + info de mapeo
    """
    
    def map_symbols(data_symbols) → (grid, mapping_info)
    def extract_pilots() → pilots
    def get_statistics() → Dict
```

**Ejemplo**:
```python
mapper = ResourceMapper(config)

# 249 símbolos QAM de datos
data_symbols = np.random.randn(249) + 1j*np.random.randn(249)

# Mapear a grid LTE
grid, mapping_info = mapper.map_symbols(data_symbols)

# grid: 512 muestras (datos + pilotos + zeros)
# mapping_info: {'data_indices': [...], 'pilot_indices': [...], ...}

# Extraer información para receptor
pilots = grid[mapping_info['pilot_indices']]
data_locations = mapping_info['data_indices']
```

---

## Detalles de Implementación

### 1. Inicialización de Tipos de Subportadora

```python
def _init_subcarrier_types(self):
    self.subcarrier_types = {}
    
    for k in range(self.N):
        if k < num_guard_left or k >= N - num_guard_right:
            # Guardias en extremos
            self.subcarrier_types[k] = 'guard'
        elif k == dc_index:
            # DC en centro
            self.subcarrier_types[k] = 'dc'
        else:
            # Dentro de útiles
            relative_pos = k - num_guard_left
            if relative_pos % pilot_spacing == pilot_spacing // 2:
                self.subcarrier_types[k] = 'pilot'
            else:
                self.subcarrier_types[k] = 'data'
```

**Lógica de Pilotos**:
- Espaciado: cada 6 subportadoras
- Offset: pilot_spacing // 2 = 3
- Primeros 3 útiles (106-108): datos
- Subportadora 109: piloto (106 + 3)
- Siguientes 3 útiles (110-112): datos
- Subportadora 113: piloto (109 + 6)
- Etc.

### 2. Mapeo de Símbolos

```python
def map_symbols(self, data_symbols):
    # Crear grid vacía (complejos)
    grid = np.zeros(self.N, dtype=complex)
    
    # Obtener índices
    data_idx = self.grid.get_data_indices()
    pilot_idx = self.grid.get_pilot_indices()
    
    # Mapear datos
    grid[data_idx] = data_symbols[:len(data_idx)]
    
    # Mapear pilotos
    pilots = self.pilot_pattern.generate_pilots(len(pilot_idx))
    grid[pilot_idx] = pilots
    
    # DC y guardias ya están en cero (inicialización)
    
    return grid, mapping_info
```

**Garantías**:
- ✓ DC siempre es 0
- ✓ Guardias siempre son 0
- ✓ Pilotos conocidos y determinísticos
- ✓ No hay solapamiento entre tipos

### 3. Generación de Pilotos (PN Sequence)

```python
def generate_pilots(self, num_pilots):
    """Genera secuencia PN basada en cell_id"""
    
    # Seed determinístico
    np.random.seed(self.cell_id)
    
    # Genera PN sequence (valores reales entre -1 y 1)
    pn_sequence = np.random.randn(num_pilots)
    
    # Normalizar a QPSK
    pn_sequence = (pn_sequence > 0).astype(float) * 2 - 1  # ±1
    
    # Combinar I+jQ para QPSK normalizado
    pn_q = np.random.randn(num_pilots)
    pn_q = (pn_q > 0).astype(float) * 2 - 1
    
    pilots = (pn_sequence + 1j * pn_q) / np.sqrt(2)
    
    return pilots
```

---

## Matemática Subyacente

### OFDM Transmission (Sin Mapeo LTE)

```
Señal transmitida:
x(t) = Σ(k=0 to N-1) X[k] exp(j2πk∆f·t)

Donde:
- X[k]: símbolo en subportadora k
- ∆f: espaciado de subportadoras
- t: tiempo
```

### Con Mapeo LTE (Receptor - Futuro)

```
Estimación de canal (con pilotos):
H_est[k] = Y_pilot[k] / S_pilot[k]

Donde:
- Y_pilot[k]: símbolo recibido en piloto k
- S_pilot[k]: símbolo transmitido (conocido)
- H_est[k]: estimación respuesta frecuencial en piloto

Equalizacion (Zero Forcing):
X̂[k] = Y[k] / H_est[k]
```

### Overhead de Pilotos

```
Overhead = num_pilotos / num_datos
         = 50 / 249
         ≈ 20%  (aceptable en LTE)

Nota: En LTE real, multipath con múltiples antenas
reduce overhead mediante técnicas avanzadas
```

---

## Ejemplos de Uso

### Uso Básico

```python
from core.modulator import OFDMModulator
from config.lte_params import LTEConfig

# Configurar
config = LTEConfig()  # 5 MHz, 300 subcarriers, etc.
modulator = OFDMModulator(config, mode='lte')

# Datos: 100 bits
bits = np.random.randint(0, 2, 100)

# Modular
signal, qam_symbols, mapping_info = modulator.modulate(bits)

# mapping_info contiene:
# - data_indices: índices de subportadoras con datos
# - pilot_indices: índices de subportadoras con pilotos
# - guard_indices: índices de guardias
# - stats: estadísticas del mapeo
```

### Stream Completo

```python
# Modular múltiples símbolos OFDM
bits_stream = np.random.randint(0, 2, 1000)
num_ofdm = 5  # 5 símbolos OFDM

signal_stream, symbols_list, mapping_infos = \
    modulator.modulate_stream(bits_stream, num_ofdm)

# signal_stream: señal concatenada de 5 símbolos
# symbols_list: lista de arrays QAM (uno por símbolo)
# mapping_infos: lista de mappings (uno por símbolo)

for i, mapping_info in enumerate(mapping_infos):
    print(f"Símbolo {i}:")
    print(f"  Datos: {len(mapping_info['data_indices'])}")
    print(f"  Pilotos: {len(mapping_info['pilot_indices'])}")
```

### Acceso a Información de Mapeo

```python
# En receptor (futuro)
signal_rx, _ = channel.transmit(signal)  # Pasar por canal
received_grid = np.fft.fft(signal_rx[:512])  # FFT

# Extraer pilotos recibidos
pilot_idx = mapping_info['pilot_indices']
pilot_rx = received_grid[pilot_idx]
pilot_tx = modulator.resource_mapper.pilot_pattern.generate_pilots(50)

# Estimar canal en posiciones de pilotos
H_est_pilots = pilot_rx / pilot_tx

# Interpolar a todas las subportadoras
# (futuro: implementar interpolation)
```

---

## Futuras Extensiones

### 1. Estimación de Canal (Receiver)

```python
class ChannelEstimator:
    """Estima respuesta frecuencial usando pilotos"""
    
    def estimate_lte(self, received_signal, mapping_info):
        """
        Extrae pilotos → estima H[k] en posiciones piloto
        Interpola a otras subportadoras
        """
        pass
```

**Algoritmos**:
- LS (Least Squares): H[k] = Y_pilot[k] / S_pilot[k]
- MMSE: incluye correlación entre subportadoras
- Interpolación linear/cubic entre pilotos

### 2. Ecualización Adaptativa

```python
class LTEEqualizer:
    """Ecualiza datos usando estimación de canal"""
    
    def zero_forcing(self, received_grid, H_est):
        """X̂ = Y / H_est"""
        pass
    
    def mmse(self, received_grid, H_est, snr):
        """MMSE equalizer (optimal)"""
        pass
```

### 3. Sincronización Temporal

```
Usar pilotos para:
- Detectar inicio de símbolo OFDM
- Rastrear timing drift
- Compensar offset de frecuencia
```

### 4. Múltiples Antenas (MIMO)

```
Estructura MIMO-LTE:
- Pilotos transmitidos en diferentes ports
- Estimación de canal por puerto
- Detector MIMO (v-BLAST, etc.)
```

### 5. Adaptación de Parámetros

```python
config = LTEConfig(
    bandwidth='10MHz',      # 600 subcarriers
    cell_id=1,              # Afecta patrón de pilotos
    subframe_config='FDD',  # FDD vs TDD
    cp_type='normal'        # Normal vs extended
)
```

---

## Verificación y Validación

### Test Suite Ejecutado

```bash
$ pytest tests/test_resource_mapper.py -v
# 20 tests, 20 passed ✓

$ pytest tests/test_integration_lte.py -v
# 10 tests, 10 passed ✓

Total: 30/30 tests PASSED
```

### Validaciones Implementadas

| Aspecto | Test | Estado |
|---------|------|--------|
| DC en centro | test_dc_in_center | ✓ |
| Guardias simétricas | test_guard_bands_symmetric | ✓ |
| Pilotos cada 6 | test_pilot_spacing | ✓ |
| Sin solapamiento | test_no_overlap_between_types | ✓ |
| BW 5MHz (300 SC) | test_lte_bandwidth_5mhz | ✓ |
| Overhead pilotos | test_lte_pilot_overhead | ✓ |
| Modulación LTE | test_modulate_lte_returns_mapping_info | ✓ |

---

## Referencias

1. **3GPP TS 36.211** - E-UTRA Physical Channels and Modulation
2. **3GPP TS 36.212** - E-UTRA Multiplexing and channel coding
3. **3GPP TS 36.213** - E-UTRA Physical layer procedures
4. **Proakis & Manolakis** - Digital Signal Processing (4th ed.)
5. **Sesia et al.** - LTE, The UMTS Long Term Evolution (2nd ed.)

---

**Documento**: Técnico - Mapeo de Recursos LTE v2.0
**Fecha**: Diciembre 2024
**Estado**: ✅ Completado y Validado
**Próximo Paso**: Implementación de Receiver (Estimación de Canal)
