import asyncio
import os
import stat

from PyQt5.QtCore import Qt, pyqtSignal, QEvent, QSize, QObject
from PyQt5.QtWidgets import (QWidget, QLabel, QHBoxLayout, QGridLayout,
                             QFrame, QSpacerItem, QSizePolicy, QCompleter)
from qasync import asyncSlot
from qfluentwidgets import EditableComboBox

from app.common.config import cfg
from app.common.icons import Icon
from app.common.qfluentwidgets import (SettingCardGroup, SwitchSettingCard, ExpandLayout,
                                       SettingCard, PushButton,
                                       setCustomStyleSheet, ComboBox, SwitchButton, ConfigItem,
                                       qconfig, IndicatorPosition, InfoBar, InfoBarPosition,
                                       SpinBox, ExpandGroupSettingCard, TransparentToolButton,
                                       FluentIcon, Flyout, FlyoutAnimationType, ToolTipFilter,
                                       ToolTipPosition)
from app.common.style_sheet import StyleSheet
from app.components.champion_icon_widget import RoundIcon, SummonerSpellButton
from app.components.message_box import MultiChampionSelectMsgBox
from app.components.seraphine_interface import SeraphineInterface
from app.components.summoner_spell_widget import SummonerSpellSelectFlyout
from app.lol.connector import connector
from app.lol.exceptions import *
from app.lol.tools import fixLCUWindowViaExe


class AuxiliaryInterface(SeraphineInterface):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)

        self.titleLabel = QLabel(self.tr("Auxiliary Functions"), self)

        self.gameGroup = SettingCardGroup(self.tr("Game"), self.scrollWidget)
        self.bpGroup = SettingCardGroup(
            self.tr("Ban / Pick"), self.scrollWidget)
        self.clientGroup = SettingCardGroup(
            self.tr("Client"), self.scrollWidget)

        self.lockConfigCard = LockConfigCard(
            self.tr("Lock config"),
            self.tr("Make your game config unchangeable"),
            self.gameGroup)

        self.fixDpiCard = FixClientDpiCard(
            self.tr("Fix client window"),
            self.tr(
                "Fix incorrect client window size caused by DirectX 9 (need UAC)"),
            self.clientGroup
        )
        self.restartClientCard = RestartClientCard(
            self.tr("Restart client"),
            self.tr("Restart the LOL client without re queuing"),
            self.clientGroup
        )

        self.autoReconnectCard = SwitchSettingCard(
            Icon.CONNECTION,
            self.tr("Auto reconnect"),
            self.tr("Automatically reconnect when disconnected"),
            cfg.enableAutoReconnect, self.gameGroup)
        self.spectateCard = SpectateCard(
            self.tr("Spectate"),
            self.tr("Spectate live game of summoner in the same environment"),
            self.gameGroup
        )

        self.autoAcceptMatchingCard = AutoAcceptMatchingCard(
            self.tr("Auto accept"),
            self.tr(
                "Accept match making automatically after the number of seconds you set"),
            cfg.enableAutoAcceptMatching, cfg.autoAcceptMatchingDelay,
            self.bpGroup)
        self.autoAcceptSwapingCard = AutoAcceptSwapingCard(
            self.tr("Auto accept swaping"),
            self.tr(
                "Accept ceil or champion swaping requests during B/P"),
            cfg.autoAcceptCeilSwap, cfg.autoAcceptChampTrade,
            self.bpGroup)
        self.autoSelectChampionCard = AutoSelectChampionCard(
            self.tr("Auto select champion"),
            self.tr("Auto select champion when your selection begins"),
            cfg.enableAutoSelectChampion,
            cfg.autoSelectChampion,
            cfg.autoSelectChampionTop,
            cfg.autoSelectChampionJug,
            cfg.autoSelectChampionMid,
            cfg.autoSelectChampionBot,
            cfg.autoSelectChampionSup,
            cfg.enableAutoSelectTimeoutCompleted,
            self.bpGroup)
        self.autoBanChampionsCard = AutoBanChampionCard(
            self.tr("Auto ban champion"),
            self.tr("Auto ban champion when your ban section begins"),
            cfg.enableAutoBanChampion,
            cfg.autoBanChampion,
            cfg.autoBanChampionTop,
            cfg.autoBanChampionJug,
            cfg.autoBanChampionMid,
            cfg.autoBanChampionBot,
            cfg.autoBanChampionSup,
            cfg.pretentBan,
            cfg.autoBanDelay,
            self.bpGroup)
        self.autoSetSpellCard = AutoSetSummonerSpellCard(
            self.tr("Auto set summoner spells"),
            self.tr("Auto set your summoner spells when champion selection begins"),
            cfg.enableAutoSetSpells,
            cfg.autoSetSummonerSpell,
            cfg.autoSetSummonerSpellTop,
            cfg.autoSetSummonerSpellJug,
            cfg.autoSetSummonerSpellMid,
            cfg.autoSetSummonerSpellBot,
            cfg.autoSetSummonerSpellSup,
            self.bpGroup
        )

        self.__initWidget()
        self.__initLayout()

    def __initWidget(self):
        self.titleLabel.setObjectName("titleLabel")
        self.scrollWidget.setObjectName('scrollWidget')

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 90, 0, 20)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)

        StyleSheet.AUXILIARY_INTERFACE.apply(self)

    def __initLayout(self):
        self.titleLabel.move(36, 30)

        # BP
        self.bpGroup.addSettingCard(self.autoAcceptMatchingCard)
        self.bpGroup.addSettingCard(self.autoAcceptSwapingCard)
        self.bpGroup.addSettingCard(self.autoSelectChampionCard)
        self.bpGroup.addSettingCard(self.autoBanChampionsCard)
        self.bpGroup.addSettingCard(self.autoSetSpellCard)

        # 游戏
        self.gameGroup.addSettingCard(self.autoReconnectCard)
        self.gameGroup.addSettingCard(self.spectateCard)
        self.gameGroup.addSettingCard(self.lockConfigCard)

        # 客户端修复
        self.clientGroup.addSettingCard(self.fixDpiCard)
        self.clientGroup.addSettingCard(self.restartClientCard)

        self.expandLayout.setSpacing(30)
        self.expandLayout.setContentsMargins(36, 0, 36, 0)
        self.expandLayout.addWidget(self.bpGroup)
        self.expandLayout.addWidget(self.gameGroup)
        self.expandLayout.addWidget(self.clientGroup)

    async def initChampionList(self):
        async def initChampions():
            champions = await self.autoSelectChampionCard.initChampionList()
            await self.autoBanChampionsCard.initChampionList(champions)

        async def initSummonerSpell():
            await self.autoSetSpellCard.initSummonerSpells()

        await asyncio.gather(initChampions(), initSummonerSpell())


class FixClientDpiCard(SettingCard):

    def __init__(self, title, content, parent):
        super().__init__(Icon.SCALEFIT, title, content, parent)
        self.pushButton = PushButton(self.tr("Fix"))
        self.pushButton.setMinimumWidth(100)

        self.hBoxLayout.addWidget(self.pushButton)
        self.hBoxLayout.addSpacing(16)

        self.pushButton.clicked.connect(self.__onButtonClicked)

    @asyncSlot()
    async def __onButtonClicked(self):
        await fixLCUWindowViaExe()


