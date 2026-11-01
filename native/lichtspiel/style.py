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
QLabel#muted, QLabel#hint { color: #a0a6a4; line-height: 1.5; }
QLabel#status { color: #d5bb8f; padding: 8px 0; }
QPushButton { background: #292d2e; color: #e9eae7; border: 1px solid #424748; border-radius: 6px; padding: 9px 14px; min-height: 18px; }
QPushButton:hover { background: #353a3b; border-color: #687070; }
QPushButton:disabled { color: #6f7574; background: #222526; border-color: #333738; }
QPushButton#primary { background: #dfb077; color: #211b15; border-color: #dfb077; font-weight: 700; }
QPushButton#primary:hover { background: #efc18a; }
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
QScrollArea { background: #191b1c; border: none; }
QScrollBar:vertical { background: #1b1e1f; width: 9px; }
QScrollBar::handle:vertical { background: #505657; border-radius: 4px; min-height: 30px; }
"""
