"""
Intelligent Rule Generation System for xanadOS Search & Destroy.

This module provides AI-driven security rule generation capabilities:
- YARA rule generation from malware samples
- Exclusion rule creation from false positives
- ClamAV signature assistance
- Rule effectiveness scoring and automatic retirement

Phase 2, Task 2.2.3: Intelligent Rule Generation
"""

import asyncio
import hashlib
import json
import logging
import re
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================

# XDG-compliant paths
DATA_DIR = Path.home() / ".local/share/search-and-destroy/rules"
GENERATED_RULES_DIR = DATA_DIR / "generated"
EXCLUSION_RULES_DIR = DATA_DIR / "exclusions"
RULE_DB_PATH = DATA_DIR / "rule_database.json"

# Ensure directories exist
for directory in [DATA_DIR, GENERATED_RULES_DIR, EXCLUSION_RULES_DIR]:
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)


# ============================================================================
# Enums and Constants
# ============================================================================


class RuleType(Enum):
    """Type of security rule."""

    YARA = "yara"
    CLAMAV = "clamav"
    EXCLUSION = "exclusion"
    CUSTOM = "custom"


class RuleStatus(Enum):
    """Rule lifecycle status."""

    ACTIVE = "active"
    TESTING = "testing"
    RETIRED = "retired"
    FAILED = "failed"


class ThreatCategory(Enum):
    """Malware threat categories."""

    TROJAN = "trojan"
    RANSOMWARE = "ransomware"
    SPYWARE = "spyware"
    ROOTKIT = "rootkit"
    WORM = "worm"
    ADWARE = "adware"
    EXPLOIT = "exploit"
    GENERIC = "generic"


# Rule effectiveness thresholds
MIN_DETECTION_RATE = 0.80  # 80% detection required
MAX_FALSE_POSITIVE_RATE = 0.01  # 1% false positives max
RULE_RETIREMENT_DAYS = 90  # Auto-retire after 90 days if ineffective
MIN_SAMPLE_SIZE = 10  # Minimum samples to evaluate rule


# ============================================================================
# Data Models
# ============================================================================


@dataclass
class MalwareSample:
    """
    Malware sample for analysis.

    Attributes:
        file_hash: SHA256 hash of the sample
        file_path: Path to the sample file
        file_size: Size in bytes
        category: Threat category
        strings: Extracted ASCII/Unicode strings
        byte_patterns: Common byte sequences
        behavior: Behavioral characteristics
        metadata: Additional sample metadata
    """

    file_hash: str
    file_path: str
    file_size: int
    category: str = ThreatCategory.GENERIC.value
    strings: list[str] = field(default_factory=list)
    byte_patterns: list[bytes] = field(default_factory=list)
    behavior: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MalwareSample":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class GeneratedRule:
    """
    Generated security rule with effectiveness metrics.

    Attributes:
        rule_id: Unique rule identifier
        rule_type: Type of rule (YARA, ClamAV, exclusion)
        name: Human-readable rule name
        content: Rule content (YARA syntax, signature, etc.)
        description: Rule description
        category: Threat category targeted
        created_at: Creation timestamp
        status: Rule lifecycle status
        true_positives: Count of correct detections
        false_positives: Count of incorrect detections
        false_negatives: Count of missed detections
        last_updated: Last update timestamp
        retirement_date: Scheduled retirement date
        metadata: Additional rule metadata
    """

    rule_id: str
    rule_type: str
    name: str
    content: str
    description: str = ""
    category: str = ThreatCategory.GENERIC.value
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    status: str = RuleStatus.TESTING.value
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    last_updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    retirement_date: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def detection_rate(self) -> float:
        """Calculate detection rate (true positives / total positives)."""
        total = self.true_positives + self.false_negatives
        return self.true_positives / total if total > 0 else 0.0

    @property
    def false_positive_rate(self) -> float:
        """Calculate false positive rate."""
        total = self.true_positives + self.false_positives
        return self.false_positives / total if total > 0 else 0.0

    @property
    def effectiveness_score(self) -> float:
        """
        Calculate overall effectiveness score (0.0-1.0).

        Combines detection rate and false positive penalty.
        """
        detection_score = self.detection_rate
        fp_penalty = self.false_positive_rate * 2.0  # Double penalty for FPs
        return max(0.0, detection_score - fp_penalty)

    @property
    def is_effective(self) -> bool:
        """Check if rule meets effectiveness criteria."""
        return (
            self.detection_rate >= MIN_DETECTION_RATE
            and self.false_positive_rate <= MAX_FALSE_POSITIVE_RATE
            and (self.true_positives + self.false_negatives) >= MIN_SAMPLE_SIZE
        )

    @property
    def should_retire(self) -> bool:
        """Check if rule should be retired."""
        if self.status == RuleStatus.RETIRED.value:
            return True

        # Check retirement date
        if self.retirement_date:
            retirement = datetime.fromisoformat(self.retirement_date)
            if datetime.utcnow() >= retirement:
                return True

        # Check effectiveness after sufficient samples
        total_samples = self.true_positives + self.false_negatives
        if total_samples >= MIN_SAMPLE_SIZE and not self.is_effective:
            return True

        return False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GeneratedRule":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class RuleGenerationResult:
    """
    Result of rule generation operation.

    Attributes:
        success: Whether generation succeeded
        rules_generated: List of generated rules
        generation_time: Time taken to generate rules
        samples_analyzed: Number of samples analyzed
        patterns_found: Number of patterns identified
        error: Error message if generation failed
    """

    success: bool
    rules_generated: list[GeneratedRule] = field(default_factory=list)
    generation_time: float = 0.0
    samples_analyzed: int = 0
    patterns_found: int = 0
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        # Convert GeneratedRule objects to dicts
        data["rules_generated"] = [rule.to_dict() for rule in self.rules_generated]
        return data


