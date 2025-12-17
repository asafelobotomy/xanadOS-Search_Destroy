#!/usr/bin/env python3
"""
Static feature extraction for malware detection.

Extracts features from PE/ELF binaries without execution:
- File metadata (size, entropy)
- PE/ELF header information
- Section characteristics
- Import/export tables
- String analysis
- Byte histograms

All feature extraction is static analysis only - NO code execution.
"""

import hashlib
import math
import re
import struct
import signal
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

import numpy as np
import pefile
from elftools.elf.elffile import ELFFile


class FeatureExtractionTimeout(Exception):
    """Raised when feature extraction exceeds timeout."""

    pass


@contextmanager
def timeout(seconds: int):
    """Context manager for timing out operations.

    SECURITY: Prevents DoS via malicious files that cause infinite loops (CWE-834).

    Args:
        seconds: Maximum time allowed for the operation

    Raises:
        FeatureExtractionTimeout: If operation exceeds timeout
    """

    def timeout_handler(signum, frame):
        raise FeatureExtractionTimeout(f"Operation exceeded {seconds} second timeout")

    # Set the signal handler
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)

    try:
        yield
    finally:
        # Restore previous handler and cancel alarm
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


class FeatureExtractor:
    """Extract static features from executable files for ML training."""

    # Feature dimensions
    ENTROPY_DIM = 1
    FILE_SIZE_DIM = 1
    BYTE_HISTOGRAM_DIM = 256
    PE_HEADER_DIM = 20
    ELF_HEADER_DIM = 20
    SECTION_FEATURES_DIM = 10
    STRING_FEATURES_DIM = 10

    # Total feature dimension
    FEATURE_DIM = (
        ENTROPY_DIM
        + FILE_SIZE_DIM
        + BYTE_HISTOGRAM_DIM
        + PE_HEADER_DIM
        + ELF_HEADER_DIM
        + SECTION_FEATURES_DIM
        + STRING_FEATURES_DIM
    )  # 318 features total

    def __init__(self, max_file_size: int = 100 * 1024 * 1024):
        """
        Initialize feature extractor.

        Args:
            max_file_size: Maximum file size to process (default: 100MB)
        """
        self.max_file_size = max_file_size

    def extract(self, file_path: Path) -> Optional[np.ndarray]:
        """
        Extract features from a file.

        Args:
            file_path: Path to executable file

        Returns:
            Feature vector as numpy array (318 dimensions) or None if extraction fails
        """
        return self.extract_features(file_path)

    def extract_features(self, file_path: Path) -> Optional[np.ndarray]:
        """
        Extract features from a file (main implementation).

        Args:
            file_path: Path to executable file

        Returns:
            Feature vector as numpy array (318 dimensions) or None if extraction fails
        """
        try:
            # SECURITY: Wrap all parsing with 60-second timeout (CWE-834 mitigation)
            with timeout(60):
                return self._extract_features_impl(file_path)
        except FeatureExtractionTimeout as e:
            print(f"[red]⏱️  Timeout extracting features from {file_path}: {e}")
            return None
        except Exception as e:
            print(f"[red]❌ Error extracting features from {file_path}: {e}")
            return None

    def _extract_features_impl(self, file_path: Path) -> Optional[np.ndarray]:
        """
        Internal feature extraction implementation (called with timeout wrapper).

        Args:
            file_path: Path to executable file

        Returns:
            Feature vector as numpy array (318 dimensions) or None if extraction fails
        """
        try:
            # Read file content
            content = file_path.read_bytes()

            # Size check
            if len(content) > self.max_file_size:
                return None

            # Initialize feature vector
            features = np.zeros(self.FEATURE_DIM, dtype=np.float32)

            # Extract features
            idx = 0

            # 1. Entropy (1 feature)
            features[idx] = self._calculate_entropy(content)
            idx += self.ENTROPY_DIM

            # 2. File size (1 feature, log-scaled)
            features[idx] = math.log10(len(content) + 1)
            idx += self.FILE_SIZE_DIM

            # 3. Byte histogram (256 features, normalized)
            hist = self._byte_histogram(content)
            features[idx : idx + self.BYTE_HISTOGRAM_DIM] = hist
            idx += self.BYTE_HISTOGRAM_DIM

            # 4. PE header features (20 features)
            if content.startswith(b"MZ"):  # PE file
                pe_features = self._extract_pe_features(content)
                features[idx : idx + self.PE_HEADER_DIM] = pe_features
            idx += self.PE_HEADER_DIM

            # 5. ELF header features (20 features)
            if content.startswith(b"\x7fELF"):  # ELF file
                elf_features = self._extract_elf_features(file_path)
                features[idx : idx + self.ELF_HEADER_DIM] = elf_features
            idx += self.ELF_HEADER_DIM

            # 6. Section features (10 features)
            section_features = self._extract_section_features(content)
            features[idx : idx + self.SECTION_FEATURES_DIM] = section_features
            idx += self.SECTION_FEATURES_DIM

            # 7. String features (10 features)
            string_features = self._extract_string_features(content)
            features[idx : idx + self.STRING_FEATURES_DIM] = string_features

            return features

        except Exception as e:
            # Log error but don't crash
            print(f"⚠️  Feature extraction failed for {file_path.name}: {e}")
            return None

    def _calculate_entropy(self, data: bytes) -> float:
        """
        Calculate Shannon entropy of data.

        Higher entropy indicates more randomness (common in packed/encrypted malware).

        Args:
            data: Byte sequence

        Returns:
            Entropy value (0-8, where 8 is maximum randomness)
        """
        if not data:
            return 0.0

        # Calculate byte frequency
        byte_counts = np.bincount(np.frombuffer(data, dtype=np.uint8), minlength=256)
        probabilities = byte_counts / len(data)

        # Remove zero probabilities
        probabilities = probabilities[probabilities > 0]

        # Calculate entropy
        entropy = -np.sum(probabilities * np.log2(probabilities))

        return float(entropy)

    def _byte_histogram(self, data: bytes) -> np.ndarray:
        """
        Calculate normalized byte histogram.

        Args:
            data: Byte sequence

        Returns:
            Normalized histogram (256 bins, sum to 1.0)
        """
        if not data:
            return np.zeros(256, dtype=np.float32)

        # Count byte frequencies
        hist = np.bincount(np.frombuffer(data, dtype=np.uint8), minlength=256)

        # Normalize
        hist = hist.astype(np.float32) / len(data)

        return hist

    def _extract_pe_features(self, content: bytes) -> np.ndarray:
        """
        Extract features from PE (Windows) executable.

        Features:
        - Number of sections
        - Timestamp
        - Size of optional header
        - Number of imports
        - Number of exports
        - Entry point address
        - Image base
        - Section alignment
        - File alignment
        - Subsystem
        - DLL characteristics
        - Size of code
        - Size of initialized data
        - Size of uninitialized data
        - Size of image
        - Size of headers
        - Checksum
        - Number of RVA and sizes
        - Has debug info
        - Is DLL

        Args:
            content: PE file bytes

        Returns:
            PE feature vector (20 dimensions)
        """
        features = np.zeros(self.PE_HEADER_DIM, dtype=np.float32)

        try:
            pe = pefile.PE(data=content, fast_load=True)

            # File header
            features[0] = pe.FILE_HEADER.NumberOfSections
            features[1] = pe.FILE_HEADER.TimeDateStamp
            features[2] = pe.FILE_HEADER.SizeOfOptionalHeader

            # Optional header (if exists)
            if hasattr(pe, "OPTIONAL_HEADER"):
                oh = pe.OPTIONAL_HEADER
                features[3] = oh.AddressOfEntryPoint
                features[4] = oh.ImageBase
                features[5] = oh.SectionAlignment
                features[6] = oh.FileAlignment
                features[7] = oh.Subsystem
                features[8] = oh.DllCharacteristics
                features[9] = oh.SizeOfCode
                features[10] = oh.SizeOfInitializedData
                features[11] = oh.SizeOfUninitializedData
                features[12] = oh.SizeOfImage
                features[13] = oh.SizeOfHeaders
                features[14] = oh.CheckSum
                features[15] = oh.NumberOfRvaAndSizes

            # Import/export counts
            features[16] = (
                len(pe.DIRECTORY_ENTRY_IMPORT)
                if hasattr(pe, "DIRECTORY_ENTRY_IMPORT")
                else 0
            )
            features[17] = (
                len(pe.DIRECTORY_ENTRY_EXPORT.symbols)
                if hasattr(pe, "DIRECTORY_ENTRY_EXPORT")
                else 0
            )

            # Boolean flags
            features[18] = 1.0 if hasattr(pe, "DIRECTORY_ENTRY_DEBUG") else 0.0
            features[19] = 1.0 if pe.is_dll() else 0.0

            pe.close()

        except Exception:
            # PE parsing failed, return zeros
            pass

        return features

    def _extract_elf_features(self, file_path: Path) -> np.ndarray:
        """
        Extract features from ELF (Linux) executable.

        Features:
        - ELF class (32/64 bit)
        - Data encoding (endianness)
        - Machine type
        - Entry point
        - Program header count
        - Section header count
        - String table index
        - Number of segments
        - Number of sections
        - Has dynamic section
        - Has symbol table
        - Has relocation
        - Is executable
        - Is shared object
        - Number of imported symbols
        - Number of exported symbols
        - Text section size
        - Data section size
        - BSS section size
        - Has stack executable flag

        Args:
            file_path: Path to ELF file

        Returns:
            ELF feature vector (20 dimensions)
        """
        features = np.zeros(self.ELF_HEADER_DIM, dtype=np.float32)

        try:
            with file_path.open("rb") as f:
                elf = ELFFile(f)

                # Header
                features[0] = 64.0 if elf.elfclass == 64 else 32.0
                features[1] = 1.0 if elf.little_endian else 0.0
                features[2] = elf["e_machine"]
                features[3] = elf["e_entry"]
                features[4] = elf["e_phnum"]
                features[5] = elf["e_shnum"]
                features[6] = elf["e_shstrndx"]

                # Sections
                features[7] = len(list(elf.iter_segments()))
                features[8] = len(list(elf.iter_sections()))

                # Section types
                has_dynamic = any(s.name == ".dynamic" for s in elf.iter_sections())
                has_symtab = any(s.name == ".symtab" for s in elf.iter_sections())
                has_rela = any(".rela" in s.name for s in elf.iter_sections())

                features[9] = 1.0 if has_dynamic else 0.0
                features[10] = 1.0 if has_symtab else 0.0
                features[11] = 1.0 if has_rela else 0.0

                # File type
                features[12] = 1.0 if elf["e_type"] == "ET_EXEC" else 0.0
                features[13] = 1.0 if elf["e_type"] == "ET_DYN" else 0.0

                # Symbol counts (approximate)
                symtab_section = elf.get_section_by_name(".symtab")
                if symtab_section:
                    features[14] = symtab_section.num_symbols()

                dynsym_section = elf.get_section_by_name(".dynsym")
                if dynsym_section:
                    features[15] = dynsym_section.num_symbols()

                # Section sizes
                text_section = elf.get_section_by_name(".text")
                if text_section:
                    features[16] = text_section["sh_size"]

                data_section = elf.get_section_by_name(".data")
                if data_section:
                    features[17] = data_section["sh_size"]

                bss_section = elf.get_section_by_name(".bss")
                if bss_section:
                    features[18] = bss_section["sh_size"]

                # Security flags
                for segment in elf.iter_segments():
                    if segment["p_type"] == "PT_GNU_STACK":
                        features[19] = 1.0 if segment["p_flags"] & 0x1 else 0.0
                        break

        except Exception:
            # ELF parsing failed, return zeros
            pass

        return features

    def _extract_section_features(self, content: bytes) -> np.ndarray:
        """
        Extract section-based features (generic, works for both PE and ELF).

        Features:
        - Average section entropy
        - Max section entropy
        - Min section entropy
        - Entropy variance
        - Number of high-entropy sections (>7.0)
        - Number of low-entropy sections (<3.0)
        - Total sections detected
        - Packing indicator (high entropy + low section count)
        - Code section ratio
        - Data section ratio

        Args:
            content: File bytes

        Returns:
            Section feature vector (10 dimensions)
        """
        features = np.zeros(self.SECTION_FEATURES_DIM, dtype=np.float32)

        try:
            # Split file into chunks and calculate entropy per chunk
            chunk_size = 4096
            num_chunks = len(content) // chunk_size

            if num_chunks == 0:
                return features

            entropies = []
            for i in range(num_chunks):
                chunk = content[i * chunk_size : (i + 1) * chunk_size]
                entropy = self._calculate_entropy(chunk)
                entropies.append(entropy)

            entropies = np.array(entropies)

            features[0] = np.mean(entropies)
            features[1] = np.max(entropies)
            features[2] = np.min(entropies)
            features[3] = np.var(entropies)
            features[4] = np.sum(entropies > 7.0)
            features[5] = np.sum(entropies < 3.0)
            features[6] = float(num_chunks)

            # Packing indicator
            features[7] = 1.0 if (np.mean(entropies) > 7.0 and num_chunks < 10) else 0.0

            # Section type ratios (approximate)
            high_entropy_ratio = np.sum(entropies > 6.0) / num_chunks
            low_entropy_ratio = np.sum(entropies < 4.0) / num_chunks

            features[8] = high_entropy_ratio
            features[9] = low_entropy_ratio

        except Exception:
            pass

        return features

    def _extract_string_features(self, content: bytes) -> np.ndarray:
        """
        Extract string-based features.

        Features:
        - Number of printable strings
        - Average string length
        - Max string length
        - Number of suspicious strings (URL, IP, registry, etc.)
        - Number of API calls detected
        - Number of file paths
        - Number of URLs
        - Number of IP addresses
        - String entropy (average)
        - Number of obfuscated strings (high entropy)

        Args:
            content: File bytes

        Returns:
            String feature vector (10 dimensions)
        """
        features = np.zeros(self.STRING_FEATURES_DIM, dtype=np.float32)

        try:
            # Extract printable strings (min length 4)
            strings = re.findall(b"[ -~]{4,}", content)

            if not strings:
                return features

            features[0] = len(strings)

            # String length statistics
            lengths = [len(s) for s in strings]
            features[1] = np.mean(lengths)
            features[2] = max(lengths)

            # Convert to text for pattern matching
            text_strings = [s.decode("ascii", errors="ignore") for s in strings]
            full_text = " ".join(text_strings)

            # Suspicious patterns
            url_pattern = r"https?://|www\."
            ip_pattern = r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"
            registry_pattern = r"HKEY_|SOFTWARE\\|CurrentVersion"
            api_pattern = r"(Create|Open|Read|Write|Delete|Execute|Load|Get|Set)(File|Process|Thread|Registry|Service)"

            features[3] = len(re.findall(url_pattern, full_text, re.IGNORECASE))
            features[4] = len(re.findall(api_pattern, full_text))
            features[5] = len(re.findall(r"[A-Z]:\\\\|/usr/|/etc/|/var/", full_text))
            features[6] = len(re.findall(url_pattern, full_text))
            features[7] = len(re.findall(ip_pattern, full_text))

            # String entropy (for obfuscation detection)
            string_entropies = [
                self._calculate_entropy(s) for s in strings[:100]
            ]  # Sample first 100
            if string_entropies:
                features[8] = np.mean(string_entropies)
                features[9] = sum(1 for e in string_entropies if e > 4.0)

        except Exception:
            pass

        return features