class RestartClientCard(SettingCard):

    def __init__(self, title, content, parent):
        super().__init__(Icon.ARROWREPEAT, title, content, parent)
        self.pushButton = PushButton(self.tr("Restart"))
        self.pushButton.setMinimumWidth(100)

        self.hBoxLayout.addWidget(self.pushButton)
        self.hBoxLayout.addSpacing(16)

        self.pushButton.clicked.connect(self.__onButtonClicked)

    @asyncSlot()
    async def __onButtonClicked(self):
        await connector.restartClient()
class SpectateCard(ExpandGroupSettingCard):
    def __init__(self, title, content=None, parent=None):
        super().__init__(Icon.EYES, title, content, parent)

        self.inputWidget = QWidget(self.view)
        self.inputLayout = QGridLayout(self.inputWidget)

        self.summonerNameLabel = QLabel(
            self.tr("Summoner's name you want to spectate:"))
        self.spectateNameComboBox = EditableComboBox()

        self.spectateTypeLabel = QLabel(self.tr("Method:"))
        self.spectateTypeComboBox = ComboBox()

        self.buttonWidget = QWidget(self.view)
        self.buttonLayout = QHBoxLayout(self.buttonWidget)
        self.button = PushButton(self.tr("Spectate"))

        self.__initLayout()
        self.__initWidget()

    def __initLayout(self):
        self.inputLayout.setVerticalSpacing(19)
        self.inputLayout.setAlignment(Qt.AlignTop)
        self.inputLayout.setContentsMargins(48, 18, 44, 18)

        self.inputLayout.addWidget(
            self.summonerNameLabel, 0, 0, alignment=Qt.AlignLeft)
        self.inputLayout.addWidget(
            self.spectateNameComboBox, 0, 1, alignment=Qt.AlignRight)
        self.inputLayout.addWidget(
            self.spectateTypeLabel, 1, 0, alignment=Qt.AlignLeft)
        self.inputLayout.addWidget(
            self.spectateTypeComboBox, 1, 1, alignment=Qt.AlignRight)

        self.inputLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)

        self.buttonLayout.setContentsMargins(48, 18, 44, 18)
        self.buttonLayout.addWidget(self.button, 0, Qt.AlignRight)
        self.buttonLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)

        self.viewLayout.setSpacing(0)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        self.addGroupWidget(self.inputWidget)
        self.addGroupWidget(self.buttonWidget)

    def __initWidget(self):
        self.spectateNameComboBox.setPlaceholderText(
            self.tr("Please input summoner's name"))
        self.spectateNameComboBox.setMinimumWidth(250)
        self.spectateNameComboBox.setClearButtonEnabled(True)

        self.button.setMinimumWidth(100)
        self.button.setEnabled(False)

        self.spectateTypeComboBox.addItem("LCU API", userData="LCU")
        self.spectateTypeComboBox.addItem(self.tr("CMD"), userData="CMD")
        self.spectateTypeComboBox.setMinimumWidth(100)

        self.spectateNameComboBox.currentTextChanged.connect(self.__onSpectateNameTextChanged)
        self.button.clicked.connect(self.__onButtonClicked)

    def __onSpectateNameTextChanged(self):
        enable = self.spectateNameComboBox.text() != ""
        self.button.setEnabled(enable)
        # FIXME: 点输入框的x号会清除文本，应该监听该事件将按钮禁用

    def setExpand(self, isExpand: bool):
        super().setExpand(isExpand)
        if isExpand:
            asyncio.create_task(self.__initFriendList())

    async def __initFriendList(self):
        res = await connector.getFriends()
        self.spectateNameComboBox.clear()
        items = [f"{i['gameName']}#{i['gameTag']}" for i in res if i.get('availability') != 'offline']
        if len(items) == 0:
            return
        self.spectateNameComboBox.addItems(items)
        self.spectateNameComboBox.setCurrentIndex(-1)
        completer = QCompleter(items, self.spectateNameComboBox)
        self.spectateNameComboBox.setCompleter(completer)

    @asyncSlot()
    async def __onButtonClicked(self):
        def info(type, title, content):
            f = InfoBar.error if type == 'error' else InfoBar.success

            f(title=title, content=content, orient=Qt.Vertical, isClosable=True,
              position=InfoBarPosition.TOP_RIGHT, duration=5000,
              parent=self.window().auxiliaryFuncInterface)

        try:
            text = self.spectateNameComboBox.text()
            text = text.replace('\u2066', '').replace('\u2069', '')

            if self.spectateTypeComboBox.currentData() == 'LCU':
                await connector.spectate(text)
            else:
                await connector.spectateDirectly(text)

        except SummonerNotFound:
            info('error', self.tr("Summoner not found"),
                 self.tr("Please check the summoner's name and retry"))
        except SummonerNotInGame:
            info('error', self.tr("Summoner isn't in game"), "")
        else:
            info('success', self.tr("Spectate successfully"),
                 self.tr("Please wait"), )


class AutoAcceptMatchingCard(ExpandGroupSettingCard):
    def __init__(self, title, content, enableConfigItem: ConfigItem = None,
                 delayConfigItem: ConfigItem = None, parent=None):
        super().__init__(Icon.CIRCLEMARK, title, content, parent)

        self.statusLabel = QLabel(self)

        self.inputWidget = QWidget(self.view)
        self.inputLayout = QHBoxLayout(self.inputWidget)

        self.secondsLabel = QLabel(self.tr("Delay seconds after match made:"))
        self.lineEdit = SpinBox()

        self.switchButtonWidget = QWidget(self.view)
        self.switchButtonLayout = QHBoxLayout(self.switchButtonWidget)

        self.switchButton = SwitchButton(indicatorPos=IndicatorPosition.RIGHT)

        self.enableConfigItem = enableConfigItem
        self.delayConfigItem = delayConfigItem

        self.__initLayout()
        self.__initWidget()

    def __initLayout(self):
        self.addWidget(self.statusLabel)

        self.inputLayout.setSpacing(19)
        self.inputLayout.setAlignment(Qt.AlignTop)
        self.inputLayout.setContentsMargins(48, 18, 44, 18)

        self.inputLayout.addWidget(self.secondsLabel, alignment=Qt.AlignLeft)
        self.inputLayout.addWidget(self.lineEdit, alignment=Qt.AlignRight)
        self.inputLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)

        self.switchButtonLayout.setContentsMargins(48, 18, 44, 18)
        self.switchButtonLayout.addWidget(self.switchButton, 0, Qt.AlignRight)
        self.switchButtonLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)

        self.viewLayout.setSpacing(0)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        self.addGroupWidget(self.inputWidget)
        self.addGroupWidget(self.switchButtonWidget)

    def __initWidget(self):
        self.lineEdit.setRange(0, 11)
        self.lineEdit.setValue(cfg.get(self.delayConfigItem))
        self.lineEdit.setSingleStep(1)
        self.lineEdit.setMinimumWidth(250)

        self.switchButton.setChecked(cfg.get(self.enableConfigItem))

        self.lineEdit.valueChanged.connect(self.__onLineEditValueChanged)
        self.switchButton.checkedChanged.connect(
            self.__onSwitchButtonCheckedChanged)

        value, isChecked = self.lineEdit.value(), self.switchButton.isChecked()
        self.__setStatusLableText(value, isChecked)

    def setValue(self, delay: int, isChecked: bool):
        qconfig.set(self.delayConfigItem, delay)
        qconfig.set(self.enableConfigItem, isChecked)

        self.__setStatusLableText(delay, isChecked)

    def __onSwitchButtonCheckedChanged(self, isChecked: bool):
        self.setValue(self.lineEdit.value(), isChecked)

    def __onLineEditValueChanged(self, value):
        self.setValue(value, self.switchButton.isChecked())

    def __setStatusLableText(self, delay, isChecked):
        if isChecked:
            self.statusLabel.setText(self.tr("Enabled, delay: ") + str(delay) +
                                     self.tr(" seconds"))
        else:
            self.statusLabel.setText(self.tr("Disabled"))


