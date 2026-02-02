# UAV 5G NR Analysis GUI - Documentación Detallada de Módulos

## Descripción General del Sistema

La GUI implementa un sistema completo de análisis UAV 5G NR utilizando **Sionna** de NVIDIA para simulaciones de comunicaciones realistas. El sistema está dividido en **5 fases de análisis** que representan aspectos fundamentales de las comunicaciones UAV.

### Escenario Base: Munich 3D Urban
- **Ubicación**: Munich urbano con 6 edificios realistas
- **gNB**: Posicionado sobre edificio más alto [300, 200, 50]m
- **Frecuencia**: 3.5 GHz (banda 5G NR)
- **Ancho de banda**: 100 MHz
- **Ray Tracing**: Implementado con Sionna RT para propagación realista

---

## FASE 1: MIMO Masivo + Beamforming

### 📡 **¿Qué hace este botón?**
Analiza el rendimiento de diferentes configuraciones de antenas MIMO masivo y estrategias de beamforming para optimizar la capacidad del enlace gNB↔UAV.

### 🔧 **Uso de Sionna**
- **NO usa Sionna directamente** - Implementa modelos teóricos MIMO
- Calcula capacidad Shannon para diferentes configuraciones de arrays
- Evalúa ganancia de beamforming con modelos analíticos
- Simula throughput con SNR variable

### 🚁 **Definición de UAVs**
- **UAV Principal**: Receptor MIMO con arrays configurables (1x1 hasta 16x8)
- **Posición Fija**: [100, 100, 100]m para análisis consistente
- **Antennas UAV**: Desde 1 hasta 8 elementos según configuración

### 🔄 **Flujo de Simulación**
1. **Configuraciones MIMO**: Evalúa 6 configuraciones (1x1, 2x2, 4x4, 8x4, 8x8, 16x8)
2. **Estrategias Beamforming**: 6 técnicas (Omnidirectional, Fixed Beam, MRT, ZF, MMSE, SVD)
3. **Rango SNR**: -10 a +30 dB (21 puntos)
4. **Cálculo Capacidad**: Shannon C = log₂(1 + SNR_effective)
5. **Array Gain**: √(Nt × Nr) donde Nt=antenas TX, Nr=antenas RX

### 📊 **Qué Calcula**
- **Throughput máximo** por configuración MIMO
- **Espectral Efficiency** (bps/Hz)
- **Ganancia de Array** en dB
- **Comparación beamforming** con diferentes técnicas
- **SNR vs Throughput** curves

### 📈 **Gráficas que Devuelve**
1. **Subplot 1**: Throughput vs SNR para configuraciones MIMO
2. **Subplot 2**: Ganancia Beamforming por técnica (barras)
3. **Subplot 3**: Comparación capacidad espectral
4. **Subplot 4**: Visualización 3D del escenario con UAV y gNB

**Resultado típico**: 8,373 Mbps máximo con configuración 16x8 + SVD beamforming

---

## FASE 2: Análisis de Altura

### 📏 **¿Qué hace este botón?**
Determina la altura óptima de vuelo del UAV analizando el throughput en función de la altitud, considerando efectos de path loss y probabilidad LoS/NLoS.

### 🔧 **Uso de Sionna**
- **Utiliza Sionna RT** para ray tracing 3D
- Calcula paths de propagación con diferentes alturas
- Modela reflexiones y obstrucciones de edificios
- Evalúa condiciones LoS/NLoS dinámicamente

### 🚁 **Definición de UAVs**
- **UAV de Análisis**: Posición horizontal fija [100, 100, variable_height]
- **Rango de Alturas**: 20m a 200m (19 puntos)
- **Array**: 4 antenas (2x2 configuración)

### 🔄 **Flujo de Simulación**
1. **Loop por alturas**: 20, 30, 40... hasta 200m
2. **Para cada altura**:
   - Mueve UAV a nueva posición
   - Ejecuta ray tracing con Sionna
   - Calcula paths de propagación (max depth=5)
   - Determina channel response
   - Evalúa métricas de throughput
