#!/usr/bin/env python3
"""
Test script for Editorial Highlights System
Verifies all components are properly installed and configured
"""

import sys
import importlib


def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")
    
    modules_to_test = [
        ('core.processor', 'VideoProcessor'),
        ('core.summarizer', 'SummaryGenerator'),
        ('core.github_deploy', 'GitHubDeployer'),
        ('core.config_manager', 'ConfigManager'),
    ]
    
    all_good = True
    
    for module_name, class_name in modules_to_test:
        try:
            module = importlib.import_module(module_name)
            if hasattr(module, class_name):
                print(f"  ✓ {module_name}.{class_name}")
            else:
                print(f"  ✗ {module_name}.{class_name} not found")
                all_good = False
        except ImportError as e:
            print(f"  ✗ {module_name}: {e}")
            all_good = False
    
    return all_good


def test_dependencies():
    """Test that external dependencies are available"""
    print("\nTesting dependencies...")
    
    dependencies = [
        'PIL',
        'requests',
        'numpy',
    ]
    
    optional_deps = [
        ('transformers', 'AI summarization'),
        ('torch', 'AI models'),
        ('pytube', 'YouTube downloads'),
        ('moviepy', 'Video processing'),
        ('yt_dlp', 'Transcript downloads'),
    ]
    
    all_good = True
    
    # Test required dependencies
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"  ✓ {dep}")
        except ImportError:
            print(f"  ✗ {dep} - REQUIRED")
            all_good = False
    
    # Test optional dependencies
    print("\nOptional dependencies:")
    for dep, purpose in optional_deps:
        try:
            __import__(dep)
            print(f"  ✓ {dep} ({purpose})")
        except ImportError:
            print(f"  ⚠ {dep} ({purpose}) - Optional but recommended")
    
    return all_good


def test_git():
    """Test that git is available"""
    print("\nTesting Git...")
    
    import subprocess
    try:
        result = subprocess.run(['git', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  ✓ Git installed: {result.stdout.strip()}")
            return True
        else:
            print("  ✗ Git not working properly")
            return False
    except FileNotFoundError:
        print("  ✗ Git not found - REQUIRED for deployment")
        return False


def test_config():
    """Test configuration setup"""
    print("\nTesting configuration...")
    
    try:
        from core.config_manager import ConfigManager
        config = ConfigManager()
        
        if config.has_github_config():
            github_config = config.get_github_config()
            print(f"  ✓ GitHub configured: {github_config['username']}/{github_config['repo']}")
        else:
            print("  ⚠ GitHub not configured (will be set up on first run)")
        
        return True
    except Exception as e:
        print(f"  ✗ Configuration error: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 50)
    print("Editorial Highlights System - Component Test")
    print("=" * 50)
    
    results = []
    
    results.append(test_imports())
    results.append(test_dependencies())
    results.append(test_git())
    results.append(test_config())
    
    print("\n" + "=" * 50)
    if all(results):
        print("✅ All core components working!")
        print("\nYou can now run: python editorial_highlights.py")
    else:
        print("⚠️  Some components need attention")
        print("\nInstall missing dependencies with: pip install -r requirements.txt")
        print("Ensure Git is installed on your system")
    print("=" * 50)


if __name__ == "__main__":
    main()