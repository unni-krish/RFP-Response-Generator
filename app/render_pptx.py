import json
import os
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
import logging

try:
    from PIL import Image as _PILImage
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Modern Color Palette
BRAND_PRIMARY = RGBColor(0, 51, 102)    # Deep Navy Blue
BRAND_SECONDARY = RGBColor(0, 102, 204) # Accent Blue
BRAND_LIGHT = RGBColor(230, 240, 250)   # Light Blue Backgrounds
TEXT_DARK = RGBColor(50, 50, 50)        # Dark Gray (Primary Text)
TEXT_LIGHT = RGBColor(120, 120, 120)    # Light Gray (Secondary Text)
WHITE = RGBColor(255, 255, 255)
ACCENT_GREEN = RGBColor(40, 167, 69)
ACCENT_ORANGE = RGBColor(253, 126, 20)

FONT_NAME = "Calibri" # universally supported sans-serif


def render_ppt_from_json(ppt_structure: dict, output_path: str):
    """Convert PPT JSON structure to an actual highly-styled PPTX file"""
    logger.info(f"Rendering PPTX to {output_path}...")
    
    prs = Presentation()
    # 16:9 Aspect Ratio
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    
    presentation_data = ppt_structure.get("presentation", {})
    client_name = presentation_data.get('client', 'Client')
    
    for slide_data in presentation_data.get("slides", []):
        # Always use the completely blank layout to construct from scratch
        slide_layout = prs.slide_layouts[6] 
        slide = prs.slides.add_slide(slide_layout)
        
        slide_type = slide_data.get("type", "text_bullets")
        title = slide_data.get("title", "")
        content = slide_data.get("content", {})
        slide_number = slide_data.get("slide_number", "")
        
        # Draw header/footer for all except title and closing
        if slide_type not in ["title_slide", "closing"]:
            _draw_header(slide, title)
            _draw_footer(slide, slide_number, client_name)
        
        # Route to specific renderer
        if slide_type == "title_slide":
            _render_title_slide(slide, content)
        elif slide_type == "agenda":
            _render_agenda(slide, content)
        elif slide_type == "text_bullets":
            _render_text_bullets(slide, content)
        elif slide_type == "two_column":
            _render_two_column(slide, content)
        elif slide_type == "diagram_with_text":
            _render_diagram_with_text(slide, content)
        elif slide_type == "table":
            _render_table(slide, content)
        elif slide_type == "architecture_diagram":
            _render_architecture_diagram(slide, content)
        elif slide_type == "component_detail":
            _render_component_detail(slide, content)
        elif slide_type == "timeline":
            _render_timeline(slide, content)
        elif slide_type == "org_chart":
            _render_org_chart(slide, content)
        elif slide_type == "case_studies":
            _render_case_studies(slide, content)
        elif slide_type == "closing":
            _render_closing(slide, content)
        else:
            # Fallback
            _render_text_bullets(slide, {"bullets": [f"Unknown slide type: {slide_type}"]})

    prs.save(output_path)
    logger.info(f"✓ Modern PPT successfully saved to {output_path}")

# --- GLOBAL SHAPE HELPERS ---

def _draw_header(slide, title_text):
    """Draws a consistent modern header."""
    # Top decorative bar
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(0.15))
    shape.fill.solid()
    shape.fill.fore_color.rgb = BRAND_PRIMARY
    shape.line.fill.background()
    
    if title_text:
        title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.333), Inches(0.8))
        tf = title_box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title_text.upper()
        p.font.name = FONT_NAME
        p.font.size = Pt(28)
        p.font.bold = True
        p.font.color.rgb = BRAND_PRIMARY
        
        # Underline
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.5), Inches(1.1), Inches(12.333), Inches(0.02))
        line.fill.solid()
        line.fill.fore_color.rgb = BRAND_LIGHT
        line.line.fill.background()

