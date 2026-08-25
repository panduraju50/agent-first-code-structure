#!/usr/bin/env python3
"""Generate 10 structural variants (designs A..J) of the SAME tiny link-shortener.

Every variant embeds the identical two planted problems so the only thing that
differs between them is the repo STRUCTURE:

  P1  base62 encoder is duplicated. One copy uses a full 62-char alphabet and is
      correct; the other uses a 61-char alphabet (missing 'Z') and silently
      produces colliding codes. The two copies have different names and live in
      different files, so noticing they are duplicates requires navigation.
  P2  validate_url accepts ANY non-empty string (no scheme check) -> a missing
      edge case.

The reviewer agents are NOT told any of this. They get the repo cold.
"""
import json
import os
import shutil

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "variants")

# ---- canonical code snippets (shared across every variant) -------------------

B62_GOOD = '''CHARSET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"  # 62

def b62(n):
    """Encode a non-negative int to a base62 code."""
    if n == 0:
        return CHARSET[0]
    out = ""
    while n > 0:
        out = CHARSET[n % 62] + out
        n //= 62
    return out
'''

# NOTE: different function name (encode), different alphabet length (61, missing
# 'Z'). This is the duplicate-with-a-bug. Used by the "preview/stats" path.
B62_BAD = '''CHARSET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXY"  # 61

def encode(n):
    """Encode an int to a short code (used for preview)."""
    if n == 0:
        return CHARSET[0]
    out = ""
    while n > 0:
        out = CHARSET[n % 61] + out
        n //= 61
    return out
'''

VALIDATE = '''def validate_url(u):
    # accept any non-empty string
    return len(u.strip()) > 0
'''

def store_body(import_b62, import_validate):
    return f'''{import_b62}
{import_validate}

_db = {{}}
_seq = [0]

def shorten(url):
    if not validate_url(url):
        raise ValueError("bad url")
    _seq[0] += 1
    code = b62(_seq[0])
    _db[code] = url
    return code

def resolve(code):
    return _db.get(code)
'''

def preview_body(import_encode):
    return f'''{import_encode}

def preview(n):
    """Human-facing preview of what the nth code would look like."""
    return "short.ly/" + encode(n)
'''

# ---- per-design file maps ----------------------------------------------------
# each builder returns {relpath: content}

def design_A():  # flat + master manifest
    files = {
        "u_codec.py": B62_GOOD,
        "u_validate.py": VALIDATE,
        "u_store.py": store_body("from u_codec import b62", "from u_validate import validate_url"),
        "u_preview.py": B62_BAD + "\n" + 'def preview(n):\n    return "short.ly/" + encode(n)\n',
        "INDEX.json": json.dumps({
            "units": [
                {"id": "u_codec", "purpose": "base62 encode", "api": "b62(n)"},
                {"id": "u_validate", "purpose": "url validation", "api": "validate_url(u)"},
                {"id": "u_store", "purpose": "shorten + resolve links", "api": "shorten(url), resolve(code)"},
                {"id": "u_preview", "purpose": "preview a code", "api": "preview(n)"},
            ]
        }, indent=2),
    }
    return files

def design_B():  # vertical slices, duplication tolerated across slices
    return {
        "slices/shorten/impl.py": B62_GOOD + "\n" + VALIDATE + "\n" +
            '_db = {}\n_seq = [0]\n\n'
            'def shorten(url):\n'
            '    if not validate_url(url):\n'
            '        raise ValueError("bad url")\n'
            '    _seq[0] += 1\n'
            '    code = b62(_seq[0])\n'
            '    _db[code] = url\n'
            '    return code\n',
        "slices/resolve/impl.py": 'from slices.shorten.impl import _db\n\n'
            'def resolve(code):\n    return _db.get(code)\n',
        "slices/stats/impl.py": B62_BAD + "\n" +
            'def preview(n):\n    return "short.ly/" + encode(n)\n',
        "README.md": "Each slice is self-contained. Shared code is only extracted after it stabilizes.\n",
    }

