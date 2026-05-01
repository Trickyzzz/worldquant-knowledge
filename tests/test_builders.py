from worldquant_knowledge.builders import build_sources


def test_build_sources_creates_partitioned_indexes(tmp_path):
    output_dir = tmp_path / "notebooklm_sources"
    build_sources(
        output_dir=output_dir,
        public_articles=[
            {
                "title": "WorldQuant Brain",
                "url": "https://www.worldquant.com/brain/",
                "markdown": "Brain article body about momentum and turnover.",
                "category": "worldquant_brain",
            }
        ],
        operators=[
            {"name": "rank", "category": "Cross Sectional", "description": "Ranks values."},
            {"name": "ts_delta", "category": "Time Series", "description": "Time-series change useful for momentum."},
            {"name": "hump", "category": "Transformational", "description": "Helps reduce turnover."},
        ],
        datasets=[{"id": "pv1", "name": "Price Volume", "description": "OHLCV data"}],
        fields=[
            {"id": "close", "dataset": {"id": "pv1"}, "type": "MATRIX", "description": "Close price"},
            {"id": "volume", "dataset": {"id": "pv1"}, "type": "MATRIX", "description": "Trading volume and liquidity"},
        ],
        notes=[],
        max_words_per_file=30000,
    )

    assert (output_dir / "00_index.md").exists()
    assert (output_dir / "operators" / "00_operators_index.md").exists()
    assert (output_dir / "datasets_and_fields" / "00_datasets_fields_index.md").exists()
    assert (output_dir / "public_articles" / "00_public_articles_index.md").exists()
    assert (output_dir / "alpha_patterns" / "02_momentum.md").exists()
    assert (output_dir / "alpha_patterns" / "06_turnover_control.md").exists()
    momentum = (output_dir / "alpha_patterns" / "02_momentum.md").read_text(encoding="utf-8")
    turnover = (output_dir / "alpha_patterns" / "06_turnover_control.md").read_text(encoding="utf-8")
    assert "ts_delta" in momentum
    assert "WorldQuant Brain" in momentum
    assert "hump" in turnover
    assert "generated placeholder" not in momentum


def test_build_sources_omits_empty_generated_sections(tmp_path):
    output_dir = tmp_path / "notebooklm_sources"
    build_sources(
        output_dir=output_dir,
        public_articles=[],
        operators=[],
        datasets=[],
        fields=[],
        notes=[],
        max_words_per_file=30000,
    )

    assert not (output_dir / "public_articles").exists()
    assert not (output_dir / "my_notes").exists()
    assert not (output_dir / "alpha_patterns" / "02_momentum.md").exists()
    assert (output_dir / "00_index.md").exists()
