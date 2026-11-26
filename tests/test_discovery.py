from scrapepolicy import find_links

HTML = """
<html><body>
<nav><a href="/tentang-kami">Tentang Kami</a></nav>
<article><a href="/news/terms-of-trade-deal">Terms of trade deal explained</a></article>
<footer>
  <a href="/syarat-dan-ketentuan">Syarat &amp; Ketentuan</a>
  <a href="https://example.com/kontak">Hubungi Kami</a>
</footer>
</body></html>
"""


def test_indonesian_links_found():
    links = find_links(HTML, "https://example.com/")
    assert links["terms_of_use"] == "https://example.com/syarat-dan-ketentuan"
    assert links["about"] == "https://example.com/tentang-kami"
    assert links["contact"] == "https://example.com/kontak"


def test_relative_urls_and_missing_page():
    html = '<footer><a href="legal/tos">Terms of Service</a><a href="/about">About us</a></footer>'
    links = find_links(html, "https://example.com/")
    assert links["terms_of_use"] == "https://example.com/legal/tos"
    assert links["about"] == "https://example.com/about"
    assert links["contact"] is None


def test_unrelated_links_return_none():
    html = '<a href="/photos">Photos</a><a href="mailto:a@b.com">Email</a>'
    assert find_links(html, "https://example.com/") == {
        "terms_of_use": None,
        "about": None,
        "contact": None,
    }