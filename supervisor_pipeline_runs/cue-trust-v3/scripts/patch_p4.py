"""P4: the agent's bash commands see only an allowlisted environment (cue-trust-v3 isolation hardening, amendment A2).
Without it the commands inherit the whole server environment: the OpenAI key, D4J_* settings (arm flag, API port, external root)
and MSWEA_GLOBAL_CONFIG_DIR, an absolute path into the run tree. Active only when D4J_AGENT_ENV_ALLOWLIST=1 (set by
start_gpt_server.sh); otherwise behaviour is unchanged. The submission tool and the model calls are untouched.
Usage: patch_p4.py <server-root-name> [...]   (also imported by setup_server.py)"""
import sys, os
V3 = "/Users/shawnli/Desktop/Honours/defects4j/.claude/worktrees/strict-depth-experiment-run-524113/supervisor_pipeline_runs/cue-trust-v3"
OLD = '''        if action.get("tool") == "submit_fault_localization":
            return self._submit_fault_localization(action)
        return super().execute(action, cwd=cwd, timeout=timeout)
'''
NEW = '''        if action.get("tool") == "submit_fault_localization":
            return self._submit_fault_localization(action)
        # cue-trust-v3 P4: allowlisted environment for the agent's commands (see scripts/patch_p4.py)
        if os.environ.get("D4J_AGENT_ENV_ALLOWLIST") == "1":
            saved = dict(os.environ)
            try:
                os.environ.clear()
                os.environ.update({k: saved[k] for k in _P4_AGENT_ENV_ALLOW if k in saved})
                return super().execute(action, cwd=cwd, timeout=timeout)
            finally:
                os.environ.clear()
                os.environ.update(saved)
        return super().execute(action, cwd=cwd, timeout=timeout)
'''
HEAD_OLD = "import json\nimport re\nimport time\n"
HEAD_NEW = ('import json\nimport os\nimport re\nimport time\n\n_P4_AGENT_ENV_ALLOW = ("PATH", "HOME", "USER", "LOGNAME", "SHELL", "TMPDIR", "LANG", "LC_ALL", '
            '"LC_CTYPE", "TERM", "JAVA_HOME", "PERL5LIB", "TZ")\n')
def apply(root_dir):
    p = f"{root_dir}/variant-lab/server/agents/mini_swe_fault_localization.py"; t = open(p).read()
    if "cue-trust-v3 P4" in t: return "already"
    assert t.count(OLD) == 1 and t.count(HEAD_OLD) == 1, p
    open(p, "w").write(t.replace(HEAD_OLD, HEAD_NEW, 1).replace(OLD, NEW, 1)); return "applied"
if __name__ == "__main__":
    for n in sys.argv[1:]: print(n, apply(f"{V3}/models/{n}"))
