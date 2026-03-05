#!/usr/bin/env sh

set -e

if [ -d ".venv" ]
then
    . .venv/bin/activate
else
    python3 -m venv .venv
    . .venv/bin/activate
    python3 -m pip install -r requirements.txt
fi

exec streamlit run app.py "$@"
