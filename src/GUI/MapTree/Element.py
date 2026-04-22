from PyQt6.QtGui import QColor


class Element():
    def __init__(self,x:float,y:float,border:str,margin:int,fill:str,id:int,text:str):
        self._x = x
        self._y = y
        self._border = border
        self._margin = margin
        self._fill = fill
        self._id = id
        self._text = text
    def getX(self)->float:
        return self._x
    def getY(self)->float:
        return self._y
    def getBorder(self)->str:
        return self._border
    def getMargin(self)->int:
        return self._margin
    def getFill(self)-> str:
        return self._fill
    def getId(self)->int:
        return self._id
    def getText(self)-> str:
        return self._text
    def elementTodict(self)-> dict:
        return {"x":self.getX(),
                 "y":self.getY(),
                 "border":self.getBorder(),
                 "margin":self.getMargin(),
                 "fill":self.getFill(),
                 "id":self.getId(),
                 "text":self.getText()
        }
        
        
    
        