#!/usr/bin/env python3
"""
NIST Audit Agent for Windows Server
Run this on Windows Server to generate audit report
"""
import json
import subprocess
import platform
import socket
from datetime import datetime

def get_system_info():
    """Get basic system information"""
    return {
        "name": platform.node(),
        "os": platform.system(),
        "version": platform.version(),
        "processor": platform.processor(),
        "timestamp": datetime.now().isoformat()
    }

def check_windows_updates():
    """Check Windows updates status"""
    try:
        # PowerShell command to get update count
        ps_cmd = '''
        $Session = New-Object -ComObject Microsoft.Update.Session
        $Searcher = $Session.CreateUpdateSearcher()
        $SearchResult = $Searcher.Search("IsInstalled=0")
        $SearchResult.Updates.Count
        '''
        
        result = subprocess.run(['powershell', '-Command', ps_cmd], 
                              capture_output=True, text=True, shell=True)
        update_count = int(result.stdout.strip()) if result.stdout.strip().isdigit() else 0
        
        return {
            "status": "PASS" if update_count < 10 else "WARNING",
            "details": f"{update_count} updates pending",
            "score": 1 if update_count < 5 else 0.5
        }
    except:
        return {"status": "FAIL", "details": "Cannot check", "score": 0}

def check_firewall():
    """Check Windows Firewall status"""
    try:
        result = subprocess.run(['netsh', 'advfirewall', 'show', 'allprofiles'], 
                              capture_output=True, text=True, shell=True)
        enabled = 'ON' in result.stdout
        
        return {
            "status": "PASS" if enabled else "FAIL",
            "details": "Enabled" if enabled else "Disabled",
            "score": 1 if enabled else 0
        }
    except:
        return {"status": "FAIL", "details": "Cannot check", "score": 0}

def check_rdp():
    """Check Remote Desktop status"""
    try:
        result = subprocess.run(['reg', 'query', 
                               'HKLM\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server', 
                               '/v', 'fDenyTSConnections'], 
                              capture_output=True, text=True, shell=True)
        rdp_enabled = '0x0' in result.stdout
        
        return {
            "status": "WARNING" if rdp_enabled else "PASS",
            "details": "Enabled" if rdp_enabled else "Disabled",
            "score": 0.5 if rdp_enabled else 1
        }
    except:
        return {"status": "FAIL", "details": "Cannot check", "score": 0}

def run_audit():
    """Main audit function"""
    print("🔍 Starting NIST Security Audit...")
    
    results = {
        "server_info": get_system_info(),
        "security_checks": {},
        "nist_score": {"score": 0, "max_score": 0, "percentage": 0}
    }
    
    # Run checks
    checks = [
        ("windows_updates", check_windows_updates),
        ("firewall", check_firewall),
        ("remote_desktop", check_rdp)
    ]
    
    for check_name, check_func in checks:
        print(f"Checking {check_name}...")
        results["security_checks"][check_name] = check_func()
    
    # Calculate score
    total_score = sum(check["score"] for check in results["security_checks"].values())
    max_score = len(results["security_checks"])
    results["nist_score"] = {
        "score": total_score,
        "max_score": max_score,
        "percentage": round((total_score / max_score) * 100, 1) if max_score > 0 else 0
    }
    
    return results

def save_report(data):
    """Save audit report to file"""
    filename = f"nist_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"✅ Audit complete!")
    print(f"📊 NIST Score: {data['nist_score']['percentage']}%")
    print(f"📄 Report saved: {filename}")
    
    # Show summary
    print("\n📋 CHECK SUMMARY:")
    for check_name, check_data in data["security_checks"].items():
        status_icon = "✅" if check_data["status"] in ["PASS", "WARNING"] else "❌"
        print(f"{status_icon} {check_name}: {check_data['details']}")
    
    return filename

if __name__ == "__main__":
    print("="*50)
    print("NIST SECURITY AUDIT AGENT")
    print("="*50)
    
    # Run audit
    audit_results = run_audit()
    
    # Save report
    report_file = save_report(audit_results)
    
    print("\n📤 Instructions:")
    print(f"1. Upload '{report_file}' to NIST Audit Console")
    print("2. View dashboard for compliance analysis")
    print("="*50)
