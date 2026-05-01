
class Point():
    def __init__(self, x:float = 0, y:float = 0):
        self.x:float = x
        self.y:float = y
        self.connected_lines:list = []

    def getX(self)-> float:
        return self.x

    def getY(self)-> float:
        return self.y
    def getParent(self):
        pass


    def pointToDict(self)-> dict:
        return {
                "x":self.getX(),
                "y":self.getY()
                }