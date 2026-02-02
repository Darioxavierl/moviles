"""
Interference Analysis GUI - Análisis de Interferencia Multi-UAV
Análisis de interferencia entre múltiples UAVs y optimización SINR
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from matplotlib.colors import LinearSegmentedColormap
import os
import json
from scipy.spatial.distance import pdist, squareform

class InterferenceAnalysisGUI:
    """Análisis de interferencia multi-UAV para GUI"""
    
    def __init__(self, output_dir="outputs"):
        """Inicializar análisis de interferencia GUI"""
        
        print("="*60)
        print("INTERFERENCE ANALYSIS GUI - Analisis Interferencia Multi-UAV")
        print("="*60)
        
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Munich scenario configuration
        self.munich_config = {
            'num_uavs': 8,          # Number of UAVs in scenario
            'num_scenarios': 5,      # Different interference scenarios
            'area_range': 300,       # ±300m analysis area
            'fixed_height': 40,      # From Phase 2 optimal height
            'min_separation': 50,    # Minimum UAV separation (meters)
            'frequency_ghz': 3.5,
            'bandwidth_mhz': 100,
            'subcarrier_spacing_khz': 30,
            'resource_blocks': 273,  # 100MHz / 30kHz spacing
            'gnb_position': [300, 200, 50],  # gNB sobre edificio más alto
            'gnb_power_dbm': 43,
            'gnb_antennas': 64,
            'uav_antennas': 4,
            'noise_figure_db': 7,
            'thermal_noise_dbm': -104  # 100MHz bandwidth
        }
        
        # Interference scenarios
        self.interference_scenarios = {
            'low_density': {'name': 'Baja Densidad', 'uav_count': 3, 'area_factor': 1.0},
            'medium_density': {'name': 'Densidad Media', 'uav_count': 5, 'area_factor': 0.8},
            'high_density': {'name': 'Alta Densidad', 'uav_count': 8, 'area_factor': 0.6},
            'clustered': {'name': 'UAVs Agrupados', 'uav_count': 6, 'area_factor': 0.4},
            'distributed': {'name': 'UAVs Distribuidos', 'uav_count': 7, 'area_factor': 1.2}
        }
        
        # System configuration
        self.system_config = {
            'scenario': 'Munich Multi-UAV Interference 5G NR',
            'max_uavs': self.munich_config['num_uavs'],
            'interference_scenarios': len(self.interference_scenarios),
            'resource_blocks': self.munich_config['resource_blocks'],
            'bandwidth': f"{self.munich_config['bandwidth_mhz']} MHz",
            'analysis_area': f"±{self.munich_config['area_range']}m"
        }
        
        print("Interference Analysis GUI inicializado")
        print(f"Directorio de salida: {output_dir}")
        print(f"Maximo UAVs: {self.munich_config['num_uavs']}")
        print(f"Escenarios: {len(self.interference_scenarios)}")
        
    def generate_uav_positions(self, scenario_key, progress_callback=None):
        """Generar posiciones de UAVs según escenario"""
        
        if progress_callback:
            progress_callback(f"Generando posiciones UAV para {scenario_key}...")
        
        scenario = self.interference_scenarios[scenario_key]
        num_uavs = scenario['uav_count']
        area_factor = scenario['area_factor']
        area_range = self.munich_config['area_range'] * area_factor
        fixed_height = self.munich_config['fixed_height']
        min_sep = self.munich_config['min_separation']
        
        # Generate positions with minimum separation constraint
        uav_positions = []
        max_attempts = 1000
        
        for i in range(num_uavs):
            attempts = 0
            while attempts < max_attempts:
                if scenario_key == 'clustered':
                    # Clustered around 2-3 centers
                    cluster_centers = [[-100, -100], [150, 100], [50, -150]]
                    center_idx = i % len(cluster_centers)
                    cluster_center = cluster_centers[center_idx]
                    x = cluster_center[0] + np.random.uniform(-50, 50)
                    y = cluster_center[1] + np.random.uniform(-50, 50)
                elif scenario_key == 'distributed':
                    # Maximum spread distribution
                    angle = 2 * np.pi * i / num_uavs + np.random.uniform(-0.3, 0.3)
                    radius = area_range * (0.6 + 0.4 * np.random.random())
                    x = radius * np.cos(angle)
                    y = radius * np.sin(angle)
                else:
                    # Random within area
                    x = np.random.uniform(-area_range, area_range)
                    y = np.random.uniform(-area_range, area_range)
                
                # Height variation
                z = fixed_height + np.random.uniform(-10, 10)
                
                new_pos = [x, y, z]
                
                # Check minimum separation
                valid_position = True
                for existing_pos in uav_positions:
                    distance = np.linalg.norm(np.array(new_pos[:2]) - np.array(existing_pos[:2]))
                    if distance < min_sep:
                        valid_position = False
                        break
                
                if valid_position:
                    uav_positions.append(new_pos)
                    break
                
                attempts += 1
            
            if attempts >= max_attempts:
                # Force position if can't find valid one
                angle = 2 * np.pi * i / num_uavs
                radius = area_range * 0.7
                x = radius * np.cos(angle)
                y = radius * np.sin(angle)
                z = fixed_height
                uav_positions.append([x, y, z])
        
        return np.array(uav_positions)
    
    def calculate_interference_matrix(self, uav_positions, progress_callback=None):
        """Calcular matriz de interferencia entre UAVs"""
        
        if progress_callback:
            progress_callback("Calculando matriz de interferencia...")
        
        num_uavs = len(uav_positions)
        gnb_pos = np.array(self.munich_config['gnb_position'])
        
        # Distance matrices
        uav_to_gnb_distances = np.array([np.linalg.norm(pos - gnb_pos) for pos in uav_positions])
        uav_distances = squareform(pdist(uav_positions))
        
        # Path loss to gNB (desired signal)
        fspl_to_gnb = 32.4 + 20 * np.log10(uav_to_gnb_distances) + 20 * np.log10(self.munich_config['frequency_ghz'])
        
        # LOS probability and additional losses
        los_prob_gnb = self._calculate_los_probability_array(uav_positions, gnb_pos)
        nlos_loss_gnb = 20 * (1 - los_prob_gnb)  # NLoS penalty
        total_path_loss_gnb = fspl_to_gnb + nlos_loss_gnb
        
        # Received signal power from gNB
        rx_power_gnb = self.munich_config['gnb_power_dbm'] - total_path_loss_gnb
        
        # Inter-UAV interference calculation
        interference_matrix = np.zeros((num_uavs, num_uavs))
        
        for i in range(num_uavs):
            for j in range(num_uavs):
                if i != j:
                    # Distance between UAVs
                    distance_ij = uav_distances[i, j]
                    
                    # UAV-to-UAV path loss (simplified)
                    if distance_ij > 0:
                        # Free space path loss between UAVs
                        fspl_uav = 32.4 + 20 * np.log10(distance_ij) + 20 * np.log10(self.munich_config['frequency_ghz'])
                        
                        # Simplified UAV transmit power (lower than gNB)
                        uav_tx_power = 23  # dBm (typical UAV power)
                        
                        # Interference power from UAV j to UAV i
                        interference_power = uav_tx_power - fspl_uav
                        interference_matrix[i, j] = 10**(interference_power / 10)  # Convert to linear
        
        # SINR calculation
        sinr_db = np.zeros(num_uavs)
        sinr_linear = np.zeros(num_uavs)
        
        # Noise power
        noise_power_dbm = self.munich_config['thermal_noise_dbm'] + self.munich_config['noise_figure_db']
        noise_power_linear = 10**(noise_power_dbm / 10)
        
        for i in range(num_uavs):
            # Desired signal power (linear)
            signal_power = 10**(rx_power_gnb[i] / 10)
            
            # Total interference from other UAVs
            total_interference = np.sum(interference_matrix[i, :])
            
            # SINR calculation
            sinr_linear[i] = signal_power / (total_interference + noise_power_linear)
            sinr_db[i] = 10 * np.log10(sinr_linear[i])
        
        # Throughput estimation with interference
        mimo_gain_db = 10 * np.log10(min(self.munich_config['gnb_antennas'], 
                                         self.munich_config['uav_antennas']))
        
        throughput_mbps = np.zeros(num_uavs)
        for i in range(num_uavs):
            # Effective SINR with MIMO gain
            eff_sinr_db = sinr_db[i] + mimo_gain_db
            eff_sinr_linear = 10**(eff_sinr_db / 10)
            
            # Shannon capacity with interference penalty
            efficiency_factor = 0.6  # Reduced efficiency due to interference
            spectral_eff = efficiency_factor * np.log2(1 + eff_sinr_linear)
            throughput_mbps[i] = spectral_eff * self.munich_config['bandwidth_mhz'] / num_uavs  # Resource sharing
        
        results = {
            'uav_positions': uav_positions,
            'distances_to_gnb': uav_to_gnb_distances,
            'path_loss_to_gnb': total_path_loss_gnb,
            'rx_power_gnb': rx_power_gnb,
            'interference_matrix': interference_matrix,
            'sinr_db': sinr_db,
            'sinr_linear': sinr_linear,
            'throughput_mbps': throughput_mbps,
            'total_throughput': np.sum(throughput_mbps),
            'avg_throughput': np.mean(throughput_mbps),
            'min_throughput': np.min(throughput_mbps),
            'max_throughput': np.max(throughput_mbps),
            'avg_sinr_db': np.mean(sinr_db),
            'min_sinr_db': np.min(sinr_db)
        }
        
        return results
    
    def _calculate_los_probability_array(self, uav_positions, gnb_pos):
        """Calcular probabilidad LoS para array de posiciones"""
        
        los_probs = np.zeros(len(uav_positions))
        
        # Munich buildings
        buildings = [
            [100, 100, 20], [200, 150, 35], [300, 200, 45],
            [150, 300, 30], [350, 350, 25], [250, 50, 40]
        ]
        
        for i, uav_pos in enumerate(uav_positions):
            height = uav_pos[2]
            los_prob_base = 1 / (1 + 9.61 * np.exp(-0.16 * (height - 1.5)))
            
            # Building blockage
            building_blockage = 0
            for bx, by, bh in buildings:
                dist_to_building = np.sqrt((uav_pos[0] - bx)**2 + (uav_pos[1] - by)**2)
                if dist_to_building < 70 and uav_pos[2] < bh + 20:
                    building_blockage += 0.1
            
            los_probs[i] = max(0.2, los_prob_base - min(0.7, building_blockage))
        
        return los_probs
    
    def analyze_interference_scenarios(self, progress_callback=None):
        """Analizar todos los escenarios de interferencia"""
        
        if progress_callback:
            progress_callback("Analizando escenarios de interferencia...")
        
        results = {}
        
        for scenario_key, scenario_info in self.interference_scenarios.items():
            if progress_callback:
                progress_callback(f"Procesando {scenario_info['name']}...")
            
            # Generate UAV positions
            uav_positions = self.generate_uav_positions(scenario_key, progress_callback)
            
            # Calculate interference
            interference_results = self.calculate_interference_matrix(uav_positions, progress_callback)
            
            # Store results
            results[scenario_key] = {
                'name': scenario_info['name'],
                'scenario_info': scenario_info,
                'results': interference_results
            }
        
        # Comparative analysis
        comparative_analysis = self._analyze_scenario_comparison(results)
        
        if progress_callback:
            progress_callback("Análisis de interferencia completado")
        
        return results, comparative_analysis
    
    def _analyze_scenario_comparison(self, results):
        """Análisis comparativo de escenarios"""
        
        comparison = {
            'best_total_throughput': {'scenario': None, 'value': 0},
            'best_avg_throughput': {'scenario': None, 'value': 0},
            'best_sinr': {'scenario': None, 'value': -999},
            'most_balanced': {'scenario': None, 'value': 0},
            'summary_stats': {}
        }
        
        for scenario_key, result in results.items():
            res = result['results']
            
            # Track best metrics
            if res['total_throughput'] > comparison['best_total_throughput']['value']:
                comparison['best_total_throughput'] = {'scenario': scenario_key, 'value': res['total_throughput']}
            
            if res['avg_throughput'] > comparison['best_avg_throughput']['value']:
                comparison['best_avg_throughput'] = {'scenario': scenario_key, 'value': res['avg_throughput']}
                
            if res['avg_sinr_db'] > comparison['best_sinr']['value']:
                comparison['best_sinr'] = {'scenario': scenario_key, 'value': res['avg_sinr_db']}
            
            # Balance score (low variance is better)
            throughput_variance = np.var(res['throughput_mbps'])
            balance_score = res['avg_throughput'] / (1 + throughput_variance)
            if balance_score > comparison['most_balanced']['value']:
                comparison['most_balanced'] = {'scenario': scenario_key, 'value': balance_score}
            
            # Summary stats
            comparison['summary_stats'][scenario_key] = {
                'num_uavs': len(res['uav_positions']),
                'total_throughput_mbps': res['total_throughput'],
                'avg_throughput_mbps': res['avg_throughput'],
                'avg_sinr_db': res['avg_sinr_db'],
                'min_sinr_db': res['min_sinr_db'],
                'throughput_fairness': res['min_throughput'] / res['max_throughput']
            }
        
        return comparison
    
    def generate_interference_plots(self, results, comparison, progress_callback=None):
        """Generar gráficos de análisis de interferencia"""
        
        if progress_callback:
            progress_callback("Generando gráficos de interferencia...")
        
        # Create comprehensive interference analysis plot (2x3 layout, sin heatmap)
        fig = plt.figure(figsize=(18, 12))
        
        # Colors for scenarios
        colors = ['#E74C3C', '#3498DB', '#2ECC71', '#F39C12', '#9B59B6']
        
        # 1. UAV Positions for Different Scenarios (3D)
        ax1 = fig.add_subplot(2, 3, 1, projection='3d')
        
        for i, (scenario_key, result) in enumerate(results.items()):
            positions = result['results']['uav_positions']
            color = colors[i % len(colors)]
            
            # Plot UAV positions
            ax1.scatter(positions[:, 0], positions[:, 1], positions[:, 2],
                       c=color, s=100, alpha=0.7, 
                       label=f"{result['name']} ({len(positions)} UAVs)")
        
        # gNB position
        gnb_pos = self.munich_config['gnb_position']
        ax1.scatter(*gnb_pos, s=400, c='red', marker='^', 
                   label='gNB', alpha=1.0, edgecolors='darkred')
        
        ax1.set_xlabel('X [m]', fontweight='bold', fontsize=12)
        ax1.set_ylabel('Y [m]', fontweight='bold', fontsize=12)
        ax1.set_zlabel('Altura [m]', fontweight='bold', fontsize=12)
        ax1.set_title('Posiciones UAV - Escenarios Interferencia\nDistribución Espacial Multi-Scenario', fontweight='bold')
        ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
        ax1.grid(True, alpha=0.3)
        
        # 2. SINR Comparison
        ax2 = fig.add_subplot(2, 3, 2)
        scenario_names = [result['name'][:15] for result in results.values()]
        avg_sinrs = [result['results']['avg_sinr_db'] for result in results.values()]
        min_sinrs = [result['results']['min_sinr_db'] for result in results.values()]
        
        x_pos = np.arange(len(scenario_names))
        bars1 = ax2.bar(x_pos - 0.2, avg_sinrs, 0.4, label='SINR Promedio', 
                       color=colors[:len(scenario_names)], alpha=0.8)
        bars2 = ax2.bar(x_pos + 0.2, min_sinrs, 0.4, label='SINR Mínimo', 
                       color=colors[:len(scenario_names)], alpha=0.5)
        
        ax2.set_ylabel('SINR [dB]', fontweight='bold', fontsize=12)
        ax2.set_title('Comparación SINR por Escenario\nCalidad de Señal vs Interferencia', fontweight='bold', fontsize=12)
        ax2.set_xticks(x_pos)
        ax2.set_xticklabels(scenario_names, rotation=45, ha='right')
        ax2.yaxis.set_major_formatter(FuncFormatter(lambda x, p: f'{x:.3f}'))
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Add value labels
        for i, (bar1, bar2, avg_val, min_val) in enumerate(zip(bars1, bars2, avg_sinrs, min_sinrs)):
            ax2.text(bar1.get_x() + bar1.get_width()/2., bar1.get_height() + 0.5,
                    f'{avg_val:.1f}', ha='center', va='bottom', fontsize=8, fontweight='bold')
        
        # 3. Throughput Analysis
        ax3 = fig.add_subplot(2, 3, 3)
        total_throughputs = [result['results']['total_throughput'] for result in results.values()]
        avg_throughputs = [result['results']['avg_throughput'] for result in results.values()]
        
        bars3 = ax3.bar(x_pos, total_throughputs, color=colors[:len(scenario_names)], alpha=0.7)
        
        # Secondary axis for average
        ax3_twin = ax3.twinx()
        line = ax3_twin.plot(x_pos, avg_throughputs, 'ro-', linewidth=3, markersize=8, 
                            label='Throughput Promedio por UAV')
        
        ax3.set_ylabel('Throughput Total [Mbps]', fontweight='bold', fontsize=12)
        ax3_twin.set_ylabel('Throughput Promedio [Mbps]', fontweight='bold', color='red', fontsize=12)
        ax3.set_title('Análisis Throughput Multi-UAV\nCapacidad Total vs Individual', fontweight='bold', fontsize=12)
        ax3.set_xticks(x_pos)
        ax3.set_xticklabels(scenario_names, rotation=45, ha='right')
        ax3.yaxis.set_major_formatter(FuncFormatter(lambda x, p: f'{x:.3f}'))
        ax3_twin.yaxis.set_major_formatter(FuncFormatter(lambda x, p: f'{x:.3f}'))
        ax3.grid(True, alpha=0.3)
        
        # Add value labels
        for i, (bar, total_val, avg_val) in enumerate(zip(bars3, total_throughputs, avg_throughputs)):
            ax3.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 10,
                    f'{total_val:.0f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        # 4. Throughput Fairness Analysis
        ax4 = fig.add_subplot(2, 3, 4)
        
        fairness_data = []
        scenario_labels = []
        
        for scenario_key, result in results.items():
            throughputs = result['results']['throughput_mbps']
            fairness_data.append(throughputs)
            scenario_labels.append(result['name'][:12])
        
        # Box plot for fairness
        bp = ax4.boxplot(fairness_data, labels=scenario_labels, patch_artist=True)
        
        # Color the boxes
        for patch, color in zip(bp['boxes'], colors[:len(scenario_labels)]):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        
        ax4.set_ylabel('Throughput Individual [Mbps]', fontweight='bold', fontsize=12)
        ax4.set_title('Análisis de Equidad (Fairness)\nDistribución Throughput por Escenario', fontweight='bold', fontsize=12)
        ax4.tick_params(axis='x', rotation=45)
        ax4.grid(True, alpha=0.3)
        
        # 5. Summary and Recommendations
        ax5 = fig.add_subplot(2, 3, 5)
        ax5.axis('off')
        
        # Summary statistics
        best_total = comparison['best_total_throughput']
        best_avg = comparison['best_avg_throughput']
        best_sinr = comparison['best_sinr']
        most_balanced = comparison['most_balanced']
        
        summary_text = f"""