class AutoAcceptSwapingCard(ExpandGroupSettingCard):
    def __init__(self, title, content, enableCeilSwapItem: ConfigItem = None,
                 enableChampSwapItem: ConfigItem = None, parent=None):
        super().__init__(Icon.TEXTCHECK, title, content, parent)

        self.statusLabel = QLabel(self)

        self.switchButtonWidget = QWidget(self.view)
        self.switchButtonLayout = QGridLayout(self.switchButtonWidget)

        self.label1 = QLabel(self.tr("Enable auto accept cail swap request:"))
        self.label2 = QLabel(
            self.tr("Enable auto accept champion trade request:"))

        self.switchButton1 = SwitchButton(indicatorPos=IndicatorPosition.RIGHT)
        self.switchButton2 = SwitchButton(indicatorPos=IndicatorPosition.RIGHT)

        self.enableCeilSwapItem = enableCeilSwapItem
        self.enableChampSwapItem = enableChampSwapItem

        self.__initLayout()
        self.__initWidget()

    def __initLayout(self):
        self.addWidget(self.statusLabel)

        self.switchButtonLayout.setVerticalSpacing(19)
        self.switchButtonLayout.addWidget(self.label1, 0, 0, Qt.AlignLeft)
        self.switchButtonLayout.addWidget(
            self.switchButton1, 0, 1, Qt.AlignRight)
        self.switchButtonLayout.addWidget(
            self.label2, 1, 0, Qt.AlignLeft)
        self.switchButtonLayout.addWidget(
            self.switchButton2, 1, 1, Qt.AlignRight)

        self.switchButtonLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)
        self.switchButtonLayout.setContentsMargins(48, 24, 44, 28)

        self.viewLayout.setSpacing(0)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        self.addGroupWidget(self.switchButtonWidget)

    def __initWidget(self):
        ceilSwap = cfg.get(cfg.autoAcceptCeilSwap)
        champTrade = cfg.get(cfg.autoAcceptChampTrade)

        self.switchButton1.setChecked(ceilSwap)
        self.switchButton2.setChecked(champTrade)

        self.__setStatusLableText()

        self.switchButton1.checkedChanged.connect(
            self.__onSwichButton1CheckedChanged)
        self.switchButton2.checkedChanged.connect(
            self.__onSwichButton2CheckedChanged)

    def __onSwichButton1CheckedChanged(self, isChecked: bool):
        cfg.set(cfg.autoAcceptCeilSwap, isChecked)
        self.__setStatusLableText()

    def __onSwichButton2CheckedChanged(self, isChecked: bool):
        cfg.set(cfg.autoAcceptChampTrade, isChecked)
        self.__setStatusLableText()

    def __setStatusLableText(self):
        ceilSwap = self.switchButton1.isChecked()
        champTrade = self.switchButton2.isChecked()

        if any([ceilSwap, champTrade]):
            self.statusLabel.setText(self.tr("Enabled"))
        else:
            self.statusLabel.setText(self.tr("Disabled"))
class LockConfigCard(SettingCard):
    def __init__(self, title, content, parent):
        super().__init__(Icon.LOCK, title, content, parent)

        self.switchButton = SwitchButton(indicatorPos=IndicatorPosition.RIGHT)

        self.hBoxLayout.addWidget(self.switchButton)
        self.hBoxLayout.addSpacing(16)

        self.switchButton.checkedChanged.connect(self.__onCheckedChanged)

    def loadNowMode(self):
        path = f"{cfg.get(cfg.lolFolder)[0]}/../Game/Config/PersistedSettings.json"

        if not os.path.exists(path):
            self.switchButton.setChecked(False)
            self.switchButton.setEnabled(False)

            return

        try:
            currentMode = stat.S_IMODE(os.lstat(path).st_mode)
            if currentMode == 0o444:
                self.switchButton.setChecked(True)
        except:
            self.switchButton.setEnabled(False)
            pass

    def __onCheckedChanged(self, isChecked: bool):
        if not self.setConfigFileReadOnlyEnabled(isChecked):
            InfoBar.error(
                title=self.tr("Error"),
                content=self.tr("Failed to set file permissions"),
                orient=Qt.Vertical,
                isClosable=True,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=5000,
                parent=self.window(),
            )

            self.switchButton.checkedChanged.disconnect()
            self.switchButton.setChecked(not isChecked)
            self.switchButton.checkedChanged.connect(self.__onCheckedChanged)

    def setConfigFileReadOnlyEnabled(self, enable):
        path = f"{cfg.get(cfg.lolFolder)[0]}/../Game/Config/PersistedSettings.json"

        if not os.path.exists(path):
            return False

        mode = 0o444 if enable else 0o666
        try:
            os.chmod(path, mode)
            currentMode = stat.S_IMODE(os.lstat(path).st_mode)

            if currentMode != mode:
                return False
        except:
            self.switchButton.setEnabled(False)
            return False

        return True
