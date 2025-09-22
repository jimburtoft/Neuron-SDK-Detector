#!/bin/bash
# AWS Neuron SDK 2.24.0 Update Script
# Release Date: 06/24/2025
# Only updates packages that are already installed

set -e

echo "Updating to AWS Neuron SDK 2.24.0 (06/24/2025)"
echo "This script only updates packages that are already installed."
echo ""

# Update package lists
echo "Updating package lists..."
sudo apt-get update

# System packages - only upgrade what's already installed
echo "Updating system packages (if installed)..."
sudo apt install --only-upgrade -y --allow-downgrades --allow-change-held-packages \
  aws-neuronx-collectives=2.26.43.0* \
  aws-neuronx-dkms=2.22.2.0* \
  aws-neuronx-gpsimd-customop-lib=0.16.2.0* \
  aws-neuronx-gpsimd-tools=0.16.1.0* \
  aws-neuronx-k8-plugin=2.26.7.0* \
  aws-neuronx-k8-scheduler=2.26.7.0* \
  aws-neuronx-oci-hook=2.10.56.0* \
  aws-neuronx-runtime-lib=2.26.42.0* \
  aws-neuronx-tools=2.24.54.0*

# Python packages - only upgrade packages that are already installed
echo "Updating Python packages (if installed)..."

# Check which packages are installed and upgrade only those
declare -a packages=(
  "aws-neuronx-runtime-discovery==2.9"
  "libneuronxla==2.2.4410.0"
  "neuronx_cc==2.19.8089.0"
  "neuronx_cc_stubs==2.19.8089.0"
  "neuronx_distributed==0.13.14393"
  "neuronx_distributed_inference==0.4.7422"
  "tensorboard_plugin_neuronx==2.0.760.0"
  "tensorflow_model_server_neuronx==2.8.4.2.12.2.0"
  "tensorflow_neuronx==2.10.1.2.1.0"
  "torch-neuronx==2.7.0.2.8.6734"
  "torch_xla==2.1.6"
  "transformers_neuronx==0.13.985"
)

for package_spec in "${packages[@]}"; do
  package_name="${package_spec%%==*}"
  # Check if package is installed (pip show returns 0 if installed)
  if pip show "$package_name" >/dev/null 2>&1; then
    echo "Upgrading $package_name..."
    pip install --upgrade "$package_spec"
  fi
done

echo ""
echo "AWS Neuron SDK 2.24.0 update complete!"
echo ""
echo "To verify your installation:"
echo "  python3 neuron_detector.py --verbose"
echo ""

# Uncomment the sections below for FRESH INSTALLATION (installs ALL packages):

# echo "Fresh installation - installing all SDK 2.24.0 system packages..."
# sudo apt install -y \
#   aws-neuronx-collectives=2.26.43.0* \
#   aws-neuronx-dkms=2.22.2.0* \
#   aws-neuronx-gpsimd-customop-lib=0.16.2.0* \
#   aws-neuronx-gpsimd-tools=0.16.1.0* \
#   aws-neuronx-k8-plugin=2.26.7.0* \
#   aws-neuronx-k8-scheduler=2.26.7.0* \
#   aws-neuronx-oci-hook=2.10.56.0* \
#   aws-neuronx-runtime-lib=2.26.42.0* \
#   aws-neuronx-tools=2.24.54.0*

# echo "Fresh installation - installing all SDK 2.24.0 Python packages..."
# pip install \
#   aws-neuronx-runtime-discovery==2.9 \
#   libneuronxla==2.2.4410.0 \
#   neuronx_cc==2.19.8089.0 \
#   neuronx_cc_stubs==2.19.8089.0 \
#   neuronx_distributed==0.13.14393 \
#   neuronx_distributed_inference==0.4.7422 \
#   tensorboard_plugin_neuronx==2.0.760.0 \
#   tensorflow_model_server_neuronx==2.8.4.2.12.2.0 \
#   tensorflow_neuronx==2.10.1.2.1.0 \
#   torch-neuronx==2.7.0.2.8.6734 \
#   torch_xla==2.1.6 \
#   transformers_neuronx==0.13.985
