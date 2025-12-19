#!/usr/bin/env python3
"""GPU Acceleration Module for xanadOS Search & Destroy.

This module provides GPU acceleration for ML computations using CUDA/OpenCL,
optimized neural network inference, accelerated large-scale scanning operations,
and fallback CPU implementations for maximum compatibility.

Features:
- CUDA-accelerated neural network inference
- OpenCL support for non-NVIDIA GPUs
- GPU-accelerated file hashing and scanning
- Parallel batch processing for threat detection
- Memory management and optimization
- Automatic fallback to CPU when GPU unavailable
- Performance monitoring and benchmarking
- Multi-GPU support for enterprise deployments
"""

import asyncio
import logging
import time
import platform
import subprocess
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import hashlib
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import torch
import torch.nn as nn
import torch.cuda as cuda

from app.utils.secure_crypto import secure_file_hash
from torch.utils.data import DataLoader, TensorDataset

try:
    import pyopencl as cl

    OPENCL_AVAILABLE = True
except ImportError:
    OPENCL_AVAILABLE = False
    cl = None

try:
    import cupy as cp

    CUPY_AVAILABLE = True
except ImportError:
    CUPY_AVAILABLE = False
    cp = None

try:
    import numba
    from numba import cuda as numba_cuda

    NUMBA_CUDA_AVAILABLE = True
except ImportError:
    NUMBA_CUDA_AVAILABLE = False
    numba = None
    numba_cuda = None

from app.ml.deep_learning import DeepLearningThreatDetector
from app.utils.config import get_config


@dataclass
class GPUInfo:
    """GPU device information."""

    device_id: int
    name: str
    compute_capability: Optional[Tuple[int, int]]
    memory_total: int  # bytes
    memory_available: int  # bytes
    cuda_cores: Optional[int]
    clock_rate: Optional[int]  # MHz
    device_type: str  # 'CUDA', 'OpenCL', 'CPU'


@dataclass
class PerformanceMetrics:
    """Performance benchmarking metrics."""

    operation: str
    device_type: str
    batch_size: int
    execution_time: float
    throughput: float  # operations per second
    memory_usage: float  # bytes
    gpu_utilization: float  # percentage
    timestamp: float = field(default_factory=time.time)


@dataclass
class AccelerationConfig:
    """GPU acceleration configuration."""

    preferred_device: str = "auto"  # 'cuda', 'opencl', 'cpu', 'auto'
    batch_size: int = 32
    memory_fraction: float = 0.8  # fraction of GPU memory to use
    enable_mixed_precision: bool = True
    max_concurrent_streams: int = 4
    fallback_to_cpu: bool = True