def _draw_footer(slide, slide_num, client_name):
    """Draws a consistent subtle footer."""
    footer_box = slide.shapes.add_textbox(Inches(0.5), Inches(7.0), Inches(12.333), Inches(0.4))
    tf = footer_box.text_frame
    p = tf.paragraphs[0]
    p.text = f"{client_name} | Architecture Proposal | Slide {slide_num}"
    p.font.name = FONT_NAME
    p.font.size = Pt(10)
    p.font.color.rgb = TEXT_LIGHT
    p.alignment = PP_ALIGN.RIGHT

# --- SPECIFIC SLIDE RENDERERS ---

def _render_title_slide(slide, content):
    """Modern split-layout title slide with gradient accent and structured typography."""
    # Full background — deep navy
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    bg.fill.solid()
    bg.fill.fore_color.rgb = BRAND_PRIMARY
    bg.line.fill.background()
    
    # Left accent stripe
    accent = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(0.4), Inches(7.5))
    accent.fill.solid()
    accent.fill.fore_color.rgb = BRAND_SECONDARY
    accent.line.fill.background()
    
    # Top decorative line
    top_line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.2), Inches(1.8), Inches(2.5), Inches(0.04))
    top_line.fill.solid()
    top_line.fill.fore_color.rgb = ACCENT_GREEN
    top_line.line.fill.background()
    
    # Subtitle label (small, above the title)
    sub_label = slide.shapes.add_textbox(Inches(1.2), Inches(2.0), Inches(10), Inches(0.5))
    tf_sub = sub_label.text_frame
    ps = tf_sub.paragraphs[0]
    ps.text = content.get("subtitle", "Solution Architecture & Technical Proposal").upper()
    ps.font.name = FONT_NAME
    ps.font.size = Pt(14)
    ps.font.color.rgb = ACCENT_GREEN
    ps.font.bold = True
    ps.font.letter_spacing = Pt(2)
    
    # Main Title — large and prominent
    project_title = content.get("project_title", "Architecture Proposal")
    # Auto-size: if title is very long, reduce font
    title_font_size = Pt(44) if len(project_title) > 50 else Pt(52)
    
    title_box = slide.shapes.add_textbox(Inches(1.2), Inches(2.8), Inches(10.5), Inches(2.2))
    tf = title_box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = project_title
    p.font.name = FONT_NAME
    p.font.size = title_font_size
    p.font.bold = True
    p.font.color.rgb = WHITE
    
    # Divider line between title and client info
    divider = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.2), Inches(5.2), Inches(4), Inches(0.03))
    divider.fill.solid()
    divider.fill.fore_color.rgb = RGBColor(100, 149, 237)  # Cornflower blue
    divider.line.fill.background()
    
    # Client name
    client_box = slide.shapes.add_textbox(Inches(1.2), Inches(5.5), Inches(10), Inches(0.5))
    tf_c = client_box.text_frame
    pc = tf_c.paragraphs[0]
    pc.text = f"Prepared for: {content.get('client_name', 'Client')}"
    pc.font.name = FONT_NAME
    pc.font.size = Pt(20)
    pc.font.color.rgb = BRAND_LIGHT
    pc.font.bold = False
    
    # Date
    date_box = slide.shapes.add_textbox(Inches(1.2), Inches(6.1), Inches(10), Inches(0.4))
    tf_d = date_box.text_frame
    pd = tf_d.paragraphs[0]
    pd.text = content.get("date", "")
    pd.font.name = FONT_NAME
    pd.font.size = Pt(16)
    pd.font.color.rgb = TEXT_LIGHT

def _render_agenda(slide, content):
    """Render agenda as a clean two-column structured list."""
    sections = content.get("sections", [])
    
    left_x = Inches(1.5)
    right_x = Inches(7.0)
    y_start = Inches(2.0)
    y_offset = Inches(0.7)
    
    for i, section in enumerate(sections):
        x = left_x if i < 5 else right_x
        y = y_start + (i % 5) * y_offset
        
        # Number Circle
        circle = slide.shapes.add_shape(MSO_SHAPE.OVAL, x, y, Inches(0.5), Inches(0.5))
        circle.fill.solid()
        circle.fill.fore_color.rgb = BRAND_SECONDARY
        circle.line.fill.background()
        tf = circle.text_frame
        p = tf.paragraphs[0]
        p.text = str(i + 1)
        p.alignment = PP_ALIGN.CENTER
        p.font.color.rgb = WHITE
        p.font.bold = True
        
        # Text
        txt_box = slide.shapes.add_textbox(x + Inches(0.7), y, Inches(4.5), Inches(0.5))
        p2 = txt_box.text_frame.paragraphs[0]
        p2.text = f"{section.get('title', '')} (Slides {section.get('slides', '')})"
        p2.font.name = FONT_NAME
        p2.font.size = Pt(18)
        p2.font.color.rgb = TEXT_DARK

