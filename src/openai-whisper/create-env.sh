#!/bin/bash

# script setup
PYTHON_ENV_NAME="proj-openai-whisper"
eval "$(conda shell.bash hook)"
conda activate base

# commands
echo "--- Removing conda environment: $PYTHON_ENV_NAME ---"
conda env remove -n $PYTHON_ENV_NAME -y
echo "--- Creating conda environment using name: $PYTHON_ENV_NAME ---"
conda create -n $PYTHON_ENV_NAME python=3.10 -y

echo "--- Activating conda environment: $PYTHON_ENV_NAME ---"
conda activate $PYTHON_ENV_NAME


echo "--- Installing dependences from https://github.com/openai/whisper ---"
pip install -U openai-whisper

echo "Run 'conda activate $PYTHON_ENV_NAME' to activate the environment"