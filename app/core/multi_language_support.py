#!/usr/bin/env python3
"""Multi-language Support System for S&D
Provides internationalization (i18n) and localization (l10n) capabilities.
"""

import gettext
import json
import locale
import logging
import math
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QCoreApplication, QTranslator
from PyQt6.QtWidgets import QApplication


class SupportedLanguage(Enum):
    """Supported languages with their ISO codes."""

    ENGLISH = ("en", "English", "English")
    SPANISH = ("es", "Español", "Spanish")
    FRENCH = ("fr", "Français", "French")
    GERMAN = ("de", "Deutsch", "German")
    ITALIAN = ("it", "Italiano", "Italian")
    PORTUGUESE = ("pt", "Português", "Portuguese")
    RUSSIAN = ("ru", "Русский", "Russian")
    CHINESE_SIMPLIFIED = ("zh_CN", "简体中文", "Chinese (Simplified)")
    CHINESE_TRADITIONAL = ("zh_TW", "繁體中文", "Chinese (Traditional)")
    JAPANESE = ("ja", "日本語", "Japanese")
    KOREAN = ("ko", "한국어", "Korean")
    ARABIC = ("ar", "العربية", "Arabic")
    HINDI = ("hi", "हिन्दी", "Hindi")
    DUTCH = ("nl", "Nederlands", "Dutch")
    POLISH = ("pl", "Polski", "Polish")
    SWEDISH = ("sv", "Svenska", "Swedish")
    NORWEGIAN = ("no", "Norsk", "Norwegian")
    DANISH = ("da", "Dansk", "Danish")
    FINNISH = ("fi", "Suomi", "Finnish")
    TURKISH = ("tr", "Türkçe", "Turkish")

    def __init__(self, code: str, native_name: str, english_name: str):
        self.code = code
        self.native_name = native_name
        self.english_name = english_name


@dataclass
class TranslationString:
    """Translation string with context and metadata."""

    key: str
    default_text: str
    context: str | None = None
    description: str | None = None
    plurals: dict[str, str] = field(default_factory=dict)
    variables: list[str] = field(default_factory=list)


class TranslationCategory(Enum):
    """Categories for organizing translations."""

    UI_GENERAL = "ui_general"
    UI_MENUS = "ui_menus"
    UI_BUTTONS = "ui_buttons"
    UI_DIALOGS = "ui_dialogs"
    UI_MESSAGES = "ui_messages"
    UI_STATUS = "ui_status"
    SCAN_OPERATIONS = "scan_operations"
    THREAT_DETECTION = "threat_detection"
    SETTINGS = "settings"
    REPORTS = "reports"
    ERRORS = "errors"
    HELP = "help"
    NOTIFICATIONS = "notifications"


@dataclass
class LanguagePreferences:
    """User language preferences."""

    primary_language: SupportedLanguage = SupportedLanguage.ENGLISH
    fallback_language: SupportedLanguage = SupportedLanguage.ENGLISH
    date_format: str = "%Y-%m-%d"
    time_format: str = "%H:%M:%S"
    number_format: str = "1,234.56"
    currency_symbol: str = "$"
    timezone: str = "UTC"
    text_direction: str = "ltr"  # "ltr" or "rtl"