class AutoSelectChampionCard(ExpandGroupSettingCard):
    def __init__(self, title, content=None,
                 enableConfigItem: ConfigItem = None,
                 championsConfigItem: ConfigItem = None,
                 topChampionsConfigItem: ConfigItem = None,
                 jugChampionsConfigItem: ConfigItem = None,
                 midChampionsConfigItem: ConfigItem = None,
                 botChampionsConfigItem: ConfigItem = None,
                 supChampionsConfigItem: ConfigItem = None,
                 enableTimeoutCompleteCfgItem: ConfigItem = None,
                 parent=None):
        super().__init__(Icon.CHECK, title, content, parent)

        self.champions = {}

        self.enableConfigItem = enableConfigItem
        self.defaultChampionsConfigItem = championsConfigItem
        self.topChampionsConfigItem = topChampionsConfigItem
        self.jugChampionsConfigItem = jugChampionsConfigItem
        self.midChampionsConfigItem = midChampionsConfigItem
        self.botChampionsConfigItem = botChampionsConfigItem
        self.supChampionsConfigItem = supChampionsConfigItem
        self.enableTimeoutCompleteCfgItem = enableTimeoutCompleteCfgItem

        self.statusLabel = QLabel()

        self.defaultCfgWidget = QWidget(self.view)
        self.defaultCfgLayout = QGridLayout(self.defaultCfgWidget)
        self.defaultHintLabel = QLabel(self.tr("Default Configurations"))
        self.helpLayout = QHBoxLayout()
        self.helpButotn = TransparentToolButton(Icon.QUESTION_CIRCLE)

        self.defaultLabel = QLabel(self.tr("Default champions: "))
        self.defaultChampions = ChampionsCard()
        self.defaultSelectButton = PushButton(self.tr("Choose"))

        self.rankCfgWidget = QWidget(self.view)
        self.rankCfgLayout = QGridLayout(self.rankCfgWidget)
        self.rankLabel = QLabel(self.tr("Rank Configurations"))

        self.topLabel = QLabel(self.tr("Top: "))
        self.jugLabel = QLabel(self.tr("Juggle: "))
        self.midLabel = QLabel(self.tr("Mid: "))
        self.botLabel = QLabel(self.tr("Bottom: "))
        self.supLabel = QLabel(self.tr("Support: "))
        self.topChampions = ChampionsCard()
        self.jugChampions = ChampionsCard()
        self.midChampions = ChampionsCard()
        self.botChampions = ChampionsCard()
        self.supChampions = ChampionsCard()
        self.topSelectButton = PushButton(self.tr("Choose"))
        self.jugSelectButton = PushButton(self.tr("Choose"))
        self.midSelectButton = PushButton(self.tr("Choose"))
        self.botSelectButton = PushButton(self.tr("Choose"))
        self.supSelectButton = PushButton(self.tr("Choose"))

        self.buttonsWidget = QWidget(self.view)
        self.buttonsLayout = QGridLayout(self.buttonsWidget)
        self.enableLabel = QLabel(self.tr("Enable:"))
        self.enableSwitchButton = SwitchButton(
            indicatorPos=IndicatorPosition.RIGHT)
        self.enableTimeoutCompleteLabel = QLabel(
            self.tr("Completed before timeout:"))
        self.enableTimeoutSwtichButton = SwitchButton(
            indicatorPos=IndicatorPosition.RIGHT)
        self.resetButton = PushButton(self.tr("Reset"))

        self.__initWidget()
        self.__initLayout()

    def __initWidget(self):
        self.defaultHintLabel.setStyleSheet("font: bold")
        self.rankLabel.setStyleSheet("font: bold")

        self.helpButotn.setFixedSize(QSize(26, 26))
        self.helpButotn.setIconSize(QSize(16, 16))

        self.helpButotn.setToolTip(self.tr(
            "Default settings must be set.\n\nIf champions set by lane are not available, default settings will be used."))
        self.helpButotn.installEventFilter(ToolTipFilter(
            self.helpButotn, 0, ToolTipPosition.RIGHT))

        # 逻辑是，必须要设置默认，才能设置具体分路和启动功能
        selected = qconfig.get(self.defaultChampionsConfigItem) != []
        checked = qconfig.get(self.enableConfigItem)
        timeoutChecked = qconfig.get(self.enableTimeoutCompleteCfgItem)

        for ty in ['default', 'top', 'jug', 'mid', 'bot', 'sup']:
            button: PushButton = getattr(self, f"{ty}SelectButton")
            button.setMinimumWidth(100)
            button.clicked.connect(lambda _, t=ty: self.__onButtonClicked(t))

            if ty != 'default':
                button.setEnabled(selected)

        self.enableSwitchButton.checkedChanged.connect(
            self.__onEnableSelectChanged)
        self.enableSwitchButton.setEnabled(selected)
        self.enableSwitchButton.setChecked(checked)

        self.enableTimeoutSwtichButton.checkedChanged.connect(
            self.__onEnableTimeoutCompleteChanged)
        self.enableTimeoutSwtichButton.setEnabled(checked)
        self.enableTimeoutSwtichButton.setChecked(timeoutChecked)

        self.resetButton.clicked.connect(self.__onResetButtonClicked)
        self.resetButton.setMinimumWidth(100)

        self.__updateStatusLabel()

    def __initLayout(self):
        self.addWidget(self.statusLabel)

        self.defaultCfgLayout.setVerticalSpacing(19)
        self.defaultCfgLayout.setContentsMargins(48, 18, 44, 18)
        self.defaultCfgLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)

        self.helpLayout.setContentsMargins(0, 0, 0, 0)
        self.helpLayout.setSpacing(10)
        self.helpLayout.addWidget(self.defaultHintLabel)
        self.helpLayout.addWidget(self.helpButotn)

        self.defaultCfgLayout.addLayout(
            self.helpLayout, 0, 0, Qt.AlignLeft)

        self.defaultCfgLayout.addWidget(
            self.defaultLabel, 1, 0, Qt.AlignLeft)
        self.defaultCfgLayout.addWidget(
            self.defaultChampions, 1, 1, Qt.AlignHCenter)
        self.defaultCfgLayout.addWidget(
            self.defaultSelectButton, 1, 2, Qt.AlignRight)

        self.rankCfgLayout.setVerticalSpacing(19)
        self.rankCfgLayout.setContentsMargins(48, 18, 44, 18)
        self.rankCfgLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)

        self.rankCfgLayout.addWidget(self.rankLabel, 0, 0, Qt.AlignLeft)

        for i, ty in enumerate(['top', 'jug', 'mid', 'bot', 'sup']):
            label = getattr(self, f"{ty}Label")
            champions = getattr(self, f"{ty}Champions")
            button = getattr(self, f"{ty}SelectButton")

            self.rankCfgLayout.addWidget(label, i + 1, 0, Qt.AlignLeft)
            self.rankCfgLayout.addWidget(champions, i + 1, 1, Qt.AlignHCenter)
            self.rankCfgLayout.addWidget(button, i + 1, 2, Qt.AlignRight)

        self.buttonsLayout.setVerticalSpacing(19)
        self.buttonsLayout.setContentsMargins(48, 18, 44, 18)
        self.buttonsLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)

        self.buttonsLayout.addWidget(
            self.enableLabel, 0, 0, Qt.AlignLeft)
        self.buttonsLayout.addWidget(
            self.enableSwitchButton, 0, 1, Qt.AlignRight)
        self.buttonsLayout.addWidget(
            self.enableTimeoutCompleteLabel, 1, 0, Qt.AlignLeft)
        self.buttonsLayout.addWidget(
            self.enableTimeoutSwtichButton, 1, 1, Qt.AlignRight)
        self.buttonsLayout.addWidget(
            self.resetButton, 2, 1, Qt.AlignRight)

        self.viewLayout.setSpacing(0)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)

        self.addGroupWidget(self.defaultCfgWidget)
        self.addGroupWidget(self.rankCfgWidget)
        self.addGroupWidget(self.buttonsWidget)

    async def initChampionList(self, champions: dict = None):
        if champions:
            self.champions = champions
        else:
            self.champions = {
                i: [name, await connector.getChampionIcon(i)]
                for i, name in connector.manager.getChampions().items()
                if i != -1
            }

        for ty in ['default', 'top', 'jug', 'mid', 'bot', 'sup']:
            configItem = getattr(self, f"{ty}ChampionsConfigItem")
            champions: ChampionsCard = getattr(self, f"{ty}Champions")
            selected = qconfig.get(configItem)

            champions.clearRequested.connect(
                lambda t=ty: self.__onChampionsChanged([], t))

            if not (type(selected) is list and all(type(s) is int for s in selected)):
                selected = []
                qconfig.set(configItem, selected)

            if len(selected) == 0:
                continue

            champions.updateChampions(
                [self.champions[id][1] for id in selected])

        return self.champions

    def __onButtonClicked(self, type: str):
        configItem: ConfigItem = getattr(self, f"{type}ChampionsConfigItem")
        selected = qconfig.get(configItem)

        box = MultiChampionSelectMsgBox(
            self.champions, selected, self.window())
        box.completed.connect(
            lambda champions, t=type: self.__onChampionsChanged(champions, t))
        box.exec()

    def __onChampionsChanged(self, champions: list, type: str):
        configItem = getattr(self, f"{type}ChampionsConfigItem")
        qconfig.set(configItem, champions)

        card: ChampionsCard = getattr(self, f"{type}Champions")
        card.updateChampions(
            [self.champions[id][1] for id in champions])

        if type != 'default':
            return

        if len(champions) == 0:
            self.enableSwitchButton.setChecked(False)
            self.enableSwitchButton.setEnabled(False)
            self.enableTimeoutSwtichButton.setChecked(False)
            self.enableTimeoutSwtichButton.setEnabled(False)
            buttonEnable = False
        else:
            self.enableSwitchButton.setEnabled(True)
            buttonEnable = True

        for ty in ['top', 'jug', 'mid', 'bot', 'sup']:
            button: PushButton = getattr(self, f"{ty}SelectButton")
            button.setEnabled(buttonEnable)

    def __onEnableSelectChanged(self, checked):
        qconfig.set(self.enableConfigItem, checked)

        for ty in ['default', 'top', 'jug', 'mid', 'bot', 'sup']:
            button: PushButton = getattr(self, f"{ty}SelectButton")
            button.setEnabled(not checked)

        self.enableTimeoutSwtichButton.setEnabled(checked)

        if not checked:
            self.enableTimeoutSwtichButton.setChecked(False)

        self.__updateStatusLabel()

    def __onEnableTimeoutCompleteChanged(self, checked):
        qconfig.set(self.enableTimeoutCompleteCfgItem, checked)

    def __updateStatusLabel(self):
        checked = self.enableSwitchButton.isChecked()

        text = self.tr("Enabled") if checked else self.tr("Disabled")
        self.statusLabel.setText(text)

    def __onResetButtonClicked(self):
        for ty in ['default', 'top', 'jug', 'mid', 'bot', 'sup']:
            self.__onChampionsChanged([], ty)


