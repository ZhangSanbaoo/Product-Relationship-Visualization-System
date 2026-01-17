#!/usr/bin/env bash
set -e

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