ANÁLISIS INTERFERENCIA MULTI-UAV

Mejor Throughput Total:
   {results[best_total['scenario']]['name']}
   {best_total['value']:.0f} Mbps

Mejor Throughput Promedio:
   {results[best_avg['scenario']]['name']}
   {best_avg['value']:.1f} Mbps/UAV

Mejor SINR:
   {results[best_sinr['scenario']]['name']}
   {best_sinr['value']:.1f} dB

Más Balanceado:
   {results[most_balanced['scenario']]['name']}
   Score: {most_balanced['value']:.1f}

Recomendación:
   Para máxima capacidad total usar
   {results[best_total['scenario']]['name']}
   
   Para mejor equidad usar
   {results[most_balanced['scenario']]['name']}
        """
        
        ax5.text(0.05, 0.95, summary_text, transform=ax5.transAxes, fontsize=10,
                verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle="round,pad=0.4", 
                facecolor='lightcyan', alpha=0.8))
        ax5.set_title('Resumen de Resultados\n(Sionna Multi-UAV)', fontweight='bold', fontsize=12)
        
        # Main title
        fig.suptitle('ANÁLISIS INTERFERENCIA MULTI-UAV - Sistema 5G NR Munich\nOptimización SINR y Gestión de Recursos', 
                    fontsize=14, fontweight='bold', y=0.98)
        
        plt.tight_layout()
        plt.subplots_adjust(top=0.93, hspace=0.35, wspace=0.3)
        
        if progress_callback:
            progress_callback("Guardando análisis de interferencia...")
        
        plot_path = os.path.join(self.output_dir, "interference_analysis.png")
        plt.savefig(plot_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return plot_path
    
    def generate_3d_interference_scene(self, results, comparison, progress_callback=None):
        """Generar escena 3D con análisis de interferencia"""
        
        if progress_callback:
            progress_callback("Generando escena 3D de interferencia...")
        
        fig = plt.figure(figsize=(18, 14))
        ax = fig.add_subplot(111, projection='3d')
        
        # Munich terrain base
        area = 500
        x_ground = np.linspace(-area//2, area//2, 20)
        y_ground = np.linspace(-area//2, area//2, 20)
        X_ground, Y_ground = np.meshgrid(x_ground, y_ground)
        Z_ground = 2 * np.sin(X_ground/100) * np.cos(Y_ground/100) + 1
        ax.plot_surface(X_ground, Y_ground, Z_ground, alpha=0.1, color='lightgray')
        
        # Munich buildings
        buildings = [
            [100, 100, 20], [200, 150, 35], [300, 200, 45],
            [150, 300, 30], [350, 350, 25], [250, 50, 40]
        ]
        building_colors = ['#8B4513', '#696969', '#708090', '#2F4F4F', '#8FBC8F', '#CD853F']
        
        for i, (x, y, h) in enumerate(buildings):
            building_size = 35
            ax.bar3d(x-building_size/2, y-building_size/2, 0, building_size, building_size, h, 
                    alpha=0.6, color=building_colors[i], edgecolor='black')
        
        # gNB Tower
        gnb_x, gnb_y, gnb_z = self.munich_config['gnb_position']
        ax.scatter([gnb_x], [gnb_y], [gnb_z], c='red', s=600, marker='^', 
                  label='gNB Base Station', alpha=1.0, edgecolors='darkred', linewidth=3)
        ax.plot([gnb_x, gnb_x], [gnb_y, gnb_y], [0, gnb_z], 'darkred', linewidth=8)
        
        # Show best interference scenario
        best_scenario_key = comparison['best_avg_throughput']['scenario']
        best_result = results[best_scenario_key]
        positions = best_result['results']['uav_positions']
        throughputs = best_result['results']['throughput_mbps']
        sinrs = best_result['results']['sinr_db']
        
        # Normalize metrics for visualization
        throughput_norm = (throughputs - np.min(throughputs)) / (np.max(throughputs) - np.min(throughputs))
        sinr_norm = (sinrs - np.min(sinrs)) / (np.max(sinrs) - np.min(sinrs))
        
        # Plot UAVs with performance-based visualization
        for i, (pos, throughput, sinr, t_norm, s_norm) in enumerate(zip(positions, throughputs, sinrs, throughput_norm, sinr_norm)):
            # Size based on throughput
            size = 100 + 300 * t_norm
            
            # Color based on SINR (green = good, red = poor)
            color = plt.cm.RdYlGn(s_norm)
            
            ax.scatter(pos[0], pos[1], pos[2], s=size, c=[color], 
                      alpha=0.8, edgecolors='black', linewidth=2)
            
            # Add UAV label
            ax.text(pos[0], pos[1], pos[2] + 5, f'UAV{i+1}\n{throughput:.0f}Mbps\n{sinr:.1f}dB', 
                   fontsize=8, ha='center', va='bottom')
        
        # Draw communication links from gNB to UAVs (colored by SINR)
        for i, (pos, sinr, s_norm) in enumerate(zip(positions, sinrs, sinr_norm)):
            color = plt.cm.RdYlGn(s_norm)
            linewidth = 2 + 3 * s_norm  # Thicker line for better SINR
            ax.plot([gnb_x, pos[0]], [gnb_y, pos[1]], [gnb_z, pos[2]], 
                   color=color, linewidth=linewidth, alpha=0.7)
        
        # Draw interference links between UAVs (only significant ones)
        interference_matrix = best_result['results']['interference_matrix']
        interference_threshold = np.percentile(interference_matrix[interference_matrix > 0], 75)
        
        for i in range(len(positions)):
            for j in range(len(positions)):
                if i != j and interference_matrix[i, j] > interference_threshold:
                    # Interference strength visualization
                    interference_strength = interference_matrix[i, j] / np.max(interference_matrix)
                    
                    ax.plot([positions[i, 0], positions[j, 0]], 
                           [positions[i, 1], positions[j, 1]], 
                           [positions[i, 2], positions[j, 2]], 
                           'r--', linewidth=1 + 2*interference_strength, alpha=0.5)
        
        # Coverage area boundary
        area_range = self.munich_config['area_range']
        theta = np.linspace(0, 2*np.pi, 50)
        boundary_x = area_range * np.cos(theta)
        boundary_y = area_range * np.sin(theta)
        boundary_z = np.full_like(boundary_x, self.munich_config['fixed_height'])
        ax.plot(boundary_x, boundary_y, boundary_z, 'cyan', linewidth=3, alpha=0.8, 
               label=f'Área Análisis ({2*area_range}m)')
        
        # Performance zones (simplified)
        # High performance zone (close to gNB)
        inner_radius = 100
        inner_x = inner_radius * np.cos(theta)
        inner_y = inner_radius * np.sin(theta)
        inner_z = np.full_like(inner_x, self.munich_config['fixed_height'])
        ax.plot(inner_x, inner_y, inner_z, 'green', linewidth=2, alpha=0.6, 
               label='Zona Alto Rendimiento')
        
        # Configuration and styling
        ax.set_xlabel('Coordenada X (metros)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Coordenada Y (metros)', fontsize=12, fontweight='bold')
        ax.set_zlabel('Altura Z (metros)', fontsize=12, fontweight='bold')
        ax.set_title(f'MUNICH 3D - Análisis Interferencia Multi-UAV\nEscenario: {best_result["name"]} (Mejor Rendimiento Promedio)', 
                    fontsize=16, fontweight='bold', pad=20)
        
        # Limits
        ax.set_xlim(-area_range-50, area_range+50)
        ax.set_ylim(-area_range-50, area_range+50) 
        ax.set_zlim(0, 100)
        
        # Custom legend
        from matplotlib.patches import Patch
        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0], [0], marker='^', color='w', markerfacecolor='red', markersize=15, 
                  label='gNB Base Station'),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='green', markersize=10, 
                  label='UAV Alto SINR'),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='red', markersize=10, 
                  label='UAV Bajo SINR'),
            Line2D([0], [0], color='green', linewidth=3, label='Enlace Buena Calidad'),
            Line2D([0], [0], color='red', linestyle='--', linewidth=2, label='Interferencia Significativa'),
            Line2D([0], [0], color='cyan', linewidth=3, label=f'Área Análisis')
        ]
        
        ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(0.02, 0.98), fontsize=9)
        
        # Grid and view
        ax.grid(True, alpha=0.3)
        ax.view_init(elev=25, azim=45)
        
        plt.tight_layout()
        
        if progress_callback:
            progress_callback("Guardando escena 3D interferencia...")
        
        scene_path = os.path.join(self.output_dir, "interference_scene_3d.png")
        plt.savefig(scene_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return scene_path
    
    def save_interference_results_json(self, results, comparison):
        """Guardar resultados del análisis en JSON"""
        
        # Prepare serializable results
        json_results = {}
        for scenario_key, result in results.items():
            res = result['results']
            json_results[scenario_key] = {
                'name': result['name'],
                'scenario_info': result['scenario_info'],
                'performance_stats': {
                    'num_uavs': len(res['uav_positions']),
                    'total_throughput_mbps': float(res['total_throughput']),
                    'avg_throughput_mbps': float(res['avg_throughput']),
                    'min_throughput_mbps': float(res['min_throughput']),
                    'max_throughput_mbps': float(res['max_throughput']),
                    'avg_sinr_db': float(res['avg_sinr_db']),
                    'min_sinr_db': float(res['min_sinr_db']),
                    'throughput_fairness': float(res['min_throughput'] / res['max_throughput'])
                },
                'uav_individual_stats': {
                    'throughputs_mbps': res['throughput_mbps'].tolist(),
                    'sinr_values_db': res['sinr_db'].tolist(),
                    'distances_to_gnb_m': res['distances_to_gnb'].tolist()
                }
            }
        
        complete_results = {
            'simulation_type': 'interference_analysis',
            'timestamp': '2026-02-01',
            'system_config': self.system_config,
            'interference_analysis': {
                'max_uavs_supported': self.munich_config['num_uavs'],
                'scenarios_analyzed': len(self.interference_scenarios),
                'resource_blocks': self.munich_config['resource_blocks'],
                'analysis_area_m2': (2 * self.munich_config['area_range'])**2
            },
            'scenario_results': json_results,
            'comparative_analysis': {
                'best_total_throughput': {
                    'scenario': results[comparison['best_total_throughput']['scenario']]['name'],
                    'value_mbps': comparison['best_total_throughput']['value']
                },
                'best_avg_throughput': {
                    'scenario': results[comparison['best_avg_throughput']['scenario']]['name'], 
                    'value_mbps': comparison['best_avg_throughput']['value']
                },
                'best_sinr': {
                    'scenario': results[comparison['best_sinr']['scenario']]['name'],
                    'value_db': comparison['best_sinr']['value']
                },
                'most_balanced': {
                    'scenario': results[comparison['most_balanced']['scenario']]['name'],
                    'balance_score': comparison['most_balanced']['value']
                }
            },
            'recommendations': {
                'for_maximum_capacity': results[comparison['best_total_throughput']['scenario']]['name'],
                'for_best_individual_performance': results[comparison['best_avg_throughput']['scenario']]['name'],
                'for_best_signal_quality': results[comparison['best_sinr']['scenario']]['name'],
                'for_fairness': results[comparison['most_balanced']['scenario']]['name']
            },
            'summary': {
                'best_scenario_overall': results[comparison['best_avg_throughput']['scenario']]['name'],
                'max_total_throughput': f"{comparison['best_total_throughput']['value']:.1f} Mbps",
                'best_individual_throughput': f"{comparison['best_avg_throughput']['value']:.1f} Mbps",
                'interference_impact': "Significativo en escenarios de alta densidad"
            }
        }
        
        json_path = os.path.join(self.output_dir, "interference_results.json")
        with open(json_path, 'w') as f:
            json.dump(complete_results, f, indent=2)
        
        return json_path
    
    def run_complete_analysis(self, progress_callback=None):
        """Ejecutar análisis completo de interferencia"""
        
        if progress_callback:
            progress_callback("Iniciando análisis de interferencia...")
        
        # 1. Analyze all interference scenarios
        results, comparison = self.analyze_interference_scenarios(progress_callback)
        
        if progress_callback:
            progress_callback("Generando visualizaciones interferencia...")
        
        # 2. Generate analysis plots
        plots_path = self.generate_interference_plots(results, comparison, progress_callback)
        
        # 3. Generate 3D scene
        scene_path = self.generate_3d_interference_scene(results, comparison, progress_callback)
        
        # 4. Save JSON results
        json_path = self.save_interference_results_json(results, comparison)
        
        if progress_callback:
            progress_callback("Análisis de interferencia completado!")
        
        # Summary
        best_scenario = comparison['best_avg_throughput']['scenario']
        best_value = comparison['best_avg_throughput']['value']
        best_sinr = comparison['best_sinr']['value']
        
        return {
            'type': 'interference_analysis',
            'plots': [plots_path],
            'scene_3d': scene_path,
            'data': json_path,
            'summary': f'Interferencia: {results[best_scenario]["name"]} mejor escenario ({best_value:.1f} Mbps/UAV)',
            'config': {
                'Interference_Analysis': {
                    'Best_Scenario': results[best_scenario]['name'],
                    'Avg_Throughput_per_UAV': f"{best_value:.1f} Mbps",
                    'Best_SINR': f"{best_sinr:.1f} dB",
                    'Scenarios_Tested': len(self.interference_scenarios)
                },
                'Performance': {
                    'Max_Total_Capacity': f"{comparison['best_total_throughput']['value']:.0f} Mbps",
                    'Best_Signal_Quality': f"{best_sinr:.1f} dB SINR",
                    'Most_Balanced': results[comparison['most_balanced']['scenario']]['name'],
                    'Analysis_Area': f"±{self.munich_config['area_range']}m"
                }
            }
        }


def run_interference_analysis_gui(output_dir="outputs", progress_callback=None):
    """Función para ejecutar desde GUI worker thread"""
    
    interference_analyzer = InterferenceAnalysisGUI(output_dir)
    results = interference_analyzer.run_complete_analysis(progress_callback)
    
    return results


if __name__ == "__main__":
    # Test standalone
    print("Testing Interference Analysis GUI...")
    results = run_interference_analysis_gui("test_outputs")
    print(f"Test completado: {results['summary']}")