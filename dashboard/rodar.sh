if [ -d /opt/homebrew/opt/openssl@3/lib ]; then
    export DYLD_LIBRARY_PATH=/opt/homebrew/opt/openssl@3/lib
fi

cd "$(dirname "$0")/.." || exit 1
exec dashboard/.venv/bin/streamlit run dashboard/app.py "$@"
