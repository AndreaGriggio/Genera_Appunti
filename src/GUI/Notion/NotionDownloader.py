from notion_client import Client
from src.GUI.config import NOTION_TOKEN

class NotionDownloader:
    def __init__(self):
        self.client = Client(auth=NOTION_TOKEN)

    def download_page(self, page_id: str) -> list[dict]:
        """Scarica tutti i blocchi di una pagina ricorsivamente."""
        blocks = []
        cursor = None

        while True:
            params = {"block_id": page_id}
            if cursor:
                params["start_cursor"] = cursor

            res = self.client.blocks.children.list(**params)

            for block in res.get("results", []):
                blocks.append(block)
                # Se ha figli (es. toggle, lista annidata) scendi
                if block.get("has_children"):
                    block["_children"] = self.download_page(block["id"])

            if not res.get("has_more"):
                break
            cursor = res.get("next_cursor")

        return blocks

if __name__ == "__main__":
    downloader = NotionDownloader()

    print(downloader.download_page("1ba8f1dee7b6808db0ecc6ecb94da325"))