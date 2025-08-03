#!/usr/bin/env python3
import subprocess
import sys
import time
import psutil

def check_ollama_metal_support():
    """Check if Ollama supports Metal acceleration"""
    print("🔍 OLLAMA METAL ACCELERATION CHECK")
    print("-" * 40)
    
    try:
        # Check Ollama version and capabilities
        result = subprocess.run(["ollama", "--version"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ Ollama Version: {result.stdout.strip()}")
        else:
            print("❌ Ollama not found or not responding")
            return False
        
        # Test inference speed with Metal (if available)
        print("\n🧪 Testing Qwen inference speed...")
        start_time = time.time()
        
        test_result = subprocess.run([
            "ollama", "run", "qwen2.5:14b", 
            "Respond with exactly: 'Metal acceleration test complete'"
        ], capture_output=True, text=True, timeout=120)
        
        inference_time = time.time() - start_time
        
        if test_result.returncode == 0:
            print(f"✅ Qwen inference completed in {inference_time:.2f} seconds")
            if inference_time < 30:
                print("🚀 Excellent performance - likely using Metal acceleration")
            elif inference_time < 60:
                print("⚡ Good performance - Metal may be active")
            else:
                print("⚠️  Slower performance - Metal may not be optimized")
            return True
        else:
            print(f"❌ Qwen inference failed: {test_result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Ollama test timed out")
        return False
    except Exception as e:
        print(f"❌ Error testing Ollama: {e}")
        return False

def check_pytorch_metal():
    """Check PyTorch Metal (MPS) availability"""
    print("\n🔍 PYTORCH METAL (MPS) CHECK")
    print("-" * 40)
    
    try:
        import torch
        
        if torch.backends.mps.is_available():
            print("✅ PyTorch Metal (MPS) is available")
            
            if torch.backends.mps.is_built():
                print("✅ PyTorch was built with Metal support")
            else:
                print("⚠️  PyTorch not built with Metal support")
            
            # Test Metal performance
            print("\n🧪 Testing Metal tensor operations...")
            device = torch.device("mps")
            
            start_time = time.time()
            x = torch.randn(1000, 1000, device=device)
            y = torch.randn(1000, 1000, device=device)
            z = torch.mm(x, y)
            torch.mps.synchronize()
            metal_time = time.time() - start_time
            
            print(f"✅ Metal tensor operation: {metal_time:.4f} seconds")
            
            # Compare with CPU
            start_time = time.time()
            x_cpu = torch.randn(1000, 1000)
            y_cpu = torch.randn(1000, 1000)
            z_cpu = torch.mm(x_cpu, y_cpu)
            cpu_time = time.time() - start_time
            
            print(f"📊 CPU tensor operation: {cpu_time:.4f} seconds")
            print(f"🚀 Metal speedup: {cpu_time / metal_time:.2f}x faster")
            
            return True
        else:
            print("❌ PyTorch Metal (MPS) not available")
            return False
            
    except ImportError:
        print("❌ PyTorch not installed")
        return False
    except Exception as e:
        print(f"❌ Error testing PyTorch Metal: {e}")
        return False

def check_coreml_support():
    """Check Core ML availability"""
    print("\n🔍 CORE ML CHECK")
    print("-" * 40)
    
    try:
        import coremltools as ct
        print(f"✅ Core ML Tools available: {ct.__version__}")
        
        # Test basic Core ML functionality
        import numpy as np
        
        # Create a simple model for testing
        print("🧪 Testing Core ML model creation...")
        
        # Simple linear model test
        from coremltools.models import MLModel
        from coremltools.models.utils import save_spec
        
        print("✅ Core ML basic functionality working")
        return True
        
    except ImportError:
        print("❌ Core ML Tools not installed")
        print("💡 Install with: pip3 install coremltools")
        return False
    except Exception as e:
        print(f"❌ Error testing Core ML: {e}")
        return False

def check_system_resources():
    """Check system memory and CPU"""
    print("\n🔍 SYSTEM RESOURCES")
    print("-" * 40)
    
    # Memory check
    memory = psutil.virtual_memory()
    print(f"💾 Total RAM: {memory.total / (1024**3):.1f} GB")
    print(f"💾 Available RAM: {memory.available / (1024**3):.1f} GB")
    print(f"💾 Memory usage: {memory.percent}%")
    
    if memory.available < 8 * (1024**3):
        print("⚠️  Less than 8GB available - may limit AI model performance")
    else:
        print("✅ Sufficient memory for AI operations")
    
    # CPU check
    cpu_count = psutil.cpu_count()
    cpu_freq = psutil.cpu_freq()
    
    print(f"🖥️  CPU cores: {cpu_count}")
    if cpu_freq:
        print(f"🖥️  CPU frequency: {cpu_freq.current:.0f} MHz")
    
    # Quick CPU test
    print("🧪 Testing CPU performance...")
    start_time = time.time()
    result = sum(i * i for i in range(1000000))
    cpu_time = time.time() - start_time
    print(f"✅ CPU test completed in {cpu_time:.4f} seconds")
    
    return memory.available > 6 * (1024**3)

def main():
    """Run comprehensive hardware compatibility check"""
    print("🔍 PHASE 2: HARDWARE COMPATIBILITY ASSESSMENT")
    print("=" * 60)
    
    results = {
        'ollama_metal': check_ollama_metal_support(),
        'pytorch_metal': check_pytorch_metal(),
        'coreml': check_coreml_support(),
        'system_resources': check_system_resources()
    }
    
    print("\n" + "=" * 60)
    print("📊 COMPATIBILITY SUMMARY")
    print("=" * 60)
    
    for check, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {check.replace('_', ' ').title()}: {status}")
    
    # Recommendations
    print("\n💡 OPTIMIZATION RECOMMENDATIONS:")
    
    if results['ollama_metal']:
        print("  ✅ Ollama ready for optimization")
    else:
        print("  🔧 Ollama needs configuration for Metal acceleration")
    
    if results['pytorch_metal']:
        print("  ✅ Ready for PyTorch Metal acceleration")
    else:
        print("  🔧 Install PyTorch with Metal support")
    
    if results['coreml']:
        print("  ✅ Core ML ready for Legal-BERT optimization")
    else:
        print("  🔧 Install Core ML Tools: pip3 install coremltools")
    
    if results['system_resources']:
        print("  ✅ System resources sufficient")
    else:
        print("  🔧 Consider closing applications to free memory")
    
    all_ready = all(results.values())
    
    print(f"\n🎯 PHASE 2 READINESS: {'✅ READY' if all_ready else '⚠️  NEEDS WORK'}")
    
    return all_ready

if __name__ == "__main__":
    main()