class AutoBanChampionCard(ExpandGroupSettingCard):
    def __init__(self, title, content=None,
                 enableConfigItem: ConfigItem = None,
                 championsConfigItem: ConfigItem = None,
                 topChampionsConfigItem: ConfigItem = None,
                 jugChampionsConfigItem: ConfigItem = None,
                 midChampionsConfigItem: ConfigItem = None,
                 botChampionsConfigItem: ConfigItem = None,
                 supChampionsConfigItem: ConfigItem = None,
                 friendlyConfigItem: ConfigItem = None,
                 delayTimeConfigItem: ConfigItem = None, parent=None):
        super().__init__(Icon.SQUARECROSS, title, content, parent)

        self.champions = {}

        self.enableConfigItem = enableConfigItem
        self.defaultChampionsConfigItem = championsConfigItem
        self.topChampionsConfigItem = topChampionsConfigItem
        self.jugChampionsConfigItem = jugChampionsConfigItem
        self.midChampionsConfigItem = midChampionsConfigItem
        self.botChampionsConfigItem = botChampionsConfigItem
        self.supChampionsConfigItem = supChampionsConfigItem

        self.friendlyConfigItem = friendlyConfigItem
        self.delayTimeConfigItem = delayTimeConfigItem

        self.statusLabel = QLabel()

        self.defaultCfgWidget = QWidget(self.view)
        self.defaultCfgLayout = QGridLayout(self.defaultCfgWidget)
        self.defaultHintLabel = QLabel(self.tr("Default Configurations"))
        self.helpLayout = QHBoxLayout()
        self.helpButotn = TransparentToolButton(Icon.QUESTION_CIRCLE)

        self.defaultLabel = QLabel(self.tr("Default champions: "))
        self.defaultChampions = ChampionsCard()
        self.defaultSelectButton = PushButton(self.tr("Choose"))

        self.rankCfgWidget = QWidget(self.view)
        self.rankCfgLayout = QGridLayout(self.rankCfgWidget)
        self.rankLabel = QLabel(self.tr("Rank Configurations"))

        self.topLabel = QLabel(self.tr("Top: "))
        self.jugLabel = QLabel(self.tr("Juggle: "))
        self.midLabel = QLabel(self.tr("Mid: "))
        self.botLabel = QLabel(self.tr("Bottom: "))
        self.supLabel = QLabel(self.tr("Support: "))
        self.topChampions = ChampionsCard()
        self.jugChampions = ChampionsCard()
        self.midChampions = ChampionsCard()
        self.botChampions = ChampionsCard()
        self.supChampions = ChampionsCard()
        self.topSelectButton = PushButton(self.tr("Choose"))
        self.jugSelectButton = PushButton(self.tr("Choose"))
        self.midSelectButton = PushButton(self.tr("Choose"))
        self.botSelectButton = PushButton(self.tr("Choose"))
        self.supSelectButton = PushButton(self.tr("Choose"))

        self.buttonsCfgWidget = QWidget(self.view)
        self.buttonsCfgLayout = QGridLayout(self.buttonsCfgWidget)
        self.delayLabel = QLabel(self.tr("Ban after a delay of seconds:"))
        self.delaySpinBox = SpinBox()
        self.enableLabel = QLabel(self.tr("Enable:"))
        self.enableSwitchButton = SwitchButton(
            indicatorPos=IndicatorPosition.RIGHT)
        self.friendlyLabel = QLabel(
            self.tr("Prevent banning champions picked by teammates:"))
        self.friendlySwitchButton = SwitchButton(
            indicatorPos=IndicatorPosition.RIGHT)

        self.resetButton = PushButton(self.tr("Reset"))

        self.__initWidget()
        self.__initLayout()

    def __initWidget(self):
        self.defaultHintLabel.setStyleSheet("font: bold")
        self.rankLabel.setStyleSheet("font: bold")

        haveDefault = qconfig.get(self.defaultChampionsConfigItem) != []
        enabled = qconfig.get(self.enableConfigItem)
        delayTime = qconfig.get(self.delayTimeConfigItem)
        friendlyEnabled = qconfig.get(self.friendlyConfigItem)

        self.helpButotn.setFixedSize(QSize(26, 26))
        self.helpButotn.setIconSize(QSize(16, 16))

        self.helpButotn.setToolTip(self.tr(
            "Default settings must be set.\n\nIf champions set by lane are not available, default settings will be used."))
        self.helpButotn.installEventFilter(ToolTipFilter(
            self.helpButotn, 0, ToolTipPosition.RIGHT))

        for ty in ['default', 'top', 'jug', 'mid', 'bot', 'sup']:
            button: PushButton = getattr(self, f"{ty}SelectButton")
            button.setMinimumWidth(100)
            button.clicked.connect(lambda _, t=ty: self.__onButtonClicked(t))

            if ty != 'default':
                button.setEnabled(haveDefault)

        self.enableSwitchButton.checkedChanged.connect(
            self.__onEnableSwitchButtonClicked)
        self.delaySpinBox.valueChanged.connect(
            self.__onDelaySpinBoxValueChanged)
        self.friendlySwitchButton.checkedChanged.connect(
            self.__onFriendlySwitchButtonClicked)
        self.resetButton.clicked.connect(self.__onResetButtonClicked)

        self.delaySpinBox.setMinimumWidth(250)
        self.delaySpinBox.setSingleStep(1)
        self.delaySpinBox.setRange(0, 25)
        self.delaySpinBox.setEnabled(haveDefault and not enabled)
        self.delaySpinBox.setValue(delayTime)
        self.enableSwitchButton.setEnabled(haveDefault)
        self.enableSwitchButton.setChecked(enabled)
        self.friendlySwitchButton.setEnabled(enabled)
        self.friendlySwitchButton.setChecked(friendlyEnabled)
        self.resetButton.setMinimumWidth(100)

        self.__updateStatusLabel()
        self.__fixStyleSheetOfSpinBox()

    def __initLayout(self):
        self.addWidget(self.statusLabel)

        self.defaultCfgLayout.setVerticalSpacing(19)
        self.defaultCfgLayout.setContentsMargins(48, 18, 44, 18)
        self.defaultCfgLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)

        self.helpLayout.setContentsMargins(0, 0, 0, 0)
        self.helpLayout.setSpacing(10)
        self.helpLayout.addWidget(self.defaultHintLabel)
        self.helpLayout.addWidget(self.helpButotn)

        self.defaultCfgLayout.addLayout(
            self.helpLayout, 0, 0, Qt.AlignLeft)

        self.defaultCfgLayout.addWidget(
            self.defaultLabel, 1, 0, Qt.AlignLeft)
        self.defaultCfgLayout.addWidget(
            self.defaultChampions, 1, 1, Qt.AlignHCenter)
        self.defaultCfgLayout.addWidget(
            self.defaultSelectButton, 1, 2, Qt.AlignRight)

        self.rankCfgLayout.setVerticalSpacing(19)
        self.rankCfgLayout.setContentsMargins(48, 18, 44, 18)
        self.rankCfgLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)

        self.rankCfgLayout.addWidget(self.rankLabel, 0, 0, Qt.AlignLeft)

        for i, ty in enumerate(['top', 'jug', 'mid', 'bot', 'sup']):
            label = getattr(self, f"{ty}Label")
            champions = getattr(self, f"{ty}Champions")
            button = getattr(self, f"{ty}SelectButton")

            self.rankCfgLayout.addWidget(label, i + 1, 0, Qt.AlignLeft)
            self.rankCfgLayout.addWidget(champions, i + 1, 1, Qt.AlignHCenter)
            self.rankCfgLayout.addWidget(button, i + 1, 2, Qt.AlignRight)

        self.buttonsCfgLayout.setVerticalSpacing(19)
        self.buttonsCfgLayout.setContentsMargins(48, 18, 44, 18)
        self.buttonsCfgLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)

        self.buttonsCfgLayout.addWidget(
            self.delayLabel, 0, 0, Qt.AlignLeft)
        self.buttonsCfgLayout.addWidget(
            self.delaySpinBox, 0, 1, Qt.AlignRight)
        self.buttonsCfgLayout.addWidget(
            self.enableLabel, 1, 0, Qt.AlignLeft)
        self.buttonsCfgLayout.addWidget(
            self.enableSwitchButton, 1, 1, Qt.AlignRight)
        self.buttonsCfgLayout.addWidget(
            self.friendlyLabel, 2, 0, Qt.AlignLeft)
        self.buttonsCfgLayout.addWidget(
            self.friendlySwitchButton, 2, 1, Qt.AlignRight)
        self.buttonsCfgLayout.addWidget(
            self.resetButton, 3, 1, Qt.AlignRight)

        self.viewLayout.setSpacing(0)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)

        self.addGroupWidget(self.defaultCfgWidget)
        self.addGroupWidget(self.rankCfgWidget)
        self.addGroupWidget(self.buttonsCfgWidget)

    async def initChampionList(self, champions: dict = None):
        if champions:
            self.champions = champions
        else:
            self.champions = {
                i: [name, await connector.getChampionIcon(i)]
                for i, name in connector.manager.getChampions().items()
                if i != -1
            }

        for ty in ['default', 'top', 'jug', 'mid', 'bot', 'sup']:
            configItem = getattr(self, f"{ty}ChampionsConfigItem")
            champions: ChampionsCard = getattr(self, f"{ty}Champions")
            selected = qconfig.get(configItem)

            champions.clearRequested.connect(
                lambda t=ty: self.__onChampionsChanged([], t))

            # 原来的配置项里储存字符串，使用 ',' 分隔
            # 现在储存的是 list 类型，其中是 championId
            # 为了兼容老版本的配置文件，这里手动对配置文件进行一下验证 / 重置
            if not (type(selected) is list and all(type(s) is int for s in selected)):
                selected = []
                qconfig.set(configItem, selected)

            if len(selected) == 0:
                continue

            champions.updateChampions(
                [self.champions[id][1] for id in selected])

        return self.champions

    def __onButtonClicked(self, type: str):
        configItem: ConfigItem = getattr(self, f"{type}ChampionsConfigItem")
        selected = qconfig.get(configItem)

        box = MultiChampionSelectMsgBox(
            self.champions, selected, self.window())
        box.completed.connect(
            lambda champions, t=type: self.__onChampionsChanged(champions, t))
        box.exec()

    def __onChampionsChanged(self, champions: list, type: str):
        configItem = getattr(self, f"{type}ChampionsConfigItem")
        qconfig.set(configItem, champions)

        card: ChampionsCard = getattr(self, f"{type}Champions")
        card.updateChampions(
            [self.champions[id][1] for id in champions])

        if type != 'default':
            return

        if len(champions) == 0:
            self.enableSwitchButton.setChecked(False)
            self.enableSwitchButton.setEnabled(False)
            self.friendlySwitchButton.setChecked(False)
            self.friendlySwitchButton.setEnabled(False)
            self.delaySpinBox.setEnabled(False)
            buttonEnable = False
        else:
            self.enableSwitchButton.setEnabled(True)
            self.delaySpinBox.setEnabled(True)
            buttonEnable = True

        for ty in ['top', 'jug', 'mid', 'bot', 'sup']:
            button: PushButton = getattr(self, f"{ty}SelectButton")
            button.setEnabled(buttonEnable)

    def __onEnableSwitchButtonClicked(self, checked):
        qconfig.set(self.enableConfigItem, checked)

        for ty in ['default', 'top', 'jug', 'mid', 'bot', 'sup']:
            button: PushButton = getattr(self, f"{ty}SelectButton")
            button.setEnabled(not checked)

        self.friendlySwitchButton.setEnabled(checked)
        self.delaySpinBox.setEnabled(not checked)

        if not checked:
            self.friendlySwitchButton.setChecked(False)

        self.__updateStatusLabel()

    def __onDelaySpinBoxValueChanged(self, value):
        qconfig.set(self.delayTimeConfigItem, value)

    def __onFriendlySwitchButtonClicked(self, checked):
        qconfig.set(self.friendlyConfigItem, checked)

    def __onResetButtonClicked(self):
        for ty in ['default', 'top', 'jug', 'mid', 'bot', 'sup']:
            self.__onChampionsChanged([], ty)

        self.delaySpinBox.setValue(0)

    def __updateStatusLabel(self):
        checked = self.enableSwitchButton.isChecked()

        text = self.tr("Enabled") if checked else self.tr("Disabled")
        self.statusLabel.setText(text)

    def __fixStyleSheetOfSpinBox(self):
        # 这玩意在深色 + Enabled 为 False 的时候看起来怪怪的，手动改一下
        light = """
            SpinBox:disabled {
                color: rgba(0, 0, 0, 150);
                background-color: rgba(249, 249, 249, 0.3);
                border: 1px solid rgba(0, 0, 0, 13);
                border-bottom: 1px solid rgba(0, 0, 0, 13);
            }
        """

        dark = """
            SpinBox:disabled {    
                color: rgba(255, 255, 255, 150);
                background-color: rgba(255, 255, 255, 0.0419);
                border: 1px solid rgba(255, 255, 255, 0.0698);
            }
        """

        setCustomStyleSheet(self.delaySpinBox, light, dark)


