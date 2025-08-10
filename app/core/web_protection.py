#!/usr/bin/env python3
"""
Web Protection System for S&D
Provides real-time web threat protection, URL filtering, and browser integration.
"""
import asyncio
import hashlib
import ipaddress
import json
import logging
import re
import socket
import sqlite3
import ssl
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse

import aiohttp
import dns.resolver


class ThreatCategory(Enum):
    """Web threat categories."""

    MALWARE = "malware"
    PHISHING = "phishing"
    SPAM = "spam"
    BOTNET = "botnet"
    SUSPICIOUS = "suspicious"
    ADULT_CONTENT = "adult_content"
    GAMBLING = "gambling"
    VIOLENCE = "violence"
    HATE_SPEECH = "hate_speech"
    ILLEGAL_CONTENT = "illegal_content"


class BlockAction(Enum):
    """Actions to take when threat is detected."""

    BLOCK = "block"
    WARN = "warn"
    LOG = "log"
    ALLOW = "allow"


class URLReputation(Enum):
    """URL reputation levels."""

    TRUSTED = "trusted"
    SAFE = "safe"
    UNKNOWN = "unknown"
    SUSPICIOUS = "suspicious"
    MALICIOUS = "malicious"


@dataclass
class WebThreat:
    """Represents a web threat detection."""

    url: str
    threat_category: ThreatCategory
    reputation: URLReputation
    risk_score: float  # 0.0 to 1.0
    detection_time: datetime
    source: str  # Detection source (blacklist, heuristic, etc.)
    details: Dict[str, Any] = field(default_factory=dict)
    blocked: bool = False


@dataclass
class URLAnalysis:
    """URL analysis result."""

    url: str
    domain: str
    ip_addresses: List[str]
    ssl_info: Dict[str, Any]
    threat_indicators: List[str]
    reputation: URLReputation
    risk_score: float
    analysis_time: float
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WebProtectionConfig:
    """Web protection configuration."""

    enabled: bool = True
    block_malware: bool = True
    block_phishing: bool = True
    block_adult_content: bool = False
    block_gambling: bool = False
    warn_suspicious: bool = True
    log_all_requests: bool = False
    enable_safe_search: bool = False
    custom_blocked_domains: Set[str] = field(default_factory=set)
    custom_allowed_domains: Set[str] = field(default_factory=set)
    threat_intelligence_feeds: List[str] = field(default_factory=list)
    dns_servers: List[str] = field(
        default_factory=lambda: [
            "8.8.8.8", "1.1.1.1"])
    request_timeout: float = 10.0
    cache_ttl_hours: int = 24
    max_redirects: int = 5


