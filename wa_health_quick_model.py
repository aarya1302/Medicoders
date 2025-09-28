"""
Quick WA Health Model Training - Streamlined for Real Data
Efficiently processes large EDDC/HMDC datasets for admission prediction
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

def load_and_link_data():
    """Load and link EDDC/HMDC datasets efficiently"""
    print("🔄 Loading WA Health datasets...")

    # Load EDDC with only essential columns for linking
    eddc_cols = [
        'synth_person_ID', 'presentation_datetime', 'discharge_datetime',
        'age', 'sex', 'triage_category', 'departure_status', 'mode_of_arrival',
        'primary_diagnosis_ICD10AM_chapter', 'mental_health_attendance',
        'metropolitan_hospital_flag', 'affected_by_drugs_and_or_alcohol',
        'self_harm_attendance'
    ]

    # Load HMDC with only essential columns
    hmdc_cols = [
        'synth_person_ID', 'admission_datetime', 'age', 'sex',
        'admission_status', 'care_type', 'major_diagnostic_categ_current'
    ]

    print("📊 Loading EDDC data...")
    eddc_df = pd.read_csv('data/synthetic_eddc_linked_representative_v20250715_01.csv', usecols=eddc_cols)
    print(f"✅ EDDC loaded: {len(eddc_df):,} presentations")

    print("📊 Loading HMDC data...")
    hmdc_df = pd.read_csv('data/synthetic_hmdc_linked_representative_v20250704_01.csv', usecols=hmdc_cols)
    print(f"✅ HMDC loaded: {len(hmdc_df):,} admissions")

    # Convert datetime columns
    eddc_df['presentation_datetime'] = pd.to_datetime(eddc_df['presentation_datetime'])
    hmdc_df['admission_datetime'] = pd.to_datetime(hmdc_df['admission_datetime'])

    print("🔗 Creating admission linkage...")

    # For efficiency, create a dictionary of HMDC admissions by person ID
    hmdc_by_person = hmdc_df.groupby('synth_person_ID')

    # Process EDDC records to find linked admissions
    admission_flags = []

    for idx, ed_record in eddc_df.iterrows():
        if idx % 10000 == 0:
            print(f"   Processed {idx:,} records...")

        person_id = ed_record['synth_person_ID']
        ed_time = ed_record['presentation_datetime']

        # Check if this person has any admissions
        if person_id in hmdc_by_person.groups:
            person_admissions = hmdc_by_person.get_group(person_id)

            # Find admissions within 24 hours of ED presentation
            time_window = (person_admissions['admission_datetime'] >= ed_time) & \
                         (person_admissions['admission_datetime'] <= ed_time + timedelta(hours=24))

            admitted = 1 if time_window.any() else 0
        else:
            admitted = 0

        admission_flags.append(admitted)

    # Add admission target to EDDC data
    eddc_df['admitted'] = admission_flags

    admission_rate = np.mean(admission_flags)
    print(f"✅ Linking complete!")
    print(f"📊 Admission rate: {admission_rate:.1%}")
    print(f"📊 Admitted patients: {sum(admission_flags):,}")

    return eddc_df

def prepare_features(df):
    """Prepare features for machine learning"""
    print("🔧 Preparing features...")

    # Create categorical encoders
    encoders = {}

    # Categorical features to encode
    cat_features = ['sex', 'primary_diagnosis_ICD10AM_chapter', 'mode_of_arrival', 'departure_status']

    for col in cat_features:
        if col in df.columns:
            le = LabelEncoder()
            df[col + '_encoded'] = le.fit_transform(df[col].astype(str).fillna('Unknown'))
            encoders[col] = le

    # Create time-based features
    df['presentation_hour'] = df['presentation_datetime'].dt.hour
    df['is_weekend'] = (df['presentation_datetime'].dt.dayofweek >= 5).astype(int)
    df['is_night'] = ((df['presentation_hour'] >= 22) | (df['presentation_hour'] <= 6)).astype(int)

    # Age groups
    df['elderly'] = (df['age'] >= 65).astype(int)
    df['pediatric'] = (df['age'] < 18).astype(int)

    # High-risk flags
    df['high_acuity'] = (df['triage_category'] <= 2).astype(int)

    # Select features for modeling
    feature_cols = [
        'age', 'triage_category', 'presentation_hour',
        'sex_encoded', 'primary_diagnosis_ICD10AM_chapter_encoded',
        'mode_of_arrival_encoded', 'departure_status_encoded',
        'mental_health_attendance', 'metropolitan_hospital_flag',
        'affected_by_drugs_and_or_alcohol', 'self_harm_attendance',
        'is_weekend', 'is_night', 'elderly', 'pediatric', 'high_acuity'
    ]

    # Filter to available columns
    available_features = [col for col in feature_cols if col in df.columns]

    X = df[available_features].fillna(0)
    y = df['admitted']

    print(f"✅ Features prepared: {len(available_features)} features, {len(X):,} samples")

    return X, y, available_features, encoders

def train_model(X, y, feature_names):
    """Train admission prediction model"""
    print("🚀 Training admission prediction model...")

    if y.sum() == 0:
        print("❌ No positive cases found - cannot train model")
        return None

    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Train model
    model = GradientBoostingClassifier(
        n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42
    )

    model.fit(X_train, y_train)

    # Evaluate
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, y_pred_proba)

    print(f"✅ Model trained!")
    print(f"📊 AUC Score: {auc:.3f}")
    print(f"📊 Training samples: {len(X_train):,}")
    print(f"📊 Test samples: {len(X_test):,}")

    # Feature importance
    importance_df = pd.DataFrame({
        'feature': feature_names,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)

    print("\n🔝 Top 10 Important Features:")
    print(importance_df.head(10))

    return model, auc, importance_df

def save_model(model, feature_names, encoders, auc_score):
    """Save trained model and components"""
    model_package = {
        'model': model,
        'feature_names': feature_names,
        'encoders': encoders,
        'auc_score': auc_score,
        'model_type': 'WA_Health_Admission_Predictor'
    }

    filename = 'wa_health_admission_model.pkl'
    with open(filename, 'wb') as f:
        pickle.dump(model_package, f)

    print(f"✅ Model saved as '{filename}'")
    return filename

def main():
    """Main training pipeline"""
    print("🏥 WA Health Quick Model Training")
    print("=" * 40)

    try:
        # Load and link data
        df = load_and_link_data()

        # Prepare features
        X, y, feature_names, encoders = prepare_features(df)

        # Train model
        model, auc, importance = train_model(X, y, feature_names)

        if model is not None:
            # Save model
            save_model(model, feature_names, encoders, auc)

            print(f"\n✅ Training Complete!")
            print(f"🎯 Model ready for integration")
            print(f"📊 Final AUC: {auc:.3f}")
        else:
            print("❌ Training failed")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()