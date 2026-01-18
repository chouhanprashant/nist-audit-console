from flask import Flask, render_template, request, jsonify, send_file
import json
import os
from datetime import datetime
import uuid

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
REPORTS_FILE = 'data/reports.json'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('data', exist_ok=True)

# Initialize reports file if not exists
if not os.path.exists(REPORTS_FILE):
    with open(REPORTS_FILE, 'w') as f:
        json.dump([], f)

@app.route('/')
def home():
    """Serve main dashboard"""
    return render_template('dashboard.html')

@app.route('/api/upload', methods=['POST'])
def upload_report():
    """Handle report upload"""
    if 'report' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['report']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Generate unique filename
    file_id = str(uuid.uuid4())[:8]
    filename = f"{file_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    
    # Save file
    file.save(filepath)
    
    # Process and save report data
    try:
        with open(filepath, 'r') as f:
            report_data = json.load(f)
        
        # Add metadata
        report_data['_id'] = file_id
        report_data['_filename'] = filename
        report_data['_upload_time'] = datetime.now().isoformat()
        
        # Save to reports database
        with open(REPORTS_FILE, 'r') as f:
            reports = json.load(f)
        
        reports.append(report_data)
        
        with open(REPORTS_FILE, 'w') as f:
            json.dump(reports, f, indent=2)
        
        return jsonify({
            'success': True,
            'id': file_id,
            'server': report_data.get('server_info', {}).get('name', 'Unknown'),
            'score': report_data.get('nist_score', {}).get('percentage', 0)
        })
        
    except json.JSONDecodeError:
        return jsonify({'error': 'Invalid JSON file'}), 400

@app.route('/api/reports')
def get_reports():
    """Get all audit reports"""
    try:
        with open(REPORTS_FILE, 'r') as f:
            reports = json.load(f)
        
        # Format for frontend
        formatted_reports = []
        for report in reports[-10:]:  # Last 10 reports
            formatted_reports.append({
                'id': report.get('_id', ''),
                'server': report.get('server_info', {}).get('name', 'Unknown'),
                'timestamp': report.get('server_info', {}).get('timestamp', ''),
                'score': report.get('nist_score', {}).get('percentage', 0),
                'controls': report.get('security_checks', {})
            })
        
        return jsonify({'reports': formatted_reports})
    
    except:
        return jsonify({'reports': []})

@app.route('/api/stats')
def get_stats():
    """Get dashboard statistics"""
    try:
        with open(REPORTS_FILE, 'r') as f:
            reports = json.load(f)
        
        if not reports:
            return jsonify({
                'servers_count': 0,
                'avg_score': 0,
                'passed_checks': 0,
                'failed_checks': 0
            })
        
        # Calculate stats
        servers_count = len(reports)
        total_score = sum(r.get('nist_score', {}).get('percentage', 0) for r in reports)
        avg_score = total_score / servers_count
        
        # Count checks
        passed_checks = 0
        failed_checks = 0
        
        for report in reports:
            checks = report.get('security_checks', {})
            for check, data in checks.items():
                if isinstance(data, dict) and data.get('status') == 'PASS':
                    passed_checks += 1
                else:
                    failed_checks += 1
        
        return jsonify({
            'servers_count': servers_count,
            'avg_score': round(avg_score, 1),
            'passed_checks': passed_checks,
            'failed_checks': failed_checks
        })
    
    except:
        return jsonify({
            'servers_count': 0,
            'avg_score': 0,
            'passed_checks': 0,
            'failed_checks': 0
        })

@app.route('/download/windows-agent')
def download_windows_agent():
    """Download Windows audit agent"""
    agent_content = '''# Windows NIST Audit Agent
import json
import subprocess
import platform
from datetime import datetime

def run_audit():
    print("Running NIST Audit...")
    # Add your audit code here
    return {"status": "success"}

if __name__ == "__main__":
    run_audit()'''
    
    # Create temporary file
    agent_file = 'windows_audit_agent.py'
    with open(agent_file, 'w') as f:
        f.write(agent_content)
    
    return send_file(agent_file, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
