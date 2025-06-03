"""
Configuration management for DumpSleuth
"""

import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


@dataclass
class AnalysisConfig:
    """Analysis configuration settings"""
    string_min_length: int = 4
    string_max_length: int = 256
    max_file_size: int = 1024  # MB
    parallel_processing: bool = True
    worker_threads: int = 4
    encoding: List[str] = field(default_factory=lambda: ["utf-8", "utf-16", "ascii"])
    

@dataclass
class OutputConfig:
    """Output configuration settings"""
    output_dir: str = "reports"
    formats: List[str] = field(default_factory=lambda: ["html", "json"])
    compress: bool = False
    include_raw_data: bool = False
    archive_after_days: int = 30
    

@dataclass
class PluginConfig:
    """Plugin configuration settings"""
    plugin_dir: str = "plugins"
    enabled: List[str] = field(default_factory=list)
    settings: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    

@dataclass
class DumpSleuthConfig:
    """Main configuration class for DumpSleuth"""
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    plugins: PluginConfig = field(default_factory=PluginConfig)
    
    # Performance settings
    buffer_size: int = 64  # MB
    cache_enabled: bool = True
    cache_size: int = 512  # MB
    chunk_size: int = 10  # MB
    use_mmap: bool = True
    
    # Security settings
    sandbox: bool = True
    malware_scan: bool = True
    validate_signatures: bool = True
    
    # Debug settings
    debug: bool = False
    log_level: str = "INFO"
    

