from pathlib import Path


def test_launch_materials_include_distribution_ready_assets():
    social_posts = Path("docs/launch/social-posts.md").read_text(encoding="utf-8")
    benchmark_card = Path("docs/launch/benchmark-card.md").read_text(encoding="utf-8")
    flow_card = Path("docs/launch/flow-card.md").read_text(encoding="utf-8")

    assert "71/71" in social_posts
    assert "Show HN" in social_posts
    assert "groundguard-benchmark" in benchmark_card
    assert "工具返回事实" in flow_card
