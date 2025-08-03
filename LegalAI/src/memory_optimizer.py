#!/usr/bin/env python3
import psutil
import gc
import subprocess

def analyze_memory():
    """macOS-compatible memory analysis"""
    mem = psutil.virtual_memory()
    
    print("🔍 DETAILED MEMORY ANALYSIS")
    print("-" * 30)
    print(f"Total: {mem.total / (1024**3):.1f}GB")
    print(f"Available: {mem.available / (1024**3):.1f}GB")
    print(f"Used: {mem.used / (1024**3):.1f}GB ({mem.percent:.1f}%)")
    print(f"Free: {mem.free / (1024**3):.1f}GB")
    
    # Recommendations
    if mem.available > 12 * (1024**3):
        print("🎉 Excellent memory availability")
    elif mem.available > 8 * (1024**3):
        print("✅ Good memory availability")
    elif mem.available > 6 * (1024**3):
        print("⚠️  Adequate memory - monitor usage")
    else:
        print("❌ Low memory - optimization needed")
        
    return mem.available > 6 * (1024**3)

def main():
    """Main memory optimization"""
    print("🔧 MEMORY STATUS CHECK")
    print("=" * 40)
    
    sufficient = analyze_memory()
    
    print(f"\n🎯 MEMORY STATUS: {'✅ READY' if sufficient else '⚠️  NEEDS MORE WORK'}")
    return sufficient

if __name__ == "__main__":
    main()