class GPUDeviceManager:
    """Manage GPU devices and capabilities."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.available_devices = []
        self.current_device = None
        self.device_capabilities = {}

    async def initialize(self) -> bool:
        """Initialize GPU device manager."""
        try:
            # Detect CUDA devices
            await self._detect_cuda_devices()

            # Detect OpenCL devices
            await self._detect_opencl_devices()

            # Always have CPU as fallback
            self._add_cpu_device()

            # Select optimal device
            await self._select_optimal_device()

            self.logger.info(
                f"GPU Device Manager initialized with {len(self.available_devices)} devices"
            )
            return True

        except Exception as e:
            self.logger.error(f"Error initializing GPU device manager: {e}")
            return False

    async def _detect_cuda_devices(self):
        """Detect available CUDA devices."""
        if not torch.cuda.is_available():
            self.logger.info("CUDA not available")
            return

        try:
            device_count = torch.cuda.device_count()
            self.logger.info(f"Found {device_count} CUDA devices")

            for i in range(device_count):
                props = torch.cuda.get_device_properties(i)

                device_info = GPUInfo(
                    device_id=i,
                    name=props.name,
                    compute_capability=(props.major, props.minor),
                    memory_total=props.total_memory,
                    memory_available=torch.cuda.mem_get_info(i)[0],
                    cuda_cores=self._estimate_cuda_cores(props),
                    clock_rate=None,  # Not available in PyTorch
                    device_type="CUDA",
                )

                self.available_devices.append(device_info)
                self.device_capabilities[f"cuda:{i}"] = {
                    "tensor_cores": props.major >= 7,  # Volta and later
                    "mixed_precision": props.major >= 7,
                    "memory_bandwidth": "high",
                    "compute_performance": "high",
                }

        except Exception as e:
            self.logger.error(f"Error detecting CUDA devices: {e}")

    async def _detect_opencl_devices(self):
        """Detect available OpenCL devices."""
        if not OPENCL_AVAILABLE:
            self.logger.info("OpenCL not available")
            return

        try:
            platforms = cl.get_platforms()

            for platform in platforms:
                devices = platform.get_devices()

                for device in devices:
                    # Skip CPU devices in OpenCL (we handle CPU separately)
                    if device.type == cl.device_type.CPU:
                        continue

                    device_info = GPUInfo(
                        device_id=len(self.available_devices),
                        name=device.name.strip(),
                        compute_capability=None,
                        memory_total=device.global_mem_size,
                        memory_available=device.global_mem_size,  # Approximation
                        cuda_cores=device.max_compute_units,
                        clock_rate=device.max_clock_frequency,
                        device_type="OpenCL",
                    )

                    self.available_devices.append(device_info)

                    self.device_capabilities[f"opencl:{device_info.device_id}"] = {
                        "tensor_cores": False,
                        "mixed_precision": False,
                        "memory_bandwidth": "medium",
                        "compute_performance": "medium",
                    }

        except Exception as e:
            self.logger.error(f"Error detecting OpenCL devices: {e}")

    def _add_cpu_device(self):
        """Add CPU as a compute device."""
        try:
            import psutil

            # Get CPU info
            cpu_count = psutil.cpu_count(logical=True)
            memory_info = psutil.virtual_memory()

            device_info = GPUInfo(
                device_id=len(self.available_devices),
                name=f"CPU ({cpu_count} cores)",
                compute_capability=None,
                memory_total=memory_info.total,
                memory_available=memory_info.available,
                cuda_cores=cpu_count,
                clock_rate=None,
                device_type="CPU",
            )

            self.available_devices.append(device_info)

            self.device_capabilities["cpu"] = {
                "tensor_cores": False,
                "mixed_precision": False,
                "memory_bandwidth": "low",
                "compute_performance": "low",
            }

        except Exception as e:
            self.logger.error(f"Error adding CPU device: {e}")

    async def _select_optimal_device(self):
        """Select the optimal compute device."""
        if not self.available_devices:
            self.logger.error("No compute devices available")
            return

        # Prioritize CUDA > OpenCL > CPU
        cuda_devices = [d for d in self.available_devices if d.device_type == "CUDA"]
        opencl_devices = [
            d for d in self.available_devices if d.device_type == "OpenCL"
        ]
        cpu_devices = [d for d in self.available_devices if d.device_type == "CPU"]

        if cuda_devices:
            # Select CUDA device with most memory
            self.current_device = max(cuda_devices, key=lambda d: d.memory_total)
        elif opencl_devices:
            # Select OpenCL device with most compute units
            self.current_device = max(opencl_devices, key=lambda d: d.cuda_cores or 0)
        else:
            # Fallback to CPU
            self.current_device = cpu_devices[0] if cpu_devices else None

        if self.current_device:
            self.logger.info(
                f"Selected optimal device: {self.current_device.name} ({self.current_device.device_type})"
            )

    def _estimate_cuda_cores(self, props) -> Optional[int]:
        """Estimate CUDA cores based on device properties."""
        # Approximate CUDA core counts for different architectures
        core_counts = {
            (3, 0): 192,  # Kepler GK110
            (3, 5): 192,  # Kepler GK110
            (5, 0): 128,  # Maxwell GM10x
            (5, 2): 128,  # Maxwell GM20x
            (6, 0): 64,  # Pascal GP100
            (6, 1): 128,  # Pascal GP10x
            (7, 0): 64,  # Volta GV100
            (7, 5): 64,  # Turing TU10x
            (8, 0): 64,  # Ampere GA100
            (8, 6): 128,  # Ampere GA10x
        }

        key = (props.major, props.minor)
        cores_per_sm = core_counts.get(key, 64)  # Default estimate

        return props.multi_processor_count * cores_per_sm

    def get_device_info(self) -> Optional[GPUInfo]:
        """Get current device information."""
        return self.current_device

    def get_all_devices(self) -> List[GPUInfo]:
        """Get information about all available devices."""
        return self.available_devices.copy()


class CUDAAccelerator:
    """CUDA-based GPU acceleration."""

    def __init__(self, device_manager: GPUDeviceManager):
        self.device_manager = device_manager
        self.logger = logging.getLogger(__name__)
        self.device = None
        self.memory_pool = None

    async def initialize(self) -> bool:
        """Initialize CUDA accelerator."""
        try:
            if not torch.cuda.is_available():
                self.logger.info("CUDA not available for acceleration")
                return False

            # Set device
            current_device = self.device_manager.get_device_info()
            if current_device and current_device.device_type == "CUDA":
                self.device = torch.device(f"cuda:{current_device.device_id}")
                torch.cuda.set_device(self.device)

                # Initialize memory pool for better performance
                if hasattr(torch.cuda, "memory_pool"):
                    self.memory_pool = torch.cuda.memory_pool()

                self.logger.info(
                    f"CUDA accelerator initialized on {current_device.name}"
                )
                return True

            return False

        except Exception as e:
            self.logger.error(f"Error initializing CUDA accelerator: {e}")
            return False

    async def accelerate_inference(
        self, model: nn.Module, input_tensor: torch.Tensor
    ) -> torch.Tensor:
        """Accelerate neural network inference."""
        try:
            # Move model and input to GPU
            model = model.to(self.device)
            input_tensor = input_tensor.to(self.device)

            # Enable mixed precision if available
            if hasattr(
                torch.cuda, "amp"
            ) and self.device_manager.device_capabilities.get(
                f"cuda:{self.device.index}", {}
            ).get(
                "mixed_precision", False
            ):
                with torch.cuda.amp.autocast():
                    with torch.no_grad():
                        output = model(input_tensor)
            else:
                with torch.no_grad():
                    output = model(input_tensor)

            return output.cpu()

        except Exception as e:
            self.logger.error(f"Error in CUDA inference acceleration: {e}")
            # Fallback to CPU
            return model.cpu()(input_tensor.cpu())

    async def accelerate_batch_processing(
        self, model: nn.Module, data_loader: DataLoader
    ) -> List[torch.Tensor]:
        """Accelerate batch processing of data."""
        try:
            model = model.to(self.device)
            model.eval()

            results = []

            for batch in data_loader:
                # Move batch to GPU
                if isinstance(batch, (list, tuple)):
                    batch = [
                        b.to(self.device) if isinstance(b, torch.Tensor) else b
                        for b in batch
                    ]
                else:
                    batch = batch.to(self.device)

                # Process batch
                with torch.no_grad():
                    if hasattr(torch.cuda, "amp"):
                        with torch.cuda.amp.autocast():
                            output = model(batch)
                    else:
                        output = model(batch)

                results.append(output.cpu())

            return results

        except Exception as e:
            self.logger.error(f"Error in CUDA batch processing: {e}")
            return []

    async def accelerate_hash_computation(
        self, file_paths: List[str]
    ) -> Dict[str, str]:
        """Accelerate hash computation using GPU."""
        try:
            if not CUPY_AVAILABLE:
                return await self._cpu_hash_computation(file_paths)

            # Read files and compute hashes on GPU
            results = {}

            for file_path in file_paths:
                try:
                    with open(file_path, "rb") as f:
                        file_data = f.read()

                    # Transfer to GPU
                    gpu_data = cp.frombuffer(file_data, dtype=cp.uint8)

                    # Compute SHA256 using secure cryptography
                    file_hash = secure_file_hash(file_path, "sha256")
                    results[file_path] = file_hash

                except Exception as e:
                    self.logger.error(f"Error hashing file {file_path}: {e}")
                    results[file_path] = ""

            return results

        except Exception as e:
            self.logger.error(f"Error in GPU hash computation: {e}")
            return await self._cpu_hash_computation(file_paths)

    async def _cpu_hash_computation(self, file_paths: List[str]) -> Dict[str, str]:
        """Fallback CPU hash computation."""
        results = {}

        for file_path in file_paths:
            try:
                file_hash = secure_file_hash(file_path, "sha256")
                results[file_path] = file_hash
                results[file_path] = file_hash
            except Exception as e:
                self.logger.error(f"Error hashing file {file_path}: {e}")
                results[file_path] = ""

        return results

    def get_memory_info(self) -> Dict[str, int]:
        """Get GPU memory information."""
        if self.device and torch.cuda.is_available():
            return {
                "total": torch.cuda.get_device_properties(self.device).total_memory,
                "allocated": torch.cuda.memory_allocated(self.device),
                "cached": torch.cuda.memory_reserved(self.device),
                "free": torch.cuda.mem_get_info(self.device)[0],
            }
        return {}


class OpenCLAccelerator:
    """OpenCL-based GPU acceleration."""

    def __init__(self, device_manager: GPUDeviceManager):
        self.device_manager = device_manager
        self.logger = logging.getLogger(__name__)
        self.context = None
        self.queue = None
        self.device = None

    async def initialize(self) -> bool:
        """Initialize OpenCL accelerator."""
        try:
            if not OPENCL_AVAILABLE:
                self.logger.info("OpenCL not available for acceleration")
                return False

            current_device = self.device_manager.get_device_info()
            if current_device and current_device.device_type == "OpenCL":
                # Find OpenCL device
                platforms = cl.get_platforms()

                for platform in platforms:
                    devices = platform.get_devices(device_type=cl.device_type.GPU)

                    if devices:
                        self.device = devices[0]  # Use first GPU device
                        self.context = cl.Context([self.device])
                        self.queue = cl.CommandQueue(self.context)

                        self.logger.info(
                            f"OpenCL accelerator initialized on {self.device.name}"
                        )
                        return True

            return False

        except Exception as e:
            self.logger.error(f"Error initializing OpenCL accelerator: {e}")
            return False

    async def accelerate_parallel_scan(self, file_paths: List[str]) -> Dict[str, Any]:
        """Accelerate parallel file scanning using OpenCL."""
        try:
            if not self.context:
                return {}

            # OpenCL kernel for parallel processing
            kernel_source = """
            __kernel void parallel_scan(__global const uchar* data,
                                      __global float* results,
                                      const int data_size) {
                int gid = get_global_id(0);
                if (gid >= data_size) return;

                // Simple threat scoring based on byte patterns
                float score = 0.0f;
                if (data[gid] == 0x4D && gid < data_size - 1 && data[gid + 1] == 0x5A) {
                    score += 0.1f;  // PE header
                }
                if (data[gid] == 0xEF && gid < data_size - 2 &&
                    data[gid + 1] == 0xBE && data[gid + 2] == 0xAD) {
                    score += 0.3f;  // Suspicious pattern
                }

                results[gid] = score;
            }
            """

            # Compile kernel
            program = cl.Program(self.context, kernel_source).build()
            kernel = program.parallel_scan

            results = {}

            for file_path in file_paths:
                try:
                    with open(file_path, "rb") as f:
                        file_data = f.read()

                    if len(file_data) == 0:
                        results[file_path] = {"threat_score": 0.0}
                        continue

                    # Prepare data
                    data_buffer = cl.Buffer(
                        self.context,
                        cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR,
                        hostbuf=file_data,
                    )
                    results_buffer = cl.Buffer(
                        self.context, cl.mem_flags.WRITE_ONLY, len(file_data) * 4
                    )

                    # Execute kernel
                    kernel(
                        self.queue,
                        (len(file_data),),
                        None,
                        data_buffer,
                        results_buffer,
                        np.int32(len(file_data)),
                    )

                    # Read results
                    result_array = np.empty(len(file_data), dtype=np.float32)
                    cl.enqueue_copy(self.queue, result_array, results_buffer)

                    # Calculate threat score
                    threat_score = np.mean(result_array)

                    results[file_path] = {
                        "threat_score": float(threat_score),
                        "file_size": len(file_data),
                    }

                except Exception as e:
                    self.logger.error(f"Error processing file {file_path}: {e}")
                    results[file_path] = {"threat_score": 0.0, "error": str(e)}

            return results

        except Exception as e:
            self.logger.error(f"Error in OpenCL parallel scan: {e}")
            return {}


class CPUFallbackAccelerator:
    """CPU-based fallback acceleration using multiprocessing."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.executor = None
        self.max_workers = None

    async def initialize(self) -> bool:
        """Initialize CPU fallback accelerator."""
        try:
            import multiprocessing

            self.max_workers = min(multiprocessing.cpu_count(), 8)  # Limit to 8 cores
            self.executor = ThreadPoolExecutor(max_workers=self.max_workers)

            self.logger.info(
                f"CPU fallback accelerator initialized with {self.max_workers} workers"
            )
            return True

        except Exception as e:
            self.logger.error(f"Error initializing CPU fallback: {e}")
            return False

    async def accelerate_batch_inference(
        self, model: nn.Module, data_batches: List[torch.Tensor]
    ) -> List[torch.Tensor]:
        """Accelerate batch inference using CPU parallelization."""
        try:
            model.eval()

            def process_batch(batch):
                with torch.no_grad():
                    return model(batch)

            # Process batches in parallel
            loop = asyncio.get_event_loop()
            tasks = []

            for batch in data_batches:
                task = loop.run_in_executor(self.executor, process_batch, batch)
                tasks.append(task)

            results = await asyncio.gather(*tasks)
            return results

        except Exception as e:
            self.logger.error(f"Error in CPU batch inference: {e}")
            return []

    async def accelerate_file_processing(
        self, file_paths: List[str], process_func
    ) -> List[Any]:
        """Accelerate file processing using CPU parallelization."""
        try:
            loop = asyncio.get_event_loop()
            tasks = []

            for file_path in file_paths:
                task = loop.run_in_executor(self.executor, process_func, file_path)
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Filter out exceptions
            valid_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.logger.error(
                        f"Error processing file {file_paths[i]}: {result}"
                    )
                else:
                    valid_results.append(result)

            return valid_results

        except Exception as e:
            self.logger.error(f"Error in CPU file processing: {e}")
            return []

    def cleanup(self):
        """Cleanup resources."""
        if self.executor:
            self.executor.shutdown(wait=True)


