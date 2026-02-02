"""
Beamforming & MIMO Analysis - Análisis de Arrays de Antenas y Beamforming
Optimización de configuraciones MIMO para maximizar throughput en UAVs
"""
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import sys
import os
from scipy.optimize import minimize_scalar
import seaborn as sns

# Importar configuraciones y sistema
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.system_config import *
from systems.basic_system import BasicUAVSystem

class BeamformingMIMOAnalysis:
    """
    Análisis completo de Beamforming y configuraciones MIMO
    """
    
    def __init__(self, test_position=[100, 100, 50]):
        """
        Inicializar análisis de Beamforming y MIMO
        
        Args:
            test_position: Posición de prueba UAV [x, y, z]
        """
        self.test_position = test_position
        
        print("="*70)
        print("ANÁLISIS DE BEAMFORMING Y MIMO")
        print("="*70)
        
        # MIMO configurations to test
        self.mimo_configs = {
            # gNB configs: [total_antennas, rows, cols]
            # UAV configs: [total_antennas, rows, cols]
            "2x2_SISO": {"gnb": [1, 1, 1], "uav": [1, 1, 1], "description": "SISO baseline"},
            "4x4_2x2": {"gnb": [4, 2, 2], "uav": [4, 2, 2], "description": "Small MIMO"},
            "16x4_4x2": {"gnb": [16, 4, 4], "uav": [4, 2, 2], "description": "Medium gNB, Small UAV"},
            "64x4_8x2": {"gnb": [64, 8, 8], "uav": [4, 2, 2], "description": "Large gNB, Small UAV (Current)"},
            "64x16_8x4": {"gnb": [64, 8, 8], "uav": [16, 4, 4], "description": "Large gNB, Medium UAV"},
            "256x16_16x4": {"gnb": [256, 16, 16], "uav": [16, 4, 4], "description": "Massive MIMO"},
        }
        
        # Beamforming strategies
        self.beamforming_strategies = {
            "omnidirectional": "Sin beamforming",
            "max_ratio": "Maximum Ratio Transmission",
            "zero_forcing": "Zero Forcing",
            "mmse": "MMSE beamforming"
        }
        
        print(f"🎯 Posición de prueba: {test_position}")
        print(f"📡 Configuraciones MIMO: {len(self.mimo_configs)}")
        print(f"🔧 Estrategias beamforming: {len(self.beamforming_strategies)}")
        
        # Results storage
        self.mimo_results = {}
        self.beamforming_results = {}
        self.optimal_configs = {}
    
    def analyze_mimo_configurations(self, snr_db=20):
        """Analizar diferentes configuraciones MIMO"""
        print(f"\n📡 ANÁLISIS DE CONFIGURACIONES MIMO")
        print(f"📶 SNR: {snr_db} dB")
        print(f"📍 Posición: {self.test_position}")
        
        results = {}
        
        for config_name, config in self.mimo_configs.items():
            print(f"\n🔧 Configuración: {config_name}")
            print(f"   gNB: {config['gnb'][0]} antenas ({config['gnb'][1]}x{config['gnb'][2]})")
            print(f"   UAV: {config['uav'][0]} antenas ({config['uav'][1]}x{config['uav'][2]})")
            
            try:
                # Create temporary modified configs
                original_gnb_config = AntennaConfig.GNB_CONFIG.copy()
                original_uav_config = AntennaConfig.UAV_CONFIG.copy()
                
                # Modify antenna configurations
                AntennaConfig.GNB_CONFIG.update({
                    'num_antennas': config['gnb'][0],
                    'array_rows': config['gnb'][1], 
                    'array_cols': config['gnb'][2]
                })
                AntennaConfig.UAV_CONFIG.update({
                    'num_antennas': config['uav'][0],
                    'array_rows': config['uav'][1],
                    'array_cols': config['uav'][2]
                })
                
                # Initialize system with new config
                system = BasicUAVSystem()
                
                # Move UAV to test position
                system.scenario.move_uav("UAV1", self.test_position)
                
                # Get paths and simulate
                paths = system.scenario.get_paths(max_depth=5)
                system.paths = paths
                
                # Simulate at test SNR
                metrics = system._simulate_single_snr(snr_db)
                
                # Calculate theoretical MIMO gain
                mimo_gain_db = 10 * np.log10(min(config['gnb'][0], config['uav'][0]))
                
                # Calculate actual SNR with channel conditions
                actual_snr_linear = 10**(snr_db/10)
                channel_power_gain = 10**(metrics['channel_gain_db']/10)
                effective_snr_linear = actual_snr_linear * channel_power_gain
                
                # Shannon capacity with MIMO spatial streams
                spatial_streams = min(config['gnb'][0], config['uav'][0])
                theoretical_capacity = spatial_streams * np.log2(1 + effective_snr_linear)
                actual_throughput = theoretical_capacity * RFConfig.BANDWIDTH_HZ / 1e6  # Convert to Mbps
                
                results[config_name] = {
                    'throughput_mbps': actual_throughput,
                    'spectral_efficiency': theoretical_capacity,
                    'channel_gain_db': metrics['channel_gain_db'],
                    'gnb_antennas': config['gnb'][0],
                    'uav_antennas': config['uav'][0],
                    'mimo_gain_db': mimo_gain_db,
                    'spatial_streams': spatial_streams,
                    'effective_snr_db': 10 * np.log10(effective_snr_linear),
                    'channel_condition': metrics.get('channel_condition', {})
                }
                
                print(f"   ✅ Throughput: {actual_throughput:.1f} Mbps")
                print(f"   ✅ MIMO gain: {mimo_gain_db:.1f} dB")
                print(f"   ✅ Spatial streams: {spatial_streams}")
                print(f"   ✅ Eficiencia: {theoretical_capacity:.2f} bits/s/Hz")
                
                # Restore original configuration
                AntennaConfig.GNB_CONFIG.update(original_gnb_config)
                AntennaConfig.UAV_CONFIG.update(original_uav_config)
                
            except Exception as e:
                print(f"   ❌ Error en configuración {config_name}: {str(e)}")
                results[config_name] = {
                    'throughput_mbps': 0,
                    'spectral_efficiency': 0,
                    'channel_gain_db': -100,
                    'error': str(e)
                }
        
        self.mimo_results = results
        return results
    
    def analyze_beamforming_impact(self, snr_range=None):
        """Analizar impacto del beamforming en diferentes SNRs"""
        if snr_range is None:
            snr_range = np.arange(0, 25, 5)
        
        print(f"\n🎯 ANÁLISIS DE IMPACTO DE BEAMFORMING")
        print(f"📶 SNR range: {snr_range[0]} - {snr_range[-1]} dB")
        
        # Use current system configuration
        print(f"🔧 Usando configuración actual del sistema")
        
        results = {}
        
        # Initialize system
        system = BasicUAVSystem()
        system.scenario.move_uav("UAV1", self.test_position)
        paths = system.scenario.get_paths(max_depth=5)
        system.paths = paths
        
        # Get base channel metrics
        base_metrics = system._simulate_single_snr(15)  # Reference SNR
        base_channel_gain = base_metrics['channel_gain_db']
        
        for strategy in self.beamforming_strategies.keys():
            print(f"\n🔧 Estrategia: {strategy}")
            
            throughput_vs_snr = []
            spectral_efficiency_vs_snr = []
            
            for snr_db in snr_range:
                try:
                    # Apply beamforming gain (simplified model)
                    if strategy == "omnidirectional":
                        bf_gain_db = 0  # No beamforming
                    elif strategy == "max_ratio":
                        bf_gain_db = 3  # Typical MRT gain
                    elif strategy == "zero_forcing":
                        bf_gain_db = 5  # ZF gain with interference nulling
                    elif strategy == "mmse":
                        bf_gain_db = 4  # MMSE balance between gain and interference
                    
                    # Calculate effective SNR
                    total_gain_db = base_channel_gain + bf_gain_db
                    effective_snr_db = snr_db + total_gain_db
                    effective_snr_linear = 10**(effective_snr_db/10)
                    
                    # Calculate Shannon capacity (conservative estimate)
                    spectral_efficiency = np.log2(1 + effective_snr_linear)
                    throughput = spectral_efficiency * RFConfig.BANDWIDTH_HZ / 1e6  # Mbps
                    
                    throughput_vs_snr.append(throughput)
                    spectral_efficiency_vs_snr.append(spectral_efficiency)
                    
                except Exception as e:
                    print(f"      Error at SNR {snr_db}: {str(e)}")
                    throughput_vs_snr.append(0)
                    spectral_efficiency_vs_snr.append(0)
            
            results[strategy] = {
                'snr_range': snr_range,
                'throughput_mbps': np.array(throughput_vs_snr),
                'spectral_efficiency': np.array(spectral_efficiency_vs_snr),
                'avg_throughput': np.mean(throughput_vs_snr),
                'peak_throughput': np.max(throughput_vs_snr),
                'description': self.beamforming_strategies[strategy],
                'beamforming_gain_db': bf_gain_db if 'bf_gain_db' in locals() else 0
            }
            
            print(f"   ✅ Throughput promedio: {np.mean(throughput_vs_snr):.1f} Mbps")
            print(f"   ✅ Throughput máximo: {np.max(throughput_vs_snr):.1f} Mbps")
            print(f"   ✅ Ganancia BF: {results[strategy]['beamforming_gain_db']:.1f} dB")
        
        self.beamforming_results = results
        return results
    
    def find_optimal_configurations(self):
        """Encontrar configuraciones óptimas"""
        print(f"\n🏆 BÚSQUEDA DE CONFIGURACIONES ÓPTIMAS")
        
        optimal = {}
        
        # Best MIMO configuration
        if self.mimo_results:
            best_mimo = max(self.mimo_results.items(), 
                           key=lambda x: x[1].get('throughput_mbps', 0))
            optimal['best_mimo'] = {
                'config': best_mimo[0],
                'throughput_mbps': best_mimo[1].get('throughput_mbps', 0),
                'spectral_efficiency': best_mimo[1].get('spectral_efficiency', 0)
            }
            
            print(f"🥇 Mejor MIMO: {best_mimo[0]}")
            print(f"   📈 Throughput: {best_mimo[1].get('throughput_mbps', 0):.1f} Mbps")
        
        # Best beamforming strategy
        if self.beamforming_results:
            best_bf = max(self.beamforming_results.items(),
                         key=lambda x: x[1].get('avg_throughput', 0))
            optimal['best_beamforming'] = {
                'strategy': best_bf[0],
                'avg_throughput': best_bf[1].get('avg_throughput', 0),
                'peak_throughput': best_bf[1].get('peak_throughput', 0)
            }
            
            print(f"🥇 Mejor Beamforming: {best_bf[0]}")
            print(f"   📈 Throughput promedio: {best_bf[1].get('avg_throughput', 0):.1f} Mbps")
            print(f"   🚀 Throughput máximo: {best_bf[1].get('peak_throughput', 0):.1f} Mbps")
        
        # Performance ratios
        if self.mimo_results:
            siso_throughput = self.mimo_results.get('2x2_SISO', {}).get('throughput_mbps', 1)
            
            for config, data in self.mimo_results.items():
                if 'throughput_mbps' in data and siso_throughput > 0:
                    gain_ratio = data['throughput_mbps'] / siso_throughput
                    data['gain_vs_siso'] = gain_ratio
                    print(f"📊 {config}: {gain_ratio:.1f}x ganancia vs SISO")
        
        self.optimal_configs = optimal
        return optimal
    
    def generate_mimo_comparison_plot(self, save_path="./UAV/outputs/mimo_analysis.png"):
        """Generar gráfico comparativo MIMO"""
        if not self.mimo_results:
            print("❌ No hay resultados MIMO para graficar.")
            return
        
        print(f"\n📊 GENERANDO GRÁFICOS MIMO...")
        
        # Create output directory
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        # Extract data
        configs = list(self.mimo_results.keys())
        throughputs = [self.mimo_results[c].get('throughput_mbps', 0) for c in configs]
        spectral_effs = [self.mimo_results[c].get('spectral_efficiency', 0) for c in configs]
        gnb_antennas = [self.mimo_results[c].get('gnb_antennas', 1) for c in configs]
        uav_antennas = [self.mimo_results[c].get('uav_antennas', 1) for c in configs]
        
        # Create figure
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # 1. Throughput comparison
        bars1 = ax1.bar(configs, throughputs, color='skyblue', alpha=0.7)
        ax1.set_ylabel('Throughput [Mbps]', fontweight='bold')
        ax1.set_title('Throughput por Configuración MIMO', fontweight='bold')
        ax1.tick_params(axis='x', rotation=45)
        ax1.grid(True, alpha=0.3)
        
        # Add value labels on bars
        for bar, val in zip(bars1, throughputs):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                    f'{val:.1f}', ha='center', va='bottom', fontweight='bold')
        
        # 2. Spectral Efficiency comparison  
        bars2 = ax2.bar(configs, spectral_effs, color='lightgreen', alpha=0.7)
        ax2.set_ylabel('Eficiencia Espectral [bits/s/Hz]', fontweight='bold')
        ax2.set_title('Eficiencia Espectral por Configuración', fontweight='bold')
        ax2.tick_params(axis='x', rotation=45)
        ax2.grid(True, alpha=0.3)
        
        for bar, val in zip(bars2, spectral_effs):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{val:.2f}', ha='center', va='bottom', fontweight='bold')
        
        # 3. Antenna scaling analysis
        total_antennas = [g*u for g,u in zip(gnb_antennas, uav_antennas)]
        ax3.scatter(total_antennas, throughputs, c=spectral_effs, s=100, alpha=0.7, cmap='viridis')
        ax3.set_xlabel('Total de Antenas (gNB × UAV)', fontweight='bold')
        ax3.set_ylabel('Throughput [Mbps]', fontweight='bold')
        ax3.set_title('Escalamiento de Antenas vs Throughput', fontweight='bold')
        ax3.grid(True, alpha=0.3)
        
        # Add config labels
        for i, config in enumerate(configs):
            ax3.annotate(config.split('_')[0], (total_antennas[i], throughputs[i]),
                        xytext=(5, 5), textcoords='offset points', fontsize=8)
        
        # 4. MIMO gain analysis
        siso_throughput = self.mimo_results.get('2x2_SISO', {}).get('throughput_mbps', 1)
        gains = [t/siso_throughput if siso_throughput > 0 else 0 for t in throughputs]
        
        bars4 = ax4.bar(configs, gains, color='orange', alpha=0.7)
        ax4.set_ylabel('Ganancia vs SISO', fontweight='bold')
        ax4.set_title('Ganancia MIMO Relativa', fontweight='bold')
        ax4.tick_params(axis='x', rotation=45)
        ax4.grid(True, alpha=0.3)
        ax4.axhline(y=1, color='red', linestyle='--', label='SISO baseline')
        ax4.legend()
        
        for bar, val in zip(bars4, gains):
            ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                    f'{val:.1f}x', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=VisualizationConfig.DPI, bbox_inches='tight')
        
        print(f"✅ Gráfico MIMO guardado: {save_path}")
        return fig
    
    def generate_beamforming_plot(self, save_path="./UAV/outputs/beamforming_analysis.png"):
        """Generar gráfico comparativo de beamforming"""
        if not self.beamforming_results:
            print("❌ No hay resultados de beamforming para graficar.")
            return
        
        print(f"\n🎯 GENERANDO GRÁFICOS BEAMFORMING...")
        
        # Create output directory
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        # Create figure
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        # 1. Throughput vs SNR for different beamforming strategies
        for strategy, data in self.beamforming_results.items():
            ax1.plot(data['snr_range'], data['throughput_mbps'], 
                    marker='o', linewidth=2, label=f"{strategy} ({data['description']})")
        
        ax1.set_xlabel('SNR [dB]', fontweight='bold')
        ax1.set_ylabel('Throughput [Mbps]', fontweight='bold')
        ax1.set_title('Impacto del Beamforming vs SNR', fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # 2. Average throughput comparison
        strategies = list(self.beamforming_results.keys())
        avg_throughputs = [self.beamforming_results[s]['avg_throughput'] for s in strategies]
        peak_throughputs = [self.beamforming_results[s]['peak_throughput'] for s in strategies]
        
        x_pos = np.arange(len(strategies))
        width = 0.35
        
        bars1 = ax2.bar(x_pos - width/2, avg_throughputs, width, 
                       label='Promedio', color='skyblue', alpha=0.7)
        bars2 = ax2.bar(x_pos + width/2, peak_throughputs, width,
                       label='Máximo', color='orange', alpha=0.7)
        
        ax2.set_xlabel('Estrategia de Beamforming', fontweight='bold')
        ax2.set_ylabel('Throughput [Mbps]', fontweight='bold')
        ax2.set_title('Comparación de Estrategias de Beamforming', fontweight='bold')
        ax2.set_xticks(x_pos)
        ax2.set_xticklabels(strategies, rotation=45)
        ax2.grid(True, alpha=0.3)
        ax2.legend()
        
        # Add value labels
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                        f'{height:.1f}', ha='center', va='bottom', fontsize=9)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=VisualizationConfig.DPI, bbox_inches='tight')
        
        print(f"✅ Gráfico Beamforming guardado: {save_path}")
        return fig
    
    def save_results(self, data_path="./UAV/outputs/mimo_beamforming_data.npz"):
        """Guardar resultados del análisis"""
        # Create output directory
        os.makedirs(os.path.dirname(data_path), exist_ok=True)
        
        # Prepare data for saving
        save_data = {
            'mimo_results': self.mimo_results,
            'beamforming_results': self.beamforming_results,
            'optimal_configs': self.optimal_configs,
            'test_position': self.test_position,
            'mimo_configs': self.mimo_configs
        }
        
        # Save as numpy arrays where possible, strings otherwise
        np.savez(data_path, **{k: v for k, v in save_data.items() if isinstance(v, (np.ndarray, list, int, float))})
        
        print(f"✅ Datos guardados: {data_path}")
    
    def generate_report(self):
        """Generar reporte completo"""
        print(f"\n" + "="*70)
        print("REPORTE DE ANÁLISIS MIMO Y BEAMFORMING")
        print("="*70)
        
        # Configuration summary
        print(f"\n📊 CONFIGURACIÓN DEL ANÁLISIS:")
        print(f"  📍 Posición de prueba: {self.test_position}")
        print(f"  📡 Configuraciones MIMO probadas: {len(self.mimo_configs)}")
        print(f"  🎯 Estrategias beamforming: {len(self.beamforming_strategies)}")
        
        # MIMO results
        if self.mimo_results:
            print(f"\n📡 RESULTADOS MIMO:")
            
            best_mimo = max(self.mimo_results.items(), 
                           key=lambda x: x[1].get('throughput_mbps', 0))
            worst_mimo = min(self.mimo_results.items(), 
                            key=lambda x: x[1].get('throughput_mbps', 0))
            
            print(f"  🥇 Mejor configuración: {best_mimo[0]}")
            print(f"     • Throughput: {best_mimo[1].get('throughput_mbps', 0):.1f} Mbps")
            print(f"     • Eficiencia espectral: {best_mimo[1].get('spectral_efficiency', 0):.2f} bits/s/Hz")
            
            print(f"  🥉 Peor configuración: {worst_mimo[0]}")
            print(f"     • Throughput: {worst_mimo[1].get('throughput_mbps', 0):.1f} Mbps")
            
            # MIMO scaling analysis
            siso_performance = self.mimo_results.get('2x2_SISO', {}).get('throughput_mbps', 0)
            if siso_performance > 0:
                mimo_gain = best_mimo[1].get('throughput_mbps', 0) / siso_performance
                print(f"  📈 Ganancia MIMO máxima: {mimo_gain:.1f}x vs SISO")
        
        # Beamforming results
        if self.beamforming_results:
            print(f"\n🎯 RESULTADOS BEAMFORMING:")
            
            best_bf = max(self.beamforming_results.items(),
                         key=lambda x: x[1].get('avg_throughput', 0))
            
            print(f"  🥇 Mejor estrategia: {best_bf[0]}")
            print(f"     • Descripción: {best_bf[1].get('description', 'N/A')}")
            print(f"     • Throughput promedio: {best_bf[1].get('avg_throughput', 0):.1f} Mbps")
            print(f"     • Throughput máximo: {best_bf[1].get('peak_throughput', 0):.1f} Mbps")
            
            # Beamforming gain
            omni_performance = self.beamforming_results.get('omnidirectional', {}).get('avg_throughput', 0)
            if omni_performance > 0:
                bf_gain = best_bf[1].get('avg_throughput', 0) / omni_performance
                print(f"  📈 Ganancia beamforming: {bf_gain:.1f}x vs omnidireccional")
        
        # Recommendations
        print(f"\n💡 RECOMENDACIONES:")
        
        if self.optimal_configs:
            if 'best_mimo' in self.optimal_configs:
                print(f"  ✅ Configuración MIMO óptima: {self.optimal_configs['best_mimo']['config']}")
            
            if 'best_beamforming' in self.optimal_configs:
                print(f"  ✅ Estrategia beamforming óptima: {self.optimal_configs['best_beamforming']['strategy']}")
            
            # Combined performance estimate
            if 'best_mimo' in self.optimal_configs and 'best_beamforming' in self.optimal_configs:
                combined_throughput = (self.optimal_configs['best_mimo']['throughput_mbps'] * 
                                     1.5)  # Conservative beamforming gain estimate
                print(f"  🚀 Throughput estimado combinado: {combined_throughput:.1f} Mbps")
        
        print("="*70)

def run_complete_mimo_beamforming_analysis():
    """Ejecutar análisis completo de MIMO y Beamforming"""
    # Test at optimal position from previous phases
    analysis = BeamformingMIMOAnalysis(test_position=[100, 100, 50])
    
    # Run MIMO analysis
    print("🔄 Ejecutando análisis MIMO...")
    mimo_results = analysis.analyze_mimo_configurations()
    
    # Run beamforming analysis
    print("🔄 Ejecutando análisis beamforming...")
    beamforming_results = analysis.analyze_beamforming_impact()
    
    # Find optimal configurations
    optimal = analysis.find_optimal_configurations()
    
    # Generate plots
    analysis.generate_mimo_comparison_plot()
    analysis.generate_beamforming_plot()
    
    # Save results
    analysis.save_results()
    
    # Generate report
    analysis.generate_report()
    
    return analysis, mimo_results, beamforming_results, optimal

if __name__ == "__main__":
    analysis, mimo_results, bf_results, optimal = run_complete_mimo_beamforming_analysis()