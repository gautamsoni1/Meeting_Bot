import easyocr
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer

reader = easyocr.Reader(['en'])

def extract_text_and_summary(image_path: str) -> str:
    # OCR: Extract text
    results = reader.readtext(image_path)
    extracted_text = " ".join([text for _, text, _ in results])
    if not extracted_text.strip():
        return "No readable text detected in the image."

    # Summarize using sumy
    parser = PlaintextParser.from_string(extracted_text, Tokenizer("english"))
    summarizer = LsaSummarizer()
    summary_sentences = summarizer(parser.document, sentences_count=3)
    summary = " ".join([str(sentence) for sentence in summary_sentences])
    return summary