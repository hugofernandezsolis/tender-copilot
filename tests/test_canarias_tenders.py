from canarias_tenders import CanariasTenderDownloader


def test_extract_documents_filters_and_deduplicates():
    html = """
    <html><body>
      <a href="/docs/pliego1.pdf">Pliego técnico</a>
      <a href="https://example.org/licitacion/expediente-77">Expediente 77</a>
      <a href="https://example.org/licitacion/expediente-77">Expediente 77 duplicado</a>
      <a href="/noticia/general">Noticia general</a>
    </body></html>
    """

    downloader = CanariasTenderDownloader()
    docs = downloader.extract_documents(html, base_url="https://www.gobiernodecanarias.org/base/")

    assert len(docs) == 2
    assert docs[0].url == "https://www.gobiernodecanarias.org/docs/pliego1.pdf"
    assert docs[1].url == "https://example.org/licitacion/expediente-77"


def test_sanitize_filename_truncates_and_replaces():
    downloader = CanariasTenderDownloader()
    name = downloader._sanitize_filename("Pliego técnico / expediente: 123")

    assert " " not in name
    assert "/" not in name
    assert len(name) <= 80