class ChampionsCard(QFrame):
    clearRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setContentsMargins(2, 0, 4, 0)
        self.hBoxLayout.setAlignment(Qt.AlignCenter)

        self.iconLayout = QHBoxLayout()
        self.iconLayout.setContentsMargins(6, 6, 0, 6)
        self.clearButton = TransparentToolButton(FluentIcon.CLOSE)
        self.clearButton.setFixedSize(28, 28)
        self.clearButton.setIconSize(QSize(15, 15))
        self.clearButton.setVisible(False)
        self.clearButton.clicked.connect(self.clearRequested)

        self.hBoxLayout.addLayout(self.iconLayout)
        self.hBoxLayout.addItem(QSpacerItem(
            0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed))
        self.hBoxLayout.addWidget(self.clearButton, alignment=Qt.AlignVCenter)

        self.setFixedWidth(250)
        self.setFixedHeight(42)

    def updateChampions(self, champions):
        self.clear()

        for icon in champions:
            icon = RoundIcon(icon, 28, 2, 2)
            self.iconLayout.addWidget(icon, alignment=Qt.AlignVCenter)

    def clear(self):
        for i in reversed(range(self.iconLayout.count())):
            item = self.iconLayout.itemAt(i)
            self.iconLayout.removeItem(item)

            if item.widget():
                item.widget().deleteLater()

    def enterEvent(self, a0: QEvent) -> None:
        self.clearButton.setVisible(True)
        return super().enterEvent(a0)

    def leaveEvent(self, a0: QEvent) -> None:
        self.clearButton.setVisible(False)
        return super().leaveEvent(a0)


