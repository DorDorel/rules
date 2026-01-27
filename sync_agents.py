import os
import shutil
import argparse
from pathlib import Path
import re

SKILL_TARGETS = [
    ".github/skills",
    ".gemini/skills",
    ".prompts/skills",
    ".claude/skills"
]

INSTRUCTION_FILES = [
    "CLAUDE.md",
    "GEMINI.md",
    "AGENT.md",
    ".cursorrules",
    ".github/copilot-instructions.md"
]

def get_rule_content(tech_path):
    rule_path = tech_path / "core.md"
    if not rule_path.exists():
        print(f"❌ Error: Could not find core.md in {tech_path}")
        return None
    with open(rule_path, 'r', encoding='utf-8') as f:
        return f.read()

def parse_metadata(file_path):
    name = file_path.parent.name
    description = f"Expert coding patterns for {name}."

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            match = re.search(r'(?i)^description:\s*(.+)', content)
            if match:
                description = match.group(1).strip()
    except Exception as e:
        print(f"⚠️ Warning reading {file_path}: {e}")
        content = ""

    return name, description, content

def create_skill_md_content(name, description, original_content):
    cleaned_content = re.sub(r'(?i)^description:\s*.+\n', '', original_content, count=1)

    return f"""---
name: {name}
description: {description}
---

{cleaned_content}
"""

def sync_skills_to_targets(source_tech_path, target_project_path):
    source_skills = source_tech_path / "skills"

    if not source_skills.exists():
        print(f"⚠️ Source skills folder not found at: {source_skills}")
        return 0

    count = 0

    for target_rel_path in SKILL_TARGETS:
        full_target_dir = target_project_path / target_rel_path
        if full_target_dir.exists():
            shutil.rmtree(full_target_dir)
        full_target_dir.mkdir(parents=True, exist_ok=True)

    for item in source_skills.iterdir():
        if item.is_dir():
            src_file = item / "prompt.md"
            if not src_file.exists(): src_file = item / "SKILL.md"
            if not src_file.exists(): src_file = item / "skill.md"

            if src_file.exists():
                name, desc, raw_content = parse_metadata(src_file)
                new_content = create_skill_md_content(name, desc, raw_content)

                for target_rel_path in SKILL_TARGETS:
                    target_dir = target_project_path / target_rel_path / name
                    target_dir.mkdir(parents=True, exist_ok=True)

                    dest_file = target_dir / "SKILL.md"

                    with open(dest_file, 'w', encoding='utf-8') as f:
                        f.write(new_content)

                    if target_rel_path == ".github/skills":
                         print(f"   🔨 Created: {target_rel_path}/{name}/SKILL.md")

                count += 1

    return count

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("tech")
    parser.add_argument("target", nargs="?", default=".")
    args = parser.parse_args()

    base_path = Path(__file__).parent
    tech_path = base_path / f"{args.tech}_rules"
    target_path = Path(args.target).expanduser().resolve()

    print(f"🚀 Starting Native Skills Deployment (SKILL.md)...")

    skill_count = sync_skills_to_targets(tech_path, target_path)
    print(f"\n✨ Successfully deployed {skill_count} skills.")

    core_content = get_rule_content(tech_path)
    if core_content:
        footer = "\n\n---\n\n## ⚡️ Native Skills Active\n"
        footer += "This workspace uses native skills structure (`.github/skills/SKILL.md`, etc).\n"

        final_content = core_content + footer

        for relative_dest in INSTRUCTION_FILES:
            dest_full_path = target_path / relative_dest
            try:
                dest_full_path.parent.mkdir(parents=True, exist_ok=True)
                with open(dest_full_path, 'w', encoding='utf-8') as f:
                    f.write(final_content)
            except Exception:
                pass
        print("✅ Instruction files updated.")