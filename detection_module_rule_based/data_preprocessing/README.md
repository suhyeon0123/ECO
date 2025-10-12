# Data Preprocessing Module

This module handles the extraction of source code from JSONL files and the generation of Code Property Graphs (CPGs) using Joern.

## Prerequisites

- Python 3.x
- Singularity container runtime
- Joern singularity image (joern.sif)

## File Structure

- `extract_source.py`: Extracts source code from JSONL files
- `process_inside_container.sh`: Processes source files within a Joern container
- `run.sh`: Main script that orchestrates the entire preprocessing pipeline

## Usage

### Main Pipeline
