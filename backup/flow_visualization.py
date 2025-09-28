import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

def create_patient_flow_animation():
    """Create animated visualization of patient flow through hospital"""
    
    # Generate realistic hourly data for 24-hour period
    hours = list(range(24))
    
    # Realistic patterns based on hospital data
    ed_arrivals = [2 + 3*np.sin(2*np.pi*(h-6)/24) + 1.5*np.sin(2*np.pi*h/12) + np.random.normal(0, 0.3) 
                   for h in hours]  # Peak at 6pm, secondary peak at noon
    
    admission_rates = [0.25 + 0.1*np.sin(2*np.pi*(h-18)/24) + np.random.normal(0, 0.02) 
                       for h in hours]  # Higher admissions in evening
    
    ed_occupancy = []
    inpatient_occupancy = []
    wait_times = []
    
    current_ed = 15  # Starting occupancy
    current_inpatient = 120
    
    for i, (arrivals, admit_rate) in enumerate(zip(ed_arrivals, admission_rates)):
        # ED dynamics
        admissions = max(0, arrivals * admit_rate)
        discharges = max(0, arrivals * (1 - admit_rate))
        
        # Update occupancy
        current_ed += arrivals - admissions - discharges
        current_ed = max(0, min(25, current_ed))  # ED capacity 25
        
        current_inpatient += admissions - (admissions * 0.2)  # 20% discharge rate
        current_inpatient = max(80, min(150, current_inpatient))  # Inpatient capacity 150
        
        ed_occupancy.append(current_ed)
        inpatient_occupancy.append(current_inpatient)
        
        # Wait times based on occupancy
        ed_util = current_ed / 25
        wait_time = 1 + ed_util * 6 + (ed_util > 0.8) * (ed_util - 0.8) * 20
        wait_times.append(wait_time)
    
    # Create the animated flow visualization
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Bed Utilization Over Time', 'Wait Times by Hour', 
                       'Admission Patterns', 'Daily Flow Summary'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # Plot 1: Bed utilization over time (top left)
    fig.add_trace(
        go.Scatter(
            x=hours,
            y=[occ/25*100 for occ in ed_occupancy],
            mode='lines+markers',
            name='ED Utilization %',
            line=dict(color='red', width=3)
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=hours,
            y=[occ/150*100 for occ in inpatient_occupancy],
            mode='lines+markers',
            name='Inpatient Utilization %',
            line=dict(color='blue', width=3)
        ),
        row=1, col=1
    )
    
    # Add capacity warning lines
    fig.add_hline(y=85, line_dash="dash", line_color="orange", 
                  annotation_text="Warning Level (85%)", row=1, col=1)
    fig.add_hline(y=95, line_dash="dash", line_color="red", 
                  annotation_text="Critical Level (95%)", row=1, col=1)
    
    # Plot 2: Wait times by hour (top right)
    color_scale = ['green' if wt < 4 else 'orange' if wt < 8 else 'red' for wt in wait_times]
    
    fig.add_trace(
        go.Bar(
            x=hours,
            y=wait_times,
            marker_color=color_scale,
            name='ED Wait Time (hrs)',
            text=[f'{wt:.1f}h' for wt in wait_times],
            textposition='auto'
        ),
        row=1, col=2
    )
    
    # Add target wait time line
    fig.add_hline(y=4, line_dash="dash", line_color="green", 
                  annotation_text="Target: 4 hours", row=1, col=2)
    
    # Plot 3: Admission patterns (bottom left)
    fig.add_trace(
        go.Scatter(
            x=hours,
            y=[rate*100 for rate in admission_rates],
            mode='lines+markers',
            name='Admission Rate %',
            line=dict(color='green', width=3),
            fill='tonexty'
        ),
        row=2, col=1
    )
    
    # Plot 4: Daily flow summary (bottom right)
    flow_categories = ['Total Arrivals', 'ED Discharges', 'Admissions', 'Bed Transfers']
    flow_values = [sum(ed_arrivals), sum(ed_arrivals)*0.7, sum(ed_arrivals)*0.3, sum(ed_arrivals)*0.25]
    
    fig.add_trace(
        go.Bar(
            x=flow_categories,
            y=flow_values,
            marker_color=['lightblue', 'lightgreen', 'orange', 'lightcoral'],
            text=[f'{v:.0f}' for v in flow_values],
            textposition='auto'
        ),
        row=2, col=2
    )
    
    # Update layout
    fig.update_layout(
        height=800,
        title_text="Hospital Patient Flow Simulation - 24 Hour View",
        title_x=0.5,
        showlegend=True,
        template="plotly_white"
    )
    
    # Update axes
    fig.update_xaxes(title_text="Hour of Day", row=1, col=1)
    fig.update_yaxes(title_text="Utilization %", row=1, col=1)
    fig.update_xaxes(title_text="Hour of Day", row=1, col=2)
    fig.update_yaxes(title_text="Wait Time (hours)", row=1, col=2)
    fig.update_xaxes(title_text="Hour of Day", row=2, col=1)
    fig.update_yaxes(title_text="Admission Rate %", row=2, col=1)
    fig.update_xaxes(title_text="Flow Category", row=2, col=2)
    fig.update_yaxes(title_text="Patient Count", row=2, col=2)
    
    return fig

