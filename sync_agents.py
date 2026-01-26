import os
import shutil
import argparse
from pathlib import Path

TARGET_FILES = [
    "CLAUDE.md",                      
    "GEMINI.md",                    
    "AGENT.md",
    ".github/copilot-instructions.md",
    ".cursorrules"
]

def sync_rules(tech_name, target_project_path):

    base_rules_path = Path(__file__).parent
    

    source_file = base_rules_path / f"{tech_name}_rules" / "core.md"
    
    if not source_file.exists():
        print(f" Error: Source file not found: {source_file}")
        print(f"   Make sure you have a folder named '{tech_name}_rules' with a 'core.md' file inside.")
        return

    target_path = Path(target_project_path)
    if not target_path.exists():
        print(f" Error: Target project path does not exist: {target_path}")
        return

    print(f" Syncing rules for [{tech_name}] to project: {target_path.name}...")
    

    try:
        with open(source_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f" Error reading source file: {e}")
        return


    success_count = 0
    for relative_dest in TARGET_FILES:
        dest_full_path = target_path / relative_dest
        
        try:

            dest_full_path.parent.mkdir(parents=True, exist_ok=True)
            

            with open(dest_full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"  Created: {relative_dest}")
            success_count += 1
            
        except Exception as e:
            print(f"  Failed to create {relative_dest}: {e}")

    print(f"\n Done! Synced {success_count} files.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sync AI Agent rules to a project.")
    

    parser.add_argument("tech", help="The technology name (e.g., flutter, nestjs, swiftui)")
    

    parser.add_argument("target", help="The path to the target project directory")

    args = parser.parse_args()
    
    sync_rules(args.tech, args.target)