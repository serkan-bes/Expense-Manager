"""
Main PyQt6 GUI application for Expense Manager.

Provides a single-column, dark-themed financial management interface supporting:
  1. Dynamic Checking/Cash accounts and Credit Cards management.
  2. Expense, Income, and Transfer (Credit Card Debt Payment) recording.
  3. Automatic Statement Closing Date calculation and multi-month Installment splitting.
  4. Real-time Dashboard with Total Liquid Cash/Bank Balance, Per-Card Statement & Limit
     Summary Cards (with visual progress bars), and searchable Transaction History.
  5. Instant runtime English / Turkish (EN | TR) interface language switching while keeping
     all database constants and internal code strictly in English.
"""

import os
import sys
from typing import Any, Dict

from PyQt6 import uic
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

import database as db
import translations as i18n

# Default category presets in English for each transaction type
EXPENSE_CATEGORIES = i18n.EXPENSE_CATEGORY_KEYS
INCOME_CATEGORIES = i18n.INCOME_CATEGORY_KEYS
TRANSFER_CATEGORIES = i18n.TRANSFER_CATEGORY_KEYS

# Modernized dark theme QSS stylesheet preserving the focused single-column aesthetic
MODERN_DARK_STYLESHEET = """
QMainWindow, QWidget#centralwidget {
    background-color: #0d1117;
    color: #e6edf3;
    font-family: "Segoe UI", "Inter", sans-serif;
    font-size: 13px;
}

QTabWidget::pane {
    border: 1px solid #262f3d;
    background-color: #131922;
    border-radius: 10px;
    top: -1px;
}

QTabBar::tab {
    background-color: #161d27;
    color: #8b949e;
    border: 1px solid #262f3d;
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 10px 22px;
    margin-right: 4px;
    font-weight: 600;
    font-size: 13px;
}

QTabBar::tab:hover {
    background-color: #1f2937;
    color: #e6edf3;
}

QTabBar::tab:selected {
    background-color: #1f6feb;
    color: #ffffff;
    border-color: #1f6feb;
}

QLabel {
    color: #c9d1d9;
    font-weight: 500;
}

QLabel#label_tx_header, QLabel#label_acc_header {
    color: #ffffff;
    font-size: 18px;
    font-weight: 700;
}

QLabel#label_tx_subheader {
    color: #8b949e;
    font-size: 12px;
    margin-bottom: 4px;
}

QLabel#label_installment_preview {
    background-color: #172130;
    color: #79c0ff;
    border: 1px solid #264066;
    border-radius: 6px;
    padding: 8px 10px;
    font-size: 12px;
}

QGroupBox {
    background-color: #161d27;
    border: 1px solid #283241;
    border-radius: 8px;
    margin-top: 12px;
    padding: 12px;
    font-weight: 600;
    color: #e6edf3;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    color: #79c0ff;
}

QLineEdit, QComboBox, QDateEdit, QSpinBox {
    background-color: #18202c;
    color: #f0f6fc;
    border: 1px solid #2e3b4e;
    border-radius: 7px;
    padding: 8px 12px;
    min-height: 20px;
    selection-background-color: #1f6feb;
}

QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QSpinBox:focus {
    border: 1px solid #388bfd;
    background-color: #1c2635;
}

QComboBox::drop-down {
    border: none;
    width: 28px;
}

QComboBox QAbstractItemView {
    background-color: #18202c;
    color: #f0f6fc;
    border: 1px solid #388bfd;
    selection-background-color: #1f6feb;
    selection-color: #ffffff;
    padding: 4px;
}

QRadioButton {
    color: #c9d1d9;
    spacing: 8px;
    font-weight: 600;
    padding: 4px 6px;
}

QRadioButton::indicator {
    width: 15px;
    height: 15px;
    border-radius: 8px;
    border: 2px solid #48566a;
    background-color: #131922;
}

QRadioButton::indicator:checked {
    background-color: #2f81f7;
    border: 2px solid #79c0ff;
}

QPushButton {
    background-color: #238636;
    color: #ffffff;
    border: 1px solid #2ea043;
    border-radius: 8px;
    padding: 10px 18px;
    font-weight: 700;
    font-size: 13px;
}

QPushButton:hover {
    background-color: #2ea043;
}

QPushButton:pressed {
    background-color: #1a6328;
}

QPushButton#buton_add_account {
    background-color: #1f6feb;
    border-color: #388bfd;
}

QPushButton#buton_add_account:hover {
    background-color: #388bfd;
}

QPushButton#buton_reset, QPushButton#buton_delete_account {
    background-color: #21262d;
    color: #f85149;
    border: 1px solid #30363d;
    padding: 8px 14px;
    font-weight: 600;
}

QPushButton#buton_reset:hover, QPushButton#buton_delete_account:hover {
    background-color: #da3633;
    color: #ffffff;
    border-color: #f85149;
}

/* Dashboard Metric Cards */
QFrame#card_liquid_balance, QFrame#card_total_income, QFrame#card_total_expense {
    background-color: #171f2c;
    border: 1px solid #2a3648;
    border-radius: 10px;
    padding: 10px 12px;
}

QLabel#label_liquid_title, QLabel#label_income_title, QLabel#label_expense_title {
    color: #8b949e;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.5px;
}

QLabel#label_liquid_value {
    color: #58a6ff;
    font-size: 20px;
    font-weight: 800;
}

QLabel#label_income_value {
    color: #3fb950;
    font-size: 20px;
    font-weight: 800;
}

QLabel#label_expense_value {
    color: #f85149;
    font-size: 20px;
    font-weight: 800;
}

QLabel#label_liquid_sub, QLabel#label_income_sub, QLabel#label_expense_sub {
    color: #8b949e;
    font-size: 11px;
}

QFrame#frame_account_form {
    background-color: #161d27;
    border: 1px solid #283241;
    border-radius: 8px;
    padding: 12px;
}

/* Scroll Area for Credit Card Summary Cards */
QScrollArea#scroll_credit_cards {
    border: none;
    background-color: transparent;
}

QWidget#scroll_credit_cards_contents {
    background-color: transparent;
}

/* Tables */
QTableWidget {
    background-color: #141a24;
    alternate-background-color: #17202d;
    color: #e6edf3;
    border: 1px solid #283241;
    border-radius: 8px;
    gridline-color: #212a38;
    selection-background-color: #1f3b63;
    selection-color: #ffffff;
}

QHeaderView::section {
    background-color: #1b2432;
    color: #8b949e;
    border: none;
    border-bottom: 1px solid #2e3b4e;
    border-right: 1px solid #212a38;
    padding: 8px 10px;
    font-weight: 700;
    font-size: 11px;
}

QProgressBar {
    background-color: #0d1117;
    border: 1px solid #2e3b4e;
    border-radius: 6px;
    text-align: center;
    color: #e6edf3;
    font-weight: 700;
    font-size: 11px;
    min-height: 16px;
    max-height: 16px;
}

QProgressBar::chunk {
    background-color: #238636;
    border-radius: 5px;
}
"""


