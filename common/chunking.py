from bs4 import BeautifulSoup


TARGET_CHUNK_WORDS = 700
OVERLAP_SENTENCES = 1
MIN_CHUNK_WORDS = 8


def _split_into_sentences(text):
    """Naive sentence splitter on '.', '!', '?' followed by whitespace."""
    import re
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s for s in sentences if s]


def _split_oversized_paragraph(paragraph):
    """
    Split a single paragraph that alone exceeds the target chunk size,
    breaking at sentence boundaries rather than mid-sentence.
    """
    sentences = _split_into_sentences(paragraph)
    chunks = []
    current = []
    current_words = 0

    for sentence in sentences:
        word_count = len(sentence.split())
        if current_words + word_count > TARGET_CHUNK_WORDS and current:
            chunks.append(" ".join(current))
            current = current[-OVERLAP_SENTENCES:]
            current_words = sum(len(s.split()) for s in current)
        current.append(sentence)
        current_words += word_count

    if current:
        chunks.append(" ".join(current))

    return chunks


def _chunk_paragraphs(paragraphs):
    """
    Accumulate paragraphs into chunks up to TARGET_CHUNK_WORDS,
    splitting any single oversized paragraph by sentence, and
    carrying the last sentence of each finished chunk forward
    as overlap into the next.
    """
    chunks = []
    current = []
    current_words = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        para_words = len(para.split())

        if para_words > TARGET_CHUNK_WORDS:
            if current:
                chunks.append(" ".join(current))
                current = []
                current_words = 0
            chunks.extend(_split_oversized_paragraph(para))
            continue

        if current_words + para_words > TARGET_CHUNK_WORDS and current:
            chunks.append(" ".join(current))
            overlap_sentences = _split_into_sentences(current[-1])[-OVERLAP_SENTENCES:]
            current = overlap_sentences
            current_words = sum(len(s.split()) for s in current)

        current.append(para)
        current_words += para_words

    if current:
        chunks.append(" ".join(current))

    return chunks


def _extract_paragraphs_from_html(html_fragment):
    """Extract plain-text paragraphs from HTML <p> tags, dropping aside/atom elements."""
    soup = BeautifulSoup(html_fragment, "html.parser")

    for tag in soup.find_all(["aside", "figure"]):
        tag.decompose()

    paragraphs = []
    for p in soup.find_all("p"):
        text = p.get_text(strip=True)
        if text:
            paragraphs.append(text)

    return paragraphs


def _chunk_liveblog(html_body):
    """
    Split a liveblog's HTML into chunks based on <div class="block"> boundaries,
    since each block is a self-contained, independently timestamped update.
    Any block whose own text still exceeds the target size is further split
    via the standard paragraph/sentence logic. Blocks with too little real
    content (e.g. just a timestamp, an embedded tweet/video with no caption
    text) are skipped entirely.
    """
    soup = BeautifulSoup(html_body, "html.parser")
    blocks = soup.find_all("div", class_="block")

    all_chunks = []
    for block in blocks:
        paragraphs = _extract_paragraphs_from_html(str(block))
        if not paragraphs:
            continue
        block_text = " ".join(paragraphs)
        if len(block_text.split()) < MIN_CHUNK_WORDS:
            continue
        if len(block_text.split()) <= TARGET_CHUNK_WORDS:
            all_chunks.append(block_text)
        else:
            all_chunks.extend(_chunk_paragraphs(paragraphs))

    return all_chunks


def chunk_article(content_type, body_html):
    """
    Given a Guardian content type and raw HTML body, return a list of
    text chunks ready for embedding. Returns an empty list for types
    with no usable text content (e.g. 'interactive').
    """
    if content_type == "interactive":
        return []

    if not body_html:
        return []

    if content_type == "liveblog":
        chunks = _chunk_liveblog(body_html)
    else:
        paragraphs = _extract_paragraphs_from_html(body_html)
        chunks = _chunk_paragraphs(paragraphs)

    return chunks


def chunk_summary(text):
    """
    For sources with short content (NYT abstract/lead_paragraph, Currents
    description) — no splitting needed, just wrap as a single chunk.
    """
    text = text.strip() if text else ""
    if not text:
        return []
    return [text]