def create_capacity_planning_chart():
    """Create capacity planning visualization"""
    
    # Scenario analysis for different bed configurations
    bed_scenarios = range(100, 201, 10)
    daily_admissions = 25  # From your model
    avg_stay = 3  # days
    
    utilizations = []
    wait_times = []
    costs = []
    
    for beds in bed_scenarios:
        # Simple queueing theory calculations
        utilization = (daily_admissions * avg_stay) / beds
        
        if utilization < 0.95:
            wait_time = (utilization / (1 - utilization)) * 0.5  # hours
        else:
            wait_time = 24  # System overloaded
        
        utilizations.append(utilization)
        wait_times.append(wait_time)
        
        # Cost calculation (bed cost vs delay cost)
        bed_cost = beds * 500  # $500 per bed per day
        delay_cost = max(0, wait_time - 4) * 1000 * daily_admissions  # $1000 per hour delay
        total_cost = bed_cost + delay_cost
        costs.append(total_cost)
    
    # Create subplot
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Bed Utilization vs Capacity', 'Wait Times vs Bed Count', 
                       'Total Daily Costs', 'Optimal Capacity Analysis'),
        vertical_spacing=0.12
    )
    
    # Plot 1: Utilization
    fig.add_trace(
        go.Scatter(
            x=list(bed_scenarios),
            y=[u*100 for u in utilizations],
            mode='lines+markers',
            name='Utilization %',
            line=dict(color='blue', width=3)
        ),
        row=1, col=1
    )
    fig.add_hline(y=85, line_dash="dash", line_color="orange", row=1, col=1)
    fig.add_hline(y=95, line_dash="dash", line_color="red", row=1, col=1)
    
    # Plot 2: Wait times
    color_map = ['green' if wt <= 4 else 'orange' if wt <= 8 else 'red' for wt in wait_times]
    fig.add_trace(
        go.Scatter(
            x=list(bed_scenarios),
            y=wait_times,
            mode='lines+markers',
            name='Wait Time (hrs)',
            line=dict(color='red', width=3),
            marker=dict(color=color_map, size=8)
        ),
        row=1, col=2
    )
    fig.add_hline(y=4, line_dash="dash", line_color="green", row=1, col=2)
    
    # Plot 3: Costs
    fig.add_trace(
        go.Scatter(
            x=list(bed_scenarios),
            y=costs,
            mode='lines+markers',
            name='Total Cost ($)',
            line=dict(color='purple', width=3)
        ),
        row=2, col=1
    )
    
    # Find optimal point (minimum cost)
    optimal_idx = costs.index(min(costs))
    optimal_beds = list(bed_scenarios)[optimal_idx]
    
    fig.add_vline(x=optimal_beds, line_dash="dash", line_color="green", 
                  annotation_text=f"Optimal: {optimal_beds} beds", row=2, col=1)
    
    # Plot 4: Summary metrics at optimal point
    metrics_x = ['Utilization', 'Wait Time', 'Daily Cost', 'Beds Needed']
    metrics_y = [utilizations[optimal_idx]*100, wait_times[optimal_idx], 
                costs[optimal_idx]/1000, optimal_beds]
    
    fig.add_trace(
        go.Bar(
            x=metrics_x,
            y=metrics_y,
            text=[f'{y:.1f}%' if i==0 else f'{y:.1f}h' if i==1 else f'${y:.0f}k' if i==2 else f'{y:.0f}' 
                  for i, y in enumerate(metrics_y)],
            textposition='auto',
            marker_color=['lightblue', 'lightcoral', 'lightgreen', 'orange'],
            name='Optimal Configuration'
        ),
        row=2, col=2
    )
    
    # Update layout
    fig.update_layout(
        height=700,
        title_text="Hospital Capacity Planning Analysis",
        title_x=0.5,
        showlegend=False,
        template="plotly_white"
    )
    
    # Update axes
    fig.update_xaxes(title_text="Number of Beds", row=1, col=1)
    fig.update_yaxes(title_text="Utilization %", row=1, col=1)
    fig.update_xaxes(title_text="Number of Beds", row=1, col=2)
    fig.update_yaxes(title_text="Wait Time (hours)", row=1, col=2)
    fig.update_xaxes(title_text="Number of Beds", row=2, col=1)
    fig.update_yaxes(title_text="Daily Cost ($)", row=2, col=1)
    
    return fig

