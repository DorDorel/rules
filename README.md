# AGENT Rules & Skills Sync Automation

This repository acts as a **Single Source of Truth (SSOT)** for AI coding rules and skills.
It maintains one `core.md` (strict rules) and a `skills/` directory (specialized tasks) per technology, syncing them to multiple agent configurations (Claude, Gemini, Copilot, Cursor) in your projects.

## 📂 Project Structure

Organize your rules and skills like this:

    /ai-rules-repo
    ├── sync_agents.py          # The automation script
    ├── README.md               # This file
    │
    ├── flutter_rules/          # Source for 'flutter'
    │   ├── core.md             # The MASTER rules file (always active)
    │   └── skills/             # Optional: Task-specific instructions
    │       ├── performance.md
    │       └── animations.md
    │
    └── swiftui_rules/          # Source for 'swiftui'
        ├── core.md
        └── skills/
            └── recipes.md      # e.g., external skills (AvdLee/References)

---

## 🚀 Usage

Run the script to inject rules and skills into a target project.

### Command Syntax
    python sync_agents.py <tech_name> <target_project_path>

### Examples

**1. Sync SwiftUI rules to the current directory:**

    python sync_agents.py swiftui .

**2. Sync Flutter rules to a specific project:**

```
    python sync_agents.py flutter ~/Projects/my-app
```

---

## ⚙️ What Actually Happens?

When you run the script, it performs three actions:

1.  **Syncs Skills:**
    * Copies the contents of `<tech>_rules/skills/` -> `<project>/.prompts/skills/`.
    * *(It cleans the target folder first to ensure strict syncing).*

2.  **Updates Rules:**
    * Reads `<tech>_rules/core.md`.
    * **Dynamically appends** a footer listing the available files in `.prompts/skills`.
    * Writes the combined result to:
        * `root/CLAUDE.md`
        * `root/GEMINI.md`
        * `root/AGENT.md`
        * `root/.cursorrules`
        * `root/.github/copilot-instructions.md`

3.  **Result:**
    The Agent now knows your strict rules **AND** knows exactly where to look (`.prompts/skills/`) when you ask for specific tasks (like "Refactor View" or "Optimize Performance").

---

## 💡 External Skills (e.g., AvdLee)

To use external skill libraries (like [AvdLee/SwiftUI-Agent-Skill](https://github.com/AvdLee/SwiftUI-Agent-Skill)):

1.  Download the desired markdown files (e.g., `reference/`).
2.  Place them inside your source folder: `swiftui_rules/skills/`.
3.  Run the sync command.

The script will automatically propagate them to your projects and link them in the Agent's context.

---

## ⚡ Setup Alias (Optional)

Add this to your `~/.zshrc` or `~/.bashrc` for quick access:
```
    alias rules-sync='python3 /absolute/path/to/ai-rules-repo/sync_agents.py'
```

**Usage:**
```
    cd ~/MyProject
    sync-ai swiftui .
```

---

## 🏆 Credits & Licenses

This repository aggregates knowledge from various expert sources to create a robust development workflow.

- **SwiftUI Skills**: Portions of the SwiftUI skills are adapted from [SwiftUI-Agent-Skill](https://github.com/AvdLee/SwiftUI-Agent-Skill) by **Antoine van der Lee**.
  - Licensed under the **MIT License**.
  - Copyright (c) 2026 Antoine van der Lee.

If you use these files, please respect the original licenses and attribute the authors.