"""User Manual Window - Display the comprehensive user manual in a scrollable dialog."""

from pathlib import Path

try:
    import markdown  # optional
except Exception:  # pragma: no cover - optional dependency
    markdown = None
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSplitter,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
)

# Import centralized version
from app import __version__

from .theme_manager import get_theme_manager
from .themed_widgets import ThemedDialog


class UserManualWindow(ThemedDialog):
    """A comprehensive user manual window with table of contents navigation."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("S&D - User Manual")
        # Match main application window size for consistency
        self.setMinimumSize(1000, 750)
        self.resize(1200, 850)  # Same as main application window
        self.setModal(
            False
        )  # Allow user to interact with main window while manual is open

        # Load the user manual content
        self.manual_content = self._load_manual_content()
        self.manual_sections = self._parse_manual_sections()

        self._setup_ui()

        # Apply theme and connect to theme changes
        self._apply_theme()

        # Connect to theme manager for automatic theme updates
        try:
            theme_manager = get_theme_manager()
            theme_manager.theme_changed.connect(self._on_theme_changed)
        except Exception as e:
            print(f"Warning: Could not connect to theme manager: {e}")

    def _on_theme_changed(self, theme_name):
        """Handle theme changes by reapplying theme and updating content."""
        self._apply_theme()
        # Update the HTML content with new theme colors
        self.content_area.setHtml(self._convert_markdown_to_html(self.manual_content))

    def _setup_ui(self):
        """Set up the user interface."""
        # Main layout with minimal margins to maximize content space
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(
            8, 8, 8, 8
        )  # Reduced margins for more content space
        main_layout.setSpacing(5)  # Minimal spacing between header, content, and footer
        main_layout.setContentsMargins(
            5, 5, 5, 5
        )  # Reduce margins to maximize content space
        main_layout.setSpacing(5)  # Reduce spacing between elements

        # Header with minimal height
        header_frame = QFrame()
        header_frame.setMaximumHeight(45)  # Reduced height to save vertical space
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(10, 5, 10, 5)  # Minimal margins
        header_layout.setContentsMargins(10, 8, 10, 8)

        title_label = QLabel("📚 S&D - Search & Destroy User Manual")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; padding: 5px;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Close button
        close_btn = QPushButton("✕ Close")
        close_btn.setObjectName("closeButton")
        close_btn.clicked.connect(self.close)
        close_btn.setMaximumWidth(100)
        header_layout.addWidget(close_btn)

        main_layout.addWidget(header_frame)

        # Create splitter layout with optimized proportions
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(
            False
        )  # Prevent sections from collapsing completely
        self.splitter.setHandleWidth(6)  # Make the handle easier to grab

        # Table of contents with adjustable width
        self.toc_tree = QTreeWidget()
        self.toc_tree.setHeaderLabel("Contents")
        self.toc_tree.setMinimumWidth(150)  # Minimum size to keep it functional
        self.toc_tree.setMaximumWidth(
            400
        )  # Maximum to prevent it from taking too much space
        self.toc_tree.itemClicked.connect(self.on_toc_item_clicked)

        # Content area with maximum space allocation
        self.content_area = QTextEdit()
        self.content_area.setReadOnly(True)
        self.content_area.setMinimumWidth(
            300
        )  # Ensure content area has reasonable minimum

        self.splitter.addWidget(self.toc_tree)
        self.splitter.addWidget(self.content_area)

        # Set initial proportions to match optimal viewing experience
        # Based on user feedback: ~280px TOC, ~920px content for 1200px window
        self.splitter.setSizes([280, 920])

        # Configure stretch factors for responsive resizing
        self.splitter.setStretchFactor(0, 0)  # TOC doesn't auto-stretch
        self.splitter.setStretchFactor(
            1, 1
        )  # Content area gets extra space when window resizes

        main_layout.addWidget(self.splitter)

        # Footer with version info
        footer_frame = QFrame()
        footer_frame.setMaximumHeight(30)  # Compact footer
        footer_layout = QHBoxLayout(footer_frame)
        footer_layout.setContentsMargins(10, 2, 10, 2)

        version_label = QLabel(
            f"User Manual v{__version__} - Last Updated: August 22, 2025"
        )
        version_label.setStyleSheet("color: gray; font-size: 9px;")
        footer_layout.addWidget(version_label)

        footer_layout.addStretch()

        help_label = QLabel(
            "💡 Navigate using the table of contents or scroll through the full manual"
        )
        help_label.setStyleSheet("color: gray; font-size: 9px;")
        footer_layout.addWidget(help_label)

        main_layout.addWidget(footer_frame)

        # Populate the table of contents and content area
        self._populate_table_of_contents()
        self.content_area.setHtml(self._convert_markdown_to_html(self.manual_content))

    def _load_manual_content(self):
        """Load the user manual content from the markdown file."""
        try:
            # Get the manual file path relative to the app directory
            manual_path = (
                Path(__file__).parent.parent.parent / "docs" / "user" / "User_Manual.md"
            )

            if manual_path.exists():
                with open(manual_path, encoding="utf-8") as f:
                    return f.read()
            else:
                return self._get_fallback_content()

        except Exception as e:
            print(f"Error loading user manual: {e}")
            return self._get_fallback_content()

    def _get_fallback_content(self):
        """Provide fallback content if the manual file cannot be loaded."""
        return """
