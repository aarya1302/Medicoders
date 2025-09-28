"""
Simple Dashboard that actually shows real patient data from the database
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sqlite3
import json
import time

# Configure Streamlit
st.set_page_config(
    page_title="Live ED Simulation - WA Health",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1e40af;
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #1e40af 0%, #3b82f6 100%);
        color: white;
        margin: -1rem -1rem 2rem -1rem;
    }
    .metric-big {
        font-size: 2.5rem;
        font-weight: 800;
        color: #1e40af;
    }
    .status-critical {
        color: #dc2626;
        background: #fef2f2;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #dc2626;
    }
    .status-warning {
        color: #d97706;
        background: #fefbf2;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #d97706;
    }
    .status-normal {
        color: #059669;
        background: #f0fdf4;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #059669;
    }
</style>
""", unsafe_allow_html=True)

def load_patients_from_db():
    """Load patients from the database"""
    try:
        conn = sqlite3.connect('backend/ed_simulation.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM patients ORDER BY timestamp DESC')
        rows = cursor.fetchall()
        
        patients = []
        for row in rows:
            try:
                patient_data = json.loads(row[3])  # data column
                patients.append(patient_data)
            except:
                continue
        
        conn.close()
        return patients
        
    except Exception as e:
        st.error(f"Database error: {e}")
        return []

def calculate_metrics(patients):
    """Calculate ED metrics from patient data"""
    if not patients:
        return {
            'total_patients': 0,
            'capacity_percentage': 0,
            'average_wait_time': 0,
            'high_risk_count': 0,
            'p1_patients': 0,
            'p2_patients': 0,
            'p3_patients': 0
        }
    
    total_patients = len(patients)
    ED_CAPACITY = 25
    capacity_percentage = min(100, (total_patients / ED_CAPACITY) * 100)
    
    # Count by priority
    p1_count = len([p for p in patients if p.get('triage_priority') == 'P1'])
    p2_count = len([p for p in patients if p.get('triage_priority') == 'P2'])
    p3_count = len([p for p in patients if p.get('triage_priority') == 'P3'])
    
    # High risk patients (admission probability > 0.7)
    high_risk_count = len([p for p in patients if p.get('admission_probability', 0) > 0.7])
    
    # Average wait time
    wait_times = [p.get('estimated_wait_time', 0) for p in patients if p.get('current_status') == 'waiting']
    avg_wait = sum(wait_times) / len(wait_times) if wait_times else 0
    
    return {
        'total_patients': total_patients,
        'capacity_percentage': capacity_percentage,
        'average_wait_time': avg_wait,
        'high_risk_count': high_risk_count,
        'p1_patients': p1_count,
        'p2_patients': p2_count,
        'p3_patients': p3_count
    }

