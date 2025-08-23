#!/bin/bash

# Stage 3A: Advanced Content Quality Optimization
# Implements GitHub Copilot 2025 documentation standards and fixes remaining validation warnings

echo "🚀 Stage 3A: Advanced Content Quality Optimization"
echo "Target: Fix 5 validation warnings to achieve 96%+ quality score"
echo ""

# Fix 1: Documentation Chat Mode - Heading hierarchy and code block languages
echo "📝 Fix 1: Documentation Chat Mode (.github/chatmodes/documentation.chatmode.md)"

# Fix heading hierarchy - ensure no skipped levels (H1 -> H2 -> H3, not H1 -> H3)
# Fix code blocks without language specification
sed -i '
    # Fix heading hierarchy: Change ### to ## where it follows ## directly
    /^## Examples$/{
        n
        s/^### API Documentation Creation$/## API Documentation Creation/
    }

    # Fix code blocks missing language specification
    s/^```$/```markdown/g

    # Fix specific code blocks that should be specific languages
    /openapi: 3\.0\.3/i\
```yaml
    /paths:/i\
```yaml
    /components:/i\
```yaml

' .github/chatmodes/documentation.chatmode.md

# Fix 2: Security Chat Mode - Heading hierarchy and list formatting
echo "📝 Fix 2: Security Chat Mode (.github/chatmodes/security.chatmode.md)"

# Add blank lines before lists and fix heading hierarchy
sed -i '
    # Add blank line before lists that are not preceded by blank line
    /^- /{
        x
        /^$/!{
            x
            i\

            b
        }
        x
    }

    # Fix heading hierarchy
    s/^#### /### /g
    s/^##### /#### /g

' .github/chatmodes/security.chatmode.md

# Fix 3: Database Optimization Prompt - Heading hierarchy and table formatting
echo "📝 Fix 3: Database Optimization Prompt (.github/prompts/database-optimization.prompt.md)"

# Fix incomplete table formatting and heading hierarchy
sed -i '
    # Fix heading hierarchy - no skipped levels
    s/^#### /### /g
    s/^##### /#### /g

    # Fix incomplete table formatting by ensuring proper table headers
    /|.*|.*|/{
        /^|.*|.*|$/{
            # Check if next line is table separator
            N
            /\n|[-:].*[-:].*|/{
                # Table is properly formatted
                P
                D
            }
            # Add missing table separator
            s/\n/\n|---|---|---|\n/
        }
    }

' .github/prompts/database-optimization.prompt.md

# Fix 4: Deployment Strategy Prompt - Heading hierarchy and table formatting
echo "📝 Fix 4: Deployment Strategy Prompt (.github/prompts/deployment-strategy.prompt.md)"

# Same fixes as database optimization
sed -i '
    # Fix heading hierarchy
    s/^#### /### /g
    s/^##### /#### /g

    # Fix incomplete table formatting
    /|.*|.*|/{
        /^|.*|.*|$/{
            N
            /\n|[-:].*[-:].*|/{
                P
                D
            }
            s/\n/\n|---|---|---|\n/
        }
    }

' .github/prompts/deployment-strategy.prompt.md

# Fix 5: Validation Implementation Summary - List formatting
echo "📝 Fix 5: Validation Implementation Summary (.github/validation/IMPLEMENTATION_SUMMARY.md)"

# Add blank lines before lists
sed -i '
    # Add blank line before lists that are not preceded by blank line
    /^- /{
        x
        /^$/!{
            x
            i\

            b
        }
        x
    }

    # Also fix numbered lists
    /^[0-9]\. /{
        x
        /^$/!{
            x
            i\

            b
        }
        x
    }

' .github/validation/IMPLEMENTATION_SUMMARY.md

echo ""
echo "✅ Stage 3A Content Quality Fixes Applied"
echo ""
echo "Applied fixes:"
echo "  🔧 Fixed heading hierarchy (no skipped levels H1->H3)"
echo "  🔧 Added language specification to code blocks"
echo "  🔧 Added blank lines before lists"
echo "  🔧 Fixed incomplete table formatting"
echo "  🔧 Applied GitHub Copilot 2025 documentation standards"
echo ""
echo "Ready for Stage 3B: Integration Test Enhancement"
