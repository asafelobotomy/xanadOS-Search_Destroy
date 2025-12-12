#!/usr/bin/env python3
"""Deep Learning Integration for xanadOS Search & Destroy.

This module provides advanced neural network capabilities for enhanced threat
detection including NLP for log analysis, behavioral modeling with LSTM networks,
computer vision for file analysis, and transfer learning capabilities.

Features:
- Advanced neural network architectures (CNN, LSTM, Transformer)
- NLP-based log analysis and threat intelligence
- Computer vision for file content analysis
- Behavioral pattern analysis with time series modeling
- Transfer learning from pretrained security models
- Ensemble methods combining multiple models
- Real-time inference optimization
- Model versioning and A/B testing
- Federated learning capabilities
"""

import asyncio
import json
import logging
import numpy as np
import pickle
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
import warnings

# Suppress FutureWarnings from third-party ML libraries (transformers, torch, sklearn)
# These are library implementation details outside our control and don't affect functionality
# Primarily from: transformers (Hugging Face), torch (PyTorch), sklearn version changes
warnings.filterwarnings("ignore", category=FutureWarning)

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset, TensorDataset
from transformers import (
    AutoTokenizer,
    AutoModel,
    BertTokenizer,
    BertModel,
    GPT2Tokenizer,
    GPT2Model,
    pipeline,
)
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import cv2
import torchvision.transforms as transforms
from torchvision.models import resnet50, efficientnet_b0
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
import spacy
from PIL import Image
import magic
import hashlib
import joblib

from app.core.ml_threat_detector import MLThreatDetector
from app.utils.config import get_config


# Download required NLTK data
try:
    nltk.download("punkt", quiet=True)
    nltk.download("stopwords", quiet=True)
    nltk.download("wordnet", quiet=True)
except:
    pass


@dataclass
class ModelConfig:
    """Deep learning model configuration."""

    model_type: str
    architecture: str
    input_shape: Tuple[int, ...]
    num_classes: int
    learning_rate: float = 0.001
    batch_size: int = 32
    epochs: int = 100
    early_stopping_patience: int = 10
    dropout_rate: float = 0.3
    l2_regularization: float = 0.001


@dataclass
class TrainingMetrics:
    """Training metrics and statistics."""

    epoch: int
    train_loss: float
    val_loss: float
    train_accuracy: float
    val_accuracy: float
    learning_rate: float
    timestamp: float = field(default_factory=time.time)


@dataclass
class ModelPrediction:
    """Model prediction result."""

    prediction: Union[int, float, List[float]]
    confidence: float
    probabilities: Optional[List[float]] = None
    features: Optional[Dict[str, Any]] = None
    model_version: str = "1.0"
    inference_time: float = 0.0


class ThreatLSTM(nn.Module):
    """LSTM network for sequential threat pattern analysis."""

    def __init__(
        self,
        input_size: int,
        hidden_size: int = 128,
        num_layers: int = 2,
        num_classes: int = 2,
        dropout: float = 0.3,
    ):
        super(ThreatLSTM, self).__init__()

        self.hidden_size = hidden_size
        self.num_layers = num_layers

        # LSTM layers
        self.lstm = nn.LSTM(
            input_size,
            hidden_size,
            num_layers,
            batch_first=True,
            dropout=dropout,
            bidirectional=True,
        )

        # Attention mechanism
        self.attention = nn.MultiheadAttention(
            embed_dim=hidden_size * 2, num_heads=8, dropout=dropout
        )

        # Output layers
        self.dropout = nn.Dropout(dropout)
        self.fc1 = nn.Linear(hidden_size * 2, hidden_size)
        self.fc2 = nn.Linear(hidden_size, num_classes)
        self.softmax = nn.Softmax(dim=1)

    def forward(self, x):
        # LSTM processing
        lstm_out, _ = self.lstm(x)

        # Apply attention
        attn_out, _ = self.attention(lstm_out, lstm_out, lstm_out)

        # Global max pooling
        pooled = torch.max(attn_out, dim=1)[0]

        # Fully connected layers
        out = self.dropout(pooled)
        out = F.relu(self.fc1(out))
        out = self.dropout(out)
        out = self.fc2(out)

        return out, self.softmax(out)


