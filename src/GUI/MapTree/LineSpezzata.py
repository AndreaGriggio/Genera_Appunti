from src.GUI.MapTree.LineElement import LineItem

class LineSpezzata(LineItem):
    def __init__(self,node_start = None, node_center = None, node_end = None,  id = 0):
        super().__init__(node_start, node_center, tipo="retta")
        self.second_line = LineItem(node_center, node_end, tipo="retta")

        self.node_center = node_center  
        self.id = id