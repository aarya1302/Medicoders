/**
 * Mobile QR Code Handler for Live ED Simulation
 * Handles WebSocket connection, form submission, and real-time updates
 */

class EDPatientApp {
    constructor() {
        this.ws = null;
        this.patientId = null;
        this.sessionId = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;

        // Hospital mapping for WA Health model
        this.hospitalMap = {
            'metro': {
                establishment_code: '8002.0',
                metropolitan_hospital_flag: 1,
                description: 'Metropolitan Hospital'
            },
            'rural': {
                establishment_code: '8000.0',
                metropolitan_hospital_flag: 0,
                description: 'Rural Hospital'
            }
        };

        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.connectWebSocket();
        this.setupPainScale();
        this.setupConditionalFields();
    }
    
    connectWebSocket() {
        const wsUrl = 'https://medicoded-websocket.fly.dev';
        
        try {
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                console.log('Connected to ED server');
                this.updateConnectionStatus('Connected', true);
                this.reconnectAttempts = 0;
                
                // Register as mobile client
                this.ws.send(JSON.stringify({
                    type: 'register',
                    client_type: 'mobile'
                }));
            };
            
            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            };
            
            this.ws.onclose = () => {
                console.log('Disconnected from ED server');
                this.updateConnectionStatus('Disconnected', false);
                this.attemptReconnect();
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateConnectionStatus('Connection Error', false);
            };
            
        } catch (error) {
            console.error('Failed to connect to ED server:', error);
            this.updateConnectionStatus('Connection Failed', false);
        }
    }
    
    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = Math.pow(2, this.reconnectAttempts) * 1000; // Exponential backoff
            
            this.updateConnectionStatus(`Reconnecting in ${delay/1000}s...`, false);
            
            setTimeout(() => {
                console.log(`Reconnection attempt ${this.reconnectAttempts}`);
                this.connectWebSocket();
            }, delay);
        } else {
            this.updateConnectionStatus('Connection Failed', false);
            this.showOfflineMode();
        }
    }
    
    updateConnectionStatus(status, connected) {
        const statusText = document.getElementById('connection-status');
        const statusDot = document.querySelector('.status-dot');
        
        statusText.textContent = status;
        statusDot.className = connected ? 'status-dot active' : 'status-dot';
    }
    
    handleWebSocketMessage(data) {
        console.log('Received:', data);
        
        switch (data.type) {
            case 'session_info':
                this.sessionId = data.session_id;
                console.log(`Joined session: ${this.sessionId}`);
                break;
                
            case 'checkin_success':
                this.handleCheckinSuccess(data);
                break;
                
            case 'checkin_error':
                this.handleCheckinError(data);
                break;
                
            case 'crisis_alert':
                this.showCrisisAlert(data);
                break;
                
            case 'ai_optimization':
                this.showAIOptimization(data);
                break;
                
            case 'patient_update':
                this.updatePatientStatus(data);
                break;
        }
    }
    
    setupEventListeners() {
        // Form submission
        const submitButton = document.getElementById('submit-button');
        submitButton.addEventListener('click', (e) => {
            e.preventDefault();
            this.submitForm();
        });
        
        // Prevent form submission on Enter key
        document.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && e.target.tagName !== 'TEXTAREA') {
                e.preventDefault();
                this.submitForm();
            }
        });
    }
    
    setupPainScale() {
        const painScale = document.getElementById('pain-level');
        const painValue = document.getElementById('pain-value');
        
        painScale.addEventListener('input', (e) => {
            painValue.textContent = e.target.value;
            
            // Change color based on pain level
            const level = parseInt(e.target.value);
            if (level <= 3) {
                painValue.style.color = '#059669'; // Green
            } else if (level <= 6) {
                painValue.style.color = '#d97706'; // Orange
            } else {
                painValue.style.color = '#dc2626'; // Red
            }
        });
    }
    
    setupConditionalFields() {
        const otherCheckbox = document.getElementById('other-complaint');
        const otherDescription = document.getElementById('other-description');
        
        otherCheckbox.addEventListener('change', (e) => {
            if (e.target.checked) {
                otherDescription.style.display = 'block';
                otherDescription.querySelector('textarea').focus();
            } else {
                otherDescription.style.display = 'none';
                otherDescription.querySelector('textarea').value = '';
            }
        });
    }
    
    collectFormData() {
        // Get hospital type selection and map to model features
        const hospitalType = document.getElementById('hospital-type').value;
        const hospitalMapping = this.hospitalMap[hospitalType] || this.hospitalMap['metro']; // Default to metro

        const formData = {
            age: parseInt(document.getElementById('age').value),
            arrival_method: document.getElementById('arrival-method').value,
            hospital_type: hospitalType,
            pain_level: parseInt(document.getElementById('pain-level').value),

            // Hospital mapping for WA Health model
            establishment_code: hospitalMapping.establishment_code,
            metropolitan_hospital_flag: hospitalMapping.metropolitan_hospital_flag,

            // Symptoms
            chest_pain: document.getElementById('chest-pain').checked,
            shortness_breath: document.getElementById('shortness-breath').checked,
            abdominal_pain: document.getElementById('abdominal-pain').checked,
            head_injury: document.getElementById('head-injury').checked,
            altered_mental: document.getElementById('altered-mental').checked,
            nausea_vomiting: document.getElementById('nausea-vomiting').checked,
            broken_bone: document.getElementById('broken-bone').checked,
            other_complaint: document.getElementById('other-text').value || '',

            // Vitals (optional)
            heart_rate: parseInt(document.getElementById('heart-rate').value) || null,
            blood_pressure: document.getElementById('blood-pressure').value || null,

            // Metadata
            timestamp: new Date().toISOString(),
            user_agent: navigator.userAgent
        };

        return formData;
    }
    
    validateForm() {
        const age = document.getElementById('age').value;
        const arrivalMethod = document.getElementById('arrival-method').value;
        const hospitalType = document.getElementById('hospital-type').value;

        if (!age || age < 0 || age > 120) {
            this.showError('Please enter a valid age (0-120)');
            return false;
        }

        if (!arrivalMethod) {
            this.showError('Please select how you arrived');
            return false;
        }

        if (!hospitalType) {
            this.showError('Please select hospital type');
            return false;
        }
        
        // Check if at least one symptom is selected
        const symptoms = [
            'chest-pain', 'shortness-breath', 'abdominal-pain', 
            'head-injury', 'altered-mental', 'nausea-vomiting', 'broken-bone'
        ];
        
        const hasSymptom = symptoms.some(id => document.getElementById(id).checked);
        const hasOtherSymptom = document.getElementById('other-complaint').checked && 
                               document.getElementById('other-text').value.trim();
        
        if (!hasSymptom && !hasOtherSymptom) {
            this.showError('Please select at least one symptom or describe your condition');
            return false;
        }

        // Validate heart rate if provided
        const heartRate = document.getElementById('heart-rate').value;
        if (heartRate && (heartRate < 40 || heartRate > 200)) {
            this.showError('Heart rate must be between 40-200 bpm (or leave blank)');
            return false;
        }

        // Validate blood pressure format if provided
        const bloodPressure = document.getElementById('blood-pressure').value;
        if (bloodPressure && !/^\d{2,3}\/\d{2,3}$/.test(bloodPressure)) {
            this.showError('Blood pressure format should be like "120/80" (or leave blank)');
            return false;
        }

        return true;
    }
    
    submitForm() {
        if (!this.validateForm()) {
            return;
        }
        
        const formData = this.collectFormData();
        const submitButton = document.getElementById('submit-button');
        
        // Show loading state
        submitButton.classList.add('loading');
        submitButton.textContent = 'Checking in...';
        submitButton.disabled = true;
        
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            // Send via WebSocket
            this.ws.send(JSON.stringify({
                type: 'patient_checkin',
                patient_data: formData
            }));
        } else {
            // Fallback: store locally and show offline message
            this.handleOfflineSubmission(formData);
        }
    }
    
    handleCheckinSuccess(data) {
        this.patientId = data.patient_id;
        
        // Update UI elements
        document.getElementById('patient-id-display').textContent = data.patient_id.substring(0, 8);
        document.getElementById('queue-position').textContent = `#${data.position_in_queue}`;
        document.getElementById('estimated-wait').textContent = `${data.estimated_wait} hrs`;
        document.getElementById('priority-display').textContent = data.priority;
        
        // Set priority color
        const priorityBadge = document.getElementById('priority-display');
        if (data.priority === 'P1') {
            priorityBadge.style.color = '#dc2626';
            priorityBadge.nextElementSibling.textContent = 'Critical Priority';
        } else if (data.priority === 'P2') {
            priorityBadge.style.color = '#d97706';
            priorityBadge.nextElementSibling.textContent = 'Moderate Priority';
        } else {
            priorityBadge.style.color = '#059669';
            priorityBadge.nextElementSibling.textContent = 'Standard Priority';
        }
        
        // Add initial update
        this.addUpdate('Checked in successfully');
        
        // Switch to status screen
        this.switchToStatusScreen();
        
        // Reset form button
        const submitButton = document.getElementById('submit-button');
        submitButton.classList.remove('loading');
        submitButton.textContent = 'CHECK IN TO ED';
        submitButton.disabled = false;
    }
    
    handleCheckinError(data) {
        this.showError(`Check-in failed: ${data.error}`);
        
        // Reset form button
        const submitButton = document.getElementById('submit-button');
        submitButton.classList.remove('loading');
        submitButton.textContent = 'CHECK IN TO ED';
        submitButton.disabled = false;
    }
    
    handleOfflineSubmission(formData) {
        // Store form data locally
        localStorage.setItem('pending_checkin', JSON.stringify(formData));
        
        // Show offline success message
        this.showOfflineSuccess();
    }
    
    switchToStatusScreen() {
        const formContainer = document.getElementById('patient-form');
        const statusScreen = document.getElementById('status-screen');
        
        formContainer.style.display = 'none';
        statusScreen.style.display = 'block';
        statusScreen.classList.add('fade-in');
        
        // Start requesting periodic updates
        this.startStatusUpdates();
    }
    
    startStatusUpdates() {
        // Request updates every 30 seconds
        this.updateInterval = setInterval(() => {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify({
                    type: 'request_update',
                    patient_id: this.patientId
                }));
            }
        }, 30000);
    }
    
    addUpdate(text) {
        const updatesList = document.getElementById('updates-list');
        const updateItem = document.createElement('div');
        updateItem.className = 'update-item';
        
        const time = new Date().toLocaleTimeString('en-US', {
            hour12: false,
            hour: '2-digit',
            minute: '2-digit'
        });
        
        updateItem.innerHTML = `
            <span class="update-time">${time}</span>
            <span class="update-text">${text}</span>
        `;
        
        updatesList.insertBefore(updateItem, updatesList.firstChild);
        
        // Keep only last 5 updates
        const updates = updatesList.children;
        if (updates.length > 5) {
            updatesList.removeChild(updates[updates.length - 1]);
        }
    }
    
    updatePatientStatus(data) {
        if (data.patient_id === this.patientId) {
            // Update queue position
            if (data.queue_position !== undefined) {
                document.getElementById('queue-position').textContent = `#${data.queue_position}`;
            }
            
            // Update wait time
            if (data.estimated_wait !== undefined) {
                document.getElementById('estimated-wait').textContent = `${data.estimated_wait} hrs`;
            }
            
            // Add status update
            if (data.status_message) {
                this.addUpdate(data.status_message);
            }
        }
    }
    
    showCrisisAlert(data) {
        const alertDiv = document.getElementById('crisis-alert');
        const alertMessage = document.getElementById('alert-message');
        
        alertMessage.textContent = data.message;
        alertDiv.style.display = 'block';
        
        // Auto-hide after 10 seconds
        setTimeout(() => {
            alertDiv.style.display = 'none';
        }, 10000);
        
        // Add to updates
        this.addUpdate(`🚨 ${data.message}`);
    }
    
    showAIOptimization(data) {
        this.addUpdate('🤖 AI optimization in progress...');
        setTimeout(() => {
            this.addUpdate(data.message);
        }, 2000);
    }
    
    showError(message) {
        // Create error toast
        const errorToast = document.createElement('div');
        errorToast.className = 'crisis-alert';
        errorToast.style.background = 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)';
        errorToast.innerHTML = `
            <div class="alert-content">
                <span class="alert-icon">⚠️</span>
                <span class="alert-text">${message}</span>
            </div>
        `;
        
        document.body.appendChild(errorToast);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            errorToast.remove();
        }, 5000);
    }
    
    showOfflineMode() {
        this.updateConnectionStatus('Offline Mode', false);
        // Could show additional offline instructions here
    }
    
    showOfflineSuccess() {
        document.getElementById('patient-id-display').textContent = 'OFFLINE-' + Math.random().toString(36).substr(2, 6);
        document.getElementById('queue-position').textContent = '#--';
        document.getElementById('estimated-wait').textContent = 'Unknown';
        document.getElementById('priority-display').textContent = 'P?';
        
        this.addUpdate('Stored locally - will sync when connected');
        this.switchToStatusScreen();
    }
}

// Global functions for HTML onclick events
function submitForm() {
    if (window.edApp) {
        window.edApp.submitForm();
    }
}

// Initialize app when page loads
document.addEventListener('DOMContentLoaded', () => {
    console.log('🏥 ED Patient App initializing...');
    window.edApp = new EDPatientApp();
});

// Handle page visibility change (when user switches tabs)
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        // Page is hidden - could pause updates
        console.log('App hidden');
    } else {
        // Page is visible - resume updates
        console.log('App visible');
        if (window.edApp && window.edApp.ws && window.edApp.ws.readyState !== WebSocket.OPEN) {
            window.edApp.connectWebSocket();
        }
    }
});

// Handle beforeunload (when user closes/refreshes page)
window.addEventListener('beforeunload', (e) => {
    if (window.edApp && window.edApp.ws) {
        window.edApp.ws.close();
    }
});