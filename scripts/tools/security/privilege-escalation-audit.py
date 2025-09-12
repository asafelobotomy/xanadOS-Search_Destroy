#!/usr/bin/env python3
"""Security audit and improvement script for privilege escalation.
Ensures all elevated operations follow security best practices.
"""

import sys
from pathlib import Path


class PrivilegeEscalationAuditor:
    """Audits Python files for privilege escalation security issues."""

    def __init__(self):
        self.issues = []
        self.secure_functions = {
            "elevated_run",
            "elevated_popen",
            "run_secure",
            "popen_secure",
        }
        self.dangerous_patterns = [
            "subprocess.run(",
            "subprocess.Popen(",
            "subprocess.call(",
            "os.system(",
            "shell=True",
        ]

    def audit_file(self, file_path: Path) -> list[tuple[int, str, str]]:
        """Audit a single Python file for security issues."""
        issues = []

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")

            # Check for direct subprocess usage in privilege-requiring operations
            for i, line in enumerate(lines, 1):
                line_stripped = line.strip()

                # Skip comments and docstrings
                if line_stripped.startswith("#") or '"""' in line_stripped:
                    continue

                # Check for dangerous patterns
                for pattern in self.dangerous_patterns:
                    if pattern in line:
                        # Check if this might need privilege escalation
                        if self._needs_privileges(line, lines, i - 1):
                            context = self._get_context(lines, i - 1)
                            issues.append(
                                (
                                    i,
                                    f"Direct subprocess usage in privileged operation: {pattern}",
                                    context,
                                )
                            )
                        elif pattern == "shell=True":
                            # shell=True is always dangerous
                            context = self._get_context(lines, i - 1)
                            issues.append((i, "Dangerous shell=True usage", context))

        except Exception as e:
            issues.append((0, f"Error reading file: {e}", ""))

        return issues

    def _needs_privileges(self, line: str, lines: list[str], line_idx: int) -> bool:
        """Check if a subprocess call likely needs privileges."""
        # Common commands that need root
        privileged_commands = [
            "sudo",
            "pkexec",
            "systemctl",
            "ufw",
            "iptables",
            "mount",
            "umount",
            "chown",
            "chmod 755",
            "chmod 644",
            "apt",
            "yum",
            "dnf",
            "pacman",
            "zypper",
        ]

        # Check current line and surrounding context
        context_lines = lines[max(0, line_idx - 2) : line_idx + 3]
        context = " ".join(context_lines).lower()

        return any(cmd in context for cmd in privileged_commands)

    def _get_context(self, lines: list[str], line_idx: int) -> str:
        """Get context around a line for better understanding."""
        start = max(0, line_idx - 1)
        end = min(len(lines), line_idx + 2)
        return "\n".join(f"{i + 1}: {lines[i]}" for i in range(start, end))

    def audit_directory(self, directory: Path) -> None:
        """Audit all Python files in a directory."""
        for py_file in directory.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue

            file_issues = self.audit_file(py_file)
            if file_issues:
                self.issues.extend(
                    [
                        (str(py_file.relative_to(directory)), line_num, issue, context)
                        for line_num, issue, context in file_issues
                    ]
                )

    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped from audit."""
        skip_patterns = [
            "__pycache__",
            ".pyc",
            "test_",
            "_test.py",
            "migrations/",
            ".git/",
        ]

        file_str = str(file_path)
        return any(pattern in file_str for pattern in skip_patterns)

    def generate_report(self) -> str:
        """Generate a security audit report."""
        if not self.issues:
            return "✅ No privilege escalation security issues found!"

        report = "🔒 PRIVILEGE ESCALATION SECURITY AUDIT REPORT\n"
        report += "=" * 60 + "\n\n"

        report += f"Found {len(self.issues)} potential security issues:\n\n"

        for file_path, line_num, issue, context in self.issues:
            report += f"📁 File: {file_path}\n"
            report += f"📍 Line {line_num}: {issue}\n"
            report += f"📝 Context:\n{context}\n"
            report += "-" * 40 + "\n\n"

        # Add recommendations
        report += "🔧 SECURITY RECOMMENDATIONS:\n\n"
        report += "1. Replace subprocess calls with elevated_run() for privileged operations\n"
        report += "2. Use run_secure()/popen_secure() for non-privileged operations\n"
        report += "3. Avoid shell=True unless absolutely necessary\n"
        report += "4. Validate all user inputs before passing to subprocess\n"
        report += "5. Use GUI authentication manager for consistent privilege handling\n\n"

        return report


def main():
    """Main function to run the privilege escalation audit."""
    import argparse

    parser = argparse.ArgumentParser(description="Privilege Escalation Security Audit")
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Run in validation mode (always returns 0)",
    )
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    current_dir = Path.cwd()

    # Look for app directory from various locations
    app_dir = None
    for base in [current_dir, script_dir.parent.parent.parent]:
        potential_app = base / "app"
        if potential_app.exists() and potential_app.is_dir():
            app_dir = potential_app
            break

    if not app_dir:
        print("❌ App directory not found!")
        print(f"Looking for: {app_dir}")
        print(f"Current dir: {current_dir}")
        return 1

    # Run the audit
    auditor = PrivilegeEscalationAuditor()
    auditor.audit_directory(app_dir)

    # Generate and print report
    report = auditor.generate_report()
    print(report)

    # Return appropriate exit code
    if args.validate_only:
        # In validation mode, always return 0 (for quick-validate)
        return 0
    else:
        # In audit mode, return 1 if issues found
        return 1 if auditor.issues else 0


if __name__ == "__main__":
    sys.exit(main())