def get_feature_names() -> list[str]:
    """
    Get human-readable feature names for interpretability.

    Returns:
        List of feature names (318 total)
    """
    names = []

    # Entropy
    names.append("entropy")

    # File size
    names.append("file_size_log")

    # Byte histogram
    names.extend([f"byte_hist_{i}" for i in range(256)])

    # PE features
    pe_names = [
        "pe_num_sections",
        "pe_timestamp",
        "pe_opt_header_size",
        "pe_entry_point",
        "pe_image_base",
        "pe_section_align",
        "pe_file_align",
        "pe_subsystem",
        "pe_dll_characteristics",
        "pe_size_code",
        "pe_size_init_data",
        "pe_size_uninit_data",
        "pe_size_image",
        "pe_size_headers",
        "pe_checksum",
        "pe_num_rva",
        "pe_num_imports",
        "pe_num_exports",
        "pe_has_debug",
        "pe_is_dll",
    ]
    names.extend(pe_names)

    # ELF features
    elf_names = [
        "elf_class",
        "elf_endian",
        "elf_machine",
        "elf_entry",
        "elf_phnum",
        "elf_shnum",
        "elf_shstrndx",
        "elf_num_segments",
        "elf_num_sections",
        "elf_has_dynamic",
        "elf_has_symtab",
        "elf_has_rela",
        "elf_is_exec",
        "elf_is_so",
        "elf_num_symbols",
        "elf_num_dynsyms",
        "elf_text_size",
        "elf_data_size",
        "elf_bss_size",
        "elf_stack_exec",
    ]
    names.extend(elf_names)

    # Section features
    section_names = [
        "section_avg_entropy",
        "section_max_entropy",
        "section_min_entropy",
        "section_entropy_var",
        "section_high_entropy_count",
        "section_low_entropy_count",
        "section_total_count",
        "section_packing_indicator",
        "section_high_entropy_ratio",
        "section_low_entropy_ratio",
    ]
    names.extend(section_names)

    # String features
    string_names = [
        "string_count",
        "string_avg_length",
        "string_max_length",
        "string_url_count",
        "string_api_count",
        "string_path_count",
        "string_url_pattern_count",
        "string_ip_count",
        "string_avg_entropy",
        "string_obfuscated_count",
    ]
    names.extend(string_names)

    return names
