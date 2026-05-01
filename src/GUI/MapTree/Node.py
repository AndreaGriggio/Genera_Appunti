from src.GUI.MapTree.Element import Element

class Connection:
    def __init__(self, target_id: int,
                       tipo: str,
                       arrow_start: bool = False, 
                       arrow_end: bool = False,
                       attachment : dict[str,str] | None = None):
        self.target_id = target_id
        self.tipo = tipo
        self.arrow_start = arrow_start
        self.arrow_end = arrow_end

        attachment = attachment or {}

        self.orientation_start = attachment.get("orientation_start","E")
        self.orientation_end = attachment.get("orientation_end","W")

    def to_dict(self) -> dict:
        return {
            "target": self.target_id,
            "tipo": self.tipo,
            "arrow_start": self.arrow_start,
            "arrow_end": self.arrow_end,
            "attachment": {
                "orientation_start": self.orientation_start,
                "orientation_end": self.orientation_end
            }
        }

class Node:
    def __init__(self, value: Element | None,
                 neighbours: list[Connection] | None):
        self.value = value
        self.neighbours = neighbours or []

    def nodeToDict(self) -> dict | None:
        if self.value is None:
            return None
        return {
            "element": self.value.elementTodict(),
            "n": [c.to_dict() for c in (self.neighbours or [])]
        }