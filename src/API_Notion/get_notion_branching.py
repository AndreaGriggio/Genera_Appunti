from notion_client import Client
from .config import NOTION_TOKEN
from .config import DATA_PATH
import json
def estrai_albero(notion: Client, page_id: str, livello: int = 0):
    """
    Returns a notion subtree given a page_id and a notion client.

    The subtree is a dictionary with the following structure:
        {
            "id": page_id,
            "titolo": title of page,
            "livello": level of page,
            "children": list of children of page
        }

    The function uses the blocks API to get the children of the page and recursively
    construct the subtree. If the page has children, the function calls itself with
    the child_id and the level of the child incremented by one. If the
    page does not have children, the function simply returns the subtree.

    Parameters:
        notion: Client
            page_id: str
            livello: int, optional, default to 0

    Returns:
        A dictionary with the subtree structure.
    """
    nodo = {
        "id": page_id,
        "titolo": None,
        "livello": livello,
        "children": []
    }

    # recupero titolo

    page = notion.pages.retrieve(page_id=page_id)

    titolo = page["properties"]["title"]["title"][0]["plain_text"]
    nodo["titolo"] = titolo

    cursor = None

    while True:
        res = notion.blocks.children.list(block_id=page_id, start_cursor=cursor)

        for b in res["results"]:
            if b["type"] == "child_page":
               
                child_id = b["id"]
                child_title = b["child_page"]["title"]

                # crea subnodo
                child_node = {
                    "id": child_id,
                    "titolo": child_title,
                    "livello": livello + 1,
                    "children": []
                }
                print(child_node)
                nodo["children"].append(child_node)

                # solo se ha sottopagine analizzo i figli
                if b.get("has_children", False):
                    child_node["children"] = estrai_albero(
                        notion, child_id, livello + 1
                    )["children"]

                
        if not res.get("has_more"):
                break
        cursor = res.get("next_cursor")

    return nodo

def get_notion_branching():
    """
    Restituisce una pagina notion a partire da un id di pagina dato.

    :param notion: oggetto notion.Client
    :param base_id: id della pagina di partenza
    :return: dizionario con la pagina di partenza e eventuali sottopagini
    """
    notion = Client(auth=NOTION_TOKEN)
    #2a68f1dee7b6807789d1ebd7e3a87fb0
    base_id = "2a68f1dee7b6807789d1ebd7e3a87fb0"
    print(notion.users.list())
    print("\a")
    #res = notion.search(query="2a78f1dee7b68007b90bd926c1ce0ddd")
    #  # titolo, parola chiave, ecc.
    # for r in res["results"]:
    #     print(r["object"], r["id"], r["url"])
    # res = estrai_pagine(notion, base_id)
    # for r in res:
    #     print(r)
    res = notion.blocks.children.list(block_id=base_id)
    print(res)
    print ("\a")
    pagina_primo_anno = res["results"][1]["id"]
    res = notion.blocks.children.list(block_id=pagina_primo_anno)
    nome = notion.pages.retrieve(page_id=pagina_primo_anno)
    print(nome["properties"]["title"]["title"][0]["plain_text"])
    print("\n")
    print(res)
    print("\n")
    print(res["results"][1]["type"],res["results"][1]["id"],res["results"][1]["child_page"]["title"])
    risultato = estrai_albero(notion, base_id)
    with open(DATA_PATH /"dict_notion.json","w",encoding="utf-8") as f:
        json.dump(risultato, f, indent=4, ensure_ascii=False)
            
            
if __name__ == "__main__" :
    get_notion_branching()