class MultiLanguageSupport:
    """Comprehensive multi-language support system providing internationalization
    and localization for the S&D antivirus application.
    """

    def __init__(self, languages_dir: str = "locales"):
        self.logger = logging.getLogger(__name__)

        # Directory structure
        self.languages_dir = Path(languages_dir)
        self.translations_cache = {}

        # Current language settings
        self.current_language = SupportedLanguage.ENGLISH
        self.preferences = LanguagePreferences()

        # Qt translation objects
        self.qt_translator = None
        self.app_translator = None

        # Translation database
        self.translation_db = {}

        # Initialize system
        self._initialize_directories()
        self._load_system_locale()

        self.logger.info("Multi-language support system initialized")

    def _initialize_directories(self):
        """Initialize language directory structure."""
        try:
            # Create main languages directory
            self.languages_dir.mkdir(exist_ok=True)

            # Create subdirectories for each supported language
            for language in SupportedLanguage:
                lang_dir = self.languages_dir / language.code / "LC_MESSAGES"
                lang_dir.mkdir(parents=True, exist_ok=True)

                # Create translation files if they don't exist
                po_file = lang_dir / "s_and_d.po"
                lang_dir / "s_and_d.mo"

                if not po_file.exists():
                    self._create_initial_po_file(po_file, language)

            self.logger.info("Language directories initialized")

        except Exception:
            self.logerror(
                "Error initializing directories: %s".replace("%s", "{e}").replace(
                    "%d", "{e}"
                )
            )

    def _load_system_locale(self):
        """Detect and load system locale."""
        try:
            # Get system locale
            system_locale = locale.getdefaultlocale()[0]

            if system_locale:
                # Map system locale to supported language
                for language in SupportedLanguage:
                    if system_locale.startswith(language.code.split("_")[0]):
                        self.current_language = language
                        break

            # Set preferences based on detected language
            self._update_preferences_for_language(self.current_language)

            self.loginfo(
                "System locale detected: %s".replace("%s", "{system_locale}").replace(
                    "%d", "{system_locale}"
                )
            )

        except Exception:
            self.logwarning(
                "Error detecting system locale: %s".replace("%s", "{e}").replace(
                    "%d", "{e}"
                )
            )
            # Fall back to English
            self.current_language = SupportedLanguage.ENGLISH

    def _update_preferences_for_language(self, language: SupportedLanguage):
        """Update preferences based on selected language."""
        try:
            # Language-specific formatting preferences
            format_preferences = {
                SupportedLanguage.ENGLISH: {
                    "date_format": "%m/%d/%Y",
                    "time_format": "%I:%M:%S %p",
                    "number_format": "1,234.56",
                    "currency_symbol": "$",
                    "text_direction": "ltr",
                },
                SupportedLanguage.GERMAN: {
                    "date_format": "%d.%m.%Y",
                    "time_format": "%H:%M:%S",
                    "number_format": "1.234,56",
                    "currency_symbol": "€",
                    "text_direction": "ltr",
                },
                SupportedLanguage.FRENCH: {
                    "date_format": "%d/%m/%Y",
                    "time_format": "%H:%M:%S",
                    "number_format": "1 234,56",
                    "currency_symbol": "€",
                    "text_direction": "ltr",
                },
                SupportedLanguage.ARABIC: {
                    "date_format": "%d/%m/%Y",
                    "time_format": "%H:%M:%S",
                    "number_format": "1,234.56",
                    "currency_symbol": "﷼",
                    "text_direction": "rtl",
                },
                SupportedLanguage.JAPANESE: {
                    "date_format": "%Y年%m月%d日",
                    "time_format": "%H時%M分%S秒",
                    "number_format": "1,234.56",
                    "currency_symbol": "¥",
                    "text_direction": "ltr",
                },
                SupportedLanguage.CHINESE_SIMPLIFIED: {
                    "date_format": "%Y年%m月%d日",
                    "time_format": "%H:%M:%S",
                    "number_format": "1,234.56",
                    "currency_symbol": "¥",
                    "text_direction": "ltr",
                },
            }

            prefs = format_preferences.get(
                language, format_preferences[SupportedLanguage.ENGLISH]
            )

            self.preferences.primary_language = language
            self.preferences.date_format = prefs["date_format"]
            self.preferences.time_format = prefs["time_format"]
            self.preferences.number_format = prefs["number_format"]
            self.preferences.currency_symbol = prefs["currency_symbol"]
            self.preferences.text_direction = prefs["text_direction"]

        except Exception:
            self.logerror(
                "Error updating language preferences: %s".replace("%s", "{e}").replace(
                    "%d", "{e}"
                )
            )

    def set_language(self, language: SupportedLanguage) -> bool:
        """Set the application language.

        Args:
            language: Language to set

        Returns:
            True if language was set successfully
        """
        try:
            self.loginfo(
                "Setting language to %s".replace(
                    "%s", "{language.english_name}"
                ).replace("%d", "{language.english_name}")
            )

            # Update current language
            old_language = self.current_language
            self.current_language = language

            # Update preferences
            self._update_preferences_for_language(language)

            # Load translations
            success = self._load_translations(language)

            if success:
                # Update Qt translators
                self._update_qt_translators(language)

                # Trigger UI update
                self._notify_language_change(old_language, language)

                self.loginfo(
                    "Language successfully changed to %s".replace(
                        "%s", "{language.english_name}"
                    ).replace("%d", "{language.english_name}")
                )
                return True
            else:
                # Revert on failure
                self.current_language = old_language
                self.logerror(
                    "Failed to set language to %s".replace(
                        "%s", "{language.english_name}"
                    ).replace("%d", "{language.english_name}")
                )
                return False

        except Exception:
            self.logerror(
                "Error setting language: %s".replace("%s", "{e}").replace("%d", "{e}")
            )
            return False

    def get_available_languages(self) -> list[tuple[str, str, str]]:
        """Get list of available languages.

        Returns:
            List of tuples (code, native_name, english_name)
        """
        return [
            (lang.code, lang.native_name, lang.english_name)
            for lang in SupportedLanguage
        ]

    def translate(
        self,
        key: str,
        category: TranslationCategory = TranslationCategory.UI_GENERAL,
        default: str = None,
        **kwargs,
    ) -> str:
        """Translate a text string.

        Args:
            key: Translation key
            category: Translation category
            default: Default text if translation not found
            **kwargs: Variables for string formatting

        Returns:
            Translated string
        """
        try:
            # Build full key with category
            full_key = f"{category.value}.{key}"

            # Get translation from cache
            translation = self._get_translation(full_key, default or key)

            # Apply string formatting if variables provided
            if kwargs:
                translation = self._format_string(translation, **kwargs)

            return translation

        except Exception:
            self.logwarning(
                "Error translating '%s': %s".replace("%s", "{key, e}").replace(
                    "%d", "{key, e}"
                )
            )
            return default or key

    def translate_plural(
        self,
        key: str,
        count: int,
        category: TranslationCategory = TranslationCategory.UI_GENERAL,
        **kwargs,
    ) -> str:
        """Translate a string with plural forms.

        Args:
            key: Translation key
            count: Number for plural form selection
            category: Translation category
            **kwargs: Variables for string formatting

        Returns:
            Translated string with correct plural form
        """
        try:
            full_key = f"{category.value}.{key}"

            # Get plural translation
            translation = self._get_plural_translation(full_key, count)

            # Apply formatting
            if kwargs:
                kwargs["count"] = count
                translation = self._format_string(translation, **kwargs)

            return translation

        except Exception:
            self.logwarning(
                "Error translating plural '%s': %s".replace("%s", "{key, e}").replace(
                    "%d", "{key, e}"
                )
            )
            return f"{key} ({count})"

    def format_date(self, date_obj, format_type: str = "default") -> str:
        """Format date according to current locale.

        Args:
            date_obj: Date object to format
            format_type: Type of format ("default", "short", "long")

        Returns:
            Formatted date string
        """
        try:
            if format_type == "short":
                format_str = self.preferences.date_format.replace("%Y", "%y")
            elif format_type == "long":
                # Add day name for long format
                if self.current_language == SupportedLanguage.ENGLISH:
                    format_str = "%A, %B %d, %Y"
                else:
                    format_str = self.preferences.date_format
            else:
                format_str = self.preferences.date_format

            return date_obj.strftime(format_str)

        except Exception:
            self.logerror(
                "Error formatting date: %s".replace("%s", "{e}").replace("%d", "{e}")
            )
            return str(date_obj)

    def format_time(self, time_obj, include_seconds: bool = True) -> str:
        """Format time according to current locale.

        Args:
            time_obj: Time object to format
            include_seconds: Whether to include seconds

        Returns:
            Formatted time string
        """
        try:
            format_str = self.preferences.time_format
            if not include_seconds:
                format_str = format_str.replace(":%S", "").replace(".%f", "")

            return time_obj.strftime(format_str)

        except Exception:
            self.logerror(
                "Error formatting time: %s".replace("%s", "{e}").replace("%d", "{e}")
            )
            return str(time_obj)

    def format_number(self, number: float, decimal_places: int = 2) -> str:
        """Format number according to current locale.

        Args:
            number: Number to format
            decimal_places: Number of decimal places

        Returns:
            Formatted number string
        """
        try:
            if self.current_language == SupportedLanguage.GERMAN:
                # German format: 1.234,56
                formatted = f"{number:,.{decimal_places}f}"
                formatted = (
                    formatted.replace(",", "X").replace(".", ",").replace("X", ".")
                )
            elif self.current_language == SupportedLanguage.FRENCH:
                # French format: 1 234,56
                formatted = f"{number:,.{decimal_places}f}"
                formatted = formatted.replace(",", " ").replace(".", ",")
            else:
                # Default English format: 1,234.56
                formatted = f"{number:,.{decimal_places}f}"

            return formatted

        except Exception:
            self.logerror(
                "Error formatting number: %s".replace("%s", "{e}").replace("%d", "{e}")
            )
            return str(number)

    def format_file_size(self, size_bytes: int) -> str:
        """Format file size according to current locale.

        Args:
            size_bytes: Size in bytes

        Returns:
            Formatted size string
        """
        try:
            # Size units translations
            units = {
                SupportedLanguage.ENGLISH: ["B", "KB", "MB", "GB", "TB"],
                SupportedLanguage.GERMAN: ["B", "KB", "MB", "GB", "TB"],
                SupportedLanguage.FRENCH: ["o", "Ko", "Mo", "Go", "To"],
                SupportedLanguage.SPANISH: ["B", "KB", "MB", "GB", "TB"],
                SupportedLanguage.CHINESE_SIMPLIFIED: ["字节", "KB", "MB", "GB", "TB"],
                SupportedLanguage.JAPANESE: ["B", "KB", "MB", "GB", "TB"],
                SupportedLanguage.RUSSIAN: ["Б", "КБ", "МБ", "ГБ", "ТБ"],
            }

            unit_list = units.get(
                self.current_language, units[SupportedLanguage.ENGLISH]
            )

            if size_bytes == 0:
                return f"0 {unit_list[0]}"

            size = abs(size_bytes)
            unit_index = min(int(math.floor(math.log(size, 1024))), len(unit_list) - 1)

            if unit_index == 0:
                return f"{size_bytes} {unit_list[0]}"

            converted_size = size / (1024**unit_index)
            formatted_size = self.format_number(
                converted_size, 1 if converted_size < 100 else 0
            )

            return f"{formatted_size} {unit_list[unit_index]}"

        except Exception:
            self.logerror(
                "Error formatting file size: %s".replace("%s", "{e}").replace(
                    "%d", "{e}"
                )
            )
            return f"{size_bytes} B"

    def get_text_direction(self) -> str:
        """Get text direction for current language.

        Returns:
            "ltr" for left-to-right, "rtl" for right-to-left
        """
        return self.preferences.text_direction

    def export_translations_for_translation(
        self, output_file: str, include_completed: bool = False
    ) -> bool:
        """Export translations in a format suitable for translators.

        Args:
            output_file: Output file path
            include_completed: Whether to include already translated strings

        Returns:
            True if export successful
        """
        try:
            export_data = {
                "metadata": {
                    "source_language": "en",
                    "export_date": "2024-01-01",
                    "total_strings": 0,
                    "categories": [cat.value for cat in TranslationCategory],
                },
                "translations": {},
            }

            # Collect all translatable strings
            all_strings = self._collect_translatable_strings()

            for category, strings in all_strings.items():
                export_data["translations"][category] = {}

                for key, translation_data in strings.items():
                    # Include string if not completed or if include_completed
                    # is True
                    if include_completed or not translation_data.get(
                        "completed", False
                    ):
                        export_data["translations"][category][key] = {
                            "original": translation_data["default_text"],
                            "context": translation_data.get("context", ""),
                            "description": translation_data.get("description", ""),
                            "translation": translation_data.get("translation", ""),
                            "completed": translation_data.get("completed", False),
                        }

            export_data["metadata"]["total_strings"] = sum(
                len(strings) for strings in export_data["translations"].values()
            )

            # Write to file
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            self.loginfo(
                "Translations exported to %s".replace("%s", "{output_file}").replace(
                    "%d", "{output_file}"
                )
            )
            return True

        except Exception:
            self.logerror(
                "Error exporting translations: %s".replace("%s", "{e}").replace(
                    "%d", "{e}"
                )
            )
            return False

    def import_completed_translations(
        self, input_file: str, target_language: SupportedLanguage
    ) -> bool:
        """Import completed translations from file.

        Args:
            input_file: Input file path
            target_language: Target language for translations

        Returns:
            True if import successful
        """
        try:
            with open(input_file, encoding="utf-8") as f:
                import_data = json.load(f)

            imported_count = 0

            # Process translations by category
            for category, translations in import_data.get("translations", {}).items():
                for key, translation_data in translations.items():
                    if translation_data.get(
                        "completed", False
                    ) and translation_data.get("translation"):
                        # Store translation
                        self._store_translation(
                            target_language,
                            category,
                            key,
                            translation_data["translation"],
                        )
                        imported_count += 1

            # Update translation files
            self._update_translation_files(target_language)

            self.logger.info(
                "Imported %d translations for %s",
                imported_count,
                target_language.english_name,
            )
            return True

        except Exception:
            self.logerror(
                "Error importing translations: %s".replace("%s", "{e}").replace(
                    "%d", "{e}"
                )
            )
            return False

    def validate_translation_coverage(
        self, language: SupportedLanguage
    ) -> dict[str, Any]:
        """Validate translation coverage for a language.

        Args:
            language: Language to validate

        Returns:
            Validation report
        """
        try:
            all_strings = self._collect_translatable_strings()
            language_translations = self._load_language_translations(language)

            report = {
                "language": language.english_name,
                "total_strings": 0,
                "translated_strings": 0,
                "missing_translations": [],
                "categories": {},
            }

            for category, strings in all_strings.items():
                category_stats = {"total": len(strings), "translated": 0, "missing": []}

                for key in strings.keys():
                    full_key = f"{category}.{key}"
                    report["total_strings"] += 1

                    if full_key in language_translations:
                        category_stats["translated"] += 1
                        report["translated_strings"] += 1
                    else:
                        category_stats["missing"].append(key)
                        report["missing_translations"].append(full_key)

                report["categories"][category] = category_stats

            report["coverage_percentage"] = (
                (report["translated_strings"] / report["total_strings"]) * 100
                if report["total_strings"] > 0
                else 0
            )

            return report

        except Exception:
            self.logerror(
                "Error validating translation coverage: %s".replace(
                    "%s", "{e}"
                ).replace("%d", "{e}")
            )
            return {}

    # Private methods

    def _create_initial_po_file(self, po_file: Path, language: SupportedLanguage):
        """Create initial PO file with headers."""
        try:
            po_content = f"""# S&D Antivirus Translation File
# Language: {language.english_name} ({language.code})
#
msgid ""
msgstr ""
"Project-Id-Version: S&D Antivirus 1.0\\n"
"Report-Msgid-Bugs-To: support@xanados.com\\n"
"POT-Creation-Date: 2024-01-01 00:00+0000\\n"
"PO-Revision-Date: 2024-01-01 00:00+0000\\n"
"Last-Translator: Translator Name <translator@example.com>\\n"
"Language-Team: {language.english_name} <{language.code}@example.com>\\n"
"Language: {language.code}\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
"Plural-Forms: nplurals=2; plural=(n != 1);\\n"

# Initial translation entries will be added here
"""

            with open(po_file, "w", encoding="utf-8") as f:
                f.write(po_content)

        except Exception:
            self.logerror(
                "Error creating PO file: %s".replace("%s", "{e}").replace("%d", "{e}")
            )

    def _load_translations(self, language: SupportedLanguage) -> bool:
        """Load translations for specified language."""
        try:
            # Clear cache
            cache_key = language.code
            if cache_key in self.translations_cache:
                del self.translations_cache[cache_key]

            # Load from MO files using gettext
            mo_file = self.languages_dir / language.code / "LC_MESSAGES" / "s_and_d.mo"

            if mo_file.exists():
                translation = gettext.translation(
                    "s_and_d",
                    localedir=str(self.languages_dir),
                    languages=[language.code],
                    fallback=True,
                )

                self.translations_cache[cache_key] = translation

                # Also install globally for gettext functions
                translation.install()

                return True
            else:
                # Create fallback translation
                self.translations_cache[cache_key] = gettext.NullTranslations()
                return False

        except Exception:
            self.logerror(
                "Error loading translations for %s: %s".replace(
                    "%s", "{language.code, e}"
                ).replace("%d", "{language.code, e}")
            )
            return False

    def _update_qt_translators(self, language: SupportedLanguage):
        """Update Qt translation objects."""
        try:
            app = QApplication.instance()
            if not app:
                return

            # Remove old translators
            if self.qt_translator:
                app.removeTranslator(self.qt_translator)
            if self.app_translator:
                app.removeTranslator(self.app_translator)

            # Create new translators
            self.qt_translator = QTranslator()
            self.app_translator = QTranslator()

            # Load Qt translations
            qt_translation_file = f"qt_{language.code}"
            if self.qt_translator.load(qt_translation_file, str(self.languages_dir)):
                app.installTranslator(self.qt_translator)

            # Load application translations
            app_translation_file = f"s_and_d_{language.code}"
            if self.app_translator.load(app_translation_file, str(self.languages_dir)):
                app.installTranslator(self.app_translator)

        except Exception:
            self.logerror(
                "Error updating Qt translators: %s".replace("%s", "{e}").replace(
                    "%d", "{e}"
                )
            )

    def _notify_language_change(
        self, old_language: SupportedLanguage, new_language: SupportedLanguage
    ):
        """Notify components about language change."""
        try:
            # Emit Qt language change event
            app = QApplication.instance()
            if app:
                QCoreApplication.postEvent(app, QCoreApplication.LanguageChange)

            # Could emit custom signals here for application components
            self.logger.info(
                "Language changed from %s to %s",
                old_language.english_name,
                new_language.english_name,
            )

        except Exception:
            self.logerror(
                "Error notifying language change: %s".replace("%s", "{e}").replace(
                    "%d", "{e}"
                )
            )

    def _get_translation(self, key: str, default: str) -> str:
        """Get translation from cache."""
        try:
            cache_key = self.current_language.code

            if cache_key in self.translations_cache:
                translation_obj = self.translations_cache[cache_key]
                return translation_obj.gettext(key) or default

            return default

        except Exception:
            return default

    def _get_plural_translation(self, key: str, count: int) -> str:
        """Get plural translation from cache."""
        try:
            cache_key = self.current_language.code

            if cache_key in self.translations_cache:
                translation_obj = self.translations_cache[cache_key]
                return translation_obj.ngettext(key, f"{key}_plural", count)

            return f"{key} ({count})"

        except Exception:
            return f"{key} ({count})"

    def _format_string(self, template: str, **kwargs) -> str:
        """Format string with variables."""
        try:
            # Support both Python format and gettext style variables
            if "{" in template and "}" in template:
                # Python style: {variable}
                return template.format(**kwargs)
            elif "%(" in template and ")" in template:
                # Gettext style: %(variable)s
                return template % kwargs
            else:
                return template

        except Exception:
            self.logwarning(
                "Error formatting string '%s': %s".replace(
                    "%s", "{template, e}"
                ).replace("%d", "{template, e}")
            )
            return template

    def _collect_translatable_strings(self) -> dict[str, dict[str, Any]]:
        """Collect all translatable strings from the application."""
        # This would scan the source code for translatable strings
        # For now, return a sample set
        return {
            "ui_general": {
                "app_name": {
                    "default_text": "S&D Antivirus",
                    "context": "Application name",
                    "description": "Main application title",
                },
                "scan": {
                    "default_text": "Scan",
                    "context": "Button/action",
                    "description": "Start scanning operation",
                },
                "settings": {
                    "default_text": "Settings",
                    "context": "Menu item",
                    "description": "Application settings",
                },
            },
            "scan_operations": {
                "scan_complete": {
                    "default_text": "Scan completed",
                    "context": "Status message",
                    "description": "Displayed when scan finishes",
                },
                "files_scanned": {
                    "default_text": "{count} files scanned",
                    "context": "Statistics",
                    "description": "Number of files processed",
                },
            },
            "threat_detection": {
                "threat_found": {
                    "default_text": "Threat detected",
                    "context": "Alert message",
                    "description": "Threat detection alert",
                },
                "malware": {
                    "default_text": "Malware",
                    "context": "Threat type",
                    "description": "Malicious software",
                },
            },
        }

    def _load_language_translations(
        self, language: SupportedLanguage
    ) -> dict[str, str]:
        """Load existing translations for a language."""
        # This would load from PO/MO files
        # For now, return empty dict
        return {}

    def _store_translation(
        self, language: SupportedLanguage, category: str, key: str, translation: str
    ):
        """Store translation in database/file."""
        # This would store in the appropriate translation file
        pass

    def _update_translation_files(self, language: SupportedLanguage):
        """Update PO/MO files with new translations."""
        # This would update the gettext files
        pass


