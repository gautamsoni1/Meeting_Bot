from PIL import Image
import nltk
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

# ✅ FIX START
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab')
# ✅ FIX END


def generate_image_summary(image_path: str) -> str:
    img = Image.open(image_path)

    # your logic here
    return "Image summary"
