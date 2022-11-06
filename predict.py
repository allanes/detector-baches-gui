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
    lista_metadatos = get_metadatos_modelos()
    
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
def get_metadatos_modelos() -> list[ModelMetadata]:
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

def get_metadata_by_name(nombre:str) -> ModelMetadata:
    lista_modelos = get_metadatos_modelos()
    for modelo in lista_modelos:
        if modelo.nombre == nombre:
            return modelo
    
    print('No se encontro el modelo')
    
def run(ruta_entrada:str, nombre_modelo:str, confianza:float = 0.2, iou:float = 0.25, lista_clases: list[str] = None):
    RUTA_BASE_YOLOS = os.getenv('RUTA_BASE_YOLOS')
    
    modelo = get_metadata_by_name(nombre_modelo)
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


def preparar_cuerpo_mail(ruta_base_label:str, confianza:float = 0.2, iou:float = 0.25, lista_clases: list[str] = None) -> str:
    print(f'lista_clases recibida: {lista_clases}')
    if not 'labels' in os.listdir(ruta_base_label):
        print(f'No se encontro la carpeta labels dentro de la carpeta {ruta_base_label}')

    # Armo la lista de archivos para ubicar los nombres de las etiquetas
    lista_archivos = os.listdir(ruta_base_label)
    lista_archivos.remove('labels')
    lista_archivos = [os.path.splitext(archivo)[0] for archivo in lista_archivos]

    # Armo una lista de etiquetas para cada archivo de referencia
    ruta_labels = ruta_base_label + '/labels'
    lista_labels = os.listdir(ruta_labels)

    etiquetas_por_archivo = []
    for archivo_ref in lista_archivos:
        sublista = []
        for label in lista_labels:
            if label.startswith(archivo_ref):
                sublista.append(label)
        etiquetas_por_archivo.append(sublista)
        
    assert len(etiquetas_por_archivo) == len(lista_archivos)

    # Busco el label con la mayor cantidad de lineas para cada archivo de ref
    lista_labels_seleccionados = []
    for archivo, lista_labels in zip(lista_archivos, etiquetas_por_archivo):
        cuenta_lineas = 0
        buffer_label = ''
        
        for label in lista_labels:
            file = open(f'{ruta_labels}/{label}', 'r')
            cant_lineas = len(file.readlines())
            if cant_lineas > cuenta_lineas: 
                cuenta_lineas = cant_lineas
                buffer_label = label
        
        lista_labels_seleccionados.append(buffer_label)
        
    assert len(etiquetas_por_archivo) == len(lista_archivos)
    
    # Preparo datos para el cuerpo
    timestamp = ruta_base_label.split("_")[-2:]
    timestamp = ' '.join(timestamp)
    nombre_modelo = '_'.join(ruta_base_label.split("_")[0:-2])
    nombre_modelo = os.path.split(nombre_modelo)[1]
    modelo = get_metadata_by_name(nombre_modelo)
    lista_etiquetas = get_lista_etiquetas(nombre_modelo)
    mapa_etiquetas = {str(idx): valor for idx, valor in enumerate(lista_etiquetas)}

    # Armo cuerpo
    cadena = '\n*******RESULTADOS DE LA DETECCION*******\n\n'
    cadena += f'Timestamp: {timestamp}\n'
    cadena += f'Ruta de referencia: {ruta_base_label}\n'
    cadena += f'Cantidad de archivos de entrada: {len(lista_archivos)}\n'
    cadena += f'Cantidad de archivos con detecciones: {len([label not in [""] for label in lista_labels_seleccionados])}\n'
    
    cadena += f'\nParámetros de la detección\n'
    cadena += f'  . Umbral de confianza: {confianza}\n'
    cadena += f'  . Umbral de IOU: {iou}\n'
    cadena += f'  . Etiquetas de detección: {[mapa_etiquetas[clase] for clase in lista_clases]}\n'
    
    cadena += f'\nDatos del modelo usado\n'
    cadena += f'  . Nombre del modelo base: {modelo.yolo_ver}\n'
    cadena += f'  . Nombre del modelo entrenado: {modelo.nombre}\n'
    cadena += f'  . Version del dataset: {modelo.dataset_ver}\n'
    cadena += f'  . Etiquetas de entrenamiento: {lista_etiquetas}\n'

    cadena += '\n'
    for archivo, label in zip(lista_archivos, lista_labels_seleccionados):
        if label == '': continue
        file = open(f'{ruta_labels}/{label}')
        lineas = file.readlines()
        lineas = [f'{mapa_etiquetas[linea[0]]} {linea}' for linea in lineas]
        cadena_detalles = '\t'.join(lineas)
        
        cadena += f'- Archivo de entrada "{archivo}"\n'
        cadena += f'  . Cantidad de detecciones: {len(lineas)}\n'
        cadena += f'  . Label de referencia: {label}\n'
        cadena += f'  . Detalle de detecciones\n\t'
        
        cadena += cadena_detalles + '\n\n'
    
    return cadena

    
if __name__ == '__main__':
    
    pass
    