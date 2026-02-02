"""
Multi-UAV & Relay Systems Analysis
Análisis de sistemas cooperativos multi-UAV con relay y redes mesh
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, ConnectionPatch
import sys
import os
from scipy.optimize import minimize_scalar
from itertools import combinations

# Importar configuraciones
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.system_config import *
from systems.basic_system import BasicUAVSystem

class MultiUAVRelayAnalysis:
    """
    Análisis completo de sistemas Multi-UAV con relay cooperativo
    """
    
    def __init__(self, gnb_position=[0, 0, 30]):
        """
        Inicializar análisis Multi-UAV
        
        Args:
            gnb_position: Posición del gNB [x, y, z]
        """
        self.gnb_position = gnb_position
        
        print("="*70)
        print("ANÁLISIS DE SISTEMAS MULTI-UAV Y RELAY")
        print("="*70)
        
        # System parameters
        self.bandwidth_hz = 100e6  # 100 MHz
        self.frequency_hz = 3.5e9  # 3.5 GHz
        
        # UAV configurations (from Phase 4 optimal)
        self.uav_configs = {
            "user_uav": {
                "position": [150, 150, 50],  # User UAV (distant from gNB)
                "antennas": 4,              # 2x2 array
                "role": "user"
            },
            "relay_uav": {
                "position": [75, 75, 60],   # Relay UAV (intermediate position)
                "antennas": 16,             # 4x4 array (better for relay)
                "role": "relay"
            },
            "mesh_uav_1": {
                "position": [100, 50, 55],  # Mesh UAV 1
                "antennas": 4,              # 2x2 array
                "role": "mesh_node"
            },
            "mesh_uav_2": {
                "position": [50, 100, 55],  # Mesh UAV 2
                "antennas": 4,              # 2x2 array
                "role": "mesh_node"
            }
        }
        
        # Network topologies to analyze
        self.topologies = {
            "direct": "gNB → User UAV (directo)",
            "relay": "gNB → Relay UAV → User UAV",
            "mesh_2hop": "gNB → Mesh UAV 1 → User UAV",
            "mesh_3hop": "gNB → Mesh UAV 1 → Mesh UAV 2 → User UAV",
            "cooperative": "gNB → [Relay + Mesh] → User UAV (cooperativo)"
        }
        
        # Relay strategies
        self.relay_strategies = {
            "amplify_forward": {"description": "Amplify & Forward", "snr_penalty_db": 3},
            "decode_forward": {"description": "Decode & Forward", "snr_penalty_db": 1},
            "compress_forward": {"description": "Compress & Forward", "snr_penalty_db": 2}
        }
        
        print(f"📡 gNB posición: {gnb_position}")
        print(f"🛰️  UAVs configurados: {len(self.uav_configs)}")
        print(f"🔗 Topologías: {len(self.topologies)}")
        print(f"📶 Estrategias relay: {len(self.relay_strategies)}")
        
        # Results storage
        self.topology_results = {}
        self.relay_optimization_results = {}
        self.cooperative_results = {}
    
    def calculate_link_performance(self, tx_pos, rx_pos, tx_antennas, rx_antennas, snr_db=20):
        """
        Calcular performance de un enlace punto a punto
        
        Args:
            tx_pos: Posición transmisor [x, y, z]
            rx_pos: Posición receptor [x, y, z]  
            tx_antennas: Número de antenas TX
            rx_antennas: Número de antenas RX
            snr_db: SNR en dB
            
        Returns:
            dict: Métricas del enlace
        """
        # Calculate distance and path loss
        distance = np.sqrt(sum((np.array(tx_pos) - np.array(rx_pos))**2))
        
        # Free space path loss (simplified)
        fspl_db = 20 * np.log10(distance) + 20 * np.log10(self.frequency_hz/1e9) + 32.45
        
        # Array gain
        array_gain_db = 10 * np.log10(tx_antennas) + 10 * np.log10(rx_antennas)
        
        # Effective SNR
        effective_snr_db = snr_db + array_gain_db - fspl_db
        effective_snr_linear = 10**(effective_snr_db/10)
        
        # MIMO streams
        spatial_streams = min(tx_antennas, rx_antennas)
        
        # Shannon capacity
        if effective_snr_linear > 0:
            spectral_efficiency = spatial_streams * np.log2(1 + effective_snr_linear / spatial_streams)
            throughput_mbps = spectral_efficiency * self.bandwidth_hz / 1e6
        else:
            spectral_efficiency = 0
            throughput_mbps = 0
        
        # LoS probability (simplified - based on elevation angle)
        height_diff = abs(tx_pos[2] - rx_pos[2])
        horizontal_dist = np.sqrt((tx_pos[0] - rx_pos[0])**2 + (tx_pos[1] - rx_pos[1])**2)
        elevation_angle = np.arctan(height_diff / horizontal_dist) * 180 / np.pi if horizontal_dist > 0 else 90
        los_probability = min(1.0, elevation_angle / 30)  # Simplified model
        
        return {
            'distance_m': distance,
            'path_loss_db': fspl_db,
            'array_gain_db': array_gain_db,
            'effective_snr_db': effective_snr_db,
            'spatial_streams': spatial_streams,
            'spectral_efficiency': spectral_efficiency,
            'throughput_mbps': throughput_mbps,
            'los_probability': los_probability,
            'elevation_angle': elevation_angle
        }
    
    def analyze_network_topologies(self, snr_db=20):
        """Analizar diferentes topologías de red"""
        print(f"\n🔗 ANÁLISIS DE TOPOLOGÍAS DE RED")
        print(f"📶 SNR base: {snr_db} dB")
        
        results = {}
        gnb_antennas = 64  # From Phase 4 optimal
        
        for topology, description in self.topologies.items():
            print(f"\n🔧 Topología: {topology}")
            print(f"   Descripción: {description}")
            
            if topology == "direct":
                # Direct link: gNB → User UAV
                user_pos = self.uav_configs["user_uav"]["position"]
                user_ant = self.uav_configs["user_uav"]["antennas"]
                
                link_perf = self.calculate_link_performance(
                    self.gnb_position, user_pos, gnb_antennas, user_ant, snr_db
                )
                
                results[topology] = {
                    'total_throughput_mbps': link_perf['throughput_mbps'],
                    'end_to_end_spectral_efficiency': link_perf['spectral_efficiency'],
                    'total_hops': 1,
                    'links': [link_perf],
                    'bottleneck_throughput': link_perf['throughput_mbps'],
                    'description': description
                }
                
            elif topology == "relay":
                # Relay link: gNB → Relay → User UAV
                relay_pos = self.uav_configs["relay_uav"]["position"]
                relay_ant = self.uav_configs["relay_uav"]["antennas"]
                user_pos = self.uav_configs["user_uav"]["position"]
                user_ant = self.uav_configs["user_uav"]["antennas"]
                
                # First hop: gNB → Relay
                link1 = self.calculate_link_performance(
                    self.gnb_position, relay_pos, gnb_antennas, relay_ant, snr_db
                )
                
                # Second hop: Relay → User UAV (with relay penalty)
                link2 = self.calculate_link_performance(
                    relay_pos, user_pos, relay_ant, user_ant, snr_db - 2  # Relay processing penalty
                )
                
                # Bottleneck determines throughput
                bottleneck_throughput = min(link1['throughput_mbps'], link2['throughput_mbps'])
                
                results[topology] = {
                    'total_throughput_mbps': bottleneck_throughput,
                    'end_to_end_spectral_efficiency': bottleneck_throughput * 1e6 / self.bandwidth_hz,
                    'total_hops': 2,
                    'links': [link1, link2],
                    'bottleneck_throughput': bottleneck_throughput,
                    'relay_gain': bottleneck_throughput / results.get('direct', {}).get('total_throughput_mbps', 1) if 'direct' in results else 1,
                    'description': description
                }
                
            elif topology == "mesh_2hop":
                # 2-hop mesh: gNB → Mesh UAV 1 → User UAV
                mesh1_pos = self.uav_configs["mesh_uav_1"]["position"]
                mesh1_ant = self.uav_configs["mesh_uav_1"]["antennas"]
                user_pos = self.uav_configs["user_uav"]["position"]
                user_ant = self.uav_configs["user_uav"]["antennas"]
                
                link1 = self.calculate_link_performance(
                    self.gnb_position, mesh1_pos, gnb_antennas, mesh1_ant, snr_db
                )
                link2 = self.calculate_link_performance(
                    mesh1_pos, user_pos, mesh1_ant, user_ant, snr_db - 1
                )
                
                bottleneck_throughput = min(link1['throughput_mbps'], link2['throughput_mbps'])
                
                results[topology] = {
                    'total_throughput_mbps': bottleneck_throughput,
                    'end_to_end_spectral_efficiency': bottleneck_throughput * 1e6 / self.bandwidth_hz,
                    'total_hops': 2,
                    'links': [link1, link2],
                    'bottleneck_throughput': bottleneck_throughput,
                    'description': description
                }
                
            elif topology == "mesh_3hop":
                # 3-hop mesh: gNB → Mesh UAV 1 → Mesh UAV 2 → User UAV
                mesh1_pos = self.uav_configs["mesh_uav_1"]["position"]
                mesh1_ant = self.uav_configs["mesh_uav_1"]["antennas"]
                mesh2_pos = self.uav_configs["mesh_uav_2"]["position"]
                mesh2_ant = self.uav_configs["mesh_uav_2"]["antennas"]
                user_pos = self.uav_configs["user_uav"]["position"]
                user_ant = self.uav_configs["user_uav"]["antennas"]
                
                link1 = self.calculate_link_performance(
                    self.gnb_position, mesh1_pos, gnb_antennas, mesh1_ant, snr_db
                )
                link2 = self.calculate_link_performance(
                    mesh1_pos, mesh2_pos, mesh1_ant, mesh2_ant, snr_db - 1
                )
                link3 = self.calculate_link_performance(
                    mesh2_pos, user_pos, mesh2_ant, user_ant, snr_db - 2
                )
                
                bottleneck_throughput = min(link1['throughput_mbps'], link2['throughput_mbps'], link3['throughput_mbps'])
                
                results[topology] = {
                    'total_throughput_mbps': bottleneck_throughput,
                    'end_to_end_spectral_efficiency': bottleneck_throughput * 1e6 / self.bandwidth_hz,
                    'total_hops': 3,
                    'links': [link1, link2, link3],
                    'bottleneck_throughput': bottleneck_throughput,
                    'description': description
                }
                
            elif topology == "cooperative":
                # Cooperative: Both relay and mesh help user UAV
                relay_pos = self.uav_configs["relay_uav"]["position"]
                relay_ant = self.uav_configs["relay_uav"]["antennas"]
                mesh1_pos = self.uav_configs["mesh_uav_1"]["position"]
                mesh1_ant = self.uav_configs["mesh_uav_1"]["antennas"]
                user_pos = self.uav_configs["user_uav"]["position"]
                user_ant = self.uav_configs["user_uav"]["antennas"]
                
                # Multiple paths to user UAV
                relay_link1 = self.calculate_link_performance(
                    self.gnb_position, relay_pos, gnb_antennas, relay_ant, snr_db
                )
                relay_link2 = self.calculate_link_performance(
                    relay_pos, user_pos, relay_ant, user_ant, snr_db - 2
                )
                
                mesh_link1 = self.calculate_link_performance(
                    self.gnb_position, mesh1_pos, gnb_antennas, mesh1_ant, snr_db
                )
                mesh_link2 = self.calculate_link_performance(
                    mesh1_pos, user_pos, mesh1_ant, user_ant, snr_db - 1
                )
                
                # Cooperative combining (simplified)
                relay_throughput = min(relay_link1['throughput_mbps'], relay_link2['throughput_mbps'])
                mesh_throughput = min(mesh_link1['throughput_mbps'], mesh_link2['throughput_mbps'])
                
                # Diversity combining gain (conservative estimate)
                cooperative_gain = 1.3  # 30% gain from diversity
                total_throughput = (relay_throughput + mesh_throughput) * cooperative_gain
                
                results[topology] = {
                    'total_throughput_mbps': total_throughput,
                    'end_to_end_spectral_efficiency': total_throughput * 1e6 / self.bandwidth_hz,
                    'total_hops': 2,  # Average
                    'links': [relay_link1, relay_link2, mesh_link1, mesh_link2],
                    'bottleneck_throughput': max(relay_throughput, mesh_throughput),
                    'relay_contribution': relay_throughput,
                    'mesh_contribution': mesh_throughput,
                    'cooperative_gain': cooperative_gain,
                    'description': description
                }
            
            print(f"   ✅ Throughput: {results[topology]['total_throughput_mbps']:.1f} Mbps")
            print(f"   ✅ Hops: {results[topology]['total_hops']}")
            print(f"   ✅ Spectral efficiency: {results[topology]['end_to_end_spectral_efficiency']:.2f} bits/s/Hz")
        
        self.topology_results = results
        return results
    
    def optimize_relay_position(self, optimization_range=100, num_positions=15):
        """Optimizar posición del UAV relay"""
        print(f"\n🎯 OPTIMIZACIÓN DE POSICIÓN RELAY")
        print(f"📏 Rango optimización: ±{optimization_range}m")
        print(f"🔍 Posiciones evaluadas: {num_positions}²")
        
        user_pos = self.uav_configs["user_uav"]["position"]
        user_ant = self.uav_configs["user_uav"]["antennas"]
        relay_ant = self.uav_configs["relay_uav"]["antennas"]
        gnb_antennas = 64
        
        # Generate grid of potential relay positions
        base_x, base_y = self.uav_configs["relay_uav"]["position"][:2]
        x_positions = np.linspace(base_x - optimization_range, base_x + optimization_range, num_positions)
        y_positions = np.linspace(base_y - optimization_range, base_y + optimization_range, num_positions)
        
        best_performance = 0
        best_position = None
        optimization_results = []
        
        for x in x_positions:
            for y in y_positions:
                relay_pos = [x, y, 60]  # Fixed height
                
                # Calculate relay performance
                link1 = self.calculate_link_performance(
                    self.gnb_position, relay_pos, gnb_antennas, relay_ant, 20
                )
                link2 = self.calculate_link_performance(
                    relay_pos, user_pos, relay_ant, user_ant, 18
                )
                
                throughput = min(link1['throughput_mbps'], link2['throughput_mbps'])
                
                optimization_results.append({
                    'position': relay_pos.copy(),
                    'throughput_mbps': throughput,
                    'link1_performance': link1,
                    'link2_performance': link2
                })
                
                if throughput > best_performance:
                    best_performance = throughput
                    best_position = relay_pos.copy()
        
        # Compare with direct link
        direct_link = self.calculate_link_performance(
            self.gnb_position, user_pos, gnb_antennas, user_ant, 20
        )
        
        improvement = best_performance / direct_link['throughput_mbps']
        
        print(f"   ✅ Mejor posición: {best_position}")
        print(f"   ✅ Throughput óptimo: {best_performance:.1f} Mbps")
        print(f"   ✅ Mejora vs directo: {improvement:.2f}x")
        print(f"   ✅ Throughput directo: {direct_link['throughput_mbps']:.1f} Mbps")
        
        self.relay_optimization_results = {
            'best_position': best_position,
            'best_throughput': best_performance,
            'improvement_factor': improvement,
            'direct_throughput': direct_link['throughput_mbps'],
            'all_positions': optimization_results,
            'grid_size': num_positions
        }
        
        return self.relay_optimization_results
    
    def analyze_relay_strategies(self, snr_db=20):
        """Analizar diferentes estrategias de relay"""
        print(f"\n📡 ANÁLISIS DE ESTRATEGIAS RELAY")
        
        results = {}
        
        # Use optimal relay position if available
        if hasattr(self, 'relay_optimization_results') and self.relay_optimization_results:
            relay_pos = self.relay_optimization_results['best_position']
        else:
            relay_pos = self.uav_configs["relay_uav"]["position"]
        
        user_pos = self.uav_configs["user_uav"]["position"]
        gnb_antennas = 64
        relay_ant = self.uav_configs["relay_uav"]["antennas"]
        user_ant = self.uav_configs["user_uav"]["antennas"]
        
        for strategy, params in self.relay_strategies.items():
            print(f"\n🔧 Estrategia: {strategy}")
            print(f"   Descripción: {params['description']}")
            print(f"   Penalty SNR: {params['snr_penalty_db']} dB")
            
            # First hop: gNB → Relay
            link1 = self.calculate_link_performance(
                self.gnb_position, relay_pos, gnb_antennas, relay_ant, snr_db
            )
            
            # Second hop: Relay → User (with strategy penalty)
            effective_snr = snr_db - params['snr_penalty_db']
            link2 = self.calculate_link_performance(
                relay_pos, user_pos, relay_ant, user_ant, effective_snr
            )
            
            bottleneck_throughput = min(link1['throughput_mbps'], link2['throughput_mbps'])
            
            results[strategy] = {
                'throughput_mbps': bottleneck_throughput,
                'snr_penalty_db': params['snr_penalty_db'],
                'description': params['description'],
                'link1': link1,
                'link2': link2,
                'bottleneck_link': 'link1' if link1['throughput_mbps'] < link2['throughput_mbps'] else 'link2'
            }
            
            print(f"   ✅ Throughput: {bottleneck_throughput:.1f} Mbps")
            print(f"   ✅ Link 1: {link1['throughput_mbps']:.1f} Mbps")
            print(f"   ✅ Link 2: {link2['throughput_mbps']:.1f} Mbps")
            print(f"   ✅ Bottleneck: {results[strategy]['bottleneck_link']}")
        
        # Find best strategy
        best_strategy = max(results.items(), key=lambda x: x[1]['throughput_mbps'])
        print(f"\n🏆 Mejor estrategia: {best_strategy[0]}")
        print(f"   📈 Throughput: {best_strategy[1]['throughput_mbps']:.1f} Mbps")
        
        return results
    
    def generate_topology_visualization(self, save_path="./UAV/outputs/multi_uav_topology.png"):
        """Generar visualización de topologías de red"""
        if not self.topology_results:
            print("❌ No hay resultados de topología para visualizar.")
            return
        
        print(f"\n🗺️  GENERANDO VISUALIZACIÓN TOPOLOGÍAS...")
        
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(18, 14))
        
        # 1. Network topology map
        ax1.set_xlim(-50, 200)
        ax1.set_ylim(-50, 200)
        ax1.set_aspect('equal')
        
        # Draw gNB
        ax1.scatter(*self.gnb_position[:2], s=300, c='red', marker='s', 
                   edgecolors='black', linewidth=2, label='gNB', zorder=5)
        ax1.text(self.gnb_position[0], self.gnb_position[1]-15, 'gNB\n64 ant', 
                ha='center', fontweight='bold')
        
        # Draw UAVs
        colors = {'user': 'blue', 'relay': 'green', 'mesh_node': 'orange'}
        for uav_name, config in self.uav_configs.items():
            pos = config['position']
            color = colors[config['role']]
            ax1.scatter(*pos[:2], s=200, c=color, marker='^', 
                       edgecolors='black', linewidth=1, zorder=4)
            ax1.text(pos[0], pos[1]-12, f"{uav_name.replace('_', ' ').title()}\n{config['antennas']} ant", 
                    ha='center', fontsize=8, fontweight='bold')
        
        # Draw links for relay topology
        if 'relay' in self.topology_results:
            relay_pos = self.uav_configs["relay_uav"]["position"]
            user_pos = self.uav_configs["user_uav"]["position"]
            
            # gNB → Relay
            ax1.plot([self.gnb_position[0], relay_pos[0]], 
                    [self.gnb_position[1], relay_pos[1]], 
                    'g-', linewidth=2, alpha=0.7)
            
            # Relay → User
            ax1.plot([relay_pos[0], user_pos[0]], 
                    [relay_pos[1], user_pos[1]], 
                    'g--', linewidth=2, alpha=0.7)
        
        ax1.set_xlabel('Position X [m]', fontweight='bold')
        ax1.set_ylabel('Position Y [m]', fontweight='bold')
        ax1.set_title('Topología de Red Multi-UAV', fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # 2. Throughput comparison
        topologies = list(self.topology_results.keys())
        throughputs = [self.topology_results[t]['total_throughput_mbps'] for t in topologies]
        
        bars = ax2.bar(topologies, throughputs, color=['red', 'green', 'orange', 'purple', 'brown'][:len(topologies)])
        ax2.set_ylabel('Throughput [Mbps]', fontweight='bold')
        ax2.set_title('Comparación de Throughput por Topología', fontweight='bold')
        ax2.tick_params(axis='x', rotation=45)
        ax2.grid(True, alpha=0.3)
        
        # Add value labels
        for bar, val in zip(bars, throughputs):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 50,
                    f'{val:.0f}', ha='center', va='bottom', fontweight='bold')
        
        # 3. Hops vs Performance
        hops = [self.topology_results[t]['total_hops'] for t in topologies]
        spectral_effs = [self.topology_results[t]['end_to_end_spectral_efficiency'] for t in topologies]
        
        scatter = ax3.scatter(hops, spectral_effs, c=throughputs, s=150, alpha=0.8, cmap='viridis')
        ax3.set_xlabel('Número de Hops', fontweight='bold')
        ax3.set_ylabel('Eficiencia Espectral [bits/s/Hz]', fontweight='bold')
        ax3.set_title('Hops vs Eficiencia Espectral', fontweight='bold')
        ax3.grid(True, alpha=0.3)
        plt.colorbar(scatter, ax=ax3, label='Throughput [Mbps]')
        
        # Add topology labels
        for i, topology in enumerate(topologies):
            ax3.annotate(topology, (hops[i], spectral_effs[i]),
                        xytext=(5, 5), textcoords='offset points', fontsize=8)
        
        # 4. Gain analysis
        if 'direct' in self.topology_results:
            direct_throughput = self.topology_results['direct']['total_throughput_mbps']
            gains = [self.topology_results[t]['total_throughput_mbps'] / direct_throughput 
                    for t in topologies]
            
            bars = ax4.bar(topologies, gains, color=['red', 'green', 'orange', 'purple', 'brown'][:len(topologies)])
            ax4.set_ylabel('Ganancia vs Directo', fontweight='bold')
            ax4.set_title('Ganancia de Topologías vs Enlace Directo', fontweight='bold')
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
    
    def generate_relay_optimization_plot(self, save_path="./UAV/outputs/relay_optimization.png"):
        """Generar gráfico de optimización de relay"""
        if not self.relay_optimization_results:
            print("❌ No hay resultados de optimización relay.")
            return
        
        print(f"\n🎯 GENERANDO GRÁFICO OPTIMIZACIÓN RELAY...")
        
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        # Extract optimization data
        positions = self.relay_optimization_results['all_positions']
        grid_size = self.relay_optimization_results['grid_size']
        
        x_coords = [p['position'][0] for p in positions]
        y_coords = [p['position'][1] for p in positions]
        throughputs = [p['throughput_mbps'] for p in positions]
        
        # Reshape for contour plot
        X = np.array(x_coords).reshape(grid_size, grid_size)
        Y = np.array(y_coords).reshape(grid_size, grid_size)
        Z = np.array(throughputs).reshape(grid_size, grid_size)
        
        # Create figure
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
        
        # 1. Optimization heatmap
        contour = ax1.contourf(X, Y, Z, levels=20, cmap='viridis')
        ax1.set_xlabel('Posición X [m]', fontweight='bold')
        ax1.set_ylabel('Posición Y [m]', fontweight='bold')
        ax1.set_title('Optimización de Posición Relay UAV', fontweight='bold')
        
        # Mark important positions
        ax1.scatter(*self.gnb_position[:2], s=200, c='red', marker='s', 
                   edgecolors='white', linewidth=2, label='gNB', zorder=5)
        
        user_pos = self.uav_configs["user_uav"]["position"]
        ax1.scatter(*user_pos[:2], s=200, c='blue', marker='^', 
                   edgecolors='white', linewidth=2, label='User UAV', zorder=5)
        
        best_pos = self.relay_optimization_results['best_position']
        ax1.scatter(*best_pos[:2], s=200, c='yellow', marker='*', 
                   edgecolors='black', linewidth=2, label='Optimal Relay', zorder=5)
        
        original_pos = self.uav_configs["relay_uav"]["position"]
        ax1.scatter(*original_pos[:2], s=100, c='orange', marker='o', 
                   edgecolors='black', linewidth=1, label='Original Relay', zorder=4)
        
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        plt.colorbar(contour, ax=ax1, label='Throughput [Mbps]')
        
        # 2. Performance improvement
        original_perf = min([p['throughput_mbps'] for p in positions 
                           if abs(p['position'][0] - original_pos[0]) < 5 and 
                              abs(p['position'][1] - original_pos[1]) < 5] + [0])
        
        best_perf = self.relay_optimization_results['best_throughput']
        direct_perf = self.relay_optimization_results['direct_throughput']
        
        categories = ['Direct\n(no relay)', 'Original\nRelay', 'Optimized\nRelay']
        performances = [direct_perf, original_perf, best_perf]
        colors = ['red', 'orange', 'green']
        
        bars = ax2.bar(categories, performances, color=colors, alpha=0.7)
        ax2.set_ylabel('Throughput [Mbps]', fontweight='bold')
        ax2.set_title('Mejora de Performance con Relay Optimizado', fontweight='bold')
        ax2.grid(True, alpha=0.3)
        
        # Add improvement percentages
        for i, (bar, val) in enumerate(zip(bars, performances)):
            if i > 0:
                improvement = ((val - direct_perf) / direct_perf) * 100
                ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 50,
                        f'+{improvement:.0f}%', ha='center', va='bottom', 
                        fontweight='bold', color='green')
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 10,
                    f'{val:.0f} Mbps', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        print(f"✅ Gráfico optimización guardado: {save_path}")
    
    def generate_report(self):
        """Generar reporte completo"""
        print(f"\n" + "="*70)
        print("REPORTE ANÁLISIS MULTI-UAV Y RELAY")
        print("="*70)
        
        # Configuration summary
        print(f"\n📊 CONFIGURACIÓN DEL SISTEMA:")
        print(f"  📡 gNB: {self.gnb_position} (64 antenas)")
        print(f"  🛰️  UAVs desplegados: {len(self.uav_configs)}")
        print(f"  📶 Bandwidth: {self.bandwidth_hz/1e6:.0f} MHz")
        print(f"  🔗 Topologías analizadas: {len(self.topologies)}")
        
        # Topology results
        if self.topology_results:
            print(f"\n🔗 RESULTADOS TOPOLOGÍAS:")
            
            # Best topology
            best_topology = max(self.topology_results.items(), 
                              key=lambda x: x[1]['total_throughput_mbps'])
            
            print(f"  🏆 Mejor topología: {best_topology[0]}")
            print(f"     • Descripción: {best_topology[1]['description']}")
            print(f"     • Throughput: {best_topology[1]['total_throughput_mbps']:.1f} Mbps")
            print(f"     • Hops: {best_topology[1]['total_hops']}")
            print(f"     • Eficiencia: {best_topology[1]['end_to_end_spectral_efficiency']:.2f} bits/s/Hz")
            
            # Compare all topologies
            if 'direct' in self.topology_results:
                direct_perf = self.topology_results['direct']['total_throughput_mbps']
                print(f"\n  📈 Comparación vs enlace directo:")
                for topology, results in self.topology_results.items():
                    if topology != 'direct':
                        gain = results['total_throughput_mbps'] / direct_perf
                        print(f"     • {topology}: {gain:.2f}x ({results['total_throughput_mbps']:.1f} Mbps)")
        
        # Relay optimization results
        if self.relay_optimization_results:
            print(f"\n🎯 OPTIMIZACIÓN RELAY:")
            print(f"  📍 Posición óptima: {self.relay_optimization_results['best_position']}")
            print(f"  📈 Throughput óptimo: {self.relay_optimization_results['best_throughput']:.1f} Mbps")
            print(f"  🚀 Mejora vs directo: {self.relay_optimization_results['improvement_factor']:.2f}x")
            print(f"  🔍 Posiciones evaluadas: {len(self.relay_optimization_results['all_positions'])}")
        
        # Key insights
        print(f"\n💡 INSIGHTS CLAVE:")
        
        if self.topology_results:
            cooperative_available = 'cooperative' in self.topology_results
            relay_available = 'relay' in self.topology_results
            
            if cooperative_available and relay_available:
                coop_perf = self.topology_results['cooperative']['total_throughput_mbps']
                relay_perf = self.topology_results['relay']['total_throughput_mbps']
                coop_advantage = coop_perf / relay_perf
                
                if coop_advantage > 1.2:
                    print(f"  ✅ Cooperación multi-UAV muy efectiva ({coop_advantage:.2f}x mejor que relay simple)")
                else:
                    print(f"  ⚠️  Cooperación multi-UAV marginal ({coop_advantage:.2f}x vs relay simple)")
            
            # Hops analysis
            max_hops = max([r['total_hops'] for r in self.topology_results.values()])
            if max_hops > 2:
                print(f"  ⚠️  Multi-hop degradation observable (hasta {max_hops} hops)")
            else:
                print(f"  ✅ Topologías eficientes (máximo {max_hops} hops)")
        
        print(f"\n🎯 RECOMENDACIONES:")
        
        if self.topology_results:
            best_topo_name = max(self.topology_results.items(), 
                               key=lambda x: x[1]['total_throughput_mbps'])[0]
            print(f"  📡 Implementar topología: {best_topo_name}")
            
            if self.relay_optimization_results:
                print(f"  📍 Posicionar relay en: {self.relay_optimization_results['best_position']}")
            
            if 'cooperative' in self.topology_results:
                coop_perf = self.topology_results['cooperative']['total_throughput_mbps']
                if coop_perf > 5000:  # High performance threshold
                    print(f"  🚀 Sistema cooperativo recomendado para aplicaciones críticas")
                else:
                    print(f"  💰 Evaluar cost/benefit de cooperación multi-UAV")
        
        print("="*70)

def run_complete_multi_uav_analysis():
    """Ejecutar análisis completo Multi-UAV"""
    # Initialize analysis
    analysis = MultiUAVRelayAnalysis()
    
    # Run topology analysis
    print("🔄 Analizando topologías de red...")
    topology_results = analysis.analyze_network_topologies()
    
    # Optimize relay position
    print("🔄 Optimizando posición relay...")
    optimization_results = analysis.optimize_relay_position()
    
    # Analyze relay strategies
    print("🔄 Analizando estrategias relay...")
    strategy_results = analysis.analyze_relay_strategies()
    
    # Generate visualizations
    analysis.generate_topology_visualization()
    analysis.generate_relay_optimization_plot()
    
    # Generate report
    analysis.generate_report()
    
    return analysis, topology_results, optimization_results, strategy_results

if __name__ == "__main__":
    analysis, topo_results, opt_results, strat_results = run_complete_multi_uav_analysis()