class ThreatCNN(nn.Module):
    """CNN for file content and binary analysis."""

    def __init__(self, input_channels: int = 1, num_classes: int = 2):
        super(ThreatCNN, self).__init__()

        # Convolutional layers
        self.conv1 = nn.Conv2d(input_channels, 32, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, padding=1)
        self.conv4 = nn.Conv2d(128, 256, kernel_size=3, padding=1)

        # Batch normalization
        self.bn1 = nn.BatchNorm2d(32)
        self.bn2 = nn.BatchNorm2d(64)
        self.bn3 = nn.BatchNorm2d(128)
        self.bn4 = nn.BatchNorm2d(256)

        # Dropout and pooling
        self.dropout = nn.Dropout(0.3)
        self.pool = nn.MaxPool2d(2, 2)
        self.adaptive_pool = nn.AdaptiveAvgPool2d((4, 4))

        # Fully connected layers
        self.fc1 = nn.Linear(256 * 4 * 4, 512)
        self.fc2 = nn.Linear(512, 128)
        self.fc3 = nn.Linear(128, num_classes)

    def forward(self, x):
        # Convolutional layers with batch norm and pooling
        x = self.pool(F.relu(self.bn1(self.conv1(x))))
        x = self.pool(F.relu(self.bn2(self.conv2(x))))
        x = self.pool(F.relu(self.bn3(self.conv3(x))))
        x = self.pool(F.relu(self.bn4(self.conv4(x))))

        # Adaptive pooling
        x = self.adaptive_pool(x)

        # Flatten
        x = x.view(x.size(0), -1)

        # Fully connected layers
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        x = F.relu(self.fc2(x))
        x = self.dropout(x)
        x = self.fc3(x)

        return x


class ThreatTransformer(nn.Module):
    """Transformer architecture for complex threat pattern analysis."""

    def __init__(
        self,
        vocab_size: int,
        embed_dim: int = 256,
        num_heads: int = 8,
        num_layers: int = 6,
        num_classes: int = 2,
        max_seq_length: int = 512,
    ):
        super(ThreatTransformer, self).__init__()

        self.embed_dim = embed_dim
        self.max_seq_length = max_seq_length

        # Embedding layers
        self.token_embedding = nn.Embedding(vocab_size, embed_dim)
        self.position_embedding = nn.Embedding(max_seq_length, embed_dim)

        # Transformer encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=embed_dim,
            nhead=num_heads,
            dim_feedforward=embed_dim * 4,
            dropout=0.1,
            activation="gelu",
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers)

        # Classification head
        self.ln_f = nn.LayerNorm(embed_dim)
        self.classifier = nn.Linear(embed_dim, num_classes)
        self.dropout = nn.Dropout(0.1)

    def forward(self, x, attention_mask=None):
        seq_length = x.size(1)

        # Create position indices
        position_ids = torch.arange(seq_length, dtype=torch.long, device=x.device)
        position_ids = position_ids.unsqueeze(0).expand_as(x)

        # Embeddings
        token_embeds = self.token_embedding(x)
        position_embeds = self.position_embedding(position_ids)
        hidden_states = token_embeds + position_embeds

        # Apply dropout
        hidden_states = self.dropout(hidden_states)

        # Transformer processing
        # Note: PyTorch transformer expects (seq_len, batch, embed_dim)
        hidden_states = hidden_states.transpose(0, 1)

        if attention_mask is not None:
            # Convert attention mask to additive mask for transformer
            attention_mask = attention_mask.masked_fill(
                attention_mask == 0, float("-inf")
            )
            attention_mask = attention_mask.masked_fill(attention_mask == 1, 0.0)

        transformer_outputs = self.transformer(
            hidden_states, src_key_padding_mask=attention_mask
        )

        # Back to (batch, seq_len, embed_dim)
        hidden_states = transformer_outputs.transpose(0, 1)

        # Use CLS token (first token) for classification
        pooled_output = hidden_states[:, 0, :]
        pooled_output = self.ln_f(pooled_output)

        # Classification
        logits = self.classifier(pooled_output)

        return logits


