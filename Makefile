.PHONY: api ui test setup cache

setup:
	pip install -r requirements.txt

cache:
	python scratch/generate_parquet.py

api:
	python -X utf8 src/main.py

ui:
	streamlit run app.py

test:
	pytest tests/ -v
