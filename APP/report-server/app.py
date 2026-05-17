# report-server/app.py
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import config
from monday_client import MondayClient
from report_generator import ReportGenerator

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

client = MondayClient(config.MONDAY_API_TOKEN)
generator = ReportGenerator(client)


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/generate-doc", methods=["POST"])
def generate_doc():
    data = request.get_json(silent=True) or {}
    board_id = str(data.get("board_id", ""))
    if not board_id:
        return jsonify({"error": "board_id required"}), 400
    try:
        doc_id = generator.generate(board_id)
        # Query doc URL
        url_res = client._query(
            "query GetDoc($id: ID!) { docs(ids: [$id]) { id url } }",
            {"id": doc_id}
        )
        docs = url_res.get("docs", [])
        doc_url = docs[0]["url"] if docs else None
        logger.info("Doc created: %s", doc_id)
        return jsonify({"doc_id": doc_id, "doc_url": doc_url})
    except Exception as e:
        logger.error("Error generating doc: %s", e)
        return jsonify({"error": str(e)}), 500


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True) or {}
    if "challenge" in data:
        return jsonify({"challenge": data["challenge"]})
    event = data.get("event", {})
    board_id = str(event.get("boardId", ""))
    if not board_id:
        return jsonify({"error": "boardId missing"}), 400
    try:
        doc_id = generator.generate(board_id)
        return jsonify({"status": "ok", "doc_id": doc_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    import os
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    port = int(os.getenv("PORT", 5000))
    app.run(port=port, debug=debug)
