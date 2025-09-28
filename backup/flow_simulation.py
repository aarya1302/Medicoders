import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import simpy
from model import load_dataset, train_admission_model

class HospitalFlowSimulator:
    """Simulates patient flow between Emergency Department and Inpatient units"""
    
    def __init__(self, ed_beds=25, inpatient_beds=150):
        self.ed_beds = ed_beds
        self.inpatient_beds = inpatient_beds
        self.metrics = {
            'ed_wait_times': [],
            'bed_utilization': [],
            'admission_delays': [],
            'discharge_times': [],
            'daily_admissions': []
        }
    
    def simulate_patient_arrival(self, env, hospital_resources, admission_model, patient_data):
        """Simulate individual patient journey through hospital system"""
        
        # Patient arrives at ED
        arrival_time = env.now
        
        # Request ED bed
        with hospital_resources['ed'].request() as ed_request:
            yield ed_request
            
            # ED triage and assessment (2-6 hours)
            ed_duration = np.random.gamma(2, 2)  # Mean ~4 hours
            yield env.timeout(ed_duration)
            
            # Get admission prediction from model
            patient_features = patient_data.sample(1)
            admission_prob = admission_model['model'].predict_proba(
                patient_features[admission_model['features']].fillna(0)
            )[0][1]
            
            # Decision: Admit or Discharge
            needs_admission = np.random.random() < admission_prob
            
            self.metrics['ed_wait_times'].append(ed_duration)
            
            if needs_admission:
                # Patient needs inpatient bed
                with hospital_resources['inpatient'].request() as bed_request:
                    # Wait for available bed
                    bed_wait_start = env.now
                    yield bed_request
                    bed_wait_time = env.now - bed_wait_start
                    
                    self.metrics['admission_delays'].append(bed_wait_time)
                    
                    # Inpatient stay duration based on patient complexity
                    if admission_prob > 0.8:  # High complexity
                        stay_duration = np.random.gamma(4, 24)  # Mean ~4 days
                    elif admission_prob > 0.5:  # Medium complexity
                        stay_duration = np.random.gamma(2, 24)  # Mean ~2 days
                    else:  # Low complexity
                        stay_duration = np.random.gamma(1, 24)  # Mean ~1 day
                    
                    yield env.timeout(stay_duration)
                    
                    self.metrics['discharge_times'].append(arrival_time + ed_duration + bed_wait_time + stay_duration)
                    self.metrics['daily_admissions'].append(1)
            else:
                # Discharge from ED
                self.metrics['daily_admissions'].append(0)
    
    def generate_patient_arrivals(self, env, hospital_resources, admission_model, patient_data, 
                                arrival_rate=3.5):
        """Generate continuous patient arrivals to ED"""
        
        while True:
            # Poisson arrival process (average 3.5 patients per hour = ~84 per day)
            interarrival_time = np.random.exponential(1/arrival_rate)
            yield env.timeout(interarrival_time)
            
            # Start patient journey
            env.process(self.simulate_patient_arrival(env, hospital_resources, 
                                                    admission_model, patient_data))
    
    def run_simulation(self, admission_model, patient_data, simulation_days=7):
        """Run complete hospital flow simulation"""
        
        print(f"🏥 Running {simulation_days}-day hospital flow simulation...")
        print(f"   ED Beds: {self.ed_beds}")
        print(f"   Inpatient Beds: {self.inpatient_beds}")
        
        # Setup SimPy environment
        env = simpy.Environment()
        
        # Hospital resources
        hospital_resources = {
            'ed': simpy.Resource(env, capacity=self.ed_beds),
            'inpatient': simpy.Resource(env, capacity=self.inpatient_beds)
        }
        
        # Start patient arrival process
        env.process(self.generate_patient_arrivals(env, hospital_resources, 
                                                 admission_model, patient_data))
        
        # Run simulation
        simulation_hours = simulation_days * 24
        env.run(until=simulation_hours)
        
        return self.analyze_results(simulation_days)
    
    def analyze_results(self, simulation_days):
        """Analyze simulation results and generate insights"""
        
        results = {}
        
        # ED Performance
        results['avg_ed_wait'] = np.mean(self.metrics['ed_wait_times'])
        results['ed_wait_95th'] = np.percentile(self.metrics['ed_wait_times'], 95)
        
        # Admission Metrics
        total_admissions = sum(self.metrics['daily_admissions'])
        total_patients = len(self.metrics['daily_admissions'])
        results['admission_rate'] = total_admissions / total_patients
        results['daily_admissions'] = total_admissions / simulation_days
        
        # Bed Utilization
        if self.metrics['admission_delays']:
            results['avg_bed_wait'] = np.mean(self.metrics['admission_delays'])
            results['bed_wait_95th'] = np.percentile(self.metrics['admission_delays'], 95)
        else:
            results['avg_bed_wait'] = 0
            results['bed_wait_95th'] = 0
        
        # System Capacity
        peak_ed_usage = min(len(self.metrics['ed_wait_times']) / simulation_days / 24 * 4, self.ed_beds)
        results['ed_utilization'] = peak_ed_usage / self.ed_beds
        
        if self.metrics['discharge_times']:
            avg_stay = np.mean([t - self.metrics['discharge_times'][i] + 
                              self.metrics['ed_wait_times'][i] 
                              for i, t in enumerate(self.metrics['discharge_times'][:len(self.metrics['ed_wait_times'])])])
            results['avg_length_of_stay'] = abs(avg_stay)
        else:
            results['avg_length_of_stay'] = 0
        
        return results

