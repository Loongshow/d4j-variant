"""Create one isolated cue-trust-v3 model server root (a patched COPY of the anthropic-pilot-v1 server; the frozen servers are
never modified). Usage: setup_server.py <name>
Patches (each asserted to apply exactly once):
  P1 agents/miniSweAgentAdapter.mjs  - the agent workspace lives OUTSIDE the repository tree under D4J_EXTERNAL_WORKSPACE_ROOT/<random>
                                       (runDir/workspace becomes a symlink to it), so no relative path from the workspace reaches any
                                       run directory, evaluation.json or sibling workspace.
  P2 agents/agentAdapter.mjs         - when D4J_PROMPT_INSPECTION=1 the rendered prompt gains ONE sentence (factor F1); the base
                                       prompt text and its sha256 are unchanged; prompt.json records inspection_requirement."""
import os, sys, json, shutil
V3 = "/Users/shawnli/Desktop/Honours/defects4j/.claude/worktrees/strict-depth-experiment-run-524113/supervisor_pipeline_runs/cue-trust-v3"
SP = "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs"
SRC = f"{SP}/anthropic-pilot-v1/variant-lab"
INSPECTION_SENTENCE = "Before you submit, display the complete source body of every method you rank in your top three."
name = sys.argv[1]; cfg = json.load(open(f"{V3}/models/servers.json"))[name]
root = f"{V3}/models/{name}"; vl = f"{root}/variant-lab"
assert not os.path.exists(vl), f"{vl} exists; refusing to overwrite"
os.makedirs(f"{root}/benchmark_runs", exist_ok=True); os.makedirs(f"{root}/runs", exist_ok=True); os.makedirs(vl)
shutil.copytree(f"{SRC}/server", f"{vl}/server", ignore=shutil.ignore_patterns("__pycache__"))
shutil.copyfile(f"{SRC}/package.json", f"{vl}/package.json")
os.symlink("/Users/shawnli/Desktop/Honours/defects4j/variant-lab/node_modules", f"{vl}/node_modules")
os.symlink(f"{V3}/new_bug_variants", f"{root}/new_bug_variants")
os.symlink("/Users/shawnli/Desktop/Honours/defects4j/workspaces", f"{root}/workspaces")

def patch(rel, old, new):
    p = f"{vl}/server/{rel}"; t = open(p).read(); assert t.count(old) == 1, (rel, old[:60], t.count(old)); open(p, "w").write(t.replace(old, new, 1))

patch("agents/miniSweAgentAdapter.mjs", 'import fsSync from "node:fs";\n', 'import fsSync from "node:fs";\nimport crypto from "node:crypto";\n')
patch("agents/miniSweAgentAdapter.mjs",
      '    const workspaceRoot = path.join(runDir, "workspace");\n    const workspaceRepo = path.join(workspaceRoot, workspaceLabelForTask(taskBundle));',
      '    // cue-trust-v3 P1: external workspace root (no relative path reaches the run tree)\n'
      '    let workspaceRoot = path.join(runDir, "workspace");\n'
      '    const externalBase = process.env.D4J_EXTERNAL_WORKSPACE_ROOT;\n'
      '    if (externalBase) {\n'
      '      const externalRoot = path.join(externalBase, crypto.randomUUID());\n'
      '      await fs.mkdir(externalRoot, { recursive: true });\n'
      '      await fs.rm(workspaceRoot, { recursive: true, force: true });\n'
      '      await fs.symlink(externalRoot, workspaceRoot);\n'
      '      workspaceRoot = externalRoot;\n'
      '    }\n'
      '    const workspaceRepo = path.join(workspaceRoot, workspaceLabelForTask(taskBundle));')
patch("agents/agentAdapter.mjs",
      'Use the repository path above as your working directory. When you have the\nten-method ranking',
      '${process.env.D4J_PROMPT_INSPECTION === "1" ? "' + INSPECTION_SENTENCE + '\\n\\n" : ""}'
      'Use the repository path above as your working directory. When you have the\nten-method ranking')
patch("agents/agentAdapter.mjs",
      '    rendered_prompt_sha256: sha256Text(renderedPrompt),\n  };',
      '    rendered_prompt_sha256: sha256Text(renderedPrompt),\n'
      '    inspection_requirement: process.env.D4J_PROMPT_INSPECTION === "1",\n  };')
json.dump({"name": name, **cfg, "patches": ["P1 external workspace", "P2 inspection sentence switch"], "inspection_sentence": INSPECTION_SENTENCE,
           "copied_from": SRC}, open(f"{root}/SERVER_SETUP.json", "w"), indent=1)
print("server root ready:", root, cfg)
