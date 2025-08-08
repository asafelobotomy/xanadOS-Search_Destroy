#!/usr/bin/env python3
"""
Link verification script for xanadOS-Search_Destroy repository
"""

import re
from pathlib import Path

def check_file_exists(file_path):
    """Check if a file exists."""
    return Path(file_path).exists()

def extract_markdown_links(file_path):
    """Extract markdown links from a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find markdown links [text](path)
        links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
        return links
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return []

def is_internal_link(link):
    """Check if link is internal (not external URL)."""
    return not link.startswith(('http://', 'https://', 'mailto:', '#'))

def resolve_relative_path(link_path, current_file_dir):
    """Resolve relative path to absolute path."""
    if link_path.startswith('../'):
        return (current_file_dir / link_path).resolve()
    elif link_path.startswith('./'):
        return (current_file_dir / link_path[2:]).resolve()
    else:
        return (current_file_dir / link_path).resolve()

def main():
    print("🔍 Comprehensive Link Verification for xanadOS-Search_Destroy")
    print("=" * 60)
    
    # Files to check
    markdown_files = [
        'README.md',
        'docs/README.md',
        'docs/user/Installation.md',
        'docs/user/User_Manual.md', 
        'docs/user/Configuration.md',
        'docs/developer/API.md',
        'docs/developer/CONTRIBUTING.md',
        'docs/developer/DEVELOPMENT.md',
    ]
    
    total_links = 0
    broken_links = 0
    
    for md_file in markdown_files:
        if not check_file_exists(md_file):
            print(f"❌ File not found: {md_file}")
            continue
            
        print(f"\n📄 Checking {md_file}:")
        links = extract_markdown_links(md_file)
        
        if not links:
            print("  ℹ️  No links found")
            continue
        
        current_dir = Path(md_file).parent
        
        for _text, link in links:
            total_links += 1
            
            # Skip external links and anchors
            if not is_internal_link(link):
                continue
                
            # Skip anchor links within the same document
            if link.startswith('#'):
                continue
            
            # Resolve the path
            resolved_path = resolve_relative_path(link, current_dir)
            
            if resolved_path.exists():
                print(f"  ✅ {link}")
            else:
                print(f"  ❌ {link} -> {resolved_path}")
                broken_links += 1
    
    print(f"\n📊 Summary:")
    print(f"  Total internal links checked: {total_links}")
    print(f"  Broken links: {broken_links}")
    
    if broken_links == 0:
        print("  🎉 All links are working!")
    else:
        print(f"  ⚠️  {broken_links} broken links found!")

if __name__ == "__main__":
    main()
