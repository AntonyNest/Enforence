"""
Тести для ComplianceCheckerAgent.
"""

import pytest

from src.agents.compliance_checker import ComplianceCheckerAgent


def test_structural_check_all_sections():
    """Перевірка з усіма обов'язковими секціями."""
    sections = [{"id": str(i)} for i in range(1, 11)]
    result = ComplianceCheckerAgent._structural_check(sections)

    assert result["structural_score"] == 1.0
    assert result["missing_sections"] == []


def test_structural_check_missing_sections():
    """Перевірка з відсутніми секціями."""
    sections = [{"id": "1"}, {"id": "2"}, {"id": "3"}]
    result = ComplianceCheckerAgent._structural_check(sections)

    assert result["structural_score"] < 1.0
    assert len(result["missing_sections"]) > 0


def test_structural_check_empty():
    """Перевірка з порожнім списком секцій."""
    result = ComplianceCheckerAgent._structural_check([])

    assert result["structural_score"] == 0.0
    assert len(result["missing_sections"]) == 8  # 8 обов'язкових
