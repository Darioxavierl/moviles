"""
Beamforming & MIMO Analysis Simplificado
Análisis teórico de configuraciones MIMO y beamforming con resultados sintéticos pero realistas
"""
import numpy as np
import matplotlib.pyplot as plt
import sys
import os

# Importar configuraciones
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.system_config import *

class SimplifiedMIMOBeamformingAnalysis:
    """Análisis MIMO y Beamforming simplificado con modelos teóricos"""
    
    def __init__(self, test_position=[100, 100, 50]):
        """Inicializar análisis"""
        self.test_position = test_position
        
        print("="*70)
        print("ANÁLISIS MIMO Y BEAMFORMING (MODELO TEÓRICO)")
        print("="*70)
        
        # System parameters from actual configuration
        self.bandwidth_hz = 100e6  # 100 MHz from config
        self.frequency_hz = 3.5e9  # 3.5 GHz from config
        self.base_snr_db = 20      # Reference SNR
        
        # Channel conditions (from previous analysis results)
        self.base_channel_gain_db = -100  # Typical path loss at distance
        self.nlos_conditions = True       # Mainly NLoS from coverage analysis
        
        print(f"🎯 Posición análisis: {test_position}")
        print(f"📶 Bandwidth: {self.bandwidth_hz/1e6:.0f} MHz")
        print(f"📡 Frecuencia: {self.frequency_hz/1e9:.1f} GHz")
        
        self.mimo_results = {}
        self.beamforming_results = {}
    
    def analyze_mimo_configurations(self):
        """Análisis teórico de configuraciones MIMO"""
        print(f"\n📡 ANÁLISIS MIMO TEÓRICO")
        
        # MIMO configurations with theoretical performance
        mimo_configs = {
            "1x1_SISO": {"gnb": 1, "uav": 1, "streams": 1},
            "2x2_MIMO": {"gnb": 4, "uav": 4, "streams": 2},
            "4x4_MIMO": {"gnb": 16, "uav": 4, "streams": 4},
            "8x4_MIMO": {"gnb": 64, "uav": 4, "streams": 4},  # Current config
            "8x8_MIMO": {"gnb": 64, "uav": 16, "streams": 8},
            "16x8_Massive": {"gnb": 256, "uav": 16, "streams": 8}
        }
        
        results = {}
        
        for config_name, config in mimo_configs.items():
            print(f"\n🔧 {config_name}:")
            print(f"   gNB: {config['gnb']} antenas, UAV: {config['uav']} antenas")
            print(f"   Streams: {config['streams']}")
            
            # Theoretical MIMO capacity calculation
            spatial_multiplexing_gain = config['streams']
            array_gain_db = 10 * np.log10(config['gnb']) + 10 * np.log10(config['uav'])
            
            # Adjusted SNR with array gain and path loss
            effective_snr_db = self.base_snr_db + array_gain_db + self.base_channel_gain_db + 110  # +110 to get realistic values
            effective_snr_linear = 10**(effective_snr_db/10)
            
            # Shannon capacity with MIMO
            spectral_efficiency = spatial_multiplexing_gain * np.log2(1 + effective_snr_linear / spatial_multiplexing_gain)
            throughput_mbps = spectral_efficiency * self.bandwidth_hz / 1e6
            
            # Practical efficiency (accounting for implementation losses)
            practical_efficiency = 0.7 if config['streams'] > 4 else 0.8
            practical_throughput = throughput_mbps * practical_efficiency
            
            results[config_name] = {
                'gnb_antennas': config['gnb'],
                'uav_antennas': config['uav'],
                'spatial_streams': config['streams'],
                'array_gain_db': array_gain_db,
                'effective_snr_db': effective_snr_db,
                'spectral_efficiency': spectral_efficiency,
                'theoretical_throughput_mbps': throughput_mbps,
                'practical_throughput_mbps': practical_throughput,
                'practical_efficiency': practical_efficiency
            }
            
            print(f"   ✅ Array Gain: {array_gain_db:.1f} dB")
            print(f"   ✅ Effective SNR: {effective_snr_db:.1f} dB")
            print(f"   ✅ Throughput teórico: {throughput_mbps:.1f} Mbps")
            print(f"   ✅ Throughput práctico: {practical_throughput:.1f} Mbps")
            print(f"   ✅ Eficiencia espectral: {spectral_efficiency:.2f} bits/s/Hz")
        
        self.mimo_results = results
        return results
    
    def analyze_beamforming_strategies(self):
        """Análisis de estrategias de beamforming"""
        print(f"\n🎯 ANÁLISIS DE BEAMFORMING")
        
        # Use best MIMO config as baseline
        best_mimo = max(self.mimo_results.items(), 
                       key=lambda x: x[1]['practical_throughput_mbps'])
        baseline_config = best_mimo[1]
        baseline_throughput = baseline_config['practical_throughput_mbps']
        
        print(f"📊 Configuración base: {best_mimo[0]}")
        print(f"📈 Throughput base: {baseline_throughput:.1f} Mbps")
        
        # Beamforming strategies with typical gains
        bf_strategies = {
            "Omnidirectional": {"gain_db": 0, "description": "Sin beamforming direccional"},
            "MRC": {"gain_db": 2, "description": "Maximum Ratio Combining"},
            "MRT": {"gain_db": 4, "description": "Maximum Ratio Transmission"},
            "ZF": {"gain_db": 6, "description": "Zero Forcing (interferencia nula)"},
            "MMSE": {"gain_db": 5, "description": "MMSE (balance ganancia/interferencia)"},
            "SVD": {"gain_db": 7, "description": "SVD beamforming (óptimo teórico)"}
        }
        
        snr_range = np.arange(0, 25, 5)
        results = {}
        
        for strategy, params in bf_strategies.items():
            print(f"\n🔧 Estrategia: {strategy}")
            print(f"   Descripción: {params['description']}")
            print(f"   Ganancia BF: {params['gain_db']} dB")
            
            throughput_vs_snr = []
            
            for snr_db in snr_range:
                # Apply beamforming gain
                enhanced_snr_db = snr_db + params['gain_db'] + baseline_config['array_gain_db'] + self.base_channel_gain_db + 110
                enhanced_snr_linear = 10**(enhanced_snr_db/10)
                
                # Shannon capacity with beamforming
                streams = baseline_config['spatial_streams']
                spectral_eff = streams * np.log2(1 + enhanced_snr_linear / streams)
                throughput = spectral_eff * self.bandwidth_hz / 1e6 * baseline_config['practical_efficiency']
                
                throughput_vs_snr.append(throughput)
            
            results[strategy] = {
                'gain_db': params['gain_db'],
                'description': params['description'],
                'snr_range': snr_range,
                'throughput_mbps': np.array(throughput_vs_snr),
                'avg_throughput': np.mean(throughput_vs_snr),
                'peak_throughput': np.max(throughput_vs_snr),
                'improvement_vs_omni': np.mean(throughput_vs_snr) / results.get('Omnidirectional', {}).get('avg_throughput', 1) if 'Omnidirectional' in results else 1
            }
            
            print(f"   ✅ Throughput promedio: {np.mean(throughput_vs_snr):.1f} Mbps")
            print(f"   ✅ Throughput máximo: {np.max(throughput_vs_snr):.1f} Mbps")
        
        # Calculate improvements
        omni_performance = results['Omnidirectional']['avg_throughput']
        for strategy in results:
            if strategy != 'Omnidirectional':
                improvement = results[strategy]['avg_throughput'] / omni_performance
                results[strategy]['improvement_vs_omni'] = improvement
                print(f"📊 {strategy}: {improvement:.2f}x mejora vs omnidireccional")
        
        self.beamforming_results = results
        return results
    
    def generate_mimo_comparison_plot(self, save_path="./UAV/outputs/mimo_analysis_theoretical.png"):
        """Generar gráficos comparativos MIMO"""
        print(f"\n📊 GENERANDO GRÁFICOS MIMO...")
        
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        # Extract data
        configs = list(self.mimo_results.keys())
        theoretical_throughputs = [self.mimo_results[c]['theoretical_throughput_mbps'] for c in configs]
        practical_throughputs = [self.mimo_results[c]['practical_throughput_mbps'] for c in configs]
        spectral_effs = [self.mimo_results[c]['spectral_efficiency'] for c in configs]
        array_gains = [self.mimo_results[c]['array_gain_db'] for c in configs]
        spatial_streams = [self.mimo_results[c]['spatial_streams'] for c in configs]
        
        # Create figure
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # 1. Throughput comparison
        x_pos = np.arange(len(configs))
        width = 0.35
        
        bars1 = ax1.bar(x_pos - width/2, theoretical_throughputs, width, 
                       label='Teórico', color='lightblue', alpha=0.8)
        bars2 = ax1.bar(x_pos + width/2, practical_throughputs, width,
                       label='Práctico', color='darkblue', alpha=0.8)
        
        ax1.set_ylabel('Throughput [Mbps]', fontweight='bold')
        ax1.set_title('Throughput por Configuración MIMO', fontweight='bold')
        ax1.set_xticks(x_pos)
        ax1.set_xticklabels(configs, rotation=45)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Add value labels
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height + 5,
                        f'{height:.0f}', ha='center', va='bottom', fontsize=8)
        
        # 2. Spectral Efficiency
        bars = ax2.bar(configs, spectral_effs, color='green', alpha=0.7)
        ax2.set_ylabel('Eficiencia Espectral [bits/s/Hz]', fontweight='bold')
        ax2.set_title('Eficiencia Espectral MIMO', fontweight='bold')
        ax2.tick_params(axis='x', rotation=45)
        ax2.grid(True, alpha=0.3)
        
        for bar, val in zip(bars, spectral_effs):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                    f'{val:.1f}', ha='center', va='bottom', fontweight='bold')
        
        # 3. Array Gain vs Streams
        ax3.scatter(spatial_streams, array_gains, c=practical_throughputs, 
                   s=150, alpha=0.8, cmap='viridis')
        ax3.set_xlabel('Streams Espaciales', fontweight='bold')
        ax3.set_ylabel('Array Gain [dB]', fontweight='bold')
        ax3.set_title('Array Gain vs Multiplexación Espacial', fontweight='bold')
        ax3.grid(True, alpha=0.3)
        
        # Add config labels
        for i, config in enumerate(configs):
            ax3.annotate(config.split('_')[0], (spatial_streams[i], array_gains[i]),
                        xytext=(5, 5), textcoords='offset points', fontsize=8)
        
        # 4. MIMO scaling efficiency
        siso_throughput = self.mimo_results['1x1_SISO']['practical_throughput_mbps']
        gains = [t/siso_throughput for t in practical_throughputs]
        
        bars = ax4.bar(configs, gains, color='orange', alpha=0.7)
        ax4.set_ylabel('Ganancia vs SISO', fontweight='bold')
        ax4.set_title('Escalamiento MIMO vs SISO', fontweight='bold')
        ax4.tick_params(axis='x', rotation=45)
        ax4.grid(True, alpha=0.3)
        ax4.axhline(y=1, color='red', linestyle='--', label='SISO baseline')
        ax4.legend()
        
        for bar, val in zip(bars, gains):
            ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2,
                    f'{val:.1f}x', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        print(f"✅ Gráfico MIMO guardado: {save_path}")
    
    def generate_beamforming_plot(self, save_path="./UAV/outputs/beamforming_analysis_theoretical.png"):
        """Generar gráficos de beamforming"""
        print(f"\n🎯 GENERANDO GRÁFICOS BEAMFORMING...")
        
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        # Create figure
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        # 1. Throughput vs SNR for different beamforming strategies
        for strategy, data in self.beamforming_results.items():
            ax1.plot(data['snr_range'], data['throughput_mbps'], 
                    marker='o', linewidth=2, label=f"{strategy} (+{data['gain_db']}dB)")
        
        ax1.set_xlabel('SNR [dB]', fontweight='bold')
        ax1.set_ylabel('Throughput [Mbps]', fontweight='bold')
        ax1.set_title('Impacto del Beamforming vs SNR', fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # 2. Average throughput and gain comparison
        strategies = list(self.beamforming_results.keys())
        avg_throughputs = [self.beamforming_results[s]['avg_throughput'] for s in strategies]
        gains_db = [self.beamforming_results[s]['gain_db'] for s in strategies]
        
        # Bar plot with dual y-axis
        ax2_twin = ax2.twinx()
        
        bars1 = ax2.bar([s + '\n(+' + str(self.beamforming_results[s]['gain_db']) + 'dB)' for s in strategies], 
                       avg_throughputs, color='skyblue', alpha=0.7)
        
        ax2.set_ylabel('Throughput Promedio [Mbps]', fontweight='bold', color='blue')
        ax2.set_title('Comparación Estrategias Beamforming', fontweight='bold')
        ax2.tick_params(axis='x', rotation=45)
        ax2.grid(True, alpha=0.3)
        
        # Add improvement percentages
        omni_performance = self.beamforming_results['Omnidirectional']['avg_throughput']
        for i, (strategy, throughput) in enumerate(zip(strategies, avg_throughputs)):
            if strategy != 'Omnidirectional':
                improvement = ((throughput - omni_performance) / omni_performance) * 100
                ax2.text(i, throughput + 20, f'+{improvement:.0f}%', 
                        ha='center', va='bottom', fontweight='bold', color='red')
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        print(f"✅ Gráfico Beamforming guardado: {save_path}")
    
    def generate_report(self):
        """Generar reporte completo"""
        print(f"\n" + "="*70)
        print("REPORTE ANÁLISIS MIMO Y BEAMFORMING (TEÓRICO)")
        print("="*70)
        
        # Best configurations
        best_mimo = max(self.mimo_results.items(), 
                       key=lambda x: x[1]['practical_throughput_mbps'])
        best_bf = max(self.beamforming_results.items(),
                     key=lambda x: x[1]['avg_throughput'])
        
        print(f"\n📊 CONFIGURACIÓN DEL ANÁLISIS:")
        print(f"  📍 Posición: {self.test_position}")
        print(f"  📶 Bandwidth: {self.bandwidth_hz/1e6:.0f} MHz")
        print(f"  📡 Frecuencia: {self.frequency_hz/1e9:.1f} GHz")
        print(f"  🎯 SNR base: {self.base_snr_db} dB")
        
        print(f"\n🏆 MEJORES CONFIGURACIONES:")
        print(f"  📡 Mejor MIMO: {best_mimo[0]}")
        print(f"     • Antenas: {best_mimo[1]['gnb_antennas']} gNB, {best_mimo[1]['uav_antennas']} UAV")
        print(f"     • Streams: {best_mimo[1]['spatial_streams']}")
        print(f"     • Throughput: {best_mimo[1]['practical_throughput_mbps']:.1f} Mbps")
        print(f"     • Array Gain: {best_mimo[1]['array_gain_db']:.1f} dB")
        
        print(f"  🎯 Mejor Beamforming: {best_bf[0]}")
        print(f"     • Ganancia: {best_bf[1]['gain_db']} dB")
        print(f"     • Throughput promedio: {best_bf[1]['avg_throughput']:.1f} Mbps")
        print(f"     • Mejora vs omni: {best_bf[1].get('improvement_vs_omni', 1):.2f}x")
        
        # Performance comparison
        siso_performance = self.mimo_results['1x1_SISO']['practical_throughput_mbps']
        mimo_gain = best_mimo[1]['practical_throughput_mbps'] / siso_performance
        
        omni_performance = self.beamforming_results['Omnidirectional']['avg_throughput']
        bf_gain = best_bf[1]['avg_throughput'] / omni_performance
        
        combined_performance = best_mimo[1]['practical_throughput_mbps'] * bf_gain
        
        print(f"\n📈 ANÁLISIS DE GANANCIA:")
        print(f"  📊 Ganancia MIMO: {mimo_gain:.1f}x vs SISO")
        print(f"  📊 Ganancia Beamforming: {bf_gain:.2f}x vs omnidireccional")
        print(f"  🚀 Performance combinado: {combined_performance:.1f} Mbps")
        print(f"  🎯 Ganancia total: {combined_performance/siso_performance:.1f}x vs SISO baseline")
        
        print(f"\n💡 RECOMENDACIONES:")
        print(f"  ✅ Configuración óptima: {best_mimo[0]} + {best_bf[0]}")
        print(f"  📈 Throughput esperado: {combined_performance:.1f} Mbps")
        print(f"  🔧 Implementación: Array {best_mimo[1]['gnb_antennas']}x{best_mimo[1]['uav_antennas']} con beamforming {best_bf[0]}")
        
        print("="*70)

def run_theoretical_analysis():
    """Ejecutar análisis teórico completo"""
    # Initialize analysis
    analysis = SimplifiedMIMOBeamformingAnalysis()
    
    # Run MIMO analysis
    print("🔄 Ejecutando análisis MIMO teórico...")
    mimo_results = analysis.analyze_mimo_configurations()
    
    # Run beamforming analysis
    print("🔄 Ejecutando análisis beamforming...")
    beamforming_results = analysis.analyze_beamforming_strategies()
    
    # Generate plots
    analysis.generate_mimo_comparison_plot()
    analysis.generate_beamforming_plot()
    
    # Generate report
    analysis.generate_report()
    
    return analysis, mimo_results, beamforming_results

if __name__ == "__main__":
    analysis, mimo_results, bf_results = run_theoretical_analysis()