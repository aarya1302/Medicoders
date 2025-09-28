#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check how establishment codes map to rural/metro in the WA Health model
"""

import pickle
import pandas as pd

def analyze_establishment_mapping():
    """Analyze establishment code vs metropolitan_hospital_flag relationship"""

    print("🏥 Analyzing establishment code mapping...\n")

    # Load the model
    with open('wa_health_admission_model.pkl', 'rb') as f:
        model_data = pickle.load(f)

    # Get establishment codes from label encoder
    establishment_encoder = model_data['label_encoders']['establishment_code']
    establishment_codes = establishment_encoder.classes_

    print(f"📊 Found {len(establishment_codes)} establishment codes:")
    print("   ", list(establishment_codes[:10]), "... (showing first 10)")

    # Check if we have any mapping data in the model
    print(f"\n🔍 Model components:")
    for key in model_data.keys():
        if key != 'model':  # Don't print the model object
            print(f"   • {key}: {type(model_data[key])}")

    # Check if there's any built-in rural/metro mapping
    print(f"\n🏷️ Features related to location:")
    features = model_data.get('feature_columns', [])
    location_features = [f for f in features if any(word in f.lower() for word in ['metro', 'rural', 'location', 'establishment', 'hospital'])]
    for feature in location_features:
        print(f"   • {feature}")

    # The key insight: model has both establishment_code_encoded AND metropolitan_hospital_flag
    print(f"\n💡 KEY INSIGHT:")
    print(f"   The model has TWO separate features:")
    print(f"   1. establishment_code_encoded (specific hospital ID)")
    print(f"   2. metropolitan_hospital_flag (rural vs metro)")
    print(f"   This means the model learns BOTH hospital identity AND location type!")

    return establishment_codes

def suggest_form_approach():
    """Suggest how to handle establishment code in the form"""

    print(f"\n=== FORM DESIGN RECOMMENDATION ===\n")

    print(f"❌ CURRENT PROBLEM:")
    print(f"   • Model trained on 79 specific hospital codes (8000.0-8078.0)")
    print(f"   • Demo users won't know their specific establishment code")
    print(f"   • Unknown codes will crash the model (LabelEncoder error)")

    print(f"\n✅ SMART SOLUTION:")
    print(f"   Instead of asking for establishment code, ask for hospital type:")

    print(f"\n   📱 Form Field:")
    print(f"   'Hospital Type:'")
    print(f"   ○ Metropolitan Hospital")
    print(f"   ○ Rural Hospital")

    print(f"\n   🔧 Backend Logic:")
    print(f"   1. User selects 'Metropolitan' or 'Rural'")
    print(f"   2. Backend maps to representative establishment codes:")
    print(f"      • Metropolitan → use 8013.0 (from your data sample)")
    print(f"      • Rural → use 8050.0 (assume mid-range = rural)")
    print(f"   3. Set metropolitan_hospital_flag = 1 (metro) or 0 (rural)")

    print(f"\n   📈 Benefits:")
    print(f"   • Users understand the question")
    print(f"   • No unknown establishment code crashes")
    print(f"   • Model still gets both features it needs")
    print(f"   • Realistic demo experience")

    print(f"\n💻 Implementation:")
    print(f"""
   HTML:
   <select id="hospital-type" required>
       <option value="metro">Metropolitan Hospital</option>
       <option value="rural">Rural Hospital</option>
   </select>

   JavaScript:
   const hospitalMap = {{
       'metro': {{ code: '8013.0', metro_flag: 1 }},
       'rural': {{ code: '8050.0', metro_flag: 0 }}
   }};

   Backend:
   establishment_code = hospitalMap[user_selection].code
   metropolitan_hospital_flag = hospitalMap[user_selection].metro_flag
   """)

if __name__ == "__main__":
    codes = analyze_establishment_mapping()
    suggest_form_approach()