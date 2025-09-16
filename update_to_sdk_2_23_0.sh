#!/bin/bash
# AWS Neuron SDK 2.23.0 Update Script
# Release Date: 05/20/2025
# Only updates packages that are already installed

set -e

echo "Updating to AWS Neuron SDK 2.23.0 (05/20/2025)"
echo "This script only updates packages that are already installed."
echo ""

# Update package lists
echo "Updating package lists..."
sudo apt-get update

# System packages - only upgrade what's already installed
echo "Updating system packages (if installed)..."
sudo apt install --only-upgrade -y --allow-downgrades --allow-change-held-packages \
  aws-neuronx-collectives=2.25.65.0* \
  aws-neuronx-dkms=2.21.37.0* \
  aws-neuronx-gpsimd-customop-lib=0.15.12.0* \
  aws-neuronx-gpsimd-tools=0.15.1.0* \
  aws-neuronx-k8-plugin=2.25.24.0* \
  aws-neuronx-k8-scheduler=2.25.24.0* \
  aws-neuronx-oci-hook=2.9.88.0* \
  aws-neuronx-runtime-discovery=2.9* \
  aws-neuronx-runtime-lib=2.25.57.0* \
  aws-neuronx-tools=2.23.9.0*

# Python packages - pip naturally skips uninstalled packages with --upgrade
echo "Updating Python packages (if installed)..."
pip install --upgrade \
  libneuronxla==2.2.3493.0 \
  neuronx_cc==2.18.121.0 \
  neuronx_cc_stubs==2.18.121.0 \
  neuronx_distributed==0.12.12111 \
  neuronx_distributed_inference==0.3.5591 \
  tensorboard_plugin_neuronx==2.0.670.0 \
  tensorflow_model_server_neuronx==2.8.4.2.12.2.0 \
  tensorflow_neuronx==2.10.1.2.1.0 \
  torch-neuronx==2.6.0.2.7.5413 \
  torch_xla==2.1.6 \
  transformers_neuronx==0.13.798

echo ""
echo "AWS Neuron SDK 2.23.0 update complete!"
echo ""
echo "To verify your installation:"
echo "  python3 neuron_detector.py --verbose"
echo ""

# Uncomment the sections below for FRESH INSTALLATION (installs ALL packages):

# echo "Fresh installation - installing all SDK 2.23.0 system packages..."
# sudo apt install -y \
#   aws-neuronx-collectives=2.25.65.0* \
#   aws-neuronx-dkms=2.21.37.0* \
#   aws-neuronx-gpsimd-customop-lib=0.15.12.0* \
#   aws-neuronx-gpsimd-tools=0.15.1.0* \
#   aws-neuronx-k8-plugin=2.25.24.0* \
#   aws-neuronx-k8-scheduler=2.25.24.0* \
#   aws-neuronx-oci-hook=2.9.88.0* \
#   aws-neuronx-runtime-discovery=2.9* \
#   aws-neuronx-runtime-lib=2.25.57.0* \
#   aws-neuronx-tools=2.23.9.0*

# echo "Fresh installation - installing all SDK 2.23.0 Python packages..."
# pip install \
#   libneuronxla==2.2.3493.0 \
#   neuronx_cc==2.18.121.0 \
#   neuronx_cc_stubs==2.18.121.0 \
#   neuronx_distributed==0.12.12111 \
#   neuronx_distributed_inference==0.3.5591 \
#   tensorboard_plugin_neuronx==2.0.670.0 \
#   tensorflow_model_server_neuronx==2.8.4.2.12.2.0 \
#   tensorflow_neuronx==2.10.1.2.1.0 \
#   torch-neuronx==2.6.0.2.7.5413 \
#   torch_xla==2.1.6 \
#   transformers_neuronx==0.13.798
