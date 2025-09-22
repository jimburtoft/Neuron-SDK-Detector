#!/bin/bash
# AWS Neuron SDK 2.26.0 Update Script
# Generated for SDK version: 2.26.0 (Release Date: 09/18/2025)
#
# This script updates existing Neuron packages to SDK 2.26.0 versions using native
# package managers (apt --only-upgrade and pip --upgrade) to update only currently 
# installed packages.
#
# Features in SDK 2.26.0:
# - PyTorch 2.8 support added
# - JAX 0.6.2 support 
# - Python 3.11 support introduced
# - Enhanced inference capabilities on Trainium2 (Trn2) instances
# - Llama 4 Scout and Maverick variants (beta) on Trn2 instances
# - FLUX.1-dev image generation models (beta) on Trn2
# - Expert parallelism support (beta)
# - On-device forward pipeline execution (beta)
# - Sequence parallelism in MoE routers
# - End-of-support for Transformers NeuronX library

echo "🚀 AWS Neuron SDK 2.26.0 Update Script"
echo "======================================"
echo "Target SDK: 2.26.0 (Released: 09/18/2025)"
echo "Update method: Only upgrade currently installed packages"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "⚠️  Running as root. System packages will be updated."
    SUDO=""
else
    echo "👤 Running as regular user. Will use sudo for system packages."
    SUDO="sudo"
fi

echo ""
echo "🔍 Checking current Neuron installation..."

# Function to check if a package is installed via apt
is_apt_package_installed() {
    dpkg -l "$1" 2>/dev/null | grep -q "^ii\|^hi"
}

# Function to check if a Python package is installed
is_python_package_installed() {
    python3 -c "import $1" 2>/dev/null
}

# Function to check if pip package is installed
is_pip_package_installed() {
    pip list 2>/dev/null | grep -q "^$1 "
}

apt_packages_found=false
python_packages_found=false

echo ""
echo "📦 System packages that will be updated:"

# Check each system package
declare -a system_packages=(
    "aws-neuronx-collectives=2.28.27.0*"
    "aws-neuronx-dkms=2.24.7.0*" 
    "aws-neuronx-gpsimd-customop-lib=0.18.0.0*"
    "aws-neuronx-gpsimd-tools=0.18.0.0*"
    "aws-neuronx-k8-plugin=2.28.4.0*"
    "aws-neuronx-k8-scheduler=2.28.4.0*"
    "aws-neuronx-oci-hook=2.12.36.0*"
    "aws-neuronx-runtime-lib=2.28.23.0*"
    "aws-neuronx-tools=2.26.14.0*"
)

for package_spec in "${system_packages[@]}"; do
    package_name="${package_spec%=*}"
    if is_apt_package_installed "$package_name"; then
        echo "  ✓ $package_name"
        apt_packages_found=true
    fi
done

echo ""
echo "🐍 Python packages that will be updated:"

# Check Python packages using import names
declare -A python_import_to_pip=(
    ["neuronxcc"]="neuronx-cc==2.21.18209.0"
    ["libneuronxla"]="libneuronxla==2.2.12677.0" 
    ["torch_neuronx"]="torch-neuronx==2.8.0.2.10.13553"
    ["transformers_neuronx"]="transformers-neuronx==0.13.1315"
    ["jax_neuronx"]="jax-neuronx==0.6.2.1.0.6446"
    ["neuronx_distributed"]="neuronx-distributed==0.15.22404"
    ["neuronx_distributed_training"]="neuronx-distributed-training==1.6.0"
    ["neuronx_distributed_inference"]="neuronx-distributed-inference==0.6.10598"
    ["tensorboard_plugin_neuronx"]="tensorboard-plugin-neuronx==2.0.837.0"
    ["tensorflow_neuronx"]="tensorflow-neuronx==2.10.1.2.1.0"
)

for import_name in "${!python_import_to_pip[@]}"; do
    if is_python_package_installed "$import_name"; then
        package_spec="${python_import_to_pip[$import_name]}"
        package_name="${package_spec%==*}"
        echo "  ✓ $package_name" 
        python_packages_found=true
    fi
done

if [ "$apt_packages_found" = false ] && [ "$python_packages_found" = false ]; then
    echo ""
    echo "ℹ️  No Neuron packages detected in current environment."
    echo "   This script only updates existing installations."
    echo ""
    echo "📝 For fresh installation, use these commands:"
    echo ""
    echo "# System packages (choose relevant ones):"
    for package_spec in "${system_packages[@]}"; do
        echo "#   $SUDO apt install ${package_spec}"
    done
    echo ""
    echo "# Python packages (choose relevant ones):"
    for import_name in "${!python_import_to_pip[@]}"; do
        package_spec="${python_import_to_pip[$import_name]}"
        echo "#   pip install ${package_spec}"
    done
    echo ""
    exit 0
fi

echo ""
read -p "🤔 Proceed with update? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Update cancelled."
    exit 0
fi

echo ""
echo "🔄 Starting update process..."

# Update system packages if any were found
if [ "$apt_packages_found" = true ]; then
    echo ""
    echo "📦 Updating system packages..."
    
    # Update package lists
    echo "  🔄 Updating package lists..."
    $SUDO apt update
    
    # Build the upgrade command with specific versions
    upgrade_cmd="$SUDO apt install --only-upgrade -y"
    for package_spec in "${system_packages[@]}"; do
        package_name="${package_spec%=*}"
        if is_apt_package_installed "$package_name"; then
            upgrade_cmd="$upgrade_cmd $package_spec"
        fi
    done
    
    echo "  🔄 Upgrading system packages..."
    echo "     Command: ${upgrade_cmd}"
    eval "$upgrade_cmd"
    
    if [ $? -eq 0 ]; then
        echo "  ✅ System packages updated successfully"
    else
        echo "  ❌ System package update failed"
        exit 1
    fi
fi

# Update Python packages if any were found
if [ "$python_packages_found" = true ]; then
    echo ""
    echo "🐍 Updating Python packages..."
    
    # Collect packages to update
    packages_to_update=()
    for import_name in "${!python_import_to_pip[@]}"; do
        if is_python_package_installed "$import_name"; then
            package_spec="${python_import_to_pip[$import_name]}"
            packages_to_update+=("$package_spec")
        fi
    done
    
    if [ ${#packages_to_update[@]} -gt 0 ]; then
        echo "  🔄 Upgrading Python packages..."
        pip install --upgrade --extra-index-url=https://pip.repos.neuron.amazonaws.com "${packages_to_update[@]}"
        
        if [ $? -eq 0 ]; then
            echo "  ✅ Python packages updated successfully"
        else
            echo "  ❌ Python package update failed"
            exit 1
        fi
    fi
fi

echo ""
echo "🎉 Update to AWS Neuron SDK 2.26.0 completed successfully!"
echo ""
echo "📝 Important Notes for SDK 2.26.0:"
echo "   • End-of-support for Transformers NeuronX library"
echo "   • PyTorch 2.8, JAX 0.6.2, and Python 3.11 support added"
echo "   • Driver versions >2.21 only support non-Inf1 instances"
echo "   • For Inf1 users: use Neuron driver 2.21 or below"
echo ""
echo "🔍 To verify the update:"
echo "   python3 neuron_detector.py --verbose"
echo ""
echo "📚 Release notes: https://awsdocs-neuron.readthedocs-hosted.com/en/latest/release-notes/2.26.0/"