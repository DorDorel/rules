import os
import shutil
import argparse
from pathlib import Path
import re

TARGET_FILES = [
    "CLAUDE.md",
    "GEMINI.md",
    "AGENT.md",
    ".cursorrules",
    ".github/copilot-instructions.md"
]

SKILLS_DEST_DIR = ".prompts/skills"

def get_rule_content(tech_path):
    rule_path = tech_path / "core.md"
    if not rule_path.exists():
        print(f"❌ Error: Could not find core.md in {tech_path}")
        return None
    with open(rule_path, 'r', encoding='utf-8') as f:
        return f.read()

def parse_skill_metadata(file_path):
    description = "No description provided."
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for _ in range(10): 
                line = f.readline()
                if not line: break
                match = re.search(r'(?i)^description:\s*(.+)', line)
                if match:
                    description = match.group(1).strip()
                    break
    except Exception:
        pass
    return description

def sync_skills(source_tech_path, target_project_path):
    source_skills = source_tech_path / "skills"
    target_skills = target_project_path / SKILLS_DEST_DIR
    
    skills_index = []

    if not source_skills.exists():
        return []

    if target_skills.exists():
        shutil.rmtree(target_skills)
    
    target_skills.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_skills, target_skills)

    clean_target_base = SKILLS_DEST_DIR.replace("\\", "/")
    
    for root, dirs, files in os.walk(target_skills):
        for file in files:
            if file.endswith(".md") and not file.startswith('.'):
                full_path = Path(root) / file
                
                rel_path = full_path.relative_to(target_project_path).as_posix()
                
                skill_name = full_path.parent.name if full_path.parent != target_skills else file.replace('.md', '')
                
                description = parse_skill_metadata(full_path)
                
                skills_index.append({
                    "name": skill_name,
                    "path": rel_path,
                    "desc": description
                })
            
    return skills_index

def generate_skills_footer(skills_index):
    if not skills_index:
        return ""
    
    footer = "\n\n---\n\n## 🧩 Capability Library (Skills)\n"
    footer += "You have access to a library of specialized skills. \n"
    footer += "When the user asks for a task that matches a skill's description, **you must READ the corresponding file** to get the instructions.\n\n"
    
    footer += "| Skill Name | Description | File Path |\n"
    footer += "| :--- | :--- | :--- |\n"
    
    sorted_skills = sorted(skills_index, key=lambda x: x['name'])
    
    for skill in sorted_skills:
        clean_desc = skill['desc'].replace("\n", " ").strip()
        
        footer += f"| **{skill['name']}** | {clean_desc} | `{skill['path']}` |\n"
        
    return footer

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("tech")
    parser.add_argument("target", nargs="?", default=".")
    args = parser.parse_args()

    base_path = Path(__file__).parent
    tech_path = base_path / f"{args.tech}_rules"
    target_path = Path(args.target).expanduser().resolve()

    print(f"🚀 Syncing {args.tech} Skills -> {target_path.name}")

    content = get_rule_content(tech_path)
    
    if content:
        skills_index = sync_skills(tech_path, target_path)
        
        final_content = content + generate_skills_footer(skills_index)

        for relative_dest in TARGET_FILES:
            dest_full_path = target_path / relative_dest
            try:
                dest_full_path.parent.mkdir(parents=True, exist_ok=True)
                with open(dest_full_path, 'w', encoding='utf-8') as f:
                    f.write(final_content)
                print(f"   ✅ Updated: {relative_dest}")
            except Exception as e:
                print(f"   ⚠️ Failed: {relative_dest} - {e}")
        
        print(f"\n✨ Success! Indexed {len(skills_index)} skills.")