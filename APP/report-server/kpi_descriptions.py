# Preencher após correr discover.py para obter os IDs correctos.
#
# Formato:
#   KPI_DESCRIPTIONS[board_id][item_id] = ["descrição 1", "descrição 2", ...]
#
# Exemplo (substituir pelos IDs reais):
#
# KPI_DESCRIPTIONS = {
#     "1234567890": {
#         "9876543210": ["% de capacidade explorada"],
#         "9876543211": ["Nº de parceiros a explorar o ANGOSAT-2"],
#         "9876543212": ["Taxa de MoUs assinados"],
#     }
# }

KPI_DESCRIPTIONS: dict[str, dict[str, list[str]]] = {
    "5090842468": {
        "2672134368": ["% de capacidade explorada"],
        "2672138862": ["Nº de parceiros a explorar o ANGOSAT-2"],
        "2672130253": ["Nº de beams ocupados"],
        "2672130254": ["Nº de parceiros a explorar o ANGOSAT-2"],
        "2672130255": ["N.º de interações realizadas"],
    }
}
