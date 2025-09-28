#!/usr/bin/env python3
"""
WA Health Hackathon - Live ED Simulation Startup Script
Uses virtual environment for proper package management
"""

import os

# Activate virtual environment
venv_activate = os.path.join(os.path.dirname(__file__), 'venv', 'bin', 'activate_this.py')
if os.path.exists(venv_activate):
    exec(open(venv_activate).read(), {'__file__': venv_activate})
elif os.path.exists('venv/bin/python'):
    # Alternative method
    import sys
    venv_python = os.path.join(os.path.dirname(__file__), 'venv', 'bin', 'python')
    if os.path.exists(venv_python):
        sys.executable = venv_python
"""
WA Health Hackathon - Live ED Simulation Startup Script
Starts all components for the spectacular demo
"""

import subprocess
import sys
import os
import time
import threading
import webbrowser
from pathlib import Path

def print_banner():
    """Print startup banner"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║  🏥 WA HEALTH HACKATHON 2025 - LIVE ED SIMULATION           ║
║                                                              ║
║     Real-time Emergency Department Crisis Management         ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)
    print("🚀 Starting Live ED Simulation System...")
    print("=" * 60)

def check_requirements():
    """Check if all requirements are installed"""
    print("📦 Checking requirements...")
    
    required_packages = [
        'streamlit', 'websockets', 'plotly', 'pandas', 
        'numpy', 'scikit-learn', 'qrcode', 'PIL'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'PIL':
                import PIL
            else:
                __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"  ❌ {package} - MISSING")
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("📝 Installing missing packages...")
        
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', 
                '-r', 'requirements_live.txt'
            ])
            print("✅ All packages installed successfully!")
        except subprocess.CalledProcessError:
            print("❌ Failed to install packages. Please run manually:")
            print("   pip install -r requirements_live.txt")
            return False
    
    return True

def fix_imports():
    """Fix import paths for the simulation"""
    print("🔧 Setting up import paths...")
    
    # Add current directory to Python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    # Fix backend imports
    backend_init = os.path.join(current_dir, 'backend', '__init__.py')
    if not os.path.exists(backend_init):
        Path(backend_init).touch()
    
    print("  ✅ Import paths configured")

def start_websocket_server():
    """Start the WebSocket server in a separate thread"""
    print("🔌 Starting WebSocket server...")
    
    def run_server():
        try:
            # Import and run the server
            sys.path.append('backend')
            from backend.websocket_server import run_server
            run_server()
        except Exception as e:
            print(f"❌ WebSocket server error: {e}")
            print("💡 Make sure no other service is using port 8765")
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Give server time to start
    time.sleep(3)
    print("  ✅ WebSocket server started on ws://https://medicoded-form.fly.dev/")
    
    return server_thread

def start_mobile_server():
    """Start simple HTTP server for mobile forms"""
    print("📱 Starting mobile form server...")
    
    def run_mobile_server():
        try:
            # Simple HTTP server for mobile files
            import http.server
            import socketserver
            
            # Get absolute path to mobile directory
            mobile_dir = os.path.join(os.path.dirname(__file__), 'mobile')
            if os.path.exists(mobile_dir):
                os.chdir(mobile_dir)
            else:
                print(f"  ❌ Mobile directory not found: {mobile_dir}")
                return
            
            PORT = 8000
            
            Handler = http.server.SimpleHTTPRequestHandler
            with socketserver.TCPServer(("", PORT), Handler) as httpd:
                print(f"  📱 Mobile server running on http://0.0.0.0:{PORT}")
                httpd.serve_forever()
                
        except Exception as e:
            print(f"❌ Mobile server error: {e}")
    
    mobile_thread = threading.Thread(target=run_mobile_server, daemon=True)
    mobile_thread.start()
    
    time.sleep(2)
    print("  ✅ Mobile form server started on http://https://medicoded-form.fly.dev/")
    
    return mobile_thread

def generate_qr_codes():
    """Generate QR codes for demo"""
    print("📋 Generating QR codes for demo...")
    
    try:
        from demo.qr_generator import QRCodeGenerator
        
        generator = QRCodeGenerator(base_url="http://https://medicoded-form.fly.dev//patient_form.html")
        
        # Create presentation QR
        generator.create_presentation_qr()
        
        # Create table cards (fewer for quick demo)
        generator.create_table_cards(tables=5, cards_per_table=4)
        
        print("  ✅ QR codes generated in demo/qr_codes/")
        
    except Exception as e:
        print(f"  ⚠️  QR code generation failed: {e}")
        print("     You can still run the demo without QR codes")

def start_dashboard():
    """Start the main dashboard"""
    print("📊 Starting live dashboard...")
    
    try:
        # Get absolute path to dashboard
        dashboard_path = os.path.join(os.path.dirname(__file__), 'live_dashboard.py')
        
        # Start Streamlit dashboard
        subprocess.Popen([
            sys.executable, '-m', 'streamlit', 'run', 
            dashboard_path,
            '--server.port=8501',
            '--server.address=0.0.0.0',
            '--browser.gatherUsageStats=false'
        ])
        
        time.sleep(5)
        print("  ✅ Dashboard started on http://https://medicoded-dashboard.fly.dev/")
        
        # Open browser
        webbrowser.open('http://https://medicoded-dashboard.fly.dev/')
        
    except Exception as e:
        print(f"❌ Dashboard startup failed: {e}")
        return False
    
    return True

def print_demo_instructions():
    """Print demo instructions"""
    instructions = """
