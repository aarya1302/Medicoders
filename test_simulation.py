#!/usr/bin/env python3
"""
Quick test script to verify Live ED Simulation components
"""

import sys
import os

def test_imports():
    """Test all required imports"""
    print("🧪 Testing imports...")
    
    try:
        import websockets
        print("  ✅ websockets")
    except ImportError as e:
        print(f"  ❌ websockets: {e}")
        return False
    
    try:
        import qrcode
        print("  ✅ qrcode")
    except ImportError as e:
        print(f"  ❌ qrcode: {e}")
        return False
        
    try:
        import plotly
        print("  ✅ plotly")
    except ImportError as e:
        print(f"  ❌ plotly: {e}")
        return False
    
    try:
        import pandas as pd
        print("  ✅ pandas")
    except ImportError as e:
        print(f"  ❌ pandas: {e}")
        return False
    
    try:
        import streamlit as st
        print("  ✅ streamlit")
    except ImportError as e:
        print(f"  ❌ streamlit: {e}")
        return False
    
    return True

def test_backend_components():
    """Test backend components"""
    print("\n🔧 Testing backend components...")
    
    # Add current directory to path
    sys.path.insert(0, os.path.dirname(__file__))
    
    try:
        from backend.patient_model import PatientDatabase, create_patient_from_form
        print("  ✅ Patient model")
        
        # Test database creation
        db = PatientDatabase(db_path=":memory:")  # In-memory database for testing
        print("  ✅ Database initialization")
        
        # Test patient creation
        test_form_data = {
            'age': 45,
            'pain_level': 7,
            'chest_pain': True,
            'arrival_method': 'Ambulance'
        }
        patient = create_patient_from_form(test_form_data, "test_session")
        print(f"  ✅ Patient creation (ID: {patient.id[:8]})")
        
        # Test database operations
        success = db.add_patient(patient)
        if success:
            print("  ✅ Database operations")
        else:
            print("  ❌ Database operations failed")
            return False
            
    except Exception as e:
        print(f"  ❌ Backend components: {e}")
        return False
    
    try:
        from backend.ml_engine import LiveMLEngine
        print("  ✅ ML engine import")
        
        # Test ML engine (without loading full model)
        engine = LiveMLEngine()
        print("  ✅ ML engine initialization")
        
    except Exception as e:
        print(f"  ❌ ML engine: {e}")
        return False
    
    return True

def test_qr_generation():
    """Test QR code generation"""
    print("\n📱 Testing QR code generation...")
    
    try:
        sys.path.insert(0, os.path.dirname(__file__))
        from demo.qr_generator import QRCodeGenerator
        
        generator = QRCodeGenerator()
        print("  ✅ QR generator initialization")
        
        # Test QR creation
        qr_img, patient_id, url = generator.create_patient_qr("TEST-001")
        print(f"  ✅ QR code creation (Patient: {patient_id})")
        print(f"  📱 URL: {url}")
        
    except Exception as e:
        print(f"  ❌ QR generation: {e}")
        return False
    
    return True

def main():
    """Run all tests"""
    print("🏥 WA Health Live ED Simulation - Component Test")
    print("=" * 50)
    
    success = True
    
    # Test imports
    if not test_imports():
        success = False
    
    # Test backend
    if not test_backend_components():
        success = False
    
    # Test QR generation
    if not test_qr_generation():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 ALL TESTS PASSED! System ready for demo.")
        print("\n🚀 Next steps:")
        print("  1. Run: python start_simulation.py")
        print("  2. Open dashboard at http://https://medicoded-dashboard.fly.dev/")
        print("  3. Test mobile form at http://https://medicoded-form.fly.dev/")
    else:
        print("❌ SOME TESTS FAILED! Check errors above.")
        print("\n💡 Try:")
        print("  1. source venv/bin/activate")
        print("  2. pip install -r requirements_live.txt")
    
    return success

if __name__ == "__main__":
    main()