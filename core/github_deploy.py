"""
GitHub deployment module for editorial highlights
Handles git operations and GitHub Pages deployment
"""

import os
import subprocess
import shutil
from pathlib import Path
from typing import Optional


class GitHubDeployer:
    def __init__(self):
        self.repo_path = None
        
    def deploy(self, source_dir: str, repo_name: str, deploy_path: str, 
               commit_message: str, username: str) -> str:
        """Deploy highlights to GitHub Pages"""
        
        # Set up repo path
        self.repo_path = Path.home() / 'Documents' / 'GitHub' / repo_name
        
        # Ensure repository exists
        if not self.ensure_repo_exists(repo_name, username):
            raise Exception("Failed to set up repository")
        
        # Copy files to repo
        target_path = self.repo_path / deploy_path
        self.copy_files(source_dir, target_path)
        
        # Generate index if needed
        self.update_main_index()
        
        # Commit and push
        self.git_commit_push(commit_message)
        
        # Return the deployed URL
        return f"https://{username}.github.io/{repo_name}/{deploy_path}/"
    
    def ensure_repo_exists(self, repo_name: str, username: str) -> bool:
        """Ensure the GitHub repository exists locally"""
        
        if self.repo_path.exists():
            # Repository exists, ensure it's a git repo
            if not (self.repo_path / '.git').exists():
                print("✓ Initializing git repository...")
                self.run_git_command(['init'], cwd=self.repo_path)
                self.setup_github_remote(repo_name, username)
            return True
        
        # Try to clone existing repo
        print(f"✓ Setting up repository...")
        repo_url = f"https://github.com/{username}/{repo_name}.git"
        
        try:
            # Try to clone
            self.repo_path.parent.mkdir(parents=True, exist_ok=True)
            result = subprocess.run(
                ['git', 'clone', repo_url, str(self.repo_path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print("✓ Repository cloned")
                return True
                
        except Exception:
            pass
        
        # Create new repo locally
        print("✓ Creating new repository...")
        self.repo_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize git
        self.run_git_command(['init'], cwd=self.repo_path)
        
        # Create initial files
        readme_path = self.repo_path / 'README.md'
        if not readme_path.exists():
            readme_content = f"""# Editorial Highlights

A collection of video highlights for presentations and editorial use.

## Structure

Highlights are organized by date and topic in subdirectories.

---

Generated with Editorial Highlights Generator
"""
            readme_path.write_text(readme_content)
        
        # Set up GitHub Pages
        self.setup_github_pages()
        
        # Add remote
        self.setup_github_remote(repo_name, username)
        
        # Initial commit
        self.run_git_command(['add', '.'], cwd=self.repo_path)
        self.run_git_command(['commit', '-m', 'Initial repository setup'], cwd=self.repo_path)
        
        print(f"\n⚠ Note: You'll need to create the repository on GitHub:")
        print(f"  1. Go to https://github.com/new")
        print(f"  2. Name it: {repo_name}")
        print(f"  3. Create as PUBLIC repository")
        print(f"  4. Don't initialize with README")
        print(f"  5. Run: git push -u origin main")
        
        return True
    
    def setup_github_remote(self, repo_name: str, username: str):
        """Set up GitHub remote"""
        repo_url = f"https://github.com/{username}/{repo_name}.git"
        
        # Check if remote exists
        result = self.run_git_command(['remote'], cwd=self.repo_path)
        
        if 'origin' not in result.stdout:
            self.run_git_command(['remote', 'add', 'origin', repo_url], cwd=self.repo_path)
    
    def setup_github_pages(self):
        """Set up GitHub Pages configuration"""
        # Create .nojekyll file to prevent Jekyll processing
        nojekyll_path = self.repo_path / '.nojekyll'
        if not nojekyll_path.exists():
            nojekyll_path.touch()
        
        # Create basic index.html if doesn't exist
        index_path = self.repo_path / 'index.html'
        if not index_path.exists():
            self.create_main_index()
    
    def copy_files(self, source_dir: str, target_path: Path):
        """Copy highlight files to repository"""
        # Create target directory
        target_path.mkdir(parents=True, exist_ok=True)
        
        # Copy all files from source
        source_path = Path(source_dir)
        for file in source_path.glob('*'):
            if file.is_file():
                shutil.copy2(file, target_path / file.name)
                print(f"✓ Copied {file.name}")
    
    def update_main_index(self):
        """Update the main index.html with links to all highlights"""
        index_path = self.repo_path / 'index.html'
        
        # Find all highlight directories
        highlight_dirs = []
        for item in self.repo_path.rglob('index.html'):
            if item.parent != self.repo_path:
                rel_path = item.parent.relative_to(self.repo_path)
                highlight_dirs.append(str(rel_path))
        
        # Sort by date (assuming YYYY-MM format)
        highlight_dirs.sort(reverse=True)
        
        # Generate HTML
        self.create_main_index(highlight_dirs)
    
    def create_main_index(self, highlight_dirs: Optional[list] = None):
        """Create the main index.html file"""
        
        if highlight_dirs:
            links_html = ""
            for dir_path in highlight_dirs:
                # Make the path more readable
                display_name = dir_path.replace('/', ' / ').replace('-', ' ').title()
                links_html += f"""
                <a href="{dir_path}/" class="highlight-link">
                    <div class="highlight-card">
                        <div class="path">{dir_path}</div>
                        <div class="title">{display_name}</div>
                    </div>
                </a>
                """
        else:
            links_html = "<p>No highlights yet. Deploy your first highlight to see it here.</p>"
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Editorial Highlights Collection</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }}
        
        .container {{
            max-width: 1000px;
            margin: 0 auto;
        }}
        
        h1 {{
            color: white;
            text-align: center;
            margin-bottom: 40px;
            font-size: 2.5em;
            text-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }}
        
        .highlights-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
        }}
        
        .highlight-link {{
            text-decoration: none;
        }}
        
        .highlight-card {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 12px;
            padding: 20px;
            transition: all 0.3s ease;
            cursor: pointer;
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        }}
        
        .highlight-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 15px 30px rgba(0,0,0,0.2);
        }}
        
        .path {{
            font-size: 12px;
            color: #667eea;
            font-family: monospace;
            margin-bottom: 8px;
        }}
        
        .title {{
            font-size: 16px;
            color: #333;
            font-weight: 500;
        }}
        
        p {{
            color: white;
            text-align: center;
            font-size: 18px;
            margin-top: 40px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Editorial Highlights Collection</h1>
        <div class="highlights-grid">
            {links_html}
        </div>
    </div>
</body>
</html>"""
        
        index_path = self.repo_path / 'index.html'
        index_path.write_text(html_content)
    
    def git_commit_push(self, message: str):
        """Commit and push changes to GitHub"""
        # Add all changes
        self.run_git_command(['add', '.'], cwd=self.repo_path)
        
        # Commit
        result = self.run_git_command(['commit', '-m', message], cwd=self.repo_path)
        
        if "nothing to commit" in result.stdout:
            print("✓ No changes to commit")
            return
        
        # Push
        print("✓ Pushing to GitHub...")
        result = self.run_git_command(['push', 'origin', 'main'], cwd=self.repo_path)
        
        if result.returncode != 0:
            # Try to push to master instead
            result = self.run_git_command(['push', 'origin', 'master'], cwd=self.repo_path)
            
            if result.returncode != 0:
                # Try to set upstream
                result = self.run_git_command(['push', '-u', 'origin', 'main'], cwd=self.repo_path)
                
                if result.returncode != 0:
                    print("\n⚠ Push failed. You may need to:")
                    print("  1. Create the repository on GitHub first")
                    print("  2. Run: git push -u origin main")
                    print(f"  From: {self.repo_path}")
    
    def run_git_command(self, args: list, cwd: Path = None) -> subprocess.CompletedProcess:
        """Run a git command"""
        if cwd is None:
            cwd = self.repo_path
            
        return subprocess.run(
            ['git'] + args,
            cwd=cwd,
            capture_output=True,
            text=True
        )