"""
Tests for all 20 working sources.
Run: pytest tests/test_sources.py -v
"""
import pytest
from dotenv import load_dotenv
load_dotenv()


def _check(fn, query="machine learning", min_results=0):
    results = fn(query)
    assert isinstance(results, list), f"Expected list, got {type(results)}"
    assert len(results) >= min_results, f"Expected >={min_results} results, got {len(results)}"
    if results:
        r = results[0]
        assert "title" in r
        assert "url" in r
        assert "source" in r
        assert "year" in r
    return results


def test_pubmed():
    from app.sources.pubmed import search_pubmed
    assert len(_check(search_pubmed)) > 0

def test_arxiv():
    from app.sources.arxiv import search_arxiv
    assert len(_check(search_arxiv)) > 0

def test_openalex():
    from app.sources.openalex import search_openalex
    assert len(_check(search_openalex)) > 0

def test_europe_pmc():
    from app.sources.europe_pmc import search_europe_pmc
    assert len(_check(search_europe_pmc)) > 0

def test_crossref():
    from app.sources.crossref import search_crossref
    assert len(_check(search_crossref)) > 0

def test_grants_nih():
    from app.sources.grants_nih import search_nih
    assert len(_check(search_nih)) > 0

def test_grants_nsf():
    from app.sources.grants_nsf import search_nsf
    assert len(_check(search_nsf)) > 0

def test_grants_ukri():
    from app.sources.grants_ukri import search_ukri
    assert len(_check(search_ukri)) > 0

def test_patents_lens():
    from app.sources.patents_lens import search_lens
    assert len(_check(search_lens)) > 0

def test_google_patents():
    from app.sources.google_patents import search_google_patents
    assert len(_check(search_google_patents)) > 0

def test_clinical_trials():
    from app.sources.clinical_trials import search_clinical_trials
    assert len(_check(search_clinical_trials)) > 0

def test_fda():
    from app.sources.fda import search_fda
    assert len(_check(search_fda)) > 0

def test_ycombinator():
    from app.sources.ycombinator import search_yc
    assert len(_check(search_yc)) > 0

def test_product_hunt():
    from app.sources.product_hunt import search_product_hunt
    assert len(_check(search_product_hunt, query="artificial intelligence")) > 0

def test_alpha_vantage():
    from app.sources.alpha_vantage import search_alpha_vantage
    assert len(_check(search_alpha_vantage)) > 0

def test_news():
    from app.sources.news import search_news
    assert len(_check(search_news)) > 0

def test_congress():
    from app.sources.congress import search_congress
    assert len(_check(search_congress, query="artificial intelligence")) > 0

def test_courtlistener():
    from app.sources.courtlistener import search_courtlistener
    assert len(_check(search_courtlistener, query="artificial intelligence")) > 0

def test_fred():
    from app.sources.fred import search_fred
    assert len(_check(search_fred, query="GDP")) > 0

# graceful zero returns (no key / disabled)
def test_semantic_scholar_graceful():
    from app.sources.semantic_scholar import search_semantic_scholar
    assert isinstance(search_semantic_scholar("machine learning"), list)

def test_patents_epo_graceful():
    from app.sources.patents_epo import search_epo
    assert isinstance(search_epo("machine learning"), list)