# S&D - Search & Destroy User Manual

## Welcome to S&D - Search & Destroy

Thank you for using S&D (Search & Destroy), your comprehensive security solution for Linux systems.

## 🚀 Getting Started

### First Launch
1. Launch S&D from your applications menu or run `./run.sh` from the terminal
2. The application automatically prevents multiple instances from running
3. Familiarize yourself with the modern tabbed interface
4. Ensure virus definitions are up-to-date

### Main Interface Overview
The S&D interface features a modern, professional design with six main tabs:
- **🏠 Dashboard Tab**: System overview and status indicators
- **🔍 Scan Tab**: Configure and execute security scans
- **🛡️ Protection Tab**: Real-time monitoring settings
- **📊 Reports Tab**: Detailed scan results and analysis
- **🗃️ Quarantine Tab**: Manage isolated threats
- **⚙️ Settings Tab**: Application configuration

## 🔍 Scanning for Threats

### Available Scan Types
- **Quick Scan**: Fast threat detection in user areas
- **Full System Scan**: Comprehensive system-wide analysis
- **Custom Directory Scan**: Targeted scanning of specific locations
- **RKHunter Scan**: Advanced rootkit detection

## 🛡️ Real-time Protection

Enable comprehensive real-time monitoring to protect your system from threats as they appear.

## 📊 Reports and Analysis

View detailed scan reports and export them in multiple formats including PDF, JSON, CSV, and XML.

## ⚙️ Configuration

Customize S&D to meet your specific security needs through the comprehensive settings interface.

---

