from dataclasses import dataclass
import os
from tkinter import *
from tkinter import ttk
from tkinter import filedialog
import cv2
import webbrowser
from urllib.parse import quote
from PIL import ImageTk, Image
from pyparsing import col

from predict import get_metadatos_modelos as get_metadatos_modelos
import predict
from dotenv import load_dotenv


load_dotenv('rutas_cfg')
RUTA_SALIDAS = os.getenv('RUTA_SALIDAS')
VENTANA_TITULO = 'Mantenimiento Vial con I.A.'
VENTANA_ANCHO = 1800
VENTANA_ALTO = 900


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
        
        # Declarar variables sincronizadas
        self.crear_variables_sincronizadas()
        
        # Creates Panel Principal
        self.main_frame = ttk.Frame(self.root)
        # self.main_frame.grid(column=0, row=0, sticky=(N, W, E, S)) #Implementado en iniciar_sesion()
        
        # Crear Login
        self.panel_login = self.crear_frame_login(parent_frame=self.root)
        self.panel_login.grid(column=0, row=0, sticky=(N, W, E, S))
        
        # Paneles principales: Entrada y salida
        self.panel_entradas = self.crear_frame_principal_entradas(parent_frame=self.main_frame)
        self.panel_entradas.grid(column=0, row=0, sticky=(N,S,E,W), columnspan=3)
        self.panel_salida = self.crear_frame_salida_videos(parent_frame=self.main_frame)
        self.panel_salida.grid(column=3, row=0, sticky=(N,S,E,W), columnspan=3)
        self.panel_email = self.crear_panel_cuerpo_mail(parent_frame=self.main_frame)
        self.panel_email.grid(column=0, row=1, sticky=(N,S,E,W), columnspan=3, rowspan=2)        
        
        
    def start(self):
        # Make it start the Event Loop
        self.root.mainloop()
        
    def crear_frame_login(self, parent_frame:str) -> ttk.Frame:
        frame = ttk.Frame(parent_frame)
        
        ttk.Label(frame, text='Inicio de sesión').grid(column=0, row=0)
        
        # ruta_logo = os.path.abspath('logo.jpeg')
        ruta_logo = 'logo.png'
        print(f'ruta logo: {ruta_logo}')
        
        # image = cv2.imread(ruta_logo)
        # # image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        # image = cv2.resize(image, (300,300))
        # image = Image.fromarray(image)
        # image = ImageTk.PhotoImage(image=image)
        log_image = PhotoImage(file=ruta_logo)
        
        self.label_logo = ttk.Label(frame, image=log_image)
        self.label_logo.grid(column=0, row=1)
        self.label_logo.configure(image=log_image)
        self.label_logo['image'] = log_image
        
        ttk.Label(frame, text='Usuario:').grid(column=0,row=2)
        ttk.Entry(frame, textvariable=self.var_usuario).grid(column=1, row=2)
        ttk.Label(frame, text='Contraseña:').grid(column=0,row=3)
        ttk.Entry(frame, textvariable=self.var_password, show='*').grid(column=1, row=3)
        self.boton_iniciar_sesion = ttk.Button(frame, text='Inciar sesion', command=self.iniciar_sesion)
        self.boton_iniciar_sesion.grid(column=0, row=4, columnspan=2, sticky=E)
        ttk.Label(frame, textvariable=self.var_msje_login).grid(column=0, row=5, columnspan=2, sticky=E)
        
        return frame
    
    def iniciar_sesion(self):
        load_dotenv('.env')
        usuario_valido = os.getenv('usuario')
        contra_valida = os.getenv('password')
        
        if self.var_usuario.get() == usuario_valido and self.var_password.get() == contra_valida:
            # self.mostrar_ventana_principal()
            self.var_msje_login.set('Iniciando sesion')
            self.panel_login.destroy()
            self.main_frame.grid(column=0, row=0, sticky=(N, W, E, S))
        else:
            if self.contador_intentos == self.cantidad_intentos_max - 1:
                self.boton_iniciar_sesion.state(['disabled'])
                return
            self.contador_intentos += 1
            intentos_restantes = self.cantidad_intentos_max - self.contador_intentos
            self.var_msje_login.set(f'Datos no válidos. Intentos restantes: {intentos_restantes}')
            
            pass
        
    def crear_variables_sincronizadas(self):
        # Generales
        ultima_salida = 'salida_ejemplo/yolov7_2_20221106_153035'
        self.capture = None
        self.modo_imagen = True
        
        # Panel Login
        self.var_usuario = StringVar(value='User')
        self.var_password = StringVar(value='1234')
        self.var_msje_login = StringVar(value='')
        self.boton_iniciar_sesion = None
        self.contador_intentos = 0
        self.cantidad_intentos_max = 3        
        
        # Panel de pedido de ruta de entrada
        self.var_tipo_entrada_elegida = StringVar(value='Archivo')
        self.ruta_entrada = StringVar()
        
        # Panel de modelo
        self.var_modelo_elegido = StringVar()
        
        # Panel etiquetas
        self.lista_vars_checkbuttons = []
        self.var_etiqueta_elegida = BooleanVar()
        self.var_modo_etiqueta_elegida = StringVar(value='Incluir')
        
        # Panel de parametros de inferencia
        self.var_confianza_elegida = DoubleVar(value=0.25)
        self.var_iou_elegido = DoubleVar(value=0.45)
        
        # Panel de detecciones
        self.ruta_salida = StringVar(value=ultima_salida)
        self.archivo_a_mostrar = StringVar()
        
        # Panel Mail
        self.var_emails_destino = StringVar(value='ados.adrian@gmail.com,')
        self.var_asunto = StringVar(value='Resultados de detecciones')
        self.var_mail_enviado = StringVar(value='')
        
    def funcion_panel_pedido_ruta(self):
        if self.var_tipo_entrada_elegida.get() == 'Carpeta':
            self.entry_archivo.state(['disabled'])
            self.btn_archivo.state(['disabled'])
            self.entry_carpeta.state(['!disabled'])
            self.btn_carpeta.state(['!disabled'])
            return    
        
        if self.var_tipo_entrada_elegida.get() == 'Archivo':
            self.entry_carpeta.state(['disabled'])
            self.btn_carpeta.state(['disabled'])
            self.entry_archivo.state(['!disabled'])
            self.btn_archivo.state(['!disabled'])
            return    
        
    
    def preparar_llamada_y_llamar(self):
        print('Preparando llamada')
        lista_clases_tildadas = []
        lista_clases_destildadas = []
        for var_chkbtn in self.lista_vars_checkbuttons:
            if var_chkbtn.get().startswith('-'):
                lista_clases_destildadas.append(var_chkbtn.get()[1:])
            else:
                lista_clases_tildadas.append(var_chkbtn.get())
        
        
        modo = self.var_modo_etiqueta_elegida.get()
        lista_clases_deseadas = lista_clases_tildadas if modo=='Incluir' else lista_clases_destildadas
        
        ruta_salida = predict.run(
            self.ruta_entrada.get(),
            nombre_modelo=self.var_modelo_elegido.get(),
            confianza=self.var_confianza_elegida.get(),
            iou=self.var_iou_elegido.get(),
            lista_clases=lista_clases_deseadas
        )
        
        cuerpo_mail = predict.preparar_cuerpo_mail(
            ruta_base_label=ruta_salida,
            confianza=self.var_confianza_elegida.get(),
            iou=self.var_iou_elegido.get(),
            lista_clases=lista_clases_deseadas
        )
        # self.cuerpo_mail = cuerpo_mail
        self.widget_cuerpo_mail.insert('0.0', cuerpo_mail)
        
        self.ruta_salida.set(os.path.abspath(ruta_salida))
        print('Salida generada en: ' + self.ruta_salida.get())
        self.archivo_a_mostrar.set('')
        
        self.configurar_widget_multimedia()
            
   
    def crear_frame_principal_entradas(self, parent_frame):
        frame_config_parametros = ttk.Frame(parent_frame, borderwidth=2, relief='raised',padding=(10,5))
        
        styling_grid = {}
        
        self.crear_panel_pedido_ruta(frame_config_parametros).grid(column=0, row=0, columnspan=3, **styling_grid)
        self.crear_panel_modelo(frame_config_parametros).grid(column=0, row=1, **styling_grid)
        self.crear_panel_parametros_deteccion(frame_config_parametros).grid(column=0, row=2, **styling_grid)
        self.crear_panel_etiquetas(frame_config_parametros).grid(column=1, row=1, rowspan=2, **styling_grid)
        self.crear_panel_parametros_entrenamiento(frame_config_parametros).grid(column=2, row=1, rowspan=4, **styling_grid)
        
        for frame in frame_config_parametros.winfo_children():
            frame['borderwidth'] = 2,
            frame['relief'] = 'raised',
            frame['padding'] = (10,5)
        
        ttk.Button(frame_config_parametros,text='RUN', command=self.preparar_llamada_y_llamar).grid(column=0, row=3, rowspan=2, sticky=(W,E))
        
        return frame_config_parametros
    
    def crear_panel_pedido_ruta(self, parent_frame) -> ttk.Frame:
        ANCHO_CAMPO_TEXTO = 80
        
        frame = ttk.Frame(parent_frame)
        
        ttk.Label(frame, text='Elegir entrada').grid(column=0, row=0)
        # Control para entrada de carpeta
        ttk.Radiobutton(frame, text='Carpeta', variable=self.var_tipo_entrada_elegida, value='Carpeta',command=self.funcion_panel_pedido_ruta).grid(column=0, row=1)
        self.entry_carpeta = ttk.Entry(frame, width=ANCHO_CAMPO_TEXTO, textvariable=self.ruta_entrada)
        self.entry_carpeta.grid(column=1, row=1)
        self.btn_carpeta = ttk.Button(frame,text='Seleccionar', command=lambda: self.ruta_entrada.set(filedialog.askdirectory()))
        self.btn_carpeta.grid(column=2, row=1)
       
        # Control para entrada de archivo
        ttk.Radiobutton(frame, text='Archivo', variable=self.var_tipo_entrada_elegida, value='Archivo',command=self.funcion_panel_pedido_ruta).grid(column=0, row=2)
        self.entry_archivo = ttk.Entry(frame, width=ANCHO_CAMPO_TEXTO, textvariable=self.ruta_entrada)
        self.entry_archivo.grid(column=1, row=2)
        self.btn_archivo = ttk.Button(frame,text='Seleccionar', command=lambda: self.ruta_entrada.set(filedialog.askopenfilename()))
        self.btn_archivo.grid(column=2, row=2)
        
        self.funcion_panel_pedido_ruta()
        return frame
    
    
    def crear_panel_modelo(self, parent_frame) -> ttk.Frame:
        frame = ttk.Frame(parent_frame)
        lista_nombres_modelos = [metadatos.nombre for metadatos in get_metadatos_modelos()]
        
        self.var_modelo_elegido.set(lista_nombres_modelos[0])
        
        ttk.Label(frame, text='Modelo').grid(column=0, row=0)
        combo = ttk.Combobox(frame, values=lista_nombres_modelos, textvariable=self.var_modelo_elegido, state='readonly')
        combo.grid(column=0, row=1)
        combo.bind('<<ComboboxSelected>>', self.actualizar_dependencias_modelo)
        
        return frame
    
    def crear_panel_parametros_deteccion(self, parent_frame) -> ttk.Frame:
        frame = ttk.Frame(parent_frame)
        
        ttk.Label(frame, text='Parametros de inferencia').grid(column=0, row=0)
        ttk.Label(frame, text='IOU').grid(column=0, row=1)
        ttk.Entry(frame, textvariable=self.var_iou_elegido, width=10).grid(column=1, row=1)
        ttk.Label(frame, text='Confianza').grid(column=0, row=2)
        ttk.Entry(frame, textvariable=self.var_confianza_elegida, width=10).grid(column=1, row=2)
        
        return frame
    
    def crear_panel_etiquetas(self, parent_frame) -> ttk.Frame:
        modelo_elegido = self.var_modelo_elegido.get()
        lista_etiquetas = predict.get_lista_etiquetas(nombre_modelo = modelo_elegido)
        
        frame = ttk.Frame(parent_frame)
        
        ttk.Label(frame, text='Etiquetas').grid(column=0, row=0)
        ttk.Radiobutton(frame, text='Incluir', variable=self.var_modo_etiqueta_elegida, value='Incluir').grid(column=0, row=1)
        ttk.Radiobutton(frame, text='Excluir', variable=self.var_modo_etiqueta_elegida, value='Excluir').grid(column=1, row=1)
        
        lista_vars_checkbuttons = [StringVar(value=f'{idx}') for idx in range(len(lista_etiquetas))]
        for idx in range(10):
            if idx < len(lista_etiquetas):
                ttk.Checkbutton(frame, text=lista_etiquetas[idx], variable=lista_vars_checkbuttons[idx], onvalue=f'{idx}', offvalue=f'-{idx}').grid(column=0, row=2+idx, sticky=(E,W))
            else:
                ttk.Checkbutton(frame, text='Sin definir', variable=self.var_etiqueta_elegida, state='disabled').grid(column=0, row=2+idx, sticky=(E,W))
        
        self.lista_vars_checkbuttons = lista_vars_checkbuttons.copy()
        
        return frame
    
    def crear_panel_parametros_entrenamiento(self, parent_frame) -> ttk.Frame:
        training_params = predict.get_training_params(self.var_modelo_elegido.get())
        
        frame = ttk.Frame(parent_frame)
        
        ttk.Label(frame, text='Parametros de entrenamiento').grid(column=0, row=0)
        self.widget_params_entrenamiento = Text(frame, width=40)
        self.widget_params_entrenamiento.grid(column=0, row=1)
        
        self.widget_params_entrenamiento.insert('0.0', training_params)
        
        return frame
    
    def actualizar_dependencias_modelo(self, other_var):
        panel_etiquetas = self.crear_panel_etiquetas(self.panel_entradas)
        panel_etiquetas.grid(column=1, row=1, rowspan=2)
        training_params = predict.get_training_params(self.var_modelo_elegido.get())
        
        # Params entrenamiento
        self.widget_params_entrenamiento.insert('0.0', training_params)
        
    def crear_frame_salida_videos(self, parent_frame) -> ttk.Frame:
        def crear_panel_control_multimedia(padre):
            control_multimedia = ttk.Frame(padre)
            ttk.Label(control_multimedia, text='Control Multimedia').grid(column=0,row=0, columnspan=2)
            ttk.Button(control_multimedia,text='<', command=self.anterior_multimedia).grid(column=0, row=1)
            ttk.Button(control_multimedia,text='>  ||', command=self.reiniciar_multimedia).grid(column=1, row=1)
            ttk.Button(control_multimedia,text='>', command=self.siguiente_multimedia).grid(column=2, row=1)
            
            return control_multimedia
            
        frame = ttk.Frame(parent_frame)
        
        ttk.Label(frame, text='Salida').grid(column=0,row=0)
        ttk.Label(frame, textvariable=self.archivo_a_mostrar).grid(column=1,row=0)
        crear_panel_control_multimedia(frame).grid(column=1, row=4)
        self.widget_deteccion_imagen = ttk.Label(frame)
        self.widget_deteccion_imagen.grid(column=0, row=1, padx=10, columnspan=3, rowspan=3)
                
        self.configurar_widget_multimedia()        
        
        return frame
    
    def siguiente_multimedia(self):
        self.configurar_widget_multimedia(siguiente=True)
        
    def anterior_multimedia(self):
        self.configurar_widget_multimedia(siguiente=False)
        
    def reiniciar_multimedia(self):
        if self.modo_imagen: return
            
        self.capture.release()
        self.capture = cv2.VideoCapture(self.archivo_a_mostrar.get())
        self.procesar_multimedia()
        pass
        
        
    def configurar_widget_multimedia(self, siguiente: bool = True):
        lista_archivos = os.listdir(self.ruta_salida.get())
        if 'labels' in lista_archivos: lista_archivos.remove('labels')
        
        archivo_nuevo = ''
        tipo_entrada_elegida = self.var_tipo_entrada_elegida.get()
        print(f'tipo_entrada_elegida: {tipo_entrada_elegida}')
        if tipo_entrada_elegida == 'Archivo':
            archivo_nuevo = lista_archivos[0]
        elif tipo_entrada_elegida == 'Carpeta':
            if self.archivo_a_mostrar.get() == '':
                archivo_nuevo = lista_archivos[0]
            else:                
                for idx, archivo in enumerate(lista_archivos):
                    if archivo == os.path.split(self.archivo_a_mostrar.get())[1]:
                        # idx_nuevo = idx
                        if siguiente:
                            if (idx == len(lista_archivos) - 1): 
                                idx = -1
                            idx_nuevo = idx + 1
                        else:
                            if (idx == 0): 
                                idx = len(lista_archivos)                        
                            idx_nuevo = idx - 1
                        
                        archivo_nuevo = lista_archivos[idx_nuevo]                        
                        break
        
        archivo_a_mostrar = f'{self.ruta_salida.get()}/{archivo_nuevo}'
        self.archivo_a_mostrar.set(archivo_a_mostrar)
            
        print(f'seleccionado archivo {archivo_a_mostrar} para mostrar')
        
        extensiones_imagen = ['.jpg', '.jpeg','.png']
        extension = os.path.splitext(archivo_a_mostrar)[1]
        es_imagen = True if extension in extensiones_imagen else False
        print(f'Modo imagen: {es_imagen}. extension: {extension}')
        if es_imagen:
            self.capture = cv2.imread(archivo_a_mostrar)
            self.modo_imagen = True
        else: # Si es video:
            self.modo_imagen = False
            self.capture = cv2.VideoCapture(archivo_a_mostrar)
            
        self.procesar_multimedia()            
    
    def procesar_multimedia(self):
        if self.modo_imagen:
            multimedia = self.capture
        else:
            fotograma_procesado, fotograma = self.capture.read()
                
            if fotograma_procesado:
                multimedia = fotograma                
            else: 
                self.capture.release()
                return
            
        ancho_alto = predict.get_metadata_by_name(self.var_modelo_elegido.get()).image_size
        multimedia = cv2.resize(multimedia, (ancho_alto,ancho_alto))
        multimedia = cv2.cvtColor(multimedia, cv2.COLOR_BGR2RGB)
        multimedia = Image.fromarray(multimedia)
        multimedia = ImageTk.PhotoImage(image=multimedia)
        
        self.widget_deteccion_imagen.configure(image=multimedia)
        self.widget_deteccion_imagen.image = multimedia
        
        if not self.modo_imagen: self.widget_deteccion_imagen.after(10, self.procesar_multimedia)
    
    def crear_panel_cuerpo_mail(self, parent_frame) -> ttk.Frame:
        
        frame = ttk.Frame(parent_frame, borderwidth=2, relief='raised',padding=(10,5))
        ttk.Label(frame, text='Mail').grid(column=0, row=0)
        
        ttk.Label(frame, text='Subject').grid(column=1, row=1)
        ttk.Entry(frame, textvariable=self.var_asunto).grid(column=1, row=2, columnspan=3)
        ttk.Label(frame, text='To:').grid(column=1, row=3)
        ttk.Entry(frame, textvariable=self.var_emails_destino).grid(column=1, row=4, columnspan=3)
        ttk.Button(frame, text='Send', command=self.enviar_email).grid(column=1, row=5)
        ttk.Label(frame, textvariable=self.var_mail_enviado).grid(column=1, row=6)
        
        self.widget_cuerpo_mail = Text(frame, width=100, height=20)
        self.widget_cuerpo_mail.grid(column=0, row=1, rowspan=6)
        return frame
    
    def enviar_email(self):
        def mailto(recipients, subject, body):
            "recipients: string with comma-separated emails (no spaces!)"
            webbrowser.open("mailto:%s?subject=%s&body=%s" %
                (recipients, quote(subject), quote(body)))
        
        asunto = self.var_asunto.get()
        emails = self.var_emails_destino.get()
        cuerpo = self.widget_cuerpo_mail.get('1.0', 'end')
        
        mailto(emails.replace(' ', ''), subject=asunto, body=cuerpo)
        
    
if __name__ == '__main__':
    gui = GUI()
    gui.start()