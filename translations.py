"""
Localization dictionary and translation helpers for Expense Manager (EN / TR).

All database storage keys ('Expense', 'Income', 'Transfer', 'Cash / Bank', 'Credit Card',
and canonical category identifiers) remain strictly in English, while all user-facing UI
strings, categories, table headers, period badges, and dialog messages are dynamically
translated based on the active language code ('EN' or 'TR').
"""

import re
from typing import Dict, List, Tuple

# Supported language codes
LANG_EN = "EN"
LANG_TR = "TR"

# Canonical category keys (stored in SQLite) paired with their localized display labels
CATEGORY_TRANSLATIONS: Dict[str, Dict[str, str]] = {
    # Expense categories
    "Groceries & Supermarket": {
        LANG_EN: "Groceries & Supermarket",
        LANG_TR: "Market & Süpermarket",
    },
    "Bills & Utilities": {
        LANG_EN: "Bills & Utilities",
        LANG_TR: "Faturalar & Aidat",
    },
    "Rent & Housing": {
        LANG_EN: "Rent & Housing",
        LANG_TR: "Kira & Konut",
    },
    "Dining & Cafe": {
        LANG_EN: "Dining & Cafe",
        LANG_TR: "Restoran & Kafe",
    },
    "Transportation & Fuel": {
        LANG_EN: "Transportation & Fuel",
        LANG_TR: "Ulaşım & Akaryakıt",
    },
    "Shopping & Electronics": {
        LANG_EN: "Shopping & Electronics",
        LANG_TR: "Alışveriş & Elektronik",
    },
    "Health & Pharmacy": {
        LANG_EN: "Health & Pharmacy",
        LANG_TR: "Sağlık & Eczane",
    },
    "Entertainment & Subscriptions": {
        LANG_EN: "Entertainment & Subscriptions",
        LANG_TR: "Eğlence & Abonelikler",
    },
    "Education & Books": {
        LANG_EN: "Education & Books",
        LANG_TR: "Eğitim & Kitap",
    },
    "Other Expense": {
        LANG_EN: "Other Expense",
        LANG_TR: "Diğer Gider",
    },
    # Income categories
    "Salary & Payroll": {
        LANG_EN: "Salary & Payroll",
        LANG_TR: "Maaş & Hakediş",
    },
    "Freelance & Business": {
        LANG_EN: "Freelance & Business",
        LANG_TR: "Serbest Kazanç & İş",
    },
    "Investments & Dividends": {
        LANG_EN: "Investments & Dividends",
        LANG_TR: "Yatırım & Temettü",
    },
    "Refund & Cashback": {
        LANG_EN: "Refund & Cashback",
        LANG_TR: "İade & Nakit Puan",
    },
    "Gift & Bonus": {
        LANG_EN: "Gift & Bonus",
        LANG_TR: "Hediye & Prim",
    },
    "Other Income": {
        LANG_EN: "Other Income",
        LANG_TR: "Diğer Gelir",
    },
    # Transfer categories
    "Credit Card Debt Payment": {
        LANG_EN: "Credit Card Debt Payment",
        LANG_TR: "Kredi Kartı Borç Ödemesi",
    },
    "Inter-Account Transfer": {
        LANG_EN: "Inter-Account Transfer",
        LANG_TR: "Hesaplar Arası Transfer",
    },
    "Credit Card Payment": {
        LANG_EN: "Credit Card Payment",
        LANG_TR: "Kredi Kartı Ödemesi",
    },
}

# Canonical English category lists per transaction type
EXPENSE_CATEGORY_KEYS: List[str] = [
    "Groceries & Supermarket",
    "Bills & Utilities",
    "Rent & Housing",
    "Dining & Cafe",
    "Transportation & Fuel",
    "Shopping & Electronics",
    "Health & Pharmacy",
    "Entertainment & Subscriptions",
    "Education & Books",
    "Other Expense",
]

INCOME_CATEGORY_KEYS: List[str] = [
    "Salary & Payroll",
    "Freelance & Business",
    "Investments & Dividends",
    "Refund & Cashback",
    "Gift & Bonus",
    "Other Income",
]

TRANSFER_CATEGORY_KEYS: List[str] = [
    "Credit Card Debt Payment",
    "Inter-Account Transfer",
]

