export const providerEnvRequirements = {
  openai: {
    provider: "openai",
    required_any: ["D4J_OPENAI_API_KEY", "OPENAI_API_KEY"],
    required_model: "D4J_OPENAI_MODEL",
    optional: ["OPENAI_BASE_URL", "D4J_OPENAI_BASE_URL"],
    supported_by_adapter: true,
  },
  anthropic: {
    provider: "anthropic",
    required_any: ["D4J_ANTHROPIC_API_KEY", "ANTHROPIC_API_KEY"],
    optional: ["D4J_CLAUDE_MODEL"],
    supported_by_adapter: false,
  },
  moonshot: {
    provider: "moonshot",
    required_any: ["D4J_KIMI_API_KEY", "KIMI_API_KEY", "MOONSHOT_API_KEY"],
    optional: ["D4J_KIMI_MODEL"],
    supported_by_adapter: false,
  },
  kimi: {
    provider: "kimi",
    required_any: ["D4J_KIMI_API_KEY", "KIMI_API_KEY", "MOONSHOT_API_KEY"],
    optional: ["D4J_KIMI_MODEL"],
    supported_by_adapter: false,
  },
};

function normalizeProvider(provider) {
  const value = String(provider ?? "").trim().toLowerCase();
  if (value === "kimi") return "kimi";
  if (value === "moonshot") return "moonshot";
  if (value === "anthropic") return "anthropic";
  return value || "openai";
}

function firstConfiguredEnv(names, env) {
  return names.find((name) => Boolean(String(env[name] ?? "").trim())) ?? "";
}

export function resolveProviderConfig(profile, env = process.env) {
  const provider = normalizeProvider(profile?.provider);
  const requirement = providerEnvRequirements[provider] ?? {
    provider,
    required_any: [],
    required_model: "",
    optional: [],
    supported_by_adapter: false,
  };
  const credentialSource = firstConfiguredEnv(requirement.required_any, env);
  const credentialConfigured = Boolean(credentialSource);
  const model = requirement.required_model ? String(env[requirement.required_model] ?? "").trim() : String(profile?.model ?? "").trim();
  const modelConfigured = Boolean(model);
  const configured = credentialConfigured && modelConfigured && requirement.supported_by_adapter;
  const missing = [
    ...(credentialConfigured ? [] : requirement.required_any),
    ...(modelConfigured || !requirement.required_model ? [] : [requirement.required_model]),
  ];

  return {
    provider,
    model,
    status: configured ? "configured" : "not_configured",
    configured,
    supported_by_adapter: requirement.supported_by_adapter,
    required_any: requirement.required_any,
    required_model: requirement.required_model,
    optional: requirement.optional,
    missing_environment: missing,
    credential_configured: credentialConfigured,
    credential_source: credentialSource || "",
    model_configured: modelConfigured,
    provider_ready: configured,
    safe_environment: {
      provider,
      credential_configured: credentialConfigured,
      credential_source: credentialSource || "",
      model_configured: modelConfigured,
      model,
      base_url_configured: Boolean(env.OPENAI_BASE_URL || env.D4J_OPENAI_BASE_URL),
    },
    message:
      configured
        ? "Provider credential and model are available to the backend process."
        : requirement.supported_by_adapter && !credentialConfigured
          ? `Set one of ${requirement.required_any.join(" or ")} in the backend environment.`
          : requirement.supported_by_adapter && !modelConfigured
            ? `Set ${requirement.required_model} in the backend environment.`
          : "This phase only executes the OpenAI-backed mini-swe-agent profile.",
  };
}

export function buildProviderEnvironment(profile, env = process.env) {
  const providerConfig = resolveProviderConfig(profile, env);
  const nextEnv = { ...env };
  if (providerConfig.provider === "openai") {
    if (nextEnv.D4J_OPENAI_API_KEY) {
      nextEnv.D4J_OPENAI_API_KEY = String(nextEnv.D4J_OPENAI_API_KEY).trim();
    }
    if (nextEnv.OPENAI_API_KEY) {
      nextEnv.OPENAI_API_KEY = String(nextEnv.OPENAI_API_KEY).trim();
    }
    if (!nextEnv.OPENAI_API_KEY && nextEnv.D4J_OPENAI_API_KEY) {
      nextEnv.OPENAI_API_KEY = nextEnv.D4J_OPENAI_API_KEY;
    }
    if (nextEnv.D4J_OPENAI_BASE_URL) {
      nextEnv.D4J_OPENAI_BASE_URL = String(nextEnv.D4J_OPENAI_BASE_URL).trim();
    }
    if (nextEnv.OPENAI_BASE_URL) {
      nextEnv.OPENAI_BASE_URL = String(nextEnv.OPENAI_BASE_URL).trim();
    }
    if (!nextEnv.OPENAI_BASE_URL && nextEnv.D4J_OPENAI_BASE_URL) {
      nextEnv.OPENAI_BASE_URL = nextEnv.D4J_OPENAI_BASE_URL;
    }
  }
  return { env: nextEnv, providerConfig };
}
