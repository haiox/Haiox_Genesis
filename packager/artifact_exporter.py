"""
Haiox Genesis - Artifact Packager, Archiver & SHA-256 Provenance Engine
Module: packager/artifact_exporter.py
Architect: AIrash (Staff Systems Engineer) for Hatef Ghanei (haiox)
"""

import hashlib
import json
import os
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any

from core.schemas import ExportArtifactResult
from core.workspace import VirtualWorkspace


class ArtifactExporter:
    """
    Packages validated multi-file projects into clean, production-grade zip archives,
    excluding volatile cache files and calculating SHA-256 cryptographic provenance manifests.
    """

    EXCLUDED_PATTERNS = {
        "__pycache__",
        ".pytest_cache",
        ".git",
        ".venv",
        "venv",
        ".DS_Store",
        "Thumbs.db",
        ".coverage"
    }

    def export_project_archive(
        self,
        workspace: VirtualWorkspace,
        output_dir: Optional[str] = None,
        archive_name: Optional[str] = None
    ) -> ExportArtifactResult:
        """
        Compresses workspace files into a zip archive and generates SHA-256 cryptographic provenance.
        """
        workspace.persist_to_disk()

        # Determine target directory
        out_path = Path(output_dir) if output_dir else (workspace.root_dir / "dist")
        out_path.mkdir(parents=True, exist_ok=True)

        zip_base_name = archive_name or f"{workspace.root_dir.name}_release"
        if not zip_base_name.endswith(".zip"):
            zip_filename = f"{zip_base_name}.zip"
        else:
            zip_filename = zip_base_name

        zip_filepath = out_path / zip_filename
        manifest_filepath = out_path / f"{zip_filename}.manifest.json"
        sums_filepath = out_path / "SHA256SUMS"

        file_manifests: List[Dict[str, Any]] = []
        total_uncompressed_bytes = 0

        # Build clean zip archive
        with zipfile.ZipFile(zip_filepath, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for rel_path, pfile in sorted(workspace.files.items()):
                # Exclude blacklisted paths
                if self._is_excluded(rel_path):
                    continue

                abs_file = workspace.root_dir / rel_path
                if not abs_file.is_file():
                    continue

                content_bytes = abs_file.read_bytes()
                file_sha = hashlib.sha256(content_bytes).hexdigest()
                file_size = len(content_bytes)

                total_uncompressed_bytes += file_size
                file_manifests.append({
                    "path": rel_path,
                    "size_bytes": file_size,
                    "sha256": file_sha
                })

                zip_file.write(abs_file, arcname=rel_path)

        # Calculate archive SHA-256
        archive_bytes = zip_filepath.stat().st_size
        archive_sha256 = self._calculate_file_sha256(zip_filepath)

        timestamp_iso = datetime.utcnow().isoformat() + "Z"

        # Construct and persist manifest
        manifest_data = {
            "archive_filename": zip_filename,
            "sha256_hash": archive_sha256,
            "total_files": len(file_manifests),
            "total_uncompressed_bytes": total_uncompressed_bytes,
            "archive_bytes": archive_bytes,
            "compression_ratio": round(archive_bytes / max(total_uncompressed_bytes, 1), 4),
            "timestamp_iso": timestamp_iso,
            "files": file_manifests
        }
        manifest_filepath.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")

        # Write SHA256SUMS file
        sums_line = f"{archive_sha256}  {zip_filename}\n"
        sums_filepath.write_text(sums_line, encoding="utf-8")

        return ExportArtifactResult(
            archive_path=str(zip_filepath),
            manifest_path=str(manifest_filepath),
            sha256_hash=archive_sha256,
            total_files=len(file_manifests),
            total_uncompressed_bytes=total_uncompressed_bytes,
            archive_bytes=archive_bytes,
            timestamp_iso=timestamp_iso
        )

    def _is_excluded(self, path_str: str) -> bool:
        """Checks if file path matches any excluded directory or file patterns."""
        parts = Path(path_str).parts
        for part in parts:
            if part in self.EXCLUDED_PATTERNS or part.endswith(".pyc"):
                return True
        return False

    def _calculate_file_sha256(self, file_path: Path) -> str:
        """Calculates standard SHA-256 digest of a physical file."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