def _render_text_bullets(slide, content):
    """Clean, padded bullet points with section headings.
    Lines without a leading dash are rendered as bold section headings.
    Lines starting with '- ' are rendered as indented sub-bullets."""
    bullets = content.get("bullets", [])
    
    txt_box = slide.shapes.add_textbox(Inches(1), Inches(1.5), Inches(11.333), Inches(5.2))
    tf = txt_box.text_frame
    tf.word_wrap = True
    
    for i, bullet in enumerate(bullets):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        bullet_str = str(bullet)
        
        if bullet_str.startswith('-'):
            # Sub-bullet: indented, lighter, smaller
            p.level = 1
            p.text = f"•  {bullet_str.lstrip('- ')}"
            p.font.size = Pt(16)
            p.font.color.rgb = TEXT_DARK
            p.font.bold = False
            p.space_after = Pt(6)
        else:
            # Section heading: bold, colored, larger
            p.level = 0
            p.text = bullet_str.upper()
            p.font.size = Pt(18)
            p.font.color.rgb = BRAND_PRIMARY
            p.font.bold = True
            p.space_before = Pt(16) if i > 0 else Pt(0)
            p.space_after = Pt(6)
        
        p.font.name = FONT_NAME

def _render_two_column(slide, content):
    """Two perfectly balanced columns with subtle background boxes."""
    # Left Column
    _draw_card(slide, Inches(0.5), Inches(1.5), Inches(6), Inches(5))
    l_box = slide.shapes.add_textbox(Inches(0.7), Inches(1.7), Inches(5.6), Inches(4.6))
    ltf = l_box.text_frame
    ltf.word_wrap = True
    lp = ltf.paragraphs[0]
    lp.text = content.get("left_title", "Left")
    lp.font.bold = True
    lp.font.size = Pt(20)
    lp.font.color.rgb = BRAND_PRIMARY
    lp.space_after = Pt(14)
    
    for item in content.get("left_items", []):
        p = ltf.add_paragraph()
        p.text = f"•  {item}"
        p.font.size = Pt(16)
        p.font.color.rgb = TEXT_DARK
        p.space_after = Pt(8)

    # Right Column
    _draw_card(slide, Inches(6.8), Inches(1.5), Inches(6), Inches(5))
    r_box = slide.shapes.add_textbox(Inches(7.0), Inches(1.7), Inches(5.6), Inches(4.6))
    rtf = r_box.text_frame
    rtf.word_wrap = True
    rp = rtf.paragraphs[0]
    rp.text = content.get("right_title", "Right")
    rp.font.bold = True
    rp.font.size = Pt(20)
    rp.font.color.rgb = BRAND_PRIMARY
    rp.space_after = Pt(14)
    
    for item in content.get("right_items", []):
        p = rtf.add_paragraph()
        p.text = f"•  {item}"
        p.font.size = Pt(16)
        p.font.color.rgb = TEXT_DARK
        p.space_after = Pt(8)