# Translation helper functions for use throughout the application

_translation_system = None


def initialize_translations(languages_dir: str = "locales") -> MultiLanguageSupport:
    """Initialize the global translation system."""
    global _translation_system
    _translation_system = MultiLanguageSupport(languages_dir)
    return _translation_system


def get_translation_system() -> MultiLanguageSupport | None:
    """Get the global translation system."""
    return _translation_system


def _(
    text: str, category: TranslationCategory = TranslationCategory.UI_GENERAL, **kwargs
) -> str:
    """Quick translation function.

    Args:
        text: Text to translate
        category: Translation category
        **kwargs: Variables for formatting

    Returns:
        Translated text
    """
    if _translation_system:
        return _translation_system.translate(text, category, text, **kwargs)
    return text


def ngettext(
    singular: str,
    plural: str,
    count: int,
    category: TranslationCategory = TranslationCategory.UI_GENERAL,
    **kwargs,
) -> str:
    """Plural translation function.

    Args:
        singular: Singular form
        plural: Plural form
        count: Number for plural selection
        category: Translation category
        **kwargs: Variables for formatting

    Returns:
        Translated text with correct plural form
    """
    if _translation_system:
        return _translation_system.translate_plural(singular, count, category, **kwargs)
    return singular if count == 1 else plural


