import kagglehub
import pandas as pd
import numpy as np
from pathlib import Path
import pyreadr
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
import pickle
import os

def load_dataset():
    """Download and load the hospital triage dataset"""
    # Download latest version
    path = kagglehub.dataset_download("maalona/hospital-triage-and-patient-history-data")
    print(f"Path to dataset files: {path}")
    
    # Load the R data file
    data_file = Path(path) / "5v_cleandf.rdata"
    result = pyreadr.read_r(str(data_file))
    
    # Get the first (and likely only) dataframe from the R file
    df_name = list(result.keys())[0]
    df = result[df_name]
    
    return df

def train_admission_model(df):
    """Train ML model to predict inpatient admissions from triage data"""
    print("\n=== TRAINING ADMISSION PREDICTION MODEL ===")
    
    # Look for admission/outcome columns
    potential_target_cols = [col for col in df.columns if any(keyword in col.lower() 
                            for keyword in ['admit', 'admission', 'discharge', 'outcome', 'disposition'])]
    print(f"Potential target columns: {potential_target_cols}")
    
    if not potential_target_cols:
        print("No clear admission target found. Creating synthetic target for demo.")
        # Create a synthetic admission target based on available features
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            # Use first numeric column to create binary target
            threshold = df[numeric_cols[0]].median()
            df['admit'] = (df[numeric_cols[0]] > threshold).astype(int)
            target_col = 'admit'
        else:
            print("Cannot create model - no suitable features found")
            return None
    else:
        target_col = potential_target_cols[0]
        # Convert target to binary if needed
        if df[target_col].dtype == 'object':
            le = LabelEncoder()
            df[target_col + '_encoded'] = le.fit_transform(df[target_col])
            target_col = target_col + '_encoded'
    
    # Select features for the model
    numeric_features = df.select_dtypes(include=[np.number]).columns.tolist()
    if target_col in numeric_features:
        numeric_features.remove(target_col)
    
    if len(numeric_features) == 0:
        print("No numeric features available for modeling")
        return None
    
    # Prepare data
    X = df[numeric_features].fillna(0)  # Simple imputation
    y = df[target_col]
    
    print(f"Features used: {numeric_features}")
    print(f"Target: {target_col}")
    print(f"Dataset size: {X.shape[0]} samples, {X.shape[1]} features")
    
    # Check if target needs encoding
    if y.dtype == 'category' or y.dtype == 'object':
        print(f"Target values: {y.value_counts()}")
        # Convert to binary for admission prediction
        if target_col == 'disposition':
            # Map disposition values to admission (1) vs discharge (0)
            admission_keywords = ['admit', 'inpatient', 'ward', 'observation', 'obs']
            y_binary = y.astype(str).str.lower().str.contains('|'.join(admission_keywords), na=False).astype(int)
            y = y_binary
            print(f"Mapped to binary admission target")
        else:
            # Use label encoder for other categorical targets
            le = LabelEncoder()
            y = le.fit_transform(y)
    
    print(f"Admission rate: {y.mean():.3f}")
    
    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # Train Gradient Boosting model (similar performance to XGBoost)
    print("\nTraining Gradient Boosting model...")
    model = GradientBoostingClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        random_state=42
    )
    
    model.fit(X_train, y_train)
    
    # Make predictions
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    y_pred = model.predict(X_test)
    
    # Evaluate model
    auc_score = roc_auc_score(y_test, y_pred_proba)
    print(f"\nModel Performance:")
    print(f"AUC Score: {auc_score:.3f}")
    print(f"Target AUC from plan: 0.75-0.85")
    
    if auc_score >= 0.75:
        print("✅ Model meets target performance!")
    else:
        print("⚠️  Model below target - may need more features or data")
    
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    
    # Feature importance
    feature_importance = pd.DataFrame({
        'feature': numeric_features,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print("\nTop 10 Most Important Features:")
    print(feature_importance.head(10))
    
    # Save model results
    results = {
        'model': model,
        'features': numeric_features,
        'target': target_col,
        'auc_score': auc_score,
        'feature_importance': feature_importance
    }
    
    # Save the trained model
    save_model(results)
    
    return results

def save_model(model_results, filename='trained_model.pkl'):
    """Save the trained model to disk"""
    try:
        with open(filename, 'wb') as f:
            pickle.dump(model_results, f)
        print(f"✅ Model saved as '{filename}'")
    except Exception as e:
        print(f"⚠️ Could not save model: {e}")

def load_saved_model(filename='trained_model.pkl'):
    """Load a previously trained model from disk"""
    if os.path.exists(filename):
        try:
            with open(filename, 'rb') as f:
                model_results = pickle.load(f)
            print(f"✅ Model loaded from '{filename}' (AUC: {model_results['auc_score']:.3f})")
            return model_results
        except Exception as e:
            print(f"⚠️ Could not load model: {e}")
            return None
    else:
        print(f"📁 No saved model found at '{filename}'")
        return None

def get_or_train_model():
    """Get model - load from disk if exists, otherwise train new one"""
    # Try to load existing model first
    model_results = load_saved_model()
    
    if model_results is not None:
        return model_results
    
    # No saved model found, train a new one
    print("🔄 No saved model found. Training new model...")
    try:
        df = load_dataset()
        model_results = train_admission_model(df)
        return model_results
    except Exception as e:
        print(f"Error training model: {e}")
        return None

def main():
    """Main function to run the ML model training as per grok-plan.md"""
    try:
        print("🚀 Loading or training admission prediction model...")
        
        # Get model (load existing or train new)
        model_results = get_or_train_model()
        
        if model_results:
            print(f"\n=== MODEL READY ===")
            print(f"✅ Gradient Boosting model available with AUC: {model_results['auc_score']:.3f}")
            print("🎯 Ready for hackathon adaptation with WA Health data!")
        else:
            print("❌ Model loading/training failed")
        
    except Exception as e:
        print(f"Error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()