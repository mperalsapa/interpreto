#!/bin/bash

# Check if conda is installed
if ! command -v conda &> /dev/null
then
  echo "conda command was not found. Exiting"
  exit 1
fi

# script setup
PYTHON_ENV_NAME="proj-faster-whisper-0.10"
eval "$(conda shell.bash hook)"
conda activate base

# commands
echo "--- Removing conda environment: $PYTHON_ENV_NAME ---"
conda env remove -n $PYTHON_ENV_NAME -y
echo "--- Creating conda environment using name: $PYTHON_ENV_NAME ---"
conda create -n $PYTHON_ENV_NAME python=3.12 -y

echo "--- Activating conda environment: $PYTHON_ENV_NAME ---"
conda activate $PYTHON_ENV_NAME
if [[ $PYTHON_ENV_NAME != $(conda env list | grep "\*" | cut -d " " -f1) ]]
then
  echo "Error activating environment"
  exit 1
else
  echo "Succesfully activated"
fi

echo "--- Installing dependences from https://github.com/SYSTRAN/faster-whisper ---"
pip install --upgrade pip
pip install faster-whisper==0.10

# cuda 11
pip install nvidia-cublas-cu11 nvidia-cudnn-cu11==8.*
pip install --force-reinstall ctranslate2==3.24.0

echo "Run 'conda activate $PYTHON_ENV_NAME' to activate the environment"