3. **SNR fijo**: 20dB para ver efectos del canal claramente
4. **Análisis estadístico**: Encuentra altura con máximo throughput

### 📊 **Qué Calcula**
- **Throughput vs altura** (Mbps)
- **Path Loss** en función de altitud
- **Probabilidad LoS** según modelo ITU-R
- **Spectral Efficiency** por altura
- **Distancia 3D** gNB↔UAV

### 📈 **Gráficas que Devuelve**
1. **Gráfico principal**: Throughput vs Altura con marcador de óptimo
2. **Escena 3D**: Visualización trayectoria vertical del UAV
3. **Path loss curve**: Pérdidas vs altura
4. **Edificios Munich**: Contexto urbano 3D

**Resultado típico**: Altura óptima 40-50m con ~1,998 Mbps

---

## FASE 3: Análisis de Cobertura

### 🗺️ **¿Qué hace este botón?**
Genera mapas de cobertura 2D analizando el throughput en diferentes posiciones horizontales con altura óptima fija (de Fase 2).

### 🔧 **Uso de Sionna**
- **Modelos analíticos** principalmente
- Path loss urbano con efectos de edificios
- LoS/NLoS probabilístico según distancia y obstáculos
- MIMO gains aplicados por posición

### 🚁 **Definición de UAVs**
- **Grid de posiciones**: 12x12 = 144 puntos de análisis
- **Área de cobertura**: ±250m desde gNB
- **Altura fija**: 40m (resultado de Fase 2)
- **Array**: 4 antenas por UAV

### 🔄 **Flujo de Simulación**
1. **Grid generation**: 144 posiciones (x,y) uniformemente distribuidas
2. **Para cada posición**:
   - Calcula distancia 3D al gNB
   - Evalúa path loss urbano (ITU-R)
   - Determina probabilidad LoS
   - Aplica shadowing effects
   - Considera bloqueo por edificios
   - Calcula throughput resultante
3. **Estadísticas**: Promedio, máximo, mínimo de cobertura

### 📊 **Qué Calcula**
- **Throughput map** 2D (Mbps por posición)
- **Path loss heatmap** 
- **LoS probability map**
- **Coverage statistics** (promedio, percentiles)
- **Área efectiva** de cobertura

### 📈 **Gráficas que Devuelve**
1. **Heatmap throughput**: Mapa de colores con throughput por posición
2. **Path loss map**: Mapa de pérdidas de propagación
3. **LoS/NLoS regions**: Zonas con línea de vista
4. **Estadísticas**: Tabla con métricas de cobertura

**Resultado típico**: 1,365 Mbps promedio en área de 0.2 km²

---

## FASE 4: Análisis de Movilidad

### 🛸 **¿Qué hace este botón?**
Evalúa diferentes patrones de trayectoria del UAV para determinar el patrón de movimiento que maximiza el throughput promedio durante la misión.

### 🔧 **Uso de Sionna**
- **Simulación temporal** con Sionna RT
- Ray tracing dinámico por cada posición de trayectoria
- Channel response variable en el tiempo
- Efectos Doppler considerados

### 🚁 **Definición de UAVs**
- **UAV dinámico**: Sigue trayectorias predefinidas
- **6 patrones**: Circular, lineal, espiral, figura-8, random, optimizada
- **Tiempo simulación**: 60 segundos con 120 steps (0.5s resolución)
- **Velocidad máxima**: 15 m/s

### 🔄 **Flujo de Simulación**
1. **Generación trayectorias**: 6 patrones matemáticamente definidos
2. **Para cada patrón**:
   - Genera 120 posiciones temporales
   - Para cada posición: ejecuta ray tracing
   - Calcula throughput instantáneo
   - Evalúa stability metrics
3. **Optimización**: Algoritmo genético para trayectoria óptima
4. **Comparación**: Ranking de patrones por performance

### 📊 **Qué Calcula**
- **Throughput promedio** por trayectoria
- **Estabilidad** (varianza del throughput)
- **Distancia total** recorrida
- **Eficiencia energética** (Mbps/meter)
- **Coverage completeness** (área visitada)

