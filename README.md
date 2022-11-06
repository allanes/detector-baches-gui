## Instalacion

1. Con la terminal en la ubicación deseada, clonar este repo y su dependencia:
   ```
   git clone https://github.com/allanes/detector-baches-gui.git
   ```

2. Crear un nuevo ambiente. Se muestran las instrucciones para crear uno usando la herramienta venv:
    Para Windows:
    ```   
    cd detector-baches-gui
    python -m venv .venv
    .venv\Scripts\activate
    python -m pip install -U pip
    ``` 

3. Para instalar las dependencias de este proyecto, desde el ambiente ejecutar:
    ```
    pip install -r requirements.txt    
    ```

4. Crear un archivo `.env` con las variables `usuario` y `password`, y darles un valor

5. Configurar rutas en archivo ``rutas_cfg.env``