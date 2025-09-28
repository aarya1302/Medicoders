#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analyze WA Health admission model features for mobile form design
"""

import pickle
import pandas as pd
import numpy as np

def analyze_wa_health_model():
    """Load and analyze the WA Health admission model"""

    print("Loading WA Health admission model...")

    try:
        with open('wa_health_admission_model.pkl', 'rb') as f:
            model_data = pickle.load(f)

        print("✅ Model loaded successfully!")
        print(f"📊 Model type: {model_data.get('model_type', 'Unknown')}")
        print(f"📈 AUC Score: {model_data.get('auc_score', 'Unknown')}")

        # Analyze feature columns
        feature_columns = model_data.get('feature_columns', [])
        print(f"\n🔧 Total Features: {len(feature_columns)}")
        print("\n📋 Required Features:")
        for i, feature in enumerate(feature_columns, 1):
            print(f"   {i:2d}. {feature}")

        # Analyze label encoders
        label_encoders = model_data.get('label_encoders', {})
        print(f"\n🏷️  Categorical Features ({len(label_encoders)}):")
        for col, encoder in label_encoders.items():
            classes = encoder.classes_
            print(f"   {col}: {len(classes)} categories")
            print(f"      Values: {list(classes)}")

        # Check if we have feature importance
        if 'feature_importance' in model_data:
            importance = model_data['feature_importance']
            print(f"\n🔝 Top 10 Most Important Features:")
            for i, (feature, imp) in enumerate(importance.head(10).iterrows(), 1):
                print(f"   {i:2d}. {feature:<35} {imp['importance']:.1%}")

        # Analyze model object
        model = model_data.get('model')
        if model:
            print(f"\n🤖 Model Details:")
            print(f"   Algorithm: {type(model).__name__}")
            if hasattr(model, 'n_estimators'):
                print(f"   Estimators: {model.n_estimators}")
            if hasattr(model, 'max_depth'):
                print(f"   Max Depth: {model.max_depth}")

        return model_data

    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return None

def create_sample_prediction(model_data):
    """Create a sample prediction to understand input format"""

    if not model_data:
        return

    print(f"\n🧪 Testing Sample Prediction...")

    # Create sample data based on feature columns
    feature_columns = model_data.get('feature_columns', [])
    sample_data = {}

    for feature in feature_columns:
        if 'age' in feature.lower():
            sample_data[feature] = 45
        elif 'encoded' in feature:
            sample_data[feature] = 0  # Will be encoded value
        elif 'hour' in feature.lower():
            sample_data[feature] = 14  # 2 PM
        elif 'category' in feature.lower():
            sample_data[feature] = 3  # ESI level 3
        elif 'visits' in feature.lower():
            sample_data[feature] = 2  # Previous visits
        elif 'score' in feature.lower():
            sample_data[feature] = 0.5  # Some score
        else:
            sample_data[feature] = 0  # Default

    try:
        # Create DataFrame
        df = pd.DataFrame([sample_data])

        # Get prediction
        model = model_data['model']

        # Try prediction
        prediction = model.predict_proba(df)[0][1]
        print(f"✅ Sample prediction successful: {prediction:.1%} admission probability")

        print(f"\n📊 Sample Input Features:")
        for feature, value in sample_data.items():
            print(f"   {feature:<35} = {value}")

    except Exception as e:
        print(f"❌ Sample prediction failed: {e}")

if __name__ == "__main__":
    model_data = analyze_wa_health_model()
    create_sample_prediction(model_data)