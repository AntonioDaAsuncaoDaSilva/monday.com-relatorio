import json
from datetime import datetime

from monday_client import MondayClient
from kpi_descriptions import KPI_DESCRIPTIONS

COLUMN_ID_KPIS        = "numeric_mkzzjvha"
COLUMN_ID_DATA        = "date_mkzz8t47"
COLUMN_ID_RESPONSAVEL = "multiple_person_mkzzc76"
COLUMN_ID_PROGRESSO   = "numeric_mm06c1nk"
COLUMN_ID_F1          = "color_mkzza0m"
COLUMN_ID_F2          = "color_mkzz87y"
COLUMN_ID_F3          = "color_mkzz22ef"
COLUMN_ID_F4          = "color_mkzzzttd"
COLUMN_ID_PDS         = "text_mm06z9km"


def _text_block(text: str, bold: bool = False) -> str:
    lines = text.split("\n")
    delta = []
    for line in lines:
        entry: dict = {"insert": line + "\n"}
        if bold:
            entry["attributes"] = {"bold": True}
        delta.append(entry)
    return json.dumps({"alignment": "left", "deltaFormat": delta})


def _get_col(item: dict, column_id: str) -> str:
    for col in item.get("column_values", []):
        if col["id"] == column_id:
            return col.get("text") or ""
    return ""


class ReportGenerator:
    def __init__(self, client: MondayClient):
        self.client = client
        self._last_block_id: str | None = None

    def _append(self, doc_id: str, block_type: str, content: str) -> str:
        block_id = self.client.add_doc_block(
            doc_id, block_type, content,
            after_block_id=self._last_block_id
        )
        self._last_block_id = block_id
        return block_id

    def _fill_table(self, doc_id: str, headers: list[str], rows: list[list[str]]) -> None:
        all_rows = [headers] + rows
        table_id, cell_ids = self.client.add_table_block_after(
            doc_id, len(headers), len(all_rows), self._last_block_id
        )
        self._last_block_id = table_id

        for r_idx, row in enumerate(all_rows):
            for c_idx, text in enumerate(row):
                is_header = r_idx == 0
                self.client.add_doc_block(
                    doc_id, "normal_text",
                    _text_block(text, bold=is_header),
                    parent_block_id=cell_ids[r_idx][c_idx],
                )

    def generate(self, board_id: str) -> str:
        self._last_block_id = None
        board = self.client.get_board_data(board_id)
        board_name = board["name"]
        items = board["items_page"]["items"]
        date_str = datetime.now().strftime("%d/%m/%Y")

        workspace_id = str(board["workspace_id"])
        doc_title = f"Relatório — {board_name} — {date_str}"
        doc_id = self.client.create_doc(workspace_id, doc_title)

        self._append(doc_id, "large_title", _text_block(doc_title))
        self._append(doc_id, "normal_text", _text_block(f"Gerado em {date_str}"))
        self._append(doc_id, "divider", "{}")

        board_kpis = KPI_DESCRIPTIONS.get(board_id, {})

        headers = ["METAS (SMART)", "DATA (FINAL)", "INDICADORES (KPI)"]
        rows = []
        for item in items:
            item_id = str(item["id"])
            meta = item["name"]
            data_termino = _get_col(item, COLUMN_ID_DATA) or "—"
            kpi_count = _get_col(item, COLUMN_ID_KPIS) or "0"
            kpi_desc_list = board_kpis.get(item_id, [])
            kpi_desc = "; ".join(kpi_desc_list) if kpi_desc_list else ""
            kpi_text = f"{kpi_desc}: {kpi_count}" if kpi_desc else kpi_count
            rows.append([meta, data_termino, kpi_text])

        self._fill_table(doc_id, headers, rows)

        # Resumo
        # --- Resumo ---
        self._append(doc_id, "divider", "{}")
        self._append(doc_id, "medium_title", _text_block("Resumo do Projecto"))

        datas = sorted(set(_get_col(i, COLUMN_ID_DATA) for i in items if _get_col(i, COLUMN_ID_DATA)))
        data_info = datas[0] if len(datas) == 1 else (f"{datas[0]} a {datas[-1]}" if datas else "—")

        responsaveis = sorted(set(
            _get_col(i, COLUMN_ID_RESPONSAVEL) for i in items
            if _get_col(i, COLUMN_ID_RESPONSAVEL)
        ))

        progressos = [float(_get_col(i, COLUMN_ID_PROGRESSO)) for i in items if _get_col(i, COLUMN_ID_PROGRESSO)]
        progresso_medio = f"{sum(progressos) / len(progressos):.1f}%" if progressos else "—"

        self._append(doc_id, "normal_text", _text_block(f"Projecto: {board_name}"))
        self._append(doc_id, "normal_text", _text_block(f"Total de metas: {len(items)}"))
        self._append(doc_id, "normal_text", _text_block(f"Data de término: {data_info}"))
        self._append(doc_id, "normal_text", _text_block(f"Responsável(eis): {', '.join(responsaveis) or '—'}"))
        self._append(doc_id, "normal_text", _text_block(f"Progresso médio: {progresso_medio}"))

        self._append(doc_id, "divider", "{}")
        self._append(doc_id, "small_title", _text_block("Estado por Meta"))

        for item in items:
            item_id = str(item["id"])
            kpi_val   = _get_col(item, COLUMN_ID_KPIS) or "—"
            progresso = _get_col(item, COLUMN_ID_PROGRESSO) or "—"
            responsavel = _get_col(item, COLUMN_ID_RESPONSAVEL) or "—"
            f1 = _get_col(item, COLUMN_ID_F1) or "—"
            f2 = _get_col(item, COLUMN_ID_F2) or "—"
            f3 = _get_col(item, COLUMN_ID_F3) or "—"
            f4 = _get_col(item, COLUMN_ID_F4) or "—"
            pds = _get_col(item, COLUMN_ID_PDS)
            kpi_desc_list = board_kpis.get(item_id, [])
            kpi_label = f"{'; '.join(kpi_desc_list)}: {kpi_val}" if kpi_desc_list else kpi_val

            linhas = [
                f"{item['name']}",
                f"  Responsável: {responsavel}",
                f"  Progresso: {progresso}%",
                f"  Fases: F1={f1} | F2={f2} | F3={f3} | F4={f4}",
                f"  Indicador: {kpi_label}",
            ]
            if pds:
                linhas.append(f"  Notas: {pds}")

            self._append(doc_id, "bulleted_list", _text_block("\n".join(linhas)))

        return doc_id
