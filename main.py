from dataclasses import dataclass
import os
from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from PIL import ImageTk, Image
from pyparsing import col
from tkVideoPlayer import TkinterVideo
import yaml
import predict
from dotenv import load_dotenv


load_dotenv('rutas_cfg')
RUTA_SALIDAS = os.getenv('RUTA_SALIDAS')
VENTANA_TITULO = 'Mantenimiento Vial con I.A.'
VENTANA_ANCHO = 1100
VENTANA_ALTO = 600


@dataclass
class ParamsDeteccion():
    confianza: float
    iou: float


class GUI():
    def __init__(self):
        # Setup main app window
        self.root = Tk()
        self.root.title(VENTANA_TITULO)
        self.root.geometry(f'{VENTANA_ANCHO}x{VENTANA_ALTO}')
        
        # Creates Main Content Frame
        self.input_params_frame = ttk.Frame(self.root).grid(column=0, row=0, sticky=(N, W, E, S))
        
        # Declarar variables sincronizadas
        self.crear_variables_deteccion()
        
        self.tab_configuracion = self.crear_frame_principal_entrada(parent_frame=self.input_params_frame)
        self.tab_configuracion.grid(column=0, row=0, sticky=(N,S,E,W), columnspan=2)
        
        
    def start(self):
        # Make it start the Event Loop
        self.root.mainloop()
        
    def crear_variables_deteccion(self):
        self.ruta_entrada = StringVar()
        self.ruta_salida = StringVar(value=RUTA_SALIDAS)
        self.nombre_modelo = StringVar()
        self.confianza_var = DoubleVar()
        self.iou_var = DoubleVar()

    
    def preparar_llamada_y_llamar(self):
        print('Preparando llamada')
        ruta_archivo_generado = predict.run(self.ruta_entrada.get())
        ruta_archivo_generado = os.path.abspath(ruta_archivo_generado)
        print('Salida generada: ' + ruta_archivo_generado)
        
        if ruta_archivo_generado.split('.')[-1] == 'mp4':
            self.videoplayer.load(ruta_archivo_generado)
            self.videoplayer.pack(expand=True, fill="both")

            self.videoplayer.play() # play the video
        else:            
            image = Image.open(ruta_archivo_generado)
            image = ImageTk.PhotoImage(image)
            
            self.output_label.configure(image=image)
            self.output_label.image=image
            # image = PhotoImage(file=ruta_archivo_generado)
            # ttk.Label(self.tab_configuracion, image=image).grid(column=0, row=6, sticky=(W,E,N,S))
    
    
    def crear_frame_principal_entrada(self, parent_frame):
        frame_config_parametros = ttk.Frame(parent_frame)
        
        styling_grid = {}
        
        self.crear_panel_pedido_ruta(frame_config_parametros).grid(column=0, row=0, columnspan=3, **styling_grid)
        self.crear_panel_modelo(frame_config_parametros).grid(column=0, row=1, **styling_grid)
        self.crear_panel_deteccion_cfg(frame_config_parametros).grid(column=0, row=2, **styling_grid)
        self.crear_panel_etiquetas(frame_config_parametros).grid(column=1, row=1, rowspan=2, **styling_grid)
        self.crear_panel_parametros_entrenamiento(frame_config_parametros).grid(column=2, row=1, rowspan=2, **styling_grid)
        
        for frame in frame_config_parametros.winfo_children():
            frame['borderwidth'] = 2,
            frame['relief'] = 'raised',
            frame['padding'] = (10,5)
        
        ttk.Button(frame_config_parametros,text='Inferir', width=20, command=self.preparar_llamada_y_llamar).grid(column=0, row=3)
        
        return frame_config_parametros
    
    def crear_panel_pedido_ruta(self, parent_frame) -> ttk.Frame:
        ANCHO_CAMPO_TEXTO = 80
        var_tipo_entrada_elegida = StringVar()
        
        frame = ttk.Frame(parent_frame)
        
        ttk.Label(frame, text='Elegir entrada').grid(column=0, row=0)
        # Control para entrada de carpeta
        ttk.Radiobutton(frame, text='Carpeta', variable=var_tipo_entrada_elegida, value='Carpeta').grid(column=0, row=1)
        ttk.Entry(frame, width=ANCHO_CAMPO_TEXTO).grid(column=1, row=1)
        ttk.Button(frame,text='Seleccionar').grid(column=2, row=1)
       
        # Control para entrada de archivo
        ttk.Radiobutton(frame, text='Archivo', variable=var_tipo_entrada_elegida, value='Archivo').grid(column=0, row=2)
        ttk.Entry(frame, width=ANCHO_CAMPO_TEXTO).grid(column=1, row=2)
        ttk.Button(frame,text='Seleccionar').grid(column=2, row=2)
        
        return frame
    
    def crear_panel_modelo(self, parent_frame) -> ttk.Frame:
        frame = ttk.Frame(parent_frame)
        metadatos_modelos = predict.recuperar_metadatos_modelos()
        lista_modelos = [metadatos.nombre for metadatos in metadatos_modelos]
        self.var_modelo_elegido = StringVar()
        self.var_modelo_elegido.set(lista_modelos[0])
        
        ttk.Label(frame, text='Modelo').grid(column=0, row=0)
        ttk.Combobox(frame, values=lista_modelos, textvariable=self.var_modelo_elegido).grid(column=0, row=1)
        
        return frame
    
    def crear_panel_deteccion_cfg(self, parent_frame) -> ttk.Frame:
        var_iou_elegido = DoubleVar(value=0.25)
        var_confianza_elegida = DoubleVar(value=0.20)
        frame = ttk.Frame(parent_frame)
        
        ttk.Label(frame, text='Parametros de inferencia').grid(column=0, row=0)
        ttk.Label(frame, text='IOU').grid(column=0, row=1)
        ttk.Entry(frame, textvariable=var_iou_elegido, width=10).grid(column=1, row=1)
        ttk.Label(frame, text='Confianza').grid(column=0, row=2)
        ttk.Entry(frame, textvariable=var_confianza_elegida, width=10).grid(column=1, row=2)
        
        return frame
    
    def crear_panel_etiquetas(self, parent_frame) -> ttk.Frame:
        metadatos_modelos = predict.recuperar_metadatos_modelos()
        ruta_base = os.getenv('RUTA_BASE_YOLOS')
        ruta_dataset_data = ruta_base + '/' + predict.DatasetRutas[metadatos_modelos[0].dataset_ver.name].value
        file = open(ruta_dataset_data, 'r')
        ds_data = yaml.load(file, Loader=yaml.SafeLoader)
        lista_etiquetas = ds_data['names']
        var_etiqueta_elegida = StringVar()
        var_modo_etiqueta_elegida = StringVar()
        
        frame = ttk.Frame(parent_frame)
        
        ttk.Label(frame, text='Etiquetas').grid(column=0, row=0)
        ttk.Radiobutton(frame, text='Incluir', variable=var_modo_etiqueta_elegida, value='Incluir').grid(column=0, row=1)
        ttk.Radiobutton(frame, text='Excluir', variable=var_modo_etiqueta_elegida, value='Excluir').grid(column=1, row=1)
        
        etiqueta = lista_etiquetas[0]
        for idx, etiqueta in enumerate(lista_etiquetas):
            ttk.Checkbutton(frame, text=etiqueta, variable=var_etiqueta_elegida).grid(column=0, row=2+idx, sticky=(E,W))
        
        return frame
    
    def crear_panel_parametros_entrenamiento(self, parent_frame) -> ttk.Frame:
        ruta_base = os.getenv('RUTA_BASE_MODELOS')
        ruta_opts = ruta_base + '/' + self.var_modelo_elegido.get() + '/opt.yaml'
        file = open(ruta_opts, 'r')
        training_params:dict = yaml.load(file, Loader=yaml.SafeLoader)
        training_params = yaml.dump(training_params, line_break='\n')
        frame = ttk.Frame(parent_frame)
        
        ttk.Label(frame, text='Parametros de entrenamiento').grid(column=0, row=0)
        widget_params_entrenamiento = Text(frame, width=40)
        widget_params_entrenamiento.grid(column=0, row=1)
        
        widget_params_entrenamiento.insert('0.0', training_params)        
        
        return frame
                
        
if __name__ == '__main__':
    gui = GUI()
    gui.start()