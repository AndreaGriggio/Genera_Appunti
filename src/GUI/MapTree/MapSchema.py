from pydantic import BaseModel, Field
from typing import Literal
class AttachOrientation(BaseModel):
    """
    Descrive su quale lato di un nodo una linea si attacca.

    Ogni nodo rettangolare ha 4 punti di attacco, uno per lato:
    
        N (Nord)  → lato superiore, centro
        S (Sud)   → lato inferiore, centro  
        E (Est)   → lato destro,    centro
        W (Ovest) → lato sinistro,  centro

    Regola per scegliere le orientazioni:
    
    - Se end è a DESTRA di start  → start usa E,  end usa W   (←–→)
    - Se end è a SINISTRA di start → start usa W,  end usa E   (←–→)
    - Se end è SOTTO start         → start usa S,  end usa N   (↕)
    - Se end è SOPRA start         → start usa N,  end usa S   (↕)

    Esempio: nodo A a sinistra collega nodo B a destra
        orientation_start = "E"   (la linea esce dal lato destro di A)
        orientation_end   = "W"   (la linea entra nel lato sinistro di B)
    """
    orientation_start: Literal["N", "S", "E", "W"] = Field(
        description=(
            "Lato del nodo SORGENTE da cui esce la linea. "
            "Scegli in base alla posizione relativa del nodo destinazione: "
            "destinazione a destra → 'E', "
            "destinazione a sinistra → 'W', "
            "destinazione in basso → 'S', "
            "destinazione in alto → 'N'."
        )
    )
    orientation_end: Literal["N", "S", "E", "W"] = Field(
        description=(
            "Lato del nodo DESTINAZIONE in cui entra la linea. "
            "Deve essere il lato opposto a orientation_start: "
            "se start='E' allora end='W', "
            "se start='W' allora end='E', "
            "se start='S' allora end='N', "
            "se start='N' allora end='S'."
        )
    )
class MapConnection(BaseModel):
    target: int = Field(description="ID del nodo di destinazione.")
    tipo: Literal["spline", "retta"] = Field(description="Tipo di linea. retta o spline")
    arrow_start : bool= Field(default= False,description="True se la linea ha una freccia che punta al nodo di partenza.")
    arrow_end : bool= Field(default= False,description="True se la linea ha una freccia che punta al nodo di destinazione.")
    attachment : AttachOrientation = Field(description=(
        "Punti di attacco della linea sui due nodi."
        "Determina da quale lato del nodo parte la linea e da quale lato arriva. "
    ))

class MapElement(BaseModel):
    id: int = Field(description="ID univoco del nodo. Il nodo radice deve avere id 0, gli altri a salire (1, 2, 3...).")
    text: str = Field(default = " " ,description="Il testo conciso, la parola chiave o il concetto centrale di questo blocco.")
    x: float = Field(default=0.0, description="Coordinata X nella mappa. Sfalsa i valori (es. 0, 500, -500) per non sovrapporre i nodi.")
    y: float = Field(default=0.0, description="Coordinata Y nella mappa. Sfalsa i valori in base alla profondità.")
    border: str = Field(default="#000000", description="Colore esadecimale del bordo, default '#000000'.")
    fill: str = Field(default="#323232", description="Colore esadecimale di sfondo, default '#323232'.")
    margin: int = Field(default=10, description="Margine interno del testo, default 10.")

class MapNode(BaseModel):
    element: MapElement
    n: list[MapConnection] = Field(
        default_factory=list, 
        description="Collegamenti ad altri nodi. È una lista di MapConnection, ogni array contiene l'ID del nodo destinazione e il tipo di linea tracciata ('spline' o 'retta')."
    )

class MapDocument(BaseModel):
    nodi: list[MapNode] = Field(description="La lista completa dei nodi che compongono la mappa mentale.")