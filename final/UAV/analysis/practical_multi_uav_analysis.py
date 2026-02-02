"""
Multi-UAV Relay Analysis - Versión Práctica con Modelos Realistas
Análisis simplificado de sistemas Multi-UAV con resultados sintéticos pero realistas
"""
import numpy as np
import matplotlib.pyplot as plt
import sys
import os

# Importar configuraciones
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.system_config import *

class PracticalMultiUAVAnalysis:
    """Análisis Multi-UAV con modelos prácticos y resultados realistas"""
    
    def __init__(self):
        """Inicializar análisis Multi-UAV"""
        
        print("="*70)
        print("ANÁLISIS MULTI-UAV Y RELAY (MODELO PRÁCTICO)")
        print("="*70)
        
        # System parameters
        self.bandwidth_hz = 100e6  # 100 MHz
        self.frequency_hz = 3.5e9  # 3.5 GHz
        self.base_snr_db = 20      # Reference SNR
        
        # Network positions (realistic urban deployment)
        self.positions = {
            "gnb": [0, 0, 30],           # gNB at 30m height
            "user_uav": [200, 200, 50],  # User UAV distant from gNB
            "relay_uav": [100, 100, 60], # Relay UAV at intermediate position
            "mesh_uav_1": [150, 50, 55], # Mesh node 1
            "mesh_uav_2": [50, 150, 55]  # Mesh node 2
        }
        
        # Antenna configurations (from Phase 4)
        self.antenna_config = {
            "gnb": 64,      # 8x8 massive MIMO
            "user_uav": 4,  # 2x2 MIMO
            "relay_uav": 16, # 4x4 MIMO (better for relay)
            "mesh_uav_1": 4, # 2x2 MIMO
            "mesh_uav_2": 4  # 2x2 MIMO
        }
        
        print(f"📡 Configuración desplegada:")
        for node, pos in self.positions.items():
            ant = self.antenna_config[node]
            print(f"  • {node}: {pos} ({ant} antenas)")
    
    def calculate_realistic_link_performance(self, tx_node, rx_node, snr_db=20):
        """Calcular performance realista de un enlace"""
        
        tx_pos = self.positions[tx_node]
        rx_pos = self.positions[rx_node] 
        tx_ant = self.antenna_config[tx_node]
        rx_ant = self.antenna_config[rx_node]
        
        # Calculate distance
        distance = np.sqrt(sum((np.array(tx_pos) - np.array(rx_pos))**2))
        
        # Realistic path loss model (3GPP Urban Macro)
        if distance < 10:
            distance = 10  # Minimum distance
        
        # Path loss calculation
        path_loss_db = 28.0 + 22 * np.log10(distance) + 20 * np.log10(self.frequency_hz/1e9)
        
        # Shadow fading (log-normal, mean 0, std 8 dB)
        shadow_fading_db = np.random.normal(0, 4)  # Reduced for stable results
        
        # Array gain
        array_gain_db = 10 * np.log10(tx_ant) + 10 * np.log10(rx_ant)
        
        # Beamforming gain (conservative estimate)
        bf_gain_db = 3 if tx_ant >= 16 else 1  # Higher gain for larger arrays
        
        # Total received SNR
        total_snr_db = snr_db + array_gain_db + bf_gain_db - path_loss_db + shadow_fading_db
        total_snr_linear = 10**(total_snr_db/10)
        
        # MIMO capacity
        spatial_streams = min(tx_ant, rx_ant)
        if total_snr_linear > 0:
            spectral_efficiency = spatial_streams * np.log2(1 + total_snr_linear / spatial_streams)
            throughput_mbps = spectral_efficiency * self.bandwidth_hz / 1e6
        else:
            spectral_efficiency = 0
            throughput_mbps = 0
        
        # LoS probability (based on elevation angle)
        height_diff = abs(tx_pos[2] - rx_pos[2])
        horizontal_dist = np.sqrt((tx_pos[0] - rx_pos[0])**2 + (tx_pos[1] - rx_pos[1])**2)
        elevation_angle = np.arctan(height_diff / max(horizontal_dist, 1)) * 180 / np.pi
        los_probability = min(1.0, elevation_angle / 20 + 0.3)  # Realistic model
        
        return {
            'tx_node': tx_node,
            'rx_node': rx_node,
            'distance_m': distance,
            'path_loss_db': path_loss_db,
            'array_gain_db': array_gain_db,
            'beamforming_gain_db': bf_gain_db,
            'total_snr_db': total_snr_db,
            'spatial_streams': spatial_streams,
            'spectral_efficiency': spectral_efficiency,
            'throughput_mbps': max(0, throughput_mbps),
            'los_probability': los_probability,
            'elevation_angle': elevation_angle
        }
    
    def analyze_network_topologies(self):
        """Analizar topologías de red Multi-UAV"""
        print(f"\n🔗 ANÁLISIS DE TOPOLOGÍAS MULTI-UAV")
        
        results = {}
        
        # 1. Direct topology: gNB → User UAV
        print(f"\n📡 Topología Directa:")
        direct_link = self.calculate_realistic_link_performance("gnb", "user_uav")
        
        results['direct'] = {
            'description': 'gNB → User UAV (directo)',
            'total_throughput_mbps': direct_link['throughput_mbps'],
            'hops': 1,
            'links': [direct_link],
            'bottleneck': direct_link['throughput_mbps'],
            'end_to_end_delay_ms': 5  # Single hop delay
        }
        
        print(f"  ✅ Throughput: {direct_link['throughput_mbps']:.1f} Mbps")
        print(f"  ✅ Distancia: {direct_link['distance_m']:.1f} m")
        print(f"  ✅ SNR efectivo: {direct_link['total_snr_db']:.1f} dB")
        
        # 2. Relay topology: gNB → Relay UAV → User UAV
        print(f"\n🛰️  Topología Relay:")
        link1 = self.calculate_realistic_link_performance("gnb", "relay_uav")
        link2 = self.calculate_realistic_link_performance("relay_uav", "user_uav", snr_db=18)  # Processing penalty
        
        relay_throughput = min(link1['throughput_mbps'], link2['throughput_mbps'])
        
        results['relay'] = {
            'description': 'gNB → Relay UAV → User UAV',
            'total_throughput_mbps': relay_throughput,
            'hops': 2,
            'links': [link1, link2],
            'bottleneck': min(link1['throughput_mbps'], link2['throughput_mbps']),
            'end_to_end_delay_ms': 12,  # Two hops + processing delay
            'relay_processing_gain': relay_throughput / direct_link['throughput_mbps'] if direct_link['throughput_mbps'] > 0 else 1
        }
        
        print(f"  ✅ Throughput: {relay_throughput:.1f} Mbps")
        print(f"  ✅ Hop 1 (gNB→Relay): {link1['throughput_mbps']:.1f} Mbps")
        print(f"  ✅ Hop 2 (Relay→User): {link2['throughput_mbps']:.1f} Mbps")
        print(f"  ✅ Ganancia vs directo: {relay_throughput/direct_link['throughput_mbps']:.2f}x")
        
        # 3. Mesh 2-hop: gNB → Mesh UAV 1 → User UAV
        print(f"\n🕸️  Topología Mesh (2 hops):")
        mesh_link1 = self.calculate_realistic_link_performance("gnb", "mesh_uav_1")
        mesh_link2 = self.calculate_realistic_link_performance("mesh_uav_1", "user_uav", snr_db=19)
        
        mesh_2hop_throughput = min(mesh_link1['throughput_mbps'], mesh_link2['throughput_mbps'])
        
        results['mesh_2hop'] = {
            'description': 'gNB → Mesh UAV 1 → User UAV',
            'total_throughput_mbps': mesh_2hop_throughput,
            'hops': 2,
            'links': [mesh_link1, mesh_link2],
            'bottleneck': min(mesh_link1['throughput_mbps'], mesh_link2['throughput_mbps']),
            'end_to_end_delay_ms': 10
        }
        
        print(f"  ✅ Throughput: {mesh_2hop_throughput:.1f} Mbps")
        
        # 4. Mesh 3-hop: gNB → Mesh UAV 1 → Mesh UAV 2 → User UAV
        print(f"\n🕸️  Topología Mesh (3 hops):")
        mesh3_link1 = self.calculate_realistic_link_performance("gnb", "mesh_uav_1")
        mesh3_link2 = self.calculate_realistic_link_performance("mesh_uav_1", "mesh_uav_2", snr_db=19)
        mesh3_link3 = self.calculate_realistic_link_performance("mesh_uav_2", "user_uav", snr_db=18)
        
        mesh_3hop_throughput = min(mesh3_link1['throughput_mbps'], 
                                  mesh3_link2['throughput_mbps'], 
                                  mesh3_link3['throughput_mbps'])
        
        results['mesh_3hop'] = {
            'description': 'gNB → Mesh UAV 1 → Mesh UAV 2 → User UAV',
            'total_throughput_mbps': mesh_3hop_throughput,
            'hops': 3,
            'links': [mesh3_link1, mesh3_link2, mesh3_link3],
            'bottleneck': min(mesh3_link1['throughput_mbps'], 
                            mesh3_link2['throughput_mbps'], 
                            mesh3_link3['throughput_mbps']),
            'end_to_end_delay_ms': 18
        }
        
        print(f"  ✅ Throughput: {mesh_3hop_throughput:.1f} Mbps")
        
        # 5. Cooperative topology: Relay + Mesh both help User UAV
        print(f"\n🤝 Topología Cooperativa:")
        
        # Path 1: gNB → Relay → User (from above)
        path1_throughput = relay_throughput
        
        # Path 2: gNB → Mesh 1 → User (from above)  
        path2_throughput = mesh_2hop_throughput
        
        # Cooperative combining with diversity gain
        diversity_gain = 1.4  # 40% gain from spatial diversity
        cooperative_throughput = (path1_throughput + path2_throughput) * diversity_gain
        
        results['cooperative'] = {
            'description': 'gNB → [Relay + Mesh] → User UAV (cooperativo)',
            'total_throughput_mbps': cooperative_throughput,
            'hops': 2,  # Average hops
            'path1_contribution': path1_throughput,
            'path2_contribution': path2_throughput,
            'diversity_gain': diversity_gain,
            'bottleneck': max(path1_throughput, path2_throughput),
            'end_to_end_delay_ms': 15,  # Parallel processing
            'cooperation_efficiency': cooperative_throughput / direct_link['throughput_mbps'] if direct_link['throughput_mbps'] > 0 else 1
        }
        
        print(f"  ✅ Throughput total: {cooperative_throughput:.1f} Mbps")
        print(f"  ✅ Contribución Relay: {path1_throughput:.1f} Mbps")
        print(f"  ✅ Contribución Mesh: {path2_throughput:.1f} Mbps")
        print(f"  ✅ Ganancia cooperativa: {diversity_gain:.2f}x")
        print(f"  ✅ Mejora vs directo: {cooperative_throughput/direct_link['throughput_mbps']:.2f}x")
        
        self.topology_results = results
        return results
    
    def optimize_relay_positioning(self):
        """Optimizar posición del relay UAV"""
        print(f"\n🎯 OPTIMIZACIÓN DE POSICIÓN RELAY")
        
        user_pos = self.positions["user_uav"]
        gnb_pos = self.positions["gnb"]
        
        # Test positions in a grid around the midpoint
        midpoint_x = (gnb_pos[0] + user_pos[0]) / 2
        midpoint_y = (gnb_pos[1] + user_pos[1]) / 2
        
        # Grid search around midpoint
        x_offsets = np.linspace(-50, 50, 10)
        y_offsets = np.linspace(-50, 50, 10)
        heights = [50, 60, 70, 80]
        
        best_position = None
        best_throughput = 0
        optimization_results = []
        
        for x_off in x_offsets:
            for y_off in y_offsets:
                for height in heights:
                    test_pos = [midpoint_x + x_off, midpoint_y + y_off, height]
                    
                    # Temporarily update relay position
                    original_pos = self.positions["relay_uav"]
                    self.positions["relay_uav"] = test_pos
                    
                    # Test relay performance
                    link1 = self.calculate_realistic_link_performance("gnb", "relay_uav")
                    link2 = self.calculate_realistic_link_performance("relay_uav", "user_uav", snr_db=18)
                    
                    throughput = min(link1['throughput_mbps'], link2['throughput_mbps'])
                    
                    optimization_results.append({
                        'position': test_pos.copy(),
                        'throughput_mbps': throughput,
                        'link1_snr': link1['total_snr_db'],
                        'link2_snr': link2['total_snr_db']
                    })
                    
                    if throughput > best_throughput:
                        best_throughput = throughput
                        best_position = test_pos.copy()
                    
                    # Restore original position
                    self.positions["relay_uav"] = original_pos
        
        # Set optimal position
        if best_position:
            self.positions["relay_uav"] = best_position
        
        # Compare with direct link
        direct_link = self.calculate_realistic_link_performance("gnb", "user_uav")
        improvement_factor = best_throughput / direct_link['throughput_mbps'] if direct_link['throughput_mbps'] > 0 else 1
        
        print(f"  ✅ Posición original: {original_pos}")
        print(f"  ✅ Posición óptima: {best_position}")
        print(f"  ✅ Throughput óptimo: {best_throughput:.1f} Mbps")
        print(f"  ✅ Mejora vs directo: {improvement_factor:.2f}x")
        print(f"  ✅ Posiciones evaluadas: {len(optimization_results)}")
        
        self.optimization_results = {
            'original_position': original_pos,
            'optimal_position': best_position,
            'optimal_throughput': best_throughput,
            'improvement_factor': improvement_factor,
            'direct_throughput': direct_link['throughput_mbps'],
            'all_results': optimization_results
        }
        
        return self.optimization_results
    
    def generate_network_visualization(self, save_path="./UAV/outputs/multi_uav_network.png"):
        """Generar visualización de red Multi-UAV"""
        print(f"\n🗺️  GENERANDO VISUALIZACIÓN DE RED...")
        
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        # Create figure with subplots
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # 1. Network topology map
        ax1.set_xlim(-50, 250)
        ax1.set_ylim(-50, 250)
        ax1.set_aspect('equal')
        
        # Draw nodes
        node_colors = {'gnb': 'red', 'user_uav': 'blue', 'relay_uav': 'green', 
                      'mesh_uav_1': 'orange', 'mesh_uav_2': 'purple'}
        node_markers = {'gnb': 's', 'user_uav': '^', 'relay_uav': '^', 
                       'mesh_uav_1': '^', 'mesh_uav_2': '^'}
        node_sizes = {'gnb': 300, 'user_uav': 200, 'relay_uav': 220, 
                     'mesh_uav_1': 200, 'mesh_uav_2': 200}
        
        for node, pos in self.positions.items():
            ax1.scatter(*pos[:2], s=node_sizes[node], c=node_colors[node], 
                       marker=node_markers[node], edgecolors='black', 
                       linewidth=2, zorder=5)
            
            # Add labels
            label = node.replace('_', ' ').title()
            if node == 'gnb':
                label += f"\n{self.antenna_config[node]} ant"
            else:
                label += f"\n{self.antenna_config[node]} ant"
            
            ax1.text(pos[0], pos[1]-15, label, ha='center', fontsize=9, fontweight='bold')
        
        # Draw links for cooperative topology
        gnb_pos = self.positions["gnb"]
        relay_pos = self.positions["relay_uav"] 
        mesh1_pos = self.positions["mesh_uav_1"]
        user_pos = self.positions["user_uav"]
        
        # Relay path
        ax1.plot([gnb_pos[0], relay_pos[0]], [gnb_pos[1], relay_pos[1]], 
                'g-', linewidth=3, alpha=0.7, label='Relay Path')
        ax1.plot([relay_pos[0], user_pos[0]], [relay_pos[1], user_pos[1]], 
                'g--', linewidth=3, alpha=0.7)
        
        # Mesh path
        ax1.plot([gnb_pos[0], mesh1_pos[0]], [gnb_pos[1], mesh1_pos[1]], 
                'orange', linewidth=2, alpha=0.7, label='Mesh Path')
        ax1.plot([mesh1_pos[0], user_pos[0]], [mesh1_pos[1], user_pos[1]], 
                'orange', linestyle='--', linewidth=2, alpha=0.7)
        
        # Direct path (dashed)
        ax1.plot([gnb_pos[0], user_pos[0]], [gnb_pos[1], user_pos[1]], 
                'r:', linewidth=2, alpha=0.5, label='Direct Path')
        
        ax1.set_xlabel('Position X [m]', fontweight='bold')
        ax1.set_ylabel('Position Y [m]', fontweight='bold')
        ax1.set_title('Red Multi-UAV con Topologías', fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. Throughput comparison
        if hasattr(self, 'topology_results'):
            topologies = list(self.topology_results.keys())
            throughputs = [self.topology_results[t]['total_throughput_mbps'] for t in topologies]
            
            colors = ['red', 'green', 'orange', 'purple', 'brown']
            bars = ax2.bar(topologies, throughputs, color=colors[:len(topologies)], alpha=0.7)
            
            ax2.set_ylabel('Throughput [Mbps]', fontweight='bold')
            ax2.set_title('Comparación de Throughput por Topología', fontweight='bold')
            ax2.tick_params(axis='x', rotation=45)
            ax2.grid(True, alpha=0.3)
            
            # Add value labels
            for bar, val in zip(bars, throughputs):
                ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 10,
                        f'{val:.0f}', ha='center', va='bottom', fontweight='bold')
        
        # 3. Delay vs Throughput analysis
        if hasattr(self, 'topology_results'):
            delays = [self.topology_results[t].get('end_to_end_delay_ms', 0) for t in topologies]
            
            scatter = ax3.scatter(delays, throughputs, c=throughputs, s=150, alpha=0.8, cmap='viridis')
            ax3.set_xlabel('End-to-End Delay [ms]', fontweight='bold')
            ax3.set_ylabel('Throughput [Mbps]', fontweight='bold') 
            ax3.set_title('Delay vs Throughput Trade-off', fontweight='bold')
            ax3.grid(True, alpha=0.3)
            
            # Add topology labels
            for i, topology in enumerate(topologies):
                ax3.annotate(topology, (delays[i], throughputs[i]),
                            xytext=(5, 5), textcoords='offset points', fontsize=8)
        
        # 4. Performance gain analysis
        if hasattr(self, 'topology_results') and 'direct' in self.topology_results:
            direct_throughput = self.topology_results['direct']['total_throughput_mbps']
            gains = [self.topology_results[t]['total_throughput_mbps'] / max(direct_throughput, 1) 
                    for t in topologies]
            
            bars = ax4.bar(topologies, gains, color=colors[:len(topologies)], alpha=0.7)
            ax4.set_ylabel('Ganancia vs Directo', fontweight='bold')
            ax4.set_title('Ganancia Relativa de Topologías', fontweight='bold')
            ax4.tick_params(axis='x', rotation=45)
            ax4.grid(True, alpha=0.3)
            ax4.axhline(y=1, color='red', linestyle='--', label='Direct baseline')
            ax4.legend()
            
            # Add gain labels
            for bar, val in zip(bars, gains):
                ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                        f'{val:.2f}x', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        print(f"✅ Visualización guardada: {save_path}")
    
    def generate_report(self):
        """Generar reporte completo"""
        print(f"\n" + "="*70)
        print("REPORTE ANÁLISIS MULTI-UAV Y RELAY")
        print("="*70)
        
        # System configuration
        print(f"\n📊 CONFIGURACIÓN DEL SISTEMA:")
        print(f"  📡 Frecuencia: {self.frequency_hz/1e9:.1f} GHz")
        print(f"  📶 Bandwidth: {self.bandwidth_hz/1e6:.0f} MHz")
        print(f"  🎯 SNR base: {self.base_snr_db} dB")
        print(f"  🛰️  Nodos desplegados: {len(self.positions)}")
        
        # Topology performance
        if hasattr(self, 'topology_results'):
            print(f"\n🔗 RESULTADOS DE TOPOLOGÍAS:")
            
            best_topology = max(self.topology_results.items(), 
                              key=lambda x: x[1]['total_throughput_mbps'])
            
            print(f"  🏆 Mejor topología: {best_topology[0]}")
            print(f"     • Throughput: {best_topology[1]['total_throughput_mbps']:.1f} Mbps")
            print(f"     • Descripción: {best_topology[1]['description']}")
            print(f"     • Hops: {best_topology[1]['hops']}")
            
            # Performance comparison
            direct_perf = self.topology_results.get('direct', {}).get('total_throughput_mbps', 0)
            print(f"\n  📈 Comparación vs enlace directo ({direct_perf:.1f} Mbps):")
            
            for topology, results in self.topology_results.items():
                if topology != 'direct':
                    gain = results['total_throughput_mbps'] / max(direct_perf, 1)
                    delay = results.get('end_to_end_delay_ms', 0)
                    print(f"     • {topology}: {gain:.2f}x ganancia, {delay}ms delay")
            
            # Cooperative analysis
            if 'cooperative' in self.topology_results:
                coop_results = self.topology_results['cooperative']
                print(f"\n  🤝 Análisis Cooperativo:")
                print(f"     • Throughput total: {coop_results['total_throughput_mbps']:.1f} Mbps")
                print(f"     • Ganancia diversidad: {coop_results.get('diversity_gain', 1):.2f}x")
                print(f"     • Eficiencia cooperación: {coop_results.get('cooperation_efficiency', 1):.2f}x")
        
        # Relay optimization
        if hasattr(self, 'optimization_results'):
            print(f"\n🎯 OPTIMIZACIÓN RELAY:")
            opt = self.optimization_results
            print(f"  📍 Posición original: {opt['original_position']}")
            print(f"  📍 Posición óptima: {opt['optimal_position']}")
            print(f"  📈 Mejora throughput: {opt['improvement_factor']:.2f}x")
            print(f"  🔍 Posiciones evaluadas: {len(opt['all_results'])}")
        
        # Key insights
        print(f"\n💡 INSIGHTS CLAVE:")
        
        if hasattr(self, 'topology_results'):
            # Multi-hop degradation
            hop_performance = {}
            for topology, results in self.topology_results.items():
                hops = results.get('hops', 1)
                throughput = results['total_throughput_mbps']
                hop_performance[hops] = hop_performance.get(hops, []) + [throughput]
            
            if len(hop_performance) > 1:
                print(f"  📊 Impacto multi-hop detectado:")
                for hops in sorted(hop_performance.keys()):
                    avg_perf = np.mean(hop_performance[hops])
                    print(f"     • {hops} hop(s): {avg_perf:.1f} Mbps promedio")
            
            # Cooperative vs single-path
            if 'cooperative' in self.topology_results and 'relay' in self.topology_results:
                coop_perf = self.topology_results['cooperative']['total_throughput_mbps']
                relay_perf = self.topology_results['relay']['total_throughput_mbps']
                coop_advantage = coop_perf / max(relay_perf, 1)
                
                if coop_advantage > 1.5:
                    print(f"  ✅ Cooperación muy efectiva: {coop_advantage:.2f}x mejor que relay único")
                elif coop_advantage > 1.1:
                    print(f"  ⚠️  Cooperación moderada: {coop_advantage:.2f}x mejor que relay único")
                else:
                    print(f"  ❌ Cooperación ineficiente: {coop_advantage:.2f}x vs relay único")
        
        # Recommendations
        print(f"\n🎯 RECOMENDACIONES:")
        
        if hasattr(self, 'topology_results'):
            best_topo_name = max(self.topology_results.items(), 
                               key=lambda x: x[1]['total_throughput_mbps'])[0]
            best_throughput = self.topology_results[best_topo_name]['total_throughput_mbps']
            
            print(f"  🏆 Topología recomendada: {best_topo_name}")
            print(f"     • Performance esperado: {best_throughput:.1f} Mbps")
            
            # Deployment recommendations
            if best_topo_name == 'cooperative':
                print(f"  💰 Sistema cooperativo justificado para aplicaciones críticas")
                print(f"  📡 Desplegar múltiples UAVs relay para redundancia")
            elif best_topo_name == 'relay':
                print(f"  💡 Relay simple suficiente - menor complejidad")
                print(f"  🎯 Optimizar posición relay para máximo throughput")
            elif best_topo_name == 'direct':
                print(f"  ⚡ Enlace directo óptimo - no requiere UAVs intermedios")
                print(f"  💲 Solución más económica")
            
            if hasattr(self, 'optimization_results'):
                if self.optimization_results['improvement_factor'] > 1.2:
                    print(f"  📍 Optimización posición relay crítica")
        
        print("="*70)

def run_practical_multi_uav_analysis():
    """Ejecutar análisis práctico completo"""
    
    # Initialize analysis
    analysis = PracticalMultiUAVAnalysis()
    
    # Run topology analysis  
    print("🔄 Analizando topologías de red...")
    topology_results = analysis.analyze_network_topologies()
    
    # Optimize relay positioning
    print("🔄 Optimizando posicionamiento relay...")
    optimization_results = analysis.optimize_relay_positioning()
    
    # Re-run topology analysis with optimized relay
    print("🔄 Re-analizando con relay optimizado...")
    final_topology_results = analysis.analyze_network_topologies()
    
    # Generate visualizations
    analysis.generate_network_visualization()
    
    # Generate comprehensive report
    analysis.generate_report()
    
    return analysis, final_topology_results, optimization_results

if __name__ == "__main__":
    analysis, topo_results, opt_results = run_practical_multi_uav_analysis()