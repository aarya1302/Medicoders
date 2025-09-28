#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug WA Health model predictions for severe patients
"""

import pickle
import pandas as pd
import numpy as np
from backend.patient_model import create_patient_from_form
from backend.ml_engine import LiveMLEngine

def debug_prediction():
    """Debug a severe patient prediction step by step"""

    print("🔍 DEBUGGING SEVERE PATIENT PREDICTION\n")

    # Create a severe patient profile
    severe_patient_data = {
        'age': 75,  # Elderly
        'arrival_method': 'Ambulance',  # High acuity arrival
        'hospital_type': 'metro',
        'establishment_code': '8002.0',
        'metropolitan_hospital_flag': 1,
        'pain_level': 9,  # Severe pain
        'chest_pain': True,  # High-risk symptom
        'shortness_breath': True,  # High-risk symptom
        'altered_mental': True,  # High-risk symptom
        'heart_rate': 120,  # Optional vital
    }

    print("📋 SEVERE PATIENT PROFILE:")
    for key, value in severe_patient_data.items():
        print(f"   {key}: {value}")

    # Create patient object
    patient = create_patient_from_form(severe_patient_data, 'debug_session')
    print(f"\n👤 PATIENT OBJECT CREATED:")
    print(f"   ID: {patient.id[:8]}")
    print(f"   Age: {patient.age}")
    print(f"   ESI Level: {patient.esi_level}")
    print(f"   Establishment: {patient.establishment_code}")
    print(f"   Metro Flag: {patient.metropolitan_hospital_flag}")
    print(f"   Symptoms: chest_pain={patient.chest_pain}, shortness_breath={patient.shortness_breath}")

    # Load ML engine and get prediction
    engine = LiveMLEngine()

    # Get the feature vector that will be sent to the model
    features = engine.patient_to_features(patient)
    print(f"\n🔧 FEATURE VECTOR:")
    for key, value in features.items():
        print(f"   {key}: {value}")

    # Get prediction
    prob = engine.predict_admission_probability(patient)
    print(f"\n📊 PREDICTION RESULT:")
    print(f"   Admission Probability: {prob:.1%}")
    print(f"   Expected for severe patient: >50%")
    print(f"   ISSUE: {'❌ TOO LOW' if prob < 0.3 else '✅ REASONABLE'}")

    return prob, features

def test_model_directly():
    """Test the model directly with manual features"""

    print(f"\n🧪 TESTING MODEL DIRECTLY\n")

    # Load the model
    with open('wa_health_admission_model.pkl', 'rb') as f:
        model_data = pickle.load(f)

    model = model_data['model']
    feature_columns = model_data['feature_columns']
    encoders = model_data['label_encoders']

    print(f"📊 MODEL INFO:")
    print(f"   Required features: {len(feature_columns)}")
    print(f"   Encoders: {len(encoders)}")

    # Create a high-risk feature vector manually
    high_risk_features = {}

    for feature in feature_columns:
        if 'age' == feature:
            high_risk_features[feature] = 75  # Elderly
        elif 'triage_category' == feature:
            high_risk_features[feature] = 1  # ESI 1 (critical)
        elif 'ed_visits_last_year' == feature:
            high_risk_features[feature] = 5  # Frequent visitor
        elif 'high_acuity' == feature:
            high_risk_features[feature] = 1  # High acuity
        elif 'presentation_hour' == feature:
            high_risk_features[feature] = 2  # 2 AM (high-risk time)
        elif 'metropolitan_hospital_flag' == feature:
            high_risk_features[feature] = 1  # Metro
        elif 'complexity_score' == feature:
            high_risk_features[feature] = 0.8  # High complexity
        elif '_encoded' in feature:
            high_risk_features[feature] = 0  # Will be encoded
        else:
            high_risk_features[feature] = 0  # Default

    # Apply encoders
    df = pd.DataFrame([high_risk_features])

    for col, encoder in encoders.items():
        if col in df.columns:
            try:
                if col == 'establishment_code':
                    df[col + '_encoded'] = encoder.transform(['8002.0'])  # Metro hospital
                elif col == 'primary_diagnosis_ICD10AM_chapter':
                    df[col + '_encoded'] = encoder.transform(['I0'])  # Cardiovascular
                elif col == 'mode_of_arrival':
                    df[col + '_encoded'] = encoder.transform(['3.0'])  # Ambulance
                else:
                    df[col + '_encoded'] = encoder.transform(['1'])  # Default
            except:
                df[col + '_encoded'] = 0

    # Select only the features the model expects
    X = df[feature_columns].fillna(0)

    print(f"\n📋 MANUAL HIGH-RISK FEATURES:")
    for col in feature_columns:
        if col in X.columns:
            print(f"   {col}: {X[col].iloc[0]}")

    # Get prediction
    prob = model.predict_proba(X)[0][1]
    print(f"\n📊 DIRECT MODEL PREDICTION:")
    print(f"   High-risk manual features: {prob:.1%}")
    print(f"   Expected: >50% for high-risk patient")

    return prob

if __name__ == "__main__":
    prob1, features = debug_prediction()
    prob2 = test_model_directly()

    print(f"\n🎯 SUMMARY:")
    print(f"   Patient object prediction: {prob1:.1%}")
    print(f"   Direct model prediction: {prob2:.1%}")
    print(f"   Issue: Model may have low baseline admission rate or feature mapping problems")