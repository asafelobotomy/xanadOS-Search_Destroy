#!/usr/bin/env python3
"""
Main Window Firewall Status Integration Patch
==============================================

Integrates the optimized firewall status monitoring system into the main window
for faster, event-driven status updates with minimal performance impact.

This patch modifies the existing timer-based system to use event-driven updates
while maintaining compatibility with the existing codebase.
"""

import logging
from typing import Any

from app.core.firewall_status_optimizer import FirewallStatusIntegration


class MainWindowFirewallPatch:
    """Integration patch for main window firewall status optimization."""

    def __init__(self, main_window):
        self.main_window = main_window
        self.logger = logging.getLogger(__name__)
        self.firewall_integration: FirewallStatusIntegration | None = None

        # Track original methods for restoration
        self._original_update_firewall_status = None
        self._original_unified_timer_update = None

    def apply_optimization(self):
        """Apply the firewall status optimization to the main window."""
        try:
            # Initialize the firewall status integration
            self.firewall_integration = FirewallStatusIntegration(
                main_window=self.main_window
            )

            # Patch the firewall status update method
            self._patch_firewall_update_method()

            # Modify the unified timer to reduce firewall status checks
            self._patch_unified_timer()

            # Start the optimized monitoring
            self.firewall_integration.start_optimization()

            msg = "Firewall status optimization applied successfully"
            self.logger.info(msg)

        except Exception as e:
            self.logger.error(f"Failed to apply firewall optimization: {e}")
            raise

    def _patch_firewall_update_method(self):
        """Patch the firewall status update method for optimization."""
        # Store original method
        if hasattr(self.main_window, "update_firewall_status"):
            self._original_update_firewall_status = (
                self.main_window.update_firewall_status
            )

        # Replace with optimized version
        update_method = self._optimized_firewall_update
        self.main_window.update_firewall_status = update_method

    def _patch_unified_timer(self):
        """Patch the unified timer to reduce firewall status polling."""
        if hasattr(self.main_window, "unified_timer_update"):
            self._original_unified_timer_update = self.main_window.unified_timer_update
            self.main_window.unified_timer_update = self._optimized_unified_timer_update

    def _optimized_firewall_update(self):
        """Optimized firewall status update using the integration."""
        try:
            if self.firewall_integration:
                # Use the optimizer to get current status
                optimizer = self.firewall_integration.optimizer
                status = optimizer.get_firewall_status(use_cache=True)

                # Update the main window cache and GUI
                self.main_window._firewall_status_cache = status

                # Update the status card if the method exists
                if hasattr(self.main_window, "update_firewall_status_card"):
                    self.main_window.update_firewall_status_card()

            # Fallback to original method if integration not available
            elif self._original_update_firewall_status:
                self._original_update_firewall_status()

        except Exception as e:
            self.logger.error(f"Error in optimized firewall update: {e}")
            # Fallback to original method on error
            if self._original_update_firewall_status:
                self._original_update_firewall_status()

    def _optimized_unified_timer_update(self):
        """Optimized unified timer that reduces firewall status checks."""
        try:
            # Call original timer update first
            if self._original_unified_timer_update:
                self._original_unified_timer_update()

            # Override firewall status update frequency
            # The optimizer handles firewall updates via events, so we can
            # reduce the timer-based checks significantly
            if hasattr(self.main_window, "timer_cycle_count"):
                cycle = self.main_window.timer_cycle_count

                # Only check firewall status every 30 cycles (30 seconds)
                # instead of every 5 cycles, events handle immediate updates
                if cycle % 30 == 0 and self.firewall_integration:
                    # Ensure the optimizer is still running
                    optimizer = self.firewall_integration.optimizer
                    stats = optimizer.get_performance_stats()
                    if not stats["monitoring_active"]:
                        self.firewall_integration.start_optimization()

        except (AttributeError, KeyError) as e:
            self.logger.error("Error in optimized unified timer: %s", e)

    def force_refresh(self):
        """Force an immediate firewall status refresh."""
        if self.firewall_integration:
            self.firewall_integration.force_refresh()

    def remove_optimization(self):
        """Remove the optimization and restore original methods."""
        try:
            # Stop the optimized monitoring
            if self.firewall_integration:
                self.firewall_integration.stop_optimization()

            # Restore original methods
            if self._original_update_firewall_status:
                self.main_window.update_firewall_status = (
                    self._original_update_firewall_status
                )

            if self._original_unified_timer_update:
                self.main_window.unified_timer_update = (
                    self._original_unified_timer_update
                )

            self.logger.info("Firewall status optimization removed")

        except Exception as e:
            self.logger.error(f"Error removing firewall optimization: {e}")

    def get_optimization_stats(self) -> dict:
        """Get performance statistics for the optimization."""
        if self.firewall_integration:
            return self.firewall_integration.optimizer.get_performance_stats()
        return {"optimization_active": False}


def apply_firewall_optimization(main_window: Any) -> Any:
    """
    Apply firewall status optimization to a main window.

    Usage:
        from app.gui.firewall_optimization_patch import (
            apply_firewall_optimization
        )

        # In main_window initialization
        self.firewall_patch = apply_firewall_optimization(self)
    """
    try:
        patch = MainWindowFirewallPatch(main_window)
        patch.apply_optimization()
        return patch

    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to apply firewall optimization: {e}")
        return None


def create_manual_refresh_trigger(main_window, firewall_patch):
    """
    Create a manual refresh trigger for testing or manual use.

    This can be connected to a button or menu item for immediate refresh.
    """

    def manual_refresh():
        """Manually trigger firewall status refresh."""
        if firewall_patch:
            firewall_patch.force_refresh()
        elif hasattr(main_window, "update_firewall_status"):
            # Fallback to standard refresh
            if hasattr(main_window, "_firewall_status_cache"):
                main_window._firewall_status_cache = None
            main_window.update_firewall_status()

    return manual_refresh
