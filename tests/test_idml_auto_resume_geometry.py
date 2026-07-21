from __future__ import annotations

import unittest
from pathlib import Path

from tools.export_idml import IdmlWriter, load_layout_params
from tools.idml.components.base import RenderContext
from tools.idml.components.prose_table import (
    auto_resume_language,
    body_data_table_kind,
    render_table_block,
)
from tools.idml.params import param_pt
from tools.idml.prose_flow import operation_final_frame_x_offset


ROOT = Path(__file__).resolve().parents[1]


class AutoResumeGeometryTests(unittest.TestCase):
    BODY_ROWS = {
        "en": (
            ("Power-on/Restart", "Manual output off"),
            ("Battery SOC", "Energy Saving mode output off"),
            ("", "Protection-triggered output off"),
            ("OTA upgrade completed", "Discharge timer-triggered output off"),
        ),
        "fr": (
            (
                "Mise sous tension/redémarrage après arrêt ou redémarrage",
                "Sortie désactivée manuellement (bouton/App)",
            ),
            (
                "SOC de la batterie ≥ limite de décharge +10% après avoir "
                "atteint la limite",
                "Sortie désactivée en mode économie d’énergie",
            ),
            ("", "Sortie désactivée suite à un déclenchement de protection"),
            (
                "Mise à niveau OTA terminée",
                "Sortie désactivée par le minuteur de décharge",
            ),
        ),
        "es": (
            (
                "Encendido/Reiniciar después de apagado o reinicio",
                "Apagado manual de la salida (botón/App)",
            ),
            (
                "SOC de la batería ≥ límite de descarga +10 % después de "
                "alcanzar el límite",
                "Apagado de salida en modo de ahorro de energía",
            ),
            ("", "Apagado de salida activado por protección"),
            (
                "Actualización OTA completada",
                "Apagado de salida activado por temporizador de descarga",
            ),
        ),
    }

    CASES = (
        (
            "en",
            ("Auto Resume Conditions", "Not Auto Resume Conditions"),
            (12.50, 11.49, 11.48, 10.01, 10.75),
            (157.52, 152.00),
            (5.2, 5.2),
            0.0,
            6.62,
        ),
        (
            "fr",
            (
                "Conditions de reprise automatique",
                "Conditions sans reprise automatique",
            ),
            (12.50, 14.45, 11.49, 10.01, 10.75),
            (147.78, 161.74),
            (2.8, 2.4),
            0.0,
            8.04,
        ),
        (
            "es",
            (
                "Condiciones de reanudación automática",
                "Condiciones sin reanudación automática",
            ),
            (12.50, 10.85, 11.48, 10.01, 10.75),
            (147.78, 161.74),
            (2.8, 2.4),
            0.69,
            9.26,
        ),
    )

    @classmethod
    def _rows(cls, headers: tuple[str, str], language: str) -> list[list[str]]:
        return [list(headers), *[list(row) for row in cls.BODY_ROWS[language]]]

    def test_localized_headers_select_reference_geometry(self) -> None:
        for (
            language,
            headers,
            row_heights,
            column_widths,
            left_insets,
            first_line_indent,
            space_before,
        ) in self.CASES:
            with self.subTest(language=language):
                writer = IdmlWriter(
                    load_layout_params(ROOT / "data" / "layout_params.csv")
                )
                ctx = RenderContext(
                    params=writer.params,
                    page_w=writer.page_w,
                    m_l=writer.m_l,
                    m_r=writer.m_r,
                    root=ROOT,
                    bundle_root=ROOT,
                    language=language,
                    inline_origin_shift=operation_final_frame_x_offset(
                        language,
                    ),
                    add_story=writer._add_story_parts,
                )
                rows = self._rows(headers, language)
                tid = f"auto_{language}"

                xml, height = render_table_block(
                    rows,
                    ctx,
                    tid=tid,
                    terminal=True,
                )
                story = dict(writer.stories)[f"st_anchor_data_{tid}"]

                self.assertEqual(language, auto_resume_language(rows))
                self.assertEqual("auto_resume", body_data_table_kind(rows))
                self.assertIn('Anchor="310.65 0"', xml)
                self.assertIn(
                    'ItemTransform="1 0 0 1 -0.37 0"',
                    xml,
                )
                self.assertIn('LeftIndent="0"', xml)
                self.assertIn(
                    f'FirstLineIndent="{first_line_indent:g}"',
                    xml,
                )
                self.assertIn(f'SpaceBefore="{space_before:g}"', xml)
                for row_height in row_heights:
                    self.assertIn(
                        f'SingleRowHeight="{row_height:g}" '
                        f'MinimumHeight="{row_height:g}" AutoGrow="false"',
                        story,
                    )
                self.assertAlmostEqual(309.52, sum(column_widths), places=2)
                for column_index, column_width in enumerate(column_widths):
                    self.assertIn(
                        f'<Column Self="{tid}col{column_index}" '
                        f'Name="{column_index}" '
                        f'SingleColumnWidth="{column_width:g}"/>',
                        story,
                    )
                for column_index, left_inset in enumerate(left_insets):
                    for row_index in (0, 1):
                        cell_marker = (
                            f'<Cell Self="{tid}c{row_index}_{column_index}" '
                        )
                        self.assertIn(cell_marker, story)
                        cell_start = story.index(cell_marker)
                        cell_end = story.index("</Cell>", cell_start)
                        cell_xml = story[cell_start:cell_end]
                        self.assertIn(
                            f'LeftInset="{left_inset:g}"',
                            cell_xml,
                        )
                        self.assertIn('RightInset="2.4"', cell_xml)
                self.assertIn('Anchor="311.02 0.5"', xml)
                self.assertIn(
                    'PointSize="6"><Properties>'
                    '<Leading type="unit">5</Leading></Properties><Content>',
                    story,
                )
                self.assertNotIn('<ParagraphStyleRange Leading="5"', story)
                for row_index, (_left, right) in enumerate(
                    self.BODY_ROWS[language],
                    start=1,
                ):
                    compact = len(" ".join(right.split())) >= 55
                    expected_size = 5.5 if compact else 6.0
                    cell_marker = f'<Cell Self="{tid}c{row_index}_1" '
                    cell_start = story.index(cell_marker)
                    cell_end = story.index("</Cell>", cell_start)
                    cell_xml = story[cell_start:cell_end]
                    self.assertIn(
                        f'PointSize="{expected_size:g}"><Properties>'
                        '<Leading type="unit">5</Leading></Properties>',
                        cell_xml,
                        msg=(
                            f"{language} Auto Resume right row {row_index} "
                            f"must use {expected_size:g}pt: {right}"
                        ),
                    )
                expected_height = (
                    sum(row_heights)
                    + space_before
                    + param_pt(writer.params, "comp_data_table_after", 3.4)
                )
                self.assertAlmostEqual(expected_height, height)

    def test_other_two_column_headers_stay_generic(self) -> None:
        rows = [["Conditions", "Other conditions"], ["A", "B"]]

        self.assertIsNone(auto_resume_language(rows))
        self.assertIsNone(body_data_table_kind(rows))


if __name__ == "__main__":
    unittest.main()
