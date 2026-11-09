"""Build the Word/PDF report for RGR No. 3, task 1."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pandas as pd
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import (
    WD_ALIGN_PARAGRAPH,
    WD_TAB_ALIGNMENT,
    WD_TAB_LEADER,
)
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "rgr3"
DATA = BASE / "data"
FIG = BASE / "figures"
REPORT_DIR = BASE / "report"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

# Title-page fields: replace with your own data if needed.
STUDENT = "Дрозд Егор Павлович"
COURSE = "3"
GROUP = "12"

TOC_ENTRIES = [
    "ВВЕДЕНИЕ",
    "ЗАДАНИЕ 1. ВЕКТОРНАЯ МОДЕЛЬ ТЕКСТА",
    "ЗАКЛЮЧЕНИЕ",
    "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ",
]


def fmt(value: float, digits: int = 3) -> str:
    return f"{value:.{digits}f}".replace(".", ",")


def fmt_int(value: int | float) -> str:
    return f"{int(round(value)):,}".replace(",", " ")


def set_run_font(run, size=14, bold=False, italic=False, name="Times New Roman"):
    run.bold = bold
    run.italic = italic
    run.font.size = Pt(size)
    run.font.name = name
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rfonts.set(qn(attr), name)


def add_para(
    doc,
    text="",
    size=14,
    bold=False,
    italic=False,
    align=WD_ALIGN_PARAGRAPH.JUSTIFY,
    indent=True,
    before=0,
    after=0,
    keep=False,
    line=18,
):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.first_line_indent = Cm(1.25) if indent else Cm(0)
    pf.line_spacing = Pt(line)
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.alignment = align
    pf.keep_with_next = keep
    if text:
        r = p.add_run(text)
        set_run_font(r, size=size, bold=bold, italic=italic)
    return p


def add_heading(doc, text, page_break=True):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.first_line_indent = Cm(0)
    pf.line_spacing = Pt(18)
    pf.space_before = Pt(0)
    pf.space_after = Pt(36)
    pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf.keep_with_next = True
    pf.page_break_before = page_break
    r = p.add_run(text.upper())
    set_run_font(r, size=16, bold=True)
    return p


def add_subheading(doc, text):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.first_line_indent = Cm(1.25)
    pf.line_spacing = Pt(18)
    pf.space_before = Pt(12)
    pf.space_after = Pt(6)
    pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
    pf.keep_with_next = True
    r = p.add_run(text)
    set_run_font(r, size=14, bold=True)
    return p


def add_formula(doc, text):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.first_line_indent = Cm(0)
    pf.line_spacing = Pt(18)
    pf.space_before = Pt(6)
    pf.space_after = Pt(6)
    pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(text)
    set_run_font(r, size=14, italic=True)
    return p


def add_bullet(doc, text):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.first_line_indent = Cm(0)
    pf.left_indent = Cm(1.25)
    pf.line_spacing = Pt(18)
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    r = p.add_run("— " + text)
    set_run_font(r, size=14)
    return p


def add_table(
    doc,
    caption,
    headers,
    rows,
    widths=None,
    font_size=11,
    keep_together=None,
    page_break=False,
):
    cap = doc.add_paragraph()
    cf = cap.paragraph_format
    cf.first_line_indent = Cm(0)
    cf.line_spacing = Pt(18)
    cf.space_before = Pt(6)
    cf.space_after = Pt(3)
    cf.alignment = WD_ALIGN_PARAGRAPH.LEFT
    cf.keep_with_next = True
    cf.page_break_before = page_break
    r = cap.add_run(caption)
    set_run_font(r, size=12, bold=True)

    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    tr_pr = table.rows[0]._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)

    for i, header in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = ""
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.line_spacing = Pt(12)
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        rr = p.add_run(str(header))
        set_run_font(rr, size=font_size, bold=True)

    for row in rows:
        cells = table.add_row().cells
        for i, value in enumerate(row):
            p = cells[i].paragraphs[0]
            p.paragraph_format.first_line_indent = Cm(0)
            p.paragraph_format.line_spacing = Pt(12)
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            rr = p.add_run(str(value))
            set_run_font(rr, size=font_size)

    if widths:
        for i, width in enumerate(widths):
            table.columns[i].width = Cm(width)
        for row in table.rows:
            for i, width in enumerate(widths):
                row.cells[i].width = Cm(width)

        tbl_pr = table._tbl.tblPr
        tbl_w = tbl_pr.find(qn("w:tblW"))
        if tbl_w is None:
            tbl_w = OxmlElement("w:tblW")
            tbl_pr.append(tbl_w)
        tbl_w.set(qn("w:type"), "dxa")
        tbl_w.set(qn("w:w"), str(int(Cm(sum(widths)).twips)))
        layout = OxmlElement("w:tblLayout")
        layout.set(qn("w:type"), "fixed")
        tbl_pr.append(layout)

    for row in table.rows:
        tr_pr = row._tr.get_or_add_trPr()
        tr_pr.append(OxmlElement("w:cantSplit"))

    if keep_together is None:
        keep_together = len(rows) <= 15
    if keep_together:
        for row in table.rows[:-1]:
            for cell in row.cells:
                for p in cell.paragraphs:
                    p.paragraph_format.keep_with_next = True
    return table


def add_figure(doc, path, caption, width_cm=16.5, page_break=False):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.first_line_indent = Cm(0)
    pf.line_spacing = 1.0
    pf.space_before = Pt(6)
    pf.space_after = Pt(3)
    pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf.keep_together = True
    pf.keep_with_next = True
    pf.page_break_before = page_break
    r = p.add_run()
    r.add_picture(str(path), width=Cm(width_cm))

    cap = doc.add_paragraph()
    cf = cap.paragraph_format
    cf.first_line_indent = Cm(0)
    cf.line_spacing = Pt(18)
    cf.space_before = Pt(0)
    cf.space_after = Pt(18)
    cf.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cf.keep_together = True
    rr = cap.add_run(caption)
    set_run_font(rr, size=12, bold=True)
    return p


def add_page_number_footer(section):
    footer = section.footer
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    run = p.add_run()
    fld_char = OxmlElement("w:fldChar")
    fld_char.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run._r.append(fld_char)
    run._r.append(instr)
    run._r.append(fld_end)
    set_run_font(run, size=12)


def setup_document():
    doc = Document()
    section = doc.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.0)
    section.bottom_margin = Cm(2.0)
    section.left_margin = Cm(3.0)
    section.right_margin = Cm(1.0)
    section.different_first_page_header_footer = True
    add_page_number_footer(section)

    style = doc.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(14)
    rpr = style.element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rfonts.set(qn(attr), "Times New Roman")
    pf = style.paragraph_format
    pf.line_spacing = Pt(18)
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    pf.first_line_indent = Cm(1.25)
    pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    return doc


def add_title_page(doc):
    def centered(text, **kwargs):
        p = add_para(
            doc,
            text,
            align=WD_ALIGN_PARAGRAPH.CENTER,
            indent=False,
            **kwargs,
        )
        p.paragraph_format.left_indent = Cm(0)
        p.paragraph_format.right_indent = Cm(2.0)
        return p

    centered("Белорусский государственный университет")
    centered("Факультет прикладной математики и информатики")
    add_para(doc, "", indent=False)
    centered("Кафедра информационных систем управления")
    add_para(doc, "", indent=False, before=60)
    centered("РАСЧЕТНО-ГРАФИЧЕСКАЯ РАБОТА № 3", size=16, bold=True, before=30)
    centered("Векторная модель текста", size=14, before=12)
    add_para(doc, "", indent=False, before=100)
    for line in ["Выполнил:", f"студент {COURSE} курса {GROUP} группы", STUDENT]:
        p = add_para(doc, line, align=WD_ALIGN_PARAGRAPH.LEFT, indent=False)
        p.paragraph_format.left_indent = Cm(7.5)
    add_para(doc, "", indent=False, before=150)
    centered("Минск, 2026")


def add_toc(doc, pages=None):
    pages = pages or {}
    add_heading(doc, "СОДЕРЖАНИЕ", page_break=True)
    for title in TOC_ENTRIES:
        p = doc.add_paragraph()
        pf = p.paragraph_format
        pf.first_line_indent = Cm(0)
        pf.line_spacing = Pt(18)
        pf.space_before = Pt(0)
        pf.space_after = Pt(0)
        pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
        pf.tab_stops.add_tab_stop(
            Cm(16.5), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS
        )
        page = str(pages.get(title, "00"))
        r = p.add_run(title + "\t" + page)
        set_run_font(r, size=14)


def build_report(path: Path, pages=None):
    results = json.loads((DATA / "task1_results.json").read_text(encoding="utf-8"))
    summary = pd.read_csv(DATA / "task1_summary.csv")

    doc = setup_document()
    add_title_page(doc)
    add_toc(doc, pages)

    # ---------------- ВВЕДЕНИЕ ----------------
    add_heading(doc, "ВВЕДЕНИЕ", page_break=True)
    add_para(
        doc,
        "Цель работы — построить векторные модели текстов на основе "
        "мультимножества слов для русского и английского языков и сравнить "
        "тексты с помощью меры сходства.",
    )
    add_para(
        doc,
        "Исходные данные — по два текста из корпуса, собранного в работе №1. "
        "Корпус построен по датасету wikimedia/wikipedia версии 20231101. "
        "Для русского языка выбраны статьи «Литва» и «Кавказские Минеральные "
        "Воды», для английского — «Anarchism» и «Ayn Rand». Пары текстов "
        "близки по размеру, что позволяет корректно сравнивать векторные "
        "модели. Характеристики текстов приведены в таблице 1.",
    )
    add_table(
        doc,
        "Таблица 1 – Исходные тексты",
        ["Язык", "Текст 1", "Текст 2", "Слов в тексте 1", "Слов в тексте 2"],
        [
            ["Русский", "Литва", "Кавказские Минеральные Воды", "5 908", "5 737"],
            ["Английский", "Anarchism", "Ayn Rand", "6 712", "6 230"],
        ],
        widths=[2.6, 3.4, 4.8, 2.8, 2.8],
    )
    add_para(
        doc,
        "Для реализации использовались язык Python и библиотеки simplemma "
        "(лемматизация), NumPy (векторные операции), pandas (таблицы) и "
        "Matplotlib (график). Все вычисления воспроизводятся в ноутбуке "
        "01_vector_models.ipynb и модуле vector_model.py.",
    )
    add_para(
        doc,
        "В задании 1 необходимо выполнить токенизацию, нормализацию, удаление "
        "стоп-слов, построить модели one-hot encoding и TF, определить "
        "пересечение мультимножеств для one-hot модели и найти косинусный "
        "коэффициент для TF модели.",
    )

    # ---------------- ЗАДАНИЕ 1 ----------------
    add_heading(doc, "ЗАДАНИЕ 1. ВЕКТОРНАЯ МОДЕЛЬ ТЕКСТА", page_break=True)
    add_para(
        doc,
        "Векторная модель представляет текст в виде вектора признаков. В "
        "качестве признаков используются слова, входящие в общий словарь пары "
        "текстов. Мультимножество слов учитывает не только наличие слова, но и "
        "число его вхождений в текст.",
    )

    add_subheading(doc, "1.1 Токенизация")
    add_para(
        doc,
        "Токенизация — разбиение текста на слова. Для русского языка "
        "использовалось регулярное выражение [а-яё]+, для английского — [a-z]+. "
        "Перед токенизацией удалялись знаки ударения, которые встречаются в "
        "русской Википедии, и все буквы приводились к нижнему регистру. "
        "Результаты токенизации приведены в таблице 2.",
    )
    token_rows = []
    for lang, label in (("ru", "Русский"), ("en", "Английский")):
        for text in results[lang]["texts"]:
            token_rows.append(
                [
                    text["title"],
                    label,
                    fmt_int(text["raw_tokens"]),
                    fmt_int(text["raw_unique_tokens"]),
                ]
            )
    add_table(
        doc,
        "Таблица 2 – Результаты токенизации",
        ["Текст", "Язык", "Токенов", "Уникальных токенов"],
        token_rows,
        widths=[5.0, 3.0, 4.2, 4.2],
    )

    add_subheading(doc, "1.2 Нормализация текста")
    add_para(
        doc,
        "В качестве нормализации применялась лемматизация библиотекой "
        "simplemma: словоформы приводились к начальной форме. Например, "
        "«Литвы» → «литва», «running» → «run», «was» → «be». Это уменьшает "
        "размер словаря и объединяет разные формы одного слова. Результаты "
        "нормализации приведены в таблице 3.",
    )
    norm_rows = []
    for lang, label in (("ru", "Русский"), ("en", "Английский")):
        for text in results[lang]["texts"]:
            norm_rows.append(
                [
                    text["title"],
                    label,
                    fmt_int(text["normalized_tokens"]),
                    fmt_int(text["normalized_unique_tokens"]),
                ]
            )
    add_table(
        doc,
        "Таблица 3 – Результаты лемматизации",
        ["Текст", "Язык", "Токенов после лемматизации", "Уникальных лемм"],
        norm_rows,
        widths=[5.0, 3.0, 4.2, 4.2],
    )

    add_subheading(doc, "1.3 Удаление стоп-слов")
    add_para(
        doc,
        "Из текстов удалялись стоп-слова: предлоги, союзы, частицы, "
        "местоимения, вспомогательные глаголы и другие служебные слова. "
        "Использовался список служебных слов из РГР №2, который также "
        "лемматизировался, чтобы удалялись все словоформы. Дополнительно "
        "удалялись одиночные буквы — артефакты токенизации. Результаты "
        "фильтрации приведены в таблице 4.",
    )
    stop_rows = []
    for lang, label in (("ru", "Русский"), ("en", "Английский")):
        for text in results[lang]["texts"]:
            stop_rows.append(
                [
                    text["title"],
                    label,
                    fmt_int(text["tokens_after_stopwords"]),
                    fmt_int(text["unique_tokens"]),
                ]
            )
    add_table(
        doc,
        "Таблица 4 – Результаты удаления стоп-слов",
        ["Текст", "Язык", "Токенов после стоп-слов", "Уникальных слов"],
        stop_rows,
        widths=[5.0, 3.0, 4.2, 4.2],
    )

    for lang, label, caption in (
        ("ru", "Русский", "Таблица 5 – Топ-10 слов после удаления стоп-слов (русский язык)"),
        ("en", "Английский", "Таблица 6 – Топ-10 слов после удаления стоп-слов (английский язык)"),
    ):
        first, second = results[lang]["texts"]
        rows = []
        for rank in range(10):
            rows.append(
                [
                    rank + 1,
                    first["top_words"][rank]["word"],
                    first["top_words"][rank]["count"],
                    second["top_words"][rank]["word"],
                    second["top_words"][rank]["count"],
                ]
            )
        add_table(
            doc,
            caption,
            ["№", first["title"], "Частота", second["title"], "Частота"],
            rows,
            widths=[1.2, 4.8, 2.3, 5.2, 2.3],
            font_size=10,
        )

    add_subheading(doc, "1.4 Модель one-hot encoding")
    add_para(
        doc,
        "Для каждой пары текстов строился общий словарь — объединение "
        "словарей двух текстов. В one-hot модели компонента вектора равна 1, "
        "если слово встречается в тексте, и 0 в противном случае. Модель "
        "учитывает только наличие слова, но не его частоту. Характеристики "
        "модели приведены в таблице 7.",
    )
    one_hot_rows = []
    for lang, label in (("ru", "Русский"), ("en", "Английский")):
        result = results[lang]
        one_hot_rows.append(
            [
                label,
                fmt_int(result["one_hot"]["vocabulary_size"]),
                fmt_int(result["one_hot"]["ones_in_matrix"]),
                fmt_int(result["one_hot"]["common_unique_words"]),
                fmt(result["one_hot"]["jaccard_similarity"], 4),
                fmt(result["one_hot"]["cosine_similarity"], 4),
            ]
        )
    add_table(
        doc,
        "Таблица 7 – Модель one-hot encoding",
        [
            "Язык",
            "Размер словаря",
            "Единиц в матрице",
            "Общих слов",
            "Жаккар",
            "Косинус",
        ],
        one_hot_rows,
        widths=[2.6, 3.2, 3.2, 2.8, 2.4, 2.4],
        font_size=10,
    )

    add_subheading(doc, "1.5 Модель TF (term frequency)")
    add_para(
        doc,
        "В TF-модели вес слова равен его относительной частоте в тексте:",
    )
    add_formula(doc, "TF(w, d) = n(w, d) / Σ n(w', d),")
    add_para(
        doc,
        "где n(w, d) — число вхождений слова w в текст d; сумма берётся по "
        "всем словам текста. Векторы строятся в общем словаре пары текстов. "
        "Наиболее весомые TF-термы приведены в таблицах 8 и 9.",
    )
    for lang, label, caption in (
        ("ru", "Русский", "Таблица 8 – Топ-10 TF-термов (русский язык)"),
        ("en", "Английский", "Таблица 9 – Топ-10 TF-термов (английский язык)"),
    ):
        first, second = results[lang]["tf"]["top_terms"]
        rows = []
        for rank in range(10):
            rows.append(
                [
                    rank + 1,
                    first["terms"][rank]["word"],
                    fmt(first["terms"][rank]["tf"], 5),
                    second["terms"][rank]["word"],
                    fmt(second["terms"][rank]["tf"], 5),
                ]
            )
        add_table(
            doc,
            caption,
            ["№", first["title"], "TF", second["title"], "TF"],
            rows,
            widths=[1.2, 4.8, 2.3, 5.2, 2.3],
            font_size=10,
        )

    add_subheading(doc, "1.6 Пересечение мультимножеств для one-hot модели")
    add_para(
        doc,
        "Для one-hot векторов пересечение — это слова, которые есть в обоих "
        "текстах (общие уникальные слова). Дополнительно для исходных "
        "мультимножеств слов вычислялось пересечение с учётом кратностей:",
    )
    add_formula(doc, "|M1 ∩ M2| = Σ min(n1(w), n2(w)).")
    add_para(
        doc,
        "Сходство множеств оценивалось коэффициентом Жаккара:",
    )
    add_formula(doc, "J = |V1 ∩ V2| / |V1 ∪ V2|,")
    add_para(
        doc,
        "где V1 и V2 — множества уникальных слов первого и второго текстов. "
        "Для one-hot векторов также вычислялся косинус. Результаты приведены "
        "в таблице 10.",
    )
    intersection_rows = []
    for lang, label in (("ru", "Русский"), ("en", "Английский")):
        result = results[lang]
        intersection_rows.append(
            [
                label,
                fmt_int(result["one_hot"]["common_unique_words"]),
                fmt_int(result["one_hot"]["union_unique_words"]),
                fmt_int(result["one_hot"]["multiset_intersection_size"]),
                fmt(result["one_hot"]["jaccard_similarity"], 4),
                fmt(result["one_hot"]["cosine_similarity"], 4),
            ]
        )
    add_table(
        doc,
        "Таблица 10 – Пересечение множеств и мультимножеств",
        [
            "Язык",
            "Общих уникальных слов",
            "Объединение",
            "Пересечение мультимножеств",
            "Жаккар",
            "Косинус one-hot",
        ],
        intersection_rows,
        widths=[2.4, 3.1, 2.5, 3.4, 2.3, 2.8],
        font_size=9,
    )

    for lang, label, caption in (
        ("ru", "Русский", "Таблица 11 – Наиболее частые общие слова (русский язык)"),
        ("en", "Английский", "Таблица 12 – Наиболее частые общие слова (английский язык)"),
    ):
        rows = []
        for rank, item in enumerate(results[lang]["one_hot"]["common_words"][:10], start=1):
            rows.append(
                [
                    rank,
                    item["word"],
                    item["count_text_1"],
                    item["count_text_2"],
                    item["min_count"],
                ]
            )
        add_table(
            doc,
            caption,
            ["№", "Слово", "В тексте 1", "В тексте 2", "Минимум"],
            rows,
            widths=[1.2, 6.0, 3.1, 3.1, 3.1],
            font_size=10,
        )

    add_subheading(doc, "1.7 Косинусный коэффициент для TF модели")
    add_para(
        doc,
        "Косинусная мера близости вычисляется по формуле",
    )
    add_formula(doc, "cos(v1, v2) = (v1 · v2) / (||v1|| · ||v2||).")
    add_para(
        doc,
        "Она не зависит от длины текста и принимает значения от 0 до 1: "
        "чем ближе значение к 1, тем более похожи частотные профили текстов. "
        "Результаты для TF модели приведены в таблице 13, сравнение моделей — "
        "в таблице 14.",
    )
    cosine_rows = []
    comparison_rows = []
    for lang, label in (("ru", "Русский"), ("en", "Английский")):
        result = results[lang]
        first, second = result["texts"]
        cosine_rows.append(
            [
                label,
                first["title"],
                second["title"],
                fmt(result["tf"]["cosine_similarity"], 4),
            ]
        )
        comparison_rows.append(
            [
                label,
                fmt(result["one_hot"]["cosine_similarity"], 4),
                fmt(result["tf"]["cosine_similarity"], 4),
            ]
        )
    add_table(
        doc,
        "Таблица 13 – Косинусный коэффициент для TF модели",
        ["Язык", "Текст 1", "Текст 2", "Косинус TF"],
        cosine_rows,
        widths=[2.8, 5.4, 5.4, 2.9],
    )
    add_table(
        doc,
        "Таблица 14 – Сравнение one-hot и TF моделей",
        ["Язык", "Косинус one-hot", "Косинус TF"],
        comparison_rows,
        widths=[4.0, 6.0, 6.0],
    )

    figure_path = FIG / "task1_top_tf.png"
    if figure_path.exists():
        add_figure(
            doc,
            figure_path,
            "Рисунок 1 – Топ-10 TF-термов после удаления стоп-слов",
            width_cm=16.5,
        )

    add_para(
        doc,
        "Вывод по заданию 1. В ходе выполнения задания построены две "
        "векторные модели для двух пар текстов. После токенизации, "
        "лемматизации и удаления стоп-слов в каждом тексте остаётся около "
        "3,5–4,1 тыс. значимых слов. One-hot модель учитывает только наличие "
        "слова, поэтому её косинус для русской пары равен примерно 0,24, для "
        "английской — примерно 0,34. TF модель дополнительно учитывает "
        "относительную частоту слов: косинус для русской пары составляет "
        "примерно 0,28, для английской — примерно 0,19. Пересечение "
        "мультимножеств с учётом кратностей больше числа общих уникальных "
        "слов (900 против 412 для русского языка и 1 061 против 489 для "
        "английского), что показывает повторяемость общих слов в обоих "
        "текстах.",
    )

    # ---------------- ЗАКЛЮЧЕНИЕ ----------------
    add_heading(doc, "ЗАКЛЮЧЕНИЕ", page_break=True)
    add_para(
        doc,
        "В работе реализовано задание 1 РГР №3: построены векторные модели "
        "текстов на основе мультимножества слов для русского и английского "
        "языков. Выполнены токенизация, лемматизация и удаление стоп-слов, "
        "построены модели one-hot encoding и TF, рассчитаны пересечение "
        "мультимножеств, коэффициент Жаккара и косинусная мера сходства.",
    )
    add_para(
        doc,
        "Полученные результаты показывают, что one-hot модель отражает факт "
        "наличия общих слов, но не учитывает их частоту, тогда как TF модель "
        "более чувствительна к распределению частот. Для дальнейших заданий "
        "работы подготовленные нормализованные тексты можно использовать для "
        "построения Bag-of-words для 2-грамм, модели TF*IDF и сравнения "
        "лемматизации со стеммингом.",
    )

    # ---------------- ИСТОЧНИКИ ----------------
    add_heading(doc, "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ", page_break=True)
    sources = [
        "Wikimedia Foundation. Wikimedia Wikipedia dataset, version 20231101 "
        "[Электронный ресурс]. — Hugging Face. — Режим доступа: "
        "https://huggingface.co/datasets/wikimedia/wikipedia.",
        "simplemma: simple multilingual lemmatizer for Python [Электронный "
        "ресурс]. — Режим доступа: https://github.com/adbar/simplemma.",
        "NumPy: the fundamental package for scientific computing with Python "
        "[Электронный ресурс]. — Режим доступа: https://numpy.org.",
        "pandas: Python Data Analysis Library [Электронный ресурс]. — Режим "
        "доступа: https://pandas.pydata.org.",
        "Matplotlib: Visualization with Python [Электронный ресурс]. — Режим "
        "доступа: https://matplotlib.org.",
        "Корпус и частотные словари проекта nlp_uni, работа №1.",
    ]
    for i, source in enumerate(sources, start=1):
        add_para(doc, f"{i}. {source}")

    doc.save(path)


def convert_to_pdf(docx_path: Path) -> Path | None:
    result = subprocess.run(
        [
            "soffice",
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            str(REPORT_DIR),
            str(docx_path),
        ],
        capture_output=True,
        text=True,
        timeout=180,
    )
    if result.returncode != 0:
        print("LibreOffice stderr:", result.stderr)
        return None
    pdf_path = docx_path.with_suffix(".pdf")
    return pdf_path if pdf_path.exists() else None


def find_heading_pages(pdf_path: Path, headings: list[str]) -> dict[str, int]:
    text = subprocess.check_output(
        ["pdftotext", "-layout", str(pdf_path), "-"],
        text=True,
    )
    pages = text.split("\f")
    result = {}
    for heading in headings:
        for page_number, page in enumerate(pages, start=1):
            if page_number <= 2:
                continue
            normalized = re.sub(r"\s+", " ", page)
            if heading in normalized:
                result[heading] = page_number
                break
    return result


def main() -> None:
    draft_path = REPORT_DIR / "РГР_3_отчет.docx"
    build_report(draft_path, pages=None)
    print("Черновик сохранен:", draft_path)

    pdf_draft = convert_to_pdf(draft_path)
    pages = {}
    if pdf_draft:
        pages = find_heading_pages(pdf_draft, TOC_ENTRIES)
        print("Найденные страницы разделов:", pages)
    else:
        print("Не удалось получить PDF для определения номеров страниц.")

    final_path = REPORT_DIR / "РГР_3_отчет.docx"
    build_report(final_path, pages=pages)
    print("Итоговый DOCX сохранен:", final_path)

    pdf_final = convert_to_pdf(final_path)
    if pdf_final:
        print("PDF для проверки:", pdf_final)
    else:
        print("PDF не создан, но DOCX готов.")


if __name__ == "__main__":
    main()
