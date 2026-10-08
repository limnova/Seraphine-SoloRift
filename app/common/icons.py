from enum import Enum

from .qfluentwidgets import getIconColor, Theme, FluentIconBase
from PyQt5.QtGui import QIcon


class Icon(FluentIconBase, Enum):
    PERSON = 'Person'
    GAME = 'Game'
    SEARCH = 'Search'
    FOLDER = 'Folder'
    BRUSH = 'Brush'
    PALETTE = 'Palette'
    CIRCLERIGHT = 'CircleRight'
    ZOOMFIT = 'ZoomFit'
    WRENCH = 'Wrench'
    HOME = 'Home'
    SLIDESEARCH = 'SlideSearch'
    CHEVRONLEFT = "ChevronLeft"
    CHEVRONRIGHT = "ChevronRight"
    GRAYCHEVRONRIGHT = "GrayChevronRight"
    COPY = 'Copy'
    CIRCLEMARK = 'CircleMark'
    TROPHY = 'Trophy'
    FEEDBACK = 'Feedback'
    INFO = 'Info'
    DELETE = 'Delete'
    BLUR = 'Blur'
    GITHUB = 'Github'
    EYES = "Eyes"
    CHECK = 'Check'
    EXIT = 'Exit'
    LOCK = 'Lock'
    SETTING = 'Setting'
    FILTER = 'Filter'
    UPDATE = 'Update'
    CONNECTION = "Connection"
    ARROWCIRCLE = 'ArrowCircle'
    SCALEFIT = 'ScaleFit'
    LOG = 'Log'
    ALERT = 'Alert'
    PLANE = 'Plane'
    APPLIST = 'AppList'
    SQUARECROSS = "SquareCross"
    BACKGROUNDCOLOR = 'BackgroundColor'
    DUALSCREEN = 'DualScreen'
    TEXTCHECK = 'TextCheck'
    DOCUMENT = 'Document'
    ARROWREPEAT = "ArrowRepeat"
    QUESTION_CIRCLE = 'QuestionCircle'
    WINDOW = "Window"
    ATTACHTEXT = "AttachText"
    TEXTCOLOR = "TextColor"
    SNOOZE = "Snooze"
    PADDINGTOP = "PaddingTop"
    CHECKBOXFILL = "CheckBoxFill"

    def path(self, theme=Theme.AUTO):
        return f'./app/resource/icons/{self.value}_{getIconColor(theme)}.svg'
