"""
Flask Web App to Test WA Health Admission Prediction Model
Interactive form to input patient data and get admission probability
"""

from flask import Flask, render_template, request, jsonify
import pickle
import pandas as pd
import numpy as np
from datetime import datetime

app = Flask(__name__)

class WAHealthModelTester:
    def __init__(self):
        self.model_data = None
        self.load_model()

    def load_model(self):
        """Load the trained WA Health model"""
        try:
            with open('wa_health_admission_model.pkl', 'rb') as f:
                self.model_data = pickle.load(f)
            print(f"✅ Model loaded: AUC {self.model_data['auc_score']:.3f}")
        except Exception as e:
            print(f"❌ Error loading model: {e}")

    def predict_admission(self, patient_data):
        """Predict admission probability for patient data"""
        if not self.model_data:
            return {"error": "Model not loaded"}

        try:
            # Create DataFrame from input
            df = pd.DataFrame([patient_data])

            # Apply encoders for categorical variables
            for col, encoder in self.model_data['encoders'].items():
                if col in df.columns:
                    try:
                        # Convert to string format that matches training data
                        if col in ['mode_of_arrival']:
                            # These were stored as "1.0", "2.0", etc.
                            df[col + '_encoded'] = encoder.transform([f"{float(df[col].iloc[0]):.1f}"])
                        else:
                            df[col + '_encoded'] = encoder.transform(df[col].astype(str))
                    except ValueError as e:
                        # Handle unseen categories - use most common class
                        print(f"Warning: Unseen category for {col}: {df[col].iloc[0]}. Using default.")
                        df[col + '_encoded'] = 0

            # Handle missing departure_status_encoded - set to default (not admitted)
            if 'departure_status_encoded' in self.model_data['feature_names']:
                df['departure_status_encoded'] = 0  # Default to "not yet decided"

            # Engineer time-based features
            hour = patient_data.get('presentation_hour', 12)
            df['presentation_hour'] = hour
            df['is_weekend'] = 1 if patient_data.get('is_weekend', False) else 0
            df['is_night'] = 1 if (hour >= 22 or hour <= 6) else 0

            # Engineer demographic features
            age = patient_data.get('age', 50)
            df['age'] = age
            df['elderly'] = 1 if age >= 65 else 0
            df['pediatric'] = 1 if age < 18 else 0

            # Engineer clinical features
            triage = patient_data.get('triage_category', 3)
            df['triage_category'] = triage
            df['high_acuity'] = 1 if triage <= 2 else 0

            # Ensure all required features are present
            for feature in self.model_data['feature_names']:
                if feature not in df.columns:
                    df[feature] = 0

            # Select features in correct order
            X = df[self.model_data['feature_names']].fillna(0)

            # Make prediction
            prob = self.model_data['model'].predict_proba(X.values)[0][1]

            # Convert numpy values to Python native types for JSON serialization
            feature_values = [float(val) if hasattr(val, 'dtype') else val for val in X.iloc[0].values]

            return {
                "admission_probability": float(prob),
                "risk_level": self.get_risk_level(prob),
                "features_used": dict(zip(self.model_data['feature_names'], feature_values))
            }

        except Exception as e:
            return {"error": f"Prediction error: {str(e)}"}

    def get_risk_level(self, prob):
        """Convert probability to risk level"""
        if prob >= 0.7:
            return "High Risk"
        elif prob >= 0.3:
            return "Moderate Risk"
        else:
            return "Low Risk"

# Initialize model tester
model_tester = WAHealthModelTester()

