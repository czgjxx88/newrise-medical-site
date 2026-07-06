#!/usr/bin/env python3
"""
常州申嘉金属制品有限公司 - A4 电子样册生成器
使用 ReportLab 生成专业 PDF 样册
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import Color, HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, Frame,
    BaseDocTemplate, PageTemplate, NextPageTemplate,
    FrameBreak, ListFlowable, ListItem
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
import os

# ============================================================
# 页面设置
# ============================================================
PAGE_W, PAGE_H = A4  # 210mm x 297mm
MARGIN = 20 * mm
CONTENT_W = PAGE_W - 2 * MARGIN

# ============================================================
# 颜色方案
# ============================================================
PRIMARY = HexColor("#1a3a5c")       # 深蓝
PRIMARY_LIGHT = HexColor("#2c5f8a")  # 亮蓝
ACCENT = HexColor("#e8832a")         # 橙色强调
DARK = HexColor("#222222")           # 深灰
MEDIUM = HexColor("#555555")         # 中灰
LIGHT = HexColor("#f5f7fa")          # 浅灰背景
WHITE = HexColor("#ffffff")
LIGHT_BLUE = HexColor("#e8f0f8")     # 淡蓝背景
ACCENT_LIGHT = HexColor("#fdf0e4")   # 淡橙背景

# ============================================================
# 字体注册
# ============================================================
# 查找系统中文支持字体
def find_chinese_font():
    # STHeiti works with ReportLab (trueType outlines)
    candidates = [
        ("STHeiti", [
            ("/System/Library/Fonts/STHeiti Medium.ttc", 0),
            ("/System/Library/Fonts/STHeiti Light.ttc", 0),
        ]),
        ("Heiti SC", []),
    ]
    
    for font_name, paths in candidates:
        # First try direct paths with subfont index
        for path_info in paths:
            if isinstance(path_info, tuple):
                path, subfont_idx = path_info
            else:
                path, subfont_idx = path_info, 0
            if os.path.exists(path):
                return font_name, path, subfont_idx
        
        # Then try fc-match
        try:
            import subprocess
            result = subprocess.run(
                ["fc-match", font_name, ":%{file}"],
                capture_output=True, text=True, timeout=5
            )
            font_path = result.stdout.strip()
            if font_path and os.path.exists(font_path):
                return font_name, font_path, 0
        except:
            pass
    
    return None, None, 0

font_name, font_path, subfont_idx = find_chinese_font()
print(f"Found font: {font_name} -> {font_path} (subfont={subfont_idx})")

if font_path:
    pdfmetrics.registerFont(TTFont("Chinese", font_path, subfontIndex=subfont_idx))
    # For bold, use Medium variant
    bold_path = None
    bold_idx = 0
    if "STHeiti" in font_name:
        if "Medium" not in font_path:
            bold_path = "/System/Library/Fonts/STHeiti Medium.ttc"
        else:
            bold_path = font_path  # Same path
        bold_idx = 0
    elif font_path.endswith(".ttc"):
        # Try to find bold in same TTC
        bold_path = font_path
        bold_idx = subfont_idx
    
    if bold_path and os.path.exists(bold_path):
        pdfmetrics.registerFont(TTFont("ChineseBold", bold_path, subfontIndex=bold_idx))
        print(f"Found bold: {bold_path}")
    else:
        pdfmetrics.registerFont(TTFont("ChineseBold", font_path, subfontIndex=subfont_idx))
    
    # Light variant
    light_path = None
    light_idx = 0
    if "STHeiti" in font_name:
        if "Light" not in font_path:
            light_path = "/System/Library/Fonts/STHeiti Light.ttc"
        else:
            light_path = font_path
        light_idx = 0
    
    if light_path and os.path.exists(light_path):
        pdfmetrics.registerFont(TTFont("ChineseLight", light_path, subfontIndex=light_idx))
    else:
        pdfmetrics.registerFont(TTFont("ChineseLight", font_path, subfontIndex=subfont_idx))
    
    MAIN_FONT = "Chinese"
    BOLD_FONT = "ChineseBold"
    LIGHT_FONT = "ChineseLight"
else:
    MAIN_FONT = "Helvetica"
    BOLD_FONT = "Helvetica-Bold"
    LIGHT_FONT = "Helvetica"

# ============================================================
# 样式定义
# ============================================================
styles = getSampleStyleSheet()

def ps(name, **kwargs):
    defaults = dict(
        fontName=MAIN_FONT,
        fontSize=10,
        leading=14,
        textColor=DARK,
        alignment=TA_LEFT,
        spaceBefore=0,
        spaceAfter=6,
    )
    defaults.update(kwargs)
    return ParagraphStyle(name, **defaults)

STYLES = {
    "title": ps("title",
        fontName=BOLD_FONT, fontSize=28, leading=36,
        textColor=WHITE, alignment=TA_CENTER,
        spaceBefore=10, spaceAfter=8),
    
    "subtitle": ps("subtitle",
        fontName=LIGHT_FONT, fontSize=14, leading=20,
        textColor=WHITE, alignment=TA_CENTER,
        spaceBefore=4, spaceAfter=6),
    
    "subtitle_dark": ps("subtitle_dark",
        fontName=LIGHT_FONT, fontSize=14, leading=20,
        textColor=PRIMARY, alignment=TA_CENTER,
        spaceBefore=4, spaceAfter=6),
    
    "section_title": ps("section_title",
        fontName=BOLD_FONT, fontSize=22, leading=28,
        textColor=PRIMARY, alignment=TA_LEFT,
        spaceBefore=8, spaceAfter=6),
    
    "section_title_en": ps("section_title_en",
        fontName=LIGHT_FONT, fontSize=11, leading=15,
        textColor=PRIMARY_LIGHT, alignment=TA_LEFT,
        spaceBefore=0, spaceAfter=10),
    
    "heading": ps("heading",
        fontName=BOLD_FONT, fontSize=14, leading=20,
        textColor=PRIMARY, alignment=TA_LEFT,
        spaceBefore=6, spaceAfter=4),
    
    "heading_accent": ps("heading_accent",
        fontName=BOLD_FONT, fontSize=14, leading=20,
        textColor=ACCENT, alignment=TA_LEFT,
        spaceBefore=6, spaceAfter=4),
    
    "body": ps("body",
        fontName=MAIN_FONT, fontSize=10, leading=16,
        textColor=DARK, alignment=TA_LEFT,
        spaceBefore=2, spaceAfter=4),
    
    "body_small": ps("body_small",
        fontName=MAIN_FONT, fontSize=9, leading=14,
        textColor=MEDIUM, alignment=TA_LEFT,
        spaceBefore=2, spaceAfter=3),
    
    "body_center": ps("body_center",
        fontName=MAIN_FONT, fontSize=10, leading=16,
        textColor=DARK, alignment=TA_CENTER,
        spaceBefore=2, spaceAfter=4),
    
    "caption": ps("caption",
        fontName=LIGHT_FONT, fontSize=9, leading=13,
        textColor=MEDIUM, alignment=TA_CENTER,
        spaceBefore=2, spaceAfter=2),
    
    "contact_label": ps("contact_label",
        fontName=BOLD_FONT, fontSize=11, leading=16,
        textColor=PRIMARY, alignment=TA_LEFT,
        spaceBefore=4, spaceAfter=2),
    
    "contact_value": ps("contact_value",
        fontName=MAIN_FONT, fontSize=12, leading=18,
        textColor=DARK, alignment=TA_LEFT,
        spaceBefore=0, spaceAfter=6),
    
    "stat_num": ps("stat_num",
        fontName=BOLD_FONT, fontSize=36, leading=42,
        textColor=ACCENT, alignment=TA_CENTER,
        spaceBefore=0, spaceAfter=2),
    
    "stat_label": ps("stat_label",
        fontName=BOLD_FONT, fontSize=11, leading=15,
        textColor=PRIMARY, alignment=TA_CENTER,
        spaceBefore=0, spaceAfter=2),
    
    "stat_desc": ps("stat_desc",
        fontName=LIGHT_FONT, fontSize=8, leading=12,
        textColor=MEDIUM, alignment=TA_CENTER,
        spaceBefore=0, spaceAfter=8),
    
    "product_name": ps("product_name",
        fontName=BOLD_FONT, fontSize=15, leading=20,
        textColor=PRIMARY, alignment=TA_LEFT,
        spaceBefore=6, spaceAfter=2),
    
    "product_name_en": ps("product_name_en",
        fontName=LIGHT_FONT, fontSize=9, leading=13,
        textColor=PRIMARY_LIGHT, alignment=TA_LEFT,
        spaceBefore=0, spaceAfter=4),
    
    "tag": ps("tag",
        fontName=MAIN_FONT, fontSize=8, leading=12,
        textColor=ACCENT, alignment=TA_LEFT,
        spaceBefore=0, spaceAfter=4),
    
    "footer": ps("footer",
        fontName=LIGHT_FONT, fontSize=7, leading=10,
        textColor=HexColor("#999999"), alignment=TA_CENTER,
        spaceBefore=0, spaceAfter=0),
    
    "value_title": ps("value_title",
        fontName=BOLD_FONT, fontSize=12, leading=16,
        textColor=PRIMARY, alignment=TA_LEFT,
        spaceBefore=4, spaceAfter=2),
    
    "value_title_en": ps("value_title_en",
        fontName=LIGHT_FONT, fontSize=8, leading=12,
        textColor=ACCENT, alignment=TA_LEFT,
        spaceBefore=0, spaceAfter=3),
    
    "divider": ps("divider",
        fontName=MAIN_FONT, fontSize=6, leading=6,
        textColor=LIGHT, alignment=TA_CENTER,
        spaceBefore=2, spaceAfter=2),
}

# ============================================================
# 页面背景绘制
# ============================================================
from reportlab.platypus.doctemplate import BaseDocTemplate, PageTemplate, Frame
from reportlab.lib.units import mm

class MyDocTemplate(BaseDocTemplate):
    pass

def cover_background(canvas, doc):
    canvas.saveState()
    # Full dark background
    canvas.setFillColor(PRIMARY)
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    # Decorative accent line at bottom
    canvas.setFillColor(ACCENT)
    canvas.rect(0, 0, PAGE_W, 6 * mm, fill=1, stroke=0)
    # Subtle decorative circle
    canvas.setFillColor(HexColor("#234d74"))
    canvas.circle(PAGE_W - 60*mm, PAGE_H - 40*mm, 50*mm, fill=1, stroke=0)
    canvas.setFillColor(HexColor("#265580"))
    canvas.circle(PAGE_W - 50*mm, PAGE_H - 50*mm, 35*mm, fill=1, stroke=0)
    canvas.restoreState()

def content_background(canvas, doc):
    canvas.saveState()
    # Header bar
    canvas.setFillColor(PRIMARY)
    canvas.rect(0, PAGE_H - 12*mm, PAGE_W, 12*mm, fill=1, stroke=0)
    # Accent line
    canvas.setFillColor(ACCENT)
    canvas.rect(0, PAGE_H - 12.5*mm, PAGE_W, 0.5*mm, fill=1, stroke=0)
    # Footer bar
    canvas.setFillColor(LIGHT)
    canvas.rect(0, 0, PAGE_W, 10*mm, fill=1, stroke=0)
    canvas.setStrokeColor(HexColor("#dddddd"))
    canvas.line(0, 10*mm, PAGE_W, 10*mm)
    # Footer text
    canvas.setFont(LIGHT_FONT if font_path else "Helvetica", 7)
    canvas.setFillColor(HexColor("#999999"))
    canvas.drawCentredString(PAGE_W/2, 4*mm, "常州申嘉金属制品有限公司  |  www.jscz-zm.com")
    canvas.restoreState()

def end_page_background(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(PRIMARY)
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    canvas.setFillColor(ACCENT)
    canvas.rect(0, PAGE_H - 6*mm, PAGE_W, 6*mm, fill=1, stroke=0)
    canvas.restoreState()

# ============================================================
# 辅助函数
# ============================================================
def colored_bg(content, color, padding=5*mm, border_radius=0):
    """Wrap content in a colored background box"""
    return content  # Simplified - we'll use table cells for backgrounds

def spacer(height=5*mm):
    return Spacer(1, height)

def line_separator(color=HexColor("#dddddd"), width=CONTENT_W, height=0.5*mm):
    t = Table([[Paragraph("", STYLES["divider"])]], 
              colWidths=[width], rowHeights=[height],
              hAlign='CENTER')
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), color),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    return t

def accent_box(content, width=CONTENT_W, bg_color=LIGHT_BLUE, padding=4*mm):
    """Create a content block with accent background"""
    if not isinstance(content, list):
        content = [content]
    t = Table([content], colWidths=[width - 2*padding])
    style_cmds = [
        ('BACKGROUND', (0,0), (-1,-1), bg_color),
        ('TOPPADDING', (0,0), (-1,-1), padding),
        ('BOTTOMPADDING', (0,0), (-1,-1), padding),
        ('LEFTPADDING', (0,0), (-1,-1), padding),
        ('RIGHTPADDING', (0,0), (-1,-1), padding),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LINEBELOW', (0,0), (-1,-1), 0, ACCENT),
    ]
    t.setStyle(TableStyle(style_cmds))
    return t

def stat_card(num, label, desc):
    """Create a stat card for company profile"""
    card_w = (CONTENT_W - 20*mm) / 3
    data = [
        [Paragraph(num, STYLES["stat_num"])],
        [Paragraph(label, STYLES["stat_label"])],
        [Paragraph(desc, STYLES["stat_desc"])],
    ]
    t = Table(data, colWidths=[card_w])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), WHITE),
        ('TOPPADDING', (0,0), (-1,-1), 12),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('ROUNDEDCORNERS', [2]),
    ]))
    return t

# ============================================================
# 构建文档内容
# ============================================================
def build_catalog():
    output_path = "/Users/lobster/workspace/lali/常州申嘉金属制品_电子样册.pdf"
    
    doc = MyDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
    )
    
    # Define page templates
    cover_frame = Frame(MARGIN, MARGIN, CONTENT_W, PAGE_H - 2*MARGIN)
    content_frame = Frame(MARGIN, 15*mm, CONTENT_W, PAGE_H - 30*mm)
    end_frame = Frame(MARGIN, MARGIN, CONTENT_W, PAGE_H - 2*MARGIN)
    
    doc.addPageTemplates([
        PageTemplate(id='Cover', frames=cover_frame, onPage=cover_background),
        PageTemplate(id='Content', frames=content_frame, onPage=content_background),
        PageTemplate(id='EndPage', frames=end_frame, onPage=end_page_background),
    ])
    
    story = []
    
    # ============================================================
    # PAGE 1: COVER
    # ============================================================
    story.append(NextPageTemplate('Content'))
    
    # Spacer for centering
    story.append(spacer(50*mm))
    
    # Company name
    story.append(Paragraph("常州申嘉金属制品有限公司", STYLES["title"]))
    story.append(spacer(6*mm))
    
    # English name
    story.append(Paragraph("CHANGZHOU SHENJIA METAL PRODUCTS CO., LTD.", 
                          ps("en_name", fontName=LIGHT_FONT, fontSize=12, leading=16,
                             textColor=HexColor("#a0c4e8"), alignment=TA_CENTER,
                             spaceBefore=0, spaceAfter=0)))
    story.append(spacer(12*mm))
    
    # Divider line
    story.append(Paragraph("━" * 30, ps("cover_divider", fontName=MAIN_FONT, fontSize=8, 
                                        leading=10, textColor=ACCENT, alignment=TA_CENTER)))
    story.append(spacer(10*mm))
    
    # Tagline
    story.append(Paragraph("专业制造 · 品质为先", 
                          ps("tagline", fontName=BOLD_FONT, fontSize=18, leading=26,
                             textColor=WHITE, alignment=TA_CENTER,
                             spaceBefore=0, spaceAfter=6)))
    story.append(spacer(4*mm))
    
    story.append(Paragraph("2026 年 公 司 概 况", 
                          ps("year", fontName=LIGHT_FONT, fontSize=13, leading=18,
                             textColor=HexColor("#a0c4e8"), alignment=TA_CENTER,
                             spaceBefore=0, spaceAfter=0)))
    
    # Bottom info
    story.append(spacer(40*mm))
    story.append(Paragraph("www.jscz-zm.com", 
                          ps("cover_url", fontName=LIGHT_FONT, fontSize=10, leading=14,
                             textColor=HexColor("#7baed4"), alignment=TA_CENTER)))
    
    story.append(PageBreak())
    
    # ============================================================
    # PAGE 2: MISSION
    # ============================================================
    story.append(Paragraph("我们的志向", STYLES["section_title"]))
    story.append(Paragraph("Our Mission", STYLES["section_title_en"]))
    story.append(spacer(6*mm))
    
    # Mission statement in a box
    mission_text = (
        "我们致力于生产高品质的不锈钢、铝制及冷凝排烟管道产品，通过专业的制造工艺与创新技术，"
        "为客户的厨房排烟和新风通风系统提供安全、可靠、高效的解决方案。"
    )
    mission_box = accent_box(
        [Paragraph(mission_text, ps("mission_body", fontName=MAIN_FONT, fontSize=12, leading=20,
                                     textColor=DARK, alignment=TA_JUSTIFY,
                                     spaceBefore=4, spaceAfter=4))],
        bg_color=LIGHT_BLUE, padding=6*mm
    )
    story.append(mission_box)
    story.append(spacer(12*mm))
    
    # Three pillars
    pillars = [
        ("专业制造", "专注排烟管领域深耕"),
        ("品质为先", "质量体系认证专利保障"),
        ("客户至上", "安全可靠的产品交付"),
    ]
    
    for title, desc in pillars:
        # Number bullet
        num_data = [[Paragraph("●", ps("bullet", fontName=MAIN_FONT, fontSize=16, 
                                        leading=20, textColor=ACCENT, alignment=TA_CENTER))]]
        num_t = Table(num_data, colWidths=[20*mm])
        num_t.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('TOPPADDING', (0,0), (-1,-1), 4),
        ]))
        
        text_data = [
            [Paragraph(title, ps("pillar_title", fontName=BOLD_FONT, fontSize=14, leading=18,
                                 textColor=PRIMARY, alignment=TA_LEFT))],
            [Paragraph(desc, ps("pillar_desc", fontName=MAIN_FONT, fontSize=11, leading=16,
                                textColor=MEDIUM, alignment=TA_LEFT))],
        ]
        text_t = Table(text_data, colWidths=[CONTENT_W - 28*mm])
        text_t.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('TOPPADDING', (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
        ]))
        
        combo = Table([[num_t, text_t]], colWidths=[20*mm, CONTENT_W - 28*mm])
        combo.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ]))
        story.append(combo)
    
    story.append(PageBreak())
    
    # ============================================================
    # PAGE 3: COMPANY PROFILE
    # ============================================================
    story.append(Paragraph("常州申嘉概况", STYLES["section_title"]))
    story.append(Paragraph("Company Profile 2026", STYLES["section_title_en"]))
    story.append(spacer(10*mm))
    
    # Stats grid
    stats = [
        ("多年深耕", "成立多年", "深耕排烟管行业"),
        ("多项认证", "ISO / 专利", "质量管理体系 + 实用新型专利"),
        ("三大品类", "核心产品", "不锈钢 / 铝制 / 冷凝排烟管"),
        ("全尺寸覆盖", "规格齐全", "口径80-350mm / 长度1-5米"),
        ("便捷安装", "配套灵活", "可选配钢头 / 塑料接头"),
        ("行业领先", "创新突破", "防脱节设计填补行业空白"),
    ]
    
    stat_table_data = []
    for i, (title, subtitle, desc) in enumerate(stats):
        col = i % 2
        row = i // 2
        if col == 0:
            stat_table_data.append([None, None])  # Start new row
        
        stat_content = Paragraph(
            f"<b><font color='#1a3a5c' size=14>{title}</font></b><br/>"
            f"<font color='#2c5f8a' size=9>{subtitle}</font><br/>"
            f"<font color='#555555' size=8>{desc}</font>",
            ps(f"stat{i}", fontName=MAIN_FONT, fontSize=10, leading=14,
               textColor=DARK, alignment=TA_CENTER, spaceBefore=6, spaceAfter=6)
        )
        
        stat_table_data[row][col] = stat_content
    
    if stat_table_data:
        # Fill incomplete last row
        if len(stat_table_data[-1]) < 2:
            stat_table_data[-1].append(Paragraph("", STYLES["body"]))
        
        col_w = (CONTENT_W - 12*mm) / 2
        bg_cmds = []
        for r in range(len(stat_table_data)):
            for c in range(2):
                bg = WHITE if (c+r) % 2 == 0 else LIGHT
                bg_cmds.append(('BACKGROUND', (c, r), (c, r), bg))
        
        stat_table = Table(stat_table_data, colWidths=[col_w, col_w], rowHeights=55*mm)
        stat_table.setStyle(TableStyle(bg_cmds + [
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
            ('RIGHTPADDING', (0,0), (-1,-1), 10),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ]))
        story.append(stat_table)
    
    story.append(PageBreak())
    
    # ============================================================
    # PAGE 4: CORPORATE VALUES
    # ============================================================
    story.append(Paragraph("企业核心价值观", STYLES["section_title"]))
    story.append(Paragraph("Corporate Values", STYLES["section_title_en"]))
    story.append(spacer(8*mm))
    
    values = [
        ("品质为本", "Quality First", "以质量管理为基石，每项产品均通过体系认证，用专利保障品质。"),
        ("持续创新", "Innovation", "防脱节设计填补行业空白，不断优化焊接工艺与产品结构。"),
        ("客户至上", "Customer Focus", "以客户需求为导向，提供安全、可靠、高效的排烟通风方案。"),
        ("专业专注", "Professionalism", "深耕金属排烟管领域，专业生产不锈钢、铝制、冷凝排烟管道。"),
        ("合作共赢", "Win-Win", "与客户、合作伙伴建立长期互信关系，共享发展成果。"),
    ]
    
    for title, en, desc in values:
        # Value card
        value_data = [
            [Paragraph(title, STYLES["value_title"]),
             Paragraph(en, STYLES["value_title_en"])],
            [Paragraph(desc, ps("value_desc", fontName=MAIN_FONT, fontSize=10, leading=15,
                               textColor=DARK, alignment=TA_LEFT, spaceBefore=2, spaceAfter=0)),
             None],
        ]
        
        value_table = Table(value_data, colWidths=[CONTENT_W - 12*mm])
        value_table.setStyle(TableStyle([
            ('SPAN', (0,0), (1,0)),
            ('SPAN', (0,1), (1,1)),
            ('BACKGROUND', (0,0), (-1,-1), WHITE),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
            ('RIGHTPADDING', (0,0), (-1,-1), 10),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LINEABOVE', (0,0), (-1,0), 2, ACCENT),
        ]))
        story.append(value_table)
        story.append(spacer(2*mm))
    
    story.append(PageBreak())
    
    # ============================================================
    # PAGE 5-6: CORE PRODUCTS
    # ============================================================
    story.append(Paragraph("核心产品", STYLES["section_title"]))
    story.append(Paragraph("Core Products", STYLES["section_title_en"]))
    story.append(spacer(6*mm))
    
    products = [
        {
            "name": "纯铝伸缩管",
            "en": "Pure Aluminum Telescopic Tube",
            "desc": "防脱节设计 · 焊接牢固超强稳定性 · 伸缩静音耐高温低温 · 防渗漏",
            "spec": "口径 80-350mm  |  长度 1-5m",
        },
        {
            "name": "不锈钢排烟管",
            "en": "Stainless Steel Exhaust Pipe",
            "desc": "耐腐蚀 · 使用寿命长 · 高强度 · 安全可靠 · 适用多种场景",
            "spec": "口径 80-350mm  |  长度 1-5m",
        },
        {
            "name": "冷凝排烟管",
            "en": "Condensing Exhaust Pipe",
            "desc": "高效冷凝 · 节能环保 · 密封性好 · 运行稳定 · 适配冷凝锅炉",
            "spec": "口径 80-350mm  |  长度 1-5m",
        },
    ]
    
    for p in products:
        # Product header
        prod_header = Table([
            [Paragraph(p["name"], STYLES["product_name"])],
            [Paragraph(p["en"], STYLES["product_name_en"])],
            [Paragraph(p["desc"], ps("prod_desc", fontName=MAIN_FONT, fontSize=10, leading=15,
                                     textColor=MEDIUM, alignment=TA_LEFT, spaceBefore=4, spaceAfter=4))],
            [Paragraph(p["spec"], ps("prod_spec", fontName=BOLD_FONT, fontSize=10, leading=14,
                                     textColor=ACCENT, alignment=TA_LEFT, spaceBefore=2, spaceAfter=6))],
        ], colWidths=[CONTENT_W - 8*mm])
        prod_header.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), LIGHT_BLUE),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('LEFTPADDING', (0,0), (-1,-1), 12),
            ('RIGHTPADDING', (0,0), (-1,-1), 12),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LINEBELOW', (0,0), (-1,-1), 1, HexColor("#c0d8ec")),
        ]))
        story.append(prod_header)
        story.append(spacer(4*mm))
    
    # Add features comparison table
    story.append(spacer(8*mm))
    story.append(Paragraph("产品特性对比", ps("comp_title", fontName=BOLD_FONT, fontSize=14, leading=18,
                                              textColor=PRIMARY, alignment=TA_LEFT)))
    story.append(spacer(4*mm))
    
    comp_data = [
        [
            Paragraph("<b>特性</b>", ps("comp_h", fontName=BOLD_FONT, fontSize=9, leading=12,
                                       textColor=WHITE, alignment=TA_CENTER)),
            Paragraph("<b>纯铝伸缩管</b>", ps("comp_h", fontName=BOLD_FONT, fontSize=9, leading=12,
                                              textColor=WHITE, alignment=TA_CENTER)),
            Paragraph("<b>不锈钢排烟管</b>", ps("comp_h", fontName=BOLD_FONT, fontSize=9, leading=12,
                                                textColor=WHITE, alignment=TA_CENTER)),
            Paragraph("<b>冷凝排烟管</b>", ps("comp_h", fontName=BOLD_FONT, fontSize=9, leading=12,
                                              textColor=WHITE, alignment=TA_CENTER)),
        ],
        [
            Paragraph("防脱节", STYLES["body_small"]),
            Paragraph("✓", ps("check", fontName=MAIN_FONT, fontSize=12, leading=16,
                              textColor=ACCENT, alignment=TA_CENTER)),
            Paragraph("—", STYLES["body_small"]),
            Paragraph("—", STYLES["body_small"]),
        ],
        [
            Paragraph("耐腐蚀", STYLES["body_small"]),
            Paragraph("✓", ps("check", fontName=MAIN_FONT, fontSize=12, leading=16,
                              textColor=ACCENT, alignment=TA_CENTER)),
            Paragraph("✓", ps("check", fontName=MAIN_FONT, fontSize=12, leading=16,
                              textColor=ACCENT, alignment=TA_CENTER)),
            Paragraph("✓", ps("check", fontName=MAIN_FONT, fontSize=12, leading=16,
                              textColor=ACCENT, alignment=TA_CENTER)),
        ],
        [
            Paragraph("耐高温", STYLES["body_small"]),
            Paragraph("✓", ps("check", fontName=MAIN_FONT, fontSize=12, leading=16,
                              textColor=ACCENT, alignment=TA_CENTER)),
            Paragraph("✓", ps("check", fontName=MAIN_FONT, fontSize=12, leading=16,
                              textColor=ACCENT, alignment=TA_CENTER)),
            Paragraph("✓", ps("check", fontName=MAIN_FONT, fontSize=12, leading=16,
                              textColor=ACCENT, alignment=TA_CENTER)),
        ],
        [
            Paragraph("适配冷凝锅炉", STYLES["body_small"]),
            Paragraph("—", STYLES["body_small"]),
            Paragraph("—", STYLES["body_small"]),
            Paragraph("✓", ps("check", fontName=MAIN_FONT, fontSize=12, leading=16,
                              textColor=ACCENT, alignment=TA_CENTER)),
        ],
    ]
    
    col_w2 = (CONTENT_W - 2*mm) / 4
    comp_table = Table(comp_data, colWidths=[col_w2, col_w2, col_w2, col_w2])
    comp_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('BACKGROUND', (0,1), (-1,-1), LIGHT),
        ('TEXTCOLOR', (0,0), (-1,0), WHITE),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('LINEBELOW', (0,0), (-1,-1), 0.5, HexColor("#dddddd")),
        ('GRID', (0,0), (-1,-1), 0.5, HexColor("#dddddd")),
    ]))
    story.append(comp_table)
    
    story.append(PageBreak())
    
    # ============================================================
    # PAGE 7: APPLICATION SCENARIOS
    # ============================================================
    story.append(Paragraph("应用场景", STYLES["section_title"]))
    story.append(Paragraph("Application Scenarios", STYLES["section_title_en"]))
    story.append(spacer(8*mm))
    
    scenarios = [
        ("🔥", "吸油烟机排烟", "高效排烟，确保厨房空气清新。纯铝材质耐腐蚀，使用寿命长久。"),
        ("🌬️", "新风系统通气", "稳定通风，保障室内空气质量。结构稳固，伸缩平稳无噪音。"),
        ("🔧", "冷凝锅炉配套", "适配冷凝锅炉排烟需求。密封防渗漏，运行安全可靠。"),
    ]
    
    for icon, title, desc in scenarios:
        scenario_data = [
            [Paragraph(title, STYLES["heading"]),],
            [Paragraph(desc, ps("scenario_desc", fontName=MAIN_FONT, fontSize=10, leading=15,
                               textColor=DARK, alignment=TA_LEFT, spaceBefore=2, spaceAfter=4))],
        ]
        scenario_table = Table(scenario_data, colWidths=[CONTENT_W - 6*mm])
        scenario_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), WHITE),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LEFTPADDING', (0,0), (-1,-1), 12),
            ('RIGHTPADDING', (0,0), (-1,-1), 12),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LINEABOVE', (0,0), (-1,0), 3, ACCENT),
        ]))
        story.append(scenario_table)
        story.append(spacer(3*mm))
    
    # Market advantage box
    story.append(spacer(8*mm))
    story.append(Paragraph("市场优势", STYLES["heading_accent"]))
    story.append(spacer(4*mm))
    
    advantage_text = (
        "作为铝伸缩管行业的创新之作，申嘉纯铝伸缩管凭借独特的防脱节设计和卓越性能，"
        "彻底颠覆传统使用体验，为用户提供安全、可靠、高效的新选择。"
    )
    adv_box = accent_box(
        [Paragraph(advantage_text, ps("adv_body", fontName=MAIN_FONT, fontSize=10, leading=16,
                                       textColor=DARK, alignment=TA_JUSTIFY,
                                       spaceBefore=2, spaceAfter=2))],
        bg_color=ACCENT_LIGHT, padding=6*mm
    )
    story.append(adv_box)
    
    story.append(PageBreak())
    
    # ============================================================
    # PAGE 8: CERTIFICATIONS & CONTACT (End Page)
    # ============================================================
    story.append(NextPageTemplate('EndPage'))
    
    story.append(Paragraph("资质与认证", STYLES["section_title"]))
    story.append(Paragraph("Certifications & Patents", STYLES["section_title_en"]))
    story.append(spacer(8*mm))
    
    certs = [
        ("质量管理体系认证", "QUALITY MANAGEMENT SYSTEM", "通过体系认证，确保产品质量一致性"),
        ("实用新型专利 — 防脱节设计", "Utility Model Patent", "先进焊接工艺，牢固连接，拉扯不脱节"),
        ("实用新型专利 — 结构优化", "Utility Model Patent", "增强抗拉强度，使用更可靠"),
        ("行业创新标准", "Industry Innovation", "填补不脱节技术空白，树立行业新标杆"),
    ]
    
    for title, en, desc in certs:
        cert_data = [
            [Paragraph(title, STYLES["heading"])],
            [Paragraph(en, ps("cert_en", fontName=LIGHT_FONT, fontSize=8, leading=12,
                              textColor=ACCENT, alignment=TA_LEFT, spaceBefore=0, spaceAfter=2))],
            [Paragraph(desc, ps("cert_desc", fontName=MAIN_FONT, fontSize=9, leading=14,
                               textColor=MEDIUM, alignment=TA_LEFT, spaceBefore=0, spaceAfter=4))],
        ]
        cert_table = Table(cert_data, colWidths=[CONTENT_W - 6*mm])
        cert_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), WHITE),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
            ('RIGHTPADDING', (0,0), (-1,-1), 10),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LINEABOVE', (0,0), (-1,0), 2, PRIMARY_LIGHT),
        ]))
        story.append(cert_table)
        story.append(spacer(2*mm))
    
    # Contact section
    story.append(spacer(12*mm))
    story.append(Paragraph("━━━━━━━━━━━━━━━━━━", ps("div2", fontName=MAIN_FONT, fontSize=6,
                                                leading=8, textColor=HexColor("#cccccc"),
                                                alignment=TA_CENTER)))
    story.append(spacer(6*mm))
    story.append(Paragraph("联系我们", STYLES["section_title"]))
    story.append(spacer(6*mm))
    
    contacts = [
        ("📞  电话", "18115023070  /  13057171394"),
        ("📧  邮箱", "czshenjia@163.com"),
        ("🌐  网址", "www.jscz-zm.com"),
        ("📍  地址", "江苏省常州市金坛经济开发区兴辰路8号"),
    ]
    
    contact_data = []
    for label, value in contacts:
        contact_data.append([
            Paragraph(label, STYLES["contact_label"]),
        ])
        contact_data.append([
            Paragraph(value, STYLES["contact_value"]),
        ])
    
    contact_table = Table(contact_data, colWidths=[CONTENT_W - 8*mm])
    contact_table.setStyle(TableStyle([
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(contact_table)
    
    story.append(spacer(12*mm))
    story.append(Paragraph("感谢您的关注", ps("thanks", fontName=BOLD_FONT, fontSize=20, leading=28,
                                              textColor=WHITE, alignment=TA_CENTER)))
    story.append(Paragraph("Thank You", ps("thanks_en", fontName=LIGHT_FONT, fontSize=14, leading=20,
                                           textColor=HexColor("#a0c4e8"), alignment=TA_CENTER)))
    
    story.append(spacer(8*mm))
    
    # Build
    doc.build(story)
    print(f"PDF generated: {output_path}")
    return output_path

if __name__ == "__main__":
    build_catalog()
