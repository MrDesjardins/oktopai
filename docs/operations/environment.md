# Environment findings

Checked 2026-08-24 before implementation:

- WSL2 Linux 6.6.87.2, x86_64.
- Python 3.14.2; 8 logical CPUs, Intel Core Ultra 9 285K.
- 23 GiB RAM, 6 GiB swap.
- `nvidia-smi` is present, but NVML reports GPU access blocked by the operating system. GPU model and VRAM are therefore not observable from this environment.
- Ollama client 0.17.2 is installed at `~/.local/bin/ollama`, but no Ollama daemon was listening on `127.0.0.1:11434` and no models could be listed.
- No `llama-server`, `llama-cli`, `mlx_lm`, or `llamacpp` executable was found.

Decision: use Ollama as the first backend because its client is installed and its `keep_alive` API supports preload/retention semantics. The backend is isolated behind `Runtime`; no model was downloaded and no system-wide dependency was installed.
## Latest training visibility check

The training virtual environment contains PyTorch `2.13.0+cu130`, but this
execution environment currently exposes no CUDA device:

```text
torch.cuda.is_available() = False
torch.cuda.device_count() = 0
nvidia-smi = GPU access blocked by the operating system
```

The v7 300-step training run therefore used CPU. The CUDA-enabled wheel is
already present; enabling GPU training requires fixing host/WSL GPU passthrough
and NVML visibility, not downloading another model or silently changing
runtime behavior.

Follow-up verification with local runtime access found the passthrough is
healthy: `/dev/dxg` and `libcuda.so.1` are present, `nvidia-smi` reports an
NVIDIA GeForce RTX 5080 with 15.92 GiB VRAM, and PyTorch sees one CUDA device.
Earlier checks were sandbox-restricted. GPU training is now enabled with
`scripts/train_lora.py --device cuda`.

## Current Codex-session visibility check (2026-08-26)

In the current managed Codex WSL session, GPU access is blocked again:

- kernel: WSL2 `6.6.87.2-microsoft-standard-WSL2`;
- `/usr/lib/wsl/lib/nvidia-smi` exists but reports `GPU access blocked by the operating system`;
- `/dev/nvidia*` device nodes are absent;
- PyTorch `2.13.0+cu130` reports `cuda_available = False` and zero devices.

This is not a missing CUDA-enabled PyTorch wheel. WSL CUDA uses the Windows
host driver and GPU virtualization; installing a Linux NVIDIA driver inside
WSL is not the correct fix. The failure is at the host/WSL or managed-session
visibility layer. Runpod previously confirmed that the project training stack
works with CUDA on an A40.