def format_file_size(size_bytes: int) -> str:
    """Format file size according to current locale."""
    if _translation_system:
        return _translation_system.format_file_size(size_bytes)
    return f"{size_bytes} B"


def format_date(date_obj, format_type: str = "default") -> str:
    """Format date according to current locale."""
    if _translation_system:
        return _translation_system.format_date(date_obj, format_type)
    return str(date_obj)


def format_number(number: float, decimal_places: int = 2) -> str:
    """Format number according to current locale."""
    if _translation_system:
        return _translation_system.format_number(number, decimal_places)
    return f"{number:.{decimal_places}f}"


# Sample translation data for demonstration
SAMPLE_TRANSLATIONS = {
    SupportedLanguage.SPANISH: {
        "ui_general.app_name": "S&D Antivirus",
        "ui_general.scan": "Escanear",
        "ui_general.settings": "Configuración",
        "ui_general.exit": "Salir",
        "ui_general.help": "Ayuda",
        "scan_operations.scan_complete": "Escaneo completado",
        "scan_operations.files_scanned": "{count} archivos escaneados",
        "threat_detection.threat_found": "Amenaza detectada",
        "threat_detection.malware": "Malware",
        "ui_buttons.start": "Iniciar",
        "ui_buttons.stop": "Detener",
        "ui_buttons.cancel": "Cancelar",
        "ui_buttons.ok": "Aceptar",
    },
    SupportedLanguage.FRENCH: {
        "ui_general.app_name": "S&D Antivirus",
        "ui_general.scan": "Scanner",
        "ui_general.settings": "Paramètres",
        "ui_general.exit": "Quitter",
        "ui_general.help": "Aide",
        "scan_operations.scan_complete": "Analyse terminée",
        "scan_operations.files_scanned": "{count} fichiers analysés",
        "threat_detection.threat_found": "Menace détectée",
        "threat_detection.malware": "Logiciel malveillant",
        "ui_buttons.start": "Démarrer",
        "ui_buttons.stop": "Arrêter",
        "ui_buttons.cancel": "Annuler",
        "ui_buttons.ok": "D'accord",
    },
    SupportedLanguage.GERMAN: {
        "ui_general.app_name": "S&D Antivirus",
        "ui_general.scan": "Scannen",
        "ui_general.settings": "Einstellungen",
        "ui_general.exit": "Beenden",
        "ui_general.help": "Hilfe",
        "scan_operations.scan_complete": "Scan abgeschlossen",
        "scan_operations.files_scanned": "{count} Dateien gescannt",
        "threat_detection.threat_found": "Bedrohung erkannt",
        "threat_detection.malware": "Malware",
        "ui_buttons.start": "Starten",
        "ui_buttons.stop": "Stoppen",
        "ui_buttons.cancel": "Abbrechen",
        "ui_buttons.ok": "OK",
    },
    SupportedLanguage.CHINESE_SIMPLIFIED: {
        "ui_general.app_name": "S&D 杀毒软件",
        "ui_general.scan": "扫描",
        "ui_general.settings": "设置",
        "ui_general.exit": "退出",
        "ui_general.help": "帮助",
        "scan_operations.scan_complete": "扫描完成",
        "scan_operations.files_scanned": "已扫描 {count} 个文件",
        "threat_detection.threat_found": "检测到威胁",
        "threat_detection.malware": "恶意软件",
        "ui_buttons.start": "开始",
        "ui_buttons.stop": "停止",
        "ui_buttons.cancel": "取消",
        "ui_buttons.ok": "确定",
    },
    SupportedLanguage.JAPANESE: {
        "ui_general.app_name": "S&D アンチウイルス",
        "ui_general.scan": "スキャン",
        "ui_general.settings": "設定",
        "ui_general.exit": "終了",
        "ui_general.help": "ヘルプ",
        "scan_operations.scan_complete": "スキャン完了",
        "scan_operations.files_scanned": "{count}個のファイルをスキャンしました",
        "threat_detection.threat_found": "脅威が検出されました",
        "threat_detection.malware": "マルウェア",
        "ui_buttons.start": "開始",
        "ui_buttons.stop": "停止",
        "ui_buttons.cancel": "キャンセル",
        "ui_buttons.ok": "OK",
    },
}


