#!/bin/bash
# AWS Neuron SDK 2.27.1 Update Script
# Release Date: 01/14/2026
# Only updates packages that are already installed

set -e

echo "Updating to AWS Neuron SDK 2.27.1 (01/14/2026)"
echo "This script only updates packages that are already installed."
echo ""

# Update package lists
echo "Updating package lists..."
sudo apt-get update

# System packages - only upgrade what's already installed
echo "Updating system packages (if installed)..."
sudo apt install --only-upgrade -y --allow-downgrades --allow-change-held-packages \
  aws-neuronx-collectives=2.29.41.0* \
  aws-neuronx-dkms=2.25.4.0* \
  aws-neuronx-gpsimd-customop-lib=0.19.2.0* \
  aws-neuronx-gpsimd-tools=0.19.1.0* \
  aws-neuronx-k8-plugin=2.29.16.0* \
  aws-neuronx-k8-scheduler=2.29.16.0* \
  aws-neuronx-oci-hook=2.13.52.0* \
  aws-neuronx-runtime-lib=2.29.40.0* \
  aws-neuronx-tools=2.27.33.0*

# Python packages - only upgrade packages that are already installed
echo "Updating Python packages (if installed)..."

# Check which packages are installed and upgrade only those
declare -a packages=(
  "libneuronxla==2.2.14584.0"
  "neuronx-cc==2.22.12471.0"
  "neuronx-cc-stubs==2.22.12471.0"
  "neuronx-distributed==0.16.25997"
  "neuronx-distributed-training==1.7.0"
  "neuronx-distributed-inference==0.7.15063"
  "nki==0.1.0"
  "tensorboard-plugin-neuronx==2.0.918.0"
  "tensorflow-neuronx==2.10.1.2.1.0"
  "torch-neuronx==2.9.0.2.11.19912"
  "jax-neuronx==0.7.0.1.0.7377"
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
echo "AWS Neuron SDK 2.27.1 update complete!"
echo ""
echo "Changes in SDK 2.27.1:"
echo "• Updated neuronx-distributed-inference (0.7.14366 → 0.7.15063)"
echo ""
echo "To verify your installation:"
echo "  python3 neuron_detector.py --verbose"
echo ""

# Uncomment the sections below for FRESH INSTALLATION (installs ALL packages):

# echo "Fresh installation - installing all SDK 2.27.1 system packages..."
# sudo apt install -y \
#   aws-neuronx-collectives=2.29.41.0* \
#   aws-neuronx-dkms=2.25.4.0* \
#   aws-neuronx-gpsimd-customop-lib=0.19.2.0* \
#   aws-neuronx-gpsimd-tools=0.19.1.0* \
#   aws-neuronx-k8-plugin=2.29.16.0* \
#   aws-neuronx-k8-scheduler=2.29.16.0* \
#   aws-neuronx-oci-hook=2.13.52.0* \
#   aws-neuronx-runtime-lib=2.29.40.0* \
#   aws-neuronx-tools=2.27.33.0*

# echo "Fresh installation - installing all SDK 2.27.1 Python packages..."
# pip install --extra-index-url=https://pip.repos.neuron.amazonaws.com \
#   libneuronxla==2.2.14584.0 \
#   neuronx-cc==2.22.12471.0 \
#   neuronx-cc-stubs==2.22.12471.0 \
#   neuronx-distributed==0.16.25997 \
#   neuronx-distributed-training==1.7.0 \
#   neuronx-distributed-inference==0.7.15063 \
#   nki==0.1.0 \
#   tensorboard-plugin-neuronx==2.0.918.0 \
#   tensorflow-neuronx==2.10.1.2.1.0 \
#   torch-neuronx==2.9.0.2.11.19912 \
#   jax-neuronx==0.7.0.1.0.7377
