#!/usr/bin/env python3
"""
Standalone WebSocket client for dashboard - prevents Streamlit connection issues
Runs as a separate process and communicates via file-based IPC
"""

import asyncio
import json
import websockets
import time
import threading
import pickle
import os
from datetime import datetime
from pathlib import Path

class StandaloneWebSocketClient:
    """External WebSocket client that communicates via files"""

    def __init__(self):
        self.ws_url = "wss://medicoded-websocket.fly.dev/"
        self.state_file = "/tmp/ed_dashboard_state.pkl"
        self.command_file = "/tmp/ed_dashboard_command.json"
        self.running = True
        self.websocket = None

        # Initialize state
        self.state = {
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

        # Track processed patients to prevent duplicates
        self.processed_patient_ids = set()

        print("🔌 Standalone WebSocket client initialized")

    def save_state(self):
        """Save current state to file"""
        try:
            with open(self.state_file, 'wb') as f:
                pickle.dump(self.state, f)
        except Exception as e:
            print(f"Error saving state: {e}")

    def check_commands(self):
        """Check for commands from dashboard"""
        try:
            if os.path.exists(self.command_file):
                with open(self.command_file, 'r') as f:
                    command = json.load(f)

                # Delete command file after reading
                os.remove(self.command_file)

                # Process command
                if command.get('action') == 'shutdown':
                    print("🔌 Shutdown command received")
                    self.running = False

        except Exception as e:
            print(f"Error checking commands: {e}")

    async def connect_websocket(self):
        """Connect to WebSocket server"""
        try:
            self.websocket = await websockets.connect(self.ws_url)
            self.state['connection_status'] = 'Connected'
            print("✅ Connected to WebSocket server")

            # Register as dashboard client with unique ID
            import uuid
            unique_id = f"dashboard-{str(uuid.uuid4())[:8]}"
            registration_msg = {
                'type': 'register',
                'client_type': 'dashboard',
                'connection_id': unique_id,
                'singleton': True
            }
            print(f"📤 Sending registration: {registration_msg}")
            await self.websocket.send(json.dumps(registration_msg))
            print(f"✅ Registration sent for client: {unique_id}")

            return True

        except Exception as e:
            print(f"WebSocket connection error: {e}")
            self.state['connection_status'] = 'Disconnected'
            return False

    async def handle_message(self, message):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            print(f"📥 External client received: {message_type}")

            if message_type == 'initial_state':
                # Load initial state
                initial_patients = data.get('patients', [])
                initial_metrics = data.get('metrics', {})

                self.state['patients'] = initial_patients
                self.state['metrics'] = initial_metrics
                self.state['last_update'] = datetime.now()

                # Track initial patient IDs
                self.processed_patient_ids.update([p.get('id') for p in initial_patients])

                print(f"📋 Initial state loaded: {len(initial_patients)} patients")

            elif message_type == 'patient_arrival':
                # New patient arrived
                print(f"🏥 PATIENT ARRIVAL RECEIVED in external client!")
                new_patient = data.get('patient')
                if new_patient:
                    patient_id = new_patient.get('id', 'Unknown')
                    print(f"   Patient ID: {patient_id}")
                    print(f"   Current patients in external client: {len(self.state['patients'])}")

                    # Prevent duplicates
                    if patient_id not in self.processed_patient_ids:
                        self.state['patients'].append(new_patient)
                        self.state['patients'] = self.state['patients'][-50:]  # Keep last 50
                        self.processed_patient_ids.add(patient_id)

                        print(f"✅ Patient added to external client: {patient_id} (Total: {len(self.state['patients'])})")

                        # Save state immediately
                        try:
                            self.save_state()
                            print(f"💾 State saved to file with {len(self.state['patients'])} patients")
                        except Exception as save_error:
                            print(f"❌ ERROR saving state: {save_error}")
                            import traceback
                            traceback.print_exc()
                    else:
                        print(f"🚫 Blocked duplicate patient: {patient_id}")
                else:
                    print("❌ No patient data in patient_arrival message!")

                # Update metrics
                server_metrics = data.get('metrics')
                if server_metrics:
                    self.state['metrics'] = server_metrics
                    print(f"📊 Metrics updated: {server_metrics.get('total_patients', 'unknown')} total patients")

                self.state['last_update'] = datetime.now()

            elif message_type == 'patient_flow_update':
                # Patient flow update - patients moving between areas
                print(f"🔄 Patient flow update received in external client!")
                updated_patients = data.get('patients', [])
                updated_metrics = data.get('metrics', {})

                if updated_patients:
                    self.state['patients'] = updated_patients
                    print(f"   Updated {len(updated_patients)} patient positions")

                if updated_metrics:
                    self.state['metrics'] = updated_metrics
                    print(f"   Updated metrics: {updated_metrics.get('bed_utilization', 'unknown')}% bed utilization")

                self.state['last_update'] = datetime.now()

            elif message_type == 'crisis_alert':
                self.state['crisis_alert'] = data
                print(f"🚨 Crisis alert: {data.get('level')}")

            elif message_type == 'ai_intervention':
                self.state['ai_alert'] = data
                print(f"🤖 AI intervention completed")

            # Save updated state
            self.save_state()

        except Exception as e:
            print(f"Error handling message: {e}")

    async def websocket_loop(self):
        """Main WebSocket message loop"""
        while self.running:
            try:
                if not self.websocket or self.websocket.closed:
                    if not await self.connect_websocket():
                        await asyncio.sleep(5)
                        continue

                # Listen for messages with timeout
                try:
                    message = await asyncio.wait_for(self.websocket.recv(), timeout=1.0)
                    print(f"📨 Message received: {message[:100]}...")
                    await self.handle_message(message)
                except asyncio.TimeoutError:
                    # Timeout is normal - continue to check commands
                    pass
                except websockets.exceptions.ConnectionClosed:
                    print("📊 WebSocket connection closed by server")
                    self.state['connection_status'] = 'Disconnected'
                    self.websocket = None
                except Exception as e:
                    print(f"❌ Error receiving message: {e}")
                    import traceback
                    traceback.print_exc()

            except Exception as e:
                print(f"WebSocket loop error: {e}")
                await asyncio.sleep(5)

    def command_loop(self):
        """Check for commands in separate thread"""
        while self.running:
            self.check_commands()
            time.sleep(1)

    async def run(self):
        """Main run method"""
        print("🚀 Starting standalone WebSocket client")

        # Start command checking thread
        command_thread = threading.Thread(target=self.command_loop, daemon=True)
        command_thread.start()

        # Run WebSocket loop
        await self.websocket_loop()

        print("🔌 Standalone WebSocket client stopped")

def main():
    """Main entry point"""
    client = StandaloneWebSocketClient()
    try:
        asyncio.run(client.run())
    except KeyboardInterrupt:
        print("🛑 Shutting down...")

if __name__ == "__main__":
    main()