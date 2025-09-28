"""
WA Health Enhanced Model - Advanced Healthcare Flow Analysis
Includes timeline analysis and transfer patterns for comprehensive DoH challenge coverage
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

class WAHealthEnhancedPredictor:
    """Enhanced WA Health predictor with timeline and transfer pattern analysis"""

    def __init__(self, eddc_path: str = None, hmdc_path: str = None):
        self.eddc_path = eddc_path
        self.hmdc_path = hmdc_path
        self.eddc_df = None
        self.hmdc_df = None
        self.enhanced_df = None
        self.model = None
        self.feature_columns = []
        self.label_encoders = {}

    def load_datasets(self):
        """Load EDDC and HMDC datasets with all temporal columns"""
        print("🚀 Loading Enhanced WA Health Model - Full Dataset Analysis")
        print("=" * 60)

        # Load with ALL datetime columns for timeline analysis
        eddc_cols = [
            'synth_person_ID', 'establishment_code', 'sex', 'age', 'ethnicity',
            'presentation_datetime', 'clinical_care_commencement_datetime',
            'bed_request_datetime', 'discharge_datetime',
            'triage_category', 'departure_status', 'mode_of_arrival', 'referral_source',
            'primary_diagnosis_ICD10AM_chapter', 'mental_health_attendance',
            'metropolitan_hospital_flag', 'affected_by_drugs_and_or_alcohol', 'self_harm_attendance'
        ]

        hmdc_cols = [
            'synth_person_ID', 'establishment_code', 'sex', 'age',
            'admission_datetime', 'date_of_procedure', 'separation_datetime',
            'admission_status', 'care_type', 'major_diagnostic_categ_current',
            'principal_procedure', 'metropolitan_hospital_flag', 'patient_postcode_region'
        ]

        try:
            print("📊 Loading EDDC data...")
            self.eddc_df = pd.read_csv(self.eddc_path, usecols=eddc_cols)  # Full dataset
            print(f"✅ EDDC loaded: {len(self.eddc_df):,} presentations")

            print("📊 Loading HMDC data...")
            self.hmdc_df = pd.read_csv(self.hmdc_path, usecols=hmdc_cols)  # Full dataset
            print(f"✅ HMDC loaded: {len(self.hmdc_df):,} admissions")

            # Convert all datetime columns
            datetime_cols_eddc = ['presentation_datetime', 'clinical_care_commencement_datetime',
                                 'bed_request_datetime', 'discharge_datetime']
            datetime_cols_hmdc = ['admission_datetime', 'date_of_procedure', 'separation_datetime']

            for col in datetime_cols_eddc:
                if col in self.eddc_df.columns:
                    self.eddc_df[col] = pd.to_datetime(self.eddc_df[col], errors='coerce')

            for col in datetime_cols_hmdc:
                if col in self.hmdc_df.columns:
                    self.hmdc_df[col] = pd.to_datetime(self.hmdc_df[col], errors='coerce')

            print(f"📅 EDDC date range: {self.eddc_df['presentation_datetime'].min()} to {self.eddc_df['presentation_datetime'].max()}")
            print(f"📅 HMDC date range: {self.hmdc_df['admission_datetime'].min()} to {self.hmdc_df['admission_datetime'].max()}")

        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return False

        return True

    def create_enhanced_linkage(self):
        """Create enhanced dataset with timeline and transfer features"""
        print("\n🔗 Creating Enhanced Linkage with Timeline & Transfer Analysis...")

        # Group HMDC by person for efficient lookup
        hmdc_by_person = self.hmdc_df.groupby('synth_person_ID')
        enhanced_records = []

        for idx, ed_record in self.eddc_df.iterrows():
            if idx % 15000 == 0:
                print(f"   Processed {idx:,} records...")

            person_id = ed_record['synth_person_ID']
            ed_time = ed_record['presentation_datetime']

            # Find matching admissions within 24 hours
            if person_id in hmdc_by_person.groups:
                person_admissions = hmdc_by_person.get_group(person_id)
                time_window = (person_admissions['admission_datetime'] >= ed_time) & \
                             (person_admissions['admission_datetime'] <= ed_time + timedelta(hours=24))
                matching_admissions = person_admissions[time_window]
            else:
                matching_admissions = pd.DataFrame()

            # Basic admission flag
            admitted = 1 if len(matching_admissions) > 0 else 0

            # Enhanced features
            enhanced_record = ed_record.to_dict()  # Convert Series to dict
            enhanced_record['admitted'] = admitted

            # === TIMELINE ANALYSIS FEATURES ===
            timeline_features = self._extract_timeline_features(ed_record)
            enhanced_record.update(timeline_features)

            # === TRANSFER PATTERN FEATURES ===
            # NOTE: These features are for analysis only, NOT for prediction
            # Using HMDC data to predict admission creates data leakage
            if admitted and len(matching_admissions) > 0:
                admission_record = matching_admissions.iloc[0]
                # Store for analysis but DON'T use in prediction
                enhanced_record['_analysis_inter_hospital_transfer'] = 1 if ed_record['establishment_code'] != admission_record['establishment_code'] else 0
                enhanced_record['_analysis_care_type'] = admission_record.get('care_type', 'Unknown')
            else:
                enhanced_record['_analysis_inter_hospital_transfer'] = 0
                enhanced_record['_analysis_care_type'] = 'Not_Admitted'

            # PREDICTION-SAFE transfer features (only using ED data)
            enhanced_record['rural_hospital'] = 1 if ed_record['metropolitan_hospital_flag'] == 0 else 0
            enhanced_record['metro_hospital'] = 1 if ed_record['metropolitan_hospital_flag'] == 1 else 0

            enhanced_records.append(enhanced_record)

        self.enhanced_df = pd.DataFrame(enhanced_records)
        admission_rate = self.enhanced_df['admitted'].mean()

        print(f"✅ Enhanced linkage complete!")
        print(f"📊 Total records: {len(self.enhanced_df):,}")
        print(f"📊 Admission rate: {admission_rate:.1%}")
        print(f"📊 Admitted patients: {self.enhanced_df['admitted'].sum():,}")

        return True

    def _extract_timeline_features(self, ed_record):
        """Extract timeline analysis features from ED record"""
        timeline_features = {}

        presentation_time = ed_record['presentation_datetime']
        care_start = ed_record['clinical_care_commencement_datetime']
        bed_request = ed_record['bed_request_datetime']
        discharge_time = ed_record['discharge_datetime']

        # Time to care commencement (minutes)
        if pd.notna(care_start) and pd.notna(presentation_time):
            timeline_features['time_to_care_minutes'] = (care_start - presentation_time).total_seconds() / 60
        else:
            timeline_features['time_to_care_minutes'] = 0

        # Time to bed request (minutes)
        if pd.notna(bed_request) and pd.notna(presentation_time):
            timeline_features['time_to_bed_request_minutes'] = (bed_request - presentation_time).total_seconds() / 60
        else:
            timeline_features['time_to_bed_request_minutes'] = 0

        # Total ED length of stay (hours)
        if pd.notna(discharge_time) and pd.notna(presentation_time):
            timeline_features['ed_length_of_stay_hours'] = (discharge_time - presentation_time).total_seconds() / 3600
        else:
            timeline_features['ed_length_of_stay_hours'] = 0

        # Care escalation speed (minutes from care start to bed request)
        if pd.notna(bed_request) and pd.notna(care_start):
            timeline_features['care_escalation_speed_minutes'] = (bed_request - care_start).total_seconds() / 60
        else:
            timeline_features['care_escalation_speed_minutes'] = 0

        # Timeline flags
        timeline_features['bed_requested'] = 1 if pd.notna(bed_request) else 0
        timeline_features['rapid_escalation'] = 1 if timeline_features['care_escalation_speed_minutes'] > 0 and timeline_features['care_escalation_speed_minutes'] < 30 else 0
        timeline_features['prolonged_ed_stay'] = 1 if timeline_features['ed_length_of_stay_hours'] > 6 else 0

        return timeline_features

    def _extract_transfer_features(self, ed_record, admission_record):
        """Extract transfer pattern features"""
        transfer_features = {}

        ed_hospital = ed_record['establishment_code']
        admission_hospital = admission_record['establishment_code']
        ed_metro = ed_record['metropolitan_hospital_flag']
        admission_metro = admission_record['metropolitan_hospital_flag']

        # Inter-hospital transfer
        transfer_features['inter_hospital_transfer'] = 1 if ed_hospital != admission_hospital else 0
        transfer_features['same_hospital_admission'] = 1 if ed_hospital == admission_hospital else 0

        # Rural to metro transfer
        transfer_features['rural_to_metro_transfer'] = 1 if (ed_metro == 0 and admission_metro == 1) else 0

        # Geographic transfer (using postcode if available)
        if 'patient_postcode_region' in admission_record:
            # Simple geographic transfer indicator
            transfer_features['geographic_transfer'] = 1 if transfer_features['inter_hospital_transfer'] == 1 else 0
        else:
            transfer_features['geographic_transfer'] = 0

        # Care type encoding
        care_type = admission_record.get('care_type', 'Unknown')
        transfer_features['admission_care_type_encoded'] = hash(str(care_type)) % 10  # Simple encoding

        return transfer_features

    def engineer_enhanced_features(self):
        """Engineer all features including timeline and transfer patterns"""
        print("\n🔧 Engineering Enhanced Features...")

        df = self.enhanced_df.copy()

        # === CATEGORICAL ENCODING ===
        categorical_features = ['sex', 'ethnicity', 'primary_diagnosis_ICD10AM_chapter',
                              'mode_of_arrival', 'referral_source', 'establishment_code']

        for col in categorical_features:
            if col in df.columns:
                le = LabelEncoder()
                df[col + '_encoded'] = le.fit_transform(df[col].astype(str).fillna('Unknown'))
                self.label_encoders[col] = le

        # === TEMPORAL FEATURES ===
        df['presentation_hour'] = df['presentation_datetime'].dt.hour
        df['presentation_day_of_week'] = df['presentation_datetime'].dt.dayofweek
        df['is_weekend'] = (df['presentation_day_of_week'] >= 5).astype(int)
        df['is_night_shift'] = ((df['presentation_hour'] >= 22) | (df['presentation_hour'] <= 6)).astype(int)
        df['is_business_hours'] = ((df['presentation_hour'] >= 8) & (df['presentation_hour'] <= 17) & (df['is_weekend'] == 0)).astype(int)

        # === DEMOGRAPHIC FEATURES ===
        df['age_group'] = pd.cut(df['age'], bins=[0, 18, 35, 50, 65, 100], labels=[0, 1, 2, 3, 4])
        df['elderly'] = (df['age'] >= 65).astype(int)
        df['pediatric'] = (df['age'] < 18).astype(int)

        # === CLINICAL RISK FEATURES ===
        df['high_acuity'] = (df['triage_category'] <= 2).astype(int)
        df['critical_patient'] = (df['triage_category'] == 1).astype(int)

        # Clinical complexity score
        df['complexity_score'] = (
            df['high_acuity'] * 3 +
            df['mental_health_attendance'] * 2 +
            df['affected_by_drugs_and_or_alcohol'] * 1 +
            df['self_harm_attendance'] * 3 +
            df['elderly'] * 1
        )

        # === FREQUENCY FEATURES ===
        # Count previous visits by same person
        df['ed_visits_last_year'] = df.groupby('synth_person_ID').cumcount() + 1
        df['frequent_visitor'] = (df['ed_visits_last_year'] > 3).astype(int)

        # === ENHANCED TIMELINE FEATURES ===
        # Convert to categorical bins for better model performance (only if columns exist)
        if 'time_to_care_minutes' in df.columns:
            df['time_to_care_category'] = pd.cut(df['time_to_care_minutes'],
                                                bins=[0, 15, 60, 180, float('inf')],
                                                labels=[0, 1, 2, 3])  # Fast, Normal, Slow, Very Slow
        else:
            df['time_to_care_category'] = 0

        if 'ed_length_of_stay_hours' in df.columns:
            df['ed_stay_category'] = pd.cut(df['ed_length_of_stay_hours'],
                                           bins=[0, 2, 6, 12, float('inf')],
                                           labels=[0, 1, 2, 3])  # Short, Normal, Long, Very Long
        else:
            df['ed_stay_category'] = 0

        self.enhanced_df = df
        print(f"✅ Enhanced feature engineering complete")
        print(f"📊 Dataset shape: {df.shape}")

        return df

    def prepare_enhanced_model_data(self):
        """Prepare features for enhanced model training"""
        print("\n📊 Preparing Enhanced Model Data...")

        # Select all enhanced features
        feature_cols = [
            # Demographics
            'age', 'sex_encoded', 'ethnicity_encoded', 'elderly', 'pediatric', 'age_group',

            # Clinical
            'triage_category', 'high_acuity', 'critical_patient', 'complexity_score',
            'primary_diagnosis_ICD10AM_chapter_encoded',
            'mental_health_attendance', 'affected_by_drugs_and_or_alcohol', 'self_harm_attendance',

            # Arrival & Hospital
            'mode_of_arrival_encoded', 'referral_source_encoded', 'establishment_code_encoded',
            'metropolitan_hospital_flag',

            # Temporal
            'presentation_hour', 'presentation_day_of_week', 'is_weekend', 'is_night_shift', 'is_business_hours',

            # Frequency
            'ed_visits_last_year', 'frequent_visitor',

            # === ENHANCED TIMELINE FEATURES ===
            'time_to_care_minutes', 'time_to_bed_request_minutes', 'ed_length_of_stay_hours',
            'care_escalation_speed_minutes', 'bed_requested', 'rapid_escalation', 'prolonged_ed_stay',
            'time_to_care_category', 'ed_stay_category',

            # === ENHANCED TRANSFER FEATURES (prediction-safe) ===
            'rural_hospital', 'metro_hospital'
        ]

        # Filter to available columns
        available_features = [col for col in feature_cols if col in self.enhanced_df.columns]

        X = self.enhanced_df[available_features].fillna(0)
        y = self.enhanced_df['admitted']

        self.feature_columns = available_features

        print(f"✅ Enhanced model data prepared:")
        print(f"   Features: {len(available_features)}")
        print(f"   Samples: {len(X):,}")
        print(f"   Positive class rate: {y.mean():.1%}")

        return X, y

    def train_enhanced_model(self):
        """Train the enhanced admission prediction model"""
        print("\n🚀 Training Enhanced WA Health Model...")

        X, y = self.prepare_enhanced_model_data()

        if y.sum() == 0:
            print("❌ No positive cases found - cannot train model")
            return None

        # Train-test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        # Train enhanced model with more complexity
        self.model = GradientBoostingClassifier(
            n_estimators=200,  # More trees
            max_depth=8,       # Deeper trees for complex patterns
            learning_rate=0.05, # Slower learning for better performance
            subsample=0.8,     # Subsampling for robustness
            random_state=42
        )

        self.model.fit(X_train, y_train)

        # Evaluate model
        y_pred_proba = self.model.predict_proba(X_test)[:, 1]
        y_pred = (y_pred_proba > 0.5).astype(int)
        auc = roc_auc_score(y_test, y_pred_proba)

        print(f"✅ Enhanced model trained!")
        print(f"📊 AUC Score: {auc:.3f}")
        print(f"📊 Training samples: {len(X_train):,}")
        print(f"📊 Test samples: {len(X_test):,}")

        # Feature importance analysis
        importance_df = pd.DataFrame({
            'feature': self.feature_columns,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)

        print("\n🔝 Top 15 Most Important Features:")
        print(importance_df.head(15))

        # Enhanced feature categories analysis
        print("\n📈 Enhanced Feature Categories:")
        timeline_features = [f for f in self.feature_columns if any(x in f for x in ['time_', 'escalation', 'stay', 'bed_requested', 'rapid', 'prolonged'])]
        transfer_features = [f for f in self.feature_columns if any(x in f for x in ['transfer', 'hospital', 'geographic', 'care_type'])]

        timeline_importance = importance_df[importance_df['feature'].isin(timeline_features)]['importance'].sum()
        transfer_importance = importance_df[importance_df['feature'].isin(transfer_features)]['importance'].sum()

        print(f"Timeline Features Impact: {timeline_importance:.3f}")
        print(f"Transfer Features Impact: {transfer_importance:.3f}")

        return auc

    def save_enhanced_model(self, filename='wa_health_enhanced_model.pkl'):
        """Save the enhanced model and all components"""
        model_package = {
            'model': self.model,
            'feature_columns': self.feature_columns,
            'label_encoders': self.label_encoders,
            'model_type': 'WA_Health_Enhanced_Predictor',
            'enhancement_features': {
                'timeline_analysis': True,
                'transfer_patterns': True,
                'surgical_complications': False  # Not implemented yet
            }
        }

        with open(filename, 'wb') as f:
            pickle.dump(model_package, f)

        print(f"\n✅ Enhanced model saved as '{filename}'")
        return filename

def main():
    """Main training pipeline for enhanced model"""
    print("🏥 WA Health Enhanced Model Training - DoH Challenge Optimized")
    print("=" * 70)

    # Initialize enhanced predictor
    predictor = WAHealthEnhancedPredictor(
        eddc_path='data/synthetic_eddc_linked_representative_v20250715_01.csv',
        hmdc_path='data/synthetic_hmdc_linked_representative_v20250704_01.csv'
    )

    try:
        # Execute enhanced training pipeline
        if not predictor.load_datasets():
            return

        if not predictor.create_enhanced_linkage():
            return

        predictor.engineer_enhanced_features()
        auc = predictor.train_enhanced_model()

        if auc:
            predictor.save_enhanced_model()
            print(f"\n🎯 Enhanced Training Complete!")
            print(f"📊 Final AUC: {auc:.3f}")
            print(f"🚀 Ready for DoH Challenge demonstration!")

    except Exception as e:
        print(f"❌ Enhanced training failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()