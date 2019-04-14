SHELL := /bin/bash

all:
	$(python) -m venv transportation-models-env
	source transportation-models-env/bin/activate && \
	pip install websockets && \
	python ./vehicle_generation.py ./data.json 10 50 && \
	curl -o ./gl-matrix.zip https://codeload.github.com/toji/gl-matrix/zip/v3.0.0 && \
	unzip ./gl-matrix.zip && \
	mv ./gl-matrix-3.0.0/dist/gl-matrix.js ./ && \
	rm -f ./gl-matrix.zip && \
	rm -rf ./gl-matrix-3.0.0 && \
	python -m webbrowser -t "./index.html" && \
	python ./main.py
clean:
	rm -f ./gl-matrix.js ./vehicle_layout.json
	rm -rf ./transportation-models-env