@app.route('/')
def index():
    """Main page with input form"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>WA Health Admission Predictor</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .form-group { margin: 15px 0; }
            label { display: block; font-weight: bold; margin-bottom: 5px; }
            input, select { padding: 8px; border: 1px solid #ddd; border-radius: 4px; width: 200px; }
            button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background: #0056b3; }
            .result { margin-top: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 4px; }
            .high-risk { background-color: #f8d7da; border-color: #f5c6cb; }
            .moderate-risk { background-color: #fff3cd; border-color: #ffeaa7; }
            .low-risk { background-color: #d4edda; border-color: #c3e6cb; }
            .feature-table { margin-top: 15px; }
            .feature-table table { width: 100%; border-collapse: collapse; }
            .feature-table th, .feature-table td { padding: 8px; border: 1px solid #ddd; text-align: left; }
            .feature-table th { background-color: #f8f9fa; }
        </style>
    </head>
    <body>
        <h1>🏥 WA Health Admission Prediction Model Tester</h1>
        <p><strong>Model Performance:</strong> AUC = 0.731 | Features: 16 EDDC clinical factors</p>

        <form id="predictionForm">
            <div class="form-group">
                <label>Age:</label>
                <input type="number" id="age" value="45" min="0" max="120">
            </div>

            <div class="form-group">
                <label>Sex:</label>
                <select id="sex">
                    <option value="1">Male</option>
                    <option value="2">Female</option>
                </select>
            </div>

            <div class="form-group">
                <label>Triage Category (1=Critical, 5=Low urgency):</label>
                <select id="triage_category">
                    <option value="1">1 - Immediate</option>
                    <option value="2">2 - Emergency</option>
                    <option value="3" selected>3 - Urgent</option>
                    <option value="4">4 - Semi-urgent</option>
                    <option value="5">5 - Non-urgent</option>
                </select>
            </div>

            <div class="form-group">
                <label>Primary Diagnosis:</label>
                <select id="primary_diagnosis_ICD10AM_chapter">
                    <option value="S0" selected>Injury/Trauma</option>
                    <option value="I0">Cardiovascular</option>
                    <option value="J0">Respiratory</option>
                    <option value="K0">Digestive</option>
                    <option value="F0">Mental Health</option>
                    <option value="M0">Musculoskeletal</option>
                    <option value="N0">Genitourinary</option>
                    <option value="A0">Infectious</option>
                    <option value="G0">Neurological</option>
                    <option value="Z0">Other</option>
                </select>
            </div>

            <div class="form-group">
                <label>Mode of Arrival:</label>
                <select id="mode_of_arrival">
                    <option value="1" selected>Walk-in</option>
                    <option value="3">Ambulance</option>
                    <option value="4">Police/Transfer</option>
                </select>
            </div>

            <!-- REMOVED: Departure Status is data leakage - it contains the answer we're predicting! -->

            <div class="form-group">
                <label>Presentation Hour (0-23):</label>
                <input type="number" id="presentation_hour" value="14" min="0" max="23">
            </div>

            <div class="form-group">
                <label>Hospital Type:</label>
                <select id="metropolitan_hospital_flag">
                    <option value="1" selected>Metropolitan</option>
                    <option value="0">Rural</option>
                </select>
            </div>

            <div class="form-group">
                <label>Mental Health Attendance:</label>
                <select id="mental_health_attendance">
                    <option value="0" selected>No</option>
                    <option value="1">Yes</option>
                </select>
            </div>

            <div class="form-group">
                <label>Affected by Drugs/Alcohol:</label>
                <select id="affected_by_drugs_and_or_alcohol">
                    <option value="0" selected>No</option>
                    <option value="1">Yes</option>
                </select>
            </div>

            <div class="form-group">
                <label>Self Harm Attendance:</label>
                <select id="self_harm_attendance">
                    <option value="0" selected>No</option>
                    <option value="1">Yes</option>
                </select>
            </div>

            <div class="form-group">
                <label>Weekend Presentation:</label>
                <select id="is_weekend">
                    <option value="false" selected>No (Weekday)</option>
                    <option value="true">Yes (Weekend)</option>
                </select>
            </div>

            <button type="submit">🔮 Predict Admission Probability</button>
        </form>

        <div id="result"></div>

        <script>
            document.getElementById('predictionForm').addEventListener('submit', function(e) {
                e.preventDefault();

                const formData = {
                    age: parseInt(document.getElementById('age').value),
                    sex: document.getElementById('sex').value,
                    triage_category: parseFloat(document.getElementById('triage_category').value),
                    primary_diagnosis_ICD10AM_chapter: document.getElementById('primary_diagnosis_ICD10AM_chapter').value,
                    mode_of_arrival: document.getElementById('mode_of_arrival').value,
                    // departure_status removed - it's data leakage!
                    presentation_hour: parseInt(document.getElementById('presentation_hour').value),
                    metropolitan_hospital_flag: parseInt(document.getElementById('metropolitan_hospital_flag').value),
                    mental_health_attendance: parseInt(document.getElementById('mental_health_attendance').value),
                    affected_by_drugs_and_or_alcohol: parseInt(document.getElementById('affected_by_drugs_and_or_alcohol').value),
                    self_harm_attendance: parseInt(document.getElementById('self_harm_attendance').value),
                    is_weekend: document.getElementById('is_weekend').value === 'true'
                };

                fetch('/predict', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(formData)
                })
                .then(response => response.json())
                .then(data => {
                    const resultDiv = document.getElementById('result');

                    if (data.error) {
                        resultDiv.innerHTML = `<div class="result"><h3>❌ Error</h3><p>${data.error}</p></div>`;
                        return;
                    }

                    const prob = (data.admission_probability * 100).toFixed(1);
                    const riskClass = data.risk_level.toLowerCase().replace(' ', '-');

                    let featuresTable = '<div class="feature-table"><h4>Features Used by Model:</h4><table><tr><th>Feature</th><th>Value</th></tr>';
                    for (const [feature, value] of Object.entries(data.features_used)) {
                        featuresTable += `<tr><td>${feature}</td><td>${value}</td></tr>`;
                    }
                    featuresTable += '</table></div>';

                    resultDiv.innerHTML = `
                        <div class="result ${riskClass}">
                            <h3>🎯 Prediction Result</h3>
                            <p><strong>Admission Probability:</strong> ${prob}%</p>
                            <p><strong>Risk Level:</strong> ${data.risk_level}</p>
                            ${featuresTable}
                        </div>
                    `;
                })
                .catch(error => {
                    document.getElementById('result').innerHTML = `<div class="result"><h3>❌ Error</h3><p>${error}</p></div>`;
                });
            });
        </script>
    </body>
    </html>
    '''

@app.route('/predict', methods=['POST'])
def predict():
    """API endpoint for predictions"""
    try:
        patient_data = request.json
        result = model_tester.predict_admission(patient_data)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    print("🚀 Starting WA Health Model Tester...")
    print("📊 Model features:", len(model_tester.model_data['feature_names']) if model_tester.model_data else 0)
    print("🌐 Open http://0.0.0.0:5000 to test the model")
    app.run(debug=True, port=5000)