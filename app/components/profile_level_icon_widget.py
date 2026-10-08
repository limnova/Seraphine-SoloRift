import sys

from PyQt5.QtCore import (Qt, QRectF, QPoint, QPropertyAnimation, QParallelAnimationGroup,
                          QEasingCurve, QSize, QRect)
from PyQt5.QtGui import QHideEvent, QPainter, QPainterPath, QPen, QFont, QPixmap, QColor
from PyQt5.QtWidgets import (QWidget, QApplication, QMainWindow, QHBoxLayout)

from app.common.qfluentwidgets import (ProgressRing, ToolTipFilter, ToolTipPosition, isDarkTheme,
                                       themeColor)


class ProgressArc(ProgressRing):
    def __init__(self, parent=None, useAni=True, text="", fontSize=10):
        self.text = text
        self.fontSize = fontSize
        self.drawVal = 0
        self.ringGap = 30
        super().__init__(parent, useAni=useAni)

    def paintEvent(self, e):
        # 有值取值, 没值保持; self.val 在控件刚实例化时, 前几次update可能会为0
        self.drawVal = self.val or self.drawVal
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        cw = self._strokeWidth  # circle thickness
        w = min(self.height(), self.width()) - cw
        rc = QRectF(cw / 2, self.height() / 2 - w / 2, w, w)

        # draw background
        bc = self.darkBackgroundColor if isDarkTheme() else self.lightBackgroundColor
        pen = QPen(bc, cw, cap=Qt.RoundCap, join=Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawArc(rc, (self.ringGap-90)*16, (360-2*self.ringGap)*16)

        if self.maximum() <= self.minimum():
            return

        # draw bar
        pen.setColor(themeColor())
        painter.setPen(pen)
        degree = int(self.drawVal / (self.maximum() -
                     self.minimum()) * (360 - 2*self.ringGap))
        painter.drawArc(rc, -(self.ringGap + 90) * 16, -degree * 16)

        painter.setFont(QFont('Microsoft YaHei', self.fontSize, QFont.Bold))
        text_rect = QRectF(0, self.height() * 0.88,
                           self.width(), self.height() * 0.12)

        painter.drawText(text_rect, Qt.AlignCenter, f"{self.text}")


class RoundLevelAvatar(QWidget):
    def __init__(self,
                 icon,
                 xpSinceLastLevel,
                 xpUntilNextLevel,
                 diameter=100,
                 text="",
                 parent=None):
        super().__init__(parent)
        self.diameter = diameter
        self.sep = .3 * diameter
        self.iconPath = icon

        self.image = QPixmap(self.iconPath)

        self.setFixedSize(self.diameter, self.diameter)

        self.xpSinceLastLevel = xpSinceLastLevel
        self.xpUntilNextLevel = xpUntilNextLevel
        self.progressRing = ProgressArc(
            self, text=text, fontSize=int(.09 * diameter))
        self.progressRing.setTextVisible(False)
        self.progressRing.setFixedSize(self.diameter, self.diameter)

        # self.setToolTip(f"Exp: {xpSinceLastLevel} / {xpUntilNextLevel}")
        self.installEventFilter(ToolTipFilter(self, 250, ToolTipPosition.TOP))
        self.paintXpSinceLastLevel = None
        self.paintXpUntilNextLevel = None
        self.callUpdate = False


    def paintEvent(self, event):
        if self.paintXpSinceLastLevel != self.xpSinceLastLevel or self.paintXpUntilNextLevel != self.xpUntilNextLevel or self.callUpdate:
            self.progressRing.setVal(self.xpSinceLastLevel * 100 //
                                     self.xpUntilNextLevel if self.xpSinceLastLevel != 0 else 1)
            self.paintXpUntilNextLevel = self.xpUntilNextLevel
            self.paintXpSinceLastLevel = self.xpSinceLastLevel
            self.callUpdate = False

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        size = (self.size() - QSize(int(self.sep), int(self.sep))) * \
            self.devicePixelRatioF()

        image = self.image
        if 'champion' in self.iconPath:
            width = image.width() - 10
            height = image.height() - 10
            image = image.copy(5, 5, width, height)

        scaledImage = image.scaled(size,
                                   Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                   Qt.TransformationMode.SmoothTransformation)

        clipPath = QPainterPath()

        rect = QRectF(self.sep // 2, self.sep // 2,
                      self.width() - self.sep,
                      self.height() - self.sep)
        clipPath.addEllipse(rect)

        painter.setClipPath(clipPath)
        painter.drawPixmap(rect.toRect(), scaledImage)

    def updateIcon(self, icon: str, xpSinceLastLevel=None, xpUntilNextLevel=None, text=""):
        self.iconPath = icon
        self.image = QPixmap(self.iconPath)

        if xpSinceLastLevel is not None and xpUntilNextLevel is not None:
            self.xpSinceLastLevel = xpSinceLastLevel
            self.xpUntilNextLevel = xpUntilNextLevel

            # self.setToolTip(f"Exp: {xpSinceLastLevel} / {xpUntilNextLevel}")

        if text:
            self.progressRing.text = text

        self.callUpdate = True
        self.repaint()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = QMainWindow()
    window.setWindowTitle("Round Icon Demo")
    window.setGeometry(100, 100, 600, 400)

    widget = QWidget(window)
    window.setCentralWidget(widget)

    layout = QHBoxLayout(widget)

    icon1 = RoundLevelAvatar("../resource/images/logo.png",
                             75,
                             100,
                             diameter=70)
    icon1.setParent(window)

    layout.addWidget(icon1)
    window.show()
    sys.exit(app.exec())
