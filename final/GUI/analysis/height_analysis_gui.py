"""
Height Analysis GUI - Análisis de Altura Óptima para GUI
Análisis de throughput vs altura UAV adaptado para interfaz PyQt6
"""
import numpy as np
import matplotlib.pyplot as plt
import os
import json

class HeightAnalysisGUI:
    """Análisis de altura óptima adaptado para GUI"""
    
    def __init__(self, output_dir="outputs"):
        """Inicializar análisis de altura GUI"""
        
        print("="*60)
        print("HEIGHT ANALYSIS GUI - Analisis Altura Optima")
        print("="*60)
        
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Munich scenario configuration
        self.munich_config = {
            'area_size_m': 500,
            'gnb_position': [300, 200, 50],  # gNB sobre edificio más alto
            'user_position_2d': [200, 200],  # Fixed horizontal position
            'height_range': np.linspace(20, 200, 19),  # 20m to 200m, 19 points
            'frequency_ghz': 3.5,
            'bandwidth_mhz': 100,
            'gnb_power_dbm': 43,
            'gnb_antennas': 64,
            'uav_antennas': 4
        }
        
        # System configuration
        self.system_config = {
            'scenario': 'Munich Urban 3D',
            'frequency': f"{self.munich_config['frequency_ghz']} GHz",
            'bandwidth': f"{self.munich_config['bandwidth_mhz']} MHz",
            'gnb_config': f"{self.munich_config['gnb_antennas']} antennas @ {self.munich_config['gnb_position']}",
            'uav_config': f"{self.munich_config['uav_antennas']} antennas",
            'analysis_range': f"{self.munich_config['height_range'][0]:.0f}-{self.munich_config['height_range'][-1]:.0f}m"
        }
        
        print("Height Analysis GUI inicializado")
        print(f"Directorio de salida: {output_dir}")
        
    def calculate_height_performance(self, progress_callback=None):
        """Calcular performance vs altura UAV"""
        
        if progress_callback:
            progress_callback("Calculando performance vs altura...")
            
        heights = self.munich_config['height_range']
        gnb_pos = np.array(self.munich_config['gnb_position'])
        user_pos_2d = np.array(self.munich_config['user_position_2d'])
        
        results = {
            'heights': heights,
            'throughput_mbps': [],
            'path_loss_db': [],
            'los_probability': [],
            'snr_db': [],
            'spectral_efficiency': []
        }
        
        if progress_callback:
            progress_callback(f"Analizando {len(heights)} alturas...")
        
        for i, height in enumerate(heights):
            if progress_callback:
                progress = (i + 1) / len(heights) * 100
                progress_callback(f"Altura {height:.0f}m ({progress:.0f}%)...")
            
            # 3D position
            uav_pos = np.array([user_pos_2d[0], user_pos_2d[1], height])
            
            # Distance calculation
            distance_3d = np.linalg.norm(uav_pos - gnb_pos)
            
            # LoS probability (ITU-R model for urban)
            los_prob = 1 / (1 + 9.61 * np.exp(-0.16 * (height - 1.5)))
            
            # Path loss calculation (3GPP TR 38.901)
            # Free space path loss
            fspl_db = 32.4 + 20 * np.log10(distance_3d) + 20 * np.log10(self.munich_config['frequency_ghz'])
            
            # Additional path loss for NLoS
            nlos_factor = 0 if los_prob > 0.5 else 20  # 20dB additional for NLoS
            total_path_loss = fspl_db + nlos_factor
            
            # Received power
            rx_power_dbm = self.munich_config['gnb_power_dbm'] - total_path_loss
            
            # SNR calculation (simplified)
            noise_floor_dbm = -104  # Typical noise floor for 100MHz BW
            snr_db = rx_power_dbm - noise_floor_dbm
            
            # MIMO gain (simplified)
            mimo_gain_db = 10 * np.log10(min(self.munich_config['gnb_antennas'], 
                                            self.munich_config['uav_antennas']))
            snr_db += mimo_gain_db
            
            # Shannon capacity with practical efficiency
            efficiency_factor = 0.75  # Practical efficiency
            spectral_eff = efficiency_factor * np.log2(1 + 10**(snr_db/10))
            
            # Throughput
            throughput_mbps = spectral_eff * self.munich_config['bandwidth_mhz']
            
            # Height-specific effects (diversity gain at certain heights)
            if 40 <= height <= 80:
                diversity_gain = 1.15  # 15% gain in optimal range
                throughput_mbps *= diversity_gain
            
            # Store results
            results['throughput_mbps'].append(max(0, throughput_mbps))
            results['path_loss_db'].append(total_path_loss)
            results['los_probability'].append(los_prob)
            results['snr_db'].append(snr_db)
            results['spectral_efficiency'].append(spectral_eff)
        
        # Convert to numpy arrays
        for key in results:
            if key != 'heights':
                results[key] = np.array(results[key])
                
        if progress_callback:
            progress_callback("Análisis de altura completado")
            
        return results
    
    def analyze_height_results(self, results):
        """Analizar resultados del análisis de altura"""
        
        # Find optimal configuration
        max_idx = np.argmax(results['throughput_mbps'])
        optimal_height = results['heights'][max_idx]
        max_throughput = results['throughput_mbps'][max_idx]
        
        # Statistics
        avg_throughput = np.mean(results['throughput_mbps'])
        min_throughput = np.min(results['throughput_mbps'])
        
        # LoS analysis
        los_heights = results['heights'][results['los_probability'] > 0.5]
        los_percentage = len(los_heights) / len(results['heights']) * 100
        
        # Performance metrics
        analysis = {
            'optimal_height_m': float(optimal_height),
            'max_throughput_mbps': float(max_throughput),
            'avg_throughput_mbps': float(avg_throughput),
            'min_throughput_mbps': float(min_throughput),
            'height_gain_factor': float(max_throughput / min_throughput),
            'los_percentage': float(los_percentage),
            'recommended_range': [40, 80],  # Optimal range
            'performance_summary': f"Altura óptima {optimal_height:.0f}m con {max_throughput:.1f} Mbps"
        }
        
        return analysis
    
    def generate_height_plots(self, results, progress_callback=None):
        """Generar gráficos del análisis de altura"""
        
        if progress_callback:
            progress_callback("Generando gráficos de altura...")
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        heights = results['heights']
        
        # Plot 1: Throughput vs Height (MAIN)
        ax1.plot(heights, results['throughput_mbps'], 'b-o', linewidth=3, markersize=8)
        ax1.set_xlabel('Altura UAV [m]', fontweight='bold', fontsize=12)
        ax1.set_ylabel('Throughput [Mbps]', fontweight='bold', fontsize=12)
        ax1.set_title('Throughput vs Altura UAV\nConfiguración MIMO 64x4', fontweight='bold', fontsize=14)
        ax1.grid(True, alpha=0.4)
        
        # Highlight optimal point
        max_idx = np.argmax(results['throughput_mbps'])
        ax1.scatter(heights[max_idx], results['throughput_mbps'][max_idx],
                   color='red', s=200, zorder=5, edgecolors='darkred', linewidth=3)
        ax1.annotate(f'Óptimo: {heights[max_idx]:.0f}m\n{results["throughput_mbps"][max_idx]:.1f} Mbps',
                    xy=(heights[max_idx], results['throughput_mbps'][max_idx]),
                    xytext=(10, 10), textcoords='offset points',
                    bbox=dict(boxstyle="round,pad=0.3", facecolor='yellow', alpha=0.8),
                    fontweight='bold')
        
        # Plot 2: Path Loss vs Height
        ax2.plot(heights, results['path_loss_db'], 'r-s', linewidth=2.5, markersize=6)
        ax2.set_xlabel('Altura UAV [m]', fontweight='bold', fontsize=12)
        ax2.set_ylabel('Path Loss [dB]', fontweight='bold', fontsize=12)
        ax2.set_title('Path Loss vs Altura', fontweight='bold', fontsize=14)
        ax2.grid(True, alpha=0.4)
        
        # Plot 3: LoS Probability vs Height
        ax3.plot(heights, results['los_probability'], 'g-^', linewidth=2.5, markersize=6)
        ax3.set_xlabel('Altura UAV [m]', fontweight='bold', fontsize=12)
        ax3.set_ylabel('Probabilidad LoS', fontweight='bold', fontsize=12)
        ax3.set_title('Probabilidad LoS vs Altura', fontweight='bold', fontsize=14)
        ax3.set_ylim([0, 1.1])
        ax3.grid(True, alpha=0.4)
        
        # Add LoS threshold line
        ax3.axhline(y=0.5, color='orange', linestyle='--', alpha=0.8, label='Umbral LoS (50%)')
        ax3.legend()
        
        # Plot 4: SNR vs Height
        ax4.plot(heights, results['snr_db'], 'm-d', linewidth=2.5, markersize=6)
        ax4.set_xlabel('Altura UAV [m]', fontweight='bold', fontsize=12)
        ax4.set_ylabel('SNR [dB]', fontweight='bold', fontsize=12)
        ax4.set_title('SNR vs Altura', fontweight='bold', fontsize=14)
        ax4.grid(True, alpha=0.4)
        
        # Add SNR threshold lines
        ax4.axhline(y=10, color='red', linestyle='--', alpha=0.6, label='Umbral mínimo (10dB)')
        ax4.axhline(y=20, color='green', linestyle='--', alpha=0.6, label='Umbral óptimo (20dB)')
        ax4.legend()
        
        # Main title
        fig.suptitle('ANÁLISIS ALTURA ÓPTIMA UAV - Sistema 5G NR Munich\nOptimización Throughput vs Altura de Vuelo', 
                    fontsize=16, fontweight='bold', y=0.95)
        
        plt.tight_layout()
        plt.subplots_adjust(top=0.88)
        
        if progress_callback:
            progress_callback("Guardando gráficos de altura...")
        
        # Save plot
        plot_path = os.path.join(self.output_dir, "height_analysis.png")
        plt.savefig(plot_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return plot_path
    
    def generate_3d_height_scene(self, results, progress_callback=None):
        """Generar escena 3D del análisis de altura"""
        
        if progress_callback:
            progress_callback("Generando mapa 3D de análisis altura...")
        
        fig = plt.figure(figsize=(18, 14))
        ax = fig.add_subplot(111, projection='3d')
        
        area = self.munich_config['area_size_m']
        
        # Terreno Munich
        x_ground = np.linspace(0, area, 30)
        y_ground = np.linspace(0, area, 30)
        X_ground, Y_ground = np.meshgrid(x_ground, y_ground)
        Z_ground = 2 * np.sin(X_ground/100) * np.cos(Y_ground/100) + 1
        ax.plot_surface(X_ground, Y_ground, Z_ground, alpha=0.2, color='lightgreen')
        
        # Edificios Munich
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
        ax.scatter([gnb_x], [gnb_y], [gnb_z], c='red', s=500, marker='^', 
                  label='gNB Base Station', alpha=1.0, edgecolors='darkred', linewidth=3)
        ax.plot([gnb_x, gnb_x], [gnb_y, gnb_y], [0, gnb_z], 'darkred', linewidth=8)
        
        # UAV trajectory (height analysis)
        user_x, user_y = self.munich_config['user_position_2d']
        heights = results['heights']
        throughputs = results['throughput_mbps']
        
        # Color UAV positions by throughput performance
        norm_throughput = (throughputs - np.min(throughputs)) / (np.max(throughputs) - np.min(throughputs))
        colors = plt.cm.viridis(norm_throughput)
        
        # Plot UAV at different heights
        for i, (height, color) in enumerate(zip(heights, colors)):
            size = 100 + 100 * norm_throughput[i]  # Larger = better performance
            ax.scatter([user_x], [user_y], [height], c=[color], s=size, 
                      alpha=0.8, edgecolors='black', linewidth=1)
        
        # Optimal height UAV (highlighted)
        max_idx = np.argmax(throughputs)
        optimal_height = heights[max_idx]
        ax.scatter([user_x], [user_y], [optimal_height], c='gold', s=300, marker='*', 
                  label=f'Altura Óptima ({optimal_height:.0f}m)', alpha=1.0, 
                  edgecolors='darkorange', linewidth=3)
        
        # Vertical line showing height range
        ax.plot([user_x, user_x], [user_y, user_y], [np.min(heights), np.max(heights)], 
               'blue', linewidth=4, alpha=0.6, label='Rango Análisis')
        
        # Communication link to optimal UAV
        ax.plot([gnb_x, user_x], [gnb_y, user_y], [gnb_z, optimal_height], 
               'gold', linewidth=6, alpha=0.8, label='Enlace Óptimo')
        
        # Height analysis zone (cylinder)
        theta = np.linspace(0, 2*np.pi, 20)
        zone_radius = 30
        for height in [np.min(heights), np.max(heights)]:
            x_zone = user_x + zone_radius * np.cos(theta)
            y_zone = user_y + zone_radius * np.sin(theta)
            z_zone = np.full_like(x_zone, height)
            ax.plot(x_zone, y_zone, z_zone, 'cyan', alpha=0.3, linewidth=1)
        
        # Configuration
        ax.set_xlabel('Coordenada X (metros)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Coordenada Y (metros)', fontsize=12, fontweight='bold')
        ax.set_zlabel('Altura Z (metros)', fontsize=12, fontweight='bold')
        ax.set_title('MAPA 3D MUNICH - Análisis Altura Óptima UAV\nOptimización Throughput vs Altura de Vuelo', 
                    fontsize=16, fontweight='bold', pad=20)
        
        # Limits
        ax.set_xlim(0, area)
        ax.set_ylim(0, area)
        ax.set_zlim(0, 250)
        
        # Legend
        ax.legend(loc='upper left', bbox_to_anchor=(0.02, 0.98), fontsize=10)
        
        # Grid and view
        ax.grid(True, alpha=0.3)
        ax.view_init(elev=25, azim=45)
        
        plt.tight_layout()
        
        if progress_callback:
            progress_callback("Guardando escena 3D altura...")
        
        # Save scene
        scene_path = os.path.join(self.output_dir, "height_scene_3d.png")
        plt.savefig(scene_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return scene_path
    
    def save_height_results_json(self, results, analysis):
        """Guardar resultados del análisis en JSON"""
        
        complete_results = {
            'simulation_type': 'height_analysis',
            'timestamp': '2026-02-01',
            'system_config': self.system_config,
            'height_analysis': {
                'heights_m': results['heights'].tolist(),
                'throughput_mbps': results['throughput_mbps'].tolist(),
                'path_loss_db': results['path_loss_db'].tolist(),
                'los_probability': results['los_probability'].tolist(),
                'snr_db': results['snr_db'].tolist()
            },
            'optimization_results': analysis,
            'summary': {
                'optimal_height_m': analysis['optimal_height_m'],
                'max_throughput_mbps': analysis['max_throughput_mbps'],
                'height_gain_factor': analysis['height_gain_factor'],
                'recommended_config': f"Operar UAV a {analysis['optimal_height_m']:.0f}m para {analysis['max_throughput_mbps']:.1f} Mbps máximo"
            }
        }
        
        json_path = os.path.join(self.output_dir, "height_results.json")
        with open(json_path, 'w') as f:
            json.dump(complete_results, f, indent=2)
        
        return json_path
    
    def run_complete_analysis(self, progress_callback=None):
        """Ejecutar análisis completo de altura"""
        
        if progress_callback:
            progress_callback("Iniciando análisis de altura...")
        
        # 1. Calculate height performance
        results = self.calculate_height_performance(progress_callback)
        
        # 2. Analyze results
        analysis = self.analyze_height_results(results)
        
        if progress_callback:
            progress_callback("Generando visualizaciones altura...")
        
        # 3. Generate plots
        plots_path = self.generate_height_plots(results, progress_callback)
        
        # 4. Generate 3D scene
        scene_path = self.generate_3d_height_scene(results, progress_callback)
        
        # 5. Save JSON results
        json_path = self.save_height_results_json(results, analysis)
        
        if progress_callback:
            progress_callback("Análisis de altura completado!")
        
        return {
            'type': 'height_analysis',
            'plots': [plots_path],
            'scene_3d': scene_path,
            'data': json_path,
            'summary': f'Altura óptima: {analysis["optimal_height_m"]:.0f}m con {analysis["max_throughput_mbps"]:.1f} Mbps',
            'config': {
                'Height_Analysis': {
                    'Optimal_Height_m': analysis['optimal_height_m'],
                    'Max_Throughput_Mbps': analysis['max_throughput_mbps'],
                    'Height_Range': f"{results['heights'][0]:.0f}-{results['heights'][-1]:.0f}m",
                    'Gain_vs_Worst': f"{analysis['height_gain_factor']:.1f}x"
                },
                'Performance': {
                    'LoS_Coverage': f"{analysis['los_percentage']:.1f}%",
                    'Recommended_Range': f"{analysis['recommended_range'][0]}-{analysis['recommended_range'][1]}m",
                    'Analysis_Summary': analysis['performance_summary']
                }
            }
        }


def run_height_analysis_gui(output_dir="outputs", progress_callback=None):
    """Función para ejecutar desde GUI worker thread"""
    
    height_analyzer = HeightAnalysisGUI(output_dir)
    results = height_analyzer.run_complete_analysis(progress_callback)
    
    return results


if __name__ == "__main__":
    # Test standalone
    print("Testing Height Analysis GUI...")
    results = run_height_analysis_gui("test_outputs")
    print(f"Test completado: {results['summary']}")