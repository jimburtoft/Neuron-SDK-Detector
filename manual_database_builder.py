#!/usr/bin/env python3
"""
Manually build the database with the correct package information
"""

import json

# Manually extracted package data from the documentation
NEURON_SDK_DATA = {
    "2.25.0": {
        "Trn1": {
            "aws-neuronx-collectives": "2.27.34.0",
            "aws-neuronx-dkms": "2.23.9.0",
            "aws-neuronx-gpsimd-customop-lib": "0.17.1.0",
            "aws-neuronx-gpsimd-tools": "0.17.0.0",
            "aws-neuronx-k8-plugin": "2.27.7.0",
            "aws-neuronx-k8-scheduler": "2.27.7.0",
            "aws-neuronx-oci-hook": "2.11.42.0",
            "aws-neuronx-runtime-discovery": "2.9",
            "aws-neuronx-runtime-lib": "2.27.23.0",
            "aws-neuronx-tools": "2.25.145.0",
            "jax_neuronx": "0.6.1.1.0.3499",
            "libneuronxla": "2.2.8201.0",
            "neuronx-cc": "2.20.9961.0",
            "neuronx-cc-stubs": "2.20.9961.0",
            "neuronx_distributed": "0.14.18461",
            "neuronx_distributed_training": "1.5.0",
            "neuronx_distributed_inference": "0.5.9230",
            "tensorboard-plugin-neuronx": "2.0.813.0",
            "tensorflow-model-server-neuronx": "2.10.1.2.12.2.0",
            "tensorflow-neuronx": "2.10.1.2.1.0",
            "torch-neuronx": "2.7.0.2.9.9357",
            "transformers-neuronx": "0.13.1216"
        },
        "Trn2": {
            "aws-neuronx-collectives": "2.27.34.0",
            "aws-neuronx-dkms": "2.23.9.0",
            "aws-neuronx-gpsimd-customop-lib": "0.17.1.0",
            "aws-neuronx-gpsimd-tools": "0.17.0.0",
            "aws-neuronx-k8-plugin": "2.27.7.0",
            "aws-neuronx-k8-scheduler": "2.27.7.0",
            "aws-neuronx-oci-hook": "2.11.42.0",
            "aws-neuronx-runtime-discovery": "2.9",
            "aws-neuronx-runtime-lib": "2.27.23.0",
            "aws-neuronx-tools": "2.25.145.0",
            "neuronx-cc": "2.20.9961.0",
            "neuronx-cc-stubs": "2.20.9961.0",
            "neuronx_distributed": "0.14.18461",
            "neuronx_distributed_training": "1.5.0",
            "neuronx_distributed_inference": "0.5.9230",
            "torch-neuronx": "2.7.0.2.9.9357"
        },
        "Inf2": {
            "aws-neuronx-collectives": "2.27.34.0",
            "aws-neuronx-dkms": "2.23.9.0",
            "aws-neuronx-gpsimd-customop-lib": "0.17.1.0",
            "aws-neuronx-gpsimd-tools": "0.17.0.0",
            "aws-neuronx-k8-plugin": "2.27.7.0",
            "aws-neuronx-k8-scheduler": "2.27.7.0",
            "aws-neuronx-oci-hook": "2.11.42.0",
            "aws-neuronx-runtime-discovery": "2.9",
            "aws-neuronx-runtime-lib": "2.27.23.0",
            "aws-neuronx-tools": "2.25.145.0",
            "jax_neuronx": "0.6.1.1.0.3499",
            "libneuronxla": "2.2.8201.0",
            "neuronx-cc": "2.20.9961.0",
            "neuronx-cc-stubs": "2.20.9961.0",
            "neuronx_distributed": "0.14.18461",
            "neuronx_distributed_inference": "0.5.9230",
            "tensorboard-plugin-neuronx": "2.0.813.0",
            "tensorflow-model-server-neuronx": "2.10.1.2.12.2.0",
            "tensorflow-neuronx": "2.10.1.2.1.0",
            "torch-neuronx": "2.7.0.2.9.9357",
            "transformers-neuronx": "0.13.1216"
        },
        "Inf1": {
            "aws-neuronx-collectives": "2.27.34.0",
            "aws-neuronx-dkms": "2.23.9.0",
            "aws-neuronx-k8-plugin": "2.27.7.0",
            "aws-neuronx-k8-scheduler": "2.27.7.0",
            "aws-neuronx-oci-hook": "2.11.42.0",
            "aws-neuronx-tools": "2.25.145.0",
            "mx_neuron": "1.8.0.2.4.147.0",
            "mxnet_neuron": "1.5.1.1.10.0.0",
            "neuron-cc": "1.24.0.0",
            "neuronperf": "1.8.93.0",
            "tensorflow-model-server-neuronx": "2.10.1.2.12.2.0",
            "tensorflow-neuron": "2.10.1.2.12.2.0",
            "torch-neuron": "1.13.1.2.11.13.0"
        }
    },
    # Add a sample second version for testing
    "2.24.0": {
        "Trn1": {
            "aws-neuronx-collectives": "2.26.43.0",
            "aws-neuronx-dkms": "2.22.2.0",
            "aws-neuronx-runtime-lib": "2.26.42.0",
            "aws-neuronx-tools": "2.24.54.0",
            "neuronx-cc": "2.19.8089.0",
            "torch-neuronx": "2.7.0.2.8.6734",
            "transformers-neuronx": "0.13.985"
        },
        "Trn2": {
            "aws-neuronx-collectives": "2.26.43.0",
            "aws-neuronx-dkms": "2.22.2.0",
            "aws-neuronx-runtime-lib": "2.26.42.0",
            "aws-neuronx-tools": "2.24.54.0",
            "neuronx-cc": "2.19.8089.0",
            "torch-neuronx": "2.7.0.2.8.6734"
        },
        "Inf2": {
            "aws-neuronx-collectives": "2.26.43.0",
            "aws-neuronx-dkms": "2.22.2.0",
            "aws-neuronx-runtime-lib": "2.26.42.0",
            "aws-neuronx-tools": "2.24.54.0",
            "neuronx-cc": "2.19.8089.0",
            "torch-neuronx": "2.7.0.2.8.6734",
            "transformers-neuronx": "0.13.985"
        },
        "Inf1": {
            "aws-neuronx-collectives": "2.26.43.0",
            "aws-neuronx-dkms": "2.22.2.0",
            "aws-neuronx-tools": "2.24.54.0",
            "mx_neuron": "1.8.0.2.4.147.0",
            "neuron-cc": "1.24.0.0",
            "torch-neuron": "1.13.1.2.11.13.0"
        }
    }
}

def main():
    # Save the database
    with open('neuron_versions.json', 'w') as f:
        json.dump(NEURON_SDK_DATA, f, indent=2, sort_keys=True)
    
    print("Database created successfully!")
    print(f"Includes {len(NEURON_SDK_DATA)} SDK versions:")
    
    for version, platforms in NEURON_SDK_DATA.items():
        total_packages = sum(len(packages) for packages in platforms.values())
        print(f"  {version}: {total_packages} total packages")
        for platform, packages in platforms.items():
            print(f"    {platform}: {len(packages)} packages")

if __name__ == '__main__':
    main()