*For the complete user manual, please ensure the User_Manual.md file is available in the docs/user/ directory.*
"""

    def _parse_manual_sections(self):
        """Parse the manual content to extract sections for the table of contents."""
        sections = []
        lines = self.manual_content.split("\n")

        for i, line in enumerate(lines):
            if line.startswith("#"):
                level = len(line) - len(line.lstrip("#"))
                title = line.lstrip("#").strip()
                sections.append({"level": level, "title": title, "line": i})

        return sections

    def _populate_table_of_contents(self):
        """Populate the table of contents tree widget."""
        self.toc_tree.clear()

        # Stack to keep track of parent items for nested sections
        parent_stack = []

        for section in self.manual_sections:
            level = section["level"]
            title = section["title"]

            # Create tree item
            item = QTreeWidgetItem()

            # Add appropriate emoji based on section content
            if any(
                keyword in title.lower() for keyword in ["getting started", "start"]
            ):
                item.setText(0, f"🚀 {title}")
            elif any(keyword in title.lower() for keyword in ["scan", "threat"]):
                item.setText(0, f"🔍 {title}")
            elif any(
                keyword in title.lower() for keyword in ["protection", "security"]
            ):
                item.setText(0, f"🛡️ {title}")
            elif any(keyword in title.lower() for keyword in ["report", "analysis"]):
                item.setText(0, f"📊 {title}")
            elif any(keyword in title.lower() for keyword in ["config", "setting"]):
                item.setText(0, f"⚙️ {title}")
            elif any(keyword in title.lower() for keyword in ["troubleshoot", "help"]):
                item.setText(0, f"🔧 {title}")
            elif any(keyword in title.lower() for keyword in ["best practice", "tip"]):
                item.setText(0, f"💡 {title}")
            else:
                item.setText(0, title)

            # Store section info for navigation
            item.setData(0, Qt.ItemDataRole.UserRole, section)

            # Determine parent based on level
            if level == 1:
                # Top level
                self.toc_tree.addTopLevelItem(item)
                parent_stack = [item]
            elif level > 1 and parent_stack:
                # Find appropriate parent
                while len(parent_stack) >= level:
                    parent_stack.pop()

                if parent_stack:
                    parent_stack[-1].addChild(item)
                else:
                    self.toc_tree.addTopLevelItem(item)

                parent_stack.append(item)

        # Expand all items
        self.toc_tree.expandAll()

    def _navigate_to_section(self, item):
        """Navigate to the selected section in the content display."""
        section_data = item.data(0, Qt.ItemDataRole.UserRole)
        if section_data:
            # Find the section title in the HTML content and scroll to it
            section_title = section_data["title"]

            # Move cursor to the beginning
            cursor = self.content_area.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            self.content_area.setTextCursor(cursor)

            # Search for the section title
            if self.content_area.find(section_title):
                # Scroll to make the found text visible
                self.content_area.ensureCursorVisible()

    def on_toc_item_clicked(self, item, column):
        """Handle table of contents item clicks."""
        self._navigate_to_section(item)

    def _convert_markdown_to_html(self, markdown_content):
        """Convert markdown content to HTML for display."""
        try:
            # Use markdown library if available, otherwise naive fallback
            if markdown is not None:
                html = markdown.markdown(
                    markdown_content,
                    extensions=["tables", "toc", "codehilite"],
                    extension_configs={"codehilite": {"css_class": "highlight"}},
                )
            else:
                # Minimal fallback: escape and wrap line breaks
                import html as _html

                escaped = _html.escape(markdown_content)
                html = "<pre>" + escaped + "</pre>"

            # Get theme-appropriate colors for HTML styling
            if hasattr(self, "get_theme_color"):
                bg_color = self.get_theme_color("secondary_bg")
                text_color = self.get_theme_color("primary_text")
                accent_color = self.get_theme_color("accent")
                border_color = self.get_theme_color("border_light")
                code_bg = self.get_theme_color("tertiary_bg")
                table_header_bg = self.get_theme_color("card_bg")
                blockquote_border = accent_color
                secondary_text = self.get_theme_color("secondary_text")
            else:
                # Fallback colors for light theme
                bg_color = "#ffffff"
                text_color = "#333333"
                accent_color = "#2c3e50"
                border_color = "#ddd"
                code_bg = "#f8f9fa"
                table_header_bg = "#f2f2f2"
                blockquote_border = "#3498db"
                secondary_text = "#666666"

            # Add theme-aware styling
            styled_html = f"""
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: {text_color};
                    margin: 15px 25px;
                    background-color: {bg_color};
                    max-width: none;
                }}
                h1 {{
                    color: {accent_color};
                    border-bottom: 2px solid {accent_color};
                    padding-bottom: 10px;
                    margin-top: 25px;
                    margin-bottom: 20px;
                    font-size: 1.8em;
                }}
                h2 {{
                    color: {text_color};
                    border-bottom: 1px solid {border_color};
                    padding-bottom: 5px;
                    margin-top: 20px;
                    margin-bottom: 15px;
                    font-size: 1.4em;
                }}
                h3 {{
                    color: {text_color};
                    margin-top: 18px;
                    margin-bottom: 10px;
                    font-size: 1.2em;
                }}
                h4 {{
                    color: {secondary_text};
                    margin-top: 15px;
                    margin-bottom: 8px;
                    font-size: 1.1em;
                }}
                code {{
                    background-color: {code_bg};
                    color: {text_color};
                    padding: 2px 6px;
                    border-radius: 4px;
                    font-family: 'Consolas', 'Monaco', monospace;
                    border: 1px solid {border_color};
                    font-size: 0.9em;
                }}
                pre {{
                    background-color: {code_bg};
                    color: {text_color};
                    padding: 15px 20px;
                    border-radius: 6px;
                    overflow-x: auto;
                    border: 1px solid {border_color};
                    margin: 15px 0;
                    font-size: 0.9em;
                }}
                pre code {{
                    background: none;
                    border: none;
                    padding: 0;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    margin: 15px 0;
                    border: 1px solid {border_color};
                }}
                th, td {{
                    border: 1px solid {border_color};
                    padding: 12px;
                    text-align: left;
                }}
                th {{
                    background-color: {table_header_bg};
                    color: {text_color};
                    font-weight: bold;
                }}
                td {{
                    background-color: {bg_color};
                }}
                blockquote {{
                    border-left: 4px solid {blockquote_border};
                    margin: 15px 0;
                    padding: 15px 20px;
                    color: {secondary_text};
                    background-color: {code_bg};
                    border-radius: 0 6px 6px 0;
                }}
                ul, ol {{
                    margin: 12px 0;
                    padding-left: 30px;
                }}
                li {{
                    margin: 6px 0;
                    line-height: 1.5;
                }}
                p {{
                    margin: 12px 0;
                    line-height: 1.6;
                }}
                strong {{
                    color: {accent_color};
                    font-weight: bold;
                }}
                em {{
                    color: {secondary_text};
                    font-style: italic;
                }}
                hr {{
                    border: none;
                    border-top: 2px solid {border_color};
                    margin: 30px 0;
                }}
                a {{
                    color: {accent_color};
                    text-decoration: none;
                }}
                a:hover {{
                    text-decoration: underline;
                }}
            </style>
            {html}
            """

            return styled_html

        except ImportError:
            # Fallback to basic HTML conversion if markdown library is not available
            return self._basic_markdown_to_html(markdown_content)

    def _basic_markdown_to_html(self, markdown_content):
        """Basic markdown to HTML conversion without external dependencies."""
        html_lines = []
        lines = markdown_content.split("\n")
        in_code_block = False

        for line in lines:
            if line.startswith("```"):
                in_code_block = not in_code_block
                if in_code_block:
                    html_lines.append("<pre><code>")
                else:
                    html_lines.append("</code></pre>")
                continue

            if in_code_block:
                html_lines.append(line)
                continue

            # Headers
            if line.startswith("####"):
                html_lines.append(f"<h4>{line[4:].strip()}</h4>")
            elif line.startswith("###"):
                html_lines.append(f"<h3>{line[3:].strip()}</h3>")
            elif line.startswith("##"):
                html_lines.append(f"<h2>{line[2:].strip()}</h2>")
            elif line.startswith("#"):
                html_lines.append(f"<h1>{line[1:].strip()}</h1>")
            # Bold text
            elif "**" in line:
                line = line.replace("**", "<strong>", 1).replace("**", "</strong>", 1)
                html_lines.append(f"<p>{line}</p>")
            # Empty lines
            elif line.strip() == "":
                html_lines.append("<br>")
            # Regular paragraphs
            else:
                html_lines.append(f"<p>{line}</p>")

        return "\n".join(html_lines)

    def _apply_theme(self):
        """Apply the current theme to the dialog."""
        if hasattr(self, "get_theme_color"):
            # Apply theme colors using correct color keys from theme manager
            bg_color = self.get_theme_color("background")
            text_color = self.get_theme_color("primary_text")
            secondary_bg = self.get_theme_color("secondary_bg")
            border_color = self.get_theme_color("border")
            accent_color = self.get_theme_color("accent")
            hover_color = self.get_theme_color("accent_hover")

            self.setStyleSheet(
                f"""
                UserManualWindow {{
                    background-color: {bg_color};
                    color: {text_color};
                }}
                QTreeWidget {{
                    background-color: {secondary_bg};
                    color: {text_color};
                    border: 1px solid {border_color};
                    selection-background-color: {accent_color};
                    selection-color: white;
                    outline: none;
                }}
                QTreeWidget::item {{
                    padding: 4px;
                    border: none;
                }}
                QTreeWidget::item:hover {{
                    background-color: {hover_color};
                }}
                QTreeWidget::item:selected {{
                    background-color: {accent_color};
                    color: white;
                }}
                QTextEdit {{
                    background-color: {secondary_bg};
                    color: {text_color};
                    border: 1px solid {border_color};
                    selection-background-color: {accent_color};
                    selection-color: white;
                }}
                QPushButton#closeButton {{
                    background-color: {accent_color};
                    color: white;
                    border: 1px solid {border_color};
                    padding: 5px 10px;
                    border-radius: 3px;
                    font-weight: bold;
                }}
                QPushButton#closeButton:hover {{
                    background-color: {hover_color};
                }}
                QPushButton#closeButton:pressed {{
                    background-color: {self.get_theme_color("accent_pressed")};
                }}
                QFrame {{
                    background-color: {bg_color};
                    color: {text_color};
                }}
                QLabel {{
                    color: {text_color};
                }}
                QSplitter {{
                    background-color: {bg_color};
                }}
                QSplitter::handle {{
                    background-color: {border_color};
                    border: 1px solid {border_color};
                    border-radius: 2px;
                    margin: 2px;
                }}
                QSplitter::handle:hover {{
                    background-color: {self.get_theme_color("accent")};
                    border: 1px solid {self.get_theme_color("accent")};
                }}
                QSplitter::handle:pressed {{
                    background-color: {self.get_theme_color("accent_pressed")};
                }}
            """
            )
