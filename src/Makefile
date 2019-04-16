SHELL := /bin/bash

all: install
install:
	sudo apt install python3
	sudo apt-get install python3-venv
	python3 -m venv transportation-models-env
	source transportation-models-env/bin/activate && \
	pip install websockets && \
	python ./vehicle_generation.py ./data.json 10 50 && \
	wget https://codeload.github.com/toji/gl-matrix/zip/v3.0.0 && \
	unzip ./v3.0.0 && \
	mv ./gl-matrix-3.0.0/dist/gl-matrix.js ./ && \
	rm -f ./gl-matrix.zip && \
	rm -rf ./gl-matrix-3.0.0 && \
	python -m webbrowser -t "./index.html" && \
	python ./main.py
clean:
	rm -f ./gl-matrix.js ./vehicle_layout.json
	rm -rf ./transportation-models-env
