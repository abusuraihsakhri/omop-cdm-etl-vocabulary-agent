"""
Tests for metrics collection and active learning modules.
"""
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from agents.metrics import SystemMetricsCollector
from agents.learning import ActiveLearningEngine


class TestSystemMetricsCollector:
    """Tests for Prometheus metrics collector."""

    def test_record_routine_task(self):
        """Routine tasks should increment routine counter."""
        collector = SystemMetricsCollector()
        collector.record_task("ROUTINE", 0.01)
        assert collector.tasks_total == 1
        assert collector.routine_tasks_total == 1
        assert collector.critical_alerts_total == 0

    def test_record_critical_task(self):
        """Critical tasks should increment critical counter."""
        collector = SystemMetricsCollector()
        collector.record_task("CRITICAL_STAT_PANIC", 0.05)
        assert collector.critical_alerts_total == 1
        assert collector.routine_tasks_total == 0

    def test_record_elevated_task(self):
        """Elevated tasks should increment elevated counter."""
        collector = SystemMetricsCollector()
        collector.record_task("ELEVATED_RISK", 0.02)
        assert collector.elevated_alerts_total == 1

    def test_record_phi_block(self):
        """PHI blocks should increment PHI counter."""
        collector = SystemMetricsCollector()
        collector.record_phi_block()
        collector.record_phi_block()
        assert collector.phi_blocks_total == 2

    def test_export_prometheus_format(self):
        """Prometheus export should include all metrics."""
        collector = SystemMetricsCollector()
        collector.record_task("ROUTINE", 0.01)
        collector.record_phi_block()
        output = collector.export_prometheus_text()
        assert "system_tasks_total" in output
        assert "alerts_triggered_total" in output
        assert "phi_outbound_blocks_total" in output
        assert "audit_chain_blocks_total" in output
        assert "task_processing_duration_avg_seconds" in output

    def test_average_latency_calculation(self):
        """Average latency should be computed correctly."""
        collector = SystemMetricsCollector()
        collector.record_task("ROUTINE", 0.1)
        collector.record_task("ROUTINE", 0.3)
        output = collector.export_prometheus_text()
        # Average should be 0.2
        assert "0.2000" in output


class TestActiveLearningEngine:
    """Tests for Bayesian calibration engine."""

    def test_initial_weights(self):
        """Initial weights should be 1.0 for all workers."""
        engine = ActiveLearningEngine()
        weights = engine.get_calibrated_weights()
        assert weights["InvariantQCWorker"] == 1.0
        assert weights["SafetyEscalationWorker"] == 1.0
        assert weights["ProtocolConformanceWorker"] == 1.0

    def test_weight_increase_with_concordant(self):
        """Weights should increase with concordant decisions."""
        engine = ActiveLearningEngine()
        for _ in range(10):
            engine.record_feedback("InvariantQCWorker", True, 0.9)
        weights = engine.get_calibrated_weights()
        assert weights["InvariantQCWorker"] > 1.0

    def test_weight_decrease_with_discordant(self):
        """Weights should decrease with discordant decisions."""
        engine = ActiveLearningEngine()
        for _ in range(10):
            engine.record_feedback("InvariantQCWorker", False, 0.1)
        weights = engine.get_calibrated_weights()
        assert weights["InvariantQCWorker"] < 1.0

    def test_uncertainty_buffer(self):
        """Borderline confidence cases should be flagged."""
        engine = ActiveLearningEngine()
        engine.record_feedback("InvariantQCWorker", True, 0.55)
        engine.record_feedback("InvariantQCWorker", False, 0.50)
        assert len(engine.uncertainty_buffer) == 2

    def test_weight_bounds(self):
        """Weights should stay within [0.2, 2.0] bounds."""
        engine = ActiveLearningEngine()
        # Many concordant decisions
        for _ in range(100):
            engine.record_feedback("InvariantQCWorker", True, 0.99)
        weights = engine.get_calibrated_weights()
        assert weights["InvariantQCWorker"] <= 2.0

        # Many discordant decisions
        for _ in range(100):
            engine.record_feedback("SafetyEscalationWorker", False, 0.01)
        weights = engine.get_calibrated_weights()
        assert weights["SafetyEscalationWorker"] >= 0.2
