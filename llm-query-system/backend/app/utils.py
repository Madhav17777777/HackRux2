# utils.py
import psutil
import gc
import os
from typing import Dict, Any

def get_memory_usage() -> Dict[str, Any]:
    """Get current memory usage information"""
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    
    return {
        "rss_mb": memory_info.rss / 1024 / 1024,  # Resident Set Size in MB
        "vms_mb": memory_info.vms / 1024 / 1024,  # Virtual Memory Size in MB
        "percent": process.memory_percent(),
        "available_mb": psutil.virtual_memory().available / 1024 / 1024
    }

def log_memory_usage(stage: str = "Unknown"):
    """Log memory usage at different stages"""
    memory = get_memory_usage()
    print(f"🧠 Memory usage at {stage}: {memory['rss_mb']:.1f}MB RSS, {memory['percent']:.1f}%")

def check_memory_limit(limit_mb: int = 400) -> bool:
    """Check if memory usage is within limits"""
    memory = get_memory_usage()
    if memory['rss_mb'] > limit_mb:
        print(f"⚠️ Memory usage {memory['rss_mb']:.1f}MB exceeds limit {limit_mb}MB")
        return False
    return True

def force_memory_cleanup():
    """Force garbage collection and memory cleanup"""
    gc.collect()
    memory_before = get_memory_usage()
    print(f"🧹 Memory cleanup: {memory_before['rss_mb']:.1f}MB")

def optimize_memory_settings():
    """Set memory optimization environment variables"""
    # Set garbage collection thresholds
    gc.set_threshold(700, 10, 10)
    
    # Set environment variables for memory optimization
    os.environ.setdefault('PYTHONHASHSEED', 'random')
    os.environ.setdefault('PYTHONDONTWRITEBYTECODE', '1')
    
    print("⚙️ Memory optimization settings applied")
