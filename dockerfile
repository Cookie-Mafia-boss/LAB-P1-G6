FROM python:3.12.5 

WORKDIR /app


COPY ai_layer.py .
COPY data_layer.py .
COPY input_output_layer.py .
COPY logic_layer.py .
COPY food_inventory_dataset.csv .
COPY test_script.py . 
COPY main.py .


COPY dependency.txt .
RUN pip install --no-cache-dir -r dependency.txt

CMD  ["python", "main.py"]

#the . is very important It tells Docker to look for the Dockerfile inside the current directory.

#docker commands 
# docker build 
#docker build  -t inf1103-labs-smart-auditor-persistence .    

# this is the example for how to run the docker image
# docker run --rm -it inf1103-labs-smart-auditor-persistence