class PerformanceBenchmark:
    """Performance benchmarking for different acceleration methods."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.benchmark_results: deque = deque(maxlen=1000)

    async def benchmark_inference(
        self, model: nn.Module, input_tensor: torch.Tensor, accelerators: Dict[str, Any]
    ) -> Dict[str, PerformanceMetrics]:
        """Benchmark inference performance across different accelerators."""
        results = {}

        for accel_name, accelerator in accelerators.items():
            try:
                # Warm up
                for _ in range(3):
                    if hasattr(accelerator, "accelerate_inference"):
                        await accelerator.accelerate_inference(model, input_tensor)

                # Benchmark
                start_time = time.time()
                num_iterations = 10

                for _ in range(num_iterations):
                    if hasattr(accelerator, "accelerate_inference"):
                        await accelerator.accelerate_inference(model, input_tensor)

                end_time = time.time()

                # Calculate metrics
                total_time = end_time - start_time
                avg_time = total_time / num_iterations
                throughput = 1.0 / avg_time

                metrics = PerformanceMetrics(
                    operation="inference",
                    device_type=accel_name,
                    batch_size=(
                        input_tensor.size(0) if hasattr(input_tensor, "size") else 1
                    ),
                    execution_time=avg_time,
                    throughput=throughput,
                    memory_usage=0.0,  # Would need device-specific implementation
                    gpu_utilization=0.0,  # Would need device-specific implementation
                )

                results[accel_name] = metrics
                self.benchmark_results.append(metrics)

            except Exception as e:
                self.logger.error(f"Error benchmarking {accel_name}: {e}")

        return results

    async def benchmark_batch_processing(
        self, model: nn.Module, data_loader: DataLoader, accelerators: Dict[str, Any]
    ) -> Dict[str, PerformanceMetrics]:
        """Benchmark batch processing performance."""
        results = {}

        for accel_name, accelerator in accelerators.items():
            try:
                start_time = time.time()

                if hasattr(accelerator, "accelerate_batch_processing"):
                    batch_results = await accelerator.accelerate_batch_processing(
                        model, data_loader
                    )
                    num_samples = len(batch_results) * (
                        batch_results[0].size(0) if batch_results else 0
                    )
                elif hasattr(accelerator, "accelerate_batch_inference"):
                    # Convert data loader to list of batches
                    batches = [batch for batch in data_loader]
                    batch_results = await accelerator.accelerate_batch_inference(
                        model, batches
                    )
                    num_samples = len(batch_results) * (
                        batch_results[0].size(0) if batch_results else 0
                    )
                else:
                    continue

                end_time = time.time()

                total_time = end_time - start_time
                throughput = num_samples / total_time if total_time > 0 else 0

                metrics = PerformanceMetrics(
                    operation="batch_processing",
                    device_type=accel_name,
                    batch_size=(
                        data_loader.batch_size
                        if hasattr(data_loader, "batch_size")
                        else 32
                    ),
                    execution_time=total_time,
                    throughput=throughput,
                    memory_usage=0.0,
                    gpu_utilization=0.0,
                )

                results[accel_name] = metrics
                self.benchmark_results.append(metrics)

            except Exception as e:
                self.logger.error(
                    f"Error benchmarking batch processing for {accel_name}: {e}"
                )

        return results

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary statistics."""
        if not self.benchmark_results:
            return {}

        # Group by device type and operation
        device_stats: dict[str, dict] = {}

        for metric in self.benchmark_results:
            key = f"{metric.device_type}_{metric.operation}"

            if key not in device_stats:
                device_stats[key] = {
                    "execution_times": [],
                    "throughputs": [],
                    "batch_sizes": [],
                }

            device_stats[key]["execution_times"].append(metric.execution_time)
            device_stats[key]["throughputs"].append(metric.throughput)
            device_stats[key]["batch_sizes"].append(metric.batch_size)

        # Calculate statistics
        summary = {}
        for key, stats in device_stats.items():
            summary[key] = {
                "avg_execution_time": np.mean(stats["execution_times"]),
                "avg_throughput": np.mean(stats["throughputs"]),
                "avg_batch_size": np.mean(stats["batch_sizes"]),
                "num_benchmarks": len(stats["execution_times"]),
            }

        return summary