class ConfigManager:
    """Manages configuration loading and validation"""
    
    DEFAULT_CONFIG_PATHS = [
        Path("config/default.yaml"),
        Path("config/dumpsleuth.yaml"),
        Path.home() / ".dumpsleuth" / "config.yaml",
        Path("/etc/dumpsleuth/config.yaml")
    ]
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self.config = DumpSleuthConfig()
        self._load_config()
        
    def _load_config(self) -> None:
        """Load configuration from file"""
        config_file = self._find_config_file()
        
        if config_file and config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    if config_file.suffix == '.yaml' or config_file.suffix == '.yml':
                        data = yaml.safe_load(f)
                    elif config_file.suffix == '.json':
                        data = json.load(f)
                    else:
                        raise ValueError(f"Unsupported config format: {config_file.suffix}")
                        
                if data:
                    self._update_config(data)
                    
            except Exception as e:
                print(f"Warning: Failed to load config from {config_file}: {e}")
                
    def _find_config_file(self) -> Optional[Path]:
        """Find configuration file"""
        if self.config_path:
            return Path(self.config_path)
            
        for path in self.DEFAULT_CONFIG_PATHS:
            if path.exists():
                return path
                
        return None
        
    def _update_config(self, data: Dict[str, Any]) -> None:
        """Update configuration from dictionary"""
        # Analysis settings
        if 'analysis' in data:
            analysis_data = data['analysis']
            if 'strings' in analysis_data:
                string_config = analysis_data['strings']
                self.config.analysis.string_min_length = string_config.get('min_length', 4)
                self.config.analysis.string_max_length = string_config.get('max_length', 256)
                self.config.analysis.encoding = string_config.get('encoding', ["utf-8", "utf-16", "ascii"])
                
            self.config.analysis.max_file_size = analysis_data.get('max_file_size', 1024)
            self.config.analysis.parallel_processing = analysis_data.get('parallel_processing', True)
            
        # Output settings
        if 'output' in data:
            output_data = data['output']
            self.config.output.output_dir = output_data.get('output_dir', 'reports')
            self.config.output.formats = output_data.get('formats', ['html', 'json'])
            self.config.output.compress = output_data.get('compress', False)
            self.config.output.include_raw_data = output_data.get('include_raw_data', False)
            
        # Plugin settings
        if 'plugins' in data:
            plugin_data = data['plugins']
            self.config.plugins.plugin_dir = plugin_data.get('plugin_dir', 'plugins')
            self.config.plugins.enabled = plugin_data.get('enabled', [])
            
            # Plugin-specific settings
            for key, value in plugin_data.items():
                if key not in ['plugin_dir', 'enabled'] and isinstance(value, dict):
                    self.config.plugins.settings[key] = value
                    
        # Performance settings
        if 'performance' in data:
            perf_data = data['performance']
            self.config.buffer_size = perf_data.get('buffer_size', 64)
            self.config.cache_enabled = perf_data.get('cache_enabled', True)
            self.config.cache_size = perf_data.get('cache_size', 512)
            self.config.chunk_size = perf_data.get('chunk_size', 10)
            self.config.use_mmap = perf_data.get('use_mmap', True)
            
        # Security settings
        if 'security' in data:
            sec_data = data['security']
            self.config.sandbox = sec_data.get('sandbox', True)
            self.config.malware_scan = sec_data.get('malware_scan', True)
            self.config.validate_signatures = sec_data.get('validate_signatures', True)
            
        # General settings
        if 'general' in data:
            gen_data = data['general']
            self.config.debug = gen_data.get('debug', False)
            self.config.analysis.worker_threads = gen_data.get('workers', 4)
            
    def get_config(self) -> DumpSleuthConfig:
        """Get the current configuration"""
        return self.config
        
    def get_plugin_config(self, plugin_name: str) -> Dict[str, Any]:
        """Get configuration for a specific plugin"""
        return self.config.plugins.settings.get(plugin_name, {})
        
    def save_config(self, path: Optional[str] = None) -> None:
        """Save current configuration to file"""
        save_path = Path(path) if path else Path("config/dumpsleuth.yaml")
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to dictionary
        config_dict = self._config_to_dict()
        
        with open(save_path, 'w') as f:
            yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)
            
    def _config_to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'general': {
                'debug': self.config.debug,
                'workers': self.config.analysis.worker_threads
            },
            'analysis': {
                'strings': {
                    'min_length': self.config.analysis.string_min_length,
                    'max_length': self.config.analysis.string_max_length,
                    'encoding': self.config.analysis.encoding
                },
                'max_file_size': self.config.analysis.max_file_size,
                'parallel_processing': self.config.analysis.parallel_processing
            },
            'output': {
                'output_dir': self.config.output.output_dir,
                'formats': self.config.output.formats,
                'compress': self.config.output.compress,
                'include_raw_data': self.config.output.include_raw_data,
                'archive_after_days': self.config.output.archive_after_days
            },
            'plugins': {
                'plugin_dir': self.config.plugins.plugin_dir,
                'enabled': self.config.plugins.enabled,
                **self.config.plugins.settings
            },
            'performance': {
                'buffer_size': self.config.buffer_size,
                'cache_enabled': self.config.cache_enabled,
                'cache_size': self.config.cache_size,
                'chunk_size': self.config.chunk_size,
                'use_mmap': self.config.use_mmap
            },
            'security': {
                'sandbox': self.config.sandbox,
                'malware_scan': self.config.malware_scan,
                'validate_signatures': self.config.validate_signatures
            }
        }
    
    def validate_config(self) -> List[str]:
        """Validate configuration and return any warnings"""
        warnings = []
        
        # Check file size limits
        if self.config.analysis.max_file_size > 2048:
            warnings.append("Max file size is very large (>2GB), this may cause memory issues")
            
        # Check worker threads
        import multiprocessing
        cpu_count = multiprocessing.cpu_count()
        if self.config.analysis.worker_threads > cpu_count * 2:
            warnings.append(f"Worker threads ({self.config.analysis.worker_threads}) exceeds 2x CPU count ({cpu_count})")
            
        # Check output directory
        output_path = Path(self.config.output.output_dir)
        if not output_path.exists():
            try:
                output_path.mkdir(parents=True, exist_ok=True)
            except:
                warnings.append(f"Cannot create output directory: {output_path}")
                
        # Check plugin directory
        if self.config.plugins.enabled:
            plugin_path = Path(self.config.plugins.plugin_dir)
            if not plugin_path.exists():
                warnings.append(f"Plugin directory does not exist: {plugin_path}")
                
        return warnings