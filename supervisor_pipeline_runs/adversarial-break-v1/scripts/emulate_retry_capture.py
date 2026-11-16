import os, sys
os.environ["MSWEA_MODEL_RETRY_STOP_AFTER_ATTEMPT"] = "2"
os.environ["ANTHROPIC_BASE_URL"] = "http://127.0.0.1:9"; os.environ["ANTHROPIC_API_KEY"] = "emulation-placeholder-not-a-real-key"
from minisweagent.models.litellm_model import LitellmModel
m = LitellmModel(model_name="anthropic/claude-sonnet-4-6", model_kwargs={"drop_params": True})
try:
    m.query([{"role": "user", "content": "say hi"}])
except Exception as e:
    print("FINAL EXCEPTION:", type(e).__name__, str(e)[:120])