# Complete UI translation dictionary for English (EN) and Turkish (TR)
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    LANG_EN: {
        # Window & Tabs
        "window_title": "Expense Manager",
        "tab_add_tx": "Add Transaction",
        "tab_dashboard": "Dashboard",
        "tab_accounts": "Accounts / Cards",
        "lang_tooltip": "Switch interface language (English / Turkish)",

        # Add Transaction Tab
        "tx_header": "New Financial Transaction",
        "tx_subheader": "Record an expense, log income, or transfer funds to pay off credit card debt.",
        "group_tx_type": "Transaction Type",
        "radio_expense": "Expense",
        "radio_income": "Income",
        "radio_transfer": "Transfer (Debt Payment)",
        "label_amount": "Amount (₺)",
        "placeholder_amount": "Enter amount (e.g. 1250.00)",
        "label_tx_date": "Transaction Date",
        "label_account_card": "Account / Credit Card",
        "label_from_account": "From Account (Source Cash / Bank)",
        "label_to_account": "To Account / Credit Card (Destination)",
        "label_installments": "Installments (1 = Single Payment)",
        "label_category": "Category",
        "select_category_prompt": "Please select a category",
        "label_description": "Description",
        "placeholder_description": "Optional note or merchant name...",
        "btn_save_tx": "Save Transaction",

        # Account Combo Item Formatting
        "combo_cash_bank_tag": "Cash/Bank",
        "combo_credit_card_tag": "Credit Card",
        "combo_balance_label": "Balance",
        "combo_avail_limit_label": "Avail. Limit",
        "combo_stmt_debt_label": "Stmt Debt",
        "combo_total_debt_label": "Total Debt",

        # Installment Preview Strings
        "period_current_stmt": "Current Statement",
        "period_future_stmt": "Future Statement",
        "preview_single_with_amt": (
            "Single Payment of {amount} ₺  •  "
            "Assigned Statement Closing Date: {stmt_date} ({period})  •  "
            "Card Closing Day: {closing_day} / Due Day: {due_day}"
        ),
        "preview_single_no_amt": (
            "Assigned Statement Closing Date for {tx_date}: {stmt_date} ({period})  •  "
            "Full purchase amount reduces Available Limit immediately."
        ),
        "preview_multi_with_amt": (
            "{count} Installments × {inst_amount} ₺/month  "
            "(Total {total_amount} ₺ deducted from Available Limit now)\n"
            "1st Installment (1/{count}): Statement {first_stmt} [{first_period}]  ->  "
            "Final ({count}/{count}): Statement {last_stmt}"
        ),
        "preview_multi_no_amt": (
            "{count} Monthly Installments  •  "
            "1st Statement: {first_stmt} [{first_period}]  ->  "
            "Final Statement ({count}/{count}): {last_stmt}"
        ),

        # Dashboard Tab
        "metric_liquid_title": "TOTAL LIQUID CASH / BANK",
        "metric_liquid_sub_default": "Unaffected by unpaid card debt",
        "metric_liquid_no_acc": "No checking/cash accounts configured",
        "metric_income_title": "TOTAL INCOME",
        "metric_income_sub": "Cumulative logged income",
        "metric_expense_title": "TOTAL EXPENSES",
        "metric_expense_sub_default": "Excludes credit card debt transfers",
        "metric_expense_sub_transfers": "Excludes {amount} ₺ in debt transfers",
        "group_cards_overview": "Credit Cards & Statement Overview",
        "empty_credit_cards": (
            "No credit cards configured yet. Open the 'Accounts / Cards' tab to add a credit card."
        ),
        "card_header_dates": "Next Statement Closing: {closing_date}  •  Due Date: {due_date}",
        "card_curr_stmt_debt": "Current Statement Debt:",
        "card_total_debt": "Total Debt (incl. Future):",
        "card_avail_limit": "Available / Limit:",
        "card_progress_format": (
            "Available Limit: {avail_pct}% ({avail_amount} ₺ available • {used_pct}% used)"
        ),
        "label_search": "Search:",
        "placeholder_search": "Filter by description, category, account, statement period, or amount...",
        "filter_show_all": "Show All",
        "filter_incomes": "Incomes",
        "filter_expenses": "Expenses",
        "filter_transfers": "Transfers",
        "tx_col_amount": "AMOUNT",
        "tx_col_category": "CATEGORY",
        "tx_col_description": "DESCRIPTION",
        "tx_col_account": "ACCOUNT",
        "tx_col_date": "DATE",
        "tx_col_period": "PERIOD / STATUS",
        "status_debt_transfer": "Debt Payment / Transfer",
        "status_current_stmt": "Current Stmt ({date})",
        "status_future_stmt": "Future Stmt ({date})",
        "status_income": "Income",
        "status_direct_expense": "Direct Expense",
        "btn_factory_reset": "Factory Reset Transactions",

        # Accounts / Cards Tab
        "acc_header": "Manage Accounts & Credit Cards",
        "group_select_acc_type": "Select Account Type to Create",
        "radio_type_cash": "Checking / Cash Account",
        "radio_type_card": "Credit Card",
        "label_cash_acc_name": "Checking / Cash Account Name",
        "placeholder_cash_acc_name": "e.g. Main Bank, Savings, Physical Cash...",
        "label_card_acc_name": "Credit Card Name",
        "placeholder_card_acc_name": "e.g. Bonus Card, World Card, Axess...",
        "label_initial_balance": "Initial Balance (₺)",
        "placeholder_initial_balance": "Starting balance (e.g. 5000.00)",
        "label_card_limit": "Total Card Limit (₺)",
        "placeholder_card_limit": "Total credit limit (e.g. 50000.00)",
        "label_closing_day": "Statement Closing Day (1-31)",
        "label_due_day": "Payment Due Day (1-31)",
        "btn_add_cash_acc": "Add Checking / Cash Account",
        "btn_add_card_acc": "Add Credit Card",
        "label_existing_accounts": "Configured Accounts & Credit Cards",
        "acc_col_name": "NAME",
        "acc_col_type": "TYPE",
        "acc_col_balance_avail": "BALANCE / AVAIL. LIMIT",
        "acc_col_init_limit": "INIT. BAL / TOTAL LIMIT",
        "acc_col_schedule": "STATEMENT / DUE DAY",
        "acc_type_cash_bank": "Cash / Bank",
        "acc_type_credit_card": "Credit Card",
        "acc_table_balance": "{amount} ₺ (Balance)",
        "acc_table_initial": "{amount} ₺ (Initial)",
        "acc_table_liquid_schedule": "N/A (Liquid Account)",
        "acc_table_avail_debt": "{avail} ₺ Avail. (Debt: {debt} ₺)",
        "acc_table_limit": "{amount} ₺ (Limit)",
        "acc_table_card_schedule": "Closing: Day {closing_day} (Next: {next_closing}) • Due: Day {due_day}",
        "btn_delete_account": "Delete Selected Account / Card",

        # Dialogs & Messages
        "btn_yes": "Yes",
        "btn_no": "No",
        "msg_invalid_input_title": "Invalid Input",
        "msg_invalid_input_body": "Please enter a valid numeric amount.",
        "msg_invalid_amount_title": "Invalid Amount",
        "msg_invalid_amount_body": "Transaction amount must be greater than zero.",
        "msg_acc_sel_err_title": "Account Selection Error",
        "msg_acc_sel_transfer_body": "Please select both a source account and a destination account/card.",
        "msg_acc_sel_single_body": "Please select an account or credit card.",
        "msg_transfer_err_title": "Transfer Error",
        "msg_transfer_same_acc_body": "Source and destination accounts cannot be the same.",
        "msg_success_title": "Success",
        "msg_tx_saved_body": "Transaction saved successfully.",
        "msg_db_err_title": "Database Error",
        "msg_tx_save_failed": "Failed to save transaction: {error}",
        "msg_val_err_title": "Validation Error",
        "msg_enter_acc_name": "Please enter an account or credit card name.",
        "msg_invalid_limit_title": "Invalid Limit",
        "msg_invalid_limit_body": "Please enter a valid numeric total card limit.",
        "msg_card_added_title": "Credit Card Added",
        "msg_card_added_body": (
            "Credit card '{name}' (Limit: {limit} ₺, "
            "Closing Day: {closing_day}, Due Day: {due_day}) has been created."
        ),
        "msg_invalid_init_bal_title": "Invalid Initial Balance",
        "msg_invalid_init_bal_body": "Please enter a valid numeric initial balance.",
        "msg_acc_added_title": "Account Added",
        "msg_acc_added_body": (
            "Checking/Cash account '{name}' (Initial Balance: {balance} ₺) has been created."
        ),
        "msg_could_not_add_acc_title": "Could Not Add Account",
        "msg_create_acc_failed": "Failed to create account: {error}",
        "msg_no_sel_title": "No Selection",
        "msg_no_sel_delete_body": "Please select an account or credit card from the table to delete.",
        "msg_confirm_delete_title": "Confirm Delete",
        "msg_confirm_delete_body": "Are you sure you want to delete '{name}'?",
        "msg_deleted_title": "Deleted",
        "msg_deleted_body": "'{name}' has been removed.",
        "msg_cannot_delete_title": "Cannot Delete Account",
        "msg_error_title": "Error",
        "msg_delete_failed": "Failed to delete account: {error}",
        "msg_confirm_reset_title": "Confirm Reset",
        "msg_confirm_reset_body": (
            "All financial transaction records will be permanently deleted.\nAre you sure?"
        ),
        "msg_reset_success_body": "All transaction records have been factory reset.",
        "msg_reset_failed": "Failed to reset database: {error}",
    },
    LANG_TR: {
        # Window & Tabs
        "window_title": "Gider Yöneticisi (Expense Manager)",
        "tab_add_tx": "İşlem Ekle",
        "tab_dashboard": "Genel Bakış",
        "tab_accounts": "Hesaplar / Kartlar",
        "lang_tooltip": "Arayüz dilini değiştir (İngilizce / Türkçe)",

        # Add Transaction Tab
        "tx_header": "Yeni Finansal İşlem",
        "tx_subheader": "Gider veya gelir kaydedin ya da kredi kartı borcunuzu ödemek için transfer yapın.",
        "group_tx_type": "İşlem Türü",
        "radio_expense": "Gider",
        "radio_income": "Gelir",
        "radio_transfer": "Transfer (Borç Ödeme)",
        "label_amount": "Tutar (₺)",
        "placeholder_amount": "Tutar girin (örn. 1250.00)",
        "label_tx_date": "İşlem Tarihi",
        "label_account_card": "Hesap / Kredi Kartı",
        "label_from_account": "Gönderen Hesap (Kaynak Nakit / Banka)",
        "label_to_account": "Alıcı Hesap / Kredi Kartı (Hedef)",
        "label_installments": "Taksit Sayısı (1 = Tek Çekim)",
        "label_category": "Kategori",
        "select_category_prompt": "Lütfen bir kategori seçin",
        "label_description": "Açıklama",
        "placeholder_description": "İsteğe bağlı not veya işyeri adı...",
        "btn_save_tx": "İşlemi Kaydet",

        # Account Combo Item Formatting
        "combo_cash_bank_tag": "Nakit/Banka",
        "combo_credit_card_tag": "Kredi Kartı",
        "combo_balance_label": "Bakiye",
        "combo_avail_limit_label": "Kull. Limit",
        "combo_stmt_debt_label": "Ekstre Borcu",
        "combo_total_debt_label": "Toplam Borç",

        # Installment Preview Strings
        "period_current_stmt": "Güncel Ekstre Dönemi",
        "period_future_stmt": "Gelecek Ekstre Dönemi",
        "preview_single_with_amt": (
            "{amount} ₺ Tek Çekim  •  "
            "Hesap Kesim Tarihi: {stmt_date} ({period})  •  "
            "Kesim Günü: {closing_day} / Son Ödeme: {due_day}"
        ),
        "preview_single_no_amt": (
            "{tx_date} tarihi için Hesap Kesim Tarihi: {stmt_date} ({period})  •  "
            "Harcamanın tam tutarı Kullanılabilir Limitten anında düşülür."
        ),
        "preview_multi_with_amt": (
            "{count} Taksit × Aylık {inst_amount} ₺  "
            "(Toplam {total_amount} ₺ Kullanılabilir Limitten anında düşülür)\n"
            "1. Taksit (1/{count}): Ekstre {first_stmt} [{first_period}]  ->  "
            "Son Taksit ({count}/{count}): Ekstre {last_stmt}"
        ),
        "preview_multi_no_amt": (
            "{count} Aylık Taksit  •  "
            "1. Ekstre: {first_stmt} [{first_period}]  ->  "
            "Son Ekstre ({count}/{count}): {last_stmt}"
        ),

        # Dashboard Tab
        "metric_liquid_title": "TOPLAM LİKİT NAKİT / BANKA",
        "metric_liquid_sub_default": "Ödenmemiş kart borçlarından etkilenmez",
        "metric_liquid_no_acc": "Tanımlı vadesiz/nakit hesap yok",
        "metric_income_title": "TOPLAM GELİR",
        "metric_income_sub": "Kaydedilen toplam gelir",
        "metric_expense_title": "TOPLAM GİDER",
        "metric_expense_sub_default": "Kredi kartı borç transferleri hariçtir",
        "metric_expense_sub_transfers": "{amount} ₺ tutarındaki borç transferleri hariçtir",
        "group_cards_overview": "Kredi Kartları & Ekstre Özeti",
        "empty_credit_cards": (
            "Henüz kredi kartı eklenmedi. Yeni kart eklemek için 'Hesaplar / Kartlar' sekmesini açın."
        ),
        "card_header_dates": "Sonraki Hesap Kesim: {closing_date}  •  Son Ödeme: {due_date}",
        "card_curr_stmt_debt": "Güncel Ekstre Borcu:",
        "card_total_debt": "Toplam Borç (Gelecek Taksitler Dahil):",
        "card_avail_limit": "Kullanılabilir / Limit:",
        "card_progress_format": (
            "Kullanılabilir Limit: %{avail_pct} ({avail_amount} ₺ kullanılabilir • %{used_pct} kullanıldı)"
        ),
        "label_search": "Ara:",
        "placeholder_search": "Açıklama, kategori, hesap, ekstre dönemi veya tutara göre filtrele...",
        "filter_show_all": "Tümü",
        "filter_incomes": "Gelirler",
        "filter_expenses": "Giderler",
        "filter_transfers": "Transferler",
        "tx_col_amount": "TUTAR",
        "tx_col_category": "KATEGORİ",
        "tx_col_description": "AÇIKLAMA",
        "tx_col_account": "HESAP",
        "tx_col_date": "TARİH",
        "tx_col_period": "DÖNEM / DURUM",
        "status_debt_transfer": "Borç Ödeme / Transfer",
        "status_current_stmt": "Güncel Ekstre ({date})",
        "status_future_stmt": "Gelecek Ekstre ({date})",
        "status_income": "Gelir",
        "status_direct_expense": "Doğrudan Gider",
        "btn_factory_reset": "Tüm İşlemleri Sıfırla",

        # Accounts / Cards Tab
        "acc_header": "Hesap & Kredi Kartı Yönetimi",
        "group_select_acc_type": "Oluşturulacak Hesap Türünü Seçin",
        "radio_type_cash": "Vadesiz / Nakit Hesap",
        "radio_type_card": "Kredi Kartı",
        "label_cash_acc_name": "Vadesiz / Nakit Hesap Adı",
        "placeholder_cash_acc_name": "örn. Ana Banka, Birikim, Nakit Cüzdan...",
        "label_card_acc_name": "Kredi Kartı Adı",
        "placeholder_card_acc_name": "örn. Bonus Kart, World Kart, Axess...",
        "label_initial_balance": "Başlangıç Bakiyesi (₺)",
        "placeholder_initial_balance": "Başlangıç bakiyesi (örn. 5000.00)",
        "label_card_limit": "Toplam Kart Limiti (₺)",
        "placeholder_card_limit": "Toplam kredi kartı limiti (örn. 50000.00)",
        "label_closing_day": "Hesap Kesim Günü (1-31)",
        "label_due_day": "Son Ödeme Günü (1-31)",
        "btn_add_cash_acc": "Vadesiz / Nakit Hesap Ekle",
        "btn_add_card_acc": "Kredi Kartı Ekle",
        "label_existing_accounts": "Tanımlı Hesaplar ve Kredi Kartları",
        "acc_col_name": "HESAP / KART ADI",
        "acc_col_type": "TÜR",
        "acc_col_balance_avail": "BAKİYE / KULL. LİMİT",
        "acc_col_init_limit": "BAŞLANGIÇ / TOPLAM LİMİT",
        "acc_col_schedule": "KESİM / SON ÖDEME GÜNÜ",
        "acc_type_cash_bank": "Nakit / Banka",
        "acc_type_credit_card": "Kredi Kartı",
        "acc_table_balance": "{amount} ₺ (Bakiye)",
        "acc_table_initial": "{amount} ₺ (Başlangıç)",
        "acc_table_liquid_schedule": "Yok (Likit Hesap)",
        "acc_table_avail_debt": "{avail} ₺ Kull. (Borç: {debt} ₺)",
        "acc_table_limit": "{amount} ₺ (Limit)",
        "acc_table_card_schedule": "Kesim: {closing_day}. Gün (Sonraki: {next_closing}) • Son Ödeme: {due_day}. Gün",
        "btn_delete_account": "Seçili Hesabı / Kartı Sil",

        # Dialogs & Messages
        "btn_yes": "Evet",
        "btn_no": "Hayır",
        "msg_invalid_input_title": "Geçersiz Giriş",
        "msg_invalid_input_body": "Lütfen geçerli bir sayısal tutar girin.",
        "msg_invalid_amount_title": "Geçersiz Tutar",
        "msg_invalid_amount_body": "İşlem tutarı sıfırdan büyük olmalıdır.",
        "msg_acc_sel_err_title": "Hesap Seçim Hatası",
        "msg_acc_sel_transfer_body": "Lütfen hem gönderen hesabı hem de alıcı hesabı/kartı seçin.",
        "msg_acc_sel_single_body": "Lütfen bir hesap veya kredi kartı seçin.",
        "msg_transfer_err_title": "Transfer Hatası",
        "msg_transfer_same_acc_body": "Gönderen ve alıcı hesap aynı olamaz.",
        "msg_success_title": "Başarılı",
        "msg_tx_saved_body": "İşlem başarıyla kaydedildi.",
        "msg_db_err_title": "Veritabanı Hatası",
        "msg_tx_save_failed": "İşlem kaydedilemedi: {error}",
        "msg_val_err_title": "Doğrulama Hatası",
        "msg_enter_acc_name": "Lütfen bir hesap veya kredi kartı adı girin.",
        "msg_invalid_limit_title": "Geçersiz Limit",
        "msg_invalid_limit_body": "Lütfen geçerli bir sayısal kart limiti girin.",
        "msg_card_added_title": "Kredi Kartı Eklendi",
        "msg_card_added_body": (
            "'{name}' kredi kartı (Limit: {limit} ₺, "
            "Hesap Kesim Günü: {closing_day}, Son Ödeme Günü: {due_day}) oluşturuldu."
        ),
        "msg_invalid_init_bal_title": "Geçersiz Başlangıç Bakiyesi",
        "msg_invalid_init_bal_body": "Lütfen geçerli bir sayısal başlangıç bakiyesi girin.",
        "msg_acc_added_title": "Hesap Eklendi",
        "msg_acc_added_body": (
            "'{name}' vadesiz/nakit hesabı (Başlangıç Bakiyesi: {balance} ₺) oluşturuldu."
        ),
        "msg_could_not_add_acc_title": "Hesap Eklenemedi",
        "msg_create_acc_failed": "Hesap oluşturulamadı: {error}",
        "msg_no_sel_title": "Seçim Yapılmadı",
        "msg_no_sel_delete_body": "Lütfen silmek için tablodan bir hesap veya kredi kartı seçin.",
        "msg_confirm_delete_title": "Silme Onayı",
        "msg_confirm_delete_body": "'{name}' hesabını/kartını silmek istediğinize emin misiniz?",
        "msg_deleted_title": "Silindi",
        "msg_deleted_body": "'{name}' başarıyla silindi.",
        "msg_cannot_delete_title": "Hesap Silinemedi",
        "msg_error_title": "Hata",
        "msg_delete_failed": "Hesap silinemedi: {error}",
        "msg_confirm_reset_title": "Sıfırlama Onayı",
        "msg_confirm_reset_body": (
            "Tüm finansal işlem kayıtları kalıcı olarak silinecektir.\nEmin misiniz?"
        ),
        "msg_reset_success_body": "Tüm işlem kayıtları başarıyla sıfırlandı.",
        "msg_reset_failed": "Veritabanı sıfırlanamadı: {error}",
    },
}

