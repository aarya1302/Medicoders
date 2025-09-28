"""
Clean WA Health Model - Remove Data Leakage
Trains admission prediction WITHOUT departure_status (target leak)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, roc_auc_score
import pickle

def train_clean_model():
    """Train model without data leakage"""
    print("🧹 Training Clean WA Health Model (No Data Leakage)")
    print("=" * 50)

    # Load data
    print("📊 Loading datasets...")
    eddc_cols = [
        'synth_person_ID', 'presentation_datetime',
        'age', 'sex', 'triage_category', 'mode_of_arrival',
        'primary_diagnosis_ICD10AM_chapter', 'mental_health_attendance',
        'metropolitan_hospital_flag', 'affected_by_drugs_and_or_alcohol',
        'self_harm_attendance'
        # NOTE: Excluding departure_status - this is data leakage!
    ]

    hmdc_cols = [
        'synth_person_ID', 'admission_datetime', 'age', 'sex'
    ]

    eddc_df = pd.read_csv('data/synthetic_eddc_linked_representative_v20250715_01.csv', usecols=eddc_cols, nrows=100000)
    hmdc_df = pd.read_csv('data/synthetic_hmdc_linked_representative_v20250704_01.csv', usecols=hmdc_cols, nrows=100000)

    print(f"✅ EDDC: {len(eddc_df):,} presentations")
    print(f"✅ HMDC: {len(hmdc_df):,} admissions")

    # Convert datetime
    eddc_df['presentation_datetime'] = pd.to_datetime(eddc_df['presentation_datetime'])
    hmdc_df['admission_datetime'] = pd.to_datetime(hmdc_df['admission_datetime'])

    # Create admission linkage
    print("🔗 Linking admissions...")
    hmdc_by_person = hmdc_df.groupby('synth_person_ID')
    admission_flags = []

    for idx, ed_record in eddc_df.iterrows():
        if idx % 10000 == 0:
            print(f"   Processed {idx:,} records...")

        person_id = ed_record['synth_person_ID']
        ed_time = ed_record['presentation_datetime']

        if person_id in hmdc_by_person.groups:
            person_admissions = hmdc_by_person.get_group(person_id)
            time_window = (person_admissions['admission_datetime'] >= ed_time) & \
                         (person_admissions['admission_datetime'] <= ed_time + timedelta(hours=24))
            admitted = 1 if time_window.any() else 0
        else:
            admitted = 0

        admission_flags.append(admitted)

    eddc_df['admitted'] = admission_flags
    admission_rate = np.mean(admission_flags)
    print(f"✅ Admission rate: {admission_rate:.1%}")

    # Feature engineering
    print("🔧 Engineering features...")

    # Encoders
    encoders = {}
    cat_features = ['sex', 'primary_diagnosis_ICD10AM_chapter', 'mode_of_arrival']

    for col in cat_features:
        if col in eddc_df.columns:
            le = LabelEncoder()
            eddc_df[col + '_encoded'] = le.fit_transform(eddc_df[col].astype(str).fillna('Unknown'))
            encoders[col] = le

    # Time features
    eddc_df['presentation_hour'] = eddc_df['presentation_datetime'].dt.hour
    eddc_df['is_weekend'] = (eddc_df['presentation_datetime'].dt.dayofweek >= 5).astype(int)
    eddc_df['is_night'] = ((eddc_df['presentation_hour'] >= 22) | (eddc_df['presentation_hour'] <= 6)).astype(int)

    # Age features
    eddc_df['elderly'] = (eddc_df['age'] >= 65).astype(int)
    eddc_df['pediatric'] = (eddc_df['age'] < 18).astype(int)

    # Acuity
    eddc_df['high_acuity'] = (eddc_df['triage_category'] <= 2).astype(int)

    # Select features (NO departure_status!)
    feature_cols = [
        'age', 'triage_category', 'presentation_hour',
        'sex_encoded', 'primary_diagnosis_ICD10AM_chapter_encoded', 'mode_of_arrival_encoded',
        'mental_health_attendance', 'metropolitan_hospital_flag',
        'affected_by_drugs_and_or_alcohol', 'self_harm_attendance',
        'is_weekend', 'is_night', 'elderly', 'pediatric', 'high_acuity'
    ]

    X = eddc_df[feature_cols].fillna(0)
    y = eddc_df['admitted']

    print(f"✅ Features: {len(feature_cols)} (no data leakage)")
    print(f"✅ Samples: {len(X):,}")
    print(f"✅ Positive rate: {y.mean():.1%}")

    # Train model
    print("🚀 Training model...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    model = GradientBoostingClassifier(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42)
    model.fit(X_train, y_train)

    # Evaluate
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, y_pred_proba)

    print(f"✅ Model trained!")
    print(f"📊 AUC Score: {auc:.3f}")

    # Feature importance
    importance_df = pd.DataFrame({
        'feature': feature_cols,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)

    print("\n🔝 Top 10 Important Features:")
    print(importance_df.head(10))

    # Save clean model
    model_package = {
        'model': model,
        'feature_names': feature_cols,
        'encoders': encoders,
        'auc_score': auc,
        'model_type': 'WA_Health_Clean_Predictor'
    }

    filename = 'wa_health_clean_model.pkl'
    with open(filename, 'wb') as f:
        pickle.dump(model_package, f)

    print(f"\n✅ Clean model saved as '{filename}'")
    print(f"🎯 No data leakage - ready for real predictions!")

    return model_package

if __name__ == "__main__":
    train_clean_model()