"""Quiet, high-contrast styling for the native control room."""

STYLESHEET = """
QMainWindow, QWidget { background: #090909; color: #f5f5f5; font-family: "Inter", "SF Pro Text", "Segoe UI", "Arial"; font-size: 13px; }
QWidget#page, QWidget#content, QStackedWidget { background: #090909; }
QWidget#navShell { background: #090909; }
QFrame#topbar { background: rgba(28, 28, 28, 242); border: 1px solid #4b4b4b; border-radius: 29px; }
QLabel { background: transparent; }
QLabel#heroEyebrow { color: #d7d7d7; font-size: 11px; font-weight: 750; letter-spacing: 2px; }
QLabel#heroTitle { color: #ffffff; font-size: 38px; font-weight: 750; }
QLabel#heroDescription { color: #cecece; font-size: 13px; }
QLabel#systemBadge { color: #eeeeee; background: #242424; border: 1px solid #565656; border-radius: 15px; padding: 8px 13px; font-size: 10px; font-weight: 750; letter-spacing: 1px; }
QLabel#brand { color: #fafafa; background: #111111; border: 1px solid #404040; border-radius: 18px; font-size: 15px; font-weight: 800; letter-spacing: 2px; padding: 9px 13px; }
QLabel#brandCaption { color: #a9a9a9; font-size: 11px; letter-spacing: 1px; }
QLabel#eyebrow { color: #adadad; font-size: 11px; font-weight: 650; letter-spacing: 1px; }
QLabel#pageTitle { color: #fafafa; font-size: 32px; font-weight: 700; }
QLabel#sectionTitle { color: #f3f3f3; font-size: 16px; font-weight: 650; }
QLabel#liveTitle { color: #fafafa; font-size: 21px; font-weight: 650; }
QLabel#timePrimary { color: #e7e7e7; font-family: "SF Mono", "Consolas", "DejaVu Sans Mono"; font-size: 11px; }
QLabel#timeSecondary { color: #aaaaaa; font-family: "SF Mono", "Consolas", "DejaVu Sans Mono"; font-size: 10px; }
QLabel#muted, QLabel#hint { color: #aaaaaa; }
QLabel#status { color: #c5c5c5; padding: 4px 0; }
QPushButton { background: #282828; color: #efefef; border: 1px solid #484848; border-radius: 9px; padding: 9px 14px; min-height: 18px; font-weight: 550; }
QPushButton:hover { background: #373737; border-color: #777777; }
QPushButton:pressed { background: #202020; }
QPushButton:focus { border: 1px solid #ffffff; }
QPushButton:disabled { color: #777777; background: #1d1d1d; border-color: #303030; }
QPushButton#primary { background: #f0f0f0; color: #101010; border-color: #ffffff; font-weight: 750; }
QPushButton#primary:hover { background: #ffffff; border-color: #ffffff; }
QPushButton#primary:disabled { background: #343434; color: #8c8c8c; border-color: #484848; }
QPushButton#danger { color: #f3f3f3; border-color: #797979; }
QPushButton#danger:hover { background: #3d3d3d; }
QPushButton#previewExpand { min-height: 16px; padding: 0; border: none; background: transparent; color: #eeeeee; font-size: 16px; }
QPushButton#previewExpand:hover { color: #ffffff; background: #393939; }
QPushButton#nav { background: transparent; border: 1px solid transparent; border-radius: 19px; text-align: center; padding: 8px 14px; color: #bcbcbc; font-size: 11px; font-weight: 750; letter-spacing: 1px; }
QPushButton#nav:hover { background: #303030; color: #ffffff; }
QPushButton#nav:checked { background: #eeeeee; color: #111111; border: 1px solid #ffffff; border-radius: 18px; }
QPushButton#subnav { background: #202020; color: #bcbcbc; border: 1px solid #444444; border-radius: 18px; padding: 8px 16px; min-height: 18px; }
QPushButton#subnav:hover { background: #303030; color: #ffffff; }
QPushButton#subnav:checked { background: #ededed; color: #111111; border: 1px solid #ffffff; border-radius: 18px; font-weight: 700; }
QLineEdit, QComboBox, QDateTimeEdit, QSpinBox { background: #202020; color: #f1f1f1; border: 1px solid #454545; border-radius: 8px; padding: 8px 10px; min-height: 20px; selection-background-color: #6e6e6e; }
QLineEdit:focus, QComboBox:focus, QDateTimeEdit:focus, QSpinBox:focus, QListWidget:focus { border: 1px solid #d9d9d9; }
QComboBox QAbstractItemView { background: #292929; color: #f1f1f1; selection-background-color: #575757; }
QListWidget { background: #191919; border: 1px solid #3d3d3d; border-radius: 10px; padding: 5px; outline: none; }
QListWidget::item { padding: 11px 10px; border-bottom: 1px solid #303030; }
QListWidget::item:hover { background: #292929; }
QListWidget::item:selected { background: #4a4a4a; color: #ffffff; border-radius: 5px; }
QFrame#rule { background: #353535; border: none; max-height: 1px; }
QFrame#liveCard { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #262626, stop:1 #1c1c1c); border: 1px solid #5b5b5b; border-radius: 14px; }
QFrame#stageCard, QFrame#recoveryCard { background: rgba(30, 30, 30, 238); border: 1px solid #525252; border-radius: 14px; }
QFrame#onboardingCard { background: #202020; border: 1px solid #6a6a6a; border-radius: 14px; }
QFrame#ruleCard { background: #202020; border: 1px solid #3d3d3d; border-radius: 10px; }
QCheckBox { spacing: 9px; background: transparent; }
QCheckBox::indicator { width: 16px; height: 16px; border: 1px solid #898989; border-radius: 4px; background: #1d1d1d; }
QCheckBox::indicator:checked { background: #eeeeee; border-color: #ffffff; }
QProgressBar { border: none; background: #414141; border-radius: 3px; }
QProgressBar#clipProgress { min-height: 8px; max-height: 8px; }
QProgressBar#clipProgress::chunk { background: #f0f0f0; border-radius: 3px; }
QProgressBar#showProgress { min-height: 4px; max-height: 4px; }
QProgressBar#showProgress::chunk { background: #a8a8a8; border-radius: 2px; }
QScrollArea { background: #090909; border: none; }
QScrollBar:vertical { background: #191919; width: 9px; }
QScrollBar::handle:vertical { background: #555555; border-radius: 4px; min-height: 30px; }
"""
