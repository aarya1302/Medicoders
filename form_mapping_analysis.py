#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Map WA Health model features to current mobile form fields
"""

def analyze_form_mapping():
    """Analyze current form vs model requirements"""

    # Model's 23 required features
    model_features = [
        'sex_encoded',
        'ethnicity_encoded',
        'mode_of_arrival_encoded',
        'primary_diagnosis_ICD10AM_chapter_encoded',
        'establishment_code_encoded',
        'age_group_encoded',
        'age',
        'triage_category',
        'presentation_hour',
        'ed_visits_last_year',
        'complexity_score',
        'metropolitan_hospital_flag',
        'mental_health_attendance',
        'affected_by_drugs_and_or_alcohol',
        'self_harm_attendance',
        'potentially_avoidable_general_practitioner_type_attendance',
        'frequent_visitor',
        'is_weekend',
        'is_night_shift',
        'is_business_hours',
        'high_acuity',
        'arrived_by_ambulance',
        'high_risk_diagnosis'
    ]

    # Current mobile form fields
    current_form_fields = [
        'age',  # Age input
        'arrival_method',  # Walk-in, Ambulance, Police/Fire
        'pain_level',  # 0-10 scale
        'chest_pain',  # Checkbox
        'shortness_breath',  # Checkbox
        'abdominal_pain',  # Checkbox
        'head_injury',  # Checkbox
        'altered_mental',  # Checkbox
        'nausea_vomiting',  # Checkbox
        'broken_bone',  # Checkbox
        'other_complaint',  # Checkbox + text
        'heart_rate',  # Optional vital
        'blood_pressure'  # Optional vital
    ]

    print("=== FORM MAPPING ANALYSIS ===\n")

    print("✅ FEATURES ALREADY CAPTURED:")
    mapped_features = []

    # Direct mappings
    if 'age' in current_form_fields:
        print("   • age → Age input field")
        mapped_features.append('age')
        mapped_features.append('age_group_encoded')  # Can derive from age

    if 'arrival_method' in current_form_fields:
        print("   • mode_of_arrival_encoded → Arrival method dropdown")
        mapped_features.append('mode_of_arrival_encoded')
        mapped_features.append('arrived_by_ambulance')  # Can derive from arrival method

    # Temporal features (auto-generated)
    print("   • presentation_hour → Auto (current time)")
    print("   • is_weekend → Auto (current date)")
    print("   • is_night_shift → Auto (current time)")
    print("   • is_business_hours → Auto (current time)")
    mapped_features.extend(['presentation_hour', 'is_weekend', 'is_night_shift', 'is_business_hours'])

    # System features (can be configured)
    print("   • establishment_code_encoded → Hospital setting")
    print("   • metropolitan_hospital_flag → Hospital setting")
    mapped_features.extend(['establishment_code_encoded', 'metropolitan_hospital_flag'])

    print(f"\n❌ MISSING CRITICAL FEATURES ({len(model_features) - len(mapped_features)}):")
    missing_features = [f for f in model_features if f not in mapped_features]

    for feature in missing_features:
        priority = "HIGH" if feature in ['sex_encoded', 'ethnicity_encoded', 'triage_category'] else "MEDIUM"
        print(f"   • {feature:<45} [{priority}]")

    print(f"\n📊 MAPPING SUMMARY:")
    print(f"   Current form fields: {len(current_form_fields)}")
    print(f"   Model features needed: {len(model_features)}")
    print(f"   Features covered: {len(mapped_features)} ({len(mapped_features)/len(model_features)*100:.0f}%)")
    print(f"   Features missing: {len(missing_features)} ({len(missing_features)/len(model_features)*100:.0f}%)")

    return missing_features

def suggest_form_improvements(missing_features):
    """Suggest specific form improvements"""

    print(f"\n=== FORM IMPROVEMENT SUGGESTIONS ===\n")

    suggestions = {
        'sex_encoded': {
            'field': 'Gender/Sex',
            'type': 'Radio buttons',
            'options': ['Male', 'Female'],
            'why': 'Core demographic - high predictive value',
            'priority': 'CRITICAL'
        },
        'ethnicity_encoded': {
            'field': 'Ethnicity',
            'type': 'Dropdown',
            'options': ['Aboriginal/Torres Strait Islander', 'Other'],
            'why': 'Important for healthcare equity and risk assessment',
            'priority': 'HIGH'
        },
        'triage_category': {
            'field': 'Emergency Severity Index (ESI)',
            'type': 'Auto-calculated',
            'options': ['1 (Critical)', '2 (Emergent)', '3 (Urgent)', '4 (Less Urgent)', '5 (Non-urgent)'],
            'why': 'Core triage assessment - can be auto-calculated from symptoms',
            'priority': 'CRITICAL'
        },
        'primary_diagnosis_ICD10AM_chapter_encoded': {
            'field': 'Primary Condition Category',
            'type': 'Auto-mapped from symptoms',
            'options': ['Cardiovascular', 'Respiratory', 'Digestive', 'Injury/Poisoning', 'Other'],
            'why': 'Map symptoms to ICD-10 chapters automatically',
            'priority': 'HIGH'
        },
        'ed_visits_last_year': {
            'field': 'Previous ED Visits',
            'type': 'Number input',
            'options': ['0', '1-2', '3-5', '6+'],
            'why': 'Frequent visitors have higher admission risk',
            'priority': 'MEDIUM'
        },
        'mental_health_attendance': {
            'field': 'Mental Health Related',
            'type': 'Checkbox',
            'options': ['Mental health concern'],
            'why': 'Important for care pathway and resource allocation',
            'priority': 'MEDIUM'
        },
        'affected_by_drugs_and_or_alcohol': {
            'field': 'Substance Involvement',
            'type': 'Checkbox',
            'options': ['Affected by alcohol/drugs'],
            'why': 'Affects care complexity and safety protocols',
            'priority': 'MEDIUM'
        },
        'self_harm_attendance': {
            'field': 'Self-harm Risk',
            'type': 'Checkbox',
            'options': ['Self-harm related'],
            'why': 'Critical for safety protocols and mental health pathway',
            'priority': 'HIGH'
        }
    }

    # Print suggestions by priority
    for priority in ['CRITICAL', 'HIGH', 'MEDIUM']:
        priority_features = [f for f in missing_features if f in suggestions and suggestions[f]['priority'] == priority]
        if priority_features:
            print(f"🔴 {priority} PRIORITY ADDITIONS:")
            for feature in priority_features:
                s = suggestions[feature]
                print(f"   + {s['field']}")
                print(f"     Type: {s['type']}")
                print(f"     Why: {s['why']}")
                if 'options' in s:
                    print(f"     Options: {', '.join(s['options'])}")
                print()

    print("💡 SMART FORM DESIGN RECOMMENDATIONS:")
    print("   1. Add 'Patient Demographics' section with sex/ethnicity")
    print("   2. Add 'Previous ED History' section")
    print("   3. Add 'Mental Health & Safety' section")
    print("   4. Auto-calculate ESI triage level from symptoms + vitals")
    print("   5. Auto-map symptoms to ICD-10 diagnostic categories")
    print("   6. Keep hospital/temporal features as backend auto-fill")

    return suggestions

if __name__ == "__main__":
    missing = analyze_form_mapping()
    suggest_form_improvements(missing)