# Build reverse lookup map so any localized category label can be resolved back to its canonical key
_REVERSE_CATEGORY_MAP: Dict[str, str] = {}
for _canon_key, _lang_map in CATEGORY_TRANSLATIONS.items():
    _REVERSE_CATEGORY_MAP[_canon_key.lower()] = _canon_key
    for _localized_val in _lang_map.values():
        _REVERSE_CATEGORY_MAP[_localized_val.lower()] = _canon_key


def tr(key: str, lang: str = LANG_EN, **kwargs) -> str:
    """
    Retrieve a translated UI string for `key` in language `lang` ('EN' or 'TR'),
    formatting any keyword placeholders if provided.
    """
    lang_dict = TRANSLATIONS.get(lang, TRANSLATIONS[LANG_EN])
    template = lang_dict.get(key, TRANSLATIONS[LANG_EN].get(key, key))
    if kwargs:
        try:
            return template.format(**kwargs)
        except KeyError:
            return template
    return template


def get_localized_categories(category_keys: List[str], lang: str = LANG_EN) -> List[Tuple[str, str]]:
    """
    Return a list of `(canonical_english_key, localized_display_text)` tuples
    for populating category combo boxes.
    """
    items: List[Tuple[str, str]] = []
    for key in category_keys:
        localized = CATEGORY_TRANSLATIONS.get(key, {}).get(lang, key)
        items.append((key, localized))
    return items


