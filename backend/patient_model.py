"""
Patient Model for Live ED Simulation
Handles patient data structure and database operations
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import random
import uuid

@dataclass
class Patient:
    """Patient data model matching our ML model requirements"""
    id: str
    session_id: str
    timestamp: datetime
    
    # Demographics
    age: int
    
    # Arrival Info
    arrival_method: str  # Walk-in, Ambulance, Police/Fire
    esi_level: int  # 1-5 Emergency Severity Index

    # Vital Signs
    heart_rate: int
    systolic_bp: int
    diastolic_bp: int
    temperature: float
    respiratory_rate: int
    oxygen_sat: int

    # Hospital Info
    establishment_code: str = "8002.0"  # Hospital code for WA Health model
    metropolitan_hospital_flag: int = 1  # 1=Metro, 0=Rural
    
    # Symptoms (Chief Complaint)
    chest_pain: bool = False
    shortness_breath: bool = False
    abdominal_pain: bool = False
    altered_mental: bool = False
    nausea_vomiting: bool = False
    head_injury: bool = False
    broken_bone: bool = False
    other_complaint: str = ""
    
    # Medical History
    cardiovascular: bool = False
    diabetes: bool = False
    hypertension: bool = False
    copd: bool = False
    kidney_disease: bool = False
    prev_admissions: int = 0
    
    # ED Status
    triage_priority: str = "P3"  # P1, P2, P3
    admission_probability: float = 0.0
    predicted_admission: bool = False
    bed_assigned: Optional[str] = None
    estimated_wait_time: float = 0.0  # hours
    current_status: str = "waiting"  # waiting, triaged, in_treatment, discharged, admitted
    
    # Cost/Resource Impact
    resource_cost: float = 0.0
    predicted_los: float = 0.0  # length of stay in hours

class PatientDatabase:
    """SQLite database for patient management"""
    
    def __init__(self, db_path: str = "backend/ed_simulation.db"):
        self.db_path = db_path
        self._conn = None
        
        # Ensure directory exists for file databases
        if self.db_path != ":memory:":
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # For in-memory databases, keep connection persistent
        if self.db_path == ":memory:":
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        conn = self._conn if self._conn else sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS patients (
                    id TEXT PRIMARY KEY,
                    session_id TEXT,
                    timestamp TEXT,
                    data TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ed_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    timestamp TEXT,
                    total_patients INTEGER,
                    capacity_percentage REAL,
                    average_wait_time REAL,
                    cost_impact REAL,
                    satisfaction_score REAL
                )
            ''')
            
            conn.commit()
            print(f"✅ Database initialized: {self.db_path}")
            
        except Exception as e:
            print(f"❌ Database initialization error: {e}")
        finally:
            if not self._conn:  # Only close if not persistent connection
                conn.close()
    
    def add_patient(self, patient: Patient) -> bool:
        """Add a new patient to the database"""
        try:
            conn = self._conn if self._conn else sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO patients (id, session_id, timestamp, data)
                VALUES (?, ?, ?, ?)
            ''', (
                patient.id,
                patient.session_id,
                patient.timestamp.isoformat(),
                json.dumps(asdict(patient), default=str)
            ))
            
            conn.commit()
            if not self._conn:  # Only close if not persistent connection
                conn.close()
            return True
        except Exception as e:
            print(f"Error adding patient: {e}")
            return False
    
    def get_patients_by_session(self, session_id: str) -> List[Patient]:
        """Get all patients for a session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT data FROM patients 
            WHERE session_id = ? 
            ORDER BY timestamp
        ''', (session_id,))
        
        patients = []
        for (data,) in cursor.fetchall():
            patient_dict = json.loads(data)
            patient_dict['timestamp'] = datetime.fromisoformat(patient_dict['timestamp'])
            patients.append(Patient(**patient_dict))
        
        conn.close()
        return patients
    
    def update_patient(self, patient: Patient) -> bool:
        """Update existing patient data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE patients 
                SET data = ?, timestamp = ?
                WHERE id = ?
            ''', (
                json.dumps(asdict(patient), default=str),
                patient.timestamp.isoformat(),
                patient.id
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error updating patient: {e}")
            return False
    
    def get_session_metrics(self, session_id: str) -> Dict:
        """Calculate real-time ED metrics for a session"""
        patients = self.get_patients_by_session(session_id)
        
        if not patients:
            return {
                'total_patients': 0,
                'capacity_percentage': 0,
                'average_wait_time': 0,
                'cost_impact': 0,
                'satisfaction_score': 100,
                'high_risk_count': 0,
                'beds_occupied': 0,
                'predicted_admissions': 0
            }
        
        # Calculate metrics
        total_patients = len(patients)
        waiting_patients = [p for p in patients if p.current_status == 'waiting']
        beds_occupied = len([p for p in patients if p.bed_assigned])
        
        # ED capacity (assume 25 beds total)
        ED_BED_COUNT = 25
        capacity_percentage = min(100, (total_patients / ED_BED_COUNT) * 100)
        
        # Average wait time
        avg_wait = sum(p.estimated_wait_time for p in waiting_patients) / max(len(waiting_patients), 1)
        
        # Cost impact calculation
        total_cost = sum(p.resource_cost for p in patients)
        
        # High risk patients (admission probability > 0.7)
        high_risk_count = len([p for p in patients if p.admission_probability > 0.7])
        
        # Predicted admissions
        predicted_admissions = len([p for p in patients if p.predicted_admission])
        
        # Patient satisfaction (decreases with wait time and capacity)
        satisfaction_base = 100
        satisfaction_penalty = min(50, capacity_percentage * 0.5 + avg_wait * 5)
        satisfaction_score = max(20, satisfaction_base - satisfaction_penalty)
        
        return {
            'total_patients': total_patients,
            'capacity_percentage': capacity_percentage,
            'average_wait_time': avg_wait,
            'cost_impact': total_cost,
            'satisfaction_score': satisfaction_score,
            'high_risk_count': high_risk_count,
            'beds_occupied': beds_occupied,
            'predicted_admissions': predicted_admissions,
            'waiting_patients': len(waiting_patients)
        }

def generate_realistic_repeat_visits(age: int) -> int:
    """Generate realistic repeat visit patterns based on age and clinical factors"""
    import random

    # Age-based repeat visit probabilities
    if age < 25:
        # Young adults - low repeat rate, mostly trauma/accidents
        return random.choices([0, 1, 2], weights=[85, 12, 3])[0]
    elif age < 45:
        # Middle-aged adults - moderate repeat rate
        return random.choices([0, 1, 2, 3], weights=[75, 15, 7, 3])[0]
    elif age < 65:
        # Older adults - higher repeat rate due to chronic conditions
        return random.choices([0, 1, 2, 3, 4, 5], weights=[60, 20, 12, 5, 2, 1])[0]
    else:
        # Elderly - highest repeat rate due to multiple comorbidities
        return random.choices([0, 1, 2, 3, 4, 5, 6, 7, 8], weights=[50, 20, 15, 8, 4, 2, 1, 0.5, 0.5])[0]

def create_patient_from_form(form_data: Dict, session_id: str) -> Patient:
    """Create a Patient object from mobile form data"""
    
    # Generate realistic vital signs based on age and complaints
    age = form_data.get('age', 65)
    pain_level = form_data.get('pain_level', 5)
    
    # Base vitals with some variation
    heart_rate = random.randint(70, 90) + (pain_level * 3) + (max(0, age - 60))
    systolic_bp = random.randint(110, 130) + (age - 40) // 2
    diastolic_bp = random.randint(70, 85) + (age - 40) // 4
    temperature = round(random.uniform(36.8, 37.2), 1)
    respiratory_rate = random.randint(14, 18) + (pain_level // 2)
    oxygen_sat = random.randint(96, 99)
    
    # Adjust vitals based on complaints
    if form_data.get('chest_pain'):
        heart_rate += random.randint(10, 25)
        systolic_bp += random.randint(10, 20)
    if form_data.get('shortness_breath'):
        respiratory_rate += random.randint(5, 10)
        oxygen_sat = random.randint(90, 96)
    
    # ESI Level based on pain level first, then symptoms and arrival method
    esi_level = 3  # Default

    # Pain level is primary factor
    if pain_level >= 9:
        esi_level = 1  # Severe pain = critical
    elif pain_level >= 7:
        esi_level = 2  # High pain = emergent
    elif pain_level >= 4:
        esi_level = 3  # Moderate pain = urgent
    elif pain_level >= 1:
        esi_level = 4  # Mild pain = less urgent
    else:  # pain_level == 0
        esi_level = 5  # No pain = non-urgent (unless other critical symptoms)

    # Adjust for critical symptoms (can override pain-based ESI)
    if form_data.get('chest_pain'):
        esi_level = min(esi_level, random.choice([1, 2, 2]))  # Chest pain can be critical
    elif form_data.get('altered_mental'):
        # Confusion - moderate concern but not usually critical
        esi_level = min(esi_level, random.choice([2, 3, 3]))  # Cap at ESI 2-3

    # Ambulance arrival suggests higher acuity
    if form_data.get('arrival_method') == 'Ambulance':
        esi_level = min(esi_level, random.choice([1, 2, 2, 3]))  # More urgent
    
    patient = Patient(
        id=str(uuid.uuid4()),
        session_id=session_id,
        timestamp=datetime.now(),
        
        # Demographics
        age=age,
        
        # Arrival
        arrival_method=form_data.get('arrival_method', 'Walk-in'),
        esi_level=esi_level,
        establishment_code=form_data.get('establishment_code', '8002.0'),
        metropolitan_hospital_flag=form_data.get('metropolitan_hospital_flag', 1),
        
        # Vitals
        heart_rate=heart_rate,
        systolic_bp=systolic_bp,
        diastolic_bp=diastolic_bp,
        temperature=temperature,
        respiratory_rate=respiratory_rate,
        oxygen_sat=oxygen_sat,
        
        # Symptoms
        chest_pain=form_data.get('chest_pain', False),
        shortness_breath=form_data.get('shortness_breath', False),
        abdominal_pain=form_data.get('abdominal_pain', False),
        altered_mental=form_data.get('altered_mental', False),
        nausea_vomiting=form_data.get('nausea_vomiting', False),
        head_injury=form_data.get('head_injury', False),
        broken_bone=form_data.get('broken_bone', False),
        other_complaint=form_data.get('other_complaint', ''),
        
        # Medical History (randomized for demo)
        cardiovascular=random.choice([True, False]) if age > 50 else False,
        diabetes=random.choice([True, False]) if age > 45 else False,
        hypertension=random.choice([True, False]) if age > 55 else False,
        copd=random.choice([True, False]) if age > 60 else False,
        kidney_disease=random.choice([True, False]) if age > 65 else False,
        prev_admissions=generate_realistic_repeat_visits(age),
    )
    
    return patient

if __name__ == "__main__":
    # Test the patient model
    db = PatientDatabase()
    
    # Create test patient
    test_data = {
        'age': 67,
        'pain_level': 8,
        'chest_pain': True,
        'arrival_method': 'Ambulance'
    }
    
    patient = create_patient_from_form(test_data, "test_session")
    print(f"Created patient: {patient.id}")
    print(f"ESI Level: {patient.esi_level}")
    print(f"Heart Rate: {patient.heart_rate}")
    print(f"Symptoms: Chest Pain = {patient.chest_pain}")