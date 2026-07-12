from pathlib import Path

from backend.app.main import get_embedding, get_llm_answer, read_document_text


def test_read_document_text_supports_txt(tmp_path: Path) -> None:
    document_path = tmp_path / 'sample.txt'
    document_path.write_text('This is a sample text document for the RAG demo.', encoding='utf-8')

    assert read_document_text(document_path) == 'This is a sample text document for the RAG demo.'


def test_fallback_pipeline_functions_work_without_api_keys() -> None:
    embedding = get_embedding('A sample chunk about experimentation')
    answer = get_llm_answer('What does the document describe?')

    assert len(embedding) == 768
    assert isinstance(answer, str) and answer
