"""
QR Code Generator for Live ED Simulation Demo
Creates QR codes that link to patient check-in form
"""

import qrcode
import os
from PIL import Image, ImageDraw, ImageFont
import uuid

class QRCodeGenerator:
    """Generate QR codes for demo distribution"""
    
    def __init__(self, base_url="http://https://medicoded-form.fly.dev//mobile/patient_form.html"):
        self.base_url = base_url
        self.output_dir = "demo/qr_codes"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def create_patient_qr(self, patient_id=None, scenario=None):
        """Create a QR code for patient check-in"""
        
        if not patient_id:
            patient_id = str(uuid.uuid4())[:8]
        
        # Create URL with patient ID
        url = f"{self.base_url}?patient_id={patient_id}"
        if scenario:
            url += f"&scenario={scenario}"
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        
        # Create QR code image
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        return qr_img, patient_id, url
    
    def create_demo_card(self, patient_id, scenario_info, qr_img):
        """Create a professional demo card with QR code"""
        
        # Card dimensions
        card_width = 600
        card_height = 400
        
        # Create card background
        card = Image.new('RGB', (card_width, card_height), 'white')
        draw = ImageDraw.Draw(card)
        
        try:
            # Try to use a nice font
            title_font = ImageFont.truetype("arial.ttf", 36)
            body_font = ImageFont.truetype("arial.ttf", 18)
            small_font = ImageFont.truetype("arial.ttf", 14)
        except:
            # Fallback to default font
            title_font = ImageFont.load_default()
            body_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # Header background
        draw.rectangle([0, 0, card_width, 80], fill='#1e40af')
        
        # Title
        draw.text((20, 20), "🏥 ROYAL PERTH ED", font=title_font, fill='white')
        draw.text((20, 55), "Emergency Department Check-in", font=body_font, fill='white')
        
        # Patient scenario
        draw.text((20, 120), f"PATIENT SCENARIO:", font=body_font, fill='black')
        draw.text((20, 150), scenario_info['description'], font=body_font, fill='#374151')
        
        # Instructions
        draw.text((20, 200), "INSTRUCTIONS:", font=body_font, fill='black')
        draw.text((20, 230), "1. Scan QR code with your phone", font=small_font, fill='#374151')
        draw.text((20, 250), "2. Fill out the emergency check-in form", font=small_font, fill='#374151')
        draw.text((20, 270), "3. Watch the main screen for your status", font=small_font, fill='#374151')
        
        # Patient ID
        draw.text((20, 320), f"Patient ID: {patient_id}", font=small_font, fill='#64748b')
        draw.text((20, 340), f"Priority: {scenario_info['priority']}", font=small_font, fill='#64748b')
        draw.text((20, 360), "WA Health Hackathon 2025", font=small_font, fill='#64748b')
        
        # Add QR code
        qr_resized = qr_img.resize((200, 200))
        card.paste(qr_resized, (card_width - 220, 120))
        
        return card
    
    def generate_demo_scenarios(self):
        """Generate different patient scenarios for demo"""
        scenarios = [
            {
                "description": "Chest pain, arrived by ambulance, age 67",
                "priority": "P1 - Critical",
                "form_data": {
                    "age": 67,
                    "arrival_method": "Ambulance",
                    "pain_level": 8,
                    "chest_pain": True,
                    "shortness_breath": False
                }
            },
            {
                "description": "Broken arm from fall, age 34, walked in",
                "priority": "P3 - Standard",
                "form_data": {
                    "age": 34,
                    "arrival_method": "Walk-in",
                    "pain_level": 6,
                    "broken_bone": True
                }
            },
            {
                "description": "Severe abdominal pain, age 45",
                "priority": "P2 - Moderate",
                "form_data": {
                    "age": 45,
                    "arrival_method": "Walk-in",
                    "pain_level": 7,
                    "abdominal_pain": True,
                    "nausea_vomiting": True
                }
            },
            {
                "description": "Head injury from accident, age 28",
                "priority": "P1 - Critical",
                "form_data": {
                    "age": 28,
                    "arrival_method": "Ambulance",
                    "pain_level": 9,
                    "head_injury": True,
                    "altered_mental": True
                }
            },
            {
                "description": "Elderly patient, shortness of breath",
                "priority": "P2 - Moderate", 
                "form_data": {
                    "age": 78,
                    "arrival_method": "Walk-in",
                    "pain_level": 4,
                    "shortness_breath": True
                }
            },
            {
                "description": "Young adult, minor complaint",
                "priority": "P3 - Standard",
                "form_data": {
                    "age": 22,
                    "arrival_method": "Walk-in",
                    "pain_level": 3,
                    "other_complaint": "Minor injury"
                }
            },
            {
                "description": "Middle-aged, multiple symptoms",
                "priority": "P2 - Moderate",
                "form_data": {
                    "age": 52,
                    "arrival_method": "Walk-in",
                    "pain_level": 5,
                    "chest_pain": True,
                    "nausea_vomiting": True
                }
            },
            {
                "description": "Senior with chronic conditions",
                "priority": "P2 - Moderate",
                "form_data": {
                    "age": 71,
                    "arrival_method": "Walk-in",
                    "pain_level": 6,
                    "shortness_breath": True,
                    "chest_pain": False
                }
            }
        ]
        
        return scenarios
    
    def create_demo_set(self, count=50):
        """Create a full set of demo QR codes"""
        scenarios = self.generate_demo_scenarios()
        created_cards = []
        
        print(f"🎯 Creating {count} demo QR codes...")
        
        for i in range(count):
            # Cycle through scenarios
            scenario = scenarios[i % len(scenarios)]
            
            # Create QR code
            qr_img, patient_id, url = self.create_patient_qr(
                patient_id=f"DEMO-{i+1:03d}",
                scenario=i % len(scenarios)
            )
            
            # Create demo card
            card = self.create_demo_card(patient_id, scenario, qr_img)
            
            # Save card
            card_filename = f"{self.output_dir}/patient_card_{i+1:03d}.png"
            card.save(card_filename, 'PNG', quality=95)
            
            created_cards.append({
                'filename': card_filename,
                'patient_id': patient_id,
                'scenario': scenario,
                'url': url
            })
            
            if (i + 1) % 10 == 0:
                print(f"✅ Created {i + 1} cards...")
        
        print(f"🎉 Successfully created {count} demo cards in {self.output_dir}/")
        return created_cards
    
    def create_presentation_qr(self):
        """Create a special QR code for presentation use"""
        
        # Create large, simple QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=15,
            border=4,
        )
        qr.add_data(self.base_url)
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Create presentation slide
        slide_width = 1200
        slide_height = 800
        
        slide = Image.new('RGB', (slide_width, slide_height), '#1e40af')
        draw = ImageDraw.Draw(slide)
        
        try:
            big_font = ImageFont.truetype("arial.ttf", 72)
            med_font = ImageFont.truetype("arial.ttf", 48)
            small_font = ImageFont.truetype("arial.ttf", 36)
        except:
            big_font = ImageFont.load_default()
            med_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # Title
        draw.text((slide_width//2, 100), "🏥 EMERGENCY!", anchor="mm", font=big_font, fill='white')
        draw.text((slide_width//2, 180), "You've all had medical emergencies", anchor="mm", font=med_font, fill='white')
        draw.text((slide_width//2, 240), "Scan this QR code to check into the ED", anchor="mm", font=small_font, fill='white')
        
        # Add large QR code
        qr_large = qr_img.resize((400, 400))
        slide.paste(qr_large, (slide_width//2 - 200, 320))
        
        # Save presentation QR
        presentation_file = f"{self.output_dir}/presentation_qr.png"
        slide.save(presentation_file, 'PNG', quality=95)
        
        print(f"📊 Created presentation QR code: {presentation_file}")
        return presentation_file
    
    def create_table_cards(self, tables=10, cards_per_table=5):
        """Create table-specific QR cards for organized distribution"""
        
        scenarios = self.generate_demo_scenarios()
        table_cards = {}
        
        print(f"📋 Creating cards for {tables} tables, {cards_per_table} cards each...")
        
        for table in range(1, tables + 1):
            table_cards[f"Table_{table}"] = []
            
            for card in range(cards_per_table):
                scenario_idx = (table * cards_per_table + card) % len(scenarios)
                scenario = scenarios[scenario_idx]
                
                patient_id = f"T{table:02d}-P{card+1:02d}"
                
                # Create QR code
                qr_img, _, url = self.create_patient_qr(
                    patient_id=patient_id,
                    scenario=scenario_idx
                )
                
                # Create custom card with table info
                card_img = self.create_table_card(table, card+1, patient_id, scenario, qr_img)
                
                # Save card
                filename = f"{self.output_dir}/table_{table:02d}_card_{card+1:02d}.png"
                card_img.save(filename, 'PNG', quality=95)
                
                table_cards[f"Table_{table}"].append({
                    'filename': filename,
                    'patient_id': patient_id,
                    'scenario': scenario,
                    'url': url
                })
        
        print(f"🎯 Created {tables * cards_per_table} table-specific cards!")
        return table_cards
    
    def create_table_card(self, table_num, card_num, patient_id, scenario, qr_img):
        """Create a table-specific card"""
        
        card_width = 500
        card_height = 350
        
        card = Image.new('RGB', (card_width, card_height), 'white')
        draw = ImageDraw.Draw(card)
        
        try:
            title_font = ImageFont.truetype("arial.ttf", 28)
            body_font = ImageFont.truetype("arial.ttf", 16)
            small_font = ImageFont.truetype("arial.ttf", 12)
        except:
            title_font = ImageFont.load_default()
            body_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # Header
        draw.rectangle([0, 0, card_width, 60], fill='#dc2626')
        draw.text((15, 15), f"🏥 TABLE {table_num} - CARD {card_num}", font=title_font, fill='white')
        
        # Scenario
        draw.text((15, 80), "YOUR EMERGENCY:", font=body_font, fill='black')
        draw.text((15, 105), scenario['description'], font=body_font, fill='#374151')
        
        # Instructions
        draw.text((15, 150), "1. Scan QR code with phone →", font=small_font, fill='#64748b')
        draw.text((15, 170), "2. Fill emergency check-in form", font=small_font, fill='#64748b')
        draw.text((15, 190), "3. Watch main screen for updates", font=small_font, fill='#64748b')
        
        # Patient info
        draw.text((15, 230), f"Patient ID: {patient_id}", font=small_font, fill='#64748b')
        draw.text((15, 250), f"Expected Priority: {scenario['priority']}", font=small_font, fill='#64748b')
        
        # Footer
        draw.text((15, 310), "WA Health Hackathon 2025 - Live ED Simulation", font=small_font, fill='#94a3b8')
        
        # QR code
        qr_resized = qr_img.resize((150, 150))
        card.paste(qr_resized, (card_width - 170, 100))
        
        return card

def main():
    """Generate all demo materials"""
    print("🏥 WA Health Hackathon - QR Code Generator")
    print("=" * 50)
    
    # Initialize generator
    generator = QRCodeGenerator()
    
    # Create presentation QR
    generator.create_presentation_qr()
    
    # Create table cards
    table_cards = generator.create_table_cards(tables=10, cards_per_table=5)
    
    # Create extra individual cards
    individual_cards = generator.create_demo_set(count=25)
    
    print("\n🎉 Demo materials created successfully!")
    print(f"📁 All files saved to: {generator.output_dir}")
    print("\n📋 What was created:")
    print("  • 1 presentation QR code (for slides)")
    print("  • 50 table-specific cards (10 tables × 5 cards)")
    print("  • 25 individual demo cards")
    print(f"  • Total: {1 + 50 + 25} files")
    
    print("\n🎯 Demo Instructions:")
    print("1. Display presentation_qr.png on main screen")
    print("2. Distribute table cards to judge tables")
    print("3. Use individual cards for backup/extras")
    print("4. Start WebSocket server before demo")
    print("5. Open live dashboard on main display")

if __name__ == "__main__":
    main()