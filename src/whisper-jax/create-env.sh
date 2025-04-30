#!/bin/bash

# Check if conda is installed
if ! command -v conda &> /dev/null
then
  echo "conda command was not found. Exiting"
  exit 1
fi

# script setup
PYTHON_ENV_NAME="proj-whisper-jax"
eval "$(conda shell.bash hook)"
conda activate base

# commands
echo "--- Removing conda environment: $PYTHON_ENV_NAME ---"
conda env remove -n $PYTHON_ENV_NAME -y
echo "--- Creating conda environment using name: $PYTHON_ENV_NAME ---"
conda create -n $PYTHON_ENV_NAME python=3.9 -y

echo "--- Activating conda environment: $PYTHON_ENV_NAME ---"
conda activate $PYTHON_ENV_NAME
if [[ $PYTHON_ENV_NAME != $(conda env list | grep "\*" | cut -d " " -f1) ]]
then
  echo "Error activating environment"
  exit 1
else
  echo "Succesfully activated"
fi

echo "--- Installing dependences from https://github.com/pip install -U "jax[cuda12]" ---"
pip install --upgrade pip

# installing jax base: https://github.com/jax-ml/jax?tab=readme-ov-file#instructions
# cpu
# pip install -U "jax"

# gpu version cuda 12
pip install -U "jax[cuda12]"

# Installing whisper-jax: https://github.com/sanchit-gandhi/whisper-jax?tab=readme-ov-file#installation
pip install git+https://github.com/sanchit-gandhi/whisper-jax.git


echo "Run 'conda activate $PYTHON_ENV_NAME' to activate the environment"
