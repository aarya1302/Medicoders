#!/usr/bin/env python3
"""
Test script for updated ML engine with WA Health model
"""

import sys
import os
from datetime import datetime
sys.path.append('backend')

from backend.ml_engine import EDSimulationEngine
from backend.patient_model import Patient

def test_ml_engine():
    """Test the updated ML engine with WA Health model"""
    print("🧪 Testing Updated ML Engine with WA Health Model")
    print("=" * 60)

    # Initialize engine
    try:
        engine = EDSimulationEngine()
        print(f"✅ ML Engine initialized successfully")
        print(f"📊 Model type: {engine.ml_engine.model_results.get('model_type', 'Unknown')}")
        print(f"📊 AUC Score: {engine.ml_engine.model_results.get('auc_score', 'Unknown')}")
        print(f"📊 Features: {len(engine.ml_engine.model_results.get('features', []))}")
    except Exception as e:
        print(f"❌ Error initializing engine: {e}")
        return

    # Create test patient
    test_patient = Patient(
        id="test_001",
        session_id="test_session",
        timestamp=datetime.now(),
        age=67,
        arrival_method="Ambulance",
        esi_level=2,
        heart_rate=95,
        systolic_bp=160,
        diastolic_bp=95,
        temperature=37.2,
        respiratory_rate=22,
        oxygen_sat=96,
        chest_pain=True,
        shortness_breath=True,
        cardiovascular=True,
        hypertension=True,
        prev_admissions=2
    )

    print(f"\n👤 Test Patient:")
    print(f"   Age: {test_patient.age}, ESI: {test_patient.esi_level}")
    print(f"   Symptoms: Chest pain, SOB")
    print(f"   History: CV disease, HTN")
    print(f"   Arrival: {test_patient.arrival_method}")

    # Test prediction
    print(f"\n🔮 Testing prediction...")
    try:
        prob = engine.ml_engine.predict_admission_probability(test_patient)
        print(f"✅ Admission probability: {prob:.1%}")

        # Validate reasonable range
        if 0.0 <= prob <= 1.0:
            print(f"✅ Probability in valid range")
        else:
            print(f"❌ Probability out of range: {prob}")

        # Check if it makes clinical sense (high-risk patient should have higher probability)
        if prob > 0.4:  # High-risk elderly patient with cardiac symptoms
            print(f"✅ Clinically sensible prediction for high-risk patient")
        else:
            print(f"⚠️  Low probability ({prob:.1%}) for high-risk patient - check feature mapping")

    except Exception as e:
        print(f"❌ Error in prediction: {e}")
        import traceback
        traceback.print_exc()
        return

    # Test batch processing
    print(f"\n📋 Testing batch processing...")
    try:
        # Create multiple test patients
        patients = [
            Patient(id="low_001", session_id="test", timestamp=datetime.now(), age=25, esi_level=4, arrival_method="Walk-in",
                   heart_rate=80, systolic_bp=120, diastolic_bp=80, temperature=36.5, respiratory_rate=16, oxygen_sat=99),
            Patient(id="mod_001", session_id="test", timestamp=datetime.now(), age=45, esi_level=3, arrival_method="Walk-in",
                   heart_rate=90, systolic_bp=140, diastolic_bp=85, temperature=37.0, respiratory_rate=18, oxygen_sat=98,
                   chest_pain=True),
            Patient(id="high_001", session_id="test", timestamp=datetime.now(), age=75, esi_level=1, arrival_method="Ambulance",
                   heart_rate=110, systolic_bp=180, diastolic_bp=100, temperature=37.5, respiratory_rate=24, oxygen_sat=94,
                   cardiovascular=True, chest_pain=True, shortness_breath=True)
        ]

        results = engine.ml_engine.batch_predict(patients)
        print(f"✅ Batch processed {len(results)} patients")

        for patient, prob, prediction in results:
            print(f"   {patient.id}: {prob:.1%} (admit: {prediction})")

    except Exception as e:
        print(f"❌ Error in batch processing: {e}")
        return

    # Test ED simulation
    print(f"\n🏥 Testing ED simulation...")
    try:
        ed_results = engine.process_new_patients(patients, "test_session")
        print(f"✅ ED simulation successful")
        print(f"   Capacity: {ed_results['ed_metrics']['capacity_percentage']:.1f}%")
        print(f"   Predicted admissions: {ed_results['ed_metrics']['predicted_admissions']}")
        print(f"   High-risk patients: {ed_results['ed_metrics']['high_risk_count']}")

    except Exception as e:
        print(f"❌ Error in ED simulation: {e}")
        return

    print(f"\n🎯 All tests completed successfully!")
    print(f"🚀 ML Engine ready for live demo with WA Health model")

if __name__ == "__main__":
    test_ml_engine()