def create_patient_journey_timeline():
    """Create timeline visualization of individual patient journeys"""
    
    # Simulate 10 patient journeys
    patients = []
    start_time = datetime(2025, 9, 20, 8, 0)  # Hackathon day!
    
    for i in range(10):
        arrival = start_time + timedelta(hours=np.random.exponential(2))
        
        # ED phase
        ed_duration = np.random.gamma(2, 2)  # 2-6 hours typically
        triage_end = arrival + timedelta(hours=0.25)  # 15 min triage
        ed_end = arrival + timedelta(hours=ed_duration)
        
        # Admission decision (using your model's 29.7% rate)
        admitted = np.random.random() < 0.297
        
        if admitted:
            bed_wait = np.random.exponential(1)  # Wait for bed
            bed_start = ed_end + timedelta(hours=bed_wait)
            
            # Length of stay based on complexity
            complexity = np.random.random()
            if complexity > 0.8:  # High complexity (20%)
                stay_days = np.random.gamma(4, 1)  # ~4 days
            elif complexity > 0.5:  # Medium complexity (30%)
                stay_days = np.random.gamma(2, 1)  # ~2 days  
            else:  # Low complexity (50%)
                stay_days = np.random.gamma(1, 1)  # ~1 day
            
            discharge = bed_start + timedelta(days=stay_days)
            outcome = "Inpatient Admit"
        else:
            discharge = ed_end
            outcome = "ED Discharge"
        
        patients.append({
            'Patient': f'Patient {i+1}',
            'Arrival': arrival,
            'Triage_End': triage_end,
            'ED_End': ed_end,
            'Discharge': discharge,
            'Outcome': outcome,
            'Admitted': admitted
        })
    
    # Create Gantt chart
    fig = go.Figure()
    
    colors = {'Triage': 'lightblue', 'ED Treatment': 'orange', 
              'Bed Wait': 'yellow', 'Inpatient Stay': 'lightgreen'}
    
    for i, patient in enumerate(patients):
        y_pos = i
        
        # Triage phase
        fig.add_trace(go.Scatter(
            x=[patient['Arrival'], patient['Triage_End']],
            y=[y_pos, y_pos],
            mode='lines',
            line=dict(color='lightblue', width=15),
            name='Triage' if i == 0 else '',
            showlegend=(i == 0),
            hovertemplate=f"{patient['Patient']}<br>Triage: 15 min<extra></extra>"
        ))
        
        # ED treatment phase
        fig.add_trace(go.Scatter(
            x=[patient['Triage_End'], patient['ED_End']],
            y=[y_pos, y_pos],
            mode='lines',
            line=dict(color='orange', width=15),
            name='ED Treatment' if i == 0 else '',
            showlegend=(i == 0),
            hovertemplate=f"{patient['Patient']}<br>ED Treatment<extra></extra>"
        ))
        
        if patient['Admitted']:
            # Bed wait (if any)
            if patient['ED_End'] < patient['Discharge']:
                bed_start = patient['ED_End'] + timedelta(hours=1)  # Simplified
                
                fig.add_trace(go.Scatter(
                    x=[patient['ED_End'], bed_start],
                    y=[y_pos, y_pos],
                    mode='lines',
                    line=dict(color='yellow', width=15),
                    name='Bed Wait' if i == 0 else '',
                    showlegend=(i == 0 and patient['Admitted']),
                    hovertemplate=f"{patient['Patient']}<br>Waiting for bed<extra></extra>"
                ))
                
                # Inpatient stay
                fig.add_trace(go.Scatter(
                    x=[bed_start, patient['Discharge']],
                    y=[y_pos, y_pos],
                    mode='lines',
                    line=dict(color='lightgreen', width=15),
                    name='Inpatient Stay' if i == 0 else '',
                    showlegend=(i == 0 and patient['Admitted']),
                    hovertemplate=f"{patient['Patient']}<br>Inpatient Stay<extra></extra>"
                ))
        
        # Add outcome markers
        marker_color = 'red' if patient['Admitted'] else 'green'
        fig.add_trace(go.Scatter(
            x=[patient['Discharge']],
            y=[y_pos],
            mode='markers',
            marker=dict(symbol='diamond', size=12, color=marker_color),
            name=patient['Outcome'] if i < 2 else '',
            showlegend=(i < 2),
            hovertemplate=f"{patient['Patient']}<br>{patient['Outcome']}<extra></extra>"
        ))
    
    # Update layout
    fig.update_layout(
        title="Patient Journey Timeline - Hackathon Day Simulation",
        xaxis_title="Time",
        yaxis_title="Patients",
        yaxis=dict(
            tickmode='array',
            tickvals=list(range(10)),
            ticktext=[f'Patient {i+1}' for i in range(10)]
        ),
        height=600,
        template="plotly_white"
    )
    
    return fig

def main():
    """Generate all flow visualizations"""
    print("🎨 Creating Hospital Flow Visualizations...")
    
    # Create the three main visualizations
    flow_fig = create_patient_flow_animation()
    capacity_fig = create_capacity_planning_chart()
    timeline_fig = create_patient_journey_timeline()
    
    # Save as HTML files for easy sharing
    flow_fig.write_html("hospital_flow_simulation.html")
    capacity_fig.write_html("capacity_planning.html") 
    timeline_fig.write_html("patient_journey_timeline.html")
    
    # Show all figures
    flow_fig.show()
    capacity_fig.show()
    timeline_fig.show()
    
    print("✅ Flow visualizations created and saved!")
    print("📁 Files created:")
    print("   • hospital_flow_simulation.html")
    print("   • capacity_planning.html")
    print("   • patient_journey_timeline.html")

if __name__ == "__main__":
    main()