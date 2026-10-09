import re


def normalize_text(text):
    text = text.lower()

    text = re.sub(
        r"[^a-z0-9\s]",
        "",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def answer_token_recall(generated_answer, expected_answer):
    """
    Measures how many tokens from the expected answer
    are present in the generated answer.
    """

    generated = set(
        normalize_text(generated_answer).split()
    )

    expected = set(
        normalize_text(expected_answer).split()
    )

    if not expected:
        return 0.0

    matched = generated.intersection(expected)

    return len(matched) / len(expected)