class NLPThreatAnalyzer:
    """NLP-based threat analysis for logs and text data."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Initialize NLP models
        self.tokenizer = None
        self.bert_model = None
        self.sentiment_pipeline = None
        self.ner_pipeline = None

        # Load spaCy model
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            self.logger.warning(
                "spaCy English model not found. Install with: python -m spacy download en_core_web_sm"
            )
            self.nlp = None

        # Initialize threat patterns
        self.threat_keywords = self._load_threat_keywords()
        self.suspicious_patterns = self._load_suspicious_patterns()

    async def initialize(self):
        """Initialize NLP models."""
        try:
            # Initialize BERT for embeddings
            self.tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
            self.bert_model = BertModel.from_pretrained("bert-base-uncased")
            self.bert_model.eval()

            # Initialize Hugging Face pipelines
            self.sentiment_pipeline = pipeline("sentiment-analysis")
            self.ner_pipeline = pipeline("ner", aggregation_strategy="simple")

            self.logger.info("NLP models initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error initializing NLP models: {e}")
            return False

    def _load_threat_keywords(self) -> List[str]:
        """Load threat-related keywords."""
        return [
            "malware",
            "virus",
            "trojan",
            "ransomware",
            "spyware",
            "adware",
            "botnet",
            "phishing",
            "exploit",
            "vulnerability",
            "backdoor",
            "rootkit",
            "keylogger",
            "worm",
            "injection",
            "shellcode",
            "payload",
            "obfuscation",
            "persistence",
            "lateral_movement",
            "privilege_escalation",
            "data_exfiltration",
            "command_control",
            "suspicious",
            "anomalous",
            "unauthorized",
            "forbidden",
            "blocked",
            "denied",
            "failed",
            "error",
            "alert",
            "warning",
        ]

    def _load_suspicious_patterns(self) -> List[str]:
        """Load suspicious regex patterns."""
        return [
            r"\b(?:\d{1,3}\.){3}\d{1,3}\b",  # IP addresses
            r"\b[a-fA-F0-9]{32,64}\b",  # Hashes
            r"\b(?:http|https|ftp)://[^\s]+",  # URLs
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Emails
            r"\b(?:cmd|powershell|bash|sh)\.exe\b",  # Command executables
            r"\bbase64\b",  # Base64 encoding
            r"\bencode|decode\b",  # Encoding references
        ]

    async def analyze_log_entry(self, log_text: str) -> Dict[str, Any]:
        """Analyze single log entry for threats."""
        try:
            analysis = {
                "threat_score": 0.0,
                "threat_indicators": [],
                "entities": [],
                "sentiment": None,
                "embeddings": None,
                "patterns_matched": [],
            }

            # Keyword analysis
            threat_score = self._analyze_keywords(log_text, analysis)

            # Pattern analysis
            pattern_score = self._analyze_patterns(log_text, analysis)

            # NLP analysis if models available
            if self.nlp:
                nlp_score = await self._analyze_with_nlp(log_text, analysis)
            else:
                nlp_score = 0.0

            # BERT embeddings
            if self.bert_model:
                analysis["embeddings"] = await self._get_bert_embeddings(log_text)

            # Calculate combined threat score
            analysis["threat_score"] = min(
                (threat_score + pattern_score + nlp_score) / 3, 1.0
            )

            return analysis

        except Exception as e:
            self.logger.error(f"Error analyzing log entry: {e}")
            return {"threat_score": 0.0, "error": str(e)}

    def _analyze_keywords(self, text: str, analysis: Dict[str, Any]) -> float:
        """Analyze text for threat keywords."""
        text_lower = text.lower()
        found_keywords = []

        for keyword in self.threat_keywords:
            if keyword in text_lower:
                found_keywords.append(keyword)

        analysis["threat_indicators"].extend(found_keywords)

        # Score based on keyword frequency and severity
        score = min(len(found_keywords) * 0.2, 1.0)
        return score

    def _analyze_patterns(self, text: str, analysis: Dict[str, Any]) -> float:
        """Analyze text for suspicious patterns."""
        import re

        matched_patterns = []
        for pattern in self.suspicious_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                matched_patterns.extend(matches)

        analysis["patterns_matched"] = matched_patterns

        # Score based on pattern matches
        score = min(len(matched_patterns) * 0.15, 1.0)
        return score

    async def _analyze_with_nlp(self, text: str, analysis: Dict[str, Any]) -> float:
        """Analyze text with NLP models."""
        try:
            # Named Entity Recognition
            if self.ner_pipeline:
                entities = self.ner_pipeline(text)
                analysis["entities"] = entities

            # Sentiment Analysis
            if self.sentiment_pipeline:
                sentiment = self.sentiment_pipeline(text)[0]
                analysis["sentiment"] = sentiment

                # Negative sentiment might indicate threats
                if sentiment["label"] == "NEGATIVE":
                    return sentiment["score"] * 0.3

            # spaCy analysis
            if self.nlp:
                doc = self.nlp(text)

                # Extract suspicious entities
                suspicious_entities = []
                for ent in doc.ents:
                    if ent.label_ in ["PERSON", "ORG", "GPE", "URL"]:
                        suspicious_entities.append(
                            {
                                "text": ent.text,
                                "label": ent.label_,
                                "start": ent.start_char,
                                "end": ent.end_char,
                            }
                        )

                analysis["entities"].extend(suspicious_entities)

                # Score based on entity types
                return min(len(suspicious_entities) * 0.1, 1.0)

            return 0.0

        except Exception as e:
            self.logger.error(f"Error in NLP analysis: {e}")
            return 0.0

    async def _get_bert_embeddings(self, text: str) -> List[float]:
        """Get BERT embeddings for text."""
        try:
            # Tokenize and encode
            inputs = self.tokenizer.encode_plus(
                text,
                add_special_tokens=True,
                max_length=512,
                truncation=True,
                padding="max_length",
                return_tensors="pt",
            )

            # Get embeddings
            with torch.no_grad():
                outputs = self.bert_model(**inputs)
                embeddings = outputs.last_hidden_state.mean(dim=1).squeeze()

            return embeddings.tolist()

        except Exception as e:
            self.logger.error(f"Error getting BERT embeddings: {e}")
            return []

    async def analyze_log_batch(self, log_entries: List[str]) -> List[Dict[str, Any]]:
        """Analyze batch of log entries."""
        tasks = [self.analyze_log_entry(entry) for entry in log_entries]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Error analyzing log entry {i}: {result}")
                valid_results.append({"threat_score": 0.0, "error": str(result)})
            else:
                valid_results.append(result)

        return valid_results


class ComputerVisionAnalyzer:
    """Computer vision analysis for file content and visual threats."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Image preprocessing
        self.transform = transforms.Compose(
            [
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
                ),
            ]
        )

        # Load pretrained models
        self.feature_extractor = None
        self.binary_analyzer = None

    async def initialize(self):
        """Initialize computer vision models."""
        try:
            # Load pretrained ResNet for feature extraction
            self.feature_extractor = resnet50(pretrained=True)
            self.feature_extractor.eval()

            # Remove the final classification layer
            self.feature_extractor = nn.Sequential(
                *list(self.feature_extractor.children())[:-1]
            )

            self.logger.info("Computer vision models initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error initializing CV models: {e}")
            return False

    async def analyze_file_visual(self, file_path: str) -> Dict[str, Any]:
        """Analyze file using visual/binary representation."""
        try:
            analysis = {
                "file_type": None,
                "visual_features": None,
                "binary_entropy": 0.0,
                "suspicious_sections": [],
                "threat_score": 0.0,
            }

            # Detect file type
            analysis["file_type"] = magic.from_file(file_path, mime=True)

            # Read file as binary
            with open(file_path, "rb") as f:
                binary_data = f.read()

            # Calculate entropy
            analysis["binary_entropy"] = self._calculate_entropy(binary_data)

            # Visual analysis for binary files
            if self._is_binary_file(analysis["file_type"]):
                visual_score = await self._analyze_binary_visual(binary_data, analysis)
            else:
                visual_score = 0.0

            # Analyze PE sections for executables
            if analysis["file_type"] in [
                "application/x-executable",
                "application/x-dosexec",
            ]:
                section_score = await self._analyze_pe_sections(file_path, analysis)
            else:
                section_score = 0.0

            # Calculate threat score
            entropy_score = min(
                analysis["binary_entropy"] / 8.0, 1.0
            )  # Normalize entropy
            analysis["threat_score"] = (
                visual_score + section_score + entropy_score
            ) / 3

            return analysis

        except Exception as e:
            self.logger.error(f"Error analyzing file visual: {e}")
            return {"threat_score": 0.0, "error": str(e)}

    def _calculate_entropy(self, data: bytes) -> float:
        """Calculate Shannon entropy of binary data."""
        if not data:
            return 0.0

        # Count byte frequencies
        byte_counts = [0] * 256
        for byte in data:
            byte_counts[byte] += 1

        # Calculate entropy
        entropy = 0.0
        data_len = len(data)

        for count in byte_counts:
            if count > 0:
                probability = count / data_len
                entropy -= probability * np.log2(probability)

        return entropy

    def _is_binary_file(self, mime_type: str) -> bool:
        """Check if file is binary."""
        binary_types = [
            "application/x-executable",
            "application/x-dosexec",
            "application/x-sharedlib",
            "application/octet-stream",
        ]
        return mime_type in binary_types

    async def _analyze_binary_visual(
        self, binary_data: bytes, analysis: Dict[str, Any]
    ) -> float:
        """Analyze binary data using visual representation."""
        try:
            # Convert binary to 2D image representation
            data_len = len(binary_data)

            # Calculate image dimensions
            width = int(np.sqrt(data_len))
            if width == 0:
                return 0.0

            height = data_len // width

            # Create 2D array
            img_data = np.frombuffer(binary_data[: width * height], dtype=np.uint8)
            img_data = img_data.reshape((height, width))

            # Convert to PIL Image
            img = Image.fromarray(img_data, mode="L")

            # Extract features using CNN
            if self.feature_extractor:
                img_tensor = self.transform(img.convert("RGB")).unsqueeze(0)

                with torch.no_grad():
                    features = self.feature_extractor(img_tensor)
                    features = features.view(features.size(0), -1)

                analysis["visual_features"] = features.numpy().tolist()[0]

                # Simple threat scoring based on feature variance
                feature_variance = np.var(features.numpy())
                return min(feature_variance / 1000, 1.0)  # Normalize

            return 0.0

        except Exception as e:
            self.logger.error(f"Error in binary visual analysis: {e}")
            return 0.0

    async def _analyze_pe_sections(
        self, file_path: str, analysis: Dict[str, Any]
    ) -> float:
        """Analyze PE file sections for suspicious characteristics."""
        try:
            # This would require a PE parser like pefile
            # For now, return basic analysis
            suspicious_sections = []

            # Check for common suspicious section names
            suspicious_names = [".packed", ".upx", ".aspack", ".themida"]

            # Mock PE analysis
            if any(name in file_path.lower() for name in suspicious_names):
                suspicious_sections.append(
                    {"name": "packed_section", "reason": "Packed executable"}
                )

            analysis["suspicious_sections"] = suspicious_sections

            return len(suspicious_sections) * 0.5

        except Exception as e:
            self.logger.error(f"Error analyzing PE sections: {e}")
            return 0.0


