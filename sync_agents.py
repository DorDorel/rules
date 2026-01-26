import os
import shutil
import argparse
from pathlib import Path

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
        print(f"Error: Could not find core.md in {tech_path}")
        return None
    with open(rule_path, 'r', encoding='utf-8') as f:
        return f.read()

def sync_skills(source_tech_path, target_project_path):
    source_skills = source_tech_path / "skills"
    target_skills = target_project_path / SKILLS_DEST_DIR
    
    available_skills = []

    if not source_skills.exists():
        return []

    if target_skills.exists():
        shutil.rmtree(target_skills)
    
    target_skills.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_skills, target_skills)

    for file in source_skills.iterdir():
        if file.is_file() and not file.name.startswith('.'):
            available_skills.append(file.name)
            
    return available_skills

def generate_skills_footer(skills_list):
    if not skills_list:
        return ""
    
    clean_path = SKILLS_DEST_DIR.replace("\\", "/")
    
    footer = "\n\n---\n\n## Available Skills & Tools\n"
    footer += f"You have access to specialized skills in the `{clean_path}/` directory.\n"
    footer += "Read the corresponding file if the user asks for these tasks:\n\n"
    
    for skill in skills_list:
        footer += f"- **{skill}**: Read `{clean_path}/{skill}`\n"
        
    return footer

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("tech")
    parser.add_argument("target", nargs="?", default=".")
    args = parser.parse_args()

    base_path = Path(__file__).parent
    tech_path = base_path / f"{args.tech}_rules"
    target_path = Path(args.target).expanduser().resolve()

    print(f"Syncing {args.tech} to {target_path.name}")

    content = get_rule_content(tech_path)
    
    if content:
        skills_found = sync_skills(tech_path, target_path)
        final_content = content + generate_skills_footer(skills_found)

        for relative_dest in TARGET_FILES:
            dest_full_path = target_path / relative_dest
            try:
                dest_full_path.parent.mkdir(parents=True, exist_ok=True)
                with open(dest_full_path, 'w', encoding='utf-8') as f:
                    f.write(final_content)
                print(f"Wrote: {relative_dest}")
            except Exception as e:
                print(f"Failed: {relative_dest} - {e}")
        
        print("Done.")