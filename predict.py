from functools import lru_cache
import os
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from dotenv import load_dotenv
import yaml
from yaml.loader import SafeLoader

load_dotenv('rutas_cfg.env')

class YoloRutas(str, Enum):
    V5 = 'yolov5'
    V7 = 'yolov7'

class YoloVersiones(str, Enum):
    V5 = 'yolov5'
    V7 = 'yolov7'
    
class DatasetRutas(str, Enum):
    V1 = 'custom_cfg/data_v1.yaml'
    V4 = 'custom_cfg/data_v4.yaml'
    
class DatasetVersiones(str, Enum):
    V1 = 'v1'
    V4 = 'v4'

@dataclass
class ModelMetadata():
    nombre: str
    ruta_pesos: str
    yolo_ver: YoloVersiones
    dataset_ver: DatasetVersiones
    image_size: int


def get_lista_etiquetas(nombre_modelo:str)->list[str]:
    lista_metadatos = recuperar_metadatos_modelos()
    
    modelo = None    
    for modelo in lista_metadatos:
        if modelo.nombre == nombre_modelo: break
    
    if not modelo:
        print(f'Modelo {nombre_modelo} no encontrado')
        return []
    
    ruta_base = os.getenv('RUTA_BASE_YOLOS')
    ruta_dataset_data = ruta_base + '/' + DatasetRutas[modelo.dataset_ver.name].value
    file = open(ruta_dataset_data, 'r')
    ds_data = yaml.load(file, Loader=yaml.SafeLoader)
    lista_etiquetas = ds_data['names']
    
    return lista_etiquetas

def get_training_params(nombre_modelo:str) -> str:
    ruta_base = os.getenv('RUTA_BASE_MODELOS')
    ruta_opts = ruta_base + '/' + nombre_modelo + '/opt.yaml'
    file = open(ruta_opts, 'r')
    training_params:dict = yaml.load(file, Loader=yaml.SafeLoader)
    training_params = yaml.dump(training_params, line_break='\n')
    
    return training_params

@lru_cache(None)
def recuperar_metadatos_modelos() -> list[ModelMetadata]:
    ruta_base = os.getenv('RUTA_BASE_MODELOS')
    lista_modelos = []
    for carpeta in os.listdir(ruta_base):
        file = open(f'{ruta_base}/{carpeta}/opt.yaml', 'r')
        opciones_usadas = yaml.load(file, Loader=SafeLoader)
        
        yolo_ver = opciones_usadas['data'].split('/')[0]
        yolo_ver = YoloVersiones(yolo_ver)
        
        dataset_ver = opciones_usadas['data'].split('/')[1][-1]
        dataset_ver = DatasetVersiones('v' + dataset_ver)
        
        image_size = 416
        if yolo_ver == YoloVersiones.V5:
            clave_yolov5 = 'imgsz'
            image_size = opciones_usadas[clave_yolov5]
        elif yolo_ver == YoloVersiones.V7:
            clave_yolov7 = 'img_size'
            image_size = opciones_usadas[clave_yolov7][0]
            
        
        lista_modelos.append(
            ModelMetadata(
                nombre=carpeta,
                ruta_pesos=f'{ruta_base}/{carpeta}/weights/best.pt',
                yolo_ver=yolo_ver,
                dataset_ver=dataset_ver,
                image_size=image_size
            )
        )
        
    print(f'Se encontraron {len(lista_modelos)} modelos:')
    [print(f'    Modelo {idx}: {modelo.nombre}') for idx, modelo in enumerate(lista_modelos)]
    
    return lista_modelos

def getMetadataByName(nombre:str) -> ModelMetadata:
    lista_modelos = recuperar_metadatos_modelos()
    for modelo in lista_modelos:
        if modelo.nombre == nombre:
            return modelo
    
    print('No se encontro el modelo')
    
def run(ruta_entrada:str, nombre_modelo:str, confianza:float = 0.2, iou:float = 0.25, lista_clases: list[str] = None):
    RUTA_BASE_YOLOS = os.getenv('RUTA_BASE_YOLOS')
    
    modelo = getMetadataByName(nombre_modelo)
    print(f'\nUsando modelo {modelo.nombre}\n')
    
    # Armo rutas antes de la llamada
    ruta_archivo_detect = f'{RUTA_BASE_YOLOS}/{YoloRutas[modelo.yolo_ver.name].value}/detect.py'
    ruta_dataset_data = DatasetRutas[modelo.dataset_ver.name].value
    carpeta_salida_base = os.getenv('RUTA_SALIDAS')
    carpeta_salida_nueva = f'{modelo.nombre}_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    
    # Llamada
    cadena = \
        f'python {ruta_archivo_detect} ' +\
        f'--weights {modelo.ruta_pesos} ' +\
        f'--img-size {modelo.image_size} ' +\
        f'--conf-thres {confianza} ' +\
        f'--source "{ruta_entrada}" ' +\
        f'--iou-thres {iou} ' +\
        f'--name {carpeta_salida_nueva} ' +\
        f'--project {carpeta_salida_base} ' +\
        f'--save-txt ' +\
        f'--save-conf'
    
    if lista_clases: cadena = f'{cadena} '+\
        f'--classes {" ".join(lista_clases)}'
    
    if modelo.yolo_ver == YoloVersiones.V5:
        cadena = cadena + f' --data {ruta_dataset_data}'
    
    print('Llamada:\n' + cadena + '\n')
    os.system(cadena)
    
    ruta_salida = carpeta_salida_base + '/' + carpeta_salida_nueva
    print(f'predict_ruta_salida: {ruta_salida}')
    
    if not len(os.listdir(ruta_salida)): return None    
    return ruta_salida

    
if __name__ == '__main__':
    pass
    