import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import psutil

# Load environment variables
load_dotenv()

class Config:
    """Comprehensive configuration management for Legal AI system"""
    
    # ========================================
    # CORE DIRECTORIES
    # ========================================
    DATABASE_DIR = Path(os.getenv("DATABASE_DIR", "database"))
    CACHE_DIR = Path(os.getenv("CACHE_DIR", "cache"))
    VECTOR_DATABASE_DIR = Path(os.getenv("VECTOR_DATABASE_DIR", "vector_database"))
    TEMP_DIR = Path(os.getenv("TEMP_DIR", "temp"))
    LOGS_DIR = Path(os.getenv("LOGS_DIR", "logs"))
    
    # Legacy support for vector DB
    VECTOR_DB_DIR = str(VECTOR_DATABASE_DIR)
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    CHUNK_SIZE = 512
    CHUNK_OVERLAP = 50
    AUTHORITY_LEVELS = {"supreme_court": 10, "court_of_appeals": 5, "appellate_division": 8, "civil_court": 12}
    
    # ========================================
    # OLLAMA CONFIGURATION
    # ========================================
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    DEFAULT_OLLAMA_MODEL = os.getenv("DEFAULT_OLLAMA_MODEL", "qwen2.5:14b")
    OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "120"))
    OLLAMA_ENABLE_METAL = os.getenv("OLLAMA_ENABLE_METAL", "true").lower() == "true"
    
    # Legacy support
    GPU_ENABLED = True
    AUTO_LOAD_MODEL = True
    FALLBACK_MODELS = ["qwen2.5:14b"]
    
    # ========================================
    # MEMORY MANAGEMENT
    # ========================================
    MAX_MEMORY_USAGE_PERCENT = int(os.getenv("MAX_MEMORY_USAGE_PERCENT", "75"))
    MEMORY_WARNING_THRESHOLD = int(os.getenv("MEMORY_WARNING_THRESHOLD", "8"))  # GB
    ENABLE_MEMORY_MONITORING = os.getenv("ENABLE_MEMORY_MONITORING", "true").lower() == "true"
    GARBAGE_COLLECTION_INTERVAL = int(os.getenv("GARBAGE_COLLECTION_INTERVAL", "300"))
    AUTO_MEMORY_CLEANUP = os.getenv("AUTO_MEMORY_CLEANUP", "true").lower() == "true"
    
    # ========================================
    # PERFORMANCE OPTIMIZATION
    # ========================================
    ENABLE_METAL_ACCELERATION = os.getenv("ENABLE_METAL_ACCELERATION", "true").lower() == "true"
    ENABLE_COREML_ACCELERATION = os.getenv("ENABLE_COREML_ACCELERATION", "true").lower() == "true"
    THREAD_POOL_SIZE = int(os.getenv("THREAD_POOL_SIZE", "4"))
    MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", "2"))
    
    # ========================================
    # LEGAL RESEARCH CONFIGURATION
    # ========================================
    MAX_CASES_PER_QUERY = int(os.getenv("MAX_CASES_PER_QUERY", "8"))
    CASE_SUMMARY_MAX_LENGTH = int(os.getenv("CASE_SUMMARY_MAX_LENGTH", "4"))
    ENABLE_CASE_CACHING = os.getenv("ENABLE_CASE_CACHING", "true").lower() == "true"
    LEGAL_RESEARCH_MODE = os.getenv("LEGAL_RESEARCH_MODE", "direct")  # direct|vector|hybrid
    
    # ========================================
    # LEGAL-BERT CONFIGURATION
    # ========================================
    LEGAL_BERT_MODEL = os.getenv("LEGAL_BERT_MODEL", "nlpaueb/legal-bert-base-uncased")
    ENABLE_LEGAL_BERT = os.getenv("ENABLE_LEGAL_BERT", "true").lower() == "true"
    LEGAL_BERT_CONFIDENCE_THRESHOLD = float(os.getenv("LEGAL_BERT_CONFIDENCE_THRESHOLD", "0.75"))
    ENABLE_COREML_LEGAL_BERT = os.getenv("ENABLE_COREML_LEGAL_BERT", "true").lower() == "true"
    
    # ========================================
    # SYSTEM PROMPT CONFIGURATION
    # ========================================
    ENABLE_ZERO_HALLUCINATION_MODE = os.getenv("ENABLE_ZERO_HALLUCINATION_MODE", "true").lower() == "true"
    ENFORCE_DOCUMENT_CITATIONS = os.getenv("ENFORCE_DOCUMENT_CITATIONS", "true").lower() == "true"
    REQUIRE_BLUEBOOK_CITATIONS = os.getenv("REQUIRE_BLUEBOOK_CITATIONS", "true").lower() == "true"
    MAX_RESPONSE_LENGTH = int(os.getenv("MAX_RESPONSE_LENGTH", "4000"))
    
    # ========================================
    # DEVELOPMENT & DEBUGGING
    # ========================================
    DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
    ENABLE_PERFORMANCE_LOGGING = os.getenv("ENABLE_PERFORMANCE_LOGGING", "true").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    BENCHMARK_MODE = os.getenv("BENCHMARK_MODE", "false").lower() == "true"
    
    @classmethod
    def validate_config(cls) -> Dict[str, Any]:
        """Validate configuration and system readiness"""
        validation_results = {
            'directories': True,
            'memory': True,
            'ollama': True,
            'performance': True,
            'warnings': [],
            'errors': []
        }
        
        # Validate directories
        try:
            for dir_attr in ['DATABASE_DIR', 'CACHE_DIR', 'VECTOR_DATABASE_DIR', 'TEMP_DIR', 'LOGS_DIR']:
                dir_path = getattr(cls, dir_attr)
                dir_path.mkdir(parents=True, exist_ok=True)
                if not dir_path.exists():
                    validation_results['directories'] = False
                    validation_results['errors'].append(f"Cannot create directory: {dir_path}")
        except Exception as e:
            validation_results['directories'] = False
            validation_results['errors'].append(f"Directory validation error: {e}")
        
        # Validate memory
        try:
            mem = psutil.virtual_memory()
            available_gb = mem.available / (1024**3)
            
            if available_gb < cls.MEMORY_WARNING_THRESHOLD:
                validation_results['warnings'].append(
                    f"Low memory: {available_gb:.1f}GB available (threshold: {cls.MEMORY_WARNING_THRESHOLD}GB)"
                )
            
            if mem.percent > cls.MAX_MEMORY_USAGE_PERCENT:
                validation_results['warnings'].append(
                    f"High memory usage: {mem.percent:.1f}% (max: {cls.MAX_MEMORY_USAGE_PERCENT}%)"
                )
                
        except Exception as e:
            validation_results['memory'] = False
            validation_results['errors'].append(f"Memory validation error: {e}")
        
        return validation_results
    
    @classmethod
    def setup_logging(cls):
        """Setup logging configuration"""
        cls.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=getattr(logging, cls.LOG_LEVEL),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(cls.LOGS_DIR / 'legal_ai.log'),
                logging.StreamHandler() if cls.DEBUG_MODE else logging.NullHandler()
            ]
        )
        
        return logging.getLogger('LegalAI')
    
    @classmethod
    def get_system_info(cls) -> Dict[str, Any]:
        """Get current system information"""
        mem = psutil.virtual_memory()
        
        return {
            'memory': {
                'total_gb': mem.total / (1024**3),
                'available_gb': mem.available / (1024**3),
                'used_percent': mem.percent,
                'status': 'good' if mem.available > cls.MEMORY_WARNING_THRESHOLD * (1024**3) else 'warning'
            },
            'cpu': {
                'cores': psutil.cpu_count(),
                'usage_percent': psutil.cpu_percent(interval=1)
            },
            'config': {
                'ollama_model': cls.DEFAULT_OLLAMA_MODEL,
                'legal_bert_enabled': cls.ENABLE_LEGAL_BERT,
                'metal_enabled': cls.ENABLE_METAL_ACCELERATION,
                'coreml_enabled': cls.ENABLE_COREML_ACCELERATION
            }
        }
    
    @classmethod
    def print_config_summary(cls):
        """Print configuration summary"""
        print("🔧 LEGAL AI CONFIGURATION SUMMARY")
        print("=" * 50)
        print(f"Ollama Model: {cls.DEFAULT_OLLAMA_MODEL}")
        print(f"Legal-BERT: {'✅ Enabled' if cls.ENABLE_LEGAL_BERT else '❌ Disabled'}")
        print(f"Metal Acceleration: {'✅ Enabled' if cls.ENABLE_METAL_ACCELERATION else '❌ Disabled'}")
        print(f"Core ML: {'✅ Enabled' if cls.ENABLE_COREML_ACCELERATION else '❌ Disabled'}")
        print(f"Research Mode: {cls.LEGAL_RESEARCH_MODE}")
        print(f"Max Cases per Query: {cls.MAX_CASES_PER_QUERY}")
        print(f"Memory Threshold: {cls.MEMORY_WARNING_THRESHOLD}GB")
        
        # System info
        system_info = cls.get_system_info()
        print(f"\n💾 Memory: {system_info['memory']['available_gb']:.1f}GB available")
        print(f"🖥️  CPU: {system_info['cpu']['cores']} cores")
        
        # Validation
        validation = cls.validate_config()
        status = "✅ READY" if all([validation['directories'], validation['memory']]) else "⚠️ ISSUES"
        print(f"\n🎯 Status: {status}")

# Initialize logging
logger = Config.setup_logging()