# ============================================================================
# Rule Generator
# ============================================================================


class RuleGenerator:
    """
    Intelligent security rule generator.

    Features:
    - AI-driven YARA rule generation from malware samples
    - Automatic exclusion rule creation from false positives
    - ClamAV signature generation assistance
    - Rule effectiveness scoring and automatic retirement
    """

    def __init__(self, rule_db_path: Path = RULE_DB_PATH):
        """
        Initialize the rule generator.

        Args:
            rule_db_path: Path to rule database JSON file
        """
        self.rule_db_path = rule_db_path
        self.rules: dict[str, GeneratedRule] = {}

        # Pattern extraction settings
        self.min_string_length = 6
        self.min_pattern_frequency = 0.7  # 70% of samples must have pattern
        self.max_rules_per_category = 10

        # Load existing rules
        self._load_rules()

    def _load_rules(self) -> None:
        """Load rules from database."""
        if self.rule_db_path.exists():
            try:
                with open(self.rule_db_path, "r") as f:
                    data = json.load(f)
                    self.rules = {
                        rule_id: GeneratedRule.from_dict(rule_data)
                        for rule_id, rule_data in data.get("rules", {}).items()
                    }
                logger.info(f"Loaded {len(self.rules)} rules from database")
            except Exception as e:
                logger.error(f"Failed to load rule database: {e}")

    def _save_rules(self) -> None:
        """Save rules to database."""
        try:
            data = {
                "rules": {
                    rule_id: rule.to_dict() for rule_id, rule in self.rules.items()
                },
                "last_updated": datetime.utcnow().isoformat(),
            }

            with open(self.rule_db_path, "w") as f:
                json.dump(data, f, indent=2)

            logger.info(f"Saved {len(self.rules)} rules to database")
        except Exception as e:
            logger.error(f"Failed to save rule database: {e}")

    async def generate_yara_rules(
        self,
        samples: list[MalwareSample],
        category: str = ThreatCategory.GENERIC.value,
        min_confidence: float = 0.7,
    ) -> RuleGenerationResult:
        """
        Generate YARA rules from malware samples.

        Args:
            samples: List of malware samples to analyze
            category: Threat category for generated rules
            min_confidence: Minimum confidence threshold (0.0-1.0)

        Returns:
            RuleGenerationResult with generated YARA rules
        """
        start_time = time.time()

        try:
            if not samples:
                return RuleGenerationResult(
                    success=False,
                    error="No samples provided",
                )

            logger.info(f"Generating YARA rules from {len(samples)} samples")

            # Extract common patterns
            patterns = await self._extract_patterns(samples, min_confidence)

            if not patterns:
                return RuleGenerationResult(
                    success=False,
                    error="No common patterns found",
                    samples_analyzed=len(samples),
                )

            # Generate YARA rules from patterns
            rules = []
            for pattern_type, pattern_data in patterns.items():
                rule = self._create_yara_rule(
                    pattern_type=pattern_type,
                    pattern_data=pattern_data,
                    category=category,
                    samples=samples,
                )
                if rule:
                    rules.append(rule)

            # Limit rules per category
            rules = rules[: self.max_rules_per_category]

            # Save rules
            for rule in rules:
                self.rules[rule.rule_id] = rule
            self._save_rules()

            generation_time = time.time() - start_time

            logger.info(f"Generated {len(rules)} YARA rules in {generation_time:.2f}s")

            return RuleGenerationResult(
                success=True,
                rules_generated=rules,
                generation_time=generation_time,
                samples_analyzed=len(samples),
                patterns_found=len(patterns),
            )

        except Exception as e:
            logger.error(f"YARA rule generation failed: {e}")
            return RuleGenerationResult(
                success=False,
                error=str(e),
                generation_time=time.time() - start_time,
            )

    async def _extract_patterns(
        self,
        samples: list[MalwareSample],
        min_confidence: float,
    ) -> dict[str, Any]:
        """
        Extract common patterns from malware samples.

        Args:
            samples: Malware samples to analyze
            min_confidence: Minimum pattern frequency threshold

        Returns:
            Dictionary of pattern types and their data
        """
        # Simulate async pattern extraction
        await asyncio.sleep(0.01)

        patterns = {}

        # Extract common strings
        string_patterns = self._extract_string_patterns(samples, min_confidence)
        if string_patterns:
            patterns["strings"] = string_patterns

        # Extract byte patterns
        byte_patterns = self._extract_byte_patterns(samples, min_confidence)
        if byte_patterns:
            patterns["bytes"] = byte_patterns

        # Extract behavioral patterns
        behavior_patterns = self._extract_behavior_patterns(samples, min_confidence)
        if behavior_patterns:
            patterns["behavior"] = behavior_patterns

        return patterns

    def _extract_string_patterns(
        self,
        samples: list[MalwareSample],
        min_confidence: float,
    ) -> list[str]:
        """Extract common ASCII/Unicode strings."""
        # Count string occurrences across samples
        string_counter = Counter()

        for sample in samples:
            # Use set to count each string only once per sample
            unique_strings = set(
                s for s in sample.strings if len(s) >= self.min_string_length
            )
            string_counter.update(unique_strings)

        # Filter strings by frequency
        min_count = int(len(samples) * min_confidence)
        common_strings = [
            string for string, count in string_counter.items() if count >= min_count
        ]

        return common_strings[:20]  # Limit to top 20 strings

    def _extract_byte_patterns(
        self,
        samples: list[MalwareSample],
        min_confidence: float,
    ) -> list[str]:
        """Extract common byte sequences."""
        # Count byte pattern occurrences
        pattern_counter = Counter()

        for sample in samples:
            # Convert byte patterns to hex strings for counting
            hex_patterns = set(pattern.hex() for pattern in sample.byte_patterns)
            pattern_counter.update(hex_patterns)

        # Filter patterns by frequency
        min_count = int(len(samples) * min_confidence)
        common_patterns = [
            pattern for pattern, count in pattern_counter.items() if count >= min_count
        ]

        return common_patterns[:10]  # Limit to top 10 patterns

    def _extract_behavior_patterns(
        self,
        samples: list[MalwareSample],
        min_confidence: float,
    ) -> dict[str, Any]:
        """Extract common behavioral characteristics."""
        # Aggregate behavioral features
        behavior_features = defaultdict(Counter)

        for sample in samples:
            for feature, value in sample.behavior.items():
                if isinstance(value, (str, int, bool)):
                    behavior_features[feature][str(value)] += 1

        # Filter features by frequency
        min_count = int(len(samples) * min_confidence)
        common_behaviors = {}

        for feature, value_counts in behavior_features.items():
            common_values = [
                value for value, count in value_counts.items() if count >= min_count
            ]
            if common_values:
                common_behaviors[feature] = common_values

        return common_behaviors

    def _create_yara_rule(
        self,
        pattern_type: str,
        pattern_data: Any,
        category: str,
        samples: list[MalwareSample],
    ) -> GeneratedRule | None:
        """
        Create a YARA rule from extracted patterns.

        Args:
            pattern_type: Type of pattern (strings, bytes, behavior)
            pattern_data: Pattern data
            category: Threat category
            samples: Original malware samples

        Returns:
            GeneratedRule or None if rule creation failed
        """
        try:
            # Generate unique rule ID
            rule_id = self._generate_rule_id(category, pattern_type)

            # Generate rule name
            rule_name = f"{category}_{pattern_type}_{int(time.time())}"

            # Build YARA rule content
            yara_content = self._build_yara_content(
                rule_name=rule_name,
                pattern_type=pattern_type,
                pattern_data=pattern_data,
                category=category,
            )

            # Calculate retirement date (90 days from now)
            retirement_date = (
                datetime.utcnow() + timedelta(days=RULE_RETIREMENT_DAYS)
            ).isoformat()

            rule = GeneratedRule(
                rule_id=rule_id,
                rule_type=RuleType.YARA.value,
                name=rule_name,
                content=yara_content,
                description=f"Auto-generated YARA rule for {category} malware",
                category=category,
                status=RuleStatus.TESTING.value,
                retirement_date=retirement_date,
                metadata={
                    "pattern_type": pattern_type,
                    "sample_count": len(samples),
                    "sample_hashes": [s.file_hash[:8] for s in samples[:5]],
                },
            )

            # Save rule to file
            self._save_rule_to_file(rule)

            return rule

        except Exception as e:
            logger.error(f"Failed to create YARA rule: {e}")
            return None

    def _build_yara_content(
        self,
        rule_name: str,
        pattern_type: str,
        pattern_data: Any,
        category: str,
    ) -> str:
        """Build YARA rule content from patterns."""
        lines = []

        # Rule header
        lines.append(f"rule {rule_name} {{")

        # Metadata
        lines.append("    meta:")
        lines.append(
            f'        description = "Auto-generated rule for {category} detection"'
        )
        lines.append(f'        category = "{category}"')
        lines.append(f'        pattern_type = "{pattern_type}"')
        lines.append(f'        generated = "{datetime.utcnow().isoformat()}"')
        lines.append(f'        author = "xanadOS Rule Generator"')

        # Strings section
        lines.append("")
        lines.append("    strings:")

        if pattern_type == "strings" and isinstance(pattern_data, list):
            for i, string in enumerate(pattern_data[:20], 1):
                # Escape special characters for YARA
                escaped = string.replace("\\", "\\\\").replace('"', '\\"')
                lines.append(f'        $s{i} = "{escaped}" ascii wide nocase')

        elif pattern_type == "bytes" and isinstance(pattern_data, list):
            for i, hex_pattern in enumerate(pattern_data[:10], 1):
                # Format hex pattern for YARA
                formatted = " ".join(
                    hex_pattern[j : j + 2] for j in range(0, len(hex_pattern), 2)
                )
                lines.append(f"        $b{i} = {{ {formatted} }}")

        # Condition section
        lines.append("")
        lines.append("    condition:")

        if pattern_type == "strings":
            count = min(len(pattern_data), 20)
            threshold = max(2, count // 3)  # Require 1/3 of strings
            lines.append(f"        {threshold} of ($s*)")

        elif pattern_type == "bytes":
            count = min(len(pattern_data), 10)
            threshold = max(1, count // 2)  # Require 1/2 of byte patterns
            lines.append(f"        {threshold} of ($b*)")

        else:
            lines.append("        any of them")

        lines.append("}")

        return "\n".join(lines)

    def _generate_rule_id(self, category: str, pattern_type: str) -> str:
        """Generate unique rule ID using UUID for uniqueness."""
        import uuid

        unique_id = str(uuid.uuid4())[:8]
        return f"rule_{category[:4]}_{pattern_type[:4]}_{unique_id}"

    def _save_rule_to_file(self, rule: GeneratedRule) -> None:
        """Save rule content to file."""
        try:
            file_path = GENERATED_RULES_DIR / f"{rule.rule_id}.yar"
            with open(file_path, "w") as f:
                f.write(rule.content)
            logger.info(f"Saved rule to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save rule file: {e}")

    async def create_exclusion_rule(
        self,
        file_path: str,
        file_hash: str,
        reason: str = "False positive",
    ) -> GeneratedRule:
        """
        Create exclusion rule for false positive.

        Args:
            file_path: Path to file that triggered false positive
            file_hash: SHA256 hash of the file
            reason: Reason for exclusion

        Returns:
            GeneratedRule with exclusion rule
        """
        # Generate rule ID
        rule_id = f"exclusion_{file_hash[:16]}"

        # Create exclusion rule (simple hash-based)
        content = json.dumps(
            {
                "type": "exclusion",
                "hash": file_hash,
                "path_pattern": Path(file_path).name,
                "reason": reason,
            },
            indent=2,
        )

        rule = GeneratedRule(
            rule_id=rule_id,
            rule_type=RuleType.EXCLUSION.value,
            name=f"Exclusion_{Path(file_path).name}",
            content=content,
            description=f"Exclusion rule: {reason}",
            category="exclusion",
            status=RuleStatus.ACTIVE.value,
            metadata={
                "file_path": file_path,
                "file_hash": file_hash,
                "reason": reason,
            },
        )

        # Save rule
        self.rules[rule_id] = rule
        self._save_rules()

        # Save to exclusion file
        exclusion_path = EXCLUSION_RULES_DIR / f"{rule_id}.json"
        with open(exclusion_path, "w") as f:
            f.write(content)

        logger.info(f"Created exclusion rule for {file_path}")

        return rule

    def update_rule_metrics(
        self,
        rule_id: str,
        true_positive: bool | None = None,
        false_positive: bool | None = None,
        false_negative: bool | None = None,
    ) -> None:
        """
        Update rule effectiveness metrics.

        Args:
            rule_id: Rule identifier
            true_positive: Increment true positive count
            false_positive: Increment false positive count
            false_negative: Increment false negative count
        """
        if rule_id not in self.rules:
            logger.warning(f"Rule {rule_id} not found")
            return

        rule = self.rules[rule_id]

        if true_positive:
            rule.true_positives += 1
        if false_positive:
            rule.false_positives += 1
        if false_negative:
            rule.false_negatives += 1

        rule.last_updated = datetime.utcnow().isoformat()

        # Check if rule should be promoted to active
        if rule.status == RuleStatus.TESTING.value and rule.is_effective:
            rule.status = RuleStatus.ACTIVE.value
            logger.info(f"Rule {rule_id} promoted to ACTIVE status")

        # Check if rule should be retired
        if rule.should_retire:
            rule.status = RuleStatus.RETIRED.value
            logger.info(f"Rule {rule_id} retired due to ineffectiveness")

        self._save_rules()

    def get_active_rules(
        self,
        rule_type: str | None = None,
        category: str | None = None,
    ) -> list[GeneratedRule]:
        """
        Get active rules, optionally filtered.

        Args:
            rule_type: Filter by rule type (YARA, exclusion, etc.)
            category: Filter by threat category

        Returns:
            List of active rules
        """
        rules = [
            rule
            for rule in self.rules.values()
            if rule.status == RuleStatus.ACTIVE.value
        ]

        if rule_type:
            rules = [r for r in rules if r.rule_type == rule_type]

        if category:
            rules = [r for r in rules if r.category == category]

        return rules

    def retire_ineffective_rules(self) -> int:
        """
        Retire rules that don't meet effectiveness criteria.

        Returns:
            Number of rules retired
        """
        retired_count = 0

        for rule in self.rules.values():
            if rule.should_retire and rule.status != RuleStatus.RETIRED.value:
                rule.status = RuleStatus.RETIRED.value
                rule.last_updated = datetime.utcnow().isoformat()
                retired_count += 1
                logger.info(
                    f"Retired rule {rule.rule_id}: "
                    f"detection={rule.detection_rate:.2%}, "
                    f"fp_rate={rule.false_positive_rate:.2%}"
                )

        if retired_count > 0:
            self._save_rules()

        return retired_count

    def get_rule_statistics(self) -> dict[str, Any]:
        """
        Get overall rule generation statistics.

        Returns:
            Dictionary with statistics
        """
        total_rules = len(self.rules)
        active_rules = sum(
            1 for r in self.rules.values() if r.status == RuleStatus.ACTIVE.value
        )
        testing_rules = sum(
            1 for r in self.rules.values() if r.status == RuleStatus.TESTING.value
        )
        retired_rules = sum(
            1 for r in self.rules.values() if r.status == RuleStatus.RETIRED.value
        )

        # Average effectiveness for active rules
        active_effectiveness = [
            r.effectiveness_score
            for r in self.rules.values()
            if r.status == RuleStatus.ACTIVE.value
        ]
        avg_effectiveness = (
            sum(active_effectiveness) / len(active_effectiveness)
            if active_effectiveness
            else 0.0
        )

        # Total detections
        total_tp = sum(r.true_positives for r in self.rules.values())
        total_fp = sum(r.false_positives for r in self.rules.values())
        total_fn = sum(r.false_negatives for r in self.rules.values())

        return {
            "total_rules": total_rules,
            "active_rules": active_rules,
            "testing_rules": testing_rules,
            "retired_rules": retired_rules,
            "avg_effectiveness": avg_effectiveness,
            "total_true_positives": total_tp,
            "total_false_positives": total_fp,
            "total_false_negatives": total_fn,
            "overall_detection_rate": (
                total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
            ),
            "overall_fp_rate": (
                total_fp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
            ),
        }
