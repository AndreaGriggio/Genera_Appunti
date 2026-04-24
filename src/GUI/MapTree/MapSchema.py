from pydantic import BaseModel, Field
from typing import Literal

class MapElement(BaseModel):
    id: int = Field(description="ID univoco del nodo. Il nodo radice deve avere id 0, gli altri a salire (1, 2, 3...).")
    text: str = Field(default = " " ,description="Il testo conciso, la parola chiave o il concetto centrale di questo blocco.")
    x: float = Field(default=0.0, description="Coordinata X nella mappa. Sfalsa i valori (es. 0, 500, -500) per non sovrapporre i nodi.")
    y: float = Field(default=0.0, description="Coordinata Y nella mappa. Sfalsa i valori in base alla profondità.")
    border: str = Field(default="#000000", description="Colore esadecimale del bordo, default '#000000'.")
    fill: str = Field(default="#323232", description="Colore esadecimale di sfondo, default '#323232'.")
    margin: int = Field(default=10, description="Margine interno del testo, default 10.")

class MapConnection(BaseModel):
    target: int = Field(description="L'ID del nodo di destinazione.")
    tipo: Literal["spline", "retta"] = Field(description="Il tipo di linea. SOLO 'spline' o 'retta'.")
class MapNode(BaseModel):
    element: MapElement
    n: list[MapConnection] = Field(
        default_factory=list, 
        description="Collegamenti ad altri nodi. È una lista di MapConnection, ogni array contiene l'ID del nodo destinazione e il tipo di linea tracciata ('spline' o 'retta')."
    )

class MapDocument(BaseModel):
    nodi: list[MapNode] = Field(description="La lista completa dei nodi che compongono la mappa mentale.")