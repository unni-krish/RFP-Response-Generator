"""
A2_Extract.py
─────────────────────────────────────────────────────────────────────────────
Agent for extracting text, tables, and images from multiple document types
and generating a detailed report using multi-modal LLMs.
"""

import os
import glob
import base64
import logging
from io import BytesIO
from PIL import Image

try:
    import fitz  # PyMuPDF
    fitz.TOOLS.mupdf_display_errors(False) # Suppress MuPDF core warnings
except ImportError:
    fitz = None

try:
    from docx import Document
except ImportError:
    Document = None

import sys
# Add parent directory to path so we can import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.llm_engine import invoke
from utils.config import load_config

config = load_config()
paths_config = config.get("paths", {})
INPUT_FOLDER = paths_config.get("input_folder", "input")

extract_config = config.get("extract", {})

# ==============================================================================
# Global Configuration & Fallbacks (from config)
# ==============================================================================
DEFAULT_VISION_MODEL = extract_config.get("vision_model", "gpt-4o")
DEFAULT_TEXT_MODEL = extract_config.get("text_model", "gpt-4o")
DEFAULT_PDF_RENDER_DPI = extract_config.get("pdf_render_dpi", 300)
SUPPORTED_IMAGE_FORMATS = extract_config.get("supported_image_formats", ["png", "jpg", "jpeg", "webp"])
SUPPORTED_WORD_FORMATS = extract_config.get("supported_word_formats", ["docx", "doc"])
SUPPORTED_PDF_FORMATS = extract_config.get("supported_pdf_formats", ["pdf"])
SUPPORTED_TXT_FORMATS = extract_config.get("supported_txt_formats", ["txt"])
PROMPT_VISION_EXTRACTION = extract_config.get("prompt_vision_extraction", "A2_vision_extraction.txt")
PROMPT_FINAL_REPORT = extract_config.get("prompt_final_report", "A2_final_report.txt")

# Setup Logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

