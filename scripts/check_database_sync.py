#!/usr/bin/env python3
"""Check what's currently in the SQLite database."""

import sys
import os
import sqlite3

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

db_path = "/home/simao/projetos/shypn/workspace/compound_cache.db"

print("="*70)
print("CHECKING CURRENT DATABASE STATE")
print("="*70)

if not os.path.exists(db_path):
    print("❌ Database doesn't exist yet")
    sys.exit(0)

with sqlite3.connect(db_path) as conn:
    cursor = conn.cursor()
    
    # Check total count
    cursor.execute("SELECT COUNT(*) FROM compounds")
    total = cursor.fetchone()[0]
    print(f"\n📊 Total compounds in database: {total}")
    
    # Check ATP specifically
    print("\n" + "="*70)
    print("CHECKING ATP (C00002):")
    print("="*70)
    cursor.execute("""
        SELECT compound_id, compound_name, delta_g_formation, charge, 
               n_protons, pKa_values, source, notes
        FROM compounds 
        WHERE compound_id = 'C00002'
    """)
    
    atp = cursor.fetchone()
    if atp:
        print(f"✓ Found in database:")
        print(f"  ID: {atp[0]}")
        print(f"  Name: {atp[1]}")
        print(f"  ΔGf°: {atp[2]}")
        print(f"  Charge: {atp[3]}")
        print(f"  #Protons: {atp[4]}")
        print(f"  pKa: {atp[5]}")
        print(f"  Source: {atp[6]}")
        print(f"  Notes: {atp[7]}")
        
        if atp[2] is None:
            print("\n⚠️  PROBLEM: No thermodynamic data (ΔGf° is NULL)")
            print("   This was seeded from mapper without thermodynamic properties")
        elif atp[2] == -2292.5:
            print("\n✓ Has correct placeholder thermodynamic data!")
        else:
            print(f"\n⚠️  Unexpected ΔGf° value: {atp[2]}")
    else:
        print("❌ C00002 (ATP) NOT in database")
    
    # Check a few more compounds
    print("\n" + "="*70)
    print("SAMPLE OF DATABASE CONTENTS:")
    print("="*70)
    cursor.execute("""
        SELECT compound_id, compound_name, delta_g_formation, charge, source
        FROM compounds 
        LIMIT 10
    """)
    
    print(f"\n{'ID':<10} {'Name':<15} {'ΔGf°':<12} {'Charge':<8} {'Source':<12}")
    print("-"*70)
    for row in cursor.fetchall():
        dgf = f"{row[2]:.2f}" if row[2] is not None else "NULL"
        charge = row[3] if row[3] is not None else "NULL"
        print(f"{row[0]:<10} {row[1]:<15} {dgf:<12} {charge:<8} {row[4]:<12}")
    
    # Check statistics by source
    print("\n" + "="*70)
    print("STATISTICS BY SOURCE:")
    print("="*70)
    cursor.execute("""
        SELECT source, COUNT(*), 
               SUM(CASE WHEN delta_g_formation IS NOT NULL THEN 1 ELSE 0 END) as with_thermo
        FROM compounds 
        GROUP BY source
    """)
    
    print(f"{'Source':<15} {'Count':<10} {'With Thermo':<15}")
    print("-"*70)
    for row in cursor.fetchall():
        print(f"{row[0]:<15} {row[1]:<10} {row[2]:<15}")

print("\n" + "="*70)
print("CONCLUSION:")
print("="*70)

# Check if there are compounds without thermodynamic data
with sqlite3.connect(db_path) as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM compounds WHERE delta_g_formation IS NULL")
    count_no_thermo = cursor.fetchone()[0]
    
    if count_no_thermo > 0:
        print(f"⚠️  {count_no_thermo} compounds have NO thermodynamic data")
        print("   These were seeded from CompoundMapper (names/IDs only)")
        print("\n💡 RECOMMENDATION:")
        print("   Delete the database and let it rebuild with placeholder data:")
        print("   rm workspace/compound_cache.db")
    else:
        print("✓ All compounds have thermodynamic data!")