class AutoSetSummonerSpellCard(ExpandGroupSettingCard):
    def __init__(self, title, content=None,
                 enableConfigItem: ConfigItem = None,
                 spellConfigItem: ConfigItem = None,
                 topSpellConfigItem: ConfigItem = None,
                 jugSpellConfigItem: ConfigItem = None,
                 midSpellConfigItem: ConfigItem = None,
                 botSpellConfigItem: ConfigItem = None,
                 supSpellConfigItem: ConfigItem = None,
                 parent=None):
        super().__init__(Icon.CHECKBOXFILL, title, content, parent)

        self.spells = {}

        self.enableConfigItem = enableConfigItem
        self.defaultSpellConfigItem = spellConfigItem
        self.topSpellConfigItem = topSpellConfigItem
        self.jugSpellConfigItem = jugSpellConfigItem
        self.midSpellConfigItem = midSpellConfigItem
        self.botSpellConfigItem = botSpellConfigItem
        self.supSpellConfigItem = supSpellConfigItem

        self.statusLabel = QLabel()

        self.defaultCfgWidget = QWidget(self.view)
        self.defaultCfgLayout = QGridLayout(self.defaultCfgWidget)
        self.defaultHintLabel = QLabel(self.tr("Default Configurations"))

        self.defaultLabel = QLabel(self.tr("Default summoner spells: "))
        self.defaultButtonLayout = QHBoxLayout()
        self.defaultSelectButton1 = SummonerSpellButton()
        self.defaultSelectButton2 = SummonerSpellButton()

        self.rankCfgWidget = QWidget(self.view)
        self.rankCfgLayout = QGridLayout(self.rankCfgWidget)
        self.rankLabel = QLabel(self.tr("Rank Configurations"))

        self.topLabel = QLabel(self.tr("Top: "))
        self.jugLabel = QLabel(self.tr("Juggle: "))
        self.midLabel = QLabel(self.tr("Mid: "))
        self.botLabel = QLabel(self.tr("Bottom: "))
        self.supLabel = QLabel(self.tr("Support: "))

        self.topButtonLayout = QHBoxLayout()
        self.topSelectButton1 = SummonerSpellButton()
        self.topSelectButton2 = SummonerSpellButton()
        self.jugButtonLayout = QHBoxLayout()
        self.jugSelectButton1 = SummonerSpellButton()
        self.jugSelectButton2 = SummonerSpellButton()
        self.midButtonLayout = QHBoxLayout()
        self.midSelectButton1 = SummonerSpellButton()
        self.midSelectButton2 = SummonerSpellButton()
        self.botButtonLayout = QHBoxLayout()
        self.botSelectButton1 = SummonerSpellButton()
        self.botSelectButton2 = SummonerSpellButton()
        self.supButtonLayout = QHBoxLayout()
        self.supSelectButton1 = SummonerSpellButton()
        self.supSelectButton2 = SummonerSpellButton()

        self.buttonsWidget = QWidget(self.view)
        self.buttonsLayout = QGridLayout(self.buttonsWidget)
        self.enableHintLabel = QLabel(self.tr("Enable:"))
        self.enableSwitchButton = SwitchButton(
            indicatorPos=IndicatorPosition.RIGHT)
        self.resetButton = PushButton(self.tr("Reset"))

        self.__initWidget()
        self.__initLayout()

    def __initWidget(self):
        # 逻辑是，必须要设置默认，才能设置具体分路和启动功能
        self.defaultHintLabel.setStyleSheet("font: bold")
        self.rankLabel.setStyleSheet("font: bold")

        # 54 是占位用的空图标
        selected = 54 not in qconfig.get(self.defaultSpellConfigItem)
        checked = qconfig.get(self.enableConfigItem)

        for ty in ['default', 'top', 'jug', 'mid', 'bot', 'sup']:
            for index in [1, 2]:
                button: SummonerSpellButton = getattr(
                    self, f"{ty}SelectButton{index}")
                button.setFixedSize(40, 40)
                button.clicked.connect(
                    lambda _, t=ty, i=index: self.__onButtonClicked(t, i))

                if ty != 'default':
                    button.setEnabled(selected)

        self.enableSwitchButton.checkedChanged.connect(
            self.__onEnableSelectChanged)
        self.enableSwitchButton.setEnabled(selected)
        self.enableSwitchButton.setChecked(checked)
        self.resetButton.setMinimumWidth(100)
        self.resetButton.clicked.connect(self.__onResetButtonClicked)

        self.__updateStatusLabel()

    def __initLayout(self):
        self.addWidget(self.statusLabel)

        self.defaultCfgLayout.setVerticalSpacing(19)
        self.defaultCfgLayout.setContentsMargins(48, 18, 44, 18)
        self.defaultCfgLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)

        self.defaultButtonLayout.addWidget(self.defaultSelectButton1)
        self.defaultButtonLayout.addWidget(self.defaultSelectButton2)
        self.defaultButtonLayout.setSpacing(10)
        self.defaultButtonLayout.setContentsMargins(0, 0, 0, 0)
        self.defaultCfgLayout.addWidget(
            self.defaultHintLabel, 0, 0, Qt.AlignLeft)
        self.defaultCfgLayout.addWidget(
            self.defaultLabel, 1, 0, Qt.AlignLeft)
        self.defaultCfgLayout.addLayout(
            self.defaultButtonLayout, 1, 1, Qt.AlignRight)

        self.rankCfgLayout.setVerticalSpacing(19)
        self.rankCfgLayout.setContentsMargins(48, 18, 44, 18)
        self.rankCfgLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)

        self.rankCfgLayout.addWidget(self.rankLabel, 0, 0, Qt.AlignLeft)

        for i, ty in enumerate(['top', 'jug', 'mid', 'bot', 'sup']):
            label = getattr(self, f"{ty}Label")
            button1 = getattr(self, f"{ty}SelectButton1")
            button2 = getattr(self, f"{ty}SelectButton2")
            layout: QHBoxLayout = getattr(self, f"{ty}ButtonLayout")

            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(10)
            layout.addWidget(button1)
            layout.addWidget(button2)

            self.rankCfgLayout.addWidget(label, i + 1, 0, Qt.AlignLeft)
            self.rankCfgLayout.addLayout(layout, i + 1, 1, Qt.AlignRight)

        self.buttonsLayout.setVerticalSpacing(19)
        self.buttonsLayout.setContentsMargins(48, 18, 44, 18)
        self.buttonsLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)

        self.buttonsLayout.addWidget(
            self.enableHintLabel, 0, 0, Qt.AlignLeft)
        self.buttonsLayout.addWidget(
            self.enableSwitchButton, 0, 1, Qt.AlignRight)

        self.buttonsLayout.addWidget(
            self.resetButton, 1, 1, Qt.AlignRight)

        self.viewLayout.setSpacing(0)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)

        self.addGroupWidget(self.defaultCfgWidget)
        self.addGroupWidget(self.rankCfgWidget)
        self.addGroupWidget(self.buttonsWidget)

    async def initSummonerSpells(self):
        self.spells = {
            i: await connector.getSummonerSpellIcon(i)
            for i in connector.manager.getSummonerSpellList()
        }

        for ty in ['default', 'top', 'jug', 'mid', 'bot', 'sup']:
            configItem = getattr(self, f"{ty}SpellConfigItem")
            selected = qconfig.get(configItem)

            for i in [1, 2]:
                spellId = selected[i - 1]

                button = f"{ty}SelectButton{i}"
                button: SummonerSpellButton = getattr(self, button)
                button.setPicture(self.spells[spellId])
                button.setSpellId(spellId)

    def __onButtonClicked(self, type: str, index: int):
        view = SummonerSpellSelectFlyout(self.spells)
        view.selectWidget.spellClicked.connect(
            lambda i, ty=type, ind=index: self.__onSpellSelected(ty, ind, i))

        button = QObject.sender(self)

        if index == 1:
            position = FlyoutAnimationType.SLIDE_LEFT
        else:
            position = FlyoutAnimationType.SLIDE_RIGHT

        self.w = Flyout.make(view, button, self, position, True)
        view.selectWidget.spellClicked.connect(self.w.fadeOut)

    def __onSpellSelected(self, type: str, index: int, id):

        button = f"{type}SelectButton{index}"
        button: SummonerSpellButton = getattr(self, button)

        if id != 54:
            anotherButton = f"{type}SelectButton{2 if index == 1 else 1}"
            anotherButton: SummonerSpellButton = getattr(self, anotherButton)
            anotherSpellId = anotherButton.getSpellId()

            # 选的技能和另一个已经选好的一样，认为是想要交换位置
            if id == anotherSpellId:
                currentSpellId = button.getSpellId()
                anotherButton.setPicture(self.spells[currentSpellId])
                anotherButton.setSpellId(currentSpellId)
                anotherButton.repaint()

        button.setPicture(self.spells[id])
        button.setSpellId(id)
        button.repaint()

        button1 = f"{type}SelectButton1"
        button1: SummonerSpellButton = getattr(self, button1)
        button2 = f"{type}SelectButton2"
        button2: SummonerSpellButton = getattr(self, button2)

        spells = [button1.getSpellId(), button2.getSpellId()]

        configItem = getattr(self, f"{type}SpellConfigItem")
        cfg.set(configItem, spells)

        if type != 'default':
            return

        buttonEnabled = False
        if id == 54:
            self.enableSwitchButton.setChecked(False)
            self.enableSwitchButton.setEnabled(False)
        elif 54 not in spells:
            self.enableSwitchButton.setEnabled(True)
            buttonEnabled = True

        for ty in ['top', 'jug', 'mid', 'bot', 'sup']:
            for i in [1, 2]:
                button = f"{ty}SelectButton{i}"
                button: SummonerSpellButton = getattr(self, button)
                button.setEnabled(buttonEnabled)

    def __onEnableSelectChanged(self, checked):
        for ty in ['default', 'top', 'jug', 'mid', 'bot', 'sup']:
            for i in [1, 2]:
                button = f"{ty}SelectButton{i}"
                button: SummonerSpellButton = getattr(self, button)
                button.setEnabled(not checked)

        cfg.set(self.enableConfigItem, checked)

        self.__updateStatusLabel()

    def __onResetButtonClicked(self):
        for ty in ['default', 'top', 'jug', 'mid', 'bot', 'sup']:
            for i in [1, 2]:
                self.__onSpellSelected(ty, i, 54)

    def __updateStatusLabel(self):
        checked = self.enableSwitchButton.isChecked()

        text = self.tr("Enabled") if checked else self.tr("Disabled")
        self.statusLabel.setText(text)
