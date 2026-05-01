from worldquant_knowledge.builders import build_sources


def test_build_sources_creates_partitioned_indexes(tmp_path):
    output_dir = tmp_path / "notebooklm_sources"
    build_sources(
        output_dir=output_dir,
        public_articles=[
            {
                "title": "WorldQuant Brain",
                "url": "https://www.worldquant.com/brain/",
                "markdown": "Brain article body",
                "category": "worldquant_brain",
            }
        ],
        operators=[{"name": "rank", "category": "Cross Sectional", "description": "Ranks values."}],
        datasets=[{"id": "pv1", "name": "Price Volume", "description": "OHLCV data"}],
        fields=[{"id": "close", "dataset": {"id": "pv1"}, "type": "MATRIX", "description": "Close price"}],
        notes=[],
        max_words_per_file=30000,
    )

    assert (output_dir / "00_index.md").exists()
    assert (output_dir / "operators" / "00_operators_index.md").exists()
    assert (output_dir / "datasets_and_fields" / "00_datasets_fields_index.md").exists()
    assert (output_dir / "public_articles" / "00_public_articles_index.md").exists()
