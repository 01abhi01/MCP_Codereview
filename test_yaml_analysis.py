#!/usr/bin/env python3
"""
Test YAML/Ansible analysis capabilities
"""

import sys
import os
import re

def simple_yaml_test():
    """Simple test of YAML/Ansible patterns"""
    print("🧪 Testing YAML/Ansible Analysis Patterns")
    print("=" * 50)
    
    test_file = "test_ansible.yml"
    
    if not os.path.exists(test_file):
        print("❌ Test file not found")
        return
    
    with open(test_file, 'r') as f:
        content = f.read()
    
    lines = content.split('\n')
    issues = []
    
    print(f"📁 Analyzing: {test_file}")
    print(f"📊 File has {len(lines)} lines")
    
    # Test our analysis patterns
    for i, line in enumerate(lines, 1):
        # Security checks
        if re.search(r'(password|secret|key|token):\s*["\']?[a-zA-Z0-9_\-+=\/]{8,}["\']?', line, re.IGNORECASE):
            issues.append({
                'line': i,
                'type': 'hardcoded_secret',
                'severity': 'high',
                'description': 'Hardcoded secret detected',
                'code': line.strip()
            })
        
        # Ansible deprecated syntax
        if 'include:' in line:
            issues.append({
                'line': i,
                'type': 'deprecated_syntax',
                'severity': 'medium', 
                'description': 'Use include_tasks instead of include',
                'code': line.strip()
            })
        
        # Inefficient modules
        if re.search(r'shell:|command:', line) and any(cmd in line.lower() for cmd in ['apt', 'yum']):
            issues.append({
                'line': i,
                'type': 'inefficient_module',
                'severity': 'medium',
                'description': 'Consider using specific Ansible modules',
                'code': line.strip()
            })
        
        # World writable permissions
        if 'mode:' in line and '777' in line:
            issues.append({
                'line': i,
                'type': 'world_writable',
                'severity': 'medium',
                'description': 'File is world-writable',
                'code': line.strip()
            })
        
        # Debug sensitive info
        if 'debug:' in line and any(sensitive in line.lower() for sensitive in ['password', 'secret', 'key']):
            issues.append({
                'line': i,
                'type': 'debug_sensitive',
                'severity': 'medium',
                'description': 'Debug might expose sensitive info',
                'code': line.strip()
            })
        
        # Deprecated loops
        if 'with_items:' in line:
            issues.append({
                'line': i,
                'type': 'deprecated_loop',
                'severity': 'medium',
                'description': 'with_items is deprecated, use loop',
                'code': line.strip()
            })
    
    print(f"\n🔍 Found {len(issues)} issues:")
    
    # Group by type
    security_issues = [i for i in issues if i['type'] in ['hardcoded_secret', 'debug_sensitive', 'world_writable']]
    quality_issues = [i for i in issues if i['type'] in ['deprecated_syntax']]
    performance_issues = [i for i in issues if i['type'] in ['inefficient_module', 'deprecated_loop']]
    
    if security_issues:
        print(f"\n🔒 Security Issues ({len(security_issues)}):")
        for issue in security_issues:
            print(f"  • Line {issue['line']}: {issue['description']}")
            print(f"    Code: {issue['code']}")
            print()
    
    if quality_issues:
        print(f"\n📝 Quality Issues ({len(quality_issues)}):")
        for issue in quality_issues:
            print(f"  • Line {issue['line']}: {issue['description']}")
            print(f"    Code: {issue['code']}")
            print()
    
    if performance_issues:
        print(f"\n⚡ Performance Issues ({len(performance_issues)}):")
        for issue in performance_issues:
            print(f"  • Line {issue['line']}: {issue['description']}")
            print(f"    Code: {issue['code']}")
            print()
    
    print("✅ YAML/Ansible pattern test completed!")
    print("\n📋 Summary:")
    print(f"   Security issues: {len(security_issues)}")
    print(f"   Quality issues: {len(quality_issues)}")  
    print(f"   Performance issues: {len(performance_issues)}")
    print(f"   Total issues: {len(issues)}")

if __name__ == "__main__":
    simple_yaml_test()
