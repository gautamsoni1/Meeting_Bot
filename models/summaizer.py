from transformers import pipeline

# LLM-based summarizer
summarizer = pipeline("summarization")

def summarize_text(text: str) -> str:
    if not text.strip():
        return "No text found in image."
    result = summarizer(text, max_length=100, min_length=20, do_sample=False)
    return result[0]["summary_text"]