🎯 DEMO READY! Here's what's running:

┌─ SERVICES ─────────────────────────────────────────────┐
│ 📊 Main Dashboard:    http://https://medicoded-dashboard.fly.dev/            │
│ 📱 Mobile Forms:      http://https://medicoded-form.fly.dev/            │
│ 🔌 WebSocket Server:  ws://https://medicoded-form.fly.dev/              │
└────────────────────────────────────────────────────────┘

🎬 PRESENTATION FLOW:

1. 📺 SETUP (Before demo):
   • Open main dashboard on presentation screen
   • Print QR codes from demo/qr_codes/ folder
   • Test mobile form on your phone

2. 🎤 PRESENTATION (5 minutes):
   • Show calm ED dashboard
   • Distribute QR codes to judges
   • "You've all had medical emergencies - scan now!"
   • Watch patients flood ED in real-time
   • Crisis builds to 90%+ capacity
   • AI intervention saves the day
   • Show ROI: $2.4M savings, 1,500% ROI

3. 🏆 SUCCESS METRICS:
   • 60+ judges scanning QR codes
   • Real-time capacity crisis visualization
   • Dramatic AI optimization intervention
   • Live cost savings calculations
   • Individual judge phone updates

📁 DEMO MATERIALS:
   • demo/qr_codes/presentation_qr.png - For main slide
   • demo/qr_codes/table_*.png - For judge tables
   • LIVE_ED_SIMULATION_PLAN.md - Full presentation script

💡 TROUBLESHOOTING:
   • Dashboard not loading? Check port 8501
   • Mobile forms not working? Check port 8000  
   • No real-time updates? Check WebSocket port 8765
   • QR codes not working? Use 0.0.0.0 URLs

🚀 YOU'RE READY TO WOW THE JUDGES! 

Press Ctrl+C to stop all services.
    """
    print(instructions)

def main():
    """Main startup sequence"""
    print_banner()
    
    # Check and install requirements
    if not check_requirements():
        return
    
    # Fix import paths
    fix_imports()
    
    # Start services
    websocket_thread = start_websocket_server()
    mobile_thread = start_mobile_server()
    
    # Generate demo materials
    generate_qr_codes()
    
    # Start main dashboard
    if not start_dashboard():
        print("❌ Failed to start dashboard")
        return
    
    # Print instructions
    print_demo_instructions()
    
    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Live ED Simulation...")
        print("👋 Thanks for the demo! Good luck at the hackathon!")
        sys.exit(0)

if __name__ == "__main__":
    main()