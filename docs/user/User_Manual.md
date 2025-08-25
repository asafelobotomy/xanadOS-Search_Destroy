# S&D - Search & Destroy User Manual

_Your comprehensive guide to protecting your Linux system from malware and security threats_

**Version 2.9.0** | _Updated: August 22, 2025_

---

## 🎯 What is S&D - Search & Destroy

**S&D (Search & Destroy)** is a powerful, user-friendly security application designed specifically for Linux systems.
It combines multiple security tools into one elegant interface to protect your computer from:

- **🦠 Viruses & Malware** - Traditional computer viruses and malicious software
- **🕷️ Rootkits** - Hidden threats that can compromise your entire system
- **🔓 Security Vulnerabilities** - Weaknesses that attackers could exploit
- **📂 Suspicious Files** - Unknown or potentially harmful files

### Why Choose S&D

✅ **Easy to Use** - Simple, modern interface that anyone can understand
✅ **Powerful Protection** - Professional-grade security with ClamAV + RKHunter
✅ **Real-time Monitoring** - Continuous protection while you work
✅ **No Performance Impact** - Lightweight design that won't slow down your computer
✅ **Open Source** - Transparent, community-driven security you can trust

---

## 🚀 Getting Started - Your First 5 Minutes

### Step 1: Launch the Application

### Easy Ways to Start S&D

- 📱 **Desktop**: Click the S&D icon in your applications menu
- 💻 **Terminal**: Run `./run.sh` from the S&D directory
- ⌨️ **Command Line**: Execute `Python -m app.main`

> 🔒 **Security Note**: S&D automatically prevents multiple instances from running simultaneously for your security.
>
>
>
>
### Step 2: Understand the Interface

S&D has a clean, tabbed interface with six main sections:

| Tab | Purpose | What You'll Do Here |
|-----|---------|-------------------|
| 🏠 **Dashboard** | System overview and status | See your protection status at a glance |
| 🔍 **Scan** | Run security scans | Check your computer for threats |
| 🛡️ **Protection** | Real-time monitoring | Enable continuous protection |
| 📊 **Reports** | View scan results | See what was found and take action |
| 🗃️ **Quarantine** | Manage isolated threats | Handle suspicious files safely |
| ⚙️ **Settings** | Configure the app | Customize how S&D works |

### Step 3: Run Your First Scan

### Recommended for new users

1. **Click the 🔍 Scan tab**
2. **Select "🚀 Quick Scan"** (fastest, scans your personal files)
3. **Click "Start Scan"** and wait for results
4. **Review any findings** in the Reports tab

> 💡 **Tip**: Your first scan helps establish a security baseline for your system.
>
>
>
>
### Step 4: Enable Real-time Protection

1. **Go to the 🛡️ Protection tab**
2. **Toggle "Real-time Monitoring" ON**
3. **You're now protected!** S&D will watch for threats automatically

---

## 🔍 Understanding Scan Types

S&D offers three types of scans, each designed for different needs:

### 🚀 Quick Scan (Recommended for Daily Use)

**What it does:** Scans your personal files and common threat locations
**How long:** 2-10 minutes
**Best for:** Daily security checks, new file verification

### When to use

- After downloading files from the internet
- Daily security maintenance (set it as a scheduled task)
- Quick verification after installing new software

### 🔍 Full System Scan (Weekly Deep Clean)

**What it does:** Scans your entire computer, including system files
**How long:** 30-90 minutes
**Best for:** Comprehensive security auditing

### When to use 2

- Weekly thorough security check
- After suspected infection or suspicious activity
- Before important system updates or backups

### ⚙️ Custom Directory Scan (Targeted Analysis)

**What it does:** Scans only the folders you choose
**How long:** Varies by selection
**Best for:** Checking specific files or directories

### When to use 3

- Scanning external USB drives or downloads
- Checking specific project folders
- Verifying files before sharing them

---

## 🔬 Advanced Security: RKHunter Rootkit Detection

### What are Rootkits

**Rootkits** are sophisticated threats that hide deep in your system, often invisible to regular antivirus software.
They can:

- Steal passwords and personal information
- Control your computer remotely
- Hide other malware from detection
- Monitor your activities without your knowledge

### Running a RKHunter Scan

RKHunter is a specialized tool for detecting these hidden threats:

1. **Click "🔍 RKHunter Scan"** in the Scan tab
2. **Enter your password** when prompted (needed for system-level access)
3. **Watch the progress** - RKHunter performs 14 different security checks
4. **Review results** with easy-to-understand color coding:
- 🟢 **Green** = Clean/Safe
- 🟡 **Yellow** = Warning/Suspicious
- 🔴 **Red** = Threat detected

> 🔐 **Why Password Required?** RKHunter needs administrator access to check system-level security.
This is normal and secure.

### Understanding RKHunter Results

### RKHunter checks for

- System file integrity (making sure important files haven't been tampered with)
- Known rootkit signatures (checking against databases of known threats)
- Suspicious system behavior (looking for signs of hidden malware)
- Network security issues (checking for unauthorized network activity)

---

## 🛡️ Real-time Protection - Your Security Shield

### What is Real-time Protection

Real-time protection is like having a security guard for your computer that **never sleeps**.
It continuously monitors your system and immediately responds to threats.

### How to Enable Protection

1. **Navigate to the 🛡️ Protection tab**
2. **Toggle "Enable Real-time Monitoring" to ON**
3. **Configure what to monitor** (recommended: keep default settings)
4. **Set automatic responses** (recommended: quarantine threats automatically)

### What Gets Monitored

When enabled, S&D watches:

- **New files** being created or downloaded
- **USB drives** and external storage when connected
- **System directories** for unauthorized changes
- **Network activity** for suspicious behavior

### Automatic Threat Response

When a threat is detected, S&D can automatically:

1. **🗃️ Quarantine** the threat (safest option - isolates but preserves for analysis)
2. **🚨 Alert you** with a notification
3. **📝 Log the event** for later review
4. **🔄 Update definitions** to catch similar threats

---

## 📊 Understanding Scan Results

### Reading Your Scan Report

After any scan, you'll see a summary with key information:

| Metric | What It Means | Good/Bad |
|--------|---------------|----------|
| **Files Scanned** | Total files checked | More = more thorough |
| **Threats Found** | Dangerous items detected | 0 = good, >0 = needs attention |
| **Scan Time** | How long the scan took | Varies by scan type |
| **System Health** | Overall security rating | Green = good, Red = needs work |

### When Threats Are Found

**Don't panic!** Finding threats is normal, especially on new systems or after browsing the internet.
Here's what to do:

1. **🗃️ Quarantine First** (recommended for beginners)
- Safely isolates the threat
- Prevents damage while allowing investigation
- Can be reversed if it's a false alarm
2. **🔍 Research the Threat**
- Use threat name in online databases (VirusTotal.com)
- Check if it's a known false positive
- Look for removal instructions from security experts
3. **💭 Consider the Context**
- Where was the file found?
- Do you remember downloading/installing it?
- Does it seem legitimate for your use?

### Managing False Positives

Sometimes legitimate files are mistakenly flagged as threats. **Signs of a false positive:**

- File is from a reputable software company
- You recently installed legitimate software
- Multiple users report the same false detection online
- The threat name includes words like "generic" or "heuristic"

### To handle false positives

1. Research the detection online
2. Add to exclusion list if confirmed safe
3. Report to ClamAV to improve future detection

---

## 🗃️ Quarantine Management Made Simple

### What is Quarantine

Think of quarantine as a **secure jail** for suspicious files. Files in quarantine:

- ✅ Can't harm your system
- ✅ Can be restored if they're actually safe
- ✅ Can be studied for analysis
- ✅ Can be permanently deleted when you're sure

### Managing Quarantined Files

### To access quarantine

1. **Click the 🗃️ Quarantine tab**
2. **Review the list** of isolated files
3. **For each file, you can:**
- **📋 View Details** - See why it was quarantined
- **🔄 Restore** - Put it back if it's safe
- **🗑️ Delete** - Remove permanently
- **📤 Export Info** - Save details for research

### Quarantine Best Practices

### For Beginners

- ❌ Don't restore files unless you're 100% sure they're safe
- ✅ Do research threat names online before making decisions
- ✅ Do ask for help if you're unsure
- ✅ Do keep quarantined items for at least a week before deleting

**Safety Rule:** _When in doubt, leave it in quarantine!_

---

## ⚙️ Essential Settings for New Users

### Quick Setup for Maximum Protection

### Recommended settings for new users

#### 🎨 Interface Settings

- **Theme**: Auto (matches your system)
- **Notifications**: Enable all (stay informed)
- **System Tray**: Enable (run in background)

#### 🔍 Scan Settings

- **Default Scan Type**: Quick Scan
- **Automatic Updates**: Daily (keep definitions current)
- **Scheduled Scans**: Enable weekly full scans

#### 🛡️ Protection Settings

- **Real-time Protection**: ON
- **Automatic Quarantine**: ON
- **Threat Notifications**: ON

#### 📊 Privacy Settings

- **Anonymous Usage Statistics**: Your choice
- **Cloud Threat Intelligence**: ON (improves detection)

### Advanced Settings (For Experienced Users)

### Performance Tuning

- CPU Usage Limit: 50% (prevents system slowdown)
- Memory Limit: 2GB (adjust based on your RAM)
- Rate Limiting: ON (prevents system overload)

### Security Hardening

- Heuristic Analysis: Medium sensitivity
- Exclusion Lists: Minimize (only add verified safe locations)
- Update Frequency: Daily definitions, weekly application

---

## 💡 Best Practices - Staying Secure

### Daily Security Habits

### 🌅 Morning Routine (2 minutes)

1. Check S&D system tray icon (should be green/active)
2. Review any overnight notifications
3. Verify real-time protection is enabled

### 🌙 Evening Routine (5 minutes)

1. Run a quick scan of downloads folder
2. Check for any quarantined items needing attention
3. Ensure automatic updates are working

### Weekly Security Maintenance

### 🗓️ Weekly Tasks (15 minutes)

1. **Run a Full System Scan** (set it running, do other things)
2. **Review the past week's reports** for patterns
3. **Update S&D application** if updates available
4. **Clean up quarantine** (delete items you've researched)

### Monthly Security Audit

### 📅 Monthly Tasks (30 minutes)

1. **Complete RKHunter scan** for deep security analysis
2. **Review and update exclusion lists** (remove old entries)
3. **Check system update status** (OS and security patches)
4. **Backup important data** (security isn't just about malware!)

### Warning Signs to Watch For

### 🚨 Immediate attention needed if you notice

- Frequent threat detections (daily finds)
- System running slower than usual
- Unexpected network activity
- Programs you didn't install appearing
- S&D protection being disabled unexpectedly

---

## 🔧 Troubleshooting Common Issues

### "Scan is Taking Too Long"

### Quick Fixes

1. **Reduce scan scope** - Use Custom Scan for specific folders
2. **Exclude large media files** - Skip videos/music if not needed
3. **Close other programs** - Free up system resources
4. **Enable rate limiting** - Prevent system overload

### "Too Many False Positives"

### Solutions

1. **Update virus definitions** - Newer definitions are more accurate
2. **Research detections online** - Check VirusTotal.com
3. **Add exclusions carefully** - Only for verified safe files
4. **Adjust sensitivity** - Lower heuristic detection if needed

### "Real-time Protection Disabled"

### Troubleshooting Steps

1. **Check system permissions** - S&D needs file access
2. **Verify no conflicts** - Other antivirus software can interfere
3. **Review exclusion lists** - Make sure S&D folders aren't excluded
4. **Restart S&D** - Close completely and reopen

### "Can't Run RKHunter Scan"

### Common Solutions

1. **Enter correct password** - Must be your user password
2. **Check sudo access** - Your user needs admin privileges
3. **Close other security tools** - Avoid conflicts during scanning
4. **Free up disk space** - RKHunter needs temporary storage

### Getting Help

### When you need assistance

1. **📖 Check this manual** - Most answers are here
2. **🔍 Search online** - Many users have similar questions
3. **📝 Check log files** - Often contain helpful error details
4. **💬 Community forums** - Ask experienced users
5. **🐛 Report bugs** - Help improve S&D for everyone

### Information to include when asking for help

- Your Linux distribution and version
- S&D version (shown in About dialog)
- Exact error message or behavior
- Steps you tried to fix the issue
- Recent system changes or installations

---

## 🎓 Understanding Security Concepts

### What Makes a File Dangerous

**🦠 Viruses** - Code that spreads by infecting other files
**🐴 Trojans** - Legitimate-looking programs that hide malicious functions
**🕷️ Rootkits** - Deep system infections that hide their presence
**🎣 Phishing** - Fake programs that steal passwords and personal info
**💣 Ransomware** - Malware that encrypts your files and demands payment

### How S&D Protects You

**🔍 Signature Detection** - Recognizes known threats by their "fingerprints"
**🧠 Heuristic Analysis** - Identifies suspicious behavior patterns
**🌐 Cloud Intelligence** - Uses global threat data for latest protections
**⚡ Real-time Monitoring** - Catches threats as they appear
**🔒 Safe Quarantine** - Isolates threats without damaging evidence

### Building Security Awareness

### Good Security Habits

- ✅ Keep software updated (OS, browsers, applications)
- ✅ Download software only from official sources
- ✅ Be cautious with email attachments and links
- ✅ Use strong, unique passwords for important accounts
- ✅ Regular backups of important data

### Warning Signs of Threats

- ❌ Unexpected pop-ups or advertisements
- ❌ Programs running slowly or crashing frequently
- ❌ Unknown programs in startup or running processes
- ❌ High network usage when you're not online
- ❌ Files or folders appearing or disappearing mysteriously

---

## 📈 Making the Most of S&D

### Power User Tips

### 🚀 Efficiency Shortcuts

- **F5** - Refresh current tab
- **Ctrl+S** - Quick scan shortcut
- **F1** - Open this User Manual
- **Ctrl+Q** - Quit application

### ⚙️ Advanced Configurations

- Create custom scan profiles for different needs
- Set up different notification profiles (work vs. home)
- Use exclusion lists strategically for performance
- Export/import settings for multiple computers

### 📊 Monitoring and Analysis

- Review scan trends to identify security patterns
- Use exported reports for compliance documentation
- Monitor system resource usage during scans
- Track false positive rates to optimize settings

### Integration with System Security

### 🔗 Working with Other Security Tools

- S&D complements (doesn't replace) your firewall
- Can work alongside system update managers
- Integrates with Linux security frameworks (AppArmor)
- Supports enterprise security policies and compliance

### 🛡️ Building a Complete Security Strategy

1. **S&D** for malware protection and system scanning
2. **Firewall** for network protection
3. **Regular Updates** for patch management
4. **Backups** for data protection and recovery
5. **User Education** for social engineering protection

---

## 📚 Quick Reference Guide

### Essential Commands Summary

| Action | How To Do It | When to Use |
|--------|-------------|-------------|
| **Quick Scan** | Scan tab → Quick Scan → Start | Daily, after downloads |
| **Full Scan** | Scan tab → Full Scan → Start | Weekly, deep cleaning |
| **RKHunter Scan** | Scan tab → RKHunter Scan → Enter password | Monthly, after issues |
| **Enable Protection** | Protection tab → Toggle ON | Always (continuous protection) |
| **Check Quarantine** | Quarantine tab → Review items | After threats found |
| **View Reports** | Reports tab → Select report | After any scan |
| **Update Definitions** | Automatic (daily) or Settings → Update | Keep current |
| **Open Manual** | Help menu → User Manual or F1 | When you need help |

### Common File Locations

| Item | Location | Purpose |
|------|----------|---------|
| **Application** | `/usr/local/bin/search-and-destroy/` | Main program files |
| **User Config** | `~/.config/search-and-destroy/` | Your personal settings |
| **Quarantine** | `~/.local/share/search-and-destroy/quarantine/` | Isolated threats |
| **Scan Reports** | `~/.local/share/search-and-destroy/reports/` | Scan history |
| **Log Files** | `~/.local/share/search-and-destroy/logs/` | Troubleshooting info |

### Emergency Procedures

### 🚨 If You Suspect Active Infection

1. **Disconnect from internet** (prevent data theft)
2. **Run immediate Full System Scan**
3. **Follow scan recommendations** (usually quarantine)
4. **Do NOT enter passwords** until system is clean
5. **Contact security expert** if unsure about results

### 🔥 If System is Severely Compromised

1. **Boot from external media** (USB Linux rescue disk)
2. **Backup critical data** to clean external storage
3. **Run S&D from rescue environment** if possible
4. **Consider complete system reinstall** for critical systems
5. **Restore data after verification** on clean system

---

_This manual is your complete guide to protecting your Linux system with S&D - Search & Destroy.
Keep it handy for reference, and remember: when in doubt about security, it's always better to be cautious!_

### 📞 Need More Help

- 📖 Additional documentation: `/docs/` folder in your S&D installation
- 🌐 Online community: Visit our GitHub page for discussions and updates
- 🐛 Bug reports: Help us improve S&D by reporting issues you encounter

**🔄 Stay Updated:** This manual is updated with each S&D release.
Check for updates regularly to stay current with new features and security improvements.

---

_Last Updated: August 22, 2025 - Version 2.9.0_
_Thank you for choosing S&D - Search & Destroy for your Linux security needs!_