### 📈 **Gráficas que Devuelve**
1. **Trayectorias 3D**: 6 patrones en espacio 3D con throughput
2. **Throughput temporal**: Series de tiempo por patrón
3. **Comparación performance**: Barras por patrón
4. **Mapa de calor**: Throughput vs posición para mejor patrón

**Resultado típico**: Trayectoria optimizada 1,649 Mbps promedio

---

## FASE 5: Análisis de Interferencia

### 📡 **¿Qué hace este botón?**
Analiza escenarios multi-UAV evaluando interferencia entre usuarios, optimización SINR y capacity con múltiples UAVs simultáneos.

### 🔧 **Uso de Sionna**
- **Multi-user MIMO** con Sionna
- **Interference modeling** entre UAVs
- **Resource allocation** optimization
- **SINR calculations** con interferencia realista

### 🚁 **Definición de UAVs**
- **Hasta 8 UAVs simultáneos** en diferentes escenarios
- **5 escenarios**: Baja densidad (3), Media (5), Alta (8), Agrupados (6), Distribuidos (7)
- **Separación mínima**: 50m entre UAVs
- **Altura fija**: 40m para todos

### 🔄 **Flujo de Simulación**
1. **Para cada escenario de interferencia**:
   - Genera posiciones UAV (evitando colisiones)
   - Calcula matriz de distancias UAV↔UAV
   - Evalúa interferencia co-canal
   - Aplica power control algorithms
2. **SINR calculation**: Por cada UAV considerando interferencia de otros
3. **Resource allocation**: Distribución óptima de Resource Blocks
4. **Throughput multi-user**: Capacidad total del sistema

### 📊 **Qué Calcula**
- **SINR promedio** por UAV en cada escenario
- **Throughput total** del sistema multi-UAV
- **Interference matrix** entre todos los UAVs
- **Resource efficiency** (Mbps por RB)
- **System capacity** con diferentes densidades

### 📈 **Gráficas que Devuelve**
1. **SINR heatmap**: Matriz de interferencia UAV vs UAV
2. **Throughput comparison**: Barras por escenario de densidad
3. **3D UAV positions**: Posiciones de UAVs con SINR color-coding
4. **Performance vs density**: Curva capacidad vs número de UAVs

**Resultado típico**: 166.5 Mbps/UAV en escenario de baja densidad

---

## Utilización de Sionna por Módulo

| Módulo | Sionna RT | Sionna Channel | Sionna MIMO | Observaciones |
|--------|-----------|----------------|-------------|---------------|
| **MIMO** | ❌ | ❌ | ❌ | Modelos teóricos analíticos |
| **Height** | ✅ | ✅ | ❌ | Ray tracing completo 3D |
| **Coverage** | ⚠️ | ⚠️ | ❌ | Modelos híbridos |
| **Mobility** | ✅ | ✅ | ⚠️ | RT temporal dinámico |
| **Interference** | ✅ | ✅ | ✅ | Sistema multi-usuario completo |

## Configuración Técnica Global

### Sistema RF
- **Frecuencia**: 3.5 GHz (5G NR n78)
- **Ancho de banda**: 100 MHz
- **Potencia gNB**: 43 dBm
- **Noise Figure**: 7 dB
- **Resource Blocks**: 273 (subcarrier spacing 30 kHz)

### Arrays de Antenas
- **gNB**: 16×4 = 64 elementos (dual-pol)
- **UAV**: 2×2 = 4 elementos (single-pol)
- **Espaciado**: 0.5λ (42.8 mm @ 3.5 GHz)

### Escenario Munich
- **Área total**: 400×400m
- **Edificios**: 6 estructuras (20-45m altura)
- **gNB altura**: 50m (sobre edificio de 45m)
- **Propagación**: LoS/NLoS con ray tracing

Este sistema proporciona un análisis completo y realista de comunicaciones UAV 5G NR desde capacidad MIMO hasta optimización multi-usuario.