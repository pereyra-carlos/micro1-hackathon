from common.text import truncate


def test_short_text_untouched():
    assert truncate("hello", limit=100) == "hello"


def test_long_text_keeps_head_and_tail():
    text = "A" * 5000 + "B" * 5000 + "C" * 5000
    out = truncate(text, limit=9000)
    assert len(out) < len(text)
    assert out.startswith("A")
    assert out.endswith("C" * 100)
    assert "chars truncated" in out


def test_tail_is_favored_over_head():
    out = truncate("x" * 20000, limit=9000)
    head, _, tail = out.partition("\n")
    assert len(tail) > len(head)
