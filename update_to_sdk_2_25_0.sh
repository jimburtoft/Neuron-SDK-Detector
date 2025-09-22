#!/bin/bash
# AWS Neuron SDK 2.25.0 Update Script
# Release Date: 07/31/2025
# Only updates packages that are already installed

set -e

echo "Updating to AWS Neuron SDK 2.25.0 (07/31/2025)"
echo "This script only updates packages that are already installed."
echo ""

# Update package lists
echo "Updating package lists..."
sudo apt-get update

# System packages - only upgrade what's already installed
echo "Updating system packages (if installed)..."
sudo apt install --only-upgrade -y --allow-downgrades --allow-change-held-packages \
  aws-neuronx-collectives=2.27.34.0* \
  aws-neuronx-dkms=2.23.9.0* \
  aws-neuronx-gpsimd-customop-lib=0.17.1.0* \
  aws-neuronx-gpsimd-tools=0.17.0.0* \
  aws-neuronx-k8-plugin=2.27.7.0* \
  aws-neuronx-k8-scheduler=2.27.7.0* \
  aws-neuronx-oci-hook=2.11.42.0* \
  aws-neuronx-runtime-lib=2.27.23.0* \
  aws-neuronx-tools=2.25.145.0*

# Python packages - pip naturally skips uninstalled packages with --upgrade
echo "Updating Python packages (if installed)..."
pip install --upgrade \
  aws-neuronx-runtime-discovery==2.9 \
  libneuronxla==2.2.8201.0 \
  neuronx_cc==2.20.9961.0 \
  neuronx_cc_stubs==2.20.9961.0 \
  neuronx_distributed==0.14.18461 \
  neuronx_distributed_inference==0.5.9230 \
  tensorboard_plugin_neuronx==2.0.813.0 \
  tensorflow_model_server_neuronx==2.10.1.2.12.2.0 \
  tensorflow_neuronx==2.10.1.2.1.0 \
  torch-neuronx==2.7.0.2.9.9357 \
  transformers_neuronx==0.13.1216

echo ""
echo "AWS Neuron SDK 2.25.0 update complete!"
echo ""
echo "To verify your installation:"
echo "  python3 neuron_detector.py --verbose"
echo ""

# Uncomment the sections below for FRESH INSTALLATION (installs ALL packages):

# echo "Fresh installation - installing all SDK 2.25.0 system packages..."
# sudo apt install -y \
#   aws-neuronx-collectives=2.27.34.0* \
#   aws-neuronx-dkms=2.23.9.0* \
#   aws-neuronx-gpsimd-customop-lib=0.17.1.0* \
#   aws-neuronx-gpsimd-tools=0.17.0.0* \
#   aws-neuronx-k8-plugin=2.27.7.0* \
#   aws-neuronx-k8-scheduler=2.27.7.0* \
#   aws-neuronx-oci-hook=2.11.42.0* \
#   aws-neuronx-runtime-lib=2.27.23.0* \
#   aws-neuronx-tools=2.25.145.0*

# echo "Fresh installation - installing all SDK 2.25.0 Python packages..."
# pip install \
#   aws-neuronx-runtime-discovery==2.9 \
#   libneuronxla==2.2.8201.0 \
#   neuronx_cc==2.20.9961.0 \
#   neuronx_cc_stubs==2.20.9961.0 \
#   neuronx_distributed==0.14.18461 \
#   neuronx_distributed_inference==0.5.9230 \
#   tensorboard_plugin_neuronx==2.0.813.0 \
#   tensorflow_model_server_neuronx==2.10.1.2.12.2.0 \
#   tensorflow_neuronx==2.10.1.2.1.0 \
#   torch-neuronx==2.7.0.2.9.9357 \
#   transformers_neuronx==0.13.1216