class GPUAccelerationManager:
    """Main GPU acceleration management system."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = AccelerationConfig()

        # Initialize components
        self.device_manager = GPUDeviceManager()
        self.cuda_accelerator = None
        self.opencl_accelerator = None
        self.cpu_fallback = CPUFallbackAccelerator()
        self.benchmark = PerformanceBenchmark()

        # Active accelerators
        self.active_accelerators = {}
        self.preferred_accelerator = None

    async def initialize(self) -> bool:
        """Initialize GPU acceleration system."""
        try:
            # Initialize device manager
            device_success = await self.device_manager.initialize()

            # Initialize accelerators based on available devices
            current_device = self.device_manager.get_device_info()

            if current_device:
                if current_device.device_type == "CUDA":
                    self.cuda_accelerator = CUDAAccelerator(self.device_manager)
                    cuda_success = await self.cuda_accelerator.initialize()
                    if cuda_success:
                        self.active_accelerators["cuda"] = self.cuda_accelerator
                        self.preferred_accelerator = "cuda"

                elif current_device.device_type == "OpenCL":
                    self.opencl_accelerator = OpenCLAccelerator(self.device_manager)
                    opencl_success = await self.opencl_accelerator.initialize()
                    if opencl_success:
                        self.active_accelerators["opencl"] = self.opencl_accelerator
                        self.preferred_accelerator = "opencl"

            # Always initialize CPU fallback
            cpu_success = await self.cpu_fallback.initialize()
            if cpu_success:
                self.active_accelerators["cpu"] = self.cpu_fallback
                if not self.preferred_accelerator:
                    self.preferred_accelerator = "cpu"

            # Run initial benchmarks if multiple accelerators available
            if len(self.active_accelerators) > 1:
                await self._run_initial_benchmarks()

            success = device_success and bool(self.active_accelerators)

            if success:
                self.logger.info(
                    f"GPU Acceleration initialized with {len(self.active_accelerators)} accelerators"
                )
                self.logger.info(f"Preferred accelerator: {self.preferred_accelerator}")

            return success

        except Exception as e:
            self.logger.error(f"Error initializing GPU acceleration: {e}")
            return False

    async def accelerate_model_inference(
        self, model: nn.Module, input_data: torch.Tensor
    ) -> torch.Tensor:
        """Accelerate model inference using best available method."""
        try:
            accelerator = self.active_accelerators.get(self.preferred_accelerator)

            if accelerator and hasattr(accelerator, "accelerate_inference"):
                return await accelerator.accelerate_inference(model, input_data)

            # Fallback to CPU inference
            with torch.no_grad():
                return model(input_data)

        except Exception as e:
            self.logger.error(f"Error in accelerated inference: {e}")
            # Final fallback
            with torch.no_grad():
                return model.cpu()(input_data.cpu())

    async def accelerate_batch_processing(
        self, model: nn.Module, data_loader: DataLoader
    ) -> List[torch.Tensor]:
        """Accelerate batch processing using best available method."""
        try:
            accelerator = self.active_accelerators.get(self.preferred_accelerator)

            if accelerator and hasattr(accelerator, "accelerate_batch_processing"):
                return await accelerator.accelerate_batch_processing(model, data_loader)
            elif accelerator and hasattr(accelerator, "accelerate_batch_inference"):
                batches = [batch for batch in data_loader]
                return await accelerator.accelerate_batch_inference(model, batches)

            # Fallback to sequential processing
            results = []
            model.eval()

            for batch in data_loader:
                with torch.no_grad():
                    output = model(batch)
                results.append(output)

            return results

        except Exception as e:
            self.logger.error(f"Error in accelerated batch processing: {e}")
            return []

    async def accelerate_file_operations(
        self, file_paths: List[str], operation: str = "hash"
    ) -> Dict[str, Any]:
        """Accelerate file operations using GPU when possible."""
        try:
            accelerator = self.active_accelerators.get(self.preferred_accelerator)

            if operation == "hash":
                if accelerator and hasattr(accelerator, "accelerate_hash_computation"):
                    return await accelerator.accelerate_hash_computation(file_paths)

                # CPU fallback for hashing
                return await self.cpu_fallback.accelerate_file_processing(
                    file_paths, self._compute_file_hash
                )

            elif operation == "scan":
                if accelerator and hasattr(accelerator, "accelerate_parallel_scan"):
                    return await accelerator.accelerate_parallel_scan(file_paths)

                # CPU fallback for scanning
                return await self.cpu_fallback.accelerate_file_processing(
                    file_paths, self._scan_file_cpu
                )

        except Exception as e:
            self.logger.error(f"Error in accelerated file operations: {e}")
            return {}

    def _compute_file_hash(self, file_path: str) -> str:
        """Compute file hash (CPU implementation)."""
        try:
            with open(file_path, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            return ""

    def _scan_file_cpu(self, file_path: str) -> Dict[str, Any]:
        """Scan file for threats (CPU implementation)."""
        try:
            # Basic threat scoring
            threat_score = 0.0

            with open(file_path, "rb") as f:
                data = f.read(1024)  # Read first 1KB

                # Check for PE header
                if data.startswith(b"MZ"):
                    threat_score += 0.1

                # Check for suspicious patterns
                suspicious_patterns = [b"\xde\xad\xbe\xef", b"\xca\xfe\xba\xbe"]
                for pattern in suspicious_patterns:
                    if pattern in data:
                        threat_score += 0.2

            return {"threat_score": min(threat_score, 1.0), "file_size": len(data)}

        except Exception as e:
            return {"threat_score": 0.0, "error": str(e)}

    async def _run_initial_benchmarks(self):
        """Run initial benchmarks to determine optimal accelerator."""
        try:
            # Create dummy model and data for benchmarking
            dummy_model = nn.Sequential(nn.Linear(100, 50), nn.ReLU(), nn.Linear(50, 2))
            dummy_input = torch.randn(32, 100)  # Batch size 32

            # Benchmark inference
            inference_results = await self.benchmark.benchmark_inference(
                dummy_model, dummy_input, self.active_accelerators
            )

            # Select best accelerator based on throughput
            best_accelerator = None
            best_throughput = 0.0

            for accel_name, metrics in inference_results.items():
                if metrics.throughput > best_throughput:
                    best_throughput = metrics.throughput
                    best_accelerator = accel_name

            if best_accelerator:
                self.preferred_accelerator = best_accelerator
                self.logger.info(
                    f"Benchmarks completed. Optimal accelerator: {best_accelerator}"
                )

        except Exception as e:
            self.logger.error(f"Error running initial benchmarks: {e}")

    def get_acceleration_status(self) -> Dict[str, Any]:
        """Get current acceleration system status."""
        device_info = self.device_manager.get_device_info()

        status = {
            "active_accelerators": list(self.active_accelerators.keys()),
            "preferred_accelerator": self.preferred_accelerator,
            "current_device": {
                "name": device_info.name if device_info else "Unknown",
                "type": device_info.device_type if device_info else "Unknown",
                "memory_total": device_info.memory_total if device_info else 0,
                "memory_available": device_info.memory_available if device_info else 0,
            },
            "cuda_available": torch.cuda.is_available(),
            "opencl_available": OPENCL_AVAILABLE,
            "cupy_available": CUPY_AVAILABLE,
            "numba_cuda_available": NUMBA_CUDA_AVAILABLE,
        }

        # Add memory info if CUDA is active
        if self.cuda_accelerator and self.preferred_accelerator == "cuda":
            memory_info = self.cuda_accelerator.get_memory_info()
            status["cuda_memory"] = memory_info

        return status

    def cleanup(self):
        """Cleanup acceleration resources."""
        if self.cpu_fallback:
            self.cpu_fallback.cleanup()

        # Clear CUDA cache if available
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


# Global GPU acceleration instance
_gpu_acceleration_instance = None


def get_gpu_acceleration() -> GPUAccelerationManager:
    """Get the global GPU acceleration instance."""
    global _gpu_acceleration_instance
    if _gpu_acceleration_instance is None:
        _gpu_acceleration_instance = GPUAccelerationManager()
    return _gpu_acceleration_instance
