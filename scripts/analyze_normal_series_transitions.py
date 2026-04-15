#!/usr/bin/env python3
"""
Comprehensive analysis of transitions across all normal models to understand
which configuration pattern is correct.
"""

import json
from pathlib import Path
from collections import defaultdict

BASE = Path("workspace/projects/My_Project/drug_discovery/models/manuscript")

def analyze_normal_series():
    print("=" * 100)
    print("COMPREHENSIVE NORMAL SERIES TRANSITION ANALYSIS")
    print("=" * 100)
    
    for i in range(8):
        normal_path = BASE / f"macrocycle_transport_normal_nme_{i}_enhanced.shy"
        
        with open(normal_path) as f:
            model = json.load(f)
        
        print(f"\n{'='*100}")
        print(f"N-Me {i} (NORMAL)")
        print(f"{'='*100}")
        
        for trans in model['transitions']:
            trans_id = trans['id']
            name = trans['name']
            trans_type = trans.get('transition_type', trans.get('type', ''))
            has_top_rate = 'rate_function' in trans
            has_props_rate = 'rate_function' in trans.get('properties', {})
            
            # Color coding
            if trans_type == 'continuous':
                symbol = "🔵"
            elif trans_type == 'adaptive':
                symbol = "🟢"
            elif trans_type == 'stochastic':
                symbol = "🟡"
            else:
                symbol = "⚪"
            
            rate_info = []
            if has_top_rate:
                rate_info.append("top")
            if has_props_rate:
                rate_info.append("props")
            rate_str = "+".join(rate_info) if rate_info else "none"
            
            print(f"  {symbol} {trans_id:4s} {name:25s} type={trans_type:12s} rate_function={rate_str}")

if __name__ == "__main__":
    analyze_normal_series()