def main():
    # Header
    st.markdown('<h1 class="main-header">🏥 ROYAL PERTH ED - LIVE SIMULATION</h1>', unsafe_allow_html=True)
    
    # Auto-refresh every 3 seconds
    placeholder = st.empty()
    
    with placeholder.container():
        # Load real patient data
        patients = load_patients_from_db()
        metrics = calculate_metrics(patients)
        
        # Session info
        st.markdown(f"""
        **Session ID:** LIVE-DEMO | **Status:** 🟢 ACTIVE | **Time:** {datetime.now().strftime('%H:%M:%S')} | **Patients in Database:** {len(patients)}
        """)
        
        # Main metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            capacity_class = "status-critical" if metrics['capacity_percentage'] > 90 else "status-warning" if metrics['capacity_percentage'] > 75 else "status-normal"
            st.markdown(f"""
            <div class="{capacity_class}">
                <div class="metric-big">{metrics['capacity_percentage']:.0f}%</div>
                <div>ED Capacity</div>
                <small>{metrics['total_patients']}/25 beds</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="status-normal">
                <div class="metric-big">{metrics['total_patients']}</div>
                <div>Total Patients</div>
                <small>Real patients checked in</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            wait_class = "status-critical" if metrics['average_wait_time'] > 4 else "status-warning" if metrics['average_wait_time'] > 2 else "status-normal"
            st.markdown(f"""
            <div class="{wait_class}">
                <div class="metric-big">{metrics['average_wait_time']:.1f}h</div>
                <div>Average Wait</div>
                <small>Target: < 4 hours</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="{'status-critical' if metrics['high_risk_count'] > 5 else 'status-warning' if metrics['high_risk_count'] > 2 else 'status-normal'}">
                <div class="metric-big">{metrics['high_risk_count']}</div>
                <div>High Risk Patients</div>
                <small>Need immediate beds</small>
            </div>
            """, unsafe_allow_html=True)
        
        # Priority breakdown
        st.markdown("### 🚨 Patient Priority Breakdown")
        priority_col1, priority_col2, priority_col3 = st.columns(3)
        
        with priority_col1:
            st.metric("P1 - Critical", metrics['p1_patients'], help="Immediate intervention required")
        with priority_col2:
            st.metric("P2 - Moderate", metrics['p2_patients'], help="Urgent care needed")
        with priority_col3:
            st.metric("P3 - Standard", metrics['p3_patients'], help="Standard priority")
        
        # Show actual patients if any exist
        if patients:
            st.markdown("### 👥 Recent Patient Check-ins")
            
            # Show last 10 patients
            recent_patients = patients[:10]
            
            for i, patient in enumerate(recent_patients):
                col1, col2, col3, col4 = st.columns([2, 1, 1, 2])
                
                with col1:
                    st.write(f"**Patient {patient.get('id', 'Unknown')[:8]}**")
                    st.write(f"Age {patient.get('age', '?')}")
                
                with col2:
                    priority = patient.get('triage_priority', 'P3')
                    color = {'P1': '🔴', 'P2': '🟡', 'P3': '🟢'}.get(priority, '⚪')
                    st.write(f"{color} {priority}")
                
                with col3:
                    risk = patient.get('admission_probability', 0) * 100
                    st.write(f"{risk:.0f}% risk")
                
                with col4:
                    symptoms = []
                    if patient.get('chestpain'): symptoms.append("Chest Pain")
                    if patient.get('respdistres'): symptoms.append("SOB")
                    if patient.get('abdomnlpain'): symptoms.append("Abd Pain")
                    st.write(", ".join(symptoms[:2]) if symptoms else "Other")
                
                if i < len(recent_patients) - 1:
                    st.divider()
            
            # Chart of admission probabilities
            if len(patients) > 1:
                st.markdown("### 📊 Admission Risk Distribution")
                
                risks = [p.get('admission_probability', 0) * 100 for p in patients]
                priorities = [p.get('triage_priority', 'P3') for p in patients]
                
                fig = px.histogram(
                    x=risks, 
                    nbins=10,
                    title="Distribution of Admission Risk Scores",
                    labels={'x': 'Admission Risk (%)', 'y': 'Number of Patients'}
                )
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.info("🏥 **Waiting for patients to check in...**")
            st.markdown("""
            **To test the system:**
            1. Go to: http://https://medicoded-form.fly.dev//patient_form.html
            2. Fill out the emergency check-in form
            3. Hit 'CHECK IN TO ED'
            4. Watch this dashboard update in real-time!
            """)
        
        # Crisis alerts
        if metrics['capacity_percentage'] > 90:
            st.error(f"🚨 **CRISIS ALERT**: ED at {metrics['capacity_percentage']:.0f}% capacity!")
        elif metrics['capacity_percentage'] > 75:
            st.warning(f"⚠️ **Warning**: ED approaching capacity at {metrics['capacity_percentage']:.0f}%")
    
    # Auto-refresh
    time.sleep(3)
    st.rerun()

if __name__ == "__main__":
    main()