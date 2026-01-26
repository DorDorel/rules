# AI Rules Sync Automation

This repository manages a **Single Source of Truth (SSOT)** for AI coding rules.
It allows you to maintain one `core.md` file per technology and sync it to multiple agent configurations (Claude, Gemini, Copilot, Cursor, etc.) in your projects.

## 📂 Project Structure

Your folder structure should look like this:

    /ai-rules-repo
    ├── sync_agents.py          # The automation script
    ├── README.md               # This file
    │
    ├── flutter_rules/          # Folder name matches the <tech> argument
    │   └── core.md             # The MASTER rules file (edit this)
    │
    ├── nestjs_rules/
    │   └── core.md
    │
    └── swiftui_rules/
        └── core.md

## 🚀 Usage

Run the script to inject the rules into a target project.

### Basic Command
    python sync_agents.py <tech_name> <target_project_path>

**Example:**
Sync Flutter rules to a specific project:

```
    python sync_agents.py flutter ~/Projects/my-cool-app
```

---

## ⚙️ What Gets Created?

The script will automatically create/overwrite the following files in the target project based on your `core.md`:

* `root/CLAUDE.md`
* `root/GEMINI.md`
* `root/AGENT.md`
* `root/.cursorrules`
* `root/.github/copilot-instructions.md` (Creates folder if missing)

To change this list, edit the `TARGET_FILES` list inside `sync_agents.py`.

---

## ⚡ Optional: Shell Alias (Shortcut)

To run this from anywhere without typing the full path, add this to your `~/.zshrc` or `~/.bashrc`:

```
    alias sync-ai='python3 /absolute/path/to/your/ai-rules-repo/sync_agents.py'
```

**Now you can just run (inside your project folder):**

```
    sync-ai flutter .
```