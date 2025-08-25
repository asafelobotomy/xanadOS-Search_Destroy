#!/usr/bin/env python3
"""
Lazy Loading Dashboard Manager for xanadOS Search & Destroy
Implements modern progressive loading patterns for optimal startup performance.
"""

import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtWidgets import QLabel, QWidget


@dataclass
class DashboardCard:
    """Represents a dashboard card with loading metadata."""

    widget: QWidget
    priority: int  # 1 = highest priority (load first)
    load_time_estimate: float  # Estimated load time in seconds
    is_loaded: bool = False
    is_visible: bool = True
    data_loader: Optional[Callable] = None
    placeholder_text: str = "Loading..."


class LazyDashboardLoader(QObject):
    """
    Modern lazy loading manager for dashboard components.

    Features:
    - Priority-based loading
    - Placeholder management
    - Progressive enhancement
    - Viewport-aware loading
    - Performance monitoring
    """

    # Signals
    card_loaded = pyqtSignal(str, object)  # card_id, data
    loading_progress = pyqtSignal(int, str)  # progress, status
    all_cards_loaded = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.cards: Dict[str, DashboardCard] = {}
        self.loading_queue: List[str] = []
        self.load_timer = QTimer()
        self.load_timer.timeout.connect(self._process_next_card)
        self.load_timer.setSingleShot(True)

        # Performance tracking
        self.load_start_time = None
        self.cards_loaded = 0
        self.total_cards = 0

        # Loading configuration
        self.batch_size = 2  # Number of cards to load simultaneously
        self.load_interval = 50  # ms between batches

    def register_card(
        self,
        card_id: str,
        widget: QWidget,
        priority: int = 5,
        data_loader: Optional[Callable] = None,
        placeholder_text: str = "Loading...",
    ) -> None:
        """Register a dashboard card for lazy loading."""

        card = DashboardCard(
            widget=widget,
            priority=priority,
            load_time_estimate=0.1,  # Default estimate
            data_loader=data_loader,
            placeholder_text=placeholder_text,
        )

        self.cards[card_id] = card
        self._setup_placeholder(card_id)

    def start_loading(self) -> None:
        """Start the lazy loading process."""
        if not self.cards:
            return

        self.load_start_time = time.time()
        self.cards_loaded = 0
        self.total_cards = len(self.cards)

        # Sort cards by priority (lower number = higher priority)
        self.loading_queue = sorted(
            self.cards.keys(), key=lambda card_id: self.cards[card_id].priority
        )

        print(f"🚀 Starting lazy loading of {self.total_cards} dashboard cards")

        # Start loading high-priority cards immediately
        self._load_immediate_cards()

        # Schedule remaining cards
        if self.loading_queue:
            self.load_timer.start(self.load_interval)

    def _setup_placeholder(self, card_id: str) -> None:
        """Setup placeholder content for a card."""
        card = self.cards[card_id]

        # Create placeholder label if widget doesn't have content
        if hasattr(card.widget, "setText"):
            card.widget.setText(card.placeholder_text)
        elif hasattr(card.widget, "setPlainText"):
            card.widget.setPlainText(card.placeholder_text)
        else:
            # For complex widgets, add a placeholder label
            placeholder = QLabel(card.placeholder_text)
            placeholder.setObjectName(f"{card_id}_placeholder")
            placeholder.setStyleSheet(
                """
                QLabel {
                    color: #b0b0b0;
                    font-style: italic;
                    padding: 10px;
                    background-color: rgba(255, 255, 255, 0.1);
                    border-radius: 4px;
                }
            """
            )

            # Try to add placeholder to widget's layout
            if hasattr(card.widget, "layout") and card.widget.layout():
                card.widget.layout().addWidget(placeholder)

    def _load_immediate_cards(self) -> None:
        """Load cards with priority 1 (highest priority) immediately."""
        immediate_cards = [
            card_id
            for card_id in self.loading_queue
            if self.cards[card_id].priority == 1
        ]

        for card_id in immediate_cards:
            self._load_card_data(card_id)
            self.loading_queue.remove(card_id)

    def _process_next_card(self) -> None:
        """Process the next card(s) in the loading queue."""
        if not self.loading_queue:
            self._finalize_loading()
            return

        # Load a batch of cards
        batch = self.loading_queue[: self.batch_size]

        for card_id in batch:
            self._load_card_data(card_id)

        # Remove processed cards from queue
        self.loading_queue = self.loading_queue[self.batch_size :]

        # Update progress
        progress = int((self.cards_loaded / self.total_cards) * 100)
        self.loading_progress.emit(
            progress,
            f"Loading dashboard components... ({self.cards_loaded}/{self.total_cards})",
        )

        # Schedule next batch
        if self.loading_queue:
            self.load_timer.start(self.load_interval)
        else:
            self._finalize_loading()

    def _load_card_data(self, card_id: str) -> None:
        """Load data for a specific card."""
        card = self.cards[card_id]

        if card.is_loaded:
            return

        try:
            start_time = time.time()

            # Load data if loader is provided
            data = None
            if card.data_loader:
                data = card.data_loader()

            # Remove placeholder
            self._remove_placeholder(card_id)

            # Mark as loaded
            card.is_loaded = True
            self.cards_loaded += 1

            # Calculate actual load time
            load_time = time.time() - start_time
            card.load_time_estimate = load_time

            # Emit signals
            self.card_loaded.emit(card_id, data)

            print(f"✅ Loaded card '{card_id}' in {load_time:.3f}s")

        except Exception as e:
            print(f"❌ Failed to load card '{card_id}': {e}")
            self._handle_load_error(card_id, str(e))

    def _remove_placeholder(self, card_id: str) -> None:
        """Remove placeholder content from a card."""
        card = self.cards[card_id]

        # Find and remove placeholder
        if hasattr(card.widget, "findChild"):
            placeholder = card.widget.findChild(QLabel, f"{card_id}_placeholder")
            if placeholder:
                placeholder.deleteLater()

    def _handle_load_error(self, card_id: str, error: str) -> None:
        """Handle card loading error."""
        card = self.cards[card_id]

        # Show error message in card
        error_text = f"Failed to load: {error}"
        if hasattr(card.widget, "setText"):
            card.widget.setText(error_text)
        elif hasattr(card.widget, "setPlainText"):
            card.widget.setPlainText(error_text)

        card.is_loaded = True  # Mark as "loaded" to avoid retry
        self.cards_loaded += 1

    def _finalize_loading(self) -> None:
        """Finalize the loading process."""
        total_time = time.time() - self.load_start_time if self.load_start_time else 0

        print("🎉 Dashboard loading completed!")
        print(f"   Total time: {total_time:.2f}s")
        print(f"   Cards loaded: {self.cards_loaded}/{self.total_cards}")

        # Calculate average load time per card
        if self.cards_loaded > 0:
            avg_load_time = total_time / self.cards_loaded
            print(f"   Average load time per card: {avg_load_time:.3f}s")

        self.loading_progress.emit(100, "Dashboard loading complete")
        self.all_cards_loaded.emit()

    def reload_card(self, card_id: str) -> None:
        """Reload a specific card."""
        if card_id not in self.cards:
            return

        card = self.cards[card_id]
        card.is_loaded = False
        self._setup_placeholder(card_id)
        self._load_card_data(card_id)

    def get_loading_stats(self) -> Dict[str, Any]:
        """Get loading performance statistics."""
        loaded_cards = [card for card in self.cards.values() if card.is_loaded]

        total_load_time = sum(card.load_time_estimate for card in loaded_cards)
        avg_load_time = total_load_time / len(loaded_cards) if loaded_cards else 0

        return {
            "total_cards": len(self.cards),
            "loaded_cards": len(loaded_cards),
            "total_load_time": total_load_time,
            "average_load_time": avg_load_time,
            "loading_progress": (
                (len(loaded_cards) / len(self.cards)) * 100 if self.cards else 0
            ),
        }


