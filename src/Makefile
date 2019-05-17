SHELL := /bin/bash

all: install
install:
	sudo apt install python3
	sudo apt-get install python3-venv
	sudo apt-get install python3-tk
	python3 -m venv transportation-models-env
	source transportation-models-env/bin/activate && \
	pip install websockets && \
	pip install matplotlib && \
	wget https://codeload.github.com/toji/gl-matrix/zip/v3.0.0 && \
	unzip ./v3.0.0 && \
	mv ./gl-matrix-3.0.0/dist/gl-matrix.js ./ && \
	rm -f ./v3.0.0 && \
	rm -rf ./gl-matrix-3.0.0 && \
	python -m webbrowser -t "./index.html" && \
	python ./main.py
fedora:
	python3 -m venv transportation-models-env
	source transportation-models-env/bin/activate && \
	pip install websockets && \
	pip install matplotlib && \
	wget https://codeload.github.com/toji/gl-matrix/zip/v3.0.0 && \
	unzip ./v3.0.0 && \
	mv ./gl-matrix-3.0.0/dist/gl-matrix.js ./ && \
	rm -f ./v3.0.0 && \
	rm -rf ./gl-matrix-3.0.0 && \
	python -m webbrowser -t "./index.html" && \
	python ./main.py
offline:
	source transportation-models-env/bin/activate && \
	python -m webbrowser -t "./index.html" && \
	python ./main.py
clean:
	rm -f ./gl-matrix.js
	rm -rf ./transportation-models-env
