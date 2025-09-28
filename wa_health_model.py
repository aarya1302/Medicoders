"""
WA Health Synthetic Data Admission Prediction Model
Trains on linked EDDC (Emergency Department) and HMDC (Hospital Morbidity) datasets
to predict inpatient admission from ED triage data
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, roc_curve
from sklearn.impute import SimpleImputer
import pickle

import matplotlib.pyplot as plt
import seaborn as sns

class WAHealthAdmissionPredictor:
    """Predict ED to inpatient admission using WA Health synthetic datasets"""

    def __init__(self, eddc_path: str = None, hmdc_path: str = None):
        """
        Initialize with paths to EDDC and HMDC datasets

        Args:
            eddc_path: Path to EDDC (Emergency Department) CSV file
            hmdc_path: Path to HMDC (Hospital Morbidity) CSV file
        """
        self.eddc_path = eddc_path
        self.hmdc_path = hmdc_path
        self.eddc_df = None
        self.hmdc_df = None
        self.linked_df = None
        self.model = None
        self.feature_columns = []
        self.label_encoders = {}
        self.scaler = StandardScaler()

    def load_datasets(self):
        """Load and validate EDDC and HMDC datasets"""
        print("🔄 Loading WA Health synthetic datasets...")

        try:
            # Load EDDC (Emergency Department) data - using subset for testing
            if self.eddc_path and Path(self.eddc_path).exists():
                print("🔄 Loading EDDC data (using subset for initial testing)...")
                self.eddc_df = pd.read_csv(self.eddc_path)  # Limit for testing
                print(f"✅ EDDC loaded: {len(self.eddc_df):,} ED presentations")
            else:
                print("⚠️ EDDC file not found - using demo data")
                self.eddc_df = self._create_demo_eddc()

            # Load HMDC (Hospital Morbidity) data - using subset for testing
            if self.hmdc_path and Path(self.hmdc_path).exists():
                print("🔄 Loading HMDC data (using subset for initial testing)...")
                self.hmdc_df = pd.read_csv(self.hmdc_path)  # Limit for testing
                print(f"✅ HMDC loaded: {len(self.hmdc_df):,} inpatient admissions")
            else:
                print("⚠️ HMDC file not found - using demo data")
                self.hmdc_df = self._create_demo_hmdc()

            # Convert datetime columns
            if 'presentation_datetime' in self.eddc_df.columns:
                self.eddc_df['presentation_datetime'] = pd.to_datetime(self.eddc_df['presentation_datetime'])
            if 'admission_datetime' in self.hmdc_df.columns:
                self.hmdc_df['admission_datetime'] = pd.to_datetime(self.hmdc_df['admission_datetime'])

            # Display dataset info
            print(f"\n📊 Dataset Overview:")
            print(f"EDDC columns: {list(self.eddc_df.columns)}")
            print(f"HMDC columns: {list(self.hmdc_df.columns)}")
            print(f"EDDC date range: {self.eddc_df['presentation_datetime'].min()} to {self.eddc_df['presentation_datetime'].max()}")
            print(f"HMDC date range: {self.hmdc_df['admission_datetime'].min()} to {self.hmdc_df['admission_datetime'].max()}")

        except Exception as e:
            print(f"❌ Error loading datasets: {e}")
            print("🔄 Creating demo datasets...")
            self.eddc_df = self._create_demo_eddc()
            self.hmdc_df = self._create_demo_hmdc()

    def _create_demo_eddc(self):
        """Create demo EDDC dataset matching WA Health structure"""
        np.random.seed(42)
        n_patients = 10000

        # Generate synthetic person IDs
        person_ids = [f"P{i+1:06d}" for i in range(n_patients)]

        # Generate realistic ED data
        data = {
            'synth_person_ID': person_ids,
            'age': np.random.normal(45, 20, n_patients).clip(0, 100).astype(int),
            'sex': np.random.choice(['M', 'F'], n_patients),
            'ethnicity': np.random.choice(['Caucasian', 'Aboriginal', 'Asian', 'Other'], n_patients, p=[0.7, 0.15, 0.1, 0.05]),
            'presentation_datetime': pd.date_range('2023-01-01', periods=n_patients, freq='H'),
            'triage_category': np.random.choice([1, 2, 3, 4, 5], n_patients, p=[0.05, 0.15, 0.35, 0.35, 0.1]),
            'mode_of_arrival': np.random.choice(['Walk-in', 'Ambulance', 'Police', 'Transfer'], n_patients, p=[0.6, 0.3, 0.05, 0.05]),
            'primary_diagnosis_ICD10AM_chapter': np.random.choice([
                'Cardiovascular', 'Respiratory', 'Injury', 'Digestive', 'Mental Health',
                'Musculoskeletal', 'Genitourinary', 'Infectious', 'Neurological', 'Other'
            ], n_patients, p=[0.15, 0.12, 0.18, 0.1, 0.08, 0.12, 0.08, 0.07, 0.05, 0.05]),
            'establishment_code': np.random.choice(['Metro_A', 'Metro_B', 'Rural_C', 'Rural_D'], n_patients, p=[0.4, 0.35, 0.15, 0.1]),
            'metropolitan_hospital_flag': np.random.choice([0, 1], n_patients, p=[0.25, 0.75]),
            'mental_health_attendance': np.random.choice([0, 1], n_patients, p=[0.85, 0.15]),
            'affected_by_drugs_and_or_alcohol': np.random.choice([0, 1], n_patients, p=[0.9, 0.1]),
            'self_harm_attendance': np.random.choice([0, 1], n_patients, p=[0.97, 0.03]),
            'potentially_avoidable_general_practitioner_type_attendance': np.random.choice([0, 1], n_patients, p=[0.7, 0.3]),
            'departure_status': np.random.choice(['Discharge', 'Admit', 'Transfer', 'LWBS'], n_patients, p=[0.65, 0.25, 0.05, 0.05])
        }

        # Add derived time features
        df = pd.DataFrame(data)
        df['presentation_datetime'] = pd.to_datetime(df['presentation_datetime'])
        df['presentation_hour'] = df['presentation_datetime'].dt.hour
        df['presentation_day_of_week'] = df['presentation_datetime'].dt.dayofweek
        df['presentation_month'] = df['presentation_datetime'].dt.month

        return df

    def _create_demo_hmdc(self):
        """Create demo HMDC dataset for admitted patients"""
        np.random.seed(42)

        # Take subset of EDDC patients who would be admitted
        if self.eddc_df is not None:
            admitted_patients = self.eddc_df[
                (self.eddc_df['triage_category'] <= 3) |
                (self.eddc_df['departure_status'] == 'Admit')
            ].sample(frac=0.3, random_state=42)  # ~30% admission rate
        else:
            n_admissions = 3000
            admitted_patients = pd.DataFrame({
                'synth_person_ID': [f"P{i+1:06d}" for i in range(n_admissions)]
            })

        n_admissions = len(admitted_patients)

        data = {
            'synth_person_ID': admitted_patients['synth_person_ID'].values,
            'age': admitted_patients['age'].values if 'age' in admitted_patients else np.random.normal(55, 18, n_admissions).clip(0, 100).astype(int),
            'sex': admitted_patients['sex'].values if 'sex' in admitted_patients else np.random.choice(['M', 'F'], n_admissions),
            'admission_datetime': pd.date_range('2023-01-01', periods=n_admissions, freq='2H'),
            'separation_datetime': pd.date_range('2023-01-02', periods=n_admissions, freq='2H'),
            'establishment_code': np.random.choice(['Metro_A', 'Metro_B', 'Rural_C', 'Rural_D'], n_admissions, p=[0.5, 0.3, 0.15, 0.05]),
            'admission_status': np.random.choice(['Emergency', 'Elective', 'Transfer'], n_admissions, p=[0.7, 0.2, 0.1]),
            'care_type': np.random.choice(['Acute', 'Rehabilitation', 'Palliative', 'Mental Health'], n_admissions, p=[0.8, 0.1, 0.05, 0.05]),
            'major_diagnostic_categ_current': np.random.choice([
                'Cardiovascular', 'Respiratory', 'Injury', 'Digestive', 'Mental Health',
                'Musculoskeletal', 'Genitourinary', 'Infectious', 'Neurological', 'Surgical'
            ], n_admissions),
            'metropolitan_hospital_flag': np.random.choice([0, 1], n_admissions, p=[0.2, 0.8]),
            'principal_procedure': np.random.choice(['Surgery', 'Diagnostic', 'Therapeutic', 'None'], n_admissions, p=[0.3, 0.25, 0.25, 0.2])
        }

        df = pd.DataFrame(data)
        df['admission_datetime'] = pd.to_datetime(df['admission_datetime'])
        df['separation_datetime'] = pd.to_datetime(df['separation_datetime'])
        df['length_of_stay'] = (df['separation_datetime'] - df['admission_datetime']).dt.days

        return df

    def create_linked_dataset(self):
        """Link EDDC and HMDC datasets to create admission prediction target"""
        print("🔗 Creating linked dataset for admission prediction...")

        # Convert datetime columns
        self.eddc_df['presentation_datetime'] = pd.to_datetime(self.eddc_df['presentation_datetime'])
        self.hmdc_df['admission_datetime'] = pd.to_datetime(self.hmdc_df['admission_datetime'])

        # Create admission target by linking datasets
        linked_admissions = []

        for _, ed_record in self.eddc_df.iterrows():
            person_id = ed_record['synth_person_ID']
            ed_time = ed_record['presentation_datetime']

            # Look for admission within 24 hours of ED presentation
            matching_admissions = self.hmdc_df[
                (self.hmdc_df['synth_person_ID'] == person_id) &
                (self.hmdc_df['admission_datetime'] >= ed_time) &
                (self.hmdc_df['admission_datetime'] <= ed_time + timedelta(hours=24))
            ]

            # Create target variable
            admitted = 1 if len(matching_admissions) > 0 else 0

            # Add admission details if found
            if admitted:
                admission_record = matching_admissions.iloc[0]
                ed_record['admitted'] = 1
                ed_record['time_to_admission'] = (admission_record['admission_datetime'] - ed_time).total_seconds() / 3600
                ed_record['admission_care_type'] = admission_record['care_type']

                # Calculate length of stay from dates
                if 'separation_datetime' in admission_record and pd.notna(admission_record['separation_datetime']):
                    sep_time = pd.to_datetime(admission_record['separation_datetime'])
                    admit_time = pd.to_datetime(admission_record['admission_datetime'])
                    ed_record['admission_los'] = (sep_time - admit_time).days
                else:
                    ed_record['admission_los'] = 0
            else:
                ed_record['admitted'] = 0
                ed_record['time_to_admission'] = np.nan
                ed_record['admission_care_type'] = 'Not_Admitted'
                ed_record['admission_los'] = 0

            linked_admissions.append(ed_record)

        self.linked_df = pd.DataFrame(linked_admissions)

        admission_rate = self.linked_df['admitted'].mean()
        print(f"✅ Linked dataset created: {len(self.linked_df):,} ED presentations")
        print(f"📊 Admission rate: {admission_rate:.1%}")
        print(f"📊 Admitted patients: {self.linked_df['admitted'].sum():,}")

        return self.linked_df

    def engineer_features(self):
        """Create features for admission prediction model"""
        print("🔧 Engineering features for admission prediction...")

        df = self.linked_df.copy()

        # Frequency features - count previous visits
        df['ed_visits_last_year'] = df.groupby('synth_person_ID').cumcount() + 1
        df['frequent_visitor'] = (df['ed_visits_last_year'] > 3).astype(int)

        # Temporal features
        df['presentation_hour'] = df['presentation_datetime'].dt.hour
        df['is_weekend'] = (df['presentation_datetime'].dt.dayofweek >= 5).astype(int)
        df['is_night_shift'] = ((df['presentation_hour'] >= 22) | (df['presentation_hour'] <= 6)).astype(int)
        df['is_business_hours'] = ((df['presentation_hour'] >= 8) & (df['presentation_hour'] <= 17) & (df['is_weekend'] == 0)).astype(int)

        # Age categories
        df['age_group'] = pd.cut(df['age'], bins=[0, 18, 35, 50, 65, 100], labels=['Child', 'Young_Adult', 'Adult', 'Older_Adult', 'Elderly'])

        # High-risk flags
        df['high_acuity'] = (df['triage_category'] <= 2).astype(int)
        df['arrived_by_ambulance'] = (df['mode_of_arrival'] == 'Ambulance').astype(int)
        df['mental_health_flag'] = df['mental_health_attendance']
        df['substance_abuse_flag'] = df['affected_by_drugs_and_or_alcohol']
        df['self_harm_flag'] = df['self_harm_attendance']

        # Clinical complexity score
        df['complexity_score'] = (
            df['high_acuity'] * 3 +
            df['mental_health_flag'] * 2 +
            df['substance_abuse_flag'] * 1 +
            df['self_harm_flag'] * 3 +
            df['frequent_visitor'] * 1
        )

        # Diagnosis risk categories
        high_risk_diagnoses = ['Cardiovascular', 'Respiratory', 'Mental Health', 'Neurological']
        df['high_risk_diagnosis'] = df['primary_diagnosis_ICD10AM_chapter'].isin(high_risk_diagnoses).astype(int)

        self.linked_df = df
        print(f"✅ Feature engineering complete. Dataset shape: {df.shape}")

        return df

    def prepare_model_data(self):
        """Prepare features and target for machine learning"""
        print("📊 Preparing data for machine learning...")

        # Select features for modeling
        categorical_features = [
            'sex', 'ethnicity', 'mode_of_arrival', 'primary_diagnosis_ICD10AM_chapter',
            'establishment_code', 'age_group'
        ]

        numerical_features = [
            'age', 'triage_category', 'presentation_hour', 'ed_visits_last_year',
            'complexity_score'
        ]

        binary_features = [
            'metropolitan_hospital_flag', 'mental_health_attendance',
            'affected_by_drugs_and_or_alcohol', 'self_harm_attendance',
            'potentially_avoidable_general_practitioner_type_attendance',
            'frequent_visitor', 'is_weekend', 'is_night_shift', 'is_business_hours',
            'high_acuity', 'arrived_by_ambulance', 'high_risk_diagnosis'
        ]

        # Encode categorical variables
        df_model = self.linked_df.copy()

        for col in categorical_features:
            if col in df_model.columns:
                le = LabelEncoder()
                df_model[col + '_encoded'] = le.fit_transform(df_model[col].astype(str))
                self.label_encoders[col] = le

        # Combine all features
        feature_cols = (
            [col + '_encoded' for col in categorical_features if col in df_model.columns] +
            [col for col in numerical_features if col in df_model.columns] +
            [col for col in binary_features if col in df_model.columns]
        )

        self.feature_columns = feature_cols

        # Prepare X and y
        X = df_model[feature_cols].fillna(0)
        y = df_model['admitted']

        print(f"✅ Model data prepared:")
        print(f"   Features: {len(feature_cols)}")
        print(f"   Samples: {len(X):,}")
        print(f"   Positive class rate: {y.mean():.1%}")

        return X, y

    def train_model(self, test_size=0.2):
        """Train admission prediction model"""
        print("🚀 Training admission prediction model...")

        X, y = self.prepare_model_data()

        # Train-test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )

        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Try multiple models
        models = {
            'GradientBoosting': GradientBoostingClassifier(
                n_estimators=200, max_depth=6, learning_rate=0.1, random_state=42
            ),
            'RandomForest': RandomForestClassifier(
                n_estimators=200, max_depth=10, random_state=42
            ),
            'LogisticRegression': LogisticRegression(
                max_iter=1000, random_state=42
            )
        }

        best_model = None
        best_auc = 0

        for name, model in models.items():
            print(f"\n🔄 Training {name}...")

            # Use scaled data for Logistic Regression, original for tree-based
            if name == 'LogisticRegression':
                model.fit(X_train_scaled, y_train)
                y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
            else:
                model.fit(X_train, y_train)
                y_pred_proba = model.predict_proba(X_test)[:, 1]

            auc = roc_auc_score(y_test, y_pred_proba)
            print(f"   AUC: {auc:.3f}")

            if auc > best_auc:
                best_auc = auc
                best_model = model
                self.model = model

        print(f"\n✅ Best model selected with AUC: {best_auc:.3f}")

        # Final evaluation
        self.evaluate_model(X_test, y_test)

        return self.model

    def evaluate_model(self, X_test, y_test):
        """Evaluate model performance"""
        print("\n📊 Model Evaluation:")

        # Make predictions
        if hasattr(self.model, 'predict_proba'):
            if isinstance(self.model, LogisticRegression):
                X_test_eval = self.scaler.transform(X_test)
            else:
                X_test_eval = X_test

            y_pred_proba = self.model.predict_proba(X_test_eval)[:, 1]
            y_pred = (y_pred_proba > 0.5).astype(int)
        else:
            y_pred = self.model.predict(X_test)
            y_pred_proba = y_pred

        # Calculate metrics
        auc = roc_auc_score(y_test, y_pred_proba)

        print(f"AUC Score: {auc:.3f}")
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred))

        # Feature importance
        if hasattr(self.model, 'feature_importances_'):
            importance_df = pd.DataFrame({
                'feature': self.feature_columns,
                'importance': self.model.feature_importances_
            }).sort_values('importance', ascending=False)

            print("\nTop 10 Most Important Features:")
            print(importance_df.head(10))

        return auc

    def save_model(self, filename='wa_health_admission_model.pkl'):
        """Save trained model and preprocessing components"""
        model_package = {
            'model': self.model,
            'feature_columns': self.feature_columns,
            'label_encoders': self.label_encoders,
            'scaler': self.scaler,
            'model_type': type(self.model).__name__
        }

        with open(filename, 'wb') as f:
            pickle.dump(model_package, f)

        print(f"✅ Model saved as '{filename}'")

    def predict_admission_probability(self, patient_data):
        """Predict admission probability for new patient"""
        if self.model is None:
            raise ValueError("Model not trained yet")

        # Convert to DataFrame if needed
        if isinstance(patient_data, dict):
            patient_df = pd.DataFrame([patient_data])
        else:
            patient_df = patient_data.copy()

        # Apply same preprocessing
        for col, le in self.label_encoders.items():
            if col in patient_df.columns:
                patient_df[col + '_encoded'] = le.transform(patient_df[col].astype(str))

        # Select features
        X = patient_df[self.feature_columns].fillna(0)

        # Scale if needed
        if isinstance(self.model, LogisticRegression):
            X = self.scaler.transform(X)

        # Predict
        prob = self.model.predict_proba(X)[:, 1]
        return prob[0] if len(prob) == 1 else prob


def main():
    """Main training pipeline"""
    print("🏥 WA Health Admission Prediction Model Training")
    print("=" * 50)

    # Initialize predictor with real WA Health synthetic data
    predictor = WAHealthAdmissionPredictor(
        eddc_path='data/synthetic_eddc_linked_representative_v20250715_01.csv',
        hmdc_path='data/synthetic_hmdc_linked_representative_v20250704_01.csv'
    )

    # Load datasets
    predictor.load_datasets()

    # Create linked dataset
    predictor.create_linked_dataset()

    # Engineer features
    predictor.engineer_features()

    # Train model
    predictor.train_model()

    # Save model
    predictor.save_model()

    print("\n✅ Training complete!")
    print("🎯 Model ready for live ED simulation integration")

    # Example prediction
    print("\n🔮 Example Prediction:")
    sample_patient = {
        'age': 65,
        'sex': 'M',
        'ethnicity': 'Caucasian',
        'triage_category': 2,
        'mode_of_arrival': 'Ambulance',
        'primary_diagnosis_ICD10AM_chapter': 'Cardiovascular',
        'establishment_code': 'Metro_A',
        'metropolitan_hospital_flag': 1,
        'mental_health_attendance': 0,
        'affected_by_drugs_and_or_alcohol': 0,
        'self_harm_attendance': 0,
        'potentially_avoidable_general_practitioner_type_attendance': 0,
        'presentation_hour': 14,
        'ed_visits_last_year': 1,
        'frequent_visitor': 0,
        'is_weekend': 0,
        'is_night_shift': 0,
        'is_business_hours': 1,
        'high_acuity': 1,
        'arrived_by_ambulance': 1,
        'high_risk_diagnosis': 1,
        'complexity_score': 3,
        'age_group': 'Older_Adult'
    }

    try:
        prob = predictor.predict_admission_probability(sample_patient)
        print(f"Admission probability: {prob:.1%}")
    except Exception as e:
        print(f"Prediction error: {e}")


if __name__ == "__main__":
    main()