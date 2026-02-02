"""
Coverage Analysis GUI - Análisis de Cobertura 2D para GUI
Análisis de cobertura con mapas de throughput, LoS/NLoS adaptado para PyQt6
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import os
import json

class CoverageAnalysisGUI:
    """Análisis de cobertura 2D adaptado para GUI"""
    
    def __init__(self, output_dir="outputs"):
        """Inicializar análisis de cobertura GUI"""
        
        print("="*60)
        print("COVERAGE ANALYSIS GUI - Analisis Cobertura 2D")
        print("="*60)
        
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Munich scenario configuration
        self.munich_config = {
            'grid_resolution': 12,  # 12x12 = 144 points (faster)
            'coverage_range': 250,  # ±250m area
            'optimal_height': 40,   # From Phase 2 result
            'frequency_ghz': 3.5,
            'bandwidth_mhz': 100,
            'gnb_position': [300, 200, 50],  # gNB sobre edificio más alto
            'gnb_power_dbm': 43,
            'gnb_antennas': 64,
            'uav_antennas': 4
        }
        
        # System configuration
        self.system_config = {
            'scenario': 'Munich Urban 3D Coverage',
            'frequency': f"{self.munich_config['frequency_ghz']} GHz",
            'bandwidth': f"{self.munich_config['bandwidth_mhz']} MHz",
            'area_size': f"{2*self.munich_config['coverage_range']}m x {2*self.munich_config['coverage_range']}m",
            'grid_points': f"{self.munich_config['grid_resolution']}x{self.munich_config['grid_resolution']} = {self.munich_config['grid_resolution']**2} puntos",
            'uav_height': f"{self.munich_config['optimal_height']}m (altura óptima)"
        }
        
        # Generate coverage grid
        self._generate_coverage_grid()
        
        print("Coverage Analysis GUI inicializado")
        print(f"Directorio de salida: {output_dir}")
        print(f"Grid: {self.munich_config['grid_resolution']**2} puntos")
        
    def _generate_coverage_grid(self):
        """Generar grid 2D de posiciones para cobertura"""
        
        range_m = self.munich_config['coverage_range']
        resolution = self.munich_config['grid_resolution']
        
        # Create grid positions
        x_positions = np.linspace(-range_m, range_m, resolution)
        y_positions = np.linspace(-range_m, range_m, resolution)
        
        # Meshgrid for visualization
        self.X, self.Y = np.meshgrid(x_positions, y_positions)
        
        # Flatten for iteration
        self.x_flat = self.X.flatten()
        self.y_flat = self.Y.flatten()
        
    def calculate_coverage_performance(self, progress_callback=None):
        """Calcular performance de cobertura en grid 2D"""
        
        if progress_callback:
            progress_callback("Calculando cobertura en grid 2D...")
            
        total_points = len(self.x_flat)
        gnb_pos = np.array(self.munich_config['gnb_position'])
        fixed_height = self.munich_config['optimal_height']
        
        # Result arrays
        throughput_grid = np.zeros(total_points)
        path_loss_grid = np.zeros(total_points)
        los_grid = np.zeros(total_points)
        snr_grid = np.zeros(total_points)
        spectral_efficiency_grid = np.zeros(total_points)
        
        if progress_callback:
            progress_callback(f"Analizando {total_points} posiciones en grid...")
        
        # Munich buildings for LoS calculation
        buildings = [
            [100, 100, 20], [200, 150, 35], [300, 200, 45],
            [150, 300, 30], [350, 350, 25], [250, 50, 40]
        ]
        
        for i, (x, y) in enumerate(zip(self.x_flat, self.y_flat)):
            if progress_callback and i % max(1, total_points // 20) == 0:
                progress = (i + 1) / total_points * 100
                progress_callback(f"Posición {i+1}/{total_points} ({progress:.0f}%)...")
            
            # UAV position at fixed optimal height
            uav_pos = np.array([x, y, fixed_height])
            
            # Distance to gNB
            distance_3d = np.linalg.norm(uav_pos - gnb_pos)
            
            # LoS calculation considering buildings
            los_probability = self._calculate_los_probability(uav_pos, gnb_pos, buildings)
            
            # Path loss calculation
            fspl_db = 32.4 + 20 * np.log10(distance_3d) + 20 * np.log10(self.munich_config['frequency_ghz'])
            
            # Additional path loss for NLoS
            if los_probability > 0.5:
                nlos_factor = 0  # LoS
                los_grid[i] = 1.0
            else:
                nlos_factor = 20  # NLoS penalty
                los_grid[i] = 0.0
            
            total_path_loss = fspl_db + nlos_factor
            
            # Received power
            rx_power_dbm = self.munich_config['gnb_power_dbm'] - total_path_loss
            
            # SNR calculation
            noise_floor_dbm = -104  # 100MHz bandwidth
            snr_db = rx_power_dbm - noise_floor_dbm
            
            # MIMO gain
            mimo_gain_db = 10 * np.log10(min(self.munich_config['gnb_antennas'], 
                                            self.munich_config['uav_antennas']))
            snr_db += mimo_gain_db
            
            # Shannon capacity
            efficiency_factor = 0.7  # Practical efficiency
            spectral_eff = efficiency_factor * np.log2(1 + max(0.1, 10**(snr_db/10)))
            throughput_mbps = spectral_eff * self.munich_config['bandwidth_mhz']
            
            # Store results
            throughput_grid[i] = max(0, throughput_mbps)
            path_loss_grid[i] = total_path_loss
            snr_grid[i] = snr_db
            spectral_efficiency_grid[i] = spectral_eff
        
        # Reshape to grid format
        resolution = self.munich_config['grid_resolution']
        results = {
            'throughput_map': throughput_grid.reshape(resolution, resolution),
            'path_loss_map': path_loss_grid.reshape(resolution, resolution),
            'los_map': los_grid.reshape(resolution, resolution),
            'snr_map': snr_grid.reshape(resolution, resolution),
            'spectral_efficiency_map': spectral_efficiency_grid.reshape(resolution, resolution),
            'X': self.X,
            'Y': self.Y,
            'grid_positions': list(zip(self.x_flat, self.y_flat))
        }
        
        if progress_callback:
            progress_callback("Análisis de cobertura completado")
            
        return results
    
    def _calculate_los_probability(self, uav_pos, gnb_pos, buildings):
        """Calcular probabilidad LoS considerando edificios"""
        
        # ITU-R model base
        height = uav_pos[2]
        los_prob_base = 1 / (1 + 9.61 * np.exp(-0.16 * (height - 1.5)))
        
        # Check building blockage
        building_blockage = 0
        for bx, by, bh in buildings:
            # Simple 2D distance check
            dist_to_building = np.sqrt((uav_pos[0] - bx)**2 + (uav_pos[1] - by)**2)
            if dist_to_building < 50 and uav_pos[2] < bh + 10:  # Near building
                building_blockage += 0.2
        
        # Combine factors
        final_prob = max(0.1, los_prob_base - min(0.8, building_blockage))
        return final_prob
    
    def analyze_coverage_results(self, results):
        """Analizar estadísticas de cobertura"""
        
        # Extract flat arrays
        throughput_flat = results['throughput_map'].flatten()
        los_flat = results['los_map'].flatten()
        path_loss_flat = results['path_loss_map'].flatten()
        
        # Overall statistics
        total_points = len(throughput_flat)
        coverage_area_km2 = (2 * self.munich_config['coverage_range'] / 1000) ** 2
        
        # Throughput statistics
        avg_throughput = np.mean(throughput_flat)
        max_throughput = np.max(throughput_flat)
        min_throughput = np.min(throughput_flat)
        
        # LoS analysis
        los_points = int(np.sum(los_flat))
        los_percentage = (los_points / total_points) * 100
        
        # LoS vs NLoS performance
        if los_points > 0:
            avg_throughput_los = np.mean(throughput_flat[los_flat == 1])
        else:
            avg_throughput_los = 0
            
        nlos_points = total_points - los_points
        if nlos_points > 0:
            avg_throughput_nlos = np.mean(throughput_flat[los_flat == 0])
            los_advantage_db = 10 * np.log10(max(avg_throughput_los / avg_throughput_nlos, 1))
        else:
            avg_throughput_nlos = 0
            los_advantage_db = 0
        
        # Coverage quality tiers
        coverage_10mbps = (np.sum(throughput_flat > 10) / total_points) * 100
        coverage_20mbps = (np.sum(throughput_flat > 20) / total_points) * 100
        coverage_50mbps = (np.sum(throughput_flat > 50) / total_points) * 100
        
        analysis = {
            'total_points': total_points,
            'coverage_area_km2': coverage_area_km2,
            'avg_throughput_mbps': float(avg_throughput),
            'max_throughput_mbps': float(max_throughput),
            'min_throughput_mbps': float(min_throughput),
            'los_percentage': float(los_percentage),
            'los_points': los_points,
            'nlos_points': nlos_points,
            'avg_throughput_los': float(avg_throughput_los),
            'avg_throughput_nlos': float(avg_throughput_nlos),
            'los_advantage_db': float(los_advantage_db),
            'coverage_10mbps_percent': float(coverage_10mbps),
            'coverage_20mbps_percent': float(coverage_20mbps),
            'coverage_50mbps_percent': float(coverage_50mbps),
            'coverage_summary': f"Cobertura promedio {avg_throughput:.1f} Mbps en {coverage_area_km2:.1f} km²"
        }
        
        return analysis
    
    def generate_coverage_plots(self, results, progress_callback=None):
        """Generar gráficos de cobertura 2D"""
        
        if progress_callback:
            progress_callback("Generando mapas de cobertura 2D...")
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(18, 14))
        
        # Custom colormaps
        colors_throughput = ['#000080', '#0000FF', '#00FFFF', '#FFFF00', '#FF8000', '#FF0000']
        cmap_throughput = LinearSegmentedColormap.from_list('throughput', colors_throughput, N=256)
        
        # 1. Throughput Heatmap (MAIN MAP)
        im1 = ax1.contourf(results['X'], results['Y'], results['throughput_map'], 
                          levels=20, cmap=cmap_throughput)
        ax1.set_xlabel('Posición X [m]', fontweight='bold', fontsize=12)
        ax1.set_ylabel('Posición Y [m]', fontweight='bold', fontsize=12)
        ax1.set_title(f'Mapa de Throughput @ {self.munich_config["optimal_height"]}m altura\nGrid {self.munich_config["grid_resolution"]}x{self.munich_config["grid_resolution"]} Munich', 
                     fontweight='bold', fontsize=14)
        ax1.grid(True, alpha=0.4)
        
        # Add gNB position
        ax1.scatter(0, 0, s=300, c='white', marker='s', edgecolors='black', linewidth=3, label='gNB')
        ax1.legend(fontsize=11)
        
        # Colorbar
        cbar1 = plt.colorbar(im1, ax=ax1)
        cbar1.set_label('Throughput [Mbps]', fontweight='bold', fontsize=12)
        
        # 2. LoS/NLoS Map
        im2 = ax2.contourf(results['X'], results['Y'], results['los_map'], 
                          levels=[0, 0.5, 1], colors=['red', 'green'], alpha=0.7)
        ax2.set_xlabel('Posición X [m]', fontweight='bold', fontsize=12)
        ax2.set_ylabel('Posición Y [m]', fontweight='bold', fontsize=12)
        ax2.set_title('Mapa de Propagación LoS/NLoS\nCondiciones de Visibilidad Directa', 
                     fontweight='bold', fontsize=14)
        ax2.grid(True, alpha=0.4)
        ax2.scatter(0, 0, s=300, c='white', marker='s', edgecolors='black', linewidth=3)
        
        # Custom legend for LoS/NLoS
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='green', alpha=0.7, label='LoS'),
            Patch(facecolor='red', alpha=0.7, label='NLoS'),
            plt.Line2D([0], [0], marker='s', color='w', markerfacecolor='white', 
                      markeredgecolor='black', markersize=10, label='gNB')
        ]
        ax2.legend(handles=legend_elements, fontsize=11)
        
        # 3. Path Loss Map
        im3 = ax3.contourf(results['X'], results['Y'], results['path_loss_map'], 
                          levels=20, cmap='viridis_r')
        ax3.set_xlabel('Posición X [m]', fontweight='bold', fontsize=12)
        ax3.set_ylabel('Posición Y [m]', fontweight='bold', fontsize=12)
        ax3.set_title('Mapa de Path Loss\nPérdidas de Propagación', fontweight='bold', fontsize=14)
        ax3.grid(True, alpha=0.4)
        ax3.scatter(0, 0, s=300, c='white', marker='s', edgecolors='black', linewidth=3)
        
        cbar3 = plt.colorbar(im3, ax=ax3)
        cbar3.set_label('Path Loss [dB]', fontweight='bold', fontsize=12)
        
        # 4. SNR Map
        im4 = ax4.contourf(results['X'], results['Y'], results['snr_map'], 
                          levels=20, cmap='plasma')
        ax4.set_xlabel('Posición X [m]', fontweight='bold', fontsize=12)
        ax4.set_ylabel('Posición Y [m]', fontweight='bold', fontsize=12)
        ax4.set_title('Mapa de SNR\nRelación Señal/Ruido', fontweight='bold', fontsize=14)
        ax4.grid(True, alpha=0.4)
        ax4.scatter(0, 0, s=300, c='white', marker='s', edgecolors='black', linewidth=3)
        
        cbar4 = plt.colorbar(im4, ax=ax4)
        cbar4.set_label('SNR [dB]', fontweight='bold', fontsize=12)
        
        # Main title
        fig.suptitle('ANÁLISIS COBERTURA 2D MUNICH - Sistema UAV 5G NR\nMapas de Throughput, LoS/NLoS, Path Loss y SNR', 
                    fontsize=16, fontweight='bold', y=0.95)
        
        plt.tight_layout()
        plt.subplots_adjust(top=0.88)
        
        if progress_callback:
            progress_callback("Guardando mapas de cobertura...")
        
        # Save plot
        plot_path = os.path.join(self.output_dir, "coverage_analysis.png")
        plt.savefig(plot_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return plot_path
    
    def generate_3d_coverage_scene(self, results, progress_callback=None):
        """Generar escena 3D del análisis de cobertura"""
        
        if progress_callback:
            progress_callback("Generando mapa 3D de cobertura...")
        
        fig = plt.figure(figsize=(18, 14))
        ax = fig.add_subplot(111, projection='3d')
        
        # Terreno Munich base
        area = 500
        x_ground = np.linspace(-area//2, area//2, 30)
        y_ground = np.linspace(-area//2, area//2, 30)
        X_ground, Y_ground = np.meshgrid(x_ground, y_ground)
        Z_ground = 2 * np.sin(X_ground/100) * np.cos(Y_ground/100) + 1
        ax.plot_surface(X_ground, Y_ground, Z_ground, alpha=0.15, color='lightgray')
        
        # Edificios Munich
        buildings = [
            [100, 100, 20], [200, 150, 35], [300, 200, 45],
            [150, 300, 30], [350, 350, 25], [250, 50, 40]
        ]
        building_colors = ['#8B4513', '#696969', '#708090', '#2F4F4F', '#8FBC8F', '#CD853F']
        
        for i, (x, y, h) in enumerate(buildings):
            building_size = 35
            ax.bar3d(x-building_size/2, y-building_size/2, 0, building_size, building_size, h, 
                    alpha=0.5, color=building_colors[i], edgecolor='black')
        
        # gNB Tower
        gnb_x, gnb_y, gnb_z = self.munich_config['gnb_position']
        ax.scatter([gnb_x], [gnb_y], [gnb_z], c='red', s=600, marker='^', 
                  label='gNB Base Station', alpha=1.0, edgecolors='darkred', linewidth=3)
        ax.plot([gnb_x, gnb_x], [gnb_y, gnb_y], [0, gnb_z], 'darkred', linewidth=10)
        
        # Coverage grid - UAVs at grid positions colored by throughput
        throughput_flat = results['throughput_map'].flatten()
        los_flat = results['los_map'].flatten()
        
        # Normalize throughput for coloring
        norm_throughput = (throughput_flat - np.min(throughput_flat)) / (np.max(throughput_flat) - np.min(throughput_flat))
        colors = plt.cm.viridis(norm_throughput)
        
        # Plot UAVs at grid positions
        fixed_height = self.munich_config['optimal_height']
        
        for i, ((x, y), color, los, throughput) in enumerate(zip(results['grid_positions'], colors, los_flat, throughput_flat)):
            # Size based on throughput performance
            size = 50 + 100 * norm_throughput[i]
            
            # Shape based on LoS/NLoS
            if los > 0.5:  # LoS
                marker = 'o'  # Circle for LoS
                alpha = 0.8
            else:  # NLoS
                marker = 's'  # Square for NLoS
                alpha = 0.6
            
            ax.scatter([x], [y], [fixed_height], c=[color], s=size, marker=marker, 
                      alpha=alpha, edgecolors='black', linewidth=0.5)
        
        # Best coverage position (highlighted)
        max_idx = np.argmax(throughput_flat)
        best_pos = results['grid_positions'][max_idx]
        ax.scatter([best_pos[0]], [best_pos[1]], [fixed_height], c='gold', s=400, marker='*', 
                  label=f'Mejor Cobertura ({throughput_flat[max_idx]:.0f} Mbps)', alpha=1.0, 
                  edgecolors='darkorange', linewidth=3)
        
        # Coverage plane at UAV height
        coverage_range = self.munich_config['coverage_range']
        coverage_x = np.linspace(-coverage_range, coverage_range, 10)
        coverage_y = np.linspace(-coverage_range, coverage_range, 10)
        X_cov, Y_cov = np.meshgrid(coverage_x, coverage_y)
        Z_cov = np.full_like(X_cov, fixed_height)
        ax.plot_surface(X_cov, Y_cov, Z_cov, alpha=0.1, color='blue', linewidth=0)
        
        # Communication links from gNB to best positions (top 5)
        top_indices = np.argsort(throughput_flat)[-5:]
        for idx in top_indices:
            pos = results['grid_positions'][idx]
            color_strength = norm_throughput[idx]
            ax.plot([gnb_x, pos[0]], [gnb_y, pos[1]], [gnb_z, fixed_height], 
                   color=plt.cm.plasma(color_strength), linewidth=3, alpha=0.7)
        
        # Coverage area boundary
        theta = np.linspace(0, 2*np.pi, 50)
        boundary_x = coverage_range * np.cos(theta)
        boundary_y = coverage_range * np.sin(theta)
        boundary_z = np.full_like(boundary_x, fixed_height)
        ax.plot(boundary_x, boundary_y, boundary_z, 'cyan', linewidth=4, alpha=0.8, 
               label=f'Área Cobertura ({2*coverage_range}m)')
        
        # Configuration
        ax.set_xlabel('Coordenada X (metros)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Coordenada Y (metros)', fontsize=12, fontweight='bold')
        ax.set_zlabel('Altura Z (metros)', fontsize=12, fontweight='bold')
        ax.set_title('MAPA 3D MUNICH - Análisis Cobertura 2D\nGrid Performance UAV en Escenario Urbano', 
                    fontsize=16, fontweight='bold', pad=20)
        
        # Limits
        ax.set_xlim(-coverage_range-50, coverage_range+50)
        ax.set_ylim(-coverage_range-50, coverage_range+50)
        ax.set_zlim(0, 100)
        
        # Legend
        ax.legend(loc='upper left', bbox_to_anchor=(0.02, 0.98), fontsize=10)
        
        # Grid and view
        ax.grid(True, alpha=0.3)
        ax.view_init(elev=30, azim=45)
        
        plt.tight_layout()
        
        if progress_callback:
            progress_callback("Guardando escena 3D cobertura...")
        
        # Save scene
        scene_path = os.path.join(self.output_dir, "coverage_scene_3d.png")
        plt.savefig(scene_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return scene_path
    
    def save_coverage_results_json(self, results, analysis):
        """Guardar resultados del análisis en JSON"""
        
        complete_results = {
            'simulation_type': 'coverage_analysis',
            'timestamp': '2026-02-01',
            'system_config': self.system_config,
            'coverage_analysis': {
                'grid_resolution': self.munich_config['grid_resolution'],
                'coverage_area_km2': analysis['coverage_area_km2'],
                'total_points': analysis['total_points'],
                'throughput_statistics': {
                    'avg_mbps': analysis['avg_throughput_mbps'],
                    'max_mbps': analysis['max_throughput_mbps'], 
                    'min_mbps': analysis['min_throughput_mbps']
                },
                'los_analysis': {
                    'los_percentage': analysis['los_percentage'],
                    'los_points': analysis['los_points'],
                    'nlos_points': analysis['nlos_points'],
                    'los_advantage_db': analysis['los_advantage_db']
                },
                'coverage_quality': {
                    'above_10mbps': analysis['coverage_10mbps_percent'],
                    'above_20mbps': analysis['coverage_20mbps_percent'],
                    'above_50mbps': analysis['coverage_50mbps_percent']
                }
            },
            'optimization_results': analysis,
            'summary': {
                'coverage_area': f"{analysis['coverage_area_km2']:.1f} km²",
                'avg_throughput': f"{analysis['avg_throughput_mbps']:.1f} Mbps",
                'los_coverage': f"{analysis['los_percentage']:.1f}%",
                'quality_coverage': f"{analysis['coverage_20mbps_percent']:.1f}% >20Mbps",
                'recommended_config': f"Grid {self.munich_config['grid_resolution']}x{self.munich_config['grid_resolution']} @ {self.munich_config['optimal_height']}m altura"
            }
        }
        
        json_path = os.path.join(self.output_dir, "coverage_results.json")
        with open(json_path, 'w') as f:
            json.dump(complete_results, f, indent=2)
        
        return json_path
    
    def run_complete_analysis(self, progress_callback=None):
        """Ejecutar análisis completo de cobertura"""
        
        if progress_callback:
            progress_callback("Iniciando análisis de cobertura...")
        
        # 1. Calculate coverage performance
        results = self.calculate_coverage_performance(progress_callback)
        
        # 2. Analyze results
        analysis = self.analyze_coverage_results(results)
        
        if progress_callback:
            progress_callback("Generando visualizaciones cobertura...")
        
        # 3. Generate plots
        plots_path = self.generate_coverage_plots(results, progress_callback)
        
        # 4. Generate 3D scene
        scene_path = self.generate_3d_coverage_scene(results, progress_callback)
        
        # 5. Save JSON results
        json_path = self.save_coverage_results_json(results, analysis)
        
        if progress_callback:
            progress_callback("Análisis de cobertura completado!")
        
        return {
            'type': 'coverage_analysis',
            'plots': [plots_path],
            'scene_3d': scene_path,
            'data': json_path,
            'summary': f'Cobertura: {analysis["avg_throughput_mbps"]:.1f} Mbps promedio en {analysis["coverage_area_km2"]:.1f} km²',
            'config': {
                'Coverage_Analysis': {
                    'Grid_Size': f"{self.munich_config['grid_resolution']}x{self.munich_config['grid_resolution']}",
                    'Coverage_Area': f"{analysis['coverage_area_km2']:.1f} km²",
                    'Avg_Throughput_Mbps': analysis['avg_throughput_mbps'],
                    'Max_Throughput_Mbps': analysis['max_throughput_mbps'],
                    'LoS_Coverage': f"{analysis['los_percentage']:.1f}%"
                },
                'Performance': {
                    'Quality_20Mbps': f"{analysis['coverage_20mbps_percent']:.1f}%",
                    'LoS_Advantage': f"{analysis['los_advantage_db']:.1f} dB",
                    'Coverage_Summary': analysis['coverage_summary'],
                    'UAV_Height': f"{self.munich_config['optimal_height']}m"
                }
            }
        }


def run_coverage_analysis_gui(output_dir="outputs", progress_callback=None):
    """Función para ejecutar desde GUI worker thread"""
    
    coverage_analyzer = CoverageAnalysisGUI(output_dir)
    results = coverage_analyzer.run_complete_analysis(progress_callback)
    
    return results


if __name__ == "__main__":
    # Test standalone
    print("Testing Coverage Analysis GUI...")
    results = run_coverage_analysis_gui("test_outputs")
    print(f"Test completado: {results['summary']}")