class WebProtectionSystem:
    """
    Comprehensive web protection system providing real-time URL filtering,
    threat detection, and browser security integration.
    """

    def __init__(
            self,
            config: WebProtectionConfig = None,
            database_path: str = None):
        self.logger = logging.getLogger(__name__)
        self.config = config or WebProtectionConfig()

        # Database for caching and storage
        self.db_path = database_path or "web_protection.db"
        self._init_database()

        # Threat intelligence
        self.malware_domains: Set[str] = set()
        self.phishing_domains: Set[str] = set()
        self.suspicious_domains: Set[str] = set()
        self.trusted_domains: Set[str] = set()

        # URL analysis cache
        self.url_cache: Dict[str, URLAnalysis] = {}
        self.cache_expiry: Dict[str, datetime] = {}

        # Real-time monitoring
        self.active_requests: Dict[str, Dict[str, Any]] = {}
        self.threat_history: List[WebThreat] = []

        # Performance tracking
        self.stats = {
            "requests_analyzed": 0,
            "threats_blocked": 0,
            "threats_warned": 0,
            "cache_hits": 0,
            "cache_misses": 0,
        }

        # Callbacks
        self.threat_detected_callback: Optional[Callable[[
            WebThreat], None]] = None
        self.request_blocked_callback: Optional[Callable[[
            str, str], None]] = None
        self.suspicious_activity_callback: Optional[
            Callable[[str, Dict[str, Any]], None]
        ] = None

        # Threading
        self.lock = threading.RLock()
        self.running = False
        self.update_thread: Optional[threading.Thread] = None

        # HTTP session for analysis
        self.session: Optional[aiohttp.ClientSession] = None

        # Load initial threat intelligence
        self._load_default_threat_lists()

        self.logger.info("Web protection system initialized")

    def _init_database(self):
        """Initialize web protection database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # URL analysis cache table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS url_cache (
                        url TEXT PRIMARY KEY,
                        domain TEXT,
                        ip_addresses TEXT,
                        ssl_info TEXT,
                        threat_indicators TEXT,
                        reputation TEXT,
                        risk_score REAL,
                        analysis_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                        details TEXT
                    )
                """
                )

                # Threat detections table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS threat_detections (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        url TEXT,
                        threat_category TEXT,
                        reputation TEXT,
                        risk_score REAL,
                        detection_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                        source TEXT,
                        details TEXT,
                        blocked BOOLEAN DEFAULT FALSE
                    )
                """
                )

                # URL reputation table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS url_reputation (
                        domain TEXT PRIMARY KEY,
                        reputation TEXT,
                        threat_categories TEXT,
                        risk_score REAL,
                        last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                        source TEXT
                    )
                """
                )

                # Blocked domains table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS blocked_domains (
                        domain TEXT PRIMARY KEY,
                        threat_category TEXT,
                        added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        source TEXT,
                        active BOOLEAN DEFAULT TRUE
                    )
                """
                )

                conn.commit()

        except Exception as e:
            self.logger.error(
                "Failed to initialize web protection database: %s", e)

    def _load_default_threat_lists(self):
        """Load default threat intelligence lists."""
        try:
            # Load from database first
            self._load_cached_threat_lists()

            # Add some default known malicious domains for testing
            default_malware = {
                "malware.test",
                "virus.example",
                "trojan.test",
                "badware.com",
                "malicious.net",
            }

            default_phishing = {
                "phishing.test",
                "fake-bank.com",
                "scam.example",
                "fraudulent.net",
                "spoofed.org",
            }

            default_trusted = {
                "google.com",
                "microsoft.com",
                "mozilla.org",
                "github.com",
                "stackoverflow.com",
                "wikipedia.org",
            }

            self.malware_domains.update(default_malware)
            self.phishing_domains.update(default_phishing)
            self.trusted_domains.update(default_trusted)

            self.logger.info(
                "Loaded threat lists: %d malware, %d phishing, %d trusted domains", len(
                    self.malware_domains), len(
                    self.phishing_domains), len(
                    self.trusted_domains), )

        except Exception as e:
            self.logger.error("Error loading threat lists: %s", e)

    def _load_cached_threat_lists(self):
        """Load threat lists from database cache."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT domain, threat_category FROM blocked_domains
                    WHERE active = TRUE
                """
                )

                for domain, category in cursor.fetchall():
                    if category == ThreatCategory.MALWARE.value:
                        self.malware_domains.add(domain)
                    elif category == ThreatCategory.PHISHING.value:
                        self.phishing_domains.add(domain)
                    elif category == ThreatCategory.SUSPICIOUS.value:
                        self.suspicious_domains.add(domain)

        except Exception as e:
            self.logger.error("Error loading cached threat lists: %s", e)

    async def start_protection(self) -> bool:
        """Start web protection system."""
        try:
            if self.running:
                self.logger.warning("Web protection already running")
                return True

            self.running = True

            # Create HTTP session
            connector = aiohttp.TCPConnector(
                limit=100,
                ttl_dns_cache=300,
                use_dns_cache=True,
                ssl=False,  # We'll handle SSL verification manually
            )
            timeout = aiohttp.ClientTimeout(total=self.config.request_timeout)
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={"User-Agent": "S&D-WebProtection/1.0"},
            )

            # Start background update thread
            self.update_thread = threading.Thread(
                target=self._threat_intel_update_loop,
                daemon=True,
                name="WebProtectionUpdater",
            )
            self.update_thread.start()

            self.logger.info("Web protection system started")
            return True

        except Exception as e:
            self.logger.error("Failed to start web protection: %s", e)
            self.running = False
            return False

    async def stop_protection(self):
        """Stop web protection system."""
        self.running = False

        # Close HTTP session
        if self.session:
            await self.session.close()
            self.session = None

        # Wait for update thread
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=5.0)

        self.logger.info("Web protection system stopped")

    async def analyze_url(
            self,
            url: str,
            force_refresh: bool = False) -> URLAnalysis:
        """
        Analyze a URL for threats and reputation.

        Args:
            url: URL to analyze
            force_refresh: Force fresh analysis, bypass cache

        Returns:
            URLAnalysis result
        """
        try:
            start_time = time.time()

            # Normalize URL
            normalized_url = self._normalize_url(url)
            parsed = urlparse(normalized_url)
            domain = parsed.netloc.lower()

            # Check cache first
            if not force_refresh:
                cached_analysis = self._get_cached_analysis(normalized_url)
                if cached_analysis:
                    self.stats["cache_hits"] += 1
                    return cached_analysis

            self.stats["cache_misses"] += 1
            self.stats["requests_analyzed"] += 1

            # Perform analysis
            threat_indicators = []
            reputation = URLReputation.UNKNOWN
            risk_score = 0.0

            # Domain reputation check
            domain_reputation = await self._check_domain_reputation(domain)
            if domain_reputation:
                reputation = domain_reputation["reputation"]
                risk_score = domain_reputation["risk_score"]
                threat_indicators.extend(
                    domain_reputation.get(
                        "indicators", []))

            # DNS analysis
            ip_addresses = await self._resolve_domain_ips(domain)

            # SSL analysis (for HTTPS URLs)
            ssl_info = {}
            if parsed.scheme == "https":
                ssl_info = await self._analyze_ssl_certificate(domain)
                if ssl_info.get("suspicious"):
                    threat_indicators.append("suspicious_ssl")
                    risk_score = max(risk_score, 0.3)

            # URL pattern analysis
            url_patterns = self._analyze_url_patterns(normalized_url)
            if url_patterns:
                threat_indicators.extend(url_patterns)
                risk_score = max(risk_score, 0.4)

            # Blacklist checks
            blacklist_result = self._check_blacklists(domain)
            if blacklist_result:
                reputation = blacklist_result["reputation"]
                risk_score = max(risk_score, blacklist_result["risk_score"])
                threat_indicators.append(
                    f"blacklist_{blacklist_result['source']}")

            # Heuristic analysis
            if self.session and reputation == URLReputation.UNKNOWN:
                heuristic_result = await self._heuristic_url_analysis(normalized_url)
                if heuristic_result:
                    threat_indicators.extend(
                        heuristic_result.get("indicators", []))
                    risk_score = max(
                        risk_score, heuristic_result.get("risk_score", 0.0)
                    )

            # Final reputation determination
            if reputation == URLReputation.UNKNOWN:
                if risk_score >= 0.8:
                    reputation = URLReputation.MALICIOUS
                elif risk_score >= 0.5:
                    reputation = URLReputation.SUSPICIOUS
                elif risk_score >= 0.2:
                    reputation = URLReputation.UNKNOWN
                else:
                    reputation = URLReputation.SAFE

            analysis_time = time.time() - start_time

            # Create analysis result
            analysis = URLAnalysis(
                url=normalized_url,
                domain=domain,
                ip_addresses=ip_addresses,
                ssl_info=ssl_info,
                threat_indicators=threat_indicators,
                reputation=reputation,
                risk_score=risk_score,
                analysis_time=analysis_time,
                details={
                    "parsed_url": {
                        "scheme": parsed.scheme,
                        "netloc": parsed.netloc,
                        "path": parsed.path,
                        "query": parsed.query,
                    },
                    "domain_age": None,  # Could be enhanced with WHOIS lookup
                    "alexa_rank": None,  # Could be enhanced with popularity data
                },
            )

            # Cache the result
            self._cache_analysis(analysis)

            # Store in database
            self._store_analysis_result(analysis)

            return analysis

        except Exception as e:
            self.logger.error("Error analyzing URL %s: %s", url, e)
            # Return safe default
            return URLAnalysis(
                url=url,
                domain=urlparse(url).netloc,
                ip_addresses=[],
                ssl_info={},
                threat_indicators=["analysis_error"],
                reputation=URLReputation.UNKNOWN,
                risk_score=0.0,
                analysis_time=0.0,
            )

    async def check_url_safety(self, url: str) -> Tuple[bool, WebThreat]:
        """
        Check if URL is safe to visit.

        Args:
            url: URL to check

        Returns:
            Tuple of (is_safe, threat_info)
        """
        try:
            analysis = await self.analyze_url(url)

            # Determine if URL should be blocked
            should_block = False
            threat_category = None
            block_reason = ""

            # Check against configuration
            if analysis.reputation == URLReputation.MALICIOUS:
                should_block = True
                if "malware" in analysis.threat_indicators:
                    threat_category = ThreatCategory.MALWARE
                    block_reason = "Known malware domain"
                elif "phishing" in analysis.threat_indicators:
                    threat_category = ThreatCategory.PHISHING
                    block_reason = "Known phishing domain"
                else:
                    threat_category = ThreatCategory.SUSPICIOUS
                    block_reason = "Malicious reputation"

            elif analysis.reputation == URLReputation.SUSPICIOUS:
                if self.config.warn_suspicious:
                    threat_category = ThreatCategory.SUSPICIOUS
                    block_reason = "Suspicious activity detected"

                # Block suspicious if high risk score
                if analysis.risk_score >= 0.7:
                    should_block = True

            # Check custom block lists
            domain = analysis.domain
            if domain in self.config.custom_blocked_domains:
                should_block = True
                threat_category = ThreatCategory.SUSPICIOUS
                block_reason = "Custom blocked domain"

            # Check custom allow lists
            if domain in self.config.custom_allowed_domains:
                should_block = False
                threat_category = None
                block_reason = ""

            # Create threat object if threat detected
            threat = None
            if threat_category:
                threat = WebThreat(
                    url=url,
                    threat_category=threat_category,
                    reputation=analysis.reputation,
                    risk_score=analysis.risk_score,
                    detection_time=datetime.now(),
                    source="web_protection_analysis",
                    details={
                        "threat_indicators": analysis.threat_indicators,
                        "block_reason": block_reason,
                        "analysis_time": analysis.analysis_time,
                    },
                    blocked=should_block,
                )

                # Store threat detection
                self.threat_history.append(threat)
                self._store_threat_detection(threat)

                # Update statistics
                if should_block:
                    self.stats["threats_blocked"] += 1
                else:
                    self.stats["threats_warned"] += 1

                # Notify callbacks
                if self.threat_detected_callback:
                    try:
                        self.threat_detected_callback(threat)
                    except Exception as e:
                        self.logger.error(
                            "Error in threat detected callback: %s", e)

                if should_block and self.request_blocked_callback:
                    try:
                        self.request_blocked_callback(url, block_reason)
                    except Exception as e:
                        self.logger.error(
                            "Error in request blocked callback: %s", e)

            return not should_block, threat

        except Exception as e:
            self.logger.error("Error checking URL safety %s: %s", url, e)
            return True, None  # Default to safe on error

    async def _check_domain_reputation(
            self, domain: str) -> Optional[Dict[str, Any]]:
        """Check domain reputation against known threat lists."""
        try:
            # Check malware domains
            if domain in self.malware_domains:
                return {
                    "reputation": URLReputation.MALICIOUS,
                    "risk_score": 0.9,
                    "indicators": ["malware", "blacklist_malware"],
                    "source": "malware_blacklist",
                }

            # Check phishing domains
            if domain in self.phishing_domains:
                return {
                    "reputation": URLReputation.MALICIOUS,
                    "risk_score": 0.8,
                    "indicators": ["phishing", "blacklist_phishing"],
                    "source": "phishing_blacklist",
                }

            # Check suspicious domains
            if domain in self.suspicious_domains:
                return {
                    "reputation": URLReputation.SUSPICIOUS,
                    "risk_score": 0.6,
                    "indicators": ["suspicious", "blacklist_suspicious"],
                    "source": "suspicious_blacklist",
                }

            # Check trusted domains
            if domain in self.trusted_domains:
                return {
                    "reputation": URLReputation.TRUSTED,
                    "risk_score": 0.0,
                    "indicators": ["trusted"],
                    "source": "trusted_whitelist",
                }

            # Check database reputation
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT reputation, risk_score, threat_categories, source
                    FROM domain_reputation
                    WHERE domain = ? AND last_updated > datetime('now', '-7 days')
                """,
                    (domain,),
                )

                result = cursor.fetchone()

            if result:
                reputation_str, risk_score, threat_categories, source = result
                return {
                    "reputation": URLReputation(reputation_str),
                    "risk_score": risk_score,
                    "indicators": (
                        json.loads(threat_categories) if threat_categories else []),
                    "source": source,
                }

            return None

        except Exception as e:
            self.logger.error("Error checking domain reputation: %s", e)
            return None

    async def _resolve_domain_ips(self, domain: str) -> List[str]:
        """Resolve domain to IP addresses."""
        try:
            # Use custom DNS servers if configured
            resolver = dns.resolver.Resolver()
            if self.config.dns_servers:
                resolver.nameservers = self.config.dns_servers

            # Resolve A records
            ip_addresses = []
            try:
                answers = resolver.resolve(domain, "A")
                for answer in answers:
                    ip_addresses.append(str(answer))
            except dns.resolver.NXDOMAIN:
                self.logger.debug("Domain not found: %s", domain)
            except Exception as e:
                self.logger.debug("DNS resolution error for %s: %s", domain, e)

            return ip_addresses

        except Exception as e:
            self.logger.error("Error resolving domain %s: %s", domain, e)
            return []

    async def _analyze_ssl_certificate(self, domain: str) -> Dict[str, Any]:
        """Analyze SSL certificate for suspicious characteristics."""
        try:
            ssl_info = {}

            # Create SSL context
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            # Connect and get certificate
            with socket.create_connection((domain, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()

                    if cert:
                        ssl_info = {
                            "subject": dict(
                                x[0] for x in cert.get(
                                    "subject",
                                    [])),
                            "issuer": dict(
                                x[0] for x in cert.get(
                                    "issuer",
                                    [])),
                            "version": cert.get("version"),
                            "serial_number": cert.get("serialNumber"),
                            "not_before": cert.get("notBefore"),
                            "not_after": cert.get("notAfter"),
                            "subject_alt_names": [
                                x[1] for x in cert.get(
                                    "subjectAltName",
                                    [])],
                            "suspicious": False,
                        }

                        # Check for suspicious characteristics
                        issuer_cn = ssl_info.get(
                            "issuer", {}).get(
                            "commonName", "")

                        # Self-signed certificates
                        if ssl_info.get("subject") == ssl_info.get("issuer"):
                            ssl_info["suspicious"] = True
                            ssl_info["suspicious_reason"] = "self_signed"

                        # Check for suspicious issuers
                        suspicious_issuers = [
                            "fake",
                            "test",
                            "invalid",
                            "temporary",
                            "localhost",
                            "example",
                        ]

                        if any(
                            suspicious in issuer_cn.lower()
                            for suspicious in suspicious_issuers
                        ):
                            ssl_info["suspicious"] = True
                            ssl_info["suspicious_reason"] = "suspicious_issuer"

                        # Check certificate validity period
                        try:
                            from datetime import datetime

                            not_after = datetime.strptime(
                                ssl_info["not_after"], "%b %d %H:%M:%S %Y %Z"
                            )
                            not_before = datetime.strptime(
                                ssl_info["not_before"], "%b %d %H:%M:%S %Y %Z"
                            )

                            # Very short validity period (less than 30 days)
                            validity_days = (not_after - not_before).days
                            if validity_days < 30:
                                ssl_info["suspicious"] = True
                                ssl_info["suspicious_reason"] = "short_validity"

                        except Exception:
                            pass

            return ssl_info

        except Exception as e:
            self.logger.debug("SSL analysis error for %s: %s", domain, e)
            return {"error": str(e)}

    def _analyze_url_patterns(self, url: str) -> List[str]:
        """Analyze URL for suspicious patterns."""
        indicators = []

        try:
            parsed = urlparse(url)

            # Check for suspicious URL patterns
            suspicious_patterns = [
                (r"[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}",
                 "ip_address_url"),
                (r"[a-f0-9]{8,}\.",
                 "hex_subdomain"),
                (r"-{2,}",
                 "multiple_hyphens"),
                (r"\.tk$|\.ml$|\.ga$|\.cf$",
                 "suspicious_tld"),
                (r"[0-9]{4,}",
                 "numeric_subdomain"),
                (r"(secure|bank|paypal|amazon|microsoft|google|apple)-[a-z0-9]+\.",
                    "brand_impersonation",
                 ),
                (r"(login|signin|verify|confirm|update|secure).*\.(tk|ml|ga|cf|bit\.ly)",
                    "phishing_pattern",
                 ),
                (r"[a-zA-Z0-9]{20,}\.",
                 "long_random_subdomain"),
            ]

            for pattern, indicator in suspicious_patterns:
                if re.search(pattern, url, re.IGNORECASE):
                    indicators.append(indicator)

            # Check for URL shorteners
            shortener_domains = [
                "bit.ly",
                "tinyurl.com",
                "t.co",
                "goo.gl",
                "ow.ly",
                "short.link",
                "tiny.cc",
            ]

            if parsed.netloc in shortener_domains:
                indicators.append("url_shortener")

            # Check for suspicious query parameters
            if parsed.query:
                suspicious_params = ["password", "ssn", "credit_card", "pin"]
                query_lower = parsed.query.lower()

                for param in suspicious_params:
                    if param in query_lower:
                        indicators.append("suspicious_parameter")
                        break

            return indicators

        except Exception as e:
            self.logger.error("Error analyzing URL patterns: %s", e)
            return []

    def _check_blacklists(self, domain: str) -> Optional[Dict[str, Any]]:
        """Check domain against blacklists."""
        try:
            # This would integrate with external blacklist services
            # For now, check internal lists

            if domain in self.malware_domains:
                return {
                    "reputation": URLReputation.MALICIOUS,
                    "risk_score": 0.9,
                    "source": "malware_blacklist",
                }

            if domain in self.phishing_domains:
                return {
                    "reputation": URLReputation.MALICIOUS,
                    "risk_score": 0.8,
                    "source": "phishing_blacklist",
                }

            return None

        except Exception as e:
            self.logger.error("Error checking blacklists: %s", e)
            return None

    async def _heuristic_url_analysis(
            self, url: str) -> Optional[Dict[str, Any]]:
        """Perform heuristic analysis by fetching URL content."""
        try:
            if not self.session:
                return None

            indicators = []
            risk_score = 0.0

            # Fetch URL with limited content
            try:
                async with self.session.get(
                    url, allow_redirects=True, max_redirects=self.config.max_redirects
                ) as response:

                    # Check response headers
                    headers = response.headers

                    # Suspicious headers
                    if "X-Forwarded-For" in headers:
                        indicators.append("proxy_forwarded")
                        risk_score += 0.1

                    # Missing security headers
                    security_headers = [
                        "X-Frame-Options",
                        "X-Content-Type-Options",
                        "X-XSS-Protection",
                        "Strict-Transport-Security",
                    ]

                    missing_headers = sum(
                        1 for header in security_headers if header not in headers)
                    if missing_headers >= 3:
                        indicators.append("missing_security_headers")
                        risk_score += 0.2

                    # Check content type
                    content_type = headers.get("Content-Type", "").lower()
                    if "text/html" in content_type:
                        # Read limited content for analysis
                        content = await response.read(8192)  # First 8KB

                        if content:
                            content_str = content.decode(
                                "utf-8", errors="ignore"
                            ).lower()

                            # Check for suspicious content patterns
                            suspicious_patterns = [
                                ("verify your account", "phishing_language"),
                                ("suspend", "phishing_language"),
                                ("urgent action required", "phishing_language"),
                                ("click here immediately", "phishing_language"),
                                ("update payment", "phishing_language"),
                                ("confirm identity", "phishing_language"),
                                ("download now", "malware_language"),
                                ("free download", "malware_language"),
                                ("codec required", "malware_language"),
                            ]

                            for pattern, indicator in suspicious_patterns:
                                if pattern in content_str:
                                    indicators.append(indicator)
                                    risk_score += 0.3
                                    break

                            # Check for hidden elements (potential cloaking)
                            if (
                                "display:none" in content_str
                                or "visibility:hidden" in content_str
                            ):
                                indicators.append("hidden_content")
                                risk_score += 0.2

                            # Check for excessive redirects in content
                            if content_str.count("location.href") > 3:
                                indicators.append("excessive_redirects")
                                risk_score += 0.3

            except aiohttp.ClientError as e:
                self.logger.debug("HTTP error analyzing %s: %s", url, e)
                # Connection errors might indicate suspicious infrastructure
                indicators.append("connection_error")
                risk_score += 0.1

            if indicators:
                return {
                    "indicators": indicators,
                    "risk_score": min(
                        risk_score,
                        1.0)}

            return None

        except Exception as e:
            self.logger.error("Error in heuristic URL analysis: %s", e)
            return None

    def _normalize_url(self, url: str) -> str:
        """Normalize URL for consistent processing."""
        try:
            # Add scheme if missing
            if not url.startswith(("http://", "https://")):
                url = "http://" + url

            parsed = urlparse(url)

            # Normalize domain
            domain = parsed.netloc.lower()

            # Remove default ports
            if ":80" in domain and parsed.scheme == "http":
                domain = domain.replace(":80", "")
            elif ":443" in domain and parsed.scheme == "https":
                domain = domain.replace(":443", "")

            # Reconstruct URL
            normalized = f"{parsed.scheme}://{domain}{parsed.path}"
            if parsed.query:
                normalized += f"?{parsed.query}"

            return normalized

        except Exception:
            return url

    def _get_cached_analysis(self, url: str) -> Optional[URLAnalysis]:
        """Get cached URL analysis."""
        with self.lock:
            if url in self.url_cache:
                # Check if cache entry is still valid
                if url in self.cache_expiry and datetime.now(
                ) < self.cache_expiry[url]:
                    return self.url_cache[url]
                else:
                    # Remove expired entry
                    del self.url_cache[url]
                    self.cache_expiry.pop(url, None)

        return None

    def _cache_analysis(self, analysis: URLAnalysis):
        """Cache URL analysis result."""
        with self.lock:
            self.url_cache[analysis.url] = analysis
            self.cache_expiry[analysis.url] = datetime.now() + timedelta(
                hours=self.config.cache_ttl_hours
            )

            # Limit cache size
            if len(self.url_cache) > 10000:
                # Remove oldest entries
                oldest_urls = sorted(
                    self.cache_expiry.keys(),
                    key=lambda u: self.cache_expiry[u])[
                    :1000]

                for url_to_remove in oldest_urls:
                    self.url_cache.pop(url_to_remove, None)
                    self.cache_expiry.pop(url_to_remove, None)

    def _store_analysis_result(self, analysis: URLAnalysis):
        """Store analysis result in database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO url_cache
                    (url, domain, ip_addresses, ssl_info, threat_indicators,
                     reputation, risk_score, analysis_time, details)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        analysis.url,
                        analysis.domain,
                        json.dumps(analysis.ip_addresses),
                        json.dumps(analysis.ssl_info),
                        json.dumps(analysis.threat_indicators),
                        analysis.reputation.value,
                        analysis.risk_score,
                        analysis.analysis_time,
                        json.dumps(analysis.details),
                    ),
                )

                conn.commit()

        except Exception as e:
            self.logger.error("Error storing analysis result: %s", e)

    def _store_threat_detection(self, threat: WebThreat):
        """Store threat detection in database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO threat_detections
                (url, threat_category, reputation, risk_score, detection_time,
                 source, details, blocked)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    threat.url,
                    threat.threat_category.value,
                    threat.reputation.value,
                    threat.risk_score,
                    threat.detection_time.isoformat(),
                    threat.source,
                    json.dumps(threat.details),
                    threat.blocked,
                ),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            self.logger.error("Error storing threat detection: %s", e)

    def _threat_intel_update_loop(self):
        """Background thread for updating threat intelligence."""
        while self.running:
            try:
                # Update threat lists every hour
                self._update_threat_intelligence()

                # Sleep for 1 hour
                for _ in range(3600):
                    if not self.running:
                        break
                    time.sleep(1)

            except Exception as e:
                self.logger.error("Error in threat intel update loop: %s", e)
                time.sleep(300)  # Sleep 5 minutes on error

    def _update_threat_intelligence(self):
        """Update threat intelligence from feeds."""
        try:
            self.logger.info("Updating threat intelligence...")

            # This would fetch from real threat intelligence feeds
            # For now, just log the update
            updated_domains = 0

            for feed_url in self.config.threat_intelligence_feeds:
                try:
                    # Would fetch and parse threat feed
                    self.logger.debug("Would update from feed: %s", feed_url)
                    updated_domains += 1
                except Exception as e:
                    self.logger.error(
                        "Error updating from feed %s: %s", feed_url, e)

            self.logger.info(
                "Threat intelligence update completed: %d feeds processed",
                len(self.config.threat_intelligence_feeds),
            )

        except Exception as e:
            self.logger.error("Error updating threat intelligence: %s", e)

    def add_blocked_domain(
            self,
            domain: str,
            threat_category: ThreatCategory,
            source: str = "manual"):
        """Add domain to blocked list."""
        try:
            # Add to appropriate in-memory list
            if threat_category == ThreatCategory.MALWARE:
                self.malware_domains.add(domain)
            elif threat_category == ThreatCategory.PHISHING:
                self.phishing_domains.add(domain)
            else:
                self.suspicious_domains.add(domain)

            # Store in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT OR REPLACE INTO blocked_domains
                (domain, threat_category, source, active)
                VALUES (?, ?, ?, TRUE)
            """,
                (domain, threat_category.value, source),
            )

            conn.commit()
            conn.close()

            self.logger.info(
                "Added blocked domain: %s (%s)", domain, threat_category.value
            )

        except Exception as e:
            self.logger.error("Error adding blocked domain: %s", e)

    def remove_blocked_domain(self, domain: str):
        """Remove domain from blocked list."""
        try:
            # Remove from in-memory lists
            self.malware_domains.discard(domain)
            self.phishing_domains.discard(domain)
            self.suspicious_domains.discard(domain)

            # Update database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE blocked_domains
                SET active = FALSE
                WHERE domain = ?
            """,
                (domain,),
            )

            conn.commit()
            conn.close()

            self.logger.info("Removed blocked domain: %s", domain)

        except Exception as e:
            self.logger.error("Error removing blocked domain: %s", e)

    def get_protection_statistics(self) -> Dict[str, Any]:
        """Get web protection statistics."""
        try:
            with self.lock:
                stats = self.stats.copy()

            # Add additional statistics
            stats.update(
                {
                    "running": self.running,
                    "malware_domains_count": len(self.malware_domains),
                    "phishing_domains_count": len(self.phishing_domains),
                    "suspicious_domains_count": len(self.suspicious_domains),
                    "trusted_domains_count": len(self.trusted_domains),
                    "cache_size": len(self.url_cache),
                    "recent_threats_count": len(self.threat_history),
                    "active_requests": len(self.active_requests),
                }
            )

            return stats

        except Exception as e:
            self.logger.error("Error getting protection statistics: %s", e)
            return {}

    def get_recent_threats(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent threat detections."""
        recent_threats = sorted(
            self.threat_history, key=lambda t: t.detection_time, reverse=True
        )[:limit]

        return [
            {
                "url": threat.url,
                "threat_category": threat.threat_category.value,
                "reputation": threat.reputation.value,
                "risk_score": threat.risk_score,
                "detection_time": threat.detection_time.isoformat(),
                "source": threat.source,
                "blocked": threat.blocked,
                "details": threat.details,
            }
            for threat in recent_threats
        ]

    # Callback setters
    def set_threat_detected_callback(
            self, callback: Callable[[WebThreat], None]):
        """Set callback for threat detection."""
        self.threat_detected_callback = callback

    def set_request_blocked_callback(
            self, callback: Callable[[str, str], None]):
        """Set callback for blocked requests."""
        self.request_blocked_callback = callback

    def set_suspicious_activity_callback(
        self, callback: Callable[[str, Dict[str, Any]], None]
    ):
        """Set callback for suspicious activity."""
        self.suspicious_activity_callback = callback


# Add missing import for DNS
try:
    import dns.resolver
except ImportError:
    # Create a mock DNS resolver if not available
    class MockDNSResolver:
        def __init__(self):
            self.nameservers = []

        def resolve(self, domain, record_type):
            # Return empty result
            return []

    dns = type("dns", (), {})()
    dns.resolver = type("resolver", (), {})()
    dns.resolver.Resolver = MockDNSResolver
    dns.resolver.NXDOMAIN = Exception
    logging.getLogger(__name__).warning(
        "DNS resolver not available, some features may not work"
    )
