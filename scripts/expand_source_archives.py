#!/usr/bin/env python3
"""Safely expand preserved KAFKA III source archives without modifying originals.

The script is intentionally idempotent: an existing extracted file is accepted
only when its SHA-256 matches the archive member. Conflicts fail closed.
No simulation, statistical analysis, or scientific test is executed here.
"""
from __future__ import annotations

import hashlib
import json
import os
import stat
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
MAX_MEMBER_BYTES = 50 * 1024 * 1024
MAX_ARCHIVE_BYTES = 100 * 1024 * 1024

ARCHIVES = [
    ("v0.4/PACOTE_KAFKA_III_V0_4_PERDAS_E_ATRASOS.zip", "v0.4/source"),
    ("v0.5C/PACOTE_KAFKA_III_V0_5C_POLITICA_E_PERDAS.zip", "v0.5C/source"),
    ("v1.7/PACOTE_KAFKA_III_V1_7_AUDITORIA_L1_L3.zip", "v1.7/source"),
    ("v1.8A/PACOTE_KAFKA_III_V1_8A_MAPA_GANHOS_PERDAS_CINZENTO.zip", "v1.8A/source"),
    ("v1.9D/KAFKA_III_V1_9D_PACOTE_COMPLETO.zip", "v1.9D/source"),
    ("v1.9F/KAFKA_III_V1_9F_ETAPA1_AUDITORIA (1).zip", "v1.9F/source"),
    ("archive/source_archives/PACOTE_REPRODUZIVEL_KAFKA_v0_2.zip",
     "archive/source_archives/PACOTE_REPRODUZIVEL_KAFKA_v0_2"),
    ("archive/recovery/PACOTE_CLAUDE_COMPLETO_V0_2_COM_RECUPERACAO_V0_3.zip",
     "archive/recovery/package_contents"),
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalized_member(info: zipfile.ZipInfo) -> PurePosixPath | None:
    name = info.filename
    if not name or "\\" in name:
        raise ValueError(f"Unsafe ZIP member name: {name!r}")
    path = PurePosixPath(name)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        raise ValueError(f"Unsafe ZIP member path: {name!r}")
    mode = (info.external_attr >> 16) & 0xFFFF
    if stat.S_ISLNK(mode):
        raise ValueError(f"Symbolic link not allowed in ZIP: {name!r}")
    if info.flag_bits & 0x1:
        raise ValueError(f"Encrypted ZIP member is not supported: {name!r}")
    return None if name.endswith("/") else path


def common_root_prefix(paths: list[PurePosixPath]) -> str | None:
    if not paths:
        return None
    first_parts = paths[0].parts
    if not first_parts:
        return None
    candidate = first_parts[0]
    if all(len(path.parts) >= 2 and path.parts[0] == candidate for path in paths):
        return candidate
    return None


def extract_archive(archive_rel: str, destination_rel: str) -> list[dict]:
    archive_path = ROOT / archive_rel
    destination = ROOT / destination_rel
    if not archive_path.is_file():
        raise FileNotFoundError(f"Expected source archive is missing: {archive_rel}")
    archive_size = archive_path.stat().st_size
    if archive_size > MAX_ARCHIVE_BYTES:
        raise ValueError(f"Archive exceeds configured limit: {archive_rel}")

    archive_hash = sha256_file(archive_path)
    destination.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(archive_path, "r") as zf:
        bad_member = zf.testzip()
        if bad_member is not None:
            raise ValueError(f"ZIP CRC failure in {archive_rel}: {bad_member}")

        file_infos = []
        total_uncompressed = 0
        for info in zf.infolist():
            member = normalized_member(info)
            if member is None:
                continue
            if info.file_size > MAX_MEMBER_BYTES:
                raise ValueError(f"ZIP member too large: {archive_rel}:{info.filename}")
            total_uncompressed += info.file_size
            if total_uncompressed > MAX_ARCHIVE_BYTES:
                raise ValueError(f"Uncompressed archive exceeds configured limit: {archive_rel}")
            file_infos.append((info, member))

        strip_prefix = common_root_prefix([member for _, member in file_infos])
        seen: set[str] = set()
        manifest_members: list[dict] = []

        for info, member in file_infos:
            parts = member.parts[1:] if strip_prefix else member.parts
            if not parts:
                raise ValueError(f"ZIP member resolves to empty path: {info.filename}")
            relative = PurePosixPath(*parts)
            relative_text = relative.as_posix()
            if relative_text in seen:
                raise ValueError(f"Duplicate normalized ZIP member: {relative_text}")
            seen.add(relative_text)

            target = destination.joinpath(*relative.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            resolved = target.resolve()
            if destination.resolve() not in resolved.parents:
                raise ValueError(f"ZIP member escapes destination: {info.filename}")

            data = zf.read(info)
            member_hash = sha256_bytes(data)
            if target.exists():
                if not target.is_file() or sha256_file(target) != member_hash:
                    raise FileExistsError(
                        f"Refusing to overwrite conflicting extracted file: {target.relative_to(ROOT)}"
                    )
            else:
                target.write_bytes(data)

            manifest_members.append({
                "archive_path": info.filename,
                "extracted_path": (Path(destination_rel) / Path(*relative.parts)).as_posix(),
                "size_bytes": len(data),
                "sha256": member_hash,
            })

    manifest = {
        "archive": archive_rel,
        "archive_size_bytes": archive_size,
        "archive_sha256": archive_hash,
        "destination": destination_rel,
        "stripped_common_root": strip_prefix,
        "integrity_test": "zipfile.testzip passed",
        "extraction_only": True,
        "scientific_code_executed": False,
        "members": manifest_members,
    }
    manifest_path = destination / "EXTRACTION_MANIFEST.json"
    rendered = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    if manifest_path.exists() and manifest_path.read_text(encoding="utf-8") != rendered:
        # Reproducible output only; changing archive bytes must be reviewed separately.
        raise FileExistsError(f"Extraction manifest conflict: {manifest_path.relative_to(ROOT)}")
    manifest_path.write_text(rendered, encoding="utf-8")
    print(f"EXTRACTED {archive_rel}: {len(manifest_members)} files -> {destination_rel}")
    return manifest_members


def write_copy(source_rel: str, destination_rel: str) -> None:
    source = ROOT / source_rel
    destination = ROOT / destination_rel
    if not source.is_file():
        raise FileNotFoundError(f"Expected dependency source is missing: {source_rel}")
    data = source.read_bytes()
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if not destination.is_file() or sha256_file(destination) != sha256_bytes(data):
            raise FileExistsError(f"Refusing to overwrite conflicting file: {destination_rel}")
    else:
        destination.write_bytes(data)


def write_text_if_absent(path_rel: str, text: str) -> None:
    path = ROOT / path_rel
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_text(encoding="utf-8") != text:
            raise FileExistsError(f"Refusing to overwrite existing file: {path_rel}")
    else:
        path.write_text(text, encoding="utf-8", newline="\n")


def build_repo_manifest() -> None:
    manifest_path = ROOT / "MANIFEST_SHA256_REPO.txt"
    entries = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or path == manifest_path:
            continue
        if ".git" in path.parts:
            continue
        rel = path.relative_to(ROOT).as_posix()
        entries.append(f"{sha256_file(path)}  {rel}")
    header = (
        "# KAFKA III repository SHA-256 manifest\n"
        "# Generated by scripts/expand_source_archives.py.\n"
        "# The manifest intentionally excludes itself (self-hashing is not defined).\n"
        "# Includes tracked source archives, extracted archive members, documentation, and figures.\n\n"
    )
    rendered = header + "\n".join(entries) + "\n"
    manifest_path.write_text(rendered, encoding="utf-8", newline="\n")
    print(f"MANIFEST: {len(entries)} files recorded")


def main() -> None:
    for archive_rel, destination_rel in ARCHIVES:
        extract_archive(archive_rel, destination_rel)

    # Make the v1.9E evidence gap explicit while preserving the exact source snapshots.
    write_copy(
        "v1.9D/source/PROTOCOLO_CANDIDATO_V1_9E.md",
        "v1.9E/PROTOCOLO_CANDIDATO_V1_9E.md",
    )
    write_copy(
        "v1.9F/source/kafka_iii_v1_9e/experiment_v1_9e.py",
        "v1.9E/dependency_snapshot/experiment_v1_9e.py",
    )
    write_text_if_absent(
        "v1.9E/dependency_snapshot/README.md",
        "# v1.9E dependency snapshot\n\n"
        "The Python file in this directory is the dependency snapshot distributed "
        "inside the v1.9F baseline-equivalence audit archive. It is retained with "
        "its source provenance and is not the complete v1.9E experiment package. "
        "The candidate protocol is copied from the v1.9D package. The original "
        "v1.9E source, results, run logs, and package manifest remain outstanding.\n",
    )

    build_repo_manifest()


if __name__ == "__main__":
    main()