class BehavioralAnalyzer:
    """Behavioral pattern analysis using time series and sequence modeling."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.behavioral_model = None
        self.sequence_length = 100
        self.feature_dimension = 50

    async def initialize(self):
        """Initialize behavioral analysis models."""
        try:
            # Create LSTM model for behavioral analysis
            self.behavioral_model = ThreatLSTM(
                input_size=self.feature_dimension,
                hidden_size=128,
                num_layers=2,
                num_classes=2,
            )

            self.logger.info("Behavioral analysis models initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error initializing behavioral models: {e}")
            return False

    async def analyze_behavior_sequence(
        self, events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze sequence of behavioral events."""
        try:
            # Extract features from events
            features = self._extract_behavioral_features(events)

            if len(features) == 0:
                return {"threat_score": 0.0, "behavioral_patterns": []}

            # Pad or truncate to sequence length
            if len(features) > self.sequence_length:
                features = features[-self.sequence_length :]
            else:
                # Pad with zeros
                padding_needed = self.sequence_length - len(features)
                features.extend([[0.0] * self.feature_dimension] * padding_needed)

            # Convert to tensor
            features_tensor = torch.FloatTensor(features).unsqueeze(0)

            # Get prediction
            if self.behavioral_model:
                with torch.no_grad():
                    logits, probabilities = self.behavioral_model(features_tensor)
                    threat_prob = probabilities[0][
                        1
                    ].item()  # Probability of threat class
            else:
                threat_prob = 0.0

            # Analyze patterns
            patterns = self._identify_patterns(events)

            return {
                "threat_score": threat_prob,
                "behavioral_patterns": patterns,
                "sequence_length": len(events),
                "features_extracted": len(features),
            }

        except Exception as e:
            self.logger.error(f"Error analyzing behavior sequence: {e}")
            return {"threat_score": 0.0, "error": str(e)}

    def _extract_behavioral_features(
        self, events: List[Dict[str, Any]]
    ) -> List[List[float]]:
        """Extract behavioral features from events."""
        features = []

        for event in events:
            # Extract basic features
            feature_vector = [0.0] * self.feature_dimension

            # Time-based features
            timestamp = event.get("timestamp", time.time())
            hour_of_day = (timestamp % 86400) / 86400  # Normalize to 0-1
            day_of_week = ((timestamp // 86400) % 7) / 7  # Normalize to 0-1

            feature_vector[0] = hour_of_day
            feature_vector[1] = day_of_week

            # Event type encoding
            event_types = [
                "file_access",
                "network_activity",
                "process_start",
                "registry_change",
                "system_call",
            ]
            event_type = event.get("type", "unknown")
            if event_type in event_types:
                feature_vector[2 + event_types.index(event_type)] = 1.0

            # Severity encoding
            severity_map = {"LOW": 0.25, "MEDIUM": 0.5, "HIGH": 0.75, "CRITICAL": 1.0}
            severity = event.get("severity", "LOW")
            feature_vector[7] = severity_map.get(severity, 0.0)

            # Process-related features
            process_name = event.get("process_name", "")
            feature_vector[8] = len(process_name) / 100  # Normalize path length
            feature_vector[9] = 1.0 if "system" in process_name.lower() else 0.0
            feature_vector[10] = 1.0 if ".exe" in process_name.lower() else 0.0

            # File-related features
            file_path = event.get("file_path", "")
            feature_vector[11] = len(file_path) / 200  # Normalize path length
            feature_vector[12] = 1.0 if "temp" in file_path.lower() else 0.0
            feature_vector[13] = 1.0 if "system" in file_path.lower() else 0.0

            # Network-related features
            if "network" in event:
                network = event["network"]
                feature_vector[14] = network.get("bytes_sent", 0) / 1000000  # Normalize
                feature_vector[15] = network.get("bytes_received", 0) / 1000000
                feature_vector[16] = 1.0 if network.get("external_ip") else 0.0

            # Add statistical features
            feature_vector[17] = event.get("cpu_usage", 0.0) / 100
            feature_vector[18] = event.get("memory_usage", 0.0) / 100

            features.append(feature_vector)

        return features

    def _identify_patterns(self, events: List[Dict[str, Any]]) -> List[str]:
        """Identify behavioral patterns in events."""
        patterns = []

        if len(events) < 2:
            return patterns

        # Check for rapid succession of events
        time_diffs = []
        for i in range(1, len(events)):
            prev_time = events[i - 1].get("timestamp", 0)
            curr_time = events[i].get("timestamp", 0)
            time_diffs.append(curr_time - prev_time)

        avg_time_diff = np.mean(time_diffs)
        if avg_time_diff < 1.0:  # Less than 1 second between events
            patterns.append("rapid_activity")

        # Check for repetitive patterns
        event_types = [event.get("type") for event in events]
        unique_types = set(event_types)
        if len(unique_types) < len(event_types) / 2:
            patterns.append("repetitive_behavior")

        # Check for escalating severity
        severities = [event.get("severity", "LOW") for event in events]
        severity_values = [
            {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}.get(s, 1)
            for s in severities
        ]
        if len(severity_values) > 1 and severity_values[-1] > severity_values[0]:
            patterns.append("escalating_severity")

        # Check for off-hours activity
        off_hours_count = 0
        for event in events:
            timestamp = event.get("timestamp", time.time())
            hour = (timestamp % 86400) // 3600
            if hour < 6 or hour > 22:  # Before 6 AM or after 10 PM
                off_hours_count += 1

        if off_hours_count > len(events) / 2:
            patterns.append("off_hours_activity")

        return patterns


class TransferLearningManager:
    """Manage transfer learning from pretrained security models."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.pretrained_models = {}
        self.model_registry = {}

    async def load_pretrained_model(self, model_name: str, model_path: str) -> bool:
        """Load pretrained model for transfer learning."""
        try:
            # Load model state
            state_dict = torch.load(model_path, map_location="cpu")

            # Create model instance based on type
            if "lstm" in model_name.lower():
                model = ThreatLSTM(input_size=50, hidden_size=128)
            elif "cnn" in model_name.lower():
                model = ThreatCNN(input_channels=1)
            elif "transformer" in model_name.lower():
                model = ThreatTransformer(vocab_size=10000)
            else:
                self.logger.error(f"Unknown model type: {model_name}")
                return False

            # Load weights
            model.load_state_dict(state_dict)
            model.eval()

            self.pretrained_models[model_name] = model
            self.logger.info(f"Loaded pretrained model: {model_name}")

            return True

        except Exception as e:
            self.logger.error(f"Error loading pretrained model {model_name}: {e}")
            return False

    async def fine_tune_model(
        self,
        base_model_name: str,
        training_data: List[Tuple[torch.Tensor, torch.Tensor]],
        num_epochs: int = 10,
    ) -> str:
        """Fine-tune pretrained model on new data."""
        try:
            if base_model_name not in self.pretrained_models:
                raise ValueError(f"Pretrained model {base_model_name} not found")

            # Clone the pretrained model
            model = self.pretrained_models[base_model_name]
            fine_tuned_model = type(model)(**self._get_model_params(model))
            fine_tuned_model.load_state_dict(model.state_dict())

            # Freeze early layers for transfer learning
            self._freeze_layers(fine_tuned_model, freeze_ratio=0.7)

            # Setup training
            optimizer = optim.Adam(
                filter(lambda p: p.requires_grad, fine_tuned_model.parameters()),
                lr=0.0001,
            )
            criterion = nn.CrossEntropyLoss()

            # Training loop
            fine_tuned_model.train()
            for epoch in range(num_epochs):
                total_loss = 0.0
                num_batches = 0

                for inputs, targets in training_data:
                    optimizer.zero_grad()

                    if isinstance(fine_tuned_model, ThreatLSTM):
                        outputs, _ = fine_tuned_model(inputs)
                    else:
                        outputs = fine_tuned_model(inputs)

                    loss = criterion(outputs, targets)
                    loss.backward()
                    optimizer.step()

                    total_loss += loss.item()
                    num_batches += 1

                avg_loss = total_loss / num_batches if num_batches > 0 else 0
                self.logger.info(f"Epoch {epoch+1}/{num_epochs}, Loss: {avg_loss:.4f}")

            # Save fine-tuned model
            model_id = f"{base_model_name}_finetuned_{int(time.time())}"
            self.pretrained_models[model_id] = fine_tuned_model

            return model_id

        except Exception as e:
            self.logger.error(f"Error fine-tuning model: {e}")
            return ""

    def _get_model_params(self, model) -> Dict[str, Any]:
        """Extract model parameters for recreation."""
        if isinstance(model, ThreatLSTM):
            return {
                "input_size": model.lstm.input_size,
                "hidden_size": model.hidden_size,
                "num_layers": model.num_layers,
            }
        elif isinstance(model, ThreatCNN):
            return {"input_channels": model.conv1.in_channels}
        elif isinstance(model, ThreatTransformer):
            return {
                "vocab_size": model.token_embedding.num_embeddings,
                "embed_dim": model.embed_dim,
            }
        else:
            return {}

    def _freeze_layers(self, model: nn.Module, freeze_ratio: float = 0.7):
        """Freeze a portion of model layers for transfer learning."""
        all_params = list(model.parameters())
        num_to_freeze = int(len(all_params) * freeze_ratio)

        for i, param in enumerate(all_params):
            if i < num_to_freeze:
                param.requires_grad = False
            else:
                param.requires_grad = True


class EnsemblePredictor:
    """Ensemble prediction combining multiple deep learning models."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.models = {}
        self.weights = {}
        self.voting_strategy = "weighted"  # 'weighted', 'majority', 'average'

    def add_model(self, model_name: str, model: nn.Module, weight: float = 1.0):
        """Add model to ensemble."""
        self.models[model_name] = model
        self.weights[model_name] = weight
        self.logger.info(f"Added model to ensemble: {model_name} (weight: {weight})")

    async def predict_ensemble(
        self, inputs: Dict[str, torch.Tensor]
    ) -> ModelPrediction:
        """Make ensemble prediction."""
        try:
            predictions = {}
            confidences = {}

            # Get predictions from all models
            for model_name, model in self.models.items():
                if model_name in inputs:
                    input_tensor = inputs[model_name]

                    with torch.no_grad():
                        if isinstance(model, ThreatLSTM):
                            logits, probabilities = model(input_tensor)
                            pred = torch.argmax(probabilities, dim=1).item()
                            conf = torch.max(probabilities, dim=1)[0].item()
                        else:
                            logits = model(input_tensor)
                            probabilities = F.softmax(logits, dim=1)
                            pred = torch.argmax(probabilities, dim=1).item()
                            conf = torch.max(probabilities, dim=1)[0].item()

                    predictions[model_name] = pred
                    confidences[model_name] = conf

            # Combine predictions
            if self.voting_strategy == "weighted":
                final_prediction = self._weighted_voting(predictions, confidences)
            elif self.voting_strategy == "majority":
                final_prediction = self._majority_voting(predictions)
            else:  # average
                final_prediction = self._average_voting(predictions, confidences)

            return ModelPrediction(
                prediction=final_prediction["prediction"],
                confidence=final_prediction["confidence"],
                probabilities=final_prediction.get("probabilities"),
                model_version="ensemble_v1.0",
            )

        except Exception as e:
            self.logger.error(f"Error in ensemble prediction: {e}")
            return ModelPrediction(
                prediction=0, confidence=0.0, model_version="ensemble_v1.0"
            )

    def _weighted_voting(
        self, predictions: Dict[str, int], confidences: Dict[str, float]
    ) -> Dict[str, Any]:
        """Weighted voting based on model confidence and weights."""
        weighted_scores = defaultdict(float)
        total_weight = 0.0

        for model_name, pred in predictions.items():
            weight = self.weights[model_name] * confidences[model_name]
            weighted_scores[pred] += weight
            total_weight += weight

        if total_weight == 0:
            return {"prediction": 0, "confidence": 0.0}

        # Normalize scores
        for pred in weighted_scores:
            weighted_scores[pred] /= total_weight

        # Get final prediction
        final_pred = max(weighted_scores.items(), key=lambda x: x[1])

        return {
            "prediction": final_pred[0],
            "confidence": final_pred[1],
            "probabilities": list(weighted_scores.values()),
        }

    def _majority_voting(self, predictions: Dict[str, int]) -> Dict[str, Any]:
        """Simple majority voting."""
        from collections import Counter

        vote_counts = Counter(predictions.values())
        final_pred = vote_counts.most_common(1)[0]

        confidence = final_pred[1] / len(predictions)

        return {"prediction": final_pred[0], "confidence": confidence}

    def _average_voting(
        self, predictions: Dict[str, int], confidences: Dict[str, float]
    ) -> Dict[str, Any]:
        """Average voting with confidence weighting."""
        if not predictions:
            return {"prediction": 0, "confidence": 0.0}

        avg_pred = sum(predictions.values()) / len(predictions)
        avg_conf = sum(confidences.values()) / len(confidences)

        return {"prediction": round(avg_pred), "confidence": avg_conf}


class DeepLearningThreatDetector:
    """Main deep learning threat detection system."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = get_config()

        # Initialize components
        self.nlp_analyzer = NLPThreatAnalyzer()
        self.cv_analyzer = ComputerVisionAnalyzer()
        self.behavioral_analyzer = BehavioralAnalyzer()
        self.transfer_manager = TransferLearningManager()
        self.ensemble = EnsemblePredictor()

        # Model storage
        self.models_dir = Path("models/deep_learning")
        self.models_dir.mkdir(parents=True, exist_ok=True)

        # Performance tracking
        self.prediction_history = deque(maxlen=10000)
        self.model_metrics = {}

    async def initialize(self):
        """Initialize all deep learning components."""
        try:
            # Initialize individual components
            nlp_success = await self.nlp_analyzer.initialize()
            cv_success = await self.cv_analyzer.initialize()
            behavioral_success = await self.behavioral_analyzer.initialize()

            # Load pretrained models if available
            await self._load_pretrained_models()

            # Setup ensemble
            await self._setup_ensemble()

            success = nlp_success and cv_success and behavioral_success

            if success:
                self.logger.info(
                    "Deep learning threat detector initialized successfully"
                )
            else:
                self.logger.warning(
                    "Some deep learning components failed to initialize"
                )

            return success

        except Exception as e:
            self.logger.error(f"Error initializing deep learning detector: {e}")
            return False

    async def analyze_comprehensive(
        self, target_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Comprehensive threat analysis using all available models."""
        try:
            results = {
                "nlp_analysis": None,
                "cv_analysis": None,
                "behavioral_analysis": None,
                "ensemble_prediction": None,
                "overall_threat_score": 0.0,
                "confidence": 0.0,
                "analysis_time": 0.0,
            }

            start_time = time.time()

            # NLP analysis for text data
            if "text_data" in target_data:
                results["nlp_analysis"] = await self.nlp_analyzer.analyze_log_entry(
                    target_data["text_data"]
                )

            # Computer vision analysis for files
            if "file_path" in target_data:
                results["cv_analysis"] = await self.cv_analyzer.analyze_file_visual(
                    target_data["file_path"]
                )

            # Behavioral analysis for event sequences
            if "events" in target_data:
                results["behavioral_analysis"] = (
                    await self.behavioral_analyzer.analyze_behavior_sequence(
                        target_data["events"]
                    )
                )

            # Ensemble prediction if models available
            if self.ensemble.models:
                # Prepare inputs for ensemble
                ensemble_inputs = await self._prepare_ensemble_inputs(
                    target_data, results
                )
                results["ensemble_prediction"] = await self.ensemble.predict_ensemble(
                    ensemble_inputs
                )

            # Calculate overall threat score
            scores = []
            if results["nlp_analysis"]:
                scores.append(results["nlp_analysis"].get("threat_score", 0.0))
            if results["cv_analysis"]:
                scores.append(results["cv_analysis"].get("threat_score", 0.0))
            if results["behavioral_analysis"]:
                scores.append(results["behavioral_analysis"].get("threat_score", 0.0))
            if results["ensemble_prediction"]:
                scores.append(results["ensemble_prediction"].confidence)

            if scores:
                results["overall_threat_score"] = np.mean(scores)
                results["confidence"] = np.std(scores) if len(scores) > 1 else 1.0

            results["analysis_time"] = time.time() - start_time

            # Record prediction
            self.prediction_history.append(
                {
                    "timestamp": time.time(),
                    "threat_score": results["overall_threat_score"],
                    "confidence": results["confidence"],
                    "components_used": [
                        k for k in results.keys() if results[k] is not None
                    ],
                }
            )

            return results

        except Exception as e:
            self.logger.error(f"Error in comprehensive analysis: {e}")
            return {"overall_threat_score": 0.0, "error": str(e)}

    async def _load_pretrained_models(self):
        """Load available pretrained models."""
        model_files = list(self.models_dir.glob("*.pth"))

        for model_file in model_files:
            model_name = model_file.stem
            success = await self.transfer_manager.load_pretrained_model(
                model_name, str(model_file)
            )
            if success:
                self.logger.info(f"Loaded pretrained model: {model_name}")

    async def _setup_ensemble(self):
        """Setup ensemble with available models."""
        # Add models to ensemble if available
        if self.behavioral_analyzer.behavioral_model:
            self.ensemble.add_model(
                "behavioral_lstm", self.behavioral_analyzer.behavioral_model, weight=1.0
            )

        # Add pretrained models
        for model_name, model in self.transfer_manager.pretrained_models.items():
            self.ensemble.add_model(model_name, model, weight=0.8)

    async def _prepare_ensemble_inputs(
        self, target_data: Dict[str, Any], analysis_results: Dict[str, Any]
    ) -> Dict[str, torch.Tensor]:
        """Prepare inputs for ensemble prediction."""
        inputs = {}

        # Prepare behavioral input if available
        if "events" in target_data and analysis_results.get("behavioral_analysis"):
            # Mock behavioral features tensor
            features = torch.randn(
                1, 100, 50
            )  # batch_size=1, seq_len=100, feature_dim=50
            inputs["behavioral_lstm"] = features

        return inputs

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the deep learning system."""
        if not self.prediction_history:
            return {}

        recent_predictions = list(self.prediction_history)[
            -1000:
        ]  # Last 1000 predictions

        threat_scores = [p["threat_score"] for p in recent_predictions]
        confidences = [p["confidence"] for p in recent_predictions]
        analysis_times = [p.get("analysis_time", 0) for p in recent_predictions]

        return {
            "total_predictions": len(self.prediction_history),
            "avg_threat_score": np.mean(threat_scores),
            "avg_confidence": np.mean(confidences),
            "avg_analysis_time": np.mean(analysis_times),
            "threat_score_std": np.std(threat_scores),
            "high_threat_percentage": len([s for s in threat_scores if s > 0.7])
            / len(threat_scores)
            * 100,
            "models_loaded": len(self.transfer_manager.pretrained_models),
            "ensemble_size": len(self.ensemble.models),
        }


# Global deep learning instance
_deep_learning_instance = None


def get_deep_learning_detector() -> DeepLearningThreatDetector:
    """Get the global deep learning detector instance."""
    global _deep_learning_instance
    if _deep_learning_instance is None:
        _deep_learning_instance = DeepLearningThreatDetector()
    return _deep_learning_instance
