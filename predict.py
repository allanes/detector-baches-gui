import os
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from dotenv import load_dotenv
import yaml
from yaml.loader import SafeLoader

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
    

def recuperar_metadatos_modelos(ruta_base:str) -> list[ModelMetadata]:
    
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


def run(ruta_archivo_entrada:str, confianza:float = 0.2, iou:float = 0.25):
    load_dotenv('rutas_cfg.env')
    RUTA_BASE_MODELOS = os.getenv('RUTA_BASE_MODELOS')
    RUTA_BASE_YOLOS = os.getenv('RUTA_BASE_YOLOS')
    modelos = recuperar_metadatos_modelos(ruta_base = RUTA_BASE_MODELOS)
    modelo = modelos[0]
    print(f'\nUsando modelo {modelo.nombre}\n')
    
    # Armo rutas antes de la llamada
    ruta_archivo_detect = f'{RUTA_BASE_YOLOS}/{YoloRutas[modelo.yolo_ver.name].value}/detect.py'
    ruta_dataset_data = DatasetRutas[modelo.dataset_ver.name].value
    carpeta_salida_base = './static/output'
    carpeta_salida_nueva = f'{modelo.nombre}_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    
    # Llamada
    cadena = \
        f'python {ruta_archivo_detect} ' +\
        f'--weights {modelo.ruta_pesos} ' +\
        f'--img-size {modelo.image_size} ' +\
        f'--conf-thres {confianza} ' +\
        f'--source {ruta_archivo_entrada} ' +\
        f'--iou-thres {iou} ' +\
        f'--name {carpeta_salida_nueva} ' +\
        f'--project {carpeta_salida_base} ' +\
        f'--save-txt ' +\
        f'--save-conf'
    
    if modelo.yolo_ver == YoloVersiones.V5:
        cadena = cadena + f' --data {ruta_dataset_data}'
    
    print('Llamada:\n' + cadena + '\n')
    os.system(cadena)
    
    nombre_archivo_entrada = os.path.split(ruta_archivo_entrada)[1]
    nombre_archivo_salida:str = nombre_archivo_entrada
    
    mapa_extensiones = {
        '.MOV': '.mp4',
        '.mov': '.mp4',
        '.mkv': '.mp4',
    }
    extension = os.path.splitext(nombre_archivo_salida)[1]
    
    if extension in mapa_extensiones.keys():
        nombre_archivo_salida = os.path.splitext(nombre_archivo_salida)[0] + mapa_extensiones[extension]
    
    ruta_archivo_salida = carpeta_salida_base + '/' + carpeta_salida_nueva + '/' + nombre_archivo_salida
    
    return ruta_archivo_salida
    
if __name__ == '__main__':
    pass
    