#!/bin/bash
# AWS Neuron SDK 2.28.0 Update Script
# Release Date: 02/26/2026
# Only updates packages that are already installed

set -e

echo "Updating to AWS Neuron SDK 2.28.0 (02/26/2026)"
echo "This script only updates packages that are already installed."
echo ""

# Update package lists
echo "Updating package lists..."
sudo apt-get update

# System packages - only upgrade what's already installed
echo "Updating system packages (if installed)..."
sudo apt install --only-upgrade -y --allow-downgrades --allow-change-held-packages \
  aws-neuronx-collectives=2.30.59.0* \
  aws-neuronx-dkms=2.26.5.0* \
  aws-neuronx-gpsimd-customop-lib=0.20.4.0* \
  aws-neuronx-gpsimd-tools=0.20.1.0* \
  aws-neuronx-k8-plugin=2.29.71.0* \
  aws-neuronx-k8-scheduler=2.29.71.0* \
  aws-neuronx-oci-hook=2.14.102.0* \
  aws-neuronx-runtime-lib=2.30.51.0* \
  aws-neuronx-tools=2.28.23.0*

# Python packages - only upgrade packages that are already installed
echo "Updating Python packages (if installed)..."

# Check which packages are installed and upgrade only those
declare -a packages=(
  "libneuronxla==2.2.15515.0"
  "neuronx-cc==2.23.6484.0"
  "neuronx-cc-stubs==2.23.6484.0"
  "neuronx-distributed==0.17.26814"
  "neuronx-distributed-training==1.7.0"
  "neuronx-distributed-inference==0.8.16251"
  "nki==0.2.0"
  "tensorboard-plugin-neuronx==2.0.918.0"
  "tensorflow-neuronx==2.10.1.2.1.0"
  "torch-neuronx==2.9.0.2.12.22436"
  "jax-neuronx==0.7.0.1.0.7584"
)

for package_spec in "${packages[@]}"; do
  package_name="${package_spec%%==*}"
  # Check if package is installed (pip show returns 0 if installed)
  if pip show "$package_name" >/dev/null 2>&1; then
    echo "Upgrading $package_name..."
    pip install --upgrade --extra-index-url=https://pip.repos.neuron.amazonaws.com "$package_spec"
  fi
done

echo ""
echo "AWS Neuron SDK 2.28.0 update complete!"
echo ""
echo "What's new in SDK 2.28.0:"
echo "• Updated compiler (neuronx-cc 2.23.6484.0)"
echo "• Updated runtime (aws-neuronx-runtime-lib 2.30.51.0)"
echo "• Updated neuronx-distributed (0.17.26814)"
echo "• Updated neuronx-distributed-inference (0.8.16251)"
echo "• NKI updated to 0.2.0"
echo ""
echo "To verify your installation:"
echo "  python3 neuron_detector.py --verbose"
echo ""

# Uncomment the sections below for FRESH INSTALLATION (installs ALL packages):

# echo "Fresh installation - installing all SDK 2.28.0 system packages..."
# sudo apt install -y \
#   aws-neuronx-collectives=2.30.59.0* \
#   aws-neuronx-dkms=2.26.5.0* \
#   aws-neuronx-gpsimd-customop-lib=0.20.4.0* \
#   aws-neuronx-gpsimd-tools=0.20.1.0* \
#   aws-neuronx-k8-plugin=2.29.71.0* \
#   aws-neuronx-k8-scheduler=2.29.71.0* \
#   aws-neuronx-oci-hook=2.14.102.0* \
#   aws-neuronx-runtime-lib=2.30.51.0* \
#   aws-neuronx-tools=2.28.23.0*

# echo "Fresh installation - installing all SDK 2.28.0 Python packages..."
# pip install --extra-index-url=https://pip.repos.neuron.amazonaws.com \
#   libneuronxla==2.2.15515.0 \
#   neuronx-cc==2.23.6484.0 \
#   neuronx-cc-stubs==2.23.6484.0 \
#   neuronx-distributed==0.17.26814 \
#   neuronx-distributed-training==1.7.0 \
#   neuronx-distributed-inference==0.8.16251 \
#   nki==0.2.0 \
#   tensorboard-plugin-neuronx==2.0.918.0 \
#   tensorflow-neuronx==2.10.1.2.1.0 \
#   torch-neuronx==2.9.0.2.12.22436 \
#   jax-neuronx==0.7.0.1.0.7584