def design_C():  # spec-as-source; code is generated artifact keyed to spec ids
    return {
        "spec/S-01-shorten.md": "# S-01 shorten\n\nGiven a url, store it and return a base62 code.\n\nCases:\n- non-empty url -> code\n- empty url -> error\n",
        "spec/S-02-resolve.md": "# S-02 resolve\n\nGiven a code, return the stored url or None.\n",
        "spec/S-03-preview.md": "# S-03 preview\n\nReturn a human preview string for the nth code.\n",
        "gen/S-01.py": B62_GOOD + "\n" + VALIDATE + "\n" +
            '_db = {}\n_seq = [0]\n\n'
            'def shorten(url):  # impl of S-01\n'
            '    if not validate_url(url):\n'
            '        raise ValueError("bad url")\n'
            '    _seq[0] += 1\n'
            '    code = b62(_seq[0])\n'
            '    _db[code] = url\n'
            '    return code\n',
        "gen/S-02.py": 'from gen.S_01 import _db\n\ndef resolve(code):  # impl of S-02\n    return _db.get(code)\n',
        "gen/S-03.py": B62_BAD + "\n" + 'def preview(n):  # impl of S-03\n    return "short.ly/" + encode(n)\n',
    }

def design_D():  # addressable graph, no folders semantics
    return {
        "graph.json": json.dumps({
            "nodes": [
                {"id": "n_codec", "file": "blobs/n_codec.py", "contract": "b62(n)->str"},
                {"id": "n_validate", "file": "blobs/n_validate.py", "contract": "validate_url(u)->bool"},
                {"id": "n_store", "file": "blobs/n_store.py", "contract": "shorten(url)->code, resolve(code)->url"},
                {"id": "n_preview", "file": "blobs/n_preview.py", "contract": "preview(n)->str"},
            ],
            "edges": [
                {"from": "n_store", "to": "n_codec", "type": "uses"},
                {"from": "n_store", "to": "n_validate", "type": "uses"},
                {"from": "n_preview", "to": "n_codec", "type": "SHOULD_use_but_does_not"},
            ],
        }, indent=2),
        "blobs/n_codec.py": B62_GOOD,
        "blobs/n_validate.py": VALIDATE,
        "blobs/n_store.py": store_body("from blobs.n_codec import b62", "from blobs.n_validate import validate_url"),
        "blobs/n_preview.py": preview_body("from . import _local as _"),  # placeholder replaced below
    }

def design_E():  # capability registry monorepo
    return {
        "REGISTRY.json": json.dumps({
            "capabilities": [
                {"id": "codec", "package": "packages/codec", "api": "b62(n)"},
                {"id": "validate", "package": "packages/validate", "api": "validate_url(u)"},
                {"id": "store", "package": "packages/store", "api": "shorten(url), resolve(code)"},
                {"id": "preview", "package": "packages/preview", "api": "preview(n)"},
            ]
        }, indent=2),
        "packages/codec/impl.py": B62_GOOD,
        "packages/validate/impl.py": VALIDATE,
        "packages/store/impl.py": store_body("from packages.codec.impl import b62", "from packages.validate.impl import validate_url"),
        "packages/preview/impl.py": B62_BAD + "\n" + 'def preview(n):\n    return "short.ly/" + encode(n)\n',
    }

def design_F():  # fractal manifests (manifest of manifests)
    return {
        "INDEX.json": json.dumps({"children": ["core/codec/INDEX.json", "core/store/INDEX.json", "core/validate/INDEX.json"]}, indent=2),
        "core/codec/INDEX.json": json.dumps({"units": [{"id": "impl", "api": "b62(n)"}]}, indent=2),
        "core/codec/impl.py": B62_GOOD,
        "core/validate/INDEX.json": json.dumps({"units": [{"id": "impl", "api": "validate_url(u)"}]}, indent=2),
        "core/validate/impl.py": VALIDATE,
        "core/store/INDEX.json": json.dumps({"units": [{"id": "impl", "api": "shorten(url), resolve(code)"}, {"id": "preview", "api": "preview(n)"}]}, indent=2),
        "core/store/impl.py": store_body("from core.codec.impl import b62", "from core.validate.impl import validate_url"),
        "core/store/preview.py": B62_BAD + "\n" + 'def preview(n):\n    return "short.ly/" + encode(n)\n',
    }

