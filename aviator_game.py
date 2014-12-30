#coding: utf-8

# Victoria Terenina, March 2012 

# Simple Aviator Game:
#   just for testing Qt capabilities and educational purposes


import sys
import random
from PyQt4.QtGui import *
from PyQt4.QtCore import *

X, Y = range(2)


class Plane(QMainWindow):
    """
    Main GUI widget for the game.

    Centers widget on the screen, sets sizes and palette,
    initialize main 'Board'.

    """

    def __init__(self):
        super(Plane, self).__init__()

        self.setGeometry(300, 300, 500, 250)
        self.setWindowTitle('Aviator')

        self.pal = self.palette()
        self.pal.setColor(QPalette.Normal, QPalette.Window,
                          QColor(250, 240, 230))
        self.setPalette(self.pal)

        self.planeBoard = Board(self)
        self.setCentralWidget(self.planeBoard)
        self.connect(self.planeBoard, SIGNAL('messageToStatusbar(QString)'),
                     self.statusBar(), SLOT('showMessage(QString)'))

        self.planeBoard.start()

        # centered on the screen
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width())/2,
                  (screen.height() - size.height())/2)



class Board(QFrame):
    """
    Controls all of the elements of the tetris game.

    Sets 'Board's sizes and plane's speed, keeps track of
    score points and elements, rules and draws them all, etc.

    Two main rules:
        bad pieces - if plane catchs them then game is over
        good pieces (golden ones) - helps to increase score points

    """

    BoardWidth = 30
    BoardHeight = 16
    Speed = 100

    def __init__(self, parent):
        super(Board, self).__init__(parent)
        self.timer = QBasicTimer()
        self.setFocusPolicy(Qt.StrongFocus)

        self.isStarted = False
        self.isPaused = False

        self.board = []

        self.piece = Shape()
        self.planePiece = Shape()
        self.planePiece.setShape(Shape.PlaneShape)


    def __setattr__(self, name, value):
        super(Board, self).__setattr__(name, value)

        # update Status Bar every time with new score
        if name is "score":
            self.emit(SIGNAL('messageToStatusbar(QString)'), str(self.score))


    def shapeAt(self, x, y):
        """ Returns current shape at the point (x,y). """
        return self.board[(y * Board.BoardWidth) + x]


    def setShapeAt(self, x, y, shape):
        """ Sets 'Shape' at the point (x,y). """
        self.board[(y * Board.BoardWidth) + x] = shape


    def squareWidth(self):
        """ Returns width of the square's area in terms of Qt. """
        return self.contentsRect().width() / Board.BoardWidth


    def squareHeight(self):
        """ Returns height of the square's area in terms of Qt. """
        return self.contentsRect().height() / Board.BoardHeight


    def start(self):
        """ Starts the Game. """
        self.score = 0
        self.stepCounter = 0
        self.isStarted = True
        self.clearBoard()

        # place plane at the main widget
        self.planeCurX = Board.BoardWidth / 4
        self.planeCurY = Board.BoardHeight / 2

        # populate board
        self.makeNewBadPiece()
        self.makeNewGoodPiece()

        self.timer.start(Board.Speed, self)


    def pause(self):
        """ Pauses the Game. """
        if not self.isStarted:
            return

        self.isPaused = not self.isPaused

        if self.isPaused:
            self.timer.stop()
            self.emit(SIGNAL('messageToStatusbar(QString)'), 'Paused')
        else:
            self.timer.start(Board.Speed, self)

        self.update()


    def paintEvent(self, event):
        """ GUI paintEvent handler.
        Draws the plane and all of the elements which was on the 'Board'.
        """

        painter = QPainter(self)
        rect = self.contentsRect()
        boardTop = rect.bottom() - Board.BoardHeight * self.squareHeight()

        # draw every cell on the board according to it shape 
        for i in range(Board.BoardHeight):
            for j in range(Board.BoardWidth):
                shape = self.shapeAt(j, Board.BoardHeight - i - 1)
                if shape != Shape.NoShape:
                    self.drawSquare(painter,
                                    rect.left() + j * self.squareWidth(),
                                    boardTop + i * self.squareHeight(),
                                    shape)

        # draw plane
        if self.planePiece.shape() != Shape.NoShape:
            for i in range(self.planePiece.size()):
                x = self.planeCurX + self.planePiece.x(i)
                y = self.planeCurY + self.planePiece.y(i)
                self.drawSquare(painter,
                               rect.left() + x * self.squareWidth(),
                               boardTop + (Board.BoardHeight - y - 1) * self.squareHeight(),
                               self.planePiece.shape())


    def drawSquare(self, painter, x, y, shape):
        """ Draws a unit of 'square' (different pieces consist from squares). """
        color = QColor(Shape.ColorTable[shape])
        painter.fillRect(x + 1, y + 1, self.squareWidth() - 2,
                        self.squareHeight() - 2, color)
        painter.setPen(color.light())
        painter.drawLine(x, y + self.squareHeight() - 1, x, y)
        painter.drawLine(x, y, x + self.squareWidth() - 1, y)

        painter.setPen(color.dark())
        painter.drawLine(x + 1, y + self.squareHeight() - 1,
                        x + self.squareWidth() - 1, y + self.squareHeight() - 1)
        painter.drawLine(x + self.squareWidth() - 1, y + self.squareHeight()-1,
                         x + self.squareWidth()-1, y + 1)


    def keyPressEvent(self, event):
        """ GUI keyPressEvent handler.
        Helps with plane navigation and managing the game.
        """

        key = event.key()

        if not self.isStarted:
            if key in [
                Qt.Key_Return,
                Qt.Key_Enter,
                Qt.Key_Space
            ]:
                self.start()
            else:
                QWidget.keyPressEvent(self, event)
            return

        if key == Qt.Key_Space:
            self.pause()
            return

        if self.isPaused:
            return

        elif key == Qt.Key_Down:
            self.tryMovePlane(self.planeCurX, self.planeCurY - 1)
        elif key == Qt.Key_Up:
            self.tryMovePlane(self.planeCurX, self.planeCurY + 1)
        elif key == Qt.Key_Left:
            self.tryMovePlane(self.planeCurX - 1, self.planeCurY)
        elif key == Qt.Key_Right:
            self.tryMovePlane(self.planeCurX + 1, self.planeCurY)
        else:
            QWidget.keyPressEvent(self, event)


    def timerEvent(self, event):
        """
        Timer event handler.

        Moves board one step further in accordance with speed
        and decides what type of Piece will be next

        """

        if event.timerId() == self.timer.timerId():
            self.moveBoard()
            self.stepCounter += 1

            # for every 10th alive step user earns 5 points 
            if self.stepCounter % 10 == 0:
                self.score += 5

            # more bad pieces in life than good ones, just reality
            if self.stepCounter % 8 == 0:
                self.makeNewBadPiece()
            elif self.stepCounter % 19 == 0:
                self.makeNewGoodPiece()
        else:
            QtFui.QFrame.timerEvent(self, event)


    def clearBoard(self):
        """ Reset the board. """
        self.board = []
        for i in range(Board.BoardHeight * Board.BoardWidth + 1):
            self.board.append(Shape.NoShape)


    def makeNewBadPiece(self):
        """
        Makes pieces with bad type, places it on the 'Board'.

        If plane can't avoid this type of piece -> Game is Over.

        """

        # make a new shape
        self.piece.setRandomBadShape()

        while True:
            # find appropriate beginning point (X, Y) for placing new Piece
            x0, y0 = self.getStartPoint()

            # check overlapping with another piece
            if not self.isOverlap(x0, y0):
                break

        # place new piece on the Board element by element
        self.placePiece(x0, y0)


    def placePiece(self, x0, y0):
        """ Sets selected shape of piece on the 'Board'. """
        for i in range(self.piece.size()):
            x = x0 + self.piece.x(i)
            y = y0 + self.piece.y(i)
            self.setShapeAt(x, y, self.piece.shape())


    def isOverlap(self, x0, y0):
        """
        Checks for overlapping on the current 'Board'.

        Need to check availability of the empty places on the 'Board'
        before placing new piece at the starting point (x0, y0).
        If all is ok - returns True, otherwise False.

        """

        for i in range(self.piece.size()):
            x = x0 + self.piece.x(i)
            y = y0 + self.piece.y(i)

            if self.shapeAt(x, y) != Shape.NoShape:
                return True

        return False


    def getStartPoint(self):
        """ Selects randomly start point for placing new piece. """
        max_width, max_height = self.piece.maxSizes()
        x0 = Board.BoardWidth - max_width
        y0 = random.randint(1, Board.BoardHeight - max_height)

        return (x0, y0)


    def makeNewGoodPiece(self):
        """
        Makes pieces with good type, places it on the 'Board'.

        This type of pieces helps getting score."

        """

        # make a new piece
        self.piece.setRandomGoodShape()

        while True:
            # find appropriate beginning point (X, Y) for placing new Piece
            x0, y0 = self.getStartPoint()

            # check overlapping with another piece
            if not self.isOverlap(x0, y0):
                break

        # place new piece on the Board element by element
        self.placePiece(x0, y0)


    def tryMovePlane(self, newX, newY):
        """ Moves plane on desired location if it can be done. """
        maxX = newX + self.planePiece.maxX()
        maxY = newY + self.planePiece.maxY()
        minX = newX + self.planePiece.minX()
        minY = newY + self.planePiece.minY()

        if minX < 0 or maxX >= Board.BoardWidth or \
           minY < 0 or maxY >= Board.BoardHeight: return False

        self.planeCurX = newX
        self.planeCurY = newY

        self.update()

        return True


    def moveBoard(self):
        """
        Moves all of the elements on 'Board' one step to the left.

        Flying effect is reached with such a 'moving' Board.

        """

        for i in range(Board.BoardWidth):
            for j in range(Board.BoardHeight):
                self.setShapeAt(i, j, self.shapeAt(i+1, j))

                # for "fading pieces" on the left side
                if i == 0 and self.shapeAt(i, j) != Shape.NoShape:
                    self.setShapeAt(i, j, Shape.NoShape)

        self.conflict()
        self.update()


    def conflict(self):
        """ Checks if plane has something ahead: good or bad type of piece. """
        for i in range(self.planePiece.size()):
            x = self.planeCurX + self.planePiece.x(i)
            y = self.planeCurY + self.planePiece.y(i)

            if self.shapeAt(x, y) != Shape.NoShape:
                self.conflictResolution(self.shapeAt(x, y), x, y)


    def conflictResolution(self, shape, x, y):
        """ Rewards the user accordingly with the type of piece. """
        if shape in [Shape.DoubleShape, Shape.TripleShape]:
            self.score += 10
            self.setShapeAt(x, y, Shape.NoShape)

        else:
            self.timer.stop()
            self.isStarted = False
            msg = 'GAME OVER: Total score %d! For another round press <Enter>' % self.score
            self.emit(SIGNAL('messageToStatusbar(QString)'), msg)




