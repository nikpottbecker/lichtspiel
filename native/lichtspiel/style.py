"""Quiet, high-contrast styling for the native control room."""

STYLESHEET = """
QMainWindow, QWidget { background: #0e0e14; color: #f1f0f5; font-family: "Inter", "SF Pro Text", "Segoe UI", "Arial"; font-size: 13px; }
QWidget#page, QWidget#content, QStackedWidget { background: #111118; }
QLabel { background: transparent; }
QWidget#sidebar { background: #14141c; border-right: 1px solid #2b2a35; }
QLabel#brand { color: #faf9fc; font-size: 18px; font-weight: 800; letter-spacing: 2px; }
QLabel#brandCaption { color: #a29fad; font-size: 11px; letter-spacing: 1px; }
QLabel#eyebrow { color: #aaa7b5; font-size: 11px; font-weight: 650; letter-spacing: 1px; }
QLabel#pageTitle { color: #faf9fc; font-size: 32px; font-weight: 700; }
QLabel#sectionTitle { color: #f3f2f7; font-size: 16px; font-weight: 650; }
QLabel#liveTitle { color: #faf9fc; font-size: 21px; font-weight: 650; }
QLabel#timePrimary { color: #e7e4ef; font-family: "SF Mono", "Consolas", "DejaVu Sans Mono"; font-size: 11px; }
QLabel#timeSecondary { color: #aaa8b6; font-family: "SF Mono", "Consolas", "DejaVu Sans Mono"; font-size: 10px; }
QLabel#muted, QLabel#hint { color: #aaa8b6; }
QLabel#status { color: #c5c2d0; padding: 4px 0; }
QPushButton { background: #262630; color: #f0eff5; border: 1px solid #41404d; border-radius: 9px; padding: 9px 14px; min-height: 18px; font-weight: 550; }
QPushButton:hover { background: #33323e; border-color: #737082; }
QPushButton:pressed { background: #1e1d29; }
QPushButton:focus { border: 1px solid #a886fa; }
QPushButton:disabled { color: #81808d; background: #1d1d26; border-color: #32313d; }
QPushButton#primary { background: #8755ed; color: #fff; border-color: #a27dfa; font-weight: 700; }
QPushButton#primary:hover { background: #9a6bf3; border-color: #c0a2ff; }
QPushButton#primary:disabled { background: #332c42; color: #91899e; border-color: #433a52; }
QPushButton#danger { color: #ffb9bc; border-color: #765359; }
QPushButton#danger:hover { background: #40282e; }
QPushButton#previewExpand { min-height: 16px; padding: 0; border: none; background: transparent; color: #c4a7ff; font-size: 16px; }
QPushButton#previewExpand:hover { color: #e0d1ff; background: #343040; }
QPushButton#nav { background: transparent; border: none; border-radius: 9px; text-align: left; padding: 11px 15px; color: #aaa8b5; font-size: 13px; }
QPushButton#nav:hover { background: #24232e; color: #f0eef7; }
QPushButton#nav:checked { background: #332741; color: #f0e7ff; border-left: 3px solid #ae7bff; }
QLineEdit, QComboBox, QDateTimeEdit, QSpinBox { background: #1f1e28; color: #f1f0f5; border: 1px solid #41404d; border-radius: 8px; padding: 8px 10px; min-height: 20px; selection-background-color: #7645d9; }
QLineEdit:focus, QComboBox:focus, QDateTimeEdit:focus, QSpinBox:focus, QListWidget:focus { border: 1px solid #a886fa; }
QComboBox QAbstractItemView { background: #272633; color: #f1f0f5; selection-background-color: #604098; }
QListWidget { background: #191922; border: 1px solid #383744; border-radius: 10px; padding: 5px; outline: none; }
QListWidget::item { padding: 11px 10px; border-bottom: 1px solid #2c2b37; }
QListWidget::item:hover { background: #282735; }
QListWidget::item:selected { background: #483365; color: #fff; border-radius: 5px; }
QFrame#rule { background: #302f3b; border: none; max-height: 1px; }
QFrame#liveCard { background: #201e2b; border: 1px solid #514760; border-radius: 12px; }
QFrame#stageCard, QFrame#recoveryCard { background: #1e1d28; border: 1px solid #3c3b48; border-radius: 12px; }
QFrame#ruleCard { background: #1e1d27; border: 1px solid #3a3946; border-radius: 10px; }
QCheckBox { spacing: 9px; background: transparent; }
QCheckBox::indicator { width: 16px; height: 16px; border: 1px solid #898694; border-radius: 4px; background: #1d1c26; }
QCheckBox::indicator:checked { background: #9667ee; border-color: #b68eff; }
QProgressBar { border: none; background: #41404c; border-radius: 3px; }
QProgressBar#clipProgress { min-height: 8px; max-height: 8px; }
QProgressBar#clipProgress::chunk { background: #ac81ff; border-radius: 3px; }
QProgressBar#showProgress { min-height: 4px; max-height: 4px; }
QProgressBar#showProgress::chunk { background: #b2abc3; border-radius: 2px; }
QScrollArea { background: #111118; border: none; }
QScrollBar:vertical { background: #191922; width: 9px; }
QScrollBar::handle:vertical { background: #555363; border-radius: 4px; min-height: 30px; }
"""
