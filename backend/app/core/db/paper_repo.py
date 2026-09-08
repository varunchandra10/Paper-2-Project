import os
import re
import json
import datetime
from typing import Optional, Dict, Any
from app.core.config import settings
from app.core.db.storage_engine import StorageEngine


class PaperRepository:
    """Repository managing paper titles, extraction lookups, and MD5 deduplication."""

    def __init__(self, storage: StorageEngine):
        self.storage = storage

    def get_paper_title_by_id_or_name(self, paper_id: Optional[str] = None, filename: Optional[str] = None) -> Optional[str]:
        """Looks up the extracted research paper title from storage/extracted_json/."""
        candidate_ids = []
        if paper_id:
            candidate_ids.append(paper_id)
            if paper_id.startswith("paper_"):
                candidate_ids.append(paper_id[6:])
            else:
                candidate_ids.append(f"paper_{paper_id}")
            slug = re.sub(r'[^a-zA-Z0-9]', '', paper_id).lower()
            candidate_ids.extend([f"paper_{slug}", slug])

        if filename:
            base = os.path.splitext(filename)[0]
            candidate_ids.extend([filename, base, f"paper_{base}"])
            clean_slug = re.sub(r'[^a-zA-Z0-9]', '', base).lower()
            candidate_ids.extend([f"paper_{clean_slug}", clean_slug])

        for cid in candidate_ids:
            json_path = os.path.join(settings.EXTRACTED_JSON_DIR, f"{cid}.json")
            if os.path.exists(json_path):
                try:
                    with open(json_path, "r", encoding="utf-8") as jf:
                        data = json.load(jf)
                        meta = data.get("metadata", {})
                        title = meta.get("title")
                        if title and isinstance(title, str) and title.strip():
                            stripped = title.strip()
                            if stripped != filename and not stripped.lower().endswith(('.pdf', '.docx')):
                                return stripped
                except Exception:
                    pass
        return None

    def get_paper_by_hash(self, file_hash: str) -> Optional[dict]:
        """Checks if a paper with this MD5 content hash has already been ingested.
        Returns paper info if found and the underlying files still exist on disk, else None.
        """
        if not file_hash:
            return None
        data = self.storage.load_index()
        paper_hashes = data.get("paper_hashes", {})
        info = paper_hashes.get(file_hash)
        if info:
            paper_id = info.get("paper_id")
            dest_pdf = os.path.join(settings.PAPERS_DIR, f"{paper_id}.pdf")
            dest_docx = os.path.join(settings.PAPERS_DIR, f"{paper_id}.docx")
            if os.path.exists(dest_pdf) or os.path.exists(dest_docx):
                return info
            else:
                # Stale hash entry (underlying file removed from disk)
                del paper_hashes[file_hash]
                data["paper_hashes"] = paper_hashes
                self.storage.save_index(data)

        # Fallback: scan extracted_json files for stored file_hash
        if os.path.exists(settings.EXTRACTED_JSON_DIR):
            for fname in os.listdir(settings.EXTRACTED_JSON_DIR):
                if fname.endswith(".json"):
                    fpath = os.path.join(settings.EXTRACTED_JSON_DIR, fname)
                    try:
                        with open(fpath, "r", encoding="utf-8") as jf:
                            doc = json.load(jf)
                            if doc.get("file_hash") == file_hash:
                                pid = doc.get("paper_id") or os.path.splitext(fname)[0]
                                meta = doc.get("metadata", {})
                                title = meta.get("title") or pid
                                self.save_paper_hash(file_hash, pid, f"{pid}.pdf", title)
                                return {
                                    "paper_id": pid,
                                    "filename": f"{pid}.pdf",
                                    "title": title
                                }
                    except Exception:
                        pass
        return None

    def save_paper_hash(
        self,
        file_hash: str,
        paper_id: str,
        filename: str,
        title: str,
        conversation_id: Optional[str] = None
    ):
        """Indexes an MD5 paper file hash for fast deduplication."""
        if not file_hash or not paper_id:
            return
        data = self.storage.load_index()
        if "paper_hashes" not in data:
            data["paper_hashes"] = {}
        data["paper_hashes"][file_hash] = {
            "paper_id": paper_id,
            "filename": filename,
            "title": title,
            "conversation_id": conversation_id,
            "created_at": datetime.datetime.now().isoformat()
        }
        self.storage.save_index(data)

    def delete_paper_hash(self, paper_id: str):
        """Removes paper hash entry when paper is deleted."""
        if not paper_id:
            return
        data = self.storage.load_index()
        paper_hashes = data.get("paper_hashes", {})
        to_delete = [
            h for h, info in paper_hashes.items()
            if info.get("paper_id") == paper_id or info.get("paper_id") == f"paper_{paper_id}"
        ]
        if to_delete:
            for h in to_delete:
                del paper_hashes[h]
            data["paper_hashes"] = paper_hashes
            self.storage.save_index(data)
