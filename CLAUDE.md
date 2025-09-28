# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **live ED (Emergency Department) simulation system** designed for healthcare hackathon demonstrations. The core concept: judges/audience members scan QR codes to become virtual patients, triggering a real-time ED crisis visualization that demonstrates AI-powered healthcare optimization.

The system transforms static ML prediction models into an interactive, real-time experience where participants witness ED overcrowding and then see AI intervention solve the crisis live.

## Architecture

### Core Data Flow
```
QR Code Scan → Mobile Patient Form → WebSocket Server → ML Processing → Live Dashboard
```

The system follows a **real-time event-driven architecture**:

1. **Mobile Interface**: HTML forms served via simple HTTP server, connects to WebSocket for real-time submission
2. **WebSocket Server**: Central hub handling patient check-ins, ML processing, and broadcasting updates
3. **ML Engine**: Processes patients through admission prediction model, calculates ED metrics
4. **Live Dashboard**: Streamlit-based visualization showing real-time ED status, crisis alerts, AI interventions

### Backend Modularity

The backend is designed to be **frontend-agnostic**:

- **Patient Model** (`backend/patient_model.py`): Core data structures and database operations
- **ML Engine** (`backend/ml_engine.py`): Admission predictions, ED metrics, crisis detection
- **WebSocket Server** (`backend/websocket_server.py`): Real-time communication layer
- **API Layer**: WebSocket messages are standardized JSON, allowing any frontend to connect

### Key Components

- **WebSocket Server** (port 8765): Real-time communication hub using synchronous `websocket-client`
- **Mobile Forms** (port 8000): Simple HTTP server serving patient check-in forms
- **Streamlit Dashboard** (port 8501): Primary visualization frontend
- **ML Model**: Gradient boosting classifier for admission prediction with real-time inference
- **SQLite Database**: Patient data persistence (`backend/ed_simulation.db`)

## Essential Commands

### Environment Setup
```bash
source venv/bin/activate
pip install -r requirements_live.txt
```

### Running the Complete System (3 terminals required)

**Terminal 1 - WebSocket Server:**
```bash
source venv/bin/activate
python -c "from backend.websocket_server import run_server; run_server()"
```

**Terminal 2 - Mobile Forms:**
```bash
cd mobile
python -m http.server 8000
```

**Terminal 3 - Dashboard:**
```bash
source venv/bin/activate
streamlit run live_dashboard.py --server.port=8501
```

### Demo Preparation
```bash
# Generate QR codes for demo
cd demo
python qr_generator.py

# Test the complete system
python test_simulation.py
```

### ML Model Operations
```bash
# Train/retrain the model
python model.py

# Test ML engine independently
python -c "from backend.ml_engine import EDSimulationEngine; engine = EDSimulationEngine()"
```

## Critical Technical Details

### WebSocket Message Protocol
The WebSocket server uses standardized JSON messages:

- **Client Registration**: `{'type': 'register', 'client_type': 'dashboard'|'mobile'}`
- **Patient Check-in**: `{'type': 'patient_checkin', 'patient_data': {...}}`
- **Real-time Updates**: `{'type': 'patient_arrival', 'patient': {...}, 'metrics': {...}}`
- **Crisis Detection**: `{'type': 'crisis_alert', 'level': 'warning'|'critical'}`
- **AI Intervention**: `{'type': 'ai_intervention', 'actions_taken': [...]}`

### Session State Management
The Streamlit dashboard uses persistent WebSocket connections stored in `st.session_state` to survive page reruns. The WebSocket manager is initialized once per browser session and handles connection lifecycle.

### ML Integration Points
- **Real-time Predictions**: Each patient gets instant admission probability calculation
- **ED Metrics**: Capacity percentage, wait times, cost impact calculated from live patient data
- **Crisis Scenarios**: Automatic triggers at 90%+ capacity with simulated AI optimization
- **ROI Calculations**: Live financial impact modeling ($2.4M projected annual savings)

### Database Schema
SQLite database stores:
- **Patients**: Demographics, vitals, symptoms, predictions, timestamps
- **Sessions**: Demo session tracking and metrics
- **ED Metrics**: Historical performance data

## Development Patterns

### Adding New Frontend
To connect a different frontend (React, Vue, etc.):
1. Connect to WebSocket server at `ws://https://medicoded-form.fly.dev/`
2. Send registration message with `client_type`
3. Handle incoming message types: `initial_state`, `patient_arrival`, `crisis_alert`, `ai_intervention`
4. Send patient data using standardized `patient_checkin` message format

### ML Model Updates
The system loads `trained_model.pkl` on startup. To update predictions:
1. Retrain model using `model.py`
2. Restart WebSocket server to reload model
3. Model features are defined in `backend/ml_engine.py`

### Crisis Simulation Tuning
Crisis thresholds and AI intervention logic are in `backend/websocket_server.py`:
- **Capacity threshold**: 90% for crisis alerts, 95% for critical
- **AI intervention**: Triggered automatically or manually via WebSocket message
- **Recovery simulation**: Bed optimization, patient fast-tracking, wait time reduction

## Demo Execution Flow

The demo follows a **5-phase narrative structure**:
1. **Calm**: Empty ED dashboard, green status
2. **Patient Flood**: Judges scan QR codes, capacity climbs
3. **Crisis**: 90%+ capacity, wait times explode, alerts fire
4. **AI Intervention**: Automatic optimization, dramatic recovery
5. **Victory**: ROI metrics, $2.4M savings display

Critical timing: Each phase has specific duration targets for maximum impact during 5-minute presentations.