#!/usr/bin/env python3
"""
Memory optimization test script
Run this to verify memory usage is within limits
"""

import requests
import time
import json
from app.utils import get_memory_usage, log_memory_usage

def test_memory_optimization():
    """Test memory usage throughout the pipeline"""
    
    print("🧪 Testing Memory Optimization")
    print("=" * 50)
    
    # Initial memory
    log_memory_usage("Initial")
    
    # Test health endpoint
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data['memory_usage_mb']}MB")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")
    
    # Test memory endpoint
    try:
        response = requests.get("http://localhost:8000/memory")
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Memory status: {data['rss_mb']}MB RSS, {data['percent']}%")
            print(f"📊 Within limit: {data['within_limit']}")
        else:
            print(f"❌ Memory check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Memory check error: {e}")
    
    # Test with sample request
    sample_request = {
        "documents": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
        "questions": ["What is this document about?", "What are the main points?"]
    }
    
    print("\n🔄 Testing sample request...")
    log_memory_usage("Before Request")
    
    try:
        start_time = time.time()
        response = requests.post(
            "http://localhost:8000/api/v1/hackrx/run",
            json=sample_request,
            timeout=60
        )
        end_time = time.time()
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Request successful in {end_time - start_time:.2f}s")
            print(f"📝 Answers: {len(data.get('answers', []))}")
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"📝 Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Request error: {e}")
    
    log_memory_usage("After Request")
    
    # Final memory check
    print("\n📊 Final Memory Summary:")
    memory = get_memory_usage()
    print(f"   RSS: {memory['rss_mb']:.1f}MB")
    print(f"   VMS: {memory['vms_mb']:.1f}MB")
    print(f"   Percent: {memory['percent']:.1f}%")
    print(f"   Available: {memory['available_mb']:.1f}MB")
    
    if memory['rss_mb'] < 400:
        print("✅ Memory usage is within limits!")
    else:
        print("⚠️ Memory usage is high - consider reducing limits")

if __name__ == "__main__":
    test_memory_optimization()
