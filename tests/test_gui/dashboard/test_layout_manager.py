#!/usr/bin/env python3
"""
Tests for Customizable Dashboard Layout Manager - Task 2.1.3

Tests cover:
- Widget configuration dataclasses
- Layout configuration and persistence
- JSON save/load functionality
"""

import json
import pytest
from pathlib import Path
from datetime import datetime

from app.gui.dashboard.layout_manager import (
    WidgetConfig,
    LayoutConfig,
    LAYOUTS_DIR,
)


# ==============================================================================
# Test Dataclasses (Can run without GUI)
# ==============================================================================

def test_widget_config_creation():
    """Test WidgetConfig dataclass creation and serialization."""
    config = WidgetConfig(
        widget_id="threat_viz",
        title="Threat Visualization",
        area="left",
        visible=True,
        floating=False,
        geometry={"x": 100, "y": 200, "width": 400, "height": 300},
    )
    
    assert config.widget_id == "threat_viz"
    assert config.title == "Threat Visualization"
    assert config.area == "left"
    assert config.visible is True
    assert config.floating is False
    assert config.geometry["width"] == 400
    
    # Test to_dict
    data = config.to_dict()
    assert data["widget_id"] == "threat_viz"
    assert data["geometry"]["x"] == 100
    
    # Test from_dict
    restored = WidgetConfig.from_dict(data)
    assert restored.widget_id == config.widget_id
    assert restored.geometry == config.geometry


def test_layout_config_creation():
    """Test LayoutConfig dataclass creation and widget management."""
    widget1 = WidgetConfig(widget_id="widget1", title="Widget 1", area="left")
    widget2 = WidgetConfig(widget_id="widget2", title="Widget 2", area="right")
    
    layout = LayoutConfig(
        name="Test Layout",
        description="A test layout configuration",
        widgets=[widget1, widget2],
        window_state={"geometry": {"x": 0, "y": 0, "width": 1200, "height": 800}},
    )
    
    assert layout.name == "Test Layout"
    assert len(layout.widgets) == 2
    assert layout.widgets[0].widget_id == "widget1"
    assert layout.window_state["geometry"]["width"] == 1200
    
    # Test to_dict
    data = layout.to_dict()
    assert data["name"] == "Test Layout"
    assert len(data["widgets"]) == 2
    assert data["widgets"][0]["widget_id"] == "widget1"
    
    # Test from_dict
    restored = LayoutConfig.from_dict(data)
    assert restored.name == layout.name
    assert len(restored.widgets) == 2
    assert restored.widgets[1].title == "Widget 2"


def test_layout_config_save_and_load(tmp_path):
    """Test LayoutConfig save/load to JSON file."""
    widget_config = WidgetConfig(
        widget_id="test_widget",
        title="Test Widget",
        area="bottom",
        visible=True,
    )
    
    layout = LayoutConfig(
        name="Saved Layout",
        description="Test save/load",
        widgets=[widget_config],
        window_state={"state": "test_state_data"},
    )
    
    # Save to file
    save_path = tmp_path / "test_layout.json"
    layout.save(save_path)
    
    assert save_path.exists()
    
    # Verify JSON structure
    with open(save_path) as f:
        data = json.load(f)
    
    assert data["name"] == "Saved Layout"
    assert data["description"] == "Test save/load"
    assert len(data["widgets"]) == 1
    assert data["widgets"][0]["widget_id"] == "test_widget"
    
    # Load from file
    loaded = LayoutConfig.load(save_path)
    assert loaded.name == "Saved Layout"
    assert len(loaded.widgets) == 1
    assert loaded.widgets[0].widget_id == "test_widget"
    assert loaded.widgets[0].area == "bottom"


def test_layout_config_modified_timestamp(tmp_path):
    """Test that modified_at timestamp updates on save."""
    layout = LayoutConfig(name="Timestamp Test")
    
    original_modified = layout.modified_at
    
    # Wait a moment and save
    import time
    time.sleep(0.1)
    
    save_path = tmp_path / "timestamp_test.json"
    layout.save(save_path)
    
    # Modified timestamp should be updated
    assert layout.modified_at != original_modified


def test_widget_config_defaults():
    """Test WidgetConfig default values."""
    config = WidgetConfig(widget_id="test", title="Test")
    
    assert config.area == "left"
    assert config.visible is True
    assert config.floating is False
    assert config.geometry == {}
    assert config.features == 7


def test_layout_config_empty_widgets():
    """Test LayoutConfig with no widgets."""
    layout = LayoutConfig(name="Empty Layout")
    
    assert len(layout.widgets) == 0
    assert layout.name == "Empty Layout"
    
    # Test save/load
    data = layout.to_dict()
    restored = LayoutConfig.from_dict(data)
    assert len(restored.widgets) == 0


def test_import_without_pyqt6():
    """Test that importing dataclasses works without PyQt6."""
    from app.gui.dashboard.layout_manager import (
        WidgetConfig,
        LayoutConfig,
    )
    
    # Dataclasses should work without PyQt6
    config = WidgetConfig(widget_id="test", title="Test", area="left")
    assert config.widget_id == "test"
