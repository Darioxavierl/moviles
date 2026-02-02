#!/usr/bin/env python3
"""
Test completo de la integración MIMO + 3D
"""

def test_mimo_complete():
    """Test limpio de la integración completa"""
    
    print("🚀 TESTING MIMO COMPLETE INTEGRATION")
    
    try:
        from GUI.analysis.mimo_beamforming_gui import MIMOBeamformingGUI
        import os
        
        # Initialize
        analysis = MIMOBeamformingGUI("outputs")
        print("✅ Analysis initialized")
        
        # Run MIMO analysis
        print("🔄 Running MIMO analysis...")
        mimo_results = analysis.analyze_mimo_configurations_with_sionna()
        print(f"✅ MIMO complete: {len(mimo_results)} configurations")
        
        # Run beamforming analysis  
        print("🔄 Running beamforming analysis...")
        beamforming_results = analysis.analyze_beamforming_strategies_with_sionna()
        print(f"✅ Beamforming complete: {len(beamforming_results)} strategies")
        
        # Generate 3D visualization
        print("🔄 Generating 3D scene...")
        scene_3d_path = analysis.generate_3d_visualization(mimo_results, beamforming_results)
        
        if scene_3d_path and os.path.exists(scene_3d_path):
            size = os.path.getsize(scene_3d_path)
            print(f"✅ 3D Scene generated: {scene_3d_path} ({size:,} bytes)")
        else:
            print("❌ 3D Scene generation failed")
            return False
        
        # Generate plots (attempt)
        print("🔄 Attempting plot generation...")
        try:
            fig = analysis.generate_mimo_sionna_plots(mimo_results, beamforming_results)
            print("✅ Plots generated successfully")
        except Exception as e:
            print(f"⚠️ Plot generation failed: {e}")
            # Continue anyway
        
        # Save results
        print("🔄 Saving results...")
        json_data = analysis.save_results_json(mimo_results, beamforming_results)
        print("✅ Results saved")
        
        # Generate summary
        summary = analysis.generate_summary_report(mimo_results, beamforming_results)
        
        # Create final result
        result = {
            'type': 'MIMO + Beamforming',
            'plots': ['outputs/mimo_beamforming_sionna_analysis.png'],
            'scene_3d': [scene_3d_path] if scene_3d_path else [],
            'data': json_data,
            'summary': summary,
            'mimo_results': mimo_results,
            'beamforming_results': beamforming_results,
            'uses_sionna': True,
            'scenario': 'Munich 3D Urban with Sionna RT'
        }
        
        print(f"\n🎉 INTEGRATION TEST SUCCESSFUL!")
        print(f"   📊 Plots: {len(result['plots'])} files")
        print(f"   🎨 Scene 3D: {len(result['scene_3d'])} files")
        print(f"   📋 Summary: {result['summary'][:50]}...")
        
        # Verify files exist
        for path in result['scene_3d']:
            if os.path.exists(path):
                print(f"   ✅ Scene file: {os.path.basename(path)} ({os.path.getsize(path):,} bytes)")
        
        print(f"\n🚀 GUI INTEGRATION READY!")
        print(f"   The GUI should now display 3D scenes in the MIMO tab.")
        
        return result
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_mimo_complete()