class A2ExtractAgent:
    def __init__(self, vision_model=DEFAULT_VISION_MODEL, text_model=DEFAULT_TEXT_MODEL):
        """
        Initializes the agent with specified models.
        vision_model: used for extracting content from images and complex PDF pages.
        text_model: used for final report generation.
        """
        self.vision_model = vision_model
        self.text_model = text_model

    def encode_image_base64(self, image_path: str) -> str:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
            
    def _encode_pil_image_base64(self, pil_img) -> str:
        buffered = BytesIO()
        pil_img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")

    def _extract_from_image_with_llm(self, base64_image: str, filename: str) -> str:
        """Uses the Vision LLM to extract text, tables, and details from an image."""
        prompt_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts", PROMPT_VISION_EXTRACTION)
        with open(prompt_path, "r", encoding="utf-8") as f:
            vision_prompt_template = f.read()
            
        vision_text = vision_prompt_template.replace("{filename}", filename)
        
        prompt = [
            {"type": "text", "text": vision_text},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
        ]
        logger.info(f"Extracting data from image via Vision LLM ({self.vision_model})...")
        vision_output = invoke(prompt, model=self.vision_model)
        logger.info(f"Vision LLM Output for {filename}:\n{vision_output}")
        return vision_output

    def process_txt(self, file_path: str) -> str:
        logger.info(f"Processing TXT file: {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def process_docx(self, file_path: str) -> str:
        logger.info(f"Processing DOCX file: {file_path}")
        if not Document:
            logger.error("python-docx is not installed.")
            return "[Error: python-docx not installed]"
        
        doc = Document(file_path)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
            
        # Optional: extract simple tables as text
        for table in doc.tables:
            for row in table.rows:
                row_data = [cell.text for cell in row.cells]
                full_text.append(" | ".join(row_data))
                
        return "\n".join(full_text)

    def process_image(self, file_path: str) -> str:
        logger.info(f"Processing Image file: {file_path}")
        base64_img = self.encode_image_base64(file_path)
        return self._extract_from_image_with_llm(base64_img, os.path.basename(file_path))

    def process_pdf(self, file_path: str) -> str:
        """
        Hybrid PDF extraction strategy:

        1. Extract text directly whenever possible
        2. Extract tables separately
        3. Detect scanned pages
        4. Detect large meaningful images
        5. Ignore small logos/icons/banners
        """

        logger.info(f"Processing PDF file: {file_path}")

        if not fitz:
            logger.error("PyMuPDF is not installed.")
            return "[Error: PyMuPDF not installed]"

        doc = fitz.open(file_path)

        extracted_content = []

        for page_num in range(len(doc)):

            page = doc.load_page(page_num)

            page_results = []

            logger.info(f"Processing Page {page_num + 1}")

            # =====================================================
            # STEP 1 - DIRECT TEXT EXTRACTION
            # =====================================================

            # Use sort=True to extract text in a more natural reading order (top-to-bottom, left-to-right)
            text = page.get_text("text", sort=True).strip()

            word_count = len(text.split())

            if text:
                page_results.append(
                    f"--- Page {page_num + 1} Text ---\n{text}"
                )

            # =====================================================
            # STEP 2 - TABLE EXTRACTION
            # =====================================================

            try:

                tables = page.find_tables()

                if tables and len(tables.tables) > 0:

                    for idx, table in enumerate(tables.tables, start=1):

                        try:
                            table_bbox = table.bbox
                            pix = page.get_pixmap(clip=table_bbox, dpi=DEFAULT_PDF_RENDER_DPI)
                            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                            base64_img = self._encode_pil_image_base64(img)

                            table_text = self._extract_from_image_with_llm(
                                base64_img,
                                f"{os.path.basename(file_path)} (Page {page_num + 1} Table {idx}) - Extract this table exactly into Markdown format without missing any rows or columns."
                            )

                            page_results.append(
                                f"\n--- Page {page_num + 1} Table {idx} ---\n{table_text}"
                            )

                        except Exception as e:
                            logger.warning(
                                f"Table extraction failed on page "
                                f"{page_num + 1}: {e}"
                            )

            except Exception:
                pass

            # =====================================================
            # STEP 3 - IMAGE ANALYSIS
            # =====================================================

            page_rect = page.rect
            page_area = page_rect.width * page_rect.height

            images = page.get_images(full=True)

            large_images = []

            for img in images:

                try:

                    xref = img[0]

                    rects = page.get_image_rects(xref)

                    for rect in rects:

                        image_area = rect.width * rect.height

                        coverage = image_area / page_area

                        if coverage >= 0.15:
                            large_images.append(rect)

                except Exception:
                    continue

            # =====================================================
            # STEP 4 - SCANNED PAGE DETECTION
            # =====================================================

            scanned_page = False

            # Increased word count threshold for scanned pages (handles hidden/garbled OCR)
            if word_count < 100 and len(large_images) > 0:
                scanned_page = True

            # =====================================================
            # STEP 5 - VISION FALLBACK
            # =====================================================

            if scanned_page:

                logger.info(
                    f"Page {page_num + 1}: "
                    f"Likely scanned document. Using Vision."
                )

                pix = page.get_pixmap(
                    dpi=DEFAULT_PDF_RENDER_DPI
                )

                img = Image.frombytes(
                    "RGB",
                    [pix.width, pix.height],
                    pix.samples
                )

                base64_img = self._encode_pil_image_base64(img)

                vision_output = self._extract_from_image_with_llm(
                    base64_img,
                    f"{os.path.basename(file_path)} "
                    f"(Page {page_num + 1})"
                )

                page_results.append(
                    f"\n--- Page {page_num + 1} Vision Extraction ---\n"
                    f"{vision_output}"
                )

            # =====================================================
            # STEP 6 - LARGE IMAGE / DIAGRAM DETECTION
            # =====================================================

            elif len(large_images) > 0:

                logger.info(
                    f"Page {page_num + 1}: "
                    f"Large image/diagram detected."
                )

                for idx, rect in enumerate(
                    large_images,
                    start=1
                ):

                    try:

                        pix = page.get_pixmap(
                            clip=rect,
                            dpi=DEFAULT_PDF_RENDER_DPI
                        )

                        img = Image.frombytes(
                            "RGB",
                            [pix.width, pix.height],
                            pix.samples
                        )

                        base64_img = self._encode_pil_image_base64(
                            img
                        )

                        image_result = (
                            self._extract_from_image_with_llm(
                                base64_img,
                                f"{os.path.basename(file_path)} "
                                f"(Page {page_num + 1} "
                                f"Diagram {idx})"
                            )
                        )

                        page_results.append(
                            f"\n--- Page {page_num + 1} "
                            f"Diagram {idx} ---\n"
                            f"{image_result}"
                        )

                    except Exception as e:

                        logger.warning(
                            f"Diagram extraction failed: {e}"
                        )

            # =====================================================
            # STEP 7 - EMPTY PAGE FALLBACK
            # =====================================================

            if not page_results:

                logger.info(
                    f"Page {page_num + 1}: "
                    f"No text found. Using Vision fallback."
                )

                pix = page.get_pixmap(
                    dpi=DEFAULT_PDF_RENDER_DPI
                )

                img = Image.frombytes(
                    "RGB",
                    [pix.width, pix.height],
                    pix.samples
                )

                base64_img = self._encode_pil_image_base64(img)

                vision_output = self._extract_from_image_with_llm(
                    base64_img,
                    f"{os.path.basename(file_path)} "
                    f"(Page {page_num + 1})"
                )

                page_results.append(
                    f"\n--- Page {page_num + 1} Vision Extraction ---\n"
                    f"{vision_output}"
                )

            extracted_content.append(
                "\n".join(page_results)
            )

        doc.close()

        return "\n\n".join(extracted_content)

    def extract_folder(self, folder_path: str) -> dict:
        """Iterates through a folder and extracts content from all supported files."""
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"Folder not found: {folder_path}")

        extracted_data = {}
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                ext = file.lower().split('.')[-1]
                
                try:
                    if ext in SUPPORTED_TXT_FORMATS:
                        extracted_data[file] = self.process_txt(file_path)
                    elif ext in SUPPORTED_WORD_FORMATS:
                        extracted_data[file] = self.process_docx(file_path)
                    elif ext in SUPPORTED_IMAGE_FORMATS:
                        extracted_data[file] = self.process_image(file_path)
                    elif ext in SUPPORTED_PDF_FORMATS:
                        extracted_data[file] = self.process_pdf(file_path)
                    else:
                        logger.warning(f"Skipping unsupported file type: {file}")
                except Exception as e:
                    logger.error(f"Error processing {file}: {e}")
                    extracted_data[file] = f"[Error extracting data: {str(e)}]"

        return extracted_data

    def generate_report(self, folder_path: str) -> str:
        """Main method: Extracts all data from folder and generates a detailed report."""
        logger.info("=== Phase 1: Extracting Content ===")
        extracted_data = self.extract_folder(folder_path)
        
        if not extracted_data:
            return "No valid documents found or processed in the folder."

        logger.info("=== Phase 2: Generating Final Report ===")
        
        # Combine all extracted content into a large context block
        context_blocks = []
        for filename, content in extracted_data.items():
            context_blocks.append(f"### Document: {filename}\n{content}\n")
        
        full_context = "\n".join(context_blocks)
        
        logger.info("Skipping final LLM summarization to prevent data loss. Returning combined extraction directly.")
        return full_context

    def generate_report_from_file(self, file_path: str) -> str:
        """Extracts data from a single file and generates a detailed report."""
        logger.info(f"=== Phase 1: Extracting Content from {file_path} ===")
        
        ext = file_path.lower().split('.')[-1]
        filename = os.path.basename(file_path)
        content = ""
        
        try:
            if ext in SUPPORTED_TXT_FORMATS:
                content = self.process_txt(file_path)
            elif ext in SUPPORTED_WORD_FORMATS:
                content = self.process_docx(file_path)
            elif ext in SUPPORTED_IMAGE_FORMATS:
                content = self.process_image(file_path)
            elif ext in SUPPORTED_PDF_FORMATS:
                content = self.process_pdf(file_path)
            else:
                return f"Unsupported file type: {filename}"
        except Exception as e:
            logger.error(f"Error processing {filename}: {e}")
            return f"[Error extracting data: {str(e)}]"

        if not content:
            return "No valid content extracted from the document."

        logger.info("=== Phase 2: Generating Final Report ===")
        full_context = f"### Document: {filename}\n{content}\n"
        
        logger.info("Skipping final LLM summarization to prevent data loss. Returning combined extraction directly.")
        return full_context

# ====================== Example Usage ======================
if __name__ == "__main__":
    # Point this to a test folder containing dummy files
    TEST_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), INPUT_FOLDER)
    
    # Create the test folder if it doesn't exist just to prevent errors on first run
    os.makedirs(TEST_FOLDER, exist_ok=True)
    
    print(f"To test this agent, place some files in: {TEST_FOLDER}")
    print("Then run this script again.")
    print("-" * 50)
    
    # If folder has files, process them
    if any(os.scandir(TEST_FOLDER)):
        agent = A2ExtractAgent(vision_model=DEFAULT_VISION_MODEL, text_model=DEFAULT_TEXT_MODEL)
        final_report = agent.generate_report(TEST_FOLDER)
        
        print("\n\n" + "="*50)
        print("FINAL REPORT:")
        print("="*50)
        print(final_report)
    else:
        print(f"Folder '{TEST_FOLDER}' is empty. No extraction performed.")
