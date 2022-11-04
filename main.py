from dataclasses import dataclass
import os
from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from PIL import ImageTk, Image
from tkVideoPlayer import TkinterVideo
import predict
from dotenv import load_dotenv


load_dotenv('rutas_cfg')
RUTA_SALIDAS = os.getenv('RUTA_SALIDAS')
VENTANA_TITULO = 'Mantenimiento Vial con I.A.'
VENTANA_ANCHO = 750
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
        self.mainframe = ttk.Frame(self.root).grid(column=0, row=0, sticky=(N, W, E, S))
        
        # Create Tab Control
        self.tab_control = ttk.Notebook(self.mainframe)
        self.tab_control.grid(column=1, row=3, sticky=(N,W,E,S))
        
        # Declarar variables sincronizadas
        self.crear_variables_deteccion()
        
        # Crear pestañas
        # self.set_defaults()
        self.tab_configuracion = self.agregar_frame_config_params(parent_frame=self.tab_control, idx_pestaña=0)
        
        # Registrar pestañas        
        self.tab_control.add(self.tab_configuracion, text='Configuracion')
        
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
    
    def crear_panel_pedido_ruta(self, parent_frame, col, row, texto, variable, texto_boton = 'Seleccionar'):
            
        frame_entrada = ttk.LabelFrame(parent_frame)
        frame_entrada.grid(column=col, row=row, sticky=(N,S,W,E), columnspan=3)        
        # Declare and place labels        
        ttk.Label(frame_entrada, text=texto).grid(column=0, row=2)        
        # Declare and place entries
        ttk.Entry(frame_entrada, textvariable=variable, width=100).grid(column=2, row=2)        
        #Declare and place buttons
        ttk.Button(frame_entrada,text=texto_boton, command=lambda: variable.set(filedialog.askopenfilename())).grid(column=3, row=2)
        
        
    def agregar_frame_config_params(self, parent_frame, idx_pestaña):
        # Declaro Frame de Geometria
        frame_config_parametros = ttk.Frame(parent_frame)
        frame_config_parametros.grid(column=idx_pestaña, row=0, sticky=(N,S,E,W), columnspan=2)
        
        self.crear_panel_pedido_ruta(frame_config_parametros, col=0, row=0, texto='Entrada', variable=self.ruta_entrada)
        self.crear_panel_pedido_ruta(frame_config_parametros, col=0, row=1, texto='Salida', variable=self.ruta_salida)
        
        # Creo panel de config de parametros de inferencia
        frame_parametros_inferencia = ttk.Frame(frame_config_parametros).grid(column=0, row=3)
        # Declare and place labels
        ttk.Label(frame_config_parametros, text="Confianza").grid(column=0, row=3, columnspan=1)
        ttk.Label(frame_config_parametros, text="IOU").grid(column=0, row=4, columnspan=1)
        # Declare entries
        confianza_entry = ttk.Entry(frame_config_parametros, width=5, textvariable=self.confianza_var)
        iou_entry = ttk.Entry(frame_config_parametros, width=5, textvariable=self.iou_var)
        # Place entries
        confianza_entry.grid(column=1, row=3)
        iou_entry.grid(column=1, row=4)
        
        # Output label
        self.output_label = ttk.Label(frame_config_parametros)
        self.output_label.grid(column=0, row=6, sticky=(W,E,N,S))
        self.videoplayer = TkinterVideo(master=self.root, scaled=False)
        
        # Seccion detectar
        ttk.Button(frame_config_parametros,text='Inferir', command=self.preparar_llamada_y_llamar).grid(column=0, row=5)
                
        return frame_config_parametros
        
        
if __name__ == '__main__':
    gui = GUI()