# Example usage functions
def create_sample_translation_files():
    """Create sample translation files for supported languages."""
    translation_system = get_translation_system()
    if not translation_system:
        return

    for language, translations in SAMPLE_TRANSLATIONS.items():
        # This would create actual PO/MO files
        # For now, just log the sample data
        translation_system.logger.info(
            "Sample translations for %s: %d entries",
            language.english_name,
            len(translations),
        )


def demonstrate_translations():
    """Demonstrate translation functionality."""
    system = initialize_translations()

    # Test different languages
    for language in [
        SupportedLanguage.ENGLISH,
        SupportedLanguage.SPANISH,
        SupportedLanguage.FRENCH,
        SupportedLanguage.GERMAN,
    ]:
        system.set_language(language)

        print(f"\n--- {language.english_name} ---")
        print(f"App Name: {_('app_name')}")
        print(f"Scan: {_('scan')}")
        print(f"Settings: {_('settings')}")
        print(
            f"Files scanned: {_('files_scanned', TranslationCategory.SCAN_OPERATIONS, count=150)}"
        )
        print(f"File size: {format_file_size(1024 * 1024 * 2.5)}")
        print(f"Number: {format_number(1234.56)}")


if __name__ == "__main__":
    # Demo the translation system
    demonstrate_translations()
