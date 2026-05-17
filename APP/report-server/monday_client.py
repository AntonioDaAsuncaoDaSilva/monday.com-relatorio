import requests


class MondayClient:
    API_URL = "https://api.monday.com/v2"

    def __init__(self, token: str):
        self.headers = {
            "Authorization": token,
            "Content-Type": "application/json",
        }

    def _query(self, query: str, variables: dict = None) -> dict:
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        response = requests.post(self.API_URL, json=payload, headers=self.headers)
        response.raise_for_status()
        data = response.json()

        if "errors" in data:
            raise Exception(f"Monday API error: {data['errors']}")

        return data["data"]

    def get_board_data(self, board_id: str) -> dict:
        query = """
        query GetBoard($board_id: ID!) {
          boards(ids: [$board_id]) {
            id
            name
            workspace_id
            columns {
              id
              title
            }
            items_page(limit: 100) {
              items {
                id
                name
                column_values {
                  id
                  text
                }
              }
            }
          }
        }
        """
        data = self._query(query, {"board_id": board_id})
        boards = data.get("boards", [])
        if not boards:
            raise Exception(f"Board {board_id} não encontrado")
        return boards[0]

    def get_workspace_name(self, workspace_id: str) -> str:
        query = """
        query GetWorkspace($ids: [ID!]) {
          workspaces(ids: $ids) {
            id
            name
          }
        }
        """
        data = self._query(query, {"ids": [workspace_id]})
        workspaces = data.get("workspaces", [])
        if not workspaces:
            raise Exception(f"Workspace {workspace_id} não encontrado")
        return workspaces[0]["name"]

    def create_doc(self, workspace_id: str, doc_name: str) -> str:
        mutation = """
        mutation CreateDoc($workspace_id: ID!, $doc_name: String!) {
          create_doc(location: {workspace: {workspace_id: $workspace_id, name: $doc_name}}) {
            id
          }
        }
        """
        data = self._query(mutation, {"workspace_id": workspace_id, "doc_name": doc_name})
        return str(data["create_doc"]["id"])

    def add_doc_block(self, doc_id: str, block_type: str, content: str,
                      parent_block_id: str = None, after_block_id: str = None) -> str:
        if parent_block_id:
            mutation = """
            mutation AddBlock($doc_id: ID!, $type: DocBlockContentType!, $content: JSON!, $parent_block_id: String!) {
              create_doc_block(doc_id: $doc_id, type: $type, content: $content, parent_block_id: $parent_block_id) {
                id
              }
            }
            """
            variables = {"doc_id": doc_id, "type": block_type, "content": content, "parent_block_id": parent_block_id}
        elif after_block_id:
            mutation = """
            mutation AddBlock($doc_id: ID!, $type: DocBlockContentType!, $content: JSON!, $after_block_id: String!) {
              create_doc_block(doc_id: $doc_id, type: $type, content: $content, after_block_id: $after_block_id) {
                id
              }
            }
            """
            variables = {"doc_id": doc_id, "type": block_type, "content": content, "after_block_id": after_block_id}
        else:
            mutation = """
            mutation AddBlock($doc_id: ID!, $type: DocBlockContentType!, $content: JSON!) {
              create_doc_block(doc_id: $doc_id, type: $type, content: $content) {
                id
              }
            }
            """
            variables = {"doc_id": doc_id, "type": block_type, "content": content}

        data = self._query(mutation, variables)
        return str(data["create_doc_block"]["id"])

    def add_table_block_after(self, doc_id: str, col_count: int, row_count: int, after_block_id: str = None) -> tuple[str, list[list[str]]]:
        import json as _json
        if after_block_id:
            mutation = """
            mutation AddTable($doc_id: ID!, $content: JSON!, $after_block_id: String!) {
              create_doc_block(doc_id: $doc_id, type: table, content: $content, after_block_id: $after_block_id) {
                id content
              }
            }
            """
            variables = {"doc_id": doc_id, "content": _json.dumps({"column_count": col_count, "row_count": row_count}), "after_block_id": after_block_id}
        else:
            mutation = """
            mutation AddTable($doc_id: ID!, $content: JSON!) {
              create_doc_block(doc_id: $doc_id, type: table, content: $content) {
                id content
              }
            }
            """
            variables = {"doc_id": doc_id, "content": _json.dumps({"column_count": col_count, "row_count": row_count})}
        data = self._query(mutation, variables)
        block = data["create_doc_block"]
        raw = _json.loads(block["content"]) if isinstance(block["content"], str) else block["content"]
        cell_ids = [[cell["blockId"] for cell in row] for row in raw["cells"]]
        return str(block["id"]), cell_ids

    def add_table_block(self, doc_id: str, col_count: int, row_count: int) -> tuple[str, list[list[str]]]:
        """Creates table and returns (block_id, cell_ids[row][col])."""
        import json as _json
        mutation = """
        mutation AddTable($doc_id: ID!, $content: JSON!) {
          create_doc_block(doc_id: $doc_id, type: table, content: $content) {
            id
            content
          }
        }
        """
        content = _json.dumps({"column_count": col_count, "row_count": row_count})
        data = self._query(mutation, {"doc_id": doc_id, "content": content})
        block = data["create_doc_block"]
        raw = _json.loads(block["content"]) if isinstance(block["content"], str) else block["content"]
        cell_ids = [[cell["blockId"] for cell in row] for row in raw["cells"]]
        return str(block["id"]), cell_ids
