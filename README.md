<div align="center">
  <img src="assets/logo.jpg" alt="CasperAC Logo" width="100%"/>

  <h1>CasperAC</h1>
  
  <p><strong>Advanced Dual-Layer Network Anonymization CLI</strong></p>

  <p>
    <a href="https://github.com/yourusername/casperac/actions"><img src="https://img.shields.io/github/actions/workflow/status/yourusername/casperac/ci.yml?branch=main" alt="Build Status"></a>
    <a href="https://pypi.org/project/casperac/"><img src="https://img.shields.io/pypi/v/casperac.svg" alt="PyPI Version"></a>
    <a href="https://pypi.org/project/casperac/"><img src="https://img.shields.io/pypi/pyversions/casperac.svg" alt="Python Versions"></a>
    <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT"></a>
  </p>
</div>

---

CasperAC is an advanced, automated network anonymization CLI tool designed to wrap any terminal command (like `curl`, `nmap`, or `wget`) in a highly secure **Dual-Layer (WARP + Tor)** tunnel. It features a true **Zero-Config Auto-Deploy** engine that installs and configures its own VPN and proxy infrastructure automatically.

## 🌟 The Dual-Layer Privacy Architecture

CasperAC employs a state-of-the-art dual-layer network stack to ensure maximum privacy and prevent Deep Packet Inspection (DPI):

1. **Layer 1: Cloudflare WARP (WireGuard VPN)**
   - All your system traffic is encrypted and sent to Cloudflare's edge network.
   - **Why?** Your local Internet Service Provider (ISP) or network administrator cannot see that you are using Tor. They only see a standard Cloudflare connection.
2. **Layer 2: The Onion Router (Tor)**
   - Inside the WARP tunnel, CasperAC routes your specific terminal command through the Tor network.
   - **Why?** The Tor Entry Node sees Cloudflare's IP instead of your real IP. Finally, the target server sees a random Tor Exit Node IP.

**Result:** Your ISP doesn't know you use Tor, the Tor network doesn't know your real IP, and the target server doesn't know who you are.

## ✨ Features

- 🚀 **Zero-Config Auto-Deploy:** If Tor or Cloudflare WARP are not installed, CasperAC automatically downloads, installs, and configures them for you via system package managers (Homebrew/APT).
- 🛡️ **Dual-Layer Security:** Combines Cloudflare WARP with Tor for ISP-blind, exit-node-anonymized traffic.
- 🔄 **Dynamic IP Rotation:** Effortlessly renew your Tor circuit with a single command to get a fresh IP address.
- **Environment Management**: Easily export or unset proxy environment variables for your current active shell session.
- **Fingerprint Evasion**: Injects standard browser User-Agents into the shell environment to help disguise underlying command fingerprints.

## 🚀 Installation

### Prerequisites
- Python 3.8+
- [Tor](https://www.torproject.org/) daemon installed and running locally on port 9050. Control port on 9051.
- [Cloudflare WARP CLI](https://developers.cloudflare.com/warp-client/get-started/linux/) (optional, but recommended for the dual-layer approach).

### Setup via PyPI (Recommended)
```bash
pip install casperac
```

### Setup from Source
```bash
git clone https://github.com/yourusername/casperac.git
cd casperac
pip install -e .
```

## 💻 Usage

```bash
# Check the status of your proxies
casperac status

# Run a specific command through the proxy chain
casperac run -- curl -I https://api.github.com/user

# Renew your Tor exit node
casperac renew

# Source proxy variables into your active shell session
eval $(casperac env-on)

# Revert proxy variables
eval $(casperac env-off)
```

## 🤝 Contributing
Contributions, issues and feature requests are welcome!
Feel free to check [issues page](https://github.com/yourusername/casperac/issues). You can also take a look at the [contributing guide](CONTRIBUTING.md).

## 📝 License
Copyright © 2024.
This project is [MIT](LICENSE) licensed.
