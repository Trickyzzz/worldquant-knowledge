from worldquant_knowledge.markdown import frontmatter, split_markdown_sections


def test_frontmatter_escapes_quotes_and_adds_required_fields():
    text = frontmatter(
        {
            "title": 'Operators "Time Series"',
            "category": "operators",
            "source_type": "brain_internal",
            "updated_at": "2026-05-01T00:00:00Z",
            "source_url": "https://api.worldquantbrain.com/operators",
        }
    )

    assert 'title: "Operators \\"Time Series\\""' in text
    assert 'category: "operators"' in text
    assert text.startswith("---\n")
    assert text.endswith("---\n")


def test_split_markdown_sections_keeps_files_under_word_limit():
    sections = [
        ("# First", "one two three four"),
        ("# Second", "five six seven eight"),
        ("# Third", "nine ten eleven twelve"),
    ]

    parts = split_markdown_sections(sections, max_words=12)

    assert len(parts) == 2
    assert "First" in parts[0]
    assert "Second" in parts[0]
    assert "Third" in parts[1]