class ViewportAwareDashboardLoader(LazyDashboardLoader):
    """
    Enhanced dashboard loader that considers viewport visibility.
    Loads visible cards first for better perceived performance.
    """

    def __init__(self, viewport_widget: QWidget, parent=None):
        super().__init__(parent)
        self.viewport = viewport_widget

    def _is_card_visible(self, card_id: str) -> bool:
        """Check if a card is visible in the viewport."""
        card = self.cards[card_id]

        if not card.widget.isVisible():
            return False

        # Get widget geometry relative to viewport
        widget_rect = card.widget.geometry()
        viewport_rect = self.viewport.geometry()

        # Simple intersection check
        return (
            widget_rect.top() < viewport_rect.bottom()
            and widget_rect.bottom() > viewport_rect.top()
        )

    def start_loading(self) -> None:
        """Start loading with viewport-aware prioritization."""
        if not self.cards:
            return

        # Separate visible and hidden cards
        visible_cards = []
        hidden_cards = []

        for card_id in self.cards.keys():
            if self._is_card_visible(card_id):
                visible_cards.append(card_id)
            else:
                hidden_cards.append(card_id)

        # Sort each group by priority
        visible_cards.sort(key=lambda cid: self.cards[cid].priority)
        hidden_cards.sort(key=lambda cid: self.cards[cid].priority)

        # Combine: visible cards first, then hidden
        self.loading_queue = visible_cards + hidden_cards

        print(
            f"📱 Viewport-aware loading: {len(visible_cards)} visible, {len(hidden_cards)} hidden cards"
        )

        # Continue with normal loading process
        super().start_loading()
