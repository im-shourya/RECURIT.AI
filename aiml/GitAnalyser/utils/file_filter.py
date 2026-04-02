"""
File filtering utilities for selecting important repository files.
Filters by language, ignores build artifacts, and prioritizes entry points.
"""
import os
from typing import List, Dict, Set


class FileFilter:
    """Filter and prioritize repository files."""
    
    # Supported programming languages and their extensions
    SUPPORTED_EXTENSIONS = {
        '.py': 'Python',
        '.c': 'C',
        '.cpp': 'C++',
        '.cc': 'C++',
        '.cxx': 'C++',
        '.h': 'C/C++',
        '.hpp': 'C++',
        '.java': 'Java',
        '.js': 'JavaScript',
        '.jsx': 'JavaScript',
        '.ts': 'TypeScript',
        '.tsx': 'TypeScript',
        '.html': 'HTML',
        '.css': 'CSS',
    }
    
    # Configuration file extensions
    CONFIG_EXTENSIONS = {
        '.json', '.yml', '.yaml', '.toml', '.ini', '.cfg', '.conf', '.xml'
    }
    
    # Common config file names
    CONFIG_FILES = {
        'package.json', 'requirements.txt', 'setup.py', 'setup.cfg', 'pyproject.toml',
        'pom.xml', 'build.gradle', 'Makefile', 'CMakeLists.txt', 'Dockerfile',
        '.gitignore', '.dockerignore', 'tsconfig.json', 'webpack.config.js',
        'babel.config.js', '.eslintrc', '.prettierrc'
    }
    
    # Directories to ignore
    IGNORE_DIRS = {
        'node_modules', 'venv', 'env', '.env', 'virtualenv', '__pycache__',
        'build', 'dist', 'target', 'bin', 'obj', '.git', '.svn', '.hg',
        'vendor', 'packages', '.idea', '.vscode', 'coverage', '.nyc_output',
        'out', 'tmp', 'temp', '.cache', '.pytest_cache', '.mypy_cache',
        'bower_components', 'jspm_packages'
    }
    
    # Binary/generated file patterns
    IGNORE_PATTERNS = {
        '.pyc', '.pyo', '.so', '.dll', '.exe', '.o', '.a', '.lib',
        '.jar', '.war', '.ear', '.class', '.min.js', '.bundle.js',
        '.map', '.lock', '.log', '.swp', '.swo', '.DS_Store',
        '.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg', '.pdf',
        '.zip', '.tar', '.gz', '.rar', '.7z'
    }
    
    # Entry point file names (high priority)
    ENTRY_POINTS = {
        'main.py', 'app.py', '__main__.py', 'server.py', 'index.py',
        'main.js', 'index.js', 'app.js', 'server.js',
        'Main.java', 'Application.java',
        'main.c', 'main.cpp'
    }
    
    @classmethod
    def should_ignore_file(cls, file_path: str) -> bool:
        """Determine if a file should be ignored."""
        # Check if in ignored directory
        path_parts = file_path.split('/')
        for part in path_parts[:-1]:  # Exclude filename itself
            if part in cls.IGNORE_DIRS or part.startswith('.'):
                return True
        
        # Check file extension
        _, ext = os.path.splitext(file_path)
        if ext.lower() in cls.IGNORE_PATTERNS:
            return True
        
        # Check if it's a hidden file
        filename = os.path.basename(file_path)
        if filename.startswith('.') and filename not in cls.CONFIG_FILES:
            return True
        
        return False
    
    @classmethod
    def get_file_language(cls, file_path: str) -> str:
        """Determine programming language from file extension."""
        _, ext = os.path.splitext(file_path)
        return cls.SUPPORTED_EXTENSIONS.get(ext.lower(), 'Unknown')
    
    @classmethod
    def is_config_file(cls, file_path: str) -> bool:
        """Check if file is a configuration file."""
        filename = os.path.basename(file_path)
        _, ext = os.path.splitext(file_path)
        
        return filename in cls.CONFIG_FILES or ext.lower() in cls.CONFIG_EXTENSIONS
    
    @classmethod
    def is_entry_point(cls, file_path: str) -> bool:
        """Check if file is likely an entry point."""
        filename = os.path.basename(file_path)
        return filename in cls.ENTRY_POINTS
    
    @classmethod
    def get_file_role(cls, file_path: str) -> str:
        """Determine the role/purpose of a file."""
        if cls.is_entry_point(file_path):
            return "entry_point"
        elif cls.is_config_file(file_path):
            return "configuration"
        elif cls.get_file_language(file_path) != 'Unknown':
            return "source_code"
        else:
            return "other"
    
    @classmethod
    def filter_important_files(cls, files: List[Dict], max_files: int = 50) -> List[Dict]:
        """
        Filter and prioritize important files from repository tree.
        Returns up to max_files most important files.
        """
        important_files = []
        
        for file in files:
            if file.get('type') != 'blob':  # Only process files, not directories
                continue
            
            path = file.get('path', '')
            
            # Skip ignored files
            if cls.should_ignore_file(path):
                continue
            
            # Check if it's a supported file type or config
            language = cls.get_file_language(path)
            role = cls.get_file_role(path)
            
            if language != 'Unknown' or role == 'configuration':
                # Assign priority score
                priority = 0
                
                # Entry points get highest priority
                if cls.is_entry_point(path):
                    priority = 100
                # Config files get high priority
                elif cls.is_config_file(path):
                    priority = 80
                # Source files in root or main directories
                elif '/' not in path or path.split('/')[0] in ['src', 'lib', 'app']:
                    priority = 60
                # Other source files
                else:
                    priority = 40
                
                # Prefer shorter paths (likely more important)
                depth = path.count('/')
                priority -= depth * 5
                
                important_files.append({
                    'path': path,
                    'language': language,
                    'role': role,
                    'priority': priority,
                    'size': file.get('size', 0)
                })
        
        # Sort by priority (descending) and limit
        important_files.sort(key=lambda x: x['priority'], reverse=True)
        
        # Limit total size to avoid fetching too much content
        selected_files = []
        total_size = 0
        max_total_size = 1_000_000  # 1MB total
        
        for file in important_files[:max_files]:
            if total_size + file['size'] > max_total_size:
                break
            selected_files.append(file)
            total_size += file['size']
        
        return selected_files