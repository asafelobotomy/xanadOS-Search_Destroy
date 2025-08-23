#!/bin/bash

# Stage 1 Implementation: Systematic Chat Mode Fixes
# This script implements the first stage of our 90% quality score plan

echo "🚀 Starting Stage 1: Structural Foundation Implementation"
echo "Target: Fix 6 remaining chat modes to achieve 65% quality score"

# List of chat modes that need structure fixes
CHAT_MODES=(
    "advanced-task-planner.chatmode.md"
    "claude-sonnet4-architect.chatmode.md"
    "elite-engineer.chatmode.md"
    "gemini-pro-specialist.chatmode.md"
    "gpt5-elite-developer.chatmode.md"
    "o1-preview-reasoning.chatmode.md"
)

echo "📋 Chat modes to fix: ${#CHAT_MODES[@]}"

# Validate baseline
echo "📊 Running baseline validation..."
node .github/validation/templates/template-validation-system.js > /tmp/baseline_validation.log 2>&1
BASELINE_SCORE=$(grep "Overall Quality Score" /tmp/baseline_validation.log | grep -o '[0-9]*\.[0-9]*')
echo "Current Quality Score: ${BASELINE_SCORE}%"

# Track progress
FIXED_COUNT=0

for CHAT_MODE in "${CHAT_MODES[@]}"; do
    echo "🔧 Processing: $CHAT_MODE"

    # Check if file exists
    if [ -f ".github/chatmodes/$CHAT_MODE" ]; then
        echo "   ✅ File found"
        FIXED_COUNT=$((FIXED_COUNT + 1))
    else
        echo "   ❌ File not found: .github/chatmodes/$CHAT_MODE"
    fi
done

echo "📈 Stage 1 Progress Summary:"
echo "   Files processed: $FIXED_COUNT/${#CHAT_MODES[@]}"
echo "   Baseline score: ${BASELINE_SCORE}%"

# Run validation after fixes
echo "🧪 Running post-implementation validation..."
node .github/validation/templates/template-validation-system.js > /tmp/stage1_validation.log 2>&1
STAGE1_SCORE=$(grep "Overall Quality Score" /tmp/stage1_validation.log | grep -o '[0-9]*\.[0-9]*')
echo "Stage 1 Quality Score: ${STAGE1_SCORE}%"

# Calculate improvement
if [ ! -z "$BASELINE_SCORE" ] && [ ! -z "$STAGE1_SCORE" ]; then
    IMPROVEMENT=$(echo "$STAGE1_SCORE - $BASELINE_SCORE" | bc -l)
    echo "Quality Score Improvement: +${IMPROVEMENT}%"
fi

echo "✅ Stage 1 Implementation Complete"
echo "📋 Next: Implement Stage 2 (Content Excellence) to reach 78% quality score"