def translate_category(raw_category: str, lang: str = LANG_EN) -> str:
    """
    Translate a stored category name (or legacy category string) into the active UI language.
    """
    if not raw_category:
        return ""
    canonical = _REVERSE_CATEGORY_MAP.get(raw_category.strip().lower(), raw_category)
    return CATEGORY_TRANSLATIONS.get(canonical, {}).get(lang, raw_category)


def translate_period_display(raw_period: str, lang: str = LANG_EN) -> str:
    """
    Translate the statement period / status string returned by `database.get_transactions_for_display()`
    into the currently selected language ('EN' or 'TR').
    """
    if not raw_period or lang == LANG_EN:
        return raw_period

    if raw_period == "Debt Payment / Transfer":
        return tr("status_debt_transfer", lang)
    if raw_period == "Income":
        return tr("status_income", lang)
    if raw_period == "Direct Expense":
        return tr("status_direct_expense", lang)

    if raw_period.startswith("Current Stmt (") and raw_period.endswith(")"):
        date_part = raw_period[len("Current Stmt (") : -1]
        return tr("status_current_stmt", lang, date=date_part)

    if raw_period.startswith("Future Stmt (") and raw_period.endswith(")"):
        date_part = raw_period[len("Future Stmt (") : -1]
        return tr("status_future_stmt", lang, date=date_part)

    return raw_period


