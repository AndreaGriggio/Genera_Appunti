from src.GUI.MapTree.Element import Element

class Node():
    def __init__(self,value:Element | None,neighbours:list[tuple[int,str]] | None):
        self.value = value
        self.neighbours = neighbours
        
    def nodeToDict(self)->dict | None:
        if self.value is None :
            return None
        
        return {
            "element":self.value.elementTodict(),
            "n":[
                {"target":n_id,"tipo":tipo}
                for n_id,tipo in (self.neighbours or [])]

        }
    


        