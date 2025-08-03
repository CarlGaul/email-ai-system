#!/usr/bin/env python3
import subprocess
import json
import re

def check_qwen_quantization():
    """Check Qwen model quantization status"""
    print("🔍 QWEN QUANTIZATION ANALYSIS")
    print("-" * 40)
    
    try:
        # Get detailed model info
        result = subprocess.run(["ollama", "show", "qwen2.5:14b"], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            print("❌ Could not get Qwen model information")
            print("💡 Try: ollama pull qwen2.5:14b")
            return False
        
        output = result.stdout
        print("📋 Model Information:")
        print(output)
        
        # Check for quantization indicators
        if "q4" in output.lower():
            print("✅ Model appears to be 4-bit quantized (optimal)")
            quantized = True
        elif "q8" in output.lower():
            print("⚠️  Model appears to be 8-bit quantized")
            print("💡 Consider q4_0 for better performance: ollama pull qwen2.5:14b:q4_0")
            quantized = True
        elif "fp16" in output.lower() or "16-bit" in output.lower():
            print("⚠️  Model appears to be 16-bit (not quantized)")
            print("💡 Pull quantized version: ollama pull qwen2.5:14b:q4_0")
            quantized = False
        else:
            print("❓ Quantization status unclear from output")
            quantized = None
        
        # Check model size as indicator
        size_match = re.search(r'Size:\s*(\d+\.?\d*)\s*([KMGT]B)', output, re.IGNORECASE)
        if size_match:
            size_value = float(size_match.group(1))
            size_unit = size_match.group(2).upper()
            
            if size_unit == 'GB':
                if size_value < 10:
                    print(f"✅ Model size ({size_value:.1f}GB) suggests good quantization")
                elif size_value < 15:
                    print(f"⚠️  Model size ({size_value:.1f}GB) suggests partial quantization")
                else:
                    print(f"❌ Model size ({size_value:.1f}GB) suggests no quantization")
        
        return quantized
        
    except subprocess.TimeoutExpired:
        print("⏰ Ollama command timed out")
        return False
    except Exception as e:
        print(f"❌ Error checking quantization: {e}")
        return False

def optimize_quantization():
    """Suggest quantization optimization"""
    print("\n🔧 QUANTIZATION OPTIMIZATION")
    print("-" * 40)
    
    print("💡 For optimal performance on M4 MacBook Air:")
    print("   1. Use 4-bit quantization: ollama pull qwen2.5:14b:q4_0")
    print("   2. Model should be ~9GB (vs ~28GB unquantized)")
    print("   3. Significant memory savings with minimal quality loss")
    
    return True

def main():
    """Main quantization check"""
    quantized = check_qwen_quantization()
    optimize_quantization()
    
    print(f"\n🎯 QUANTIZATION STATUS: {'✅ OPTIMIZED' if quantized else '⚠️  NEEDS OPTIMIZATION'}")
    
    return quantized

if __name__ == "__main__":
    main()
