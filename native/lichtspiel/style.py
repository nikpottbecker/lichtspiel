"""Restrained Qt widget styling; no web renderer is used."""

STYLESHEET = """
QMainWindow, QWidget { background: #151718; color: #ebece9; font-family: "Arial"; font-size: 13px; }
QWidget#page { background: #191b1c; }
QLabel { background: transparent; }
QWidget#sidebar { background: #111314; border-right: 1px solid #313536; }
QWidget#content { background: #191b1c; }
QLabel#brand { color: #e8bc83; font-size: 18px; font-weight: 700; letter-spacing: 2px; }
QLabel#brandCaption, QLabel#eyebrow { color: #a0a6a4; font-size: 11px; }
QLabel#pageTitle { color: #f4f2ed; font-size: 26px; font-weight: 600; }
QLabel#sectionTitle { color: #f1eee8; font-size: 16px; font-weight: 600; }
QLabel#liveTitle { color: #f5f1e9; font-size: 19px; font-weight: 600; }
QLabel#timePrimary { color: #f0e9db; font-family: "SF Mono", "Consolas", "DejaVu Sans Mono"; font-size: 11px; }
QLabel#timeSecondary { color: #aeb5b2; font-family: "SF Mono", "Consolas", "DejaVu Sans Mono"; font-size: 10px; }
QLabel#muted, QLabel#hint { color: #a0a6a4; line-height: 1.5; }
QLabel#status { color: #d5bb8f; padding: 8px 0; }
QPushButton { background: #292d2e; color: #e9eae7; border: 1px solid #424748; border-radius: 6px; padding: 9px 14px; min-height: 18px; }
QPushButton:hover { background: #353a3b; border-color: #687070; }
QPushButton:disabled { color: #6f7574; background: #222526; border-color: #333738; }
QPushButton#primary { background: #dfb077; color: #211b15; border-color: #dfb077; font-weight: 700; }
QPushButton#primary:hover { background: #efc18a; }
QPushButton#primary:disabled { background: #343838; color: #8d9491; border-color: #454b49; }
QPushButton#danger { color: #e9b0a6; }
QPushButton#nav { background: transparent; border: none; border-radius: 5px; text-align: left; padding: 12px 14px; color: #b4bbba; }
QPushButton#nav:hover { background: #242829; }
QPushButton#nav:checked { background: #30302b; color: #f1d4aa; }
QLineEdit, QComboBox, QDateTimeEdit { background: #202324; color: #eceeea; border: 1px solid #444949; border-radius: 5px; padding: 8px 10px; min-height: 20px; selection-background-color: #ab8054; }
QLineEdit:focus, QComboBox:focus, QDateTimeEdit:focus, QListWidget:focus { border: 1px solid #c79b68; }
QComboBox QAbstractItemView { background: #25292a; color: #eceeea; selection-background-color: #604d35; }
QListWidget { background: #202324; border: 1px solid #383d3e; border-radius: 6px; padding: 5px; outline: none; }
QListWidget::item { padding: 11px 10px; border-bottom: 1px solid #303536; }
QListWidget::item:selected { background: #4b4438; color: #fff5e7; }
QFrame#rule { background: #363b3c; border: none; max-height: 1px; }
QFrame#liveCard { background: #202324; border: 1px solid #3d4242; border-radius: 7px; }
QFrame#ruleCard { background: #222526; border: 1px solid #383e3e; border-radius: 6px; }
QCheckBox { spacing: 9px; }
QCheckBox::indicator { width: 15px; height: 15px; border: 1px solid #757b77; border-radius: 3px; background: #1b1e1e; }
QCheckBox::indicator:checked { background: #dfb077; border-color: #dfb077; }
QProgressBar { border: none; background: #444948; border-radius: 3px; }
QProgressBar#clipProgress { min-height: 7px; max-height: 7px; }
QProgressBar#clipProgress::chunk { background: #e1b37b; border-radius: 3px; }
QProgressBar#showProgress { min-height: 4px; max-height: 4px; }
QProgressBar#showProgress::chunk { background: #8f9691; border-radius: 2px; }
QScrollArea { background: #191b1c; border: none; }
QScrollBar:vertical { background: #1b1e1f; width: 9px; }
QScrollBar::handle:vertical { background: #505657; border-radius: 4px; min-height: 30px; }
"""
