import type {
  BatchGenerateResponse,
  FaultLocalizationRun,
  VariantArtifactText,
  VariantDetail,
  VariantLibraryResponse,
  VariantValidationResponse,
} from "./types";

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { error?: string } | null;
    throw new Error(body?.error ?? `${response.status} ${response.statusText}`);
  }
  return (await response.json()) as T;
}

export async function getVariantLibrary(): Promise<VariantLibraryResponse> {
  return fetchJson<VariantLibraryResponse>("/api/variants");
}

export async function getVariantDetail(variantId: string): Promise<VariantDetail> {
  return fetchJson<VariantDetail>(`/api/variants/${encodeURIComponent(variantId)}`);
}

export async function getVariantReasoningTree(variantId: string): Promise<VariantArtifactText> {
  return fetchJson<VariantArtifactText>(`/api/variants/${encodeURIComponent(variantId)}/reasoning-tree`);
}

export async function getVariantDiff(variantId: string): Promise<VariantArtifactText> {
  return fetchJson<VariantArtifactText>(`/api/variants/${encodeURIComponent(variantId)}/diff`);
}

export async function getVariantTest(variantId: string): Promise<VariantArtifactText> {
  return fetchJson<VariantArtifactText>(`/api/variants/${encodeURIComponent(variantId)}/test`);
}

export async function getVariantValidation(variantId: string): Promise<VariantValidationResponse> {
  return fetchJson<VariantValidationResponse>(`/api/variants/${encodeURIComponent(variantId)}/validation`);
}

export async function runFaultLocalization(variantId: string): Promise<FaultLocalizationRun> {
  return fetchJson<FaultLocalizationRun>(`/api/variants/${encodeURIComponent(variantId)}/fault-localization/run`, {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export async function getFaultLocalizationRuns(variantId: string): Promise<FaultLocalizationRun[]> {
  return fetchJson<FaultLocalizationRun[]>(
    `/api/variants/${encodeURIComponent(variantId)}/fault-localization/runs`,
  );
}

export async function generateMissingL10Variants(): Promise<BatchGenerateResponse> {
  return fetchJson<BatchGenerateResponse>("/api/variants/generate-missing-l10", {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export async function generateProjectL10Variant(project: string): Promise<BatchGenerateResponse["results"][number]> {
  return fetchJson<BatchGenerateResponse["results"][number]>(
    `/api/bugs/${encodeURIComponent(project)}/1/generate-variant`,
    {
      method: "POST",
      body: JSON.stringify({}),
    },
  );
}