def translate_db_exception(error_message: str, lang: str = LANG_EN) -> str:
    """
    Translate validation exception messages raised by `database.py` into Turkish when `lang == 'TR'`
    while keeping `database.py` strictly in English.
    """
    if lang == LANG_EN:
        return error_message

    static_map = {
        "Account name cannot be empty.": "Hesap adı boş bırakılamaz.",
        "Card name cannot be empty.": "Kart adı boş bırakılamaz.",
        "Total card limit must be greater than zero.": "Toplam kart limiti sıfırdan büyük olmalıdır.",
        "Statement closing day must be between 1 and 31.": "Hesap kesim günü 1 ile 31 arasında olmalıdır.",
        "Payment due day must be between 1 and 31.": "Son ödeme günü 1 ile 31 arasında olmalıdır.",
        "Transaction amount must be greater than zero.": "İşlem tutarı sıfırdan büyük olmalıdır.",
        "Please select a target account/card for the transfer.": "Lütfen transfer için bir hedef hesap/kart seçin.",
        "Source and destination accounts cannot be the same.": "Gönderen ve alıcı hesap aynı olamaz.",
    }
    if error_message in static_map:
        return static_map[error_message]

    # Pattern: "An account or card named 'X' already exists."
    m_exists = re.match(r"^An account or card named '(.+)' already exists\.$", error_message)
    if m_exists:
        return f"'{m_exists.group(1)}' adında bir hesap veya kart zaten mevcut."

    # Pattern: "Cannot delete 'X' because it has N linked transaction(s)."
    m_del = re.match(
        r"^Cannot delete '(.+)' because it has (\d+) linked transaction\(s\)\.$",
        error_message,
    )
    if m_del:
        return (
            f"'{m_del.group(1)}' silinemedi; bu hesaba bağlı {m_del.group(2)} adet işlem kaydı bulunuyor."
        )

    return error_message
