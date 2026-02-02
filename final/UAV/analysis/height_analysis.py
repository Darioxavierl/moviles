"""
Height Analysis - Análisis de Throughput vs Altura UAV
Analiza el desempeño del sistema UAV a diferentes alturas (50-200m)
"""
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt
import sys
import os

# Importar configuraciones y sistema
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.system_config import *
from systems.basic_system import BasicUAVSystem

class HeightAnalysis:
    """
    Análisis completo de throughput vs altura UAV
    Genera métricas y visualizaciones del impacto de la altura en el desempeño
    """
    
    def __init__(self, height_range=None, fixed_snr_db=20):
        """
        Inicializar análisis de altura
        
        Args:
            height_range: Lista de alturas a analizar [m]
            fixed_snr_db: SNR fijo para análisis de canal
        """
        self.height_range = height_range or ScenarioConfig.HEIGHT_RANGE
        self.fixed_snr_db = fixed_snr_db
        
        print("="*70)
        print("ANÁLISIS DE ALTURA UAV - THROUGHPUT vs ALTURA")
        print("="*70)
        
        # Create basic system
        print("🔧 Inicializando sistema UAV...")
        self.system = BasicUAVSystem()
        
        print(f"📈 Rango de alturas: {min(self.height_range)} - {max(self.height_range)} m")
        print(f"📡 SNR fijo: {fixed_snr_db} dB")
        
        # Storage for results
        self.results = None
    
    def run_height_sweep(self):
        """Ejecutar sweep completo de alturas"""
        print(f"\n🚁 INICIANDO SWEEP DE ALTURAS...")
        
        # Run the height analysis using the system's method
        self.results = self.system.simulate_height_analysis(self.height_range)
        
        print(f"✅ Sweep completado para {len(self.height_range)} alturas")
        
        return self.results
    
    def analyze_results(self):
        """Analizar resultados y extraer insights"""
        if self.results is None:
            print("❌ No hay resultados. Ejecute run_height_sweep() primero.")
            return None
        
        print(f"\n📊 ANÁLISIS DE RESULTADOS:")
        
        # Find optimal height
        max_idx = np.argmax(self.results['throughput_mbps'])
        optimal_height = self.results['heights'][max_idx]
        max_throughput = self.results['throughput_mbps'][max_idx]
        
        # Calculate statistics
        avg_throughput = np.mean(self.results['throughput_mbps'])
        min_throughput = np.min(self.results['throughput_mbps'])
        
        # LoS statistics
        los_heights = np.array(self.height_range)[np.array(self.results['los_probability']) > 0.5]
        los_percentage = len(los_heights) / len(self.height_range) * 100
        
        analysis = {
            'optimal_height_m': optimal_height,
            'max_throughput_mbps': max_throughput,
            'avg_throughput_mbps': avg_throughput,
            'min_throughput_mbps': min_throughput,
            'throughput_range_mbps': max_throughput - min_throughput,
            'los_percentage': los_percentage,
            'los_heights': los_heights.tolist() if len(los_heights) > 0 else [],
            'coverage_reliability': np.std(self.results['throughput_mbps']) / avg_throughput * 100  # CV%
        }
        
        # Print analysis
        print(f"  🎯 Altura óptima: {optimal_height} m")
        print(f"  📈 Throughput máximo: {max_throughput:.1f} Mbps")
        print(f"  📊 Throughput promedio: {avg_throughput:.1f} Mbps")
        print(f"  📉 Throughput mínimo: {min_throughput:.1f} Mbps")
        print(f"  🔄 Rango dinámico: {analysis['throughput_range_mbps']:.1f} Mbps")
        print(f"  👁️  LoS en {los_percentage:.1f}% de alturas")
        print(f"  📈 Variabilidad (CV): {analysis['coverage_reliability']:.1f}%")
        
        if len(los_heights) > 0:
            print(f"  ✅ Alturas con LoS: {los_heights}")
        else:
            print(f"  ⚠️  No se detectó LoS en ninguna altura")
        
        return analysis
    
    def plot_results(self, save_path="./UAV/outputs/height_analysis.png"):
        """Generar gráficos del análisis"""
        if self.results is None:
            print("❌ No hay resultados para graficar.")
            return
        
        print(f"\n📈 GENERANDO GRÁFICOS...")
        
        # Create output directory
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        # Main plot: Throughput vs Height
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        
        # Plot 1: Throughput vs Height (MAIN)
        ax1.plot(self.results['heights'], self.results['throughput_mbps'], 
                'b-o', linewidth=3, markersize=8, label='Throughput')
        ax1.set_xlabel('Altura UAV [m]', fontweight='bold')
        ax1.set_ylabel('Throughput [Mbps]', fontweight='bold')
        ax1.set_title('Throughput vs Altura UAV\n(gNB MIMO 64x4, UAV 4 antenas)', fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # Highlight optimal point
        max_idx = np.argmax(self.results['throughput_mbps'])
        ax1.scatter(self.results['heights'][max_idx], self.results['throughput_mbps'][max_idx],
                   color='red', s=150, zorder=5, label=f"Óptimo: {self.results['heights'][max_idx]}m")
        ax1.legend()
        
        # Plot 2: Path Loss vs Height
        ax2.plot(self.results['heights'], self.results['path_loss_db'], 
                'r-s', linewidth=2.5, markersize=6)
        ax2.set_xlabel('Altura UAV [m]', fontweight='bold')
        ax2.set_ylabel('Path Loss [dB]', fontweight='bold')
        ax2.set_title('Path Loss vs Altura', fontweight='bold')
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: LoS Probability vs Height
        ax3.plot(self.results['heights'], self.results['los_probability'], 
                'g-^', linewidth=2.5, markersize=6)
        ax3.set_xlabel('Altura UAV [m]', fontweight='bold')
        ax3.set_ylabel('Probabilidad LoS', fontweight='bold')
        ax3.set_title('Probabilidad LoS vs Altura', fontweight='bold')
        ax3.set_ylim([-0.1, 1.1])
        ax3.grid(True, alpha=0.3)
        
        # Plot 4: Spectral Efficiency vs Height
        ax4.plot(self.results['heights'], self.results['spectral_efficiency'], 
                'm-d', linewidth=2.5, markersize=6)
        ax4.set_xlabel('Altura UAV [m]', fontweight='bold')
        ax4.set_ylabel('Spectral Efficiency [bits/s/Hz]', fontweight='bold')
        ax4.set_title('Eficiencia Espectral vs Altura', fontweight='bold')
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=VisualizationConfig.DPI, bbox_inches='tight')
        
        print(f"✅ Gráfico guardado: {save_path}")
        
        return fig
    
    def save_results(self, data_path="./UAV/outputs/height_analysis_data.npz"):
        """Guardar resultados para análisis posterior"""
        if self.results is None:
            print("❌ No hay resultados para guardar.")
            return
        
        # Create output directory
        os.makedirs(os.path.dirname(data_path), exist_ok=True)
        
        # Save data
        np.savez(data_path, 
                heights=self.results['heights'],
                throughput_mbps=self.results['throughput_mbps'],
                path_loss_db=self.results['path_loss_db'],
                los_probability=self.results['los_probability'],
                spectral_efficiency=self.results['spectral_efficiency'],
                fixed_snr_db=self.fixed_snr_db)
        
        print(f"✅ Datos guardados: {data_path}")
    
    def generate_report(self):
        """Generar reporte completo del análisis"""
        if self.results is None:
            print("❌ Ejecute el análisis primero.")
            return
        
        analysis = self.analyze_results()
        
        print(f"\n" + "="*70)
        print("REPORTE DE ANÁLISIS DE ALTURA UAV")
        print("="*70)
        
        # Configuration
        info = self.system.get_system_info()
        print(f"\n📊 CONFIGURACIÓN:")
        print(f"  • Escenario: {info['scene']}")
        print(f"  • Frecuencia: {info['frequency_ghz'][0]} GHz")
        print(f"  • gNB: {info['gnb_antennas']} antenas @ {info['gnb_position']}")
        print(f"  • UAV: {info['uav_antennas']} antenas")
        print(f"  • Ancho de banda: {info['bandwidth_mhz']} MHz")
        print(f"  • SNR fijo: {self.fixed_snr_db} dB")
        
        # Results summary
        print(f"\n📈 RESULTADOS CLAVE:")
        print(f"  🎯 ALTURA ÓPTIMA: {analysis['optimal_height_m']} m")
        print(f"     → Throughput máximo: {analysis['max_throughput_mbps']:.1f} Mbps")
        print(f"  📊 Rango de desempeño:")
        print(f"     → Mejor altura: {analysis['max_throughput_mbps']:.1f} Mbps")
        print(f"     → Peor altura: {analysis['min_throughput_mbps']:.1f} Mbps")
        print(f"     → Variación: {analysis['throughput_range_mbps']:.1f} Mbps")
        print(f"  👁️  Condiciones de propagación:")
        print(f"     → LoS en {analysis['los_percentage']:.1f}% de alturas")
        print(f"     → Variabilidad: {analysis['coverage_reliability']:.1f}%")
        
        # Recommendations
        print(f"\n💡 RECOMENDACIONES:")
        if analysis['optimal_height_m'] <= 100:
            print(f"  ✅ Operar a baja altura ({analysis['optimal_height_m']}m) para máximo throughput")
        elif analysis['optimal_height_m'] <= 150:
            print(f"  ✅ Altura media ({analysis['optimal_height_m']}m) ofrece buen balance")
        else:
            print(f"  ⚠️  Alta altura ({analysis['optimal_height_m']}m) puede tener mayor cobertura pero menor throughput")
        
        if analysis['los_percentage'] > 80:
            print(f"  ✅ Excelente propagación LoS en la mayoría de alturas")
        elif analysis['los_percentage'] > 50:
            print(f"  ⚠️  Propagación mixta LoS/NLoS según altura")
        else:
            print(f"  ❌ Predomina propagación NLoS - considerar reposicionar gNB")
        
        if analysis['coverage_reliability'] < 20:
            print(f"  ✅ Desempeño consistente entre alturas")
        else:
            print(f"  ⚠️  Alta variabilidad - altura crítica para desempeño")
        
        print("="*70)

def run_height_analysis():
    """Ejecutar análisis completo de altura"""
    # Create and run analysis
    analysis = HeightAnalysis()
    
    # Run the sweep
    results = analysis.run_height_sweep()
    
    # Analyze results
    insights = analysis.analyze_results()
    
    # Generate plots
    analysis.plot_results()
    
    # Save data
    analysis.save_results()
    
    # Generate report
    analysis.generate_report()
    
    return analysis, results, insights

if __name__ == "__main__":
    analysis, results, insights = run_height_analysis()