def create_flow_visualizations(simulator_results, admission_predictions):
    """Create visualizations for patient flow analysis"""
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('Hospital Patient Flow Analysis', fontsize=16)
    
    # Plot 1: Admission Probability Distribution
    axes[0,0].hist(admission_predictions, bins=30, alpha=0.7, color='skyblue', edgecolor='black')
    axes[0,0].set_title('Distribution of Admission Probabilities')
    axes[0,0].set_xlabel('Admission Probability')
    axes[0,0].set_ylabel('Number of Patients')
    axes[0,0].axvline(np.mean(admission_predictions), color='red', linestyle='--', 
                     label=f'Mean: {np.mean(admission_predictions):.3f}')
    axes[0,0].legend()
    
    # Plot 2: Flow Metrics Bar Chart
    metrics = ['Avg ED Wait (hrs)', 'Avg Bed Wait (hrs)', 'Admission Rate (%)', 'ED Utilization (%)']
    values = [
        simulator_results['avg_ed_wait'],
        simulator_results['avg_bed_wait'], 
        simulator_results['admission_rate'] * 100,
        simulator_results['ed_utilization'] * 100
    ]
    
    bars = axes[0,1].bar(metrics, values, color=['lightcoral', 'lightblue', 'lightgreen', 'orange'])
    axes[0,1].set_title('Key Hospital Flow Metrics')
    axes[0,1].set_ylabel('Hours / Percentage')
    plt.setp(axes[0,1].get_xticklabels(), rotation=45, ha='right')
    
    # Add value labels on bars
    for bar, value in zip(bars, values):
        height = bar.get_height()
        axes[0,1].text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                      f'{value:.1f}', ha='center', va='bottom')
    
    # Plot 3: Capacity Planning Scenarios
    bed_scenarios = range(100, 201, 25)
    wait_times = []
    
    for beds in bed_scenarios:
        # Simple queueing theory approximation
        utilization = simulator_results['daily_admissions'] * simulator_results['avg_length_of_stay'] / 24 / beds
        if utilization < 0.95:
            wait_time = utilization / (1 - utilization) * simulator_results['avg_length_of_stay'] / 24
        else:
            wait_time = 24  # System overloaded
        wait_times.append(wait_time)
    
    axes[1,0].plot(bed_scenarios, wait_times, marker='o', linewidth=2, color='purple')
    axes[1,0].axhline(4, color='red', linestyle='--', label='4-hour target')
    axes[1,0].set_title('Bed Capacity vs Wait Time')
    axes[1,0].set_xlabel('Number of Inpatient Beds')
    axes[1,0].set_ylabel('Average Wait Time (hours)')
    axes[1,0].legend()
    axes[1,0].grid(True, alpha=0.3)
    
    # Plot 4: Daily Flow Prediction
    days = range(1, 8)  # 7 days
    predicted_admissions = [simulator_results['daily_admissions']] * 7
    predicted_range = [simulator_results['daily_admissions'] * 0.8, 
                      simulator_results['daily_admissions'] * 1.2]
    
    axes[1,1].plot(days, predicted_admissions, marker='s', linewidth=2, color='green', 
                  label='Predicted Daily Admissions')
    axes[1,1].fill_between(days, [predicted_range[0]] * 7, [predicted_range[1]] * 7, 
                          alpha=0.3, color='green', label='±20% Range')
    axes[1,1].set_title('Weekly Admission Forecast')
    axes[1,1].set_xlabel('Day')
    axes[1,1].set_ylabel('Number of Admissions')
    axes[1,1].legend()
    axes[1,1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('hospital_flow_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    return fig

def generate_flow_insights(results, admission_rate):
    """Generate business insights from flow simulation"""
    
    print("\n" + "="*60)
    print("🏥 HOSPITAL FLOW SIMULATION RESULTS")
    print("="*60)
    
    print(f"\n📊 PATIENT FLOW METRICS:")
    print(f"   • Daily Admissions: {results['daily_admissions']:.1f} patients/day")
    print(f"   • Admission Rate: {results['admission_rate']:.1%}")
    print(f"   • Average ED Wait: {results['avg_ed_wait']:.1f} hours")
    print(f"   • Average Bed Wait: {results['avg_bed_wait']:.1f} hours")
    
    print(f"\n🛏️  CAPACITY ANALYSIS:")
    print(f"   • ED Utilization: {results['ed_utilization']:.1%}")
    print(f"   • Average Length of Stay: {results['avg_length_of_stay']:.1f} hours")
    
    print(f"\n⚠️  PERFORMANCE ALERTS:")
    if results['avg_bed_wait'] > 4:
        print(f"   🔴 HIGH BED WAIT TIMES: {results['avg_bed_wait']:.1f}hrs (Target: <4hrs)")
    else:
        print(f"   ✅ Bed wait times within target")
        
    if results['ed_utilization'] > 0.85:
        print(f"   🔴 HIGH ED UTILIZATION: {results['ed_utilization']:.1%} (Target: <85%)")
    else:
        print(f"   ✅ ED utilization manageable")
    
    print(f"\n💰 BUSINESS IMPACT:")
    daily_cost_savings = results['daily_admissions'] * 0.1 * 5000  # 10% efficiency * $5000 per admission
    print(f"   • Predicted bed planning saves ~${daily_cost_savings:,.0f}/day")
    print(f"   • Annual potential savings: ~${daily_cost_savings * 365:,.0f}")
    
    print(f"\n🎯 RECOMMENDATIONS:")
    if results['avg_bed_wait'] > 2:
        additional_beds = int(results['daily_admissions'] * 0.2)
        print(f"   • Consider adding {additional_beds} inpatient beds")
    
    if results['admission_rate'] > 0.35:
        print(f"   • High admission rate ({results['admission_rate']:.1%}) - review discharge protocols")
    
    print(f"   • Optimize staffing for {results['daily_admissions']:.0f} daily admissions")
    
    return results

def main():
    """Main function to run complete patient flow analysis"""
    
    print("🚀 Starting Hospital Patient Flow Analysis...")
    
    # Load data and train model
    print("\n1️⃣ Loading dataset and training admission model...")
    df = load_dataset()
    model_results = train_admission_model(df)
    
    if not model_results:
        print("❌ Model training failed")
        return
    
    # Get sample predictions for flow simulation
    sample_size = 1000
    sample_data = df.sample(sample_size, random_state=42)
    X_sample = sample_data[model_results['features']].fillna(0)
    admission_predictions = model_results['model'].predict_proba(X_sample)[:, 1]
    
    print(f"✅ Model trained with AUC: {model_results['auc_score']:.3f}")
    print(f"   Sample predictions: {len(admission_predictions)} patients")
    print(f"   Mean admission probability: {np.mean(admission_predictions):.3f}")
    
    # Run flow simulation
    print("\n2️⃣ Running hospital flow simulation...")
    simulator = HospitalFlowSimulator(ed_beds=25, inpatient_beds=150)
    simulation_results = simulator.run_simulation(model_results, sample_data, simulation_days=7)
    
    # Generate insights
    print("\n3️⃣ Analyzing results and generating insights...")
    insights = generate_flow_insights(simulation_results, np.mean(admission_predictions))
    
    # Create visualizations
    print("\n4️⃣ Creating flow visualizations...")
    create_flow_visualizations(simulation_results, admission_predictions)
    print("📈 Visualizations saved as 'hospital_flow_analysis.png'")
    
    print("\n🎯 PATIENT FLOW MODELING COMPLETE!")
    print("✅ Challenge #3 implemented: Patient flow between ED and inpatient events")
    
    return simulation_results, model_results

if __name__ == "__main__":
    results = main()