class Shape(object):
    """
    Contains all types of shapes for the 'Board'.

    Holds all information about every type of shape: color, coordinates,
    groups, sizes, etc.

    """

    NoShape = 0
    PlaneShape = 1
    DoubleShape = 2
    TripleShape = 3
    StarShape = 4
    IShape = 5
    RectHorizontalShape = 6
    SquareShape = 7

    CoordsTable = {
        NoShape: ((0, 0),),
        PlaneShape: ((0, 0), (0, 1), (0, 2), (1, 1), (2, 0), (2, 1), (2, 2), (3, 1)),
        DoubleShape: ((0, 0), (1, 0)),
        TripleShape: ((0, 0), (1, 0), (2, 0)),
        StarShape: ((1, 0), (0, 1), (1, 1), (2, 1), (1, 2)),
        IShape: ((0, 0), (1, 0), (2, 0), (1, 1), (1, 2), (0, 2), (2, 2)),
        RectHorizontalShape: ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1), (3, 0), (3, 1)),
        SquareShape: ((0, 0), (1, 0), (0, 1), (1, 1))
    }

    ColorTable = {
        NoShape: 0x000000,
        PlaneShape: 0x36648B,
        DoubleShape: 0xFFCC00,
        TripleShape: 0xFF9900,
        StarShape: 0x8B7355,
        IShape: 0x8B6969,
        RectHorizontalShape: 0x8B2252,
        SquareShape: 0x8B3A3A
    }

    @classmethod
    def goodPieces(cls):
        """ Returns list of pieces, which helps increase score points. """
        return [cls.TripleShape, cls.DoubleShape]


    @classmethod
    def badPieces(cls):
        """ Returns list of bad pieces. """
        return [cls.StarShape, cls.IShape, cls.RectHorizontalShape, cls.SquareShape]


    def __init__(self):
        """ Initializes default shape = NoShape """
        self.setShape(Shape.NoShape)
        self._maxSizes = {}


    def shape(self):
        """ Returns current shape. """
        return self._shape


    def setShape(self, shape):
        """ Sets 'shape' and coordinates. """
        self.coords = Shape.CoordsTable[shape]
        self._shape = shape


    def size(self):
        """ Returns length of current shape coordinates. """
        return len(Shape.CoordsTable[self._shape])


    def maxSizes(self):
        """ Returns maximum width and height of current shape.

        Doesn't calculate values on every call, computes them only once
        in order to fill dict with them.
        """

        # prevents recalculation of sizes after every call
        if not self._maxSizes.has_key(self._shape):
            x_max = max([point[X] for point in self.coords])
            y_max = max([point[Y] for point in self.coords])

            # coordinates begin from (0,0) => size + 1
            self._maxSizes[self._shape] = (x_max+1, y_max+1)

        return self._maxSizes[self._shape]


    def setRandomBadShape(self):
        """ Sets random shape of bad type """
        self.setShape(random.choice(Shape.badPieces()))


    def setRandomGoodShape(self):
        """ Sets random shape of good type """
        self.setShape(random.choice(Shape.goodPieces()))


    def x(self, index):
        return self.coords[index][0]


    def y(self, index):
        return self.coords[index][1]


    def minX(self):
        """ Returns the lowest X-point of the current shape. """
        m = self.coords[0][0]
        for i in range(len(self.coords)):
            m = min(m, self.coords[i][0])

        return m


    def maxX(self):
        """ Returns the highest X-point of the current shape. """
        m = self.coords[0][0]
        for i in range(len(self.coords)):
            m = max(m, self.coords[i][0])

        return m


    def minY(self):
        """ Returns the lowest Y-point of the current shape. """
        m = self.coords[0][1]
        for i in range(len(self.coords)):
            m = min(m, self.coords[i][1])

        return m


    def maxY(self):
        """ Returns the highest Y-point of the current shape. """
        m = self.coords[0][1]
        for i in range(len(self.coords)):
            m = max(m, self.coords[i][1])

        return m




if __name__ == '__main__':
    app = QApplication(sys.argv)
    plane = Plane()
    plane.show()
    sys.exit(app.exec_())


