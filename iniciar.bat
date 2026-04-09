@echo off
echo Preparando o ambiente Pro...
python -m pip install streamlit yfinance ta plotly pandas numpy

echo.
echo Iniciando o App Cripto Premium...
python -m streamlit run app.py
pause