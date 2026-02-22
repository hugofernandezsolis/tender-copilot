"""Utilidades para acceder y descargar licitaciones del Gobierno de Canarias.

Este módulo evita dependencias externas y usa únicamente librerías estándar.
"""

from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
import json
import re

DEFAULT_PROFILE_URL = "https://www.gobiernodecanarias.org/hacienda/contratacion/perfil_contratante/"


@dataclass(slots=True)
class TenderDocument:
    """Representa un documento descargable asociado a una licitación."""

    title: str
    url: str


class _AnchorCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._current_href: str | None = None
        self._current_text: list[str] = []
        self.anchors: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        attr_map = dict(attrs)
        href = attr_map.get("href")
        if not href:
            return
        self._current_href = href.strip()
        self._current_text = []

    def handle_data(self, data: str) -> None:
        if self._current_href is None:
            return
        text = data.strip()
        if text:
            self._current_text.append(text)

    def handle_endtag(self, tag: str) -> None:
        if tag != "a" or self._current_href is None:
            return
        text = " ".join(self._current_text).strip()
        self.anchors.append((self._current_href, text))
        self._current_href = None
        self._current_text = []


class CanariasTenderDownloader:
    """Cliente mínimo para extraer y descargar documentos de licitaciones."""

    def __init__(self, user_agent: str = "tender-copilot/1.0") -> None:
        self.user_agent = user_agent

    def fetch_html(self, url: str) -> str:
        req = Request(url, headers={"User-Agent": self.user_agent})
        with urlopen(req, timeout=30) as resp:  # noqa: S310
            return resp.read().decode("utf-8", errors="replace")

    def extract_documents(self, html: str, base_url: str = DEFAULT_PROFILE_URL) -> list[TenderDocument]:
        parser = _AnchorCollector()
        parser.feed(html)

        docs: list[TenderDocument] = []
        for href, text in parser.anchors:
            absolute_url = urljoin(base_url, href)
            if not self._is_candidate_document(absolute_url, text):
                continue
            title = text or Path(urlparse(absolute_url).path).name or "documento"
            docs.append(TenderDocument(title=title, url=absolute_url))

        return self._deduplicate(docs)

    def list_documents(self, source_url: str = DEFAULT_PROFILE_URL) -> list[TenderDocument]:
        html = self.fetch_html(source_url)
        return self.extract_documents(html, base_url=source_url)

    def download_documents(
        self,
        documents: Iterable[TenderDocument],
        output_dir: str | Path,
    ) -> list[Path]:
        destination = Path(output_dir)
        destination.mkdir(parents=True, exist_ok=True)

        downloaded: list[Path] = []
        for index, document in enumerate(documents, start=1):
            safe_name = self._sanitize_filename(document.title)
            suffix = Path(urlparse(document.url).path).suffix or ".bin"
            target = destination / f"{index:03d}_{safe_name}{suffix}"
            req = Request(document.url, headers={"User-Agent": self.user_agent})
            with urlopen(req, timeout=60) as resp:  # noqa: S310
                target.write_bytes(resp.read())
            downloaded.append(target)

        return downloaded

    @staticmethod
    def _is_candidate_document(url: str, text: str) -> bool:
        lowered_url = url.lower()
        lowered_text = text.lower()
        has_document_extension = lowered_url.endswith((".pdf", ".doc", ".docx", ".zip", ".odt"))
        tender_keyword = any(
            keyword in lowered_url or keyword in lowered_text
            for keyword in (
                "licit",
                "pliego",
                "expediente",
                "anuncio",
                "adjudic",
            )
        )
        return has_document_extension or tender_keyword

    @staticmethod
    def _sanitize_filename(value: str) -> str:
        cleaned = re.sub(r"[^\w\-.]+", "_", value, flags=re.UNICODE).strip("._")
        return cleaned[:80] or "documento"

    @staticmethod
    def _deduplicate(documents: list[TenderDocument]) -> list[TenderDocument]:
        seen: set[str] = set()
        unique: list[TenderDocument] = []
        for doc in documents:
            if doc.url in seen:
                continue
            seen.add(doc.url)
            unique.append(doc)
        return unique


def _main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Descarga licitaciones del Gobierno de Canarias")
    parser.add_argument("--source-url", default=DEFAULT_PROFILE_URL, help="URL de origen a analizar")
    parser.add_argument("--output-dir", default="downloads/canarias", help="Carpeta de descarga")
    parser.add_argument("--max", type=int, default=20, help="Número máximo de documentos a descargar")
    parser.add_argument("--dry-run", action="store_true", help="Solo listar documentos sin descargarlos")
    args = parser.parse_args()

    downloader = CanariasTenderDownloader()
    documents = downloader.list_documents(args.source_url)
    selected = documents[: args.max]

    if args.dry_run:
        payload = [{"title": d.title, "url": d.url} for d in selected]
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    paths = downloader.download_documents(selected, args.output_dir)
    for path in paths:
        print(path)


if __name__ == "__main__":
    _main()
