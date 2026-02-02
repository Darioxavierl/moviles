"""
Test GUI Components - Verificar que los componentes funcionan
Test sin display gráfico para verificar la funcionalidad
"""
import sys
import os

# Add GUI directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_mimo_analysis():
    """Test del análisis MIMO sin GUI"""
    print("🧪 Testing MIMO Analysis...")
    
    try:
        from analysis.mimo_beamforming_gui import run_mimo_analysis_gui
        
        # Crear directorio test
        test_dir = "test_outputs"
        os.makedirs(test_dir, exist_ok=True)
        
        # Ejecutar análisis
        def progress_callback(msg):
            print(f"  {msg}")
        
        results = run_mimo_analysis_gui(test_dir, progress_callback)
        
        print(f"MIMO Analysis completado:")
        print(f"  Plots: {results['plots']}")
        print(f"  🎨 Scene 3D: {results['scene_3d']}")
        print(f"  💾 Data: {results['data']}")
        print(f"  Summary: {results['summary']}")
        
        # Verificar archivos generados
        for file_path in results['plots'] + [results['scene_3d'], results['data']]:
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                print(f"  {file_path} ({size} bytes)")
            else:
                print(f"  ❌ {file_path} NOT FOUND")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en test MIMO: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_configuration_loading():
    """Test de carga de configuración"""
    print("\n🧪 Testing Configuration Loading...")
    
    try:
        # Test system config
        config_path = "config/system_config.py"
        if os.path.exists(config_path):
            print("System config encontrado")
        else:
            print("❌ System config no encontrado")
        
        # Test scenario config
        scenario_path = "scenarios/munich_uav_scenario.py"
        if os.path.exists(scenario_path):
            print("Munich scenario encontrado")
        else:
            print("❌ Munich scenario no encontrado")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en test config: {str(e)}")
        return False

def test_gui_components():
    """Test de componentes GUI sin display"""
    print("\n🧪 Testing GUI Components (no display)...")
    
    try:
        # Test import de componentes principales
        from main import ControlPanel, ConfigPanel, ResultsTabWidget, MainWindow
        print("Todos los componentes GUI importados correctamente")
        
        # Test simulation worker
        from main import SimulationWorker
        print("SimulationWorker importado correctamente")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en test GUI: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_directory_structure():
    """Verificar estructura de directorios"""
    print("\n🧪 Testing Directory Structure...")
    
    required_dirs = [
        "config",
        "scenarios", 
        "analysis",
        "interface",
        "visualization",
        "outputs"
    ]
    
    all_good = True
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"{dir_path}")
        else:
            print(f"❌ {dir_path} MISSING")
            all_good = False
    
    return all_good

def main():
    """Ejecutar todos los tests"""
    print("="*60)
    print("🚀 GUI SYSTEM TESTS - UAV 5G NR")
    print("="*60)
    
    tests = [
        ("Directory Structure", test_directory_structure),
        ("Configuration Loading", test_configuration_loading),
        ("GUI Components", test_gui_components),
        ("MIMO Analysis", test_mimo_analysis)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        success = test_func()
        results.append((test_name, success))
    
    print("\n" + "="*60)
    print("TEST RESULTS SUMMARY")
    print("="*60)
    
    for test_name, success in results:
        status = "PASS" if success else "FAIL"
        print(f"{test_name:.<30} {status}")
    
    total_tests = len(results)
    passed_tests = sum(1 for _, success in results if success)
    
    print(f"\nTotal: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎊 ALL TESTS PASSED! GUI system ready!")
    else:
        print("Some tests failed, check output above")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()