def _render_architecture_diagram(slide, content):
    """Embed a Graphviz-rendered PNG diagram into the slide, scaled to fit."""
    diagram_path = content.get("diagram_path")
    caption = content.get("caption", "Architecture Diagram")

    # Safe content region: leave room for header (~1.3") and footer+caption (~1.1")
    MAX_W = Inches(12.333)
    MAX_H = Inches(4.8)
    CONTENT_TOP = Inches(1.35)
    SLIDE_W = Inches(13.333)

    if diagram_path and os.path.exists(diagram_path):
        try:
            # --- Determine natural image aspect ratio ---
            img_w_px, img_h_px = None, None
            if _PIL_AVAILABLE:
                try:
                    with _PILImage.open(diagram_path) as im:
                        img_w_px, img_h_px = im.size
                except Exception:
                    pass

            # Fallback to 1024x768 since we generate 1024x768 images via OpenAI
            if not (img_w_px and img_h_px):
                img_w_px, img_h_px = 1024, 768

            img_aspect = img_w_px / img_h_px
            # Scale to fit MAX_W × MAX_H preserving aspect ratio
            pic_w = MAX_W
            pic_h = int(MAX_W / img_aspect)
            if pic_h > MAX_H:
                pic_h = MAX_H
                pic_w = int(MAX_H * img_aspect)

            # Center horizontally on the slide
            pic_left = (SLIDE_W - pic_w) // 2
            # Vertically center within content band
            pic_top = CONTENT_TOP + (MAX_H - pic_h) // 2

            slide.shapes.add_picture(diagram_path, pic_left, pic_top, pic_w, pic_h)
            w_in = round(pic_w / 914400, 2)
            h_in = round(pic_h / 914400, 2)
            logger.info(f"Embedded diagram ({w_in}in x {h_in}in) from {diagram_path}")
        except Exception as e:
            logger.error(f"Failed to embed diagram image: {e}")
            _diagram_placeholder(slide, caption)
    else:
        logger.warning(f"Diagram PNG not found at {diagram_path!r}; using placeholder.")
        _diagram_placeholder(slide, caption)

    # Caption below (fixed at bottom of content zone)
    cap_box = slide.shapes.add_textbox(Inches(0.5), Inches(6.4), Inches(12.333), Inches(0.45))
    cp = cap_box.text_frame.paragraphs[0]
    cp.text = caption
    cp.alignment = PP_ALIGN.CENTER
    cp.font.name = FONT_NAME
    cp.font.size = Pt(11)
    cp.font.color.rgb = TEXT_LIGHT
    cp.font.italic = True


def _diagram_placeholder(slide, caption):
    """Shaded placeholder shown when the diagram PNG is not available."""
    ph = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.5), Inches(1.4), Inches(12.333), Inches(5.0))
    ph.fill.solid()
    ph.fill.fore_color.rgb = BRAND_LIGHT
    ph.line.fill.background()
    tf = ph.text_frame
    p = tf.paragraphs[0]
    p.text = f"[ Architecture Diagram ]\n{caption}\n\nInsert generated PNG here."
    p.alignment = PP_ALIGN.CENTER
    p.font.color.rgb = BRAND_SECONDARY
    p.font.size = Pt(18)


def _render_component_detail(slide, content):
    """
    Renders a component detail slide with:
    - A description band at the top
    - A responsive grid of styled cards (supports 6+ components)
    - A column of checkmark highlights on the right
    """
    description = content.get("description", "")
    components  = content.get("components", [])  
    benefits    = content.get("benefits", [])
    principles  = content.get("principles", [])
    highlights  = benefits or principles

    # ── Description Banner ──────────────────────────────────────────────────
    if description:
        banner = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, Inches(1.2), Inches(13.333), Inches(0.65))
        banner.fill.solid()
        banner.fill.fore_color.rgb = BRAND_LIGHT
        banner.line.fill.background()
        tf = banner.text_frame
        tf.margin_left = Inches(0.4)
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = description
        p.font.name = FONT_NAME
        p.font.size = Pt(14)
        p.font.color.rgb = BRAND_PRIMARY
        p.font.italic = True

    # ── Component Cards ──────────────────────────────────────────────────────
    # Determine grid layout based on number of items
    items = components if components else []
    num_items = min(len(items), 9)
    
    # Use 2 columns for highlights panel, 3 columns if no highlights
    has_highlights = len(highlights) > 0
    if has_highlights:
        card_cols = 2
        card_w = Inches(3.8)
        x_start = Inches(0.5)
    else:
        card_cols = 3
        card_w = Inches(3.8)
        x_start = Inches(0.5)
    
    card_h = Inches(1.2)
    col_gap = Inches(0.25)
    row_gap = Inches(0.2)
    y_start = Inches(2.1)
    
    # Alternate colors for visual variety
    card_colors = [BRAND_PRIMARY, BRAND_SECONDARY, RGBColor(52, 73, 94), 
                   RGBColor(39, 174, 96), RGBColor(142, 68, 173), RGBColor(41, 128, 185)]

    for i, comp in enumerate(items[:num_items]):
        col = i % card_cols
        row = i // card_cols
        x = x_start + col * (card_w + col_gap)
        y = y_start + row * (card_h + row_gap)

        # Card background
        card_color = card_colors[i % len(card_colors)]
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, card_w, card_h)
        card.fill.solid()
        card.fill.fore_color.rgb = card_color
        card.line.fill.background()

        # Accent stripe on left
        stripe = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, Inches(0.06), card_h)
        stripe.fill.solid()
        stripe.fill.fore_color.rgb = ACCENT_GREEN
        stripe.line.fill.background()

        # Card text
        tf_box = slide.shapes.add_textbox(x + Inches(0.15), y + Inches(0.08), card_w - Inches(0.25), card_h - Inches(0.15))
        tf2 = tf_box.text_frame
        tf2.word_wrap = True

        if isinstance(comp, dict):
            name  = comp.get("name", "")
            layer = comp.get("layer", "")
            desc  = comp.get("description", "")
        else:
            name  = str(comp)
            layer = ""
            desc  = ""

        np = tf2.paragraphs[0]
        np.text = name
        np.font.name = FONT_NAME
        np.font.bold = True
        np.font.size = Pt(13)
        np.font.color.rgb = WHITE

        if layer:
            lp = tf2.add_paragraph()
            lp.text = f"[{layer}]"
            lp.font.name = FONT_NAME
            lp.font.size = Pt(9)
            lp.font.color.rgb = BRAND_LIGHT

        if desc:
            dp = tf2.add_paragraph()
            dp.text = desc[:100] + ("\u2026" if len(desc) > 100 else "")
            dp.font.name = FONT_NAME
            dp.font.size = Pt(10)
            dp.font.color.rgb = BRAND_LIGHT

    # ── Highlights Panel (right side) ─────────────────────────────────────────
    if highlights:
        panel_x = Inches(8.5)
        panel = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                       panel_x, Inches(2.0), Inches(4.4), Inches(5.0))
        panel.fill.solid()
        panel.fill.fore_color.rgb = BRAND_LIGHT
        panel.line.fill.background()

        h_box = slide.shapes.add_textbox(Inches(8.7), Inches(2.15), Inches(4.0), Inches(4.7))
        h_tf = h_box.text_frame
        h_tf.word_wrap = True

        title_p = h_tf.paragraphs[0]
        title_p.text = "KEY HIGHLIGHTS"
        title_p.font.name = FONT_NAME
        title_p.font.bold = True
        title_p.font.size = Pt(14)
        title_p.font.color.rgb = BRAND_PRIMARY
        title_p.space_after = Pt(10)

        for point in highlights[:8]:  # Support up to 8 highlights
            hp = h_tf.add_paragraph()
            hp.text = f"\u2713  {point}"
            hp.font.name = FONT_NAME
            hp.font.size = Pt(11)
            hp.font.color.rgb = ACCENT_GREEN
            hp.space_after = Pt(6)

def _render_table(slide, content):
    """Modern styled table with support for 3-4+ columns."""
    headers = content.get("headers", [])
    rows = content.get("rows", [])
    
    if not headers or not rows:
        return
    
    num_cols = len(headers)
    num_rows = len(rows) + 1  # +1 for header
    
    # Adjust font sizes based on content density
    header_font_size = Pt(13) if num_cols > 3 else Pt(14)
    cell_font_size = Pt(11) if num_cols > 3 else Pt(13)
    table_height = min(Inches(5.0), Inches(0.5 * num_rows))
    
    table_shape = slide.shapes.add_table(
        num_rows, num_cols,
        Inches(0.5), Inches(1.5), Inches(12.333), table_height
    ).table
    
    # Header row
    for col_idx, header in enumerate(headers):
        cell = table_shape.cell(0, col_idx)
        cell.text = header
        cell.fill.solid()
        cell.fill.fore_color.rgb = BRAND_PRIMARY
        p = cell.text_frame.paragraphs[0]
        p.font.bold = True
        p.font.color.rgb = WHITE
        p.font.name = FONT_NAME
        p.font.size = header_font_size
        cell.text_frame.margin_left = Inches(0.08)
        cell.text_frame.margin_top = Inches(0.04)
    
    # Data rows
    for row_idx, row in enumerate(rows, start=1):
        for col_idx, value in enumerate(row[:num_cols]):  # Guard against extra columns
            cell = table_shape.cell(row_idx, col_idx)
            cell.text = str(value)
            
            if row_idx % 2 == 0:
                cell.fill.solid()
                cell.fill.fore_color.rgb = BRAND_LIGHT
            else:
                cell.fill.solid()
                cell.fill.fore_color.rgb = WHITE
                
            p = cell.text_frame.paragraphs[0]
            p.font.color.rgb = TEXT_DARK
            p.font.name = FONT_NAME
            p.font.size = cell_font_size
            cell.text_frame.margin_left = Inches(0.08)
            cell.text_frame.margin_top = Inches(0.04)

def _render_timeline(slide, content):
    """Horizontal chevron-style timeline for phases."""
    phases = content.get("phases", [])
    num_phases = len(phases)
    if num_phases == 0: return
    
    width = 12.0 / num_phases
    
    for i, phase in enumerate(phases):
        x = Inches(0.6 + i * width)
        y = Inches(3.0)
        
        # Chevron
        shape = slide.shapes.add_shape(MSO_SHAPE.CHEVRON, x, y, Inches(width - 0.1), Inches(1.2))
        shape.fill.solid()
        shape.fill.fore_color.rgb = BRAND_PRIMARY if i % 2 == 0 else BRAND_SECONDARY
        shape.line.fill.background()
        
        tf = shape.text_frame
        p = tf.paragraphs[0]
        p.text = f"{phase.get('phase', '')}\n{phase.get('duration', '')}"
        p.font.bold = True
        p.font.color.rgb = WHITE
        p.alignment = PP_ALIGN.CENTER
        
        # Details below
        txt_box = slide.shapes.add_textbox(x, y + Inches(1.4), Inches(width - 0.2), Inches(2.0))
        txt_tf = txt_box.text_frame
        txt_tf.word_wrap = True
        
        dp = txt_tf.paragraphs[0]
        dp.text = phase.get('deliverables', '')
        dp.font.size = Pt(14)
        dp.font.color.rgb = TEXT_DARK
        
        tp = txt_tf.add_paragraph()
        tp.text = f"Team: {phase.get('team_size', '')}"
        tp.font.size = Pt(12)
        tp.font.color.rgb = TEXT_LIGHT
        tp.font.bold = True

def _render_org_chart(slide, content):
    """Visual hierarchy for team structure."""
    roles = content.get("roles", [])
    
    # Fake a hierarchy visually
    _draw_card(slide, Inches(5.16), Inches(1.5), Inches(3), Inches(1), BRAND_PRIMARY, WHITE)
    tbox = slide.shapes.add_textbox(Inches(5.16), Inches(1.7), Inches(3), Inches(0.8))
    tbox.text_frame.paragraphs[0].text = roles[0] if roles else "Lead"
    tbox.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
    tbox.text_frame.paragraphs[0].font.color.rgb = WHITE
    tbox.text_frame.paragraphs[0].font.bold = True
    
    # Connecting line
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(6.66), Inches(2.5), Inches(0.02), Inches(0.5))
    line.fill.solid()
    line.fill.fore_color.rgb = BRAND_PRIMARY
    line.line.fill.background()
    
    horiz_line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.5), Inches(3.0), Inches(10.33), Inches(0.02))
    horiz_line.fill.solid()
    horiz_line.fill.fore_color.rgb = BRAND_PRIMARY
    horiz_line.line.fill.background()
    
    # Subordinates
    sub_roles = roles[1:]
    if not sub_roles: return
    
    width = 10.33 / len(sub_roles)
    for i, role in enumerate(sub_roles):
        x = Inches(1.5 + (i * width))
        
        # Drop line
        dline = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x + Inches(width/2), Inches(3.0), Inches(0.02), Inches(0.5))
        dline.fill.solid()
        dline.fill.fore_color.rgb = BRAND_PRIMARY
        dline.line.fill.background()
        
        _draw_card(slide, x + Inches(0.1), Inches(3.5), Inches(width - 0.2), Inches(1), BRAND_SECONDARY, WHITE)
        rbox = slide.shapes.add_textbox(x + Inches(0.1), Inches(3.7), Inches(width - 0.2), Inches(0.8))
        rp = rbox.text_frame.paragraphs[0]
        rp.text = role
        rp.alignment = PP_ALIGN.CENTER
        rp.font.size = Pt(12)
        rp.font.bold = True
        rp.font.color.rgb = WHITE

def _render_case_studies(slide, content):
    """Grid of cards for case studies."""
    studies = content.get("case_studies", [])
    
    for i, study in enumerate(studies):
        x = Inches(0.6 + i * 4.1)
        y = Inches(2.0)
        
        _draw_card(slide, x, y, Inches(3.8), Inches(4.0))
        
        box = slide.shapes.add_textbox(x + Inches(0.2), y + Inches(0.2), Inches(3.4), Inches(3.6))
        tf = box.text_frame
        tf.word_wrap = True
        
        p = tf.paragraphs[0]
        p.text = study.get('client', '')
        p.font.bold = True
        p.font.size = Pt(20)
        p.font.color.rgb = BRAND_PRIMARY
        p.space_after = Pt(14)
        
        p2 = tf.add_paragraph()
        p2.text = "Project:\n" + study.get('project', '')
        p2.font.size = Pt(16)
        p2.font.color.rgb = TEXT_DARK
        p2.space_after = Pt(14)
        
        p3 = tf.add_paragraph()
        p3.text = "Outcome:\n" + study.get('outcome', '')
        p3.font.size = Pt(16)
        p3.font.color.rgb = ACCENT_GREEN
        p3.font.bold = True

def _render_closing(slide, content):
    """Closing thank you slide with full bleed background."""
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    bg.fill.solid()
    bg.fill.fore_color.rgb = BRAND_PRIMARY
    bg.line.fill.background()
    
    box = slide.shapes.add_textbox(Inches(1), Inches(2), Inches(11.333), Inches(4))
    tf = box.text_frame
    tf.word_wrap = True
    
    p = tf.paragraphs[0]
    p.text = content.get("message", "Thank You")
    p.font.name = FONT_NAME
    p.font.size = Pt(64)
    p.font.bold = True
    p.font.color.rgb = WHITE
    p.alignment = PP_ALIGN.CENTER
    p.space_after = Pt(20)
    
    p2 = tf.add_paragraph()
    p2.text = f"{content.get('invitation', '')}\n\n{content.get('contact', '')}"
    p2.font.name = FONT_NAME
    p2.font.size = Pt(24)
    p2.font.color.rgb = BRAND_LIGHT
    p2.alignment = PP_ALIGN.CENTER


def _draw_card(slide, left, top, width, height, bg_color=BRAND_LIGHT, border_color=BRAND_LIGHT):
    """Utility to draw a rounded card shape for modular UI."""
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = bg_color
    shape.line.fill.solid()
    shape.line.fill.fore_color.rgb = border_color
    return shape

if __name__ == "__main__":
    if os.path.exists("output/ppt_structure.json"):
        with open("output/ppt_structure.json", "r") as f:
            ppt_structure = json.load(f)
        render_ppt_from_json(ppt_structure, "output/Architecture_Proposal.pptx")
    else:
        logger.error("No ppt_structure.json found to test rendering.")
