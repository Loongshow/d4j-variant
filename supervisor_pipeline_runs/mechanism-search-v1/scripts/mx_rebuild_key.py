"""Rebuild review/VARIANT_KEY.json from validated, packaged instance specs.

Re-hosted instances require reproduced=true; new builds require overall=READY;
derived revisions require status=READY and inherit their parent's key fields,
with explicit spec fields taking precedence. Resolve the complete key before
atomically replacing it, so invalid inputs or interrupted writes leave it intact.
Run after builders finish; atomic replacement does not make their inputs a snapshot.
Usage: python3 scripts/mx_rebuild_key.py (root inferred from this script).
"""
import json
import os
import tempfile
from pathlib import Path


def read_json(path):
    with path.open() as stream:
        return json.load(stream)


def methods(value):
    if isinstance(value, dict):
        value = [value]
    if not isinstance(value, list):
        raise ValueError("method locations must be a list or a class/method object")
    return [item if isinstance(item, str) else f"{item['class']}::{item['method']}" for item in value]


def build_key(root):
    specs, variants = {}, {}
    for path in sorted((root / "instances").glob("*/spec.json")):
        spec = read_json(path)
        variant = spec.get("variant_id")
        if not variant:
            continue
        iid, project, kind = spec["iid"], spec["project"], spec.get("kind")
        directory = root / "new_bug_variants" / project / "bug-1/L20" / variant
        if not directory.is_dir():
            continue
        if kind == "rehosted":
            ready = read_json(path.parent / "reproduction.json").get("reproduced") is True
        elif kind in ("new", "derived"):
            field = "status" if kind == "derived" else "overall"
            ready = read_json(path.parent / "validation.json").get(field) == "READY"
        else:
            raise ValueError(f"{iid}: unsupported instance kind {kind!r}")
        if not ready:
            continue
        if iid in specs or variant in variants:
            raise ValueError(f"duplicate instance or variant: {iid}, {variant}")
        specs[iid] = (spec, directory)
        variants[variant] = iid

    key, resolving = {}, set()

    def resolve(iid):
        if iid not in specs:
            raise ValueError(f"unresolved validated parent instance: {iid}")
        spec, directory = specs[iid]
        variant = spec["variant_id"]
        if variant in key:
            return key[variant]
        if iid in resolving:
            raise ValueError(f"cyclic derived parent: {iid}")
        resolving.add(iid)
        if spec["kind"] == "derived":
            parent_iid = spec["parent_iid"]
            entry = dict(resolve(parent_iid))
            if specs[parent_iid][0]["variant_id"] != spec["parent_variant"]:
                raise ValueError(f"{iid}: parent_iid and parent_variant disagree")
        else:
            entry = {"group": None, "mechanism": None, "tags": None, "tier": None,
                     "decoys": [], "entry_points": [], "fault_lines": [], "evidence": [],
                     "expected_signature": None}
        for field in ("group", "mechanism", "tags", "tier", "gold", "decoys",
                      "entry_points", "fault_lines", "evidence", "expected_signature", "trigger"):
            if field in spec:
                entry[field] = spec[field]
        entry["gold"] = methods(entry["gold"])
        entry["decoys"] = methods(entry["decoys"])
        trigger = entry["trigger"]
        if not isinstance(trigger, str):
            entry["trigger"] = f"{trigger['test_class']}::{trigger['test_method']}"
        hashes = read_json(directory / "variant_manifest.json")["artifact_hashes"]
        entry.update({"instance_id": iid, "project": spec["project"],
                      "fresh": str(root / "construction/fresh" / spec["project"]),
                      "variant_patch_sha256": hashes["variant.patch"],
                      "test_patch_sha256": hashes["test.patch"]})
        key[variant] = entry
        resolving.remove(iid)
        return entry

    for iid in specs:
        resolve(iid)
    return key


def write_key(path, key):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, prefix=f".{path.name}.",
                                         suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(key, stream, indent=1, sort_keys=True)
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def main():
    root = Path(__file__).resolve().parents[1]
    key = build_key(root)
    write_key(root / "review/VARIANT_KEY.json", key)
    print(len(key), "variants in key:", sorted((entry["instance_id"], variant) for variant, entry in key.items()))


if __name__ == "__main__":
    main()