class MainWindow(QMainWindow):
    """Main window controller coordinating all tabs, dynamic forms, localization, and database queries."""

    def __init__(self) -> None:
        super().__init__()

        # Default active UI language ('EN' or 'TR')
        self.current_lang: str = i18n.LANG_EN

        # Ensure database is initialized and migrated inside data/database.db
        db.init_db()

        # Load the Qt Designer UI file relative to this script's directory
        ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Expance manager.ui")
        uic.loadUi(ui_path, self)

        # Apply the modernized dark theme stylesheet
        self.setStyleSheet(MODERN_DARK_STYLESHEET)

        # Build and mount the compact top-right language switcher (EN | TR)
        self._setup_language_switcher()

        # Configure date picker to default to today
        self.line_date.setDate(QDate.currentDate())

        # Configure tables for clean read-only display and responsive column stretching
        self._configure_tables()

        # Connect signals for Add Transaction tab
        self.buton_expense.toggled.connect(self._on_transaction_type_changed)
        self.buton_income.toggled.connect(self._on_transaction_type_changed)
        self.buton_transfer.toggled.connect(self._on_transaction_type_changed)
        self.combo_account.currentIndexChanged.connect(self._on_selected_account_changed)
        self.spin_installments.valueChanged.connect(self.update_installment_preview)
        self.line_amount.textChanged.connect(self.update_installment_preview)
        self.line_date.dateChanged.connect(self.update_installment_preview)
        self.buton_save.clicked.connect(self.save_function)

        # Connect signals for Dashboard tab (search, filters, factory reset)
        self.line_search.textChanged.connect(self.update_table)
        self.radio_showall.clicked.connect(self.update_table)
        self.radio_income.clicked.connect(self.update_table)
        self.radio_expense.clicked.connect(self.update_table)
        if hasattr(self, "radio_transfer"):
            self.radio_transfer.clicked.connect(self.update_table)
        if hasattr(self, "buton_reset"):
            self.buton_reset.clicked.connect(self.reset_database)

        # Connect signals for Accounts / Cards management tab
        self.radio_add_cash_account.toggled.connect(self._on_account_creation_type_changed)
        self.radio_add_credit_card.toggled.connect(self._on_account_creation_type_changed)
        self.buton_add_account.clicked.connect(self.handle_add_account)
        self.buton_delete_account.clicked.connect(self.handle_delete_account)

        # Refresh everything when switching tabs
        self.page_finansdurum.currentChanged.connect(self.refresh_all_views)

        # Apply initial language translations and populate all views
        self.retranslate_ui()

    # ==========================================================================
    # Language Switcher (EN | TR) & Instant UI Retranslation
    # ==========================================================================

    def _tr(self, key: str, **kwargs) -> str:
        """Shortcut helper to fetch a localized string in `self.current_lang`."""
        return i18n.tr(key, self.current_lang, **kwargs)

    def _setup_language_switcher(self) -> None:
        """
        Create a compact, styled `EN | TR` language selector in the top-right corner
        of the main tab widget (`Qt.Corner.TopRightCorner`).
        """
        self.lang_container = QWidget(self)
        row = QHBoxLayout(self.lang_container)
        row.setContentsMargins(0, 0, 2, 4)
        row.setSpacing(0)

        self.lang_pill = QFrame(self.lang_container)
        self.lang_pill.setObjectName("lang_pill")
        pill_layout = QHBoxLayout(self.lang_pill)
        pill_layout.setContentsMargins(3, 2, 3, 2)
        pill_layout.setSpacing(2)

        self.btn_lang_en = QPushButton("EN", self.lang_pill)
        self.btn_lang_en.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_lang_en.setFixedHeight(24)
        self.btn_lang_en.clicked.connect(lambda: self._on_lang_button_clicked(i18n.LANG_EN))

        self.label_lang_sep = QLabel("|", self.lang_pill)
        self.label_lang_sep.setStyleSheet(
            "color: #48566a; font-weight: 700; font-size: 11px; padding: 0 2px; border: none;"
        )

        self.btn_lang_tr = QPushButton("TR", self.lang_pill)
        self.btn_lang_tr.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_lang_tr.setFixedHeight(24)
        self.btn_lang_tr.clicked.connect(lambda: self._on_lang_button_clicked(i18n.LANG_TR))

        pill_layout.addWidget(self.btn_lang_en)
        pill_layout.addWidget(self.label_lang_sep)
        pill_layout.addWidget(self.btn_lang_tr)
        row.addWidget(self.lang_pill)

        # Mount the switcher in the top-right corner of the QTabWidget
        self.page_finansdurum.setCornerWidget(
            self.lang_container, Qt.Corner.TopRightCorner
        )
        self._update_language_switcher_styles()

    def _on_lang_button_clicked(self, target_lang: str) -> None:
        """
        Switch to `target_lang`, or toggle between EN and TR if the user clicks
        the already active segment on the `EN | TR` control.
        """
        if self.current_lang == target_lang:
            self.toggle_language()
        else:
            self.set_language(target_lang)

    def toggle_language(self) -> None:
        """Toggle the active interface language between 'EN' and 'TR'."""
        next_lang = i18n.LANG_TR if self.current_lang == i18n.LANG_EN else i18n.LANG_EN
        self.set_language(next_lang)

    def set_language(self, lang: str) -> None:
        """Set the active UI language ('EN' or 'TR') and immediately retranslate all screens."""
        normalized = lang.upper().strip()
        if normalized not in (i18n.LANG_EN, i18n.LANG_TR):
            return
        if self.current_lang == normalized:
            return
        self.current_lang = normalized
        self.retranslate_ui()

    def _update_language_switcher_styles(self) -> None:
        """Apply visual highlight styles to the active language button in the `EN | TR` pill."""
        self.lang_pill.setStyleSheet(
            """
            QFrame#lang_pill {
                background-color: #161d27;
                border: 1px solid #2e3b4e;
                border-radius: 7px;
            }
            """
        )
        active_qss = """
            QPushButton {
                background-color: #1f6feb;
                color: #ffffff;
                border: none;
                border-radius: 5px;
                padding: 2px 10px;
                font-size: 11px;
                font-weight: 800;
            }
            QPushButton:hover {
                background-color: #388bfd;
            }
        """
        inactive_qss = """
            QPushButton {
                background-color: transparent;
                color: #8b949e;
                border: none;
                border-radius: 5px;
                padding: 2px 10px;
                font-size: 11px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #1f2937;
                color: #e6edf3;
            }
        """
        is_en = self.current_lang == i18n.LANG_EN
        self.btn_lang_en.setStyleSheet(active_qss if is_en else inactive_qss)
        self.btn_lang_tr.setStyleSheet(inactive_qss if is_en else active_qss)

        tooltip = self._tr("lang_tooltip")
        self.btn_lang_en.setToolTip(tooltip)
        self.btn_lang_tr.setToolTip(tooltip)
        self.lang_pill.setToolTip(tooltip)

    def retranslate_ui(self) -> None:
        """
        Immediately update all visible labels, tab titles, placeholders, table headers,
        dropdown items, and dynamic summary widgets to match `self.current_lang`.
        """
        self._update_language_switcher_styles()

        # Window and Tab titles
        self.setWindowTitle(self._tr("window_title"))
        self.page_finansdurum.setTabText(0, self._tr("tab_add_tx"))
        self.page_finansdurum.setTabText(1, self._tr("tab_dashboard"))
        self.page_finansdurum.setTabText(2, self._tr("tab_accounts"))

        # Tab 1: Add Transaction static labels & controls
        self.label_tx_header.setText(self._tr("tx_header"))
        self.label_tx_subheader.setText(self._tr("tx_subheader"))
        self.groupislem_turu.setTitle(self._tr("group_tx_type"))
        self.buton_expense.setText(self._tr("radio_expense"))
        self.buton_income.setText(self._tr("radio_income"))
        self.buton_transfer.setText(self._tr("radio_transfer"))
        self.tutar_3.setText(self._tr("label_amount"))
        self.line_amount.setPlaceholderText(self._tr("placeholder_amount"))
        self.label_3.setText(self._tr("label_tx_date"))
        self.label_account_title.setText(self._tr("label_account_card"))
        self.label_from_account.setText(self._tr("label_from_account"))
        self.label_to_account.setText(self._tr("label_to_account"))
        self.label_installments.setText(self._tr("label_installments"))
        self.label_2.setText(self._tr("label_category"))
        self.line_description.setText(self._tr("label_description"))
        self.line_descr.setPlaceholderText(self._tr("placeholder_description"))
        self.buton_save.setText(self._tr("btn_save_tx"))

        # Tab 2: Dashboard static labels, filters & table headers
        self.label_liquid_title.setText(self._tr("metric_liquid_title"))
        self.label_income_title.setText(self._tr("metric_income_title"))
        self.label_income_sub.setText(self._tr("metric_income_sub"))
        self.label_expense_title.setText(self._tr("metric_expense_title"))
        self.group_credit_cards_overview.setTitle(self._tr("group_cards_overview"))
        self.label.setText(self._tr("label_search"))
        self.line_search.setPlaceholderText(self._tr("placeholder_search"))
        self.radio_showall.setText(self._tr("filter_show_all"))
        self.radio_income.setText(self._tr("filter_incomes"))
        self.radio_expense.setText(self._tr("filter_expenses"))
        if hasattr(self, "radio_transfer"):
            self.radio_transfer.setText(self._tr("filter_transfers"))
        self.table_transaction.setHorizontalHeaderLabels(
            [
                self._tr("tx_col_amount"),
                self._tr("tx_col_category"),
                self._tr("tx_col_description"),
                self._tr("tx_col_account"),
                self._tr("tx_col_date"),
                self._tr("tx_col_period"),
            ]
        )
        self.buton_reset.setText(self._tr("btn_factory_reset"))

        # Tab 3: Accounts / Cards static labels, form fields & table headers
        self.label_acc_header.setText(self._tr("acc_header"))
        self.group_add_account_type.setTitle(self._tr("group_select_acc_type"))
        self.radio_add_cash_account.setText(self._tr("radio_type_cash"))
        self.radio_add_credit_card.setText(self._tr("radio_type_card"))
        self.label_initial_balance.setText(self._tr("label_initial_balance"))
        self.line_initial_balance.setPlaceholderText(self._tr("placeholder_initial_balance"))
        self.label_card_limit.setText(self._tr("label_card_limit"))
        self.line_card_limit.setPlaceholderText(self._tr("placeholder_card_limit"))
        self.label_closing_day.setText(self._tr("label_closing_day"))
        self.label_due_day.setText(self._tr("label_due_day"))
        self.label_existing_accounts.setText(self._tr("label_existing_accounts"))
        self.table_accounts.setHorizontalHeaderLabels(
            [
                self._tr("acc_col_name"),
                self._tr("acc_col_type"),
                self._tr("acc_col_balance_avail"),
                self._tr("acc_col_init_limit"),
                self._tr("acc_col_schedule"),
            ]
        )
        self.buton_delete_account.setText(self._tr("btn_delete_account"))

        # Refresh dynamic form labels and all data-driven views
        self._on_account_creation_type_changed()
        self.update_category()
        self.refresh_all_views()

    def _ask_yes_no_question(self, title: str, message: str) -> bool:
        """Display a localized Yes/No confirmation dialog and return True if confirmed."""
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Question)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        yes_btn = msg_box.addButton(self._tr("btn_yes"), QMessageBox.ButtonRole.YesRole)
        no_btn = msg_box.addButton(self._tr("btn_no"), QMessageBox.ButtonRole.NoRole)
        msg_box.setDefaultButton(no_btn)
        msg_box.exec()
        return msg_box.clickedButton() == yes_btn

    def _configure_tables(self) -> None:
        """Configure table headers, selection behavior, and read-only states."""
        self.table_transaction.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table_transaction.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.table_transaction.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table_transaction.setAlternatingRowColors(True)
        self.table_transaction.verticalHeader().setVisible(False)

        self.table_accounts.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table_accounts.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.table_accounts.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table_accounts.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.table_accounts.setAlternatingRowColors(True)
        self.table_accounts.verticalHeader().setVisible(False)

    # ==========================================================================
    # Dynamic Form State Management (Add Transaction Tab)
    # ==========================================================================

    def get_selected_transaction_type(self) -> str:
        """Return the currently active canonical transaction type ('Expense', 'Income', or 'Transfer')."""
        if self.buton_income.isChecked():
            return db.TX_TYPE_INCOME
        if hasattr(self, "buton_transfer") and self.buton_transfer.isChecked():
            return db.TX_TYPE_TRANSFER
        return db.TX_TYPE_EXPENSE

    def _on_transaction_type_changed(self) -> None:
        """
        Update categories, account dropdowns, and dynamic fields whenever the user
        switches between Expense, Income, and Transfer.
        """
        self.update_category()
        self.populate_account_combos()
        self._update_dynamic_transaction_fields()

    def update_category(self) -> None:
        """
        Populate `combo_category` with localized category names while storing canonical
        English category keys in `itemData` for consistent database storage.
        """
        prev_canonical = self.combo_category.currentData()
        self.combo_category.clear()

        tx_type = self.get_selected_transaction_type()
        if tx_type == db.TX_TYPE_EXPENSE:
            cat_keys = EXPENSE_CATEGORIES
        elif tx_type == db.TX_TYPE_INCOME:
            cat_keys = INCOME_CATEGORIES
        elif tx_type == db.TX_TYPE_TRANSFER:
            cat_keys = TRANSFER_CATEGORIES
        else:
            self.combo_category.addItem(self._tr("select_category_prompt"), "")
            return

        for canonical_key, localized_label in i18n.get_localized_categories(
            cat_keys, self.current_lang
        ):
            self.combo_category.addItem(localized_label, canonical_key)

        if prev_canonical:
            for idx in range(self.combo_category.count()):
                if self.combo_category.itemData(idx) == prev_canonical:
                    self.combo_category.setCurrentIndex(idx)
                    break

    def populate_account_combos(self) -> None:
        """
        Populate `combo_account`, `combo_from_account`, and `combo_to_account` dynamically
        from the SQLite `accounts` table along with localized real-time balances and limits.
        """
        summary = db.get_financial_summary()
        cash_accounts = summary["cash_accounts"]
        credit_cards = summary["credit_cards"]
        tx_type = self.get_selected_transaction_type()

        cash_tag = self._tr("combo_cash_bank_tag")
        card_tag = self._tr("combo_credit_card_tag")
        bal_lbl = self._tr("combo_balance_label")
        avail_lbl = self._tr("combo_avail_limit_label")
        stmt_debt_lbl = self._tr("combo_stmt_debt_label")
        total_debt_lbl = self._tr("combo_total_debt_label")

        # Preserve previous selections across refreshes and language switches
        prev_single = self.combo_account.currentData()
        prev_single_name = prev_single["name"] if isinstance(prev_single, dict) else None

        prev_from = self.combo_from_account.currentData()
        prev_from_name = prev_from["name"] if isinstance(prev_from, dict) else None

        prev_to = self.combo_to_account.currentData()
        prev_to_name = prev_to["name"] if isinstance(prev_to, dict) else None

        self.combo_account.blockSignals(True)
        self.combo_account.clear()

        if tx_type == db.TX_TYPE_INCOME:
            # Income goes primarily into Checking/Cash accounts
            for acc in cash_accounts:
                label = f"{acc['name']}  [{cash_tag} • {bal_lbl}: {acc['current_balance']:,.2f} ₺]"
                self.combo_account.addItem(label, acc)
        else:
            # Expense can be paid from either a Checking/Cash account or a Credit Card
            for acc in cash_accounts:
                label = f"{acc['name']}  [{cash_tag} • {bal_lbl}: {acc['current_balance']:,.2f} ₺]"
                self.combo_account.addItem(label, acc)
            for card in credit_cards:
                label = (
                    f"{card['name']}  [{card_tag} • {avail_lbl}: "
                    f"{card['available_limit']:,.2f} ₺]"
                )
                self.combo_account.addItem(label, card)

        # Restore previous selection if still available
        if prev_single_name:
            for idx in range(self.combo_account.count()):
                data = self.combo_account.itemData(idx)
                if isinstance(data, dict) and data.get("name") == prev_single_name:
                    self.combo_account.setCurrentIndex(idx)
                    break

        self.combo_account.blockSignals(False)

        # Populate Transfer combos: From Account (Cash/Bank) -> To Account (Credit Cards & Cash/Bank)
        self.combo_from_account.clear()
        for acc in cash_accounts:
            label = f"{acc['name']}  ({bal_lbl}: {acc['current_balance']:,.2f} ₺)"
            self.combo_from_account.addItem(label, acc)

        if prev_from_name:
            for idx in range(self.combo_from_account.count()):
                data = self.combo_from_account.itemData(idx)
                if isinstance(data, dict) and data.get("name") == prev_from_name:
                    self.combo_from_account.setCurrentIndex(idx)
                    break

        self.combo_to_account.clear()
        # List Credit Cards first in `To Account` since Transfer is primarily for Credit Card Debt Payment
        for card in credit_cards:
            label = (
                f"{card['name']}  [{card_tag} • {stmt_debt_lbl}: "
                f"{card['current_statement_debt']:,.2f} ₺ | {total_debt_lbl}: {card['total_debt']:,.2f} ₺]"
            )
            self.combo_to_account.addItem(label, card)
        for acc in cash_accounts:
            label = f"{acc['name']}  [{cash_tag} • {bal_lbl}: {acc['current_balance']:,.2f} ₺]"
            self.combo_to_account.addItem(label, acc)

        if prev_to_name:
            for idx in range(self.combo_to_account.count()):
                data = self.combo_to_account.itemData(idx)
                if isinstance(data, dict) and data.get("name") == prev_to_name:
                    self.combo_to_account.setCurrentIndex(idx)
                    break

    def _on_selected_account_changed(self) -> None:
        """Trigger dynamic field visibility and preview update when the selected account changes."""
        self._update_dynamic_transaction_fields()

    def _update_dynamic_transaction_fields(self) -> None:
        """
        Show or hide dynamic fields on the Add Transaction tab:
          - If `Transfer` is selected: hide `widget_single_account` and `widget_installments`,
            and show `widget_transfer_accounts` (`From Account` -> `To Account`).
          - If `Expense` is selected AND a Credit Card is selected in `combo_account`:
            show `widget_installments` (`Installments` spinbox + statement closing preview).
          - Otherwise: show `widget_single_account` and hide `widget_installments`.
        """
        tx_type = self.get_selected_transaction_type()

        if tx_type == db.TX_TYPE_TRANSFER:
            self.widget_single_account.setVisible(False)
            self.widget_transfer_accounts.setVisible(True)
            self.widget_installments.setVisible(False)
            self.spin_installments.setValue(1)
            return

        self.widget_single_account.setVisible(True)
        self.widget_transfer_accounts.setVisible(False)

        selected_acc = self.combo_account.currentData()
        is_credit_card = (
            isinstance(selected_acc, dict)
            and selected_acc.get("account_type") == db.ACCOUNT_TYPE_CREDIT_CARD
        )

        if tx_type == db.TX_TYPE_EXPENSE and is_credit_card:
            self.widget_installments.setVisible(True)
            self.update_installment_preview()
        else:
            self.widget_installments.setVisible(False)
            self.spin_installments.setValue(1)

    def update_installment_preview(self) -> None:
        """
        Calculate and display a real-time localized preview of the credit card statement closing
        date, whether the transaction falls into the current or future statement period, and the
        monthly installment breakdown when `Installments >= 1`.
        """
        if not self.widget_installments.isVisible():
            return

        selected_acc = self.combo_account.currentData()
        if not isinstance(selected_acc, dict) or selected_acc.get("account_type") != db.ACCOUNT_TYPE_CREDIT_CARD:
            self.label_installment_preview.clear()
            return

        closing_day = int(selected_acc.get("closing_day") or 1)
        due_day = int(selected_acc.get("due_day") or 1)
        inst_count = self.spin_installments.value()

        qdate = self.line_date.date()
        tx_date = db.parse_date(qdate.toString("dd.MM.yyyy"))

        try:
            raw_amount = float(self.line_amount.text().replace(",", ".").strip())
            if raw_amount <= 0:
                raw_amount = 0.0
        except ValueError:
            raw_amount = 0.0

        schedule = db.calculate_installment_schedule(
            total_amount=raw_amount,
            tx_date=tx_date,
            closing_day=closing_day,
            installments=inst_count,
        )
        first_item = schedule[0]
        last_item = schedule[-1]

        first_period_localized = (
            self._tr("period_current_stmt")
            if first_item["is_current_period"]
            else self._tr("period_future_stmt")
        )

        if inst_count == 1:
            if raw_amount > 0:
                text = self._tr(
                    "preview_single_with_amt",
                    amount=f"{raw_amount:,.2f}",
                    stmt_date=first_item["statement_date_str"],
                    period=first_period_localized,
                    closing_day=closing_day,
                    due_day=due_day,
                )
            else:
                text = self._tr(
                    "preview_single_no_amt",
                    tx_date=qdate.toString("dd.MM.yyyy"),
                    stmt_date=first_item["statement_date_str"],
                    period=first_period_localized,
                )
        else:
            if raw_amount > 0:
                text = self._tr(
                    "preview_multi_with_amt",
                    count=inst_count,
                    inst_amount=f"{first_item['raw_amount']:,.2f}",
                    total_amount=f"{raw_amount:,.2f}",
                    first_stmt=first_item["statement_date_str"],
                    first_period=first_period_localized,
                    last_stmt=last_item["statement_date_str"],
                )
            else:
                text = self._tr(
                    "preview_multi_no_amt",
                    count=inst_count,
                    first_stmt=first_item["statement_date_str"],
                    first_period=first_period_localized,
                    last_stmt=last_item["statement_date_str"],
                )

        self.label_installment_preview.setText(text)

    # ==========================================================================
    # Saving Transactions (Expense, Income, Transfer / Installments)
    # ==========================================================================

    def save_function(self) -> None:
        """
        Validate user inputs and record the transaction (or installment series) into SQLite.
        Canonical English transaction types and category keys are stored in the database.
        """
        try:
            amount_text = self.line_amount.text().replace(",", ".").strip()
            try:
                raw_amount = float(amount_text)
            except ValueError:
                QMessageBox.warning(
                    self,
                    self._tr("msg_invalid_input_title"),
                    self._tr("msg_invalid_input_body"),
                )
                return

            if raw_amount <= 0:
                QMessageBox.warning(
                    self,
                    self._tr("msg_invalid_amount_title"),
                    self._tr("msg_invalid_amount_body"),
                )
                return

            tx_type = self.get_selected_transaction_type()
            description = self.line_descr.text().strip()
            # Store canonical English category key in the database
            canonical_category = (
                self.combo_category.currentData() or self.combo_category.currentText()
            )
            qdate = self.line_date.date()
            tx_date = db.parse_date(qdate.toString("dd.MM.yyyy"))

            if tx_type == db.TX_TYPE_TRANSFER:
                from_data = self.combo_from_account.currentData()
                to_data = self.combo_to_account.currentData()
                if not isinstance(from_data, dict) or not isinstance(to_data, dict):
                    QMessageBox.warning(
                        self,
                        self._tr("msg_acc_sel_err_title"),
                        self._tr("msg_acc_sel_transfer_body"),
                    )
                    return

                from_name = from_data["name"]
                to_name = to_data["name"]
                if from_name == to_name:
                    QMessageBox.warning(
                        self,
                        self._tr("msg_transfer_err_title"),
                        self._tr("msg_transfer_same_acc_body"),
                    )
                    return

                db.record_transaction(
                    transaction_type=db.TX_TYPE_TRANSFER,
                    raw_amount=raw_amount,
                    category=canonical_category,
                    description=description,
                    account_name=from_name,
                    tx_date=tx_date,
                    to_account_name=to_name,
                    installments=1,
                )
            else:
                acc_data = self.combo_account.currentData()
                if not isinstance(acc_data, dict):
                    QMessageBox.warning(
                        self,
                        self._tr("msg_acc_sel_err_title"),
                        self._tr("msg_acc_sel_single_body"),
                    )
                    return

                account_name = acc_data["name"]
                is_card = acc_data.get("account_type") == db.ACCOUNT_TYPE_CREDIT_CARD
                installments = (
                    self.spin_installments.value()
                    if (tx_type == db.TX_TYPE_EXPENSE and is_card)
                    else 1
                )

                db.record_transaction(
                    transaction_type=tx_type,
                    raw_amount=raw_amount,
                    category=canonical_category,
                    description=description,
                    account_name=account_name,
                    tx_date=tx_date,
                    to_account_name=None,
                    installments=installments,
                )

            QMessageBox.information(
                self, self._tr("msg_success_title"), self._tr("msg_tx_saved_body")
            )
            self.line_amount.clear()
            self.line_descr.clear()
            self.spin_installments.setValue(1)
            self.refresh_all_views()

        except Exception as exc:
            err_msg = i18n.translate_db_exception(str(exc), self.current_lang)
            QMessageBox.critical(
                self,
                self._tr("msg_db_err_title"),
                self._tr("msg_tx_save_failed", error=err_msg),
            )

    # ==========================================================================
    # Dashboard & Credit Card Summary Cards Rendering
    # ==========================================================================

    def refresh_all_views(self) -> None:
        """Refresh account dropdowns, Dashboard metrics, Credit Card cards, and tables."""
        self.populate_account_combos()
        self._update_dynamic_transaction_fields()
        self.update_dashboard_summaries()
        self.update_table()
        self.update_accounts_table()

    def update_dashboard_summaries(self) -> None:
        """
        Update the top liquid cash/bank balance card, income/expense summary cards,
        and rebuild the per-credit-card summary cards with visual progress bars.
        """
        summary = db.get_financial_summary()

        # 1. Total Liquid Cash/Bank Balance (completely unaffected by credit card purchases)
        liquid_bal = summary["total_liquid_balance"]
        self.label_liquid_value.setText(f"{liquid_bal:,.2f} ₺")

        if summary["cash_accounts"]:
            per_acc_parts = [
                f"{acc['name']}: {acc['current_balance']:,.2f} ₺"
                for acc in summary["cash_accounts"]
            ]
            self.label_liquid_sub.setText("  |  ".join(per_acc_parts))
        else:
            self.label_liquid_sub.setText(self._tr("metric_liquid_no_acc"))

        # 2. Total Income & Total Expense (Transfers are strictly excluded from Expenses)
        self.label_income_value.setText(f"{summary['total_income']:,.2f} ₺")
        self.label_expense_value.setText(f"{summary['total_expense']:,.2f} ₺")
        if summary["total_transfers"] > 0:
            self.label_expense_sub.setText(
                self._tr(
                    "metric_expense_sub_transfers",
                    amount=f"{summary['total_transfers']:,.2f}",
                )
            )
        else:
            self.label_expense_sub.setText(self._tr("metric_expense_sub_default"))

        # 3. Rebuild Credit Card Summary Cards inside `creditCardsContainerLayout`
        layout = self.creditCardsContainerLayout
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        credit_cards = summary["credit_cards"]
        if not credit_cards:
            empty_label = QLabel(self._tr("empty_credit_cards"))
            empty_label.setStyleSheet("color: #8b949e; font-style: italic; padding: 12px;")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(empty_label)
            return

        for card in credit_cards:
            card_widget = self._create_credit_card_summary_widget(card)
            layout.addWidget(card_widget)

    def _create_credit_card_summary_widget(self, card: Dict[str, Any]) -> QWidget:
        """
        Build a localized visual summary card widget for a single Credit Card displaying:
          - Card Name & Next Statement Closing Date (plus Payment Due Date)
          - Current Statement Debt (amount due in the current statement period)
          - Total Debt (including future installments)
          - Available Limit / Total Limit with a styled visual QProgressBar
        """
        frame = QFrame()
        frame.setStyleSheet(
            """
            QFrame {
                background-color: #182232;
                border: 1px solid #2b3a52;
                border-radius: 9px;
                padding: 8px 12px;
            }
            QLabel {
                border: none;
                background: transparent;
                padding: 0px;
            }
            """
        )
        vbox = QVBoxLayout(frame)
        vbox.setContentsMargins(10, 8, 10, 8)
        vbox.setSpacing(6)

        # Header Row: Card Name on left, Next Statement Closing Date & Due Date on right
        header_row = QHBoxLayout()
        title_lbl = QLabel(f"💳 {card['name']}")
        title_lbl.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: 700;")

        closing_lbl = QLabel(
            self._tr(
                "card_header_dates",
                closing_date=card["next_closing_date_str"],
                due_date=card["next_due_date_str"],
            )
        )
        closing_lbl.setStyleSheet("color: #79c0ff; font-size: 12px; font-weight: 600;")
        closing_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        header_row.addWidget(title_lbl)
        header_row.addStretch()
        header_row.addWidget(closing_lbl)
        vbox.addLayout(header_row)

        # Metrics Row: Current Statement Debt | Total Debt | Available / Total Limit
        metrics_row = QHBoxLayout()
        metrics_row.setSpacing(16)

        curr_debt_lbl = QLabel(
            f"{self._tr('card_curr_stmt_debt')} "
            f"<b style='color:#ffa657;'>{card['current_statement_debt']:,.2f} ₺</b>"
        )
        total_debt_lbl = QLabel(
            f"{self._tr('card_total_debt')} "
            f"<b style='color:#f85149;'>{card['total_debt']:,.2f} ₺</b>"
        )
        avail_limit_lbl = QLabel(
            f"{self._tr('card_avail_limit')} "
            f"<b style='color:#3fb950;'>{card['available_limit']:,.2f} ₺</b>"
            f" / {card['credit_limit']:,.2f} ₺"
        )

        metrics_row.addWidget(curr_debt_lbl)
        metrics_row.addWidget(total_debt_lbl)
        metrics_row.addStretch()
        metrics_row.addWidget(avail_limit_lbl)
        vbox.addLayout(metrics_row)

        # Visual Progress Bar showing Available Limit vs Total Limit
        progress = QProgressBar()
        progress.setRange(0, 100)
        avail_pct = int(card["available_percent"])
        used_pct = int(card["used_percent"])
        progress.setValue(avail_pct)
        progress.setFormat(
            self._tr(
                "card_progress_format",
                avail_pct=avail_pct,
                avail_amount=f"{card['available_limit']:,.2f}",
                used_pct=used_pct,
            )
        )

        # Dynamic color coding based on remaining available limit percentage
        if avail_pct >= 50:
            chunk_color = "#238636"  # Healthy green
        elif avail_pct >= 20:
            chunk_color = "#d29922"  # Warning amber
        else:
            chunk_color = "#da3633"  # High utilization red

        progress.setStyleSheet(
            f"""
            QProgressBar {{
                background-color: #0d1117;
                border: 1px solid #30363d;
                border-radius: 6px;
                text-align: center;
                color: #f0f6fc;
                font-size: 11px;
                font-weight: 700;
            }}
            QProgressBar::chunk {{
                background-color: {chunk_color};
                border-radius: 5px;
            }}
            """
        )
        vbox.addWidget(progress)

        return frame

    def update_table(self) -> None:
        """
        Filter and populate the Dashboard transaction table (`table_transaction`)
        with color-coded amounts, localized categories, and localized statement period badges.
        Supports searching in both English and Turkish simultaneously.
        """
        try:
            search_query = self.line_search.text().strip().lower()
            type_filter = "All"
            if self.radio_income.isChecked():
                type_filter = db.TX_TYPE_INCOME
            elif self.radio_expense.isChecked():
                type_filter = db.TX_TYPE_EXPENSE
            elif hasattr(self, "radio_transfer") and self.radio_transfer.isChecked():
                type_filter = db.TX_TYPE_TRANSFER

            # Fetch records by type_filter first, then match search against both EN and TR display strings
            all_records = db.get_transactions_for_display(
                search_text="", type_filter=type_filter
            )

            self.table_transaction.setRowCount(0)
            bold_font = QFont()
            bold_font.setBold(True)

            row_idx = 0
            for rec in all_records:
                amount_val = float(rec["amount"])
                tx_type = rec["transaction_type"]
                raw_cat = rec["category"]
                localized_cat = i18n.translate_category(raw_cat, self.current_lang)
                raw_period = rec["period_display"]
                localized_period = i18n.translate_period_display(
                    raw_period, self.current_lang
                )

                if search_query:
                    searchable_blob = " ".join(
                        [
                            str(rec["date"]).lower(),
                            str(rec["account_display"]).lower(),
                            raw_cat.lower(),
                            localized_cat.lower(),
                            str(rec["description"]).lower(),
                            tx_type.lower(),
                            raw_period.lower(),
                            localized_period.lower(),
                            f"{abs(amount_val):.2f}",
                            str(abs(amount_val)),
                        ]
                    )
                    if search_query not in searchable_blob:
                        continue

                self.table_transaction.insertRow(row_idx)

                if tx_type == db.TX_TYPE_INCOME:
                    amount_str = f"+{abs(amount_val):,.2f} ₺"
                    amount_color = QColor("#3fb950")
                elif tx_type == db.TX_TYPE_TRANSFER:
                    amount_str = f"⇄ {abs(amount_val):,.2f} ₺"
                    amount_color = QColor("#58a6ff")
                else:
                    amount_str = f"-{abs(amount_val):,.2f} ₺"
                    amount_color = QColor("#f85149")

                amount_item = QTableWidgetItem(amount_str)
                amount_item.setForeground(amount_color)
                amount_item.setFont(bold_font)

                cat_item = QTableWidgetItem(localized_cat)
                desc_item = QTableWidgetItem(rec["description"])
                acc_item = QTableWidgetItem(rec["account_display"])
                date_item = QTableWidgetItem(rec["date"])
                period_item = QTableWidgetItem(localized_period)

                # Highlight Current vs Future Statement items in the Period column
                if "Current Stmt" in raw_period:
                    period_item.setForeground(QColor("#ffa657"))
                elif "Future Stmt" in raw_period:
                    period_item.setForeground(QColor("#79c0ff"))
                elif tx_type == db.TX_TYPE_TRANSFER:
                    period_item.setForeground(QColor("#58a6ff"))
                elif tx_type == db.TX_TYPE_INCOME:
                    period_item.setForeground(QColor("#3fb950"))

                self.table_transaction.setItem(row_idx, 0, amount_item)
                self.table_transaction.setItem(row_idx, 1, cat_item)
                self.table_transaction.setItem(row_idx, 2, desc_item)
                self.table_transaction.setItem(row_idx, 3, acc_item)
                self.table_transaction.setItem(row_idx, 4, date_item)
                if self.table_transaction.columnCount() > 5:
                    self.table_transaction.setItem(row_idx, 5, period_item)

                row_idx += 1

        except Exception as exc:
            print(f"Table update error: {exc}")

    # ==========================================================================
    # Accounts / Credit Cards Management Tab
    # ==========================================================================

    def _on_account_creation_type_changed(self) -> None:
        """
        Switch the Accounts / Cards creation form between Checking/Cash Account fields
        (Account Name, Initial Balance) and Credit Card fields (Card Name, Total Limit,
        Statement Closing Day 1-31, Payment Due Day 1-31).
        """
        is_card = self.radio_add_credit_card.isChecked()
        self.widget_cash_fields.setVisible(not is_card)
        self.widget_card_fields.setVisible(is_card)

        if is_card:
            self.label_new_acc_name.setText(self._tr("label_card_acc_name"))
            self.line_new_acc_name.setPlaceholderText(self._tr("placeholder_card_acc_name"))
            self.buton_add_account.setText(self._tr("btn_add_card_acc"))
        else:
            self.label_new_acc_name.setText(self._tr("label_cash_acc_name"))
            self.line_new_acc_name.setPlaceholderText(self._tr("placeholder_cash_acc_name"))
            self.buton_add_account.setText(self._tr("btn_add_cash_acc"))

    def handle_add_account(self) -> None:
        """Validate and create a new Checking/Cash Account or Credit Card in SQLite."""
        name = self.line_new_acc_name.text().strip()
        if not name:
            QMessageBox.warning(
                self,
                self._tr("msg_val_err_title"),
                self._tr("msg_enter_acc_name"),
            )
            return

        is_card = self.radio_add_credit_card.isChecked()
        try:
            if is_card:
                limit_text = self.line_card_limit.text().replace(",", ".").strip()
                try:
                    credit_limit = float(limit_text)
                except ValueError:
                    QMessageBox.warning(
                        self,
                        self._tr("msg_invalid_limit_title"),
                        self._tr("msg_invalid_limit_body"),
                    )
                    return

                closing_day = self.spin_closing_day.value()
                due_day = self.spin_due_day.value()
                db.add_credit_card(
                    name=name,
                    credit_limit=credit_limit,
                    closing_day=closing_day,
                    due_day=due_day,
                )
                QMessageBox.information(
                    self,
                    self._tr("msg_card_added_title"),
                    self._tr(
                        "msg_card_added_body",
                        name=name,
                        limit=f"{credit_limit:,.2f}",
                        closing_day=closing_day,
                        due_day=due_day,
                    ),
                )
                self.line_card_limit.clear()
            else:
                init_text = self.line_initial_balance.text().replace(",", ".").strip() or "0"
                try:
                    initial_balance = float(init_text)
                except ValueError:
                    QMessageBox.warning(
                        self,
                        self._tr("msg_invalid_init_bal_title"),
                        self._tr("msg_invalid_init_bal_body"),
                    )
                    return

                db.add_cash_account(name=name, initial_balance=initial_balance)
                QMessageBox.information(
                    self,
                    self._tr("msg_acc_added_title"),
                    self._tr(
                        "msg_acc_added_body",
                        name=name,
                        balance=f"{initial_balance:,.2f}",
                    ),
                )
                self.line_initial_balance.setText("0.00")

            self.line_new_acc_name.clear()
            self.refresh_all_views()

        except ValueError as val_err:
            err_msg = i18n.translate_db_exception(str(val_err), self.current_lang)
            QMessageBox.warning(
                self, self._tr("msg_could_not_add_acc_title"), err_msg
            )
        except Exception as exc:
            err_msg = i18n.translate_db_exception(str(exc), self.current_lang)
            QMessageBox.critical(
                self,
                self._tr("msg_db_err_title"),
                self._tr("msg_create_acc_failed", error=err_msg),
            )

    def update_accounts_table(self) -> None:
        """Populate `table_accounts` on the Accounts / Cards tab with localized live balances and limits."""
        summary = db.get_financial_summary()
        all_rows = []

        for acc in summary["cash_accounts"]:
            all_rows.append(
                {
                    "name": acc["name"],
                    "type": self._tr("acc_type_cash_bank"),
                    "primary_metric": self._tr(
                        "acc_table_balance", amount=f"{acc['current_balance']:,.2f}"
                    ),
                    "secondary_metric": self._tr(
                        "acc_table_initial", amount=f"{acc['initial_balance']:,.2f}"
                    ),
                    "schedule": self._tr("acc_table_liquid_schedule"),
                }
            )

        for card in summary["credit_cards"]:
            all_rows.append(
                {
                    "name": card["name"],
                    "type": self._tr("acc_type_credit_card"),
                    "primary_metric": self._tr(
                        "acc_table_avail_debt",
                        avail=f"{card['available_limit']:,.2f}",
                        debt=f"{card['total_debt']:,.2f}",
                    ),
                    "secondary_metric": self._tr(
                        "acc_table_limit", amount=f"{card['credit_limit']:,.2f}"
                    ),
                    "schedule": self._tr(
                        "acc_table_card_schedule",
                        closing_day=card["closing_day"],
                        next_closing=card["next_closing_date_str"],
                        due_day=card["due_day"],
                    ),
                }
            )

        self.table_accounts.setRowCount(0)
        for idx, item in enumerate(all_rows):
            self.table_accounts.insertRow(idx)
            self.table_accounts.setItem(idx, 0, QTableWidgetItem(item["name"]))
            self.table_accounts.setItem(idx, 1, QTableWidgetItem(item["type"]))
            self.table_accounts.setItem(idx, 2, QTableWidgetItem(item["primary_metric"]))
            self.table_accounts.setItem(idx, 3, QTableWidgetItem(item["secondary_metric"]))
            self.table_accounts.setItem(idx, 4, QTableWidgetItem(item["schedule"]))

    def handle_delete_account(self) -> None:
        """Delete the currently selected account or credit card in `table_accounts`."""
        selected_row = self.table_accounts.currentRow()
        if selected_row < 0:
            QMessageBox.warning(
                self,
                self._tr("msg_no_sel_title"),
                self._tr("msg_no_sel_delete_body"),
            )
            return

        name_item = self.table_accounts.item(selected_row, 0)
        if not name_item:
            return
        acc_name = name_item.text()

        confirmed = self._ask_yes_no_question(
            self._tr("msg_confirm_delete_title"),
            self._tr("msg_confirm_delete_body", name=acc_name),
        )
        if not confirmed:
            return

        try:
            db.delete_account(acc_name)
            QMessageBox.information(
                self,
                self._tr("msg_deleted_title"),
                self._tr("msg_deleted_body", name=acc_name),
            )
            self.refresh_all_views()
        except ValueError as val_err:
            err_msg = i18n.translate_db_exception(str(val_err), self.current_lang)
            QMessageBox.warning(self, self._tr("msg_cannot_delete_title"), err_msg)
        except Exception as exc:
            err_msg = i18n.translate_db_exception(str(exc), self.current_lang)
            QMessageBox.critical(
                self,
                self._tr("msg_error_title"),
                self._tr("msg_delete_failed", error=err_msg),
            )

    # ==========================================================================
    # Factory Reset
    # ==========================================================================

    def reset_database(self) -> None:
        """Prompt for confirmation and wipe all transaction records from the database."""
        confirmed = self._ask_yes_no_question(
            self._tr("msg_confirm_reset_title"),
            self._tr("msg_confirm_reset_body"),
        )
        if confirmed:
            try:
                db.reset_all_transactions()
                self.refresh_all_views()
                QMessageBox.information(
                    self,
                    self._tr("msg_success_title"),
                    self._tr("msg_reset_success_body"),
                )
            except Exception as exc:
                err_msg = i18n.translate_db_exception(str(exc), self.current_lang)
                QMessageBox.critical(
                    self,
                    self._tr("msg_error_title"),
                    self._tr("msg_reset_failed", error=err_msg),
                )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
