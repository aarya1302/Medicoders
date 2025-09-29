"""
Live ED Dashboard - Spectacular Real-time Visualization
Main dashboard for judges to watch the ED simulation unfold
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import websocket
import threading
import time
from datetime import datetime, timedelta
import uuid
import queue
import atexit
import pickle
import os

# Configure Streamlit page
st.set_page_config(
    page_title="Live ED Simulation - WA Health",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Session state will be initialized globally below - no per-session initialization needed

# Custom CSS for spectacular visualization
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    /* Hide Streamlit elements */
    .stDeployButton {display: none;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stApp > header {height: 0rem;}
    .stApp > div:first-child {padding-top: 0rem;}
    
    /* Global styling */
    .stApp {
        font-family: 'Inter', sans-serif;
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
        color: white;
    }
    
    /* Main header */
    .main-header {
        background: linear-gradient(90deg, #1e40af 0%, #3b82f6 50%, #06b6d4 100%);
        padding: 20px 40px;
        margin: -1rem -1rem 2rem -1rem;
        text-align: center;
        box-shadow: 0 10px 25px rgba(0,0,0,0.3);
    }
    
    .main-title {
        font-size: 3rem;
        font-weight: 800;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .main-subtitle {
        font-size: 1.2rem;
        margin: 8px 0 0 0;
        opacity: 0.9;
    }
    
    /* Session info */
    .session-bar {
        background: rgba(255,255,255,0.1);
        padding: 12px 40px;
        margin: -1rem -1rem 2rem -1rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        backdrop-filter: blur(10px);
    }
    
    /* Status cards */
    .status-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 20px;
        margin-bottom: 30px;
    }
    
    .status-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.2);
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        transition: all 0.3s ease;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    
    .status-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 40px rgba(0,0,0,0.2);
    }
    
    .status-value {
        font-size: 2.5rem;
        font-weight: 800;
        margin-bottom: 8px;
        background: linear-gradient(135deg, #06b6d4, #3b82f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .status-label {
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        opacity: 0.8;
    }
    
    .status-change {
        font-size: 0.8rem;
        margin-top: 8px;
    }
    
    /* Critical status colors */
    .status-critical { 
        background: linear-gradient(135deg, rgba(239,68,68,0.2) 0%, rgba(220,38,38,0.1) 100%);
        border-color: rgba(239,68,68,0.3);
    }
    
    .status-critical .status-value {
        background: linear-gradient(135deg, #ef4444, #dc2626);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .status-warning { 
        background: linear-gradient(135deg, rgba(245,158,11,0.2) 0%, rgba(217,119,6,0.1) 100%);
        border-color: rgba(245,158,11,0.3);
    }
    
    .status-warning .status-value {
        background: linear-gradient(135deg, #f59e0b, #d97706);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* ED Layout */
    .ed-layout {
        background: rgba(255,255,255,0.05);
        border-radius: 16px;
        padding: 24px;
        margin: 20px 0;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    /* Crisis alert */
    .crisis-alert {
        position: fixed;
        top: 120px;
        left: 50%;
        transform: translateX(-50%);
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        color: white;
        padding: 20px 40px;
        border-radius: 12px;
        box-shadow: 0 10px 30px rgba(239,68,68,0.4);
        z-index: 1000;
        animation: emergencyPulse 2s infinite;
        font-weight: 600;
        font-size: 1.1rem;
    }
    
    @keyframes emergencyPulse {
        0%, 100% { box-shadow: 0 10px 30px rgba(239,68,68,0.4); }
        50% { box-shadow: 0 10px 50px rgba(239,68,68,0.8); }
    }
    
    /* AI intervention alert */
    .ai-alert {
        position: fixed;
        top: 120px;
        left: 50%;
        transform: translateX(-50%);
        background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
        color: white;
        padding: 20px 40px;
        border-radius: 12px;
        box-shadow: 0 10px 30px rgba(6,182,212,0.4);
        z-index: 1000;
        animation: aiGlow 1.5s infinite;
        font-weight: 600;
        font-size: 1.1rem;
    }
    
    @keyframes aiGlow {
        0%, 100% { box-shadow: 0 10px 30px rgba(6,182,212,0.4); }
        50% { box-shadow: 0 15px 40px rgba(6,182,212,0.8); }
    }
    
    /* Metrics styling */
    .metric-big {
        font-size: 3rem;
        font-weight: 800;
        line-height: 1;
    }
    
    .metric-medium {
        font-size: 2rem;
        font-weight: 700;
    }
    
    /* Animation classes */
    .fade-in {
        animation: fadeIn 0.8s ease-out;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .slide-in {
        animation: slideIn 0.6s ease-out;
    }
    
    @keyframes slideIn {
        from { opacity: 0; transform: translateX(-30px); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    /* Chart containers */
    .js-plotly-plot {
        background: rgba(255,255,255,0.05) !important;
        border-radius: 12px !important;
        backdrop-filter: blur(10px) !important;
    }
    
    /* Patient flow indicators */
    .patient-flow {
        display: flex;
        gap: 12px;
        flex-wrap: wrap;
        margin: 20px 0;
    }
    
    .patient-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        animation: patientPulse 2s ease-in-out infinite;
    }
    
    .patient-p1 { background: #ef4444; }
    .patient-p2 { background: #f59e0b; }
    .patient-p3 { background: #10b981; }
    
    @keyframes patientPulse {
        0%, 100% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.2); opacity: 0.7; }
    }
    
    /* ROI Display */
    .roi-highlight {
        background: linear-gradient(135deg, rgba(16,185,129,0.2) 0%, rgba(5,150,105,0.1) 100%);
        border: 2px solid rgba(16,185,129,0.3);
        border-radius: 16px;
        padding: 24px;
        margin: 20px 0;
        text-align: center;
    }
    
    .roi-value {
        font-size: 4rem;
        font-weight: 900;
        background: linear-gradient(135deg, #10b981, #059669);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 8px;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .main-title { font-size: 2rem; }
        .session-bar { flex-direction: column; gap: 12px; }
        .status-grid { grid-template-columns: 1fr 1fr; }
    }
</style>
""", unsafe_allow_html=True)

