"""
Real-time WebSocket Server for Live ED Simulation
Handles patient check-ins, ML predictions, and live dashboard updates
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Set
import websockets
from websockets.server import WebSocketServerProtocol
import threading
import time

from patient_model import PatientDatabase, Patient, create_patient_from_form
from ml_engine import EDSimulationEngine

class LiveEDServer:
    """WebSocket server for real-time ED simulation"""
    
    def __init__(self, host="0.0.0.0", port=8765):
        self.host = host
        self.port = port
        self.session_id = str(uuid.uuid4())[:8]  # Short session ID
        
        # Core components
        self.db = PatientDatabase()
        self.ed_engine = EDSimulationEngine()
        
        # Connected clients with deduplication tracking
        self.dashboard_clients: Set[WebSocketServerProtocol] = set()
        self.mobile_clients: Set[WebSocketServerProtocol] = set()
        self.dashboard_connection_ids: Set[str] = set()  # Track unique connection IDs

        # Clear any stale connection IDs from previous sessions
        self.dashboard_connection_ids.clear()
        
        # Session state
        self.patients: List[Patient] = []
        self.simulation_active = True
        
        print(f"🏥 Live ED Server initialized - Session: {self.session_id}")
    
    async def register_client(self, websocket: WebSocketServerProtocol, client_type: str, connection_id: str = None):
        """Register a new client connection with deduplication"""
        if client_type == "dashboard":
            # Check for duplicate dashboard connections
            if connection_id and connection_id in self.dashboard_connection_ids:
                print(f"🚫 BLOCKED duplicate dashboard connection: {connection_id}")
                await websocket.send(json.dumps({
                    'type': 'connection_rejected',
                    'reason': 'duplicate_connection',
                    'connection_id': connection_id
                }))
                await websocket.close()
                return False

            # Accept new dashboard connection
            self.dashboard_clients.add(websocket)
            if connection_id:
                self.dashboard_connection_ids.add(connection_id)
                print(f"📊 Dashboard client connected: {connection_id} ({len(self.dashboard_clients)} total)")
            else:
                print(f"📊 Dashboard client connected (no ID) ({len(self.dashboard_clients)} total)")

        elif client_type == "mobile":
            self.mobile_clients.add(websocket)
            print(f"📱 Mobile client connected ({len(self.mobile_clients)} total)")

        # Send initial state to new client
        await self.send_initial_state(websocket, client_type)
        return True
    
    async def unregister_client(self, websocket: WebSocketServerProtocol):
        """Remove a client connection and clean up connection IDs"""
        # Remove from dashboard clients and clean up connection ID
        if websocket in self.dashboard_clients:
            self.dashboard_clients.discard(websocket)
            # Note: We don't remove connection_id immediately to prevent immediate reconnections
            # Connection IDs will be cleaned up after a delay or server restart
            print(f"❌ Dashboard client disconnected ({len(self.dashboard_clients)} remaining)")

        # Remove from mobile clients
        if websocket in self.mobile_clients:
            self.mobile_clients.discard(websocket)
            print(f"❌ Mobile client disconnected ({len(self.mobile_clients)} remaining)")
    
    async def send_initial_state(self, websocket: WebSocketServerProtocol, client_type: str):
        """Send current ED state to newly connected client"""
        try:
            if client_type == "dashboard":
                # Send full dashboard state
                current_metrics = self.ed_engine.calculate_ed_metrics(self.patients, self.session_id)
                bed_status = self.ed_engine.get_bed_status()
                
                await websocket.send(json.dumps({
                    'type': 'initial_state',
                    'session_id': self.session_id,
                    'patients': [self.patient_to_dict(p) for p in self.patients],
                    'metrics': current_metrics,
                    'bed_status': bed_status,
                    'timestamp': datetime.now().isoformat()
                }))
            
            elif client_type == "mobile":
                # Send session info to mobile
                await websocket.send(json.dumps({
                    'type': 'session_info',
                    'session_id': self.session_id,
                    'ed_status': 'active',
                    'timestamp': datetime.now().isoformat()
                }))
                
        except Exception as e:
            print(f"Error sending initial state: {e}")
    
    async def handle_patient_checkin(self, patient_data: Dict, websocket: WebSocketServerProtocol):
        """Process a new patient check-in from mobile app"""
        try:
            # Create patient from form data
            patient = create_patient_from_form(patient_data, self.session_id)
            
            # Add to database
            self.db.add_patient(patient)
            self.patients.append(patient)
            
            print(f"👤 New patient checked in: {patient.id[:8]} (Age: {patient.age}, ESI: {patient.esi_level})")
            
            # Process through ML engine with ALL patients for correct metrics
            simulation_results = self.ed_engine.process_new_patients(self.patients, self.session_id)
            
            # Calculate more accurate queue position
            available_beds = len([bed for bed, patient_id in self.ed_engine.beds.items() if patient_id is None])
            waiting_patients = [p for p in self.patients if p.current_status == 'waiting']

            # Position in queue (0 if beds available and patient qualifies)
            if available_beds > 0 and (patient.triage_priority in ['P1', 'P2'] or patient.admission_probability > 0.6):
                queue_position = 0
            else:
                queue_position = len(waiting_patients)

            # Send confirmation to mobile client
            await websocket.send(json.dumps({
                'type': 'checkin_success',
                'patient_id': patient.id,
                'position_in_queue': queue_position,
                'estimated_wait': patient.estimated_wait_time,
                'priority': patient.triage_priority,
                'beds_available': available_beds,
                'qualifies_for_immediate_bed': patient.triage_priority in ['P1', 'P2'] or patient.admission_probability > 0.6,
                'timestamp': datetime.now().isoformat()
            }))
            
            # Broadcast update to all dashboard clients
            patient_arrival_msg = {
                'type': 'patient_arrival',
                'patient': self.patient_to_dict(patient),
                'metrics': simulation_results['ed_metrics'],
                'bed_status': simulation_results['bed_assignments'],
                'recommendations': simulation_results.get('recommendations', []),
                'timestamp': datetime.now().isoformat()
            }
            print(f"📤 Broadcasting patient_arrival to {len(self.dashboard_clients)} dashboard clients")
            print(f"   Patient ID: {patient.id[:8]}, Dashboard clients: {[str(c.remote_address) for c in self.dashboard_clients]}")
            await self.broadcast_to_dashboards(patient_arrival_msg)
            
            # Check for crisis scenarios
            if simulation_results['ed_metrics']['capacity_percentage'] > 90:
                await self.broadcast_crisis_alert(simulation_results['ed_metrics'])
            
        except Exception as e:
            print(f"Error processing patient check-in: {e}")
            await websocket.send(json.dumps({
                'type': 'checkin_error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }))
    
    async def broadcast_to_dashboards(self, message: Dict):
        """Broadcast message to all dashboard clients"""
        if self.dashboard_clients:
            message_json = json.dumps(message)
            print(f"🔊 Broadcasting to {len(self.dashboard_clients)} dashboard clients:")
            for i, client in enumerate(self.dashboard_clients):
                print(f"   Client {i+1}: {client.remote_address}")

            results = await asyncio.gather(
                *[client.send(message_json) for client in self.dashboard_clients],
                return_exceptions=True
            )

            # Check for send failures
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    print(f"❌ Failed to send to client {i+1}: {result}")
                else:
                    print(f"✅ Successfully sent to client {i+1}")
        else:
            print("⚠️ No dashboard clients to broadcast to!")
    
    async def broadcast_to_mobile(self, message: Dict):
        """Broadcast message to all mobile clients"""
        if self.mobile_clients:
            message_json = json.dumps(message)
            await asyncio.gather(
                *[client.send(message_json) for client in self.mobile_clients],
                return_exceptions=True
            )
    
    async def broadcast_crisis_alert(self, metrics: Dict):
        """Broadcast crisis alert to all clients"""
        crisis_message = {
            'type': 'crisis_alert',
            'level': 'critical' if metrics['capacity_percentage'] > 95 else 'warning',
            'capacity': metrics['capacity_percentage'],
            'wait_time': metrics['average_wait_time'],
            'message': f"🚨 ED at {metrics['capacity_percentage']:.0f}% capacity!",
            'timestamp': datetime.now().isoformat()
        }
        
        await self.broadcast_to_dashboards(crisis_message)
        await self.broadcast_to_mobile(crisis_message)
    
    async def simulate_ai_intervention(self):
        """Simulate AI intervention during crisis scenarios"""
        current_metrics = self.ed_engine.calculate_ed_metrics(self.patients, self.session_id)
        
        if current_metrics['capacity_percentage'] > 90 and len(self.patients) > 15:
            print("🤖 AI Intervention triggered!")
            
            # Simulate AI optimizations
            await asyncio.sleep(2)  # Dramatic pause
            
            # Fast-track low-risk patients
            low_risk_patients = [p for p in self.patients 
                               if p.admission_probability < 0.3 and p.current_status == 'waiting']
            
            for patient in low_risk_patients[:5]:  # Fast-track first 5
                patient.current_status = 'discharged'
                patient.estimated_wait_time = 0.1
            
            # Optimize bed allocation and treatment areas
            self.ed_engine.intelligent_bed_allocation(self.patients)
            area_optimization_actions = self.ed_engine.intelligent_area_optimization()
            
            # Recalculate metrics
            optimized_metrics = self.ed_engine.calculate_ed_metrics(self.patients, self.session_id)
            
            # Broadcast AI intervention results
            await self.broadcast_to_dashboards({
                'type': 'ai_intervention',
                'before_metrics': current_metrics,
                'after_metrics': optimized_metrics,
                'actions_taken': [
                    f"✅ Fast-tracked {len(low_risk_patients[:5])} low-risk patients",
                    "✅ Optimized bed allocation",
                    "✅ Reduced average wait time",
                    "✅ Improved patient flow"
                ] + area_optimization_actions,
                'savings': {
                    'wait_time_reduction': current_metrics['average_wait_time'] - optimized_metrics['average_wait_time'],
                    'cost_savings': 25000,  # Simulated cost savings
                    'efficiency_gain': '23%'
                },
                'timestamp': datetime.now().isoformat()
            })
            
            # Update mobile clients
            await self.broadcast_to_mobile({
                'type': 'ai_optimization',
                'message': '🤖 AI optimization complete - wait times reduced!',
                'timestamp': datetime.now().isoformat()
            })
    
    def patient_to_dict(self, patient: Patient) -> Dict:
        """Convert Patient object to dictionary for JSON serialization"""
        return {
            'id': patient.id[:8],  # Shortened ID
            'age': patient.age,
            'arrival_method': patient.arrival_method,
            'esi_level': patient.esi_level,
            'priority': patient.triage_priority,
            'admission_probability': round(patient.admission_probability, 3),
            'predicted_admission': patient.predicted_admission,
            'status': patient.current_status,
            'current_area': getattr(patient, 'current_area', 'waiting'),
            'wait_time': patient.estimated_wait_time,
            'bed_assigned': patient.bed_assigned,
            'symptoms': {
                'chest_pain': patient.chest_pain,
                'shortness_breath': patient.shortness_breath,
                'abdominal_pain': patient.abdominal_pain,
                'altered_mental': patient.altered_mental,
                'nausea_vomiting': patient.nausea_vomiting
            },
            'vitals': {
                'heart_rate': patient.heart_rate,
                'blood_pressure': f"{patient.systolic_bp}/{patient.diastolic_bp}",
                'temperature': patient.temperature,
                'oxygen_sat': patient.oxygen_sat
            },
            'cost': patient.resource_cost,
            'timestamp': patient.timestamp.isoformat()
        }
    
    async def handle_message(self, websocket: WebSocketServerProtocol, message: str):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            print(f"🔍 DEBUG: handle_message called with type: {message_type} from {websocket.remote_address}")
            
            if message_type == 'register':
                client_type = data.get('client_type', 'dashboard')
                connection_id = data.get('connection_id')
                success = await self.register_client(websocket, client_type, connection_id)
                if not success:
                    return  # Connection was rejected and closed
            
            elif message_type == 'patient_checkin':
                await self.handle_patient_checkin(data['patient_data'], websocket)
            
            elif message_type == 'request_update':
                # Send current state
                current_metrics = self.ed_engine.calculate_ed_metrics(self.patients, self.session_id)
                await websocket.send(json.dumps({
                    'type': 'state_update',
                    'metrics': current_metrics,
                    'patients': [self.patient_to_dict(p) for p in self.patients[-10:]],  # Last 10 patients
                    'timestamp': datetime.now().isoformat()
                }))
            
            elif message_type == 'trigger_ai':
                # Manual AI intervention trigger
                await self.simulate_ai_intervention()
            
            elif message_type == 'reset_simulation':
                # Reset simulation state
                self.patients = []
                self.ed_engine.beds = {f"Bed_{i+1:02d}": None for i in range(self.ed_engine.bed_count)}
                await self.broadcast_to_dashboards({
                    'type': 'simulation_reset',
                    'timestamp': datetime.now().isoformat()
                })
                
        except json.JSONDecodeError:
            print(f"Invalid JSON received: {message}")
        except Exception as e:
            print(f"Error handling message: {e}")
    
    async def client_handler(self, websocket: WebSocketServerProtocol, path: str):
        """Handle individual client connections"""
        client_id = str(uuid.uuid4())[:8]
        print(f"🔗 New connection: {client_id} ({websocket.remote_address})")
        
        try:
            async for message in websocket:
                await self.handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            print(f"Connection closed: {client_id}")
        except Exception as e:
            print(f"Error with client {client_id}: {e}")
        finally:
            await self.unregister_client(websocket)
    
    async def background_tasks(self):
        """Run background simulation tasks"""
        while self.simulation_active:
            try:
                # Update patient flow and check for AI intervention opportunities
                if len(self.patients) > 0:
                    # Update patient flow through treatment areas
                    print(f"🔄 Background task: Updating flow for {len(self.patients)} patients...")
                    self.ed_engine.update_patient_flow(self.patients)

                    # Debug: Show current patient areas
                    for p in self.patients:
                        current_area = getattr(p, 'current_area', 'unknown')
                        print(f"   Patient {p.id[:8]}: {current_area}")

                    # Recalculate metrics after patient flow update
                    current_metrics = self.ed_engine.calculate_ed_metrics(self.patients, self.session_id)

                    # Broadcast updated state to dashboards
                    await self.broadcast_to_dashboards({
                        'type': 'patient_flow_update',
                        'metrics': current_metrics,
                        'patients': [self.patient_to_dict(p) for p in self.patients[-20:]],
                        'timestamp': datetime.now().isoformat()
                    })

                    # Auto-trigger AI intervention during crisis
                    if (current_metrics['capacity_percentage'] > 92 and
                        len([p for p in self.patients if p.current_status == 'waiting']) > 10):
                        await self.simulate_ai_intervention()
                
                await asyncio.sleep(5)  # Check every 5 seconds for faster demo responsiveness
                
            except Exception as e:
                print(f"Background task error: {e}")
                await asyncio.sleep(5)
    
    async def start_server(self):
        """Start the WebSocket server"""
        print(f"🚀 Starting Live ED Server on {self.host}:{self.port}")
        print(f"📋 Session ID: {self.session_id}")
        
        # Start background tasks
        background_task = asyncio.create_task(self.background_tasks())
        
        # Start WebSocket server
        async with websockets.serve(self.client_handler, self.host, self.port):
            print(f"✅ Server running! Connect to ws://{self.host}:{self.port}")
            await asyncio.Future()  # Run forever

def run_server():
    """Run the server (for standalone execution)"""
    server = LiveEDServer()
    asyncio.run(server.start_server())

if __name__ == "__main__":
    run_server()