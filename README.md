## Introduction

This is a desktop application for road-damage datection. This application exposes the models generated in the [Backend repository](https://github.com/allanes/pothole-detector-backend).

This project aids in obtaining a road-damage detection model for assessing potholes study.

Here you will find how to speciallize YOLOv5 and YOLOv7 object detection algorithms in road damage.


## Pre-requisites

This application looks for the models in generated directly in the [Backend repository](https://github.com/allanes/pothole-detector-backend).

## Installation

1. Open the terminal in the desired directory and clone this project:
   ```
   git clone https://github.com/allanes/pothole-detector-gui.git
   ```

2. Create a new Python environment. Below are the instructions to create one
using *venv* on Windows:
    ```   
    cd pothole-detector-gui
    python -m venv .venv
    .venv\Scripts\activate
    python -m pip install -U pip
    ``` 

3. To install requirements, copy the following commands to the activated 
environment:
    ```
    pip install -r requirements.txt    
    ```

4. Crear un archivo con nombre `.env` en la raíz del proyecto con las variables `usuario` y `password`, y darles un valor

5. Configurar rutas en archivo ``rutas_cfg.env``. Crear el directorio asignado en la variable `RUTA_SALIDAS` si no existe.

## Use
On Windows, run `iniciar_gui.bat` to open the GUI. Alternatively, you can run `main.py` from within the activated environment:
    ```
    .venv\Scripts\activate
    python main.py
    ```

Default user: `User`
Default password: `1234`

1. Provide an input image, video or directory to process
2. Select an algorithm and its exposed parameters
3. Click `Run`
4. After processing is done, the output will be displayed to the right
5. An email will be prefilled with a summary and the details of the inference. You can edit it there or after pressing the `Send`  button, which will open it in your default email manager.
