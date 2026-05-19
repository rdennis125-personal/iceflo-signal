from pathlib import Path

from iceflo_signal.delivery.demo_renderer import render_template_demos


def test_render_template_demos_writes_html_index_and_eml(tmp_path: Path) -> None:
    result = render_template_demos(
        recipient="rdennis125@gmail.com",
        output_dir=tmp_path,
        template_dir=Path("templates"),
    )

    assert len(result.html_paths) == 5
    assert len(result.eml_paths) == 5
    assert result.index_path.exists()
    assert "rdennis125@gmail.com" in result.index_path.read_text(encoding="utf-8")
    assert "Lorem ipsum" in result.html_paths[0].read_text(encoding="utf-8")
    assert "To: rdennis125@gmail.com" in result.eml_paths[0].read_text(encoding="utf-8")