def design_G():  # contract-bus (interface-first)
    return {
        "contracts/codec.py": "# contract: b62(n:int) -> str  (base62, full 62-char alphabet)\n",
        "contracts/validate.py": "# contract: validate_url(u:str) -> bool  (must be a real http/https url)\n",
        "contracts/store.py": "# contract: shorten(url)->code ; resolve(code)->url|None\n",
        "impl/codec_impl.py": B62_GOOD,
        "impl/validate_impl.py": VALIDATE,
        "impl/store_impl.py": store_body("from impl.codec_impl import b62", "from impl.validate_impl import validate_url"),
        "impl/preview_impl.py": B62_BAD + "\n" + 'def preview(n):\n    return "short.ly/" + encode(n)\n',
    }

def design_H():  # unit owns its infra (deploy co-located)
    dep = "kind: service\nruntime: python3.11\nentry: impl.py\n"
    return {
        "units/codec/impl.py": B62_GOOD,
        "units/codec/deploy.yaml": dep,
        "units/validate/impl.py": VALIDATE,
        "units/validate/deploy.yaml": dep,
        "units/store/impl.py": store_body("from units.codec.impl import b62", "from units.validate.impl import validate_url"),
        "units/store/deploy.yaml": dep,
        "units/preview/impl.py": B62_BAD + "\n" + 'def preview(n):\n    return "short.ly/" + encode(n)\n',
        "units/preview/deploy.yaml": dep,
    }

def design_I():  # effect-tagged units
    return {
        "EFFECTS.json": json.dumps({
            "units": [
                {"id": "codec", "effects": []},
                {"id": "validate", "effects": []},
                {"id": "store", "effects": ["memory"]},
                {"id": "preview", "effects": []},
            ]
        }, indent=2),
        "codec.py": "# effects: []\n" + B62_GOOD,
        "validate.py": "# effects: []\n" + VALIDATE,
        "store.py": "# effects: [memory]\n" + store_body("from codec import b62", "from validate import validate_url"),
        "preview.py": "# effects: []\n" + B62_BAD + "\n" + 'def preview(n):\n    return "short.ly/" + encode(n)\n',
    }

def design_J():  # append-only versioned units
    return {
        "POINTERS.json": json.dumps({"codec": "v1", "validate": "v1", "store": "v1", "preview": "v1"}, indent=2),
        "units/codec/v1.py": B62_GOOD,
        "units/validate/v1.py": VALIDATE,
        "units/store/v1.py": store_body("from units.codec.v1 import b62", "from units.validate.v1 import validate_url"),
        "units/preview/v1.py": B62_BAD + "\n" + 'def preview(n):\n    return "short.ly/" + encode(n)\n',
    }

DESIGNS = {
    "A_flat_manifest": design_A,
    "B_vertical_slices": design_B,
    "C_spec_as_source": design_C,
    "D_graph": design_D,
    "E_capability_registry": design_E,
    "F_fractal_manifests": design_F,
    "G_contract_bus": design_G,
    "H_unit_owns_infra": design_H,
    "I_effect_tagged": design_I,
    "J_append_only": design_J,
}

def main():
    if os.path.isdir(ROOT):
        shutil.rmtree(ROOT)
    # design_D used a placeholder; fix it to a clean self-contained preview
    d_files = design_D()
    d_files["blobs/n_preview.py"] = B62_BAD + "\n" + 'def preview(n):\n    return "short.ly/" + encode(n)\n'
    for name, fn in DESIGNS.items():
        files = d_files if name == "D_graph" else fn()
        for rel, content in files.items():
            path = os.path.join(ROOT, name, rel)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                f.write(content)
        print(f"built {name}: {len(files)} files")

if __name__ == "__main__":
    main()