class ExternalWebSocketManager:
    """WebSocket manager that uses external process - no connection conflicts"""

    def __init__(self):
        self.state_file = "/tmp/ed_dashboard_state.pkl"
        self.command_file = "/tmp/ed_dashboard_command.json"
        self.process = None
        self.message_queue = queue.Queue()

        # Add attributes that the dashboard expects
        self.ws_connected = False
        self.ws_url = "wss://medicoded-websocket.fly.dev/"

        print("🔌 External WebSocket manager initialized")

    def start_connection(self):
        """Start external WebSocket client if not already running"""
        if not self.is_client_running():
            print("🚀 Starting external WebSocket client")
            import subprocess
            import sys

            # Start the external client with proper environment
            self.process = subprocess.Popen([
                sys.executable,
                "websocket_client.py"
            ],
            stdout=None,  # Let output show in terminal
            stderr=None,  # Let errors show in terminal
            cwd=os.getcwd(),
            env=os.environ.copy())  # Copy current environment

            # Wait for connection with timeout
            print("⏳ Waiting for WebSocket connection...")
            max_wait = 60  # seconds
            wait_interval = 0.5
            elapsed = 0

            while elapsed < max_wait:
                time.sleep(wait_interval)
                elapsed += wait_interval
                print("self.is_client_running()", self.is_client_running())
                print("self.check_connection_status()", self.check_connection_status())

                # Check if process is running and connection is established
                if self.is_client_running() and self.check_connection_status():
                    print("✅ External WebSocket client connected")
                   
                    self.ws_connected = True
                    break
                elif elapsed >= 2:  # Start checking connection status after 2 seconds
                    print(f"⏳ Still connecting... ({elapsed:.1f}s)")
            else:
                print("❌ WebSocket client failed to connect within timeout")
                self.ws_connected = False
        else:
            print("♻️ External WebSocket client already running")
            self.ws_connected = True

    def is_client_running(self):
        """Check if external WebSocket client is running"""
        try:
            import subprocess
            result = subprocess.run(['pgrep', '-f', 'websocket_client.py'],
                                  capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False

    def check_connection_status(self):
        """Check if WebSocket client is actually connected"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'rb') as f:
                    state = pickle.load(f)
                    return state.get('connection_status') == 'Connected'
        except Exception:
            pass
        return False

    def get_state(self):
        """Get current state from external client"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'rb') as f:
                    return pickle.load(f)
        except Exception as e:
            print(f"Error reading state: {e}")

        # Return empty state if file doesn't exist or error
        return {
            'patients': [],
            'metrics': {
                'total_patients': 0,
                'capacity_percentage': 0,
                'average_wait_time': 0,
                'high_risk_count': 0,
                'beds_occupied': 0,
                'predicted_admissions': 0,
                'p1_patients': 0,
                'p2_patients': 0,
                'p3_patients': 0,
                'satisfaction_score': 100,
                'cost_impact': 0,
                'bed_utilization': 0
            },
            'crisis_alert': None,
            'ai_alert': None,
            'last_update': datetime.now(),
            'connection_status': 'Disconnected'
        }

    def send_command(self, command):
        """Send command to external client"""
        try:
            with open(self.command_file, 'w') as f:
                json.dump(command, f)
        except Exception as e:
            print(f"Error sending command: {e}")

    def shutdown(self):
        """Shutdown external WebSocket client"""
        print("🔌 Shutting down external WebSocket client")
        self.send_command({'action': 'shutdown'})

        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except:
                try:
                    self.process.kill()
                except:
                    pass

# Initialize external WebSocket manager
if not hasattr(st, '_external_ws_manager'):
    st._external_ws_manager = ExternalWebSocketManager()
    st._external_ws_manager.start_connection()

    # Note: Removed atexit cleanup handler as it was causing premature shutdowns
    # during Streamlit reruns. The external client will be cleaned up when the
    # terminal session ends or can be killed manually with pkill.

# Store reference in session state
st.session_state.websocket_manager = st._external_ws_manager
# print("🔗 Using external WebSocket manager")

# Also make dashboard state global to prevent session conflicts
if not hasattr(st, '_dashboard_state_global'):
    st._dashboard_state_global = {
        'patients': [],
        'metrics': {
            'total_patients': 0,
            'capacity_percentage': 0,
            'average_wait_time': 0,
            'high_risk_count': 0,
            'beds_occupied': 0,
            'predicted_admissions': 0,
            'p1_patients': 0,
            'p2_patients': 0,
            'p3_patients': 0,
            'satisfaction_score': 100,
            'cost_impact': 0,
            'bed_utilization': 0
        },
        'crisis_alert': None,
        'ai_alert': None,
        'last_update': datetime.now(),
        'connection_status': 'Disconnected'
    }

# Use global state instead of per-session state
st.session_state.dashboard_state = st._dashboard_state_global

class LiveDashboard:
    def __init__(self):
        self.session_id = self.get_session_id()
        # Use the globally initialized WebSocket manager
        self.ws_manager = st.session_state.websocket_manager
    
    def get_session_id(self):
        """Get or create session ID"""
        if 'session_id' not in st.session_state:
            st.session_state.session_id = f"DEMO-{uuid.uuid4().hex[:8].upper()}"
        return st.session_state.session_id
    
    def get_empty_metrics(self):
        """Return empty metrics structure"""
        return {
            'total_patients': 0,
            'capacity_percentage': 0,
            'average_wait_time': 0,
            'high_risk_count': 0,
            'beds_occupied': 0,
            'predicted_admissions': 0,
            'p1_patients': 0,
            'p2_patients': 0,
            'p3_patients': 0,
            'satisfaction_score': 100,
            'cost_impact': 0,
            'bed_utilization': 0
        }

    def read_external_state(self):
        """Read state from external WebSocket client file"""
        try:
            external_state = self.ws_manager.get_state()
            if external_state:
                # Update global state with data from external client
                external_patients = external_state.get('patients', [])
                external_metrics = external_state.get('metrics', {})

                if external_patients:
                    # Only log when patient count changes
                    current_count = len(st._dashboard_state_global.get('patients', []))
                    new_count = len(external_patients)

                    if new_count != current_count:
                        print(f"📄 File update: {current_count} → {new_count} patients")

                    st._dashboard_state_global['patients'] = external_patients
                    st._dashboard_state_global['metrics'] = external_metrics
                    st._dashboard_state_global['last_update'] = datetime.now()

                    # Also update session state
                    st.session_state.dashboard_state['patients'] = external_patients
                    st.session_state.dashboard_state['metrics'] = external_metrics
        except Exception as e:
            print(f"❌ Error reading external state: {e}")

    def process_queued_messages(self):
        """Process queued WebSocket messages in main thread"""

        # First, read the latest state from external client file
        self.read_external_state()

        # Then process any queued messages (legacy)
        while not self.ws_manager.message_queue.empty():
            try:
                data = self.ws_manager.message_queue.get_nowait()
                message_type = data.get('type')

                if message_type == 'initial_state':
                    # Update GLOBAL state with initial server state
                    initial_patients = data.get('patients', [])
                    initial_metrics = data.get('metrics', self.get_empty_metrics())

                    st._dashboard_state_global['patients'] = initial_patients
                    st._dashboard_state_global['metrics'] = initial_metrics
                    st._dashboard_state_global['last_update'] = datetime.now()

                    # Initialize global patient tracking
                    if not hasattr(st, '_recent_patient_ids_global'):
                        st._recent_patient_ids_global = set()
                    st._recent_patient_ids_global.update([p.get('id') for p in initial_patients])

                    # Debug: Show initial state loaded into global
                    patient_count = len(initial_patients)
                    total_from_metrics = initial_metrics.get('total_patients', 0)
                    print(f"📋 Initial state loaded into GLOBAL: {patient_count} patients, {total_from_metrics} total")

                elif message_type == 'patient_arrival':
                    # New patient arrived
                    new_patient = data.get('patient')
                    print(f"📥 PATIENT ARRIVAL MESSAGE: {new_patient.get('id', 'Unknown') if new_patient else 'None'}")
                    if new_patient:
                        patient_id = new_patient.get('id', 'Unknown')

                        # Use GLOBAL state for patient tracking - no session conflicts
                        global_patients = st._dashboard_state_global['patients']
                        existing_ids = [p.get('id') for p in global_patients]

                        # Initialize global recent tracking if needed
                        if not hasattr(st, '_recent_patient_ids_global'):
                            st._recent_patient_ids_global = set()

                        # Strict duplicate prevention
                        if patient_id not in existing_ids and patient_id not in st._recent_patient_ids_global:
                            # Add to GLOBAL patient list (only if new)
                            print(f"🔍 ADDING PATIENT TO GLOBAL: {patient_id} - Total will be {len(st._dashboard_state_global['patients']) + 1}")
                            st._dashboard_state_global['patients'].append(new_patient)
                            st._dashboard_state_global['patients'] = st._dashboard_state_global['patients'][-50:]  # Keep last 50

                            # Track in global recent additions
                            st._recent_patient_ids_global.add(patient_id)
                            if len(st._recent_patient_ids_global) > 100:  # Prevent memory bloat
                                st._recent_patient_ids_global = set(list(st._recent_patient_ids_global)[-50:])

                            # Log successful addition
                            total_patients = len(st._dashboard_state_global['patients'])
                            print(f"✅ Patient added to GLOBAL state: {patient_id} (GLOBAL total: {total_patients})")
                        else:
                            print(f"🚫 BLOCKED duplicate patient: {patient_id} (already in global state)")

                        # Always update GLOBAL metrics from server data
                        server_metrics = data.get('metrics')
                        if server_metrics:
                            st._dashboard_state_global['metrics'] = server_metrics
                            # Debug: Compare server vs dashboard counts
                            server_total = server_metrics.get('total_patients', 0)
                            capacity = server_metrics.get('capacity_percentage', 0)
                            dashboard_count = len(st._dashboard_state_global['patients'])
                            print(f"📊 Server: {server_total} patients | Dashboard: {dashboard_count} patients | {capacity:.1f}% capacity")
                        else:
                            # Fallback: calculate basic metrics from GLOBAL patient data
                            global_patients = st._dashboard_state_global['patients']
                            total_patients = len(global_patients)
                            high_risk = len([p for p in global_patients if p.get('admission_probability', 0) > 0.7])
                            p1_patients = len([p for p in global_patients if p.get('priority') == 'P1'])
                            p2_patients = len([p for p in global_patients if p.get('priority') == 'P2'])
                            p3_patients = len([p for p in global_patients if p.get('priority') == 'P3'])

                            st._dashboard_state_global['metrics'].update({
                                'total_patients': total_patients,
                                'high_risk_count': high_risk,
                                'p1_patients': p1_patients,
                                'p2_patients': p2_patients,
                                'p3_patients': p3_patients,
                                'capacity_percentage': min(100, total_patients * 4),  # Rough capacity calc
                                'average_wait_time': total_patients * 0.3,  # Rough wait time calc
                            })

                        st.session_state.dashboard_state['last_update'] = datetime.now()

                elif message_type == 'patient_flow_update':
                    # Patient flow update - patients moving between treatment areas
                    updated_metrics = data.get('metrics', {})
                    updated_patients = data.get('patients', [])

                    # Update both session and global state with latest patient positions
                    st.session_state.dashboard_state['metrics'] = updated_metrics
                    st.session_state.dashboard_state['patients'] = updated_patients
                    st.session_state.dashboard_state['last_update'] = datetime.now()

                    # Also update global state
                    st._dashboard_state_global['metrics'] = updated_metrics
                    st._dashboard_state_global['patients'] = updated_patients
                    st._dashboard_state_global['last_update'] = datetime.now()

                    print(f"🔄 Patient flow update: {len(updated_patients)} patients")

                elif message_type == 'crisis_alert':
                    # Crisis alert
                    st.session_state.dashboard_state['crisis_alert'] = {
                        'level': data.get('level', 'warning'),
                        'message': data.get('message', 'ED at capacity!'),
                        'capacity': data.get('capacity', 0),
                        'timestamp': datetime.now()
                    }
                    print(f"🚨 Crisis alert: {data.get('message')}")

                elif message_type == 'ai_intervention':
                    # AI intervention
                    st.session_state.dashboard_state['ai_alert'] = {
                        'before_metrics': data.get('before_metrics', {}),
                        'after_metrics': data.get('after_metrics', {}),
                        'actions': data.get('actions_taken', []),
                        'savings': data.get('savings', {}),
                        'timestamp': datetime.now()
                    }
                    # Update metrics with post-AI metrics
                    st.session_state.dashboard_state['metrics'] = data.get('after_metrics', st.session_state.dashboard_state['metrics'])
                    print("🤖 AI intervention processed")

                elif message_type == 'state_update':
                    # General state update
                    st.session_state.dashboard_state['metrics'] = data.get('metrics', st.session_state.dashboard_state['metrics'])
                    new_patients = data.get('patients', [])
                    if new_patients:
                        st.session_state.dashboard_state['patients'] = new_patients
                    st.session_state.dashboard_state['last_update'] = datetime.now()

            except queue.Empty:
                break
            except Exception as e:
                print(f"Error processing queued message: {e}")

    def render_header(self):
        """Render the main dashboard header"""
        st.markdown(f"""
        <div class="main-header">
            <h1 class="main-title">🏥 ROYAL PERTH ED - LIVE SIMULATION</h1>
            <p class="main-subtitle">Real-time Emergency Department Crisis Management</p>
        </div>
        
        <div class="session-bar">
            <div>
                <strong>Session ID:</strong> {self.session_id} |
                <strong>WebSocket:</strong> <span style="color: {'#10b981' if st.session_state.get('dashboard_state', {}).get('connection_status') == 'Connected' else '#ef4444'};">● {st.session_state.get('dashboard_state', {}).get('connection_status', 'Disconnected')}</span> |
                <strong>Time:</strong> {datetime.now().strftime('%H:%M:%S')}
            </div>
            <div>
                <strong>Demo Mode:</strong> WA Health Hackathon 2025
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def render_status_cards(self, metrics):
        """Render real-time status cards"""
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        with col1:
            status_class = "status-critical" if metrics['capacity_percentage'] > 90 else "status-warning" if metrics['capacity_percentage'] > 75 else ""
            st.markdown(f"""
            <div class="status-card {status_class}">
                <div class="status-value">{metrics['capacity_percentage']:.0f}%</div>
                <div class="status-label">ED Capacity</div>
                <div class="status-change">{'🚨 Critical' if metrics['capacity_percentage'] > 90 else '⚠️ High' if metrics['capacity_percentage'] > 75 else '✅ Normal'}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="status-card">
                <div class="status-value">{metrics['total_patients']}</div>
                <div class="status-label">Total Patients</div>
                <div class="status-change">+{metrics.get('new_patients', 0)} this minute</div>
            </div>
            """, unsafe_allow_html=True)
            # Debug: Show mismatch occasionally to avoid spam
            dashboard_count = len(st.session_state.dashboard_state.get('patients', []))
            server_count = metrics.get('total_patients', 0)
            if server_count != dashboard_count:
                if not hasattr(st.session_state, 'mismatch_count'):
                    st.session_state.mismatch_count = 0
                st.session_state.mismatch_count += 1
                if st.session_state.mismatch_count % 10 == 1:  # Print every 10th mismatch
                    print(f"⚠️  MISMATCH #{st.session_state.mismatch_count}: Displaying {server_count} patients but have {dashboard_count} in dashboard list")
        
        with col3:
            wait_class = "status-critical" if metrics['average_wait_time'] > 4 else "status-warning" if metrics['average_wait_time'] > 2 else ""
            st.markdown(f"""
            <div class="status-card {wait_class}">
                <div class="status-value">{metrics['average_wait_time']:.1f}h</div>
                <div class="status-label">Avg Wait Time</div>
                <div class="status-change">Target: < 4 hours</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="status-card {'status-critical' if metrics['high_risk_count'] > 5 else ''}">
                <div class="status-value">{metrics['high_risk_count']}</div>
                <div class="status-label">High Risk</div>
                <div class="status-change">Need beds now</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col5:
            st.markdown(f"""
            <div class="status-card">
                <div class="status-value">{metrics['bed_utilization']:.0f}%</div>
                <div class="status-label">Bed Utilization</div>
                <div class="status-change">{metrics['beds_occupied']}/17 treatment beds</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col6:
            satisfaction_class = "status-critical" if metrics['satisfaction_score'] < 50 else "status-warning" if metrics['satisfaction_score'] < 75 else ""
            st.markdown(f"""
            <div class="status-card {satisfaction_class}">
                <div class="status-value">{metrics['satisfaction_score']:.0f}%</div>
                <div class="status-label">Patient Satisfaction</div>
                <div class="status-change">{'😡 Poor' if metrics['satisfaction_score'] < 50 else '😐 Fair' if metrics['satisfaction_score'] < 75 else '😊 Good'}</div>
            </div>
            """, unsafe_allow_html=True)
    
    def render_patient_flow_chart(self, patients):
        """Render real-time patient flow visualization"""
        if not patients:
            # Show empty ED
            fig = go.Figure()
            fig.add_annotation(
                text="🏥 Waiting for patients to arrive...<br>Scan QR codes to start!",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False,
                font=dict(size=20, color="white"),
            )
            fig.update_layout(
                title="Emergency Department - Patient Flow",
                template="plotly_dark",
                height=400,
                showlegend=False,
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig, use_container_width=True)
            return
        
        # Create timeline of arrivals
        timestamps = [datetime.fromisoformat(p.get('timestamp', datetime.now().isoformat())) for p in patients]
        priorities = [p.get('priority', 'P3') for p in patients]
        admission_probs = [p.get('admission_probability', 0) * 100 for p in patients]
        
        # Color mapping
        color_map = {'P1': '#ef4444', 'P2': '#f59e0b', 'P3': '#10b981'}
        colors = [color_map.get(p, '#64748b') for p in priorities]
        
        fig = make_subplots(
            rows=2, cols=1,
            row_heights=[0.7, 0.3],
            subplot_titles=("Patient Arrivals & Risk Assessment", "ED Capacity Over Time"),
            vertical_spacing=0.1
        )
        
        # Patient scatter plot
        fig.add_trace(
            go.Scatter(
                x=timestamps,
                y=admission_probs,
                mode='markers+lines',
                marker=dict(
                    color=colors,
                    size=[15 if p == 'P1' else 12 if p == 'P2' else 8 for p in priorities],
                    opacity=0.8,
                    line=dict(width=2, color='white')
                ),
                line=dict(color='rgba(255,255,255,0.3)', width=1),
                name='Patient Risk',
                hovertemplate="<b>Patient %{pointNumber}</b><br>" +
                            "Admission Risk: %{y:.1f}%<br>" +
                            "Priority: " + '<br>'.join([str(p) for p in priorities]) + "<br>" +
                            "Time: %{x}<br>" +
                            "<extra></extra>"
            ),
            row=1, col=1
        )
        
        # Capacity timeline
        capacity_timeline = []
        for i in range(len(patients)):
            capacity_timeline.append((i + 1) / 17 * 100)  # 17 treatment beds (fast_track + acute + critical + observation)
        
        fig.add_trace(
            go.Scatter(
                x=timestamps,
                y=capacity_timeline,
                mode='lines+markers',
                fill='tozeroy',
                fillcolor='rgba(59,130,246,0.3)',
                line=dict(color='#3b82f6', width=3),
                marker=dict(size=6),
                name='ED Capacity',
            ),
            row=2, col=1
        )
        
        # Add capacity warning lines
        fig.add_hline(y=75, line_dash="dash", line_color="orange", 
                     annotation_text="Warning (75%)", row=2, col=1)
        fig.add_hline(y=90, line_dash="dash", line_color="red", 
                     annotation_text="Critical (90%)", row=2, col=1)
        
        fig.update_layout(
            template="plotly_dark",
            height=600,
            showlegend=True,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        fig.update_xaxes(title_text="Time", row=2, col=1)
        fig.update_yaxes(title_text="Admission Risk (%)", row=1, col=1)
        fig.update_yaxes(title_text="Capacity (%)", range=[0, 100], row=2, col=1)
        
        st.plotly_chart(fig, use_container_width=True)
    
    def render_ed_layout(self, patients):
        """Render 3D-style ED layout with patient positions"""
        st.markdown('<div class="ed-layout">', unsafe_allow_html=True)
        st.markdown("### 🏥 Emergency Department Layout")
        
        # Create ED floor plan
        fig = go.Figure()
        
        # ED rooms/areas
        rooms = [
            {"name": "Triage", "x": [0, 2], "y": [8, 10], "color": "#3b82f6"},
            {"name": "Waiting Room", "x": [0, 4], "y": [5, 7], "color": "#64748b"},
            {"name": "Treatment Area A", "x": [5, 8], "y": [7, 10], "color": "#10b981"},
            {"name": "Treatment Area B", "x": [5, 8], "y": [4, 6], "color": "#10b981"},
            {"name": "Critical Care", "x": [9, 12], "y": [7, 10], "color": "#ef4444"},
            {"name": "Observation", "x": [9, 12], "y": [4, 6], "color": "#f59e0b"},
            {"name": "Discharge", "x": [0, 2], "y": [0, 2], "color": "#059669"},
        ]
        
        for room in rooms:
            fig.add_shape(
                type="rect",
                x0=room["x"][0], y0=room["y"][0],
                x1=room["x"][1], y1=room["y"][1],
                fillcolor=room["color"],
                opacity=0.3,
                layer="below",
                line=dict(color=room["color"], width=2)
            )
            
            fig.add_annotation(
                x=(room["x"][0] + room["x"][1]) / 2,
                y=(room["y"][0] + room["y"][1]) / 2,
                text=room["name"],
                showarrow=False,
                font=dict(color="white", size=10),
            )
        
        # Add patients as dots
        if patients:
            for i, patient in enumerate(patients[-20:]):  # Show last 20 patients
                priority = patient.get('priority', 'P3')
                status = patient.get('status', 'waiting')
                
                # Position based on actual treatment area (matches bed utilization calculation)
                current_area = patient.get('current_area', 'waiting')

                if current_area == 'triage':
                    x, y = 1 + (i % 2) * 0.5, 9 + (i // 2) * 0.2
                elif current_area == 'waiting':
                    x, y = 2 + (i % 4) * 0.3, 6 + (i // 4) * 0.2
                elif current_area == 'fast_track':
                    x, y = 6 + (i % 3) * 0.5, 8 + (i // 3) * 0.3
                elif current_area == 'acute_care':
                    x, y = 6 + (i % 3) * 0.5, 5 + (i // 3) * 0.3
                elif current_area == 'critical_care':
                    x, y = 10 + (i % 2) * 0.5, 8.5 + (i // 2) * 0.2
                elif current_area == 'observation':
                    x, y = 10 + (i % 3) * 0.5, 5 + (i // 3) * 0.3
                elif current_area == 'discharge':
                    x, y = 1 + (i % 2) * 0.5, 1 + (i // 2) * 0.2
                else:
                    # Fallback to waiting area
                    x, y = 2 + (i % 4) * 0.3, 6 + (i // 4) * 0.2
                
                color = {'P1': '#ef4444', 'P2': '#f59e0b', 'P3': '#10b981'}.get(priority, '#64748b')
                
                fig.add_trace(go.Scatter(
                    x=[x], y=[y],
                    mode='markers',
                    marker=dict(color=color, size=12, opacity=0.8),
                    name=f"Patient {i+1} ({priority})",
                    showlegend=False,
                    hovertemplate=f"<b>Patient {patient.get('id', i)}</b><br>" +
                                f"Priority: {priority}<br>" +
                                f"Status: {status}<br>" +
                                f"Risk: {patient.get('admission_probability', 0)*100:.1f}%<br>" +
                                "<extra></extra>"
                ))
        
        fig.update_layout(
            template="plotly_dark",
            height=400,
            showlegend=False,
            xaxis=dict(range=[-1, 13], showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(range=[-1, 11], showgrid=False, zeroline=False, showticklabels=False),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    def render_patient_analytics(self, patients):
        """Render patient demographics and repeat visitor analytics"""
        st.markdown("### 📊 Patient Analytics")

        if not patients:
            st.info("📈 Patient analytics will appear here as patients check in")
            return

        # Calculate repeat visitor statistics
        total_patients = len(patients)
        repeat_visitors = len([p for p in patients if getattr(p, 'prev_admissions', 0) > 0])
        repeat_percentage = (repeat_visitors / total_patients * 100) if total_patients > 0 else 0

        # Calculate metro vs rural
        metro_patients = len([p for p in patients if getattr(p, 'metropolitan_hospital_flag', 1) == 1])
        rural_patients = total_patients - metro_patients

        # Create two columns for the charts
        col1, col2 = st.columns(2)

        with col1:
            # Repeat Visitors Pie Chart
            repeat_labels = ['First-time', 'Repeat Visitors']
            repeat_values = [total_patients - repeat_visitors, repeat_visitors]
            repeat_colors = ['#10b981', '#f59e0b']

            fig_repeat = go.Figure(data=[go.Pie(
                labels=repeat_labels,
                values=repeat_values,
                hole=0.4,
                marker_colors=repeat_colors,
                textinfo='label+percent',
                textfont_size=12,
                hovertemplate="<b>%{label}</b><br>" +
                            "Count: %{value}<br>" +
                            "Percentage: %{percent}<br>" +
                            "<extra></extra>"
            )])

            fig_repeat.update_layout(
                title={
                    'text': f"🔄 Repeat Visitors<br><span style='font-size:14px'>({repeat_percentage:.0f}% repeat rate)</span>",
                    'x': 0.5,
                    'font': {'size': 16}
                },
                template="plotly_dark",
                height=300,
                margin=dict(l=10, r=10, t=60, b=10),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                showlegend=True,
                legend=dict(
                    orientation="v",
                    yanchor="middle",
                    y=0.5,
                    xanchor="left",
                    x=1.05
                )
            )

            st.plotly_chart(fig_repeat, use_container_width=True)

        with col2:
            # Metro vs Rural Pie Chart
            location_labels = ['Metropolitan', 'Rural']
            location_values = [metro_patients, rural_patients]
            location_colors = ['#3b82f6', '#ef4444']

            fig_location = go.Figure(data=[go.Pie(
                labels=location_labels,
                values=location_values,
                hole=0.4,
                marker_colors=location_colors,
                textinfo='label+percent',
                textfont_size=12,
                hovertemplate="<b>%{label}</b><br>" +
                            "Count: %{value}<br>" +
                            "Percentage: %{percent}<br>" +
                            "<extra></extra>"
            )])

            fig_location.update_layout(
                title={
                    'text': f"🏙️ Hospital Location<br><span style='font-size:14px'>({metro_patients}M / {rural_patients}R)</span>",
                    'x': 0.5,
                    'font': {'size': 16}
                },
                template="plotly_dark",
                height=300,
                margin=dict(l=10, r=10, t=60, b=10),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                showlegend=True,
                legend=dict(
                    orientation="v",
                    yanchor="middle",
                    y=0.5,
                    xanchor="left",
                    x=1.05
                )
            )

            st.plotly_chart(fig_location, use_container_width=True)

        # Summary statistics
        if repeat_visitors > 0:
            avg_prev_admissions = sum(getattr(p, 'prev_admissions', 0) for p in patients if getattr(p, 'prev_admissions', 0) > 0) / repeat_visitors
            frequent_visitors = len([p for p in patients if getattr(p, 'prev_admissions', 0) >= 3])
        else:
            avg_prev_admissions = 0
            frequent_visitors = 0

        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%);
            border-radius: 12px;
            padding: 16px;
            margin: 10px 0;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        ">
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; text-align: center;">
                <div>
                    <div style="font-size: 1.5rem; font-weight: 600; color: #f59e0b;">{repeat_percentage:.0f}%</div>
                    <div style="font-size: 0.8rem; opacity: 0.8;">Repeat Rate</div>
                </div>
                <div>
                    <div style="font-size: 1.5rem; font-weight: 600; color: #3b82f6;">{frequent_visitors}</div>
                    <div style="font-size: 0.8rem; opacity: 0.8;">Frequent Visitors (3+)</div>
                </div>
                <div>
                    <div style="font-size: 1.5rem; font-weight: 600; color: #10b981;">{avg_prev_admissions:.1f}</div>
                    <div style="font-size: 0.8rem; opacity: 0.8;">Avg Previous Visits</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    def render_roi_display(self, metrics):
        """Render dramatic ROI calculations"""
        # Calculate real-time savings
        patients_processed = metrics.get('total_patients', 0)
        efficiency_gain = min(30, patients_processed * 0.5)  # Up to 30% efficiency gain
        cost_per_patient_saved = 1200  # Average cost savings per patient
        total_savings = patients_processed * cost_per_patient_saved * (efficiency_gain / 100)
        
        annual_projection = total_savings * 365 if patients_processed > 0 else 2400000
        roi_percentage = (annual_projection / 150000) * 100 if annual_projection > 150000 else 1500
        
        st.markdown(f"""
        <div class="roi-highlight">
            <h3 style="margin-bottom: 20px;">💰 LIVE ROI CALCULATION</h3>
            <div class="roi-value">${total_savings:,.0f}</div>
            <p style="font-size: 1.2rem; margin-bottom: 16px;">Cost Savings This Session</p>
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; margin-top: 20px;">
                <div>
                    <div style="font-size: 1.8rem; font-weight: 700; color: #10b981;">${annual_projection:,.0f}</div>
                    <div style="font-size: 0.9rem; opacity: 0.8;">Annual Projection</div>
                </div>
                <div>
                    <div style="font-size: 1.8rem; font-weight: 700; color: #3b82f6;">{roi_percentage:,.0f}%</div>
                    <div style="font-size: 0.9rem; opacity: 0.8;">ROI</div>
                </div>
                <div>
                    <div style="font-size: 1.8rem; font-weight: 700; color: #f59e0b;">{efficiency_gain:.1f}%</div>
                    <div style="font-size: 0.9rem; opacity: 0.8;">Efficiency Gain</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def render_crisis_alerts(self):
        """Render crisis and AI intervention alerts"""
        metrics = st.session_state.dashboard_state['metrics']
        
        # Crisis alert
        if metrics.get('capacity_percentage', 0) > 90:
            st.markdown(f"""
            <div class="crisis-alert">
                🚨 CRITICAL: ED at {metrics['capacity_percentage']:.0f}% capacity! 
                Average wait time: {metrics.get('average_wait_time', 0):.1f} hours
            </div>
            """, unsafe_allow_html=True)
        
        # AI intervention alert
        if st.session_state.dashboard_state.get('ai_alert'):
            st.markdown(f"""
            <div class="ai-alert">
                🤖 AI INTERVENTION: {st.session_state.dashboard_state['ai_alert']}
            </div>
            """, unsafe_allow_html=True)
    
    def render_live_feed(self, patients):
        """Render live patient feed"""
        st.markdown("### 📡 Live Patient Feed")
        
        if not patients:
            st.info("🏥 Waiting for patients to check in via QR codes...")
            return
        
        # Show last 10 patients
        recent_patients = patients[-10:] if len(patients) > 10 else patients

        # Debug: Check for duplicates in the rendering list
        patient_ids = [p.get('id') for p in recent_patients]
        unique_ids = list(set(patient_ids))
        if len(patient_ids) != len(unique_ids):
            print(f"🔁 DUPLICATE PATIENTS IN FEED: {len(patient_ids)} total, {len(unique_ids)} unique")
            print(f"   IDs: {patient_ids}")

        for patient in reversed(recent_patients):
            priority = patient.get('priority', 'P3')
            risk = patient.get('admission_probability', 0) * 100
            age = patient.get('age', '?')
            
            priority_color = {'P1': '#ef4444', 'P2': '#f59e0b', 'P3': '#10b981'}.get(priority, '#64748b')
            
            st.markdown(f"""
            <div style="
                background: linear-gradient(90deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%);
                border-left: 4px solid {priority_color};
                padding: 12px 16px;
                margin: 8px 0;
                border-radius: 8px;
                backdrop-filter: blur(10px);
                display: flex;
                justify-content: space-between;
                align-items: center;
            ">
                <div>
                    <strong>Patient {patient.get('id', 'Unknown')[:8]}</strong> 
                    <span style="opacity: 0.8;">• Age {age} • {priority}</span>
                </div>
                <div style="text-align: right;">
                    <div style="font-weight: 600; color: {priority_color};">{risk:.0f}% Risk</div>
                    <div style="font-size: 0.8rem; opacity: 0.7;">{patient.get('status', 'waiting')}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    def simulate_data_for_demo(self):
        """Simulate some demo data if no real patients"""
        if len(st.session_state.dashboard_state['patients']) == 0:
            # Add some demo patients for visualization
            demo_patients = []
            for i in range(5):
                demo_patients.append({
                    'id': f'DEMO-{i:03d}',
                    'age': 45 + i * 5,
                    'priority': ['P1', 'P2', 'P2', 'P3', 'P3'][i],
                    'admission_probability': [0.9, 0.7, 0.6, 0.3, 0.2][i],
                    'status': ['waiting', 'in_treatment', 'waiting', 'waiting', 'waiting'][i],
                    'timestamp': (datetime.now() - timedelta(minutes=i*5)).isoformat()
                })
            
            st.session_state.dashboard_state['patients'] = demo_patients
            st.session_state.dashboard_state['metrics'] = {
                'total_patients': 5,
                'capacity_percentage': 20,
                'average_wait_time': 1.5,
                'high_risk_count': 2,
                'beds_occupied': 5,
                'predicted_admissions': 3,
                'p1_patients': 1,
                'p2_patients': 2,
                'p3_patients': 2,
                'satisfaction_score': 85,
                'cost_impact': 15000,
                'bed_utilization': 20
            }
    
    def run(self):
        """Main dashboard rendering loop"""
        # Process any queued WebSocket messages in main thread
        self.process_queued_messages()

        # Update connection status based on WebSocket state
        if self.ws_manager.ws_connected:
            st.session_state.dashboard_state['connection_status'] = 'Connected'
        else:
            st.session_state.dashboard_state['connection_status'] = 'Disconnected'

        self.render_header()
        self.render_crisis_alerts()

        # Get current state
        metrics = st.session_state.dashboard_state['metrics']
        patients = st.session_state.dashboard_state['patients']

        # Track patient count changes to avoid spam
        global_patients = len(st._dashboard_state_global.get('patients', []))
        session_patients = len(patients)

        # Initialize previous count tracking
        if not hasattr(st.session_state, 'last_patient_count'):
            st.session_state.last_patient_count = 0

        # Only debug when patient count changes
        if global_patients != st.session_state.last_patient_count:
            print(f"👤 NEW PATIENT: Total now {global_patients} patients")

            # Show newest patient data (not first)
            if global_patients > 0:
                newest_patient = st._dashboard_state_global['patients'][-1]  # Last patient added
                print(f"   📋 Latest Patient: ID {newest_patient.get('id', 'Unknown')[:8]}")
                print(f"      Age: {newest_patient.get('age', '?')}, ESI: {newest_patient.get('esi_level', '?')}")
                print(f"      Priority: {newest_patient.get('priority', '?')}, Risk: {newest_patient.get('admission_probability', 0)*100:.0f}%")
                print(f"      Status: {newest_patient.get('status', '?')}, Wait: {newest_patient.get('wait_time', 0)}h")

            # Update tracking
            st.session_state.last_patient_count = global_patients

        # Only show demo data if NOT connected - otherwise show real data (even if empty)
        if not self.ws_manager.ws_connected:
            if global_patients != st.session_state.last_patient_count:
                print("🎭 Using DEMO data: Not connected to WebSocket")
            self.simulate_data_for_demo()
            metrics = st.session_state.dashboard_state['metrics']
            patients = st.session_state.dashboard_state['patients']
        elif len(patients) == 0 and global_patients > 0:
            if global_patients != st.session_state.last_patient_count:
                print(f"🔄 Syncing {global_patients} patients from global state...")
            st.session_state.dashboard_state['patients'] = st._dashboard_state_global['patients']
            patients = st.session_state.dashboard_state['patients']
        elif len(patients) == 0:
            # Only print once when first connecting
            if not hasattr(st.session_state, 'empty_logged'):
                print("📊 Connected but no patients yet - showing empty metrics")
                st.session_state.empty_logged = True
        else:
            # Patients available - clear empty flag
            if hasattr(st.session_state, 'empty_logged'):
                delattr(st.session_state, 'empty_logged')
        
        # Main dashboard layout
        self.render_status_cards(metrics)
        
        # Two-column layout
        col1, col2 = st.columns([2, 1])
        
        with col1:
            self.render_patient_flow_chart(patients)
            self.render_ed_layout(patients)
        
        with col2:
            self.render_live_feed(patients)
            self.render_patient_analytics(patients)
            self.render_roi_display(metrics)
        
        # Auto-refresh
        time.sleep(2)
        st.rerun()

# Main execution
if __name__ == "__main__":
    dashboard = LiveDashboard()
    dashboard.run()