# Mobility Analysis - Scenario Configurations

## Dos Escenarios Disponibles

### ESCENARIO 1: RUTAS CON DESTINOS DIFERENTES (Default)
**Pregunta**: "¿Cuál es la mejor ruta entre dos destinos distintos?"

**Configuración:**
- Route A: [50, 150, 35] → [250, 100, 60] (distancia 237.9m)
- Route B: [50, 150, 35] → [100, 300, 50] (distancia 183.3m)
- Punto de inicio: MISMO
- Destino: DIFERENTE

**Resultado Actual:**
- Route A: 375.4 Mbps (menos óptima)
- Route B: 399.5 Mbps ✅ **MEJOR**

**Cómo ejecutar:**
```bash
python mobility.py
```

O explícitamente:
```python
mobility.generate_routes(num_points=20, route_style="curved", scenario="default")
```

---

### ESCENARIO 2: RUTAS AL MISMO DESTINO (NEW!)
**Pregunta**: "¿Cuál es la mejor ruta para llegar al MISMO destino?"

**Configuración:**
- Route A: [80, 100, 35] → [280, 150, 55] (curva a la IZQUIERDA)
- Route B: [80, 100, 35] → [280, 150, 55] (curva a la DERECHA)
- Punto de inicio: MISMO
- Destino: IDÉNTICO
- Rutas: Caminos diferentes (rodean por lados opuestos)

**Ventajas:**
- Comparación pura de caminos alternativos
- Mismo punto inicio/fin = mismo "viaje"
- Simula decisión de ruta: "¿Por dónde es mejor ir?"
- Rutas más largas = más datos de comparación

**Cómo ejecutar:**
```bash
cd /home/dariox/Moviles/moviles/final/testsrt
/home/dariox/Moviles/moviles/final/.venv/bin/python mobility.py
```

**Luego edita `mobility.py` línea ~726:**

**ANTES:**
```python
mobility.generate_routes(num_points=20)
```

**DESPUÉS:**
```python
mobility.generate_routes(num_points=20, scenario="best_route")
```

---

## Personalizar Escenarios

### Modificar coordenadas (archivo mobility.py):

**ScenarioConfig (línea 61-67):**
```python
class ScenarioConfig:
    """Rutas con destinos diferentes"""
    GNB_POSITION = [110, 70, 20]
    ROUTE_A_START = [50, 150, 35]
    ROUTE_A_END = [250, 100, 60]      # ← CAMBIAR DESTINO A
    ROUTE_B_START = [50, 150, 35]
    ROUTE_B_END = [100, 300, 50]      # ← CAMBIAR DESTINO B
```

**ScenarioConfig_BestRoute (línea 69-80):**
```python
class ScenarioConfig_BestRoute:
    """Rutas al mismo destino"""
    GNB_POSITION = [110, 70, 20]
    ROUTE_A_START = [80, 100, 35]     # ← CAMBIAR INICIO
    ROUTE_A_END = [280, 150, 55]      # ← CAMBIAR DESTINO COMÚN
    ROUTE_B_START = [80, 100, 35]     # ← DEBE SER IGUAL A ROUTE_A_START
    ROUTE_B_END = [280, 150, 55]      # ← DEBE SER IGUAL A ROUTE_A_END
```

---

## Estilos de Rutas

Además del escenario, puedes cambiar el **estilo de la trayectoria:**

```python
mobility.generate_routes(num_points=20, route_style="curved", scenario="default")
```

### Opciones:
1. **"curved"** (default) - Arco suave, realista
2. **"spiral"** - Espiral descendente
3. **"direct"** - Línea recta

---

## Archivos Generados

- `mobility_comparison_analysis.png` - Gráficos: Throughput, SNR, Path Loss, resumen
- `mobility_3d_renders.png` - Renderizado 3D de ambas rutas (vista superior)

---

## Flujo de Trabajo Recomendado

### 1. Prueba con rutas diferentes (default):
```bash
python mobility.py
```
Resultado: Comparar qué destino es mejor

### 2. Prueba con mismo destino:
Edita línea 726 de mobility.py:
```python
mobility.generate_routes(num_points=20, scenario="best_route")
```
Ejecuta:
```bash
python mobility.py
```
Resultado: "Para llegar a [280, 150, 55], ¿cuál camino es mejor?"

### 3. Personaliza tus propias rutas:
Edita ScenarioConfig o ScenarioConfig_BestRoute con tus coordenadas

---

## Interpretación de Resultados

**En ESCENARIO 1 (destinos diferentes):**
- Ruta más corta ≠ mejor throughput
- Diferencia en Signal Propagation por geometría

**En ESCENARIO 2 (mismo destino):**
- Ambas rutas llegan al mismo punto
- Diferencia = impacto puro del camino elegido
- Conclusión clara: "La mejor ruta es Route A/B porque..."

