from flask import Flask, render_template
app = Flask(__name__)
import platform
import psutil
import re
import subprocess
import cpuinfo
import pynvml
import pandas as pd
import pythoncom
import wmi
import winreg
import subprocess


info_cpu = cpuinfo.get_cpu_info()

def obtener_info_general():
    
    info_general = {}
    
    # Nombre del dispositivo
    info_general["Nombre del Dispositivo: "] = platform.node()

    # Información del procesador
    info_general["Procesador del Sistema"] = platform.processor()
    info_general["Cantidad de Núcleos del Procesador"] = str(psutil.cpu_count(logical=False)) + " núcleos"
    info_general["Cantidad de Hilos del Procesador"] = str(psutil.cpu_count()) + " hilos"

    # Frecuencia base del procesador
    info_general["Frecuencia Base del Procesador"] = info_cpu['hz_advertised_friendly']

    # RAM instalada
    info_general["Ram Instalada en el Sistema"] = str(round(psutil.virtual_memory().total / (1024**3))) + " GB"

    # Información del sistema operativo
    info_general["Tipo de sistema"] = platform.architecture()[0]
    info_general["Tipo de sistema"] = info_general["Tipo de sistema"].replace("bit", " bits")
    
    info_general["Edición de Windows Instalada"] = platform.system() + ' ' + platform.release()
    info_general["Versión de Windows Instalada"] = platform.version()
    info_general["Compilación de SO"] = platform.win32_ver()[2]
    
    return info_general
    
def obtener_espec_procesador():
    
    espec_procesador = {}

    # Nombre del procesador
    espec_procesador["Nombre del Procesador"] = info_cpu['brand_raw']

    # Arquitectura del procesador
    espec_procesador["Arquitectura del Procesador"] = info_cpu['arch']

    # Frecuencia base del procesador
    espec_procesador["Frecuencia Base del Procesador"] = info_cpu['hz_advertised_friendly']
    digitos = ""
    digitos = digitos + (espec_procesador["Frecuencia Base del Procesador"][2])
    digitos = digitos + (espec_procesador["Frecuencia Base del Procesador"][3])
    digitos = digitos + (espec_procesador["Frecuencia Base del Procesador"][4])
    digitos = digitos + (espec_procesador["Frecuencia Base del Procesador"][5])
    espec_procesador["Frecuencia Base del Procesador"] = espec_procesador["Frecuencia Base del Procesador"].replace(digitos,digitos[0])

    # Número de núcleos
    espec_procesador["Número de Núcleos Físicos"] = str(psutil.cpu_count(logical=False)) + " núcleos físicos"

    # Número de hilos
    espec_procesador["Número de Núcleos Lógicos"] = str(info_cpu['count']) + " núcleos lógicos"

    # Fabricante del procesador
    espec_procesador["Fabricante del Procesador"] = info_cpu['vendor_id_raw']

    # Tamaño de la caché L1
    espec_procesador["Caché L1"] = str((int((info_cpu['l2_cache_size']) / 8) / 1024)) + " kB"
    
    # Tamaño de la caché L2
    espec_procesador["Caché L2"] = str(info_cpu['l2_cache_size'] / 1024**2) + " MB"

    # Tamaño de la caché L3
    espec_procesador["Caché L3"] = str(info_cpu['l3_cache_size'] / 1024**2) + " MB"

    return espec_procesador

def obtener_espec_ram():

    espec_ram = {}
    
    pythoncom.CoInitialize()
    w = wmi.WMI()

    # Obtener la información de las memorias RAM instaladas
    info_memoria = w.Win32_PhysicalMemory()

    # variable para obtener cantidad de Memorias
    cant_memorias = len(info_memoria)
    cant_info = 0
    
    # Iterar a través de la información de la memoria RAM
    for mem in info_memoria:
        cant_info = cant_info + 1
        espec_ram["Fabricante de la Memoria (" + str(cant_info) + ")"] = mem.Manufacturer
        espec_ram["Modelo de la Memoria (" + str(cant_info) + ")"] = mem.PartNumber
        espec_ram["Capacidad Total de la Memoria (" + str(cant_info) + ")"] = str(int(mem.Capacity) / (1024**3)) + " GB"
        espec_ram["Velocidad de la Memoria (" + str(cant_info) + ")"] = str(mem.Speed) + " Mhz"
    
    return espec_ram

def obtener_espec_discos():
    
    espec_discos = {}
    
    # Conectar con la API de WMI
    wmi_obj = wmi.WMI()

    # Obtener información de los discos duros
    cant_discos = 0
    for disk in wmi_obj.Win32_DiskDrive():
        cant_discos = cant_discos + 1
        espec_discos["Modelo del Disco (" + str(cant_discos) + ")"] = disk.Model
        espec_discos["Tipo de Interfaz del Disco (" + str(cant_discos) + ")"] = disk.InterfaceType
        espec_discos["Tamaño del Disco (" + str(cant_discos) + ")"] = int(disk.Size)/1024**3
        
        # Verificar si es un SSD o HDD
        if "SSD" in disk.Model.upper():
            espec_discos["Tipo de Disco del Disco (" + str(cant_discos) + ")"] = "SSD"
        else:
            espec_discos["Tipo de Disco del Disco (" + str(cant_discos) + ")"] = "HDD"

        # Obtener información adicional usando asociaciones
        for partition in disk.associators("Win32_DiskDriveToDiskPartition"):
            for logical_disk in partition.associators("Win32_LogicalDiskToPartition"):
                espec_discos["Letra del Disco (" + str(cant_discos) + ")"] = logical_disk.Caption
                espec_discos["Sistema de Archivos del Disco (" + str(cant_discos) + ")"] = logical_disk.FileSystem
                espec_discos["Tamaño Libre del Disco (" + str(cant_discos) + ")"] = str(round((int(logical_disk.FreeSpace)/1024**3), 2)) + " GB"
                espec_discos["Tamaño total del Disco (" + str(cant_discos) + ")"] = str(round((int(logical_disk.Size)/1024**3), 2)) + " GB"
                espec_discos["Tamaño Usado del Disco (" + str(cant_discos) + ")"] = str(round((int(int(logical_disk.Size) - int(logical_disk.FreeSpace))/1024**3), 2)) + " GB"
                # print("Letra de unidad: ", logical_disk.Caption)
                # print("Sistema de archivos: ", logical_disk.FileSystem)
        
    return espec_discos

def obtener_espec_gpu():

    espec_gpu = {}
    
    # Conectar con la biblioteca NVML
    pynvml.nvmlInit()

    # Obtener el número de dispositivos NVIDIA en el sistema
    device_count = pynvml.nvmlDeviceGetCount()

    # Iterar a través de los dispositivos y obtener información de cada uno
    for i in range(device_count):
        handle = pynvml.nvmlDeviceGetHandleByIndex(i)
        gpu_name = pynvml.nvmlDeviceGetName(handle)
        gpu_mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
        gpu_utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
        gpu_temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
        gpu_power_usage = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0
        gpu_power_limit = pynvml.nvmlDeviceGetEnforcedPowerLimit(handle) / 1000.0
        gpu_fan_speed = pynvml.nvmlDeviceGetFanSpeed(handle)
        gpu_pci_info = pynvml.nvmlDeviceGetPciInfo(handle)
        gpu_uuid = pynvml.nvmlDeviceGetUUID(handle)
        gpu_compute_mode = pynvml.nvmlDeviceGetComputeMode(handle)

        # guardar la información en la lista
        espec_gpu["Nombre del GPU"] = gpu_name
        espec_gpu["Memoria Total de GPU"] = str(round((gpu_mem_info.total/1024**3), 2)) + " GB"
        espec_gpu["Memoria Usada de GPU"] = str(round((gpu_mem_info.used/1024**3), 2)) + " GB"
        espec_gpu["Memoria Libre de GPU"] = str(round((gpu_mem_info.free/1024**3), 2)) + " GB"
        espec_gpu["Porcentaje de Uso del GPU"] = str(gpu_utilization.gpu) + " %"
        espec_gpu["Temperatura del GPU"] = str(gpu_temp) + " °C"
        espec_gpu["Consumo de Energía de GPU"] = str(gpu_power_usage) + " W"
        espec_gpu["Límite de Energía de GPU"] = str(gpu_power_limit) + " W"
        espec_gpu["Velocidad de Ventiladores"] = str(gpu_fan_speed) + " %"
        espec_gpu["ID Del Dispositivo"] = gpu_uuid
        espec_gpu["Modo de Computación"] = gpu_compute_mode
        espec_gpu["Tipo de Dispositivo"] = "Dedicada" if "NVIDIA" in gpu_name else "Integrada"
        
    # Finalizar la conexión con la biblioteca NVML
    pynvml.nvmlShutdown()
    
    return espec_gpu

def obtener_programas():
    programas_instalados = {}
    
    # Abrir la clave del Registro que contiene la información de los programas instalados
    reg_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
    
    # Recorrer las subclaves para obtener la información de los programas
    num_subkeys = winreg.QueryInfoKey(reg_key)[0]
    cantidad_programas = 0
    for i in range(num_subkeys):
        subkey_name = winreg.EnumKey(reg_key, i)
        subkey = winreg.OpenKey(reg_key, subkey_name)
        
        try:
            # Obtener los valores de la subclave
            program_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
            program_publisher = winreg.QueryValueEx(subkey, "Publisher")[0]
            install_date = winreg.QueryValueEx(subkey, "InstallDate")[0]
            program_size = winreg.QueryValueEx(subkey, "EstimatedSize")[0]
            program_version = winreg.QueryValueEx(subkey, "DisplayVersion")[0]
            
            cantidad_programas = cantidad_programas + 1
            # Agregar la información del programa a la lista
            
            programas_instalados["Nombre del Programa #" + str(cantidad_programas)] = program_name
            programas_instalados["Editor del Programa #"  + str(cantidad_programas)] = program_publisher
            programas_instalados["Fecha_Instalación del Programa #"  + str(cantidad_programas)] = install_date
            programas_instalados["Tamaño del Programa #"  + str(cantidad_programas)] = program_size
            programas_instalados["Versión del Programa #"  + str(cantidad_programas)] = program_version
        
        except OSError:
            # Ignorar subclaves sin valores requeridos
            pass
        
        subkey.Close()
    
    reg_key.Close()
    return programas_instalados

def obtener_procesos():
    
    procesos_sistema = {}
    
    procesos = psutil.process_iter()

    cantidad_procesos = 0
    
    # Iterar sobre los procesos y obtener información relevante
    for proceso in procesos:
        try:
            # Obtener el ID de proceso (ProcessId), nombre del proceso, número de hilos (ThreadCount) y estado del proceso
            cantidad_procesos = cantidad_procesos + 1
            
            pid = proceso.pid
            nombre = proceso.name()
            num_hilos = proceso.num_threads()
            estado = "En ejecución" if proceso.is_running() else "Detenido"

            
            procesos_sistema["Proceso pid del proceso #" + str(cantidad_procesos)] = pid
            procesos_sistema["Nombre del proceso #" + str(cantidad_procesos)] = nombre
            procesos_sistema["Numero de hilos del proceso #" + str(cantidad_procesos)] = num_hilos
            procesos_sistema["Estado del proceso #" + str(cantidad_procesos)] = estado
            
            # Imprimir la información del proceso
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            # Ignorar procesos que no existen, acceso denegado o procesos zombies
            pass
        
    return procesos_sistema
    

def generar_tablas(datos_general, datos_procesador, datos_ram, datos_discos, datos_gpu, datos_programas, datos_procesos):
    df_general = pd.DataFrame(list(datos_general.items()),columns = ['Característica','Valor'])
    tabla_general = df_general.to_html(classes="table table-striped", index=False)

    df_procesador = pd.DataFrame(list(datos_procesador.items()),columns = ['Característica','Valor'])
    tabla_procesador = df_procesador.to_html(classes="adicional", table_id="tabla1", index=False)

    df_ram = pd.DataFrame(list(datos_ram.items()),columns = ['Característica','Valor'])
    tabla_ram = df_ram.to_html(classes="adicional", table_id="tabla2", index=False)
    
    df_discos = pd.DataFrame(list(datos_discos.items()),columns = ['Característica','Valor'])
    tabla_discos = df_discos.to_html(classes="adicional", table_id="tabla3", index=False)
    
    df_gpu = pd.DataFrame(list(datos_gpu.items()),columns = ['Característica','Valor'])
    tabla_gpu = df_gpu.to_html(classes="adicional", table_id="tabla4", index=False)
    
    df_programas = pd.DataFrame(list(datos_programas.items()),columns = ['Característica','Valor'])
    tabla_programas = df_programas.to_html(classes="adicional", table_id="tabla5", index=False)

    df_procesos = pd.DataFrame(list(datos_procesos.items()),columns = ['Característica','Valor'])
    tabla_procesos = df_procesos.to_html(classes="adicional", table_id="tabla6", index=False)

    return tabla_general, tabla_procesador, tabla_ram, tabla_discos, tabla_gpu, tabla_programas, tabla_procesos

@app.route("/")
def index():
    datos_general = obtener_info_general()
    datos_procesador = obtener_espec_procesador()
    pythoncom.CoInitialize()
    datos_ram = obtener_espec_ram()
    datos_discos = obtener_espec_discos()
    datos_gpu = obtener_espec_gpu()
    datos_programas = obtener_programas()
    datos_procesos = obtener_procesos()
    
    tabla_general, tabla_procesador, tabla_ram, tabla_discos, tabla_gpu, tabla_programas, tabla_procesos = generar_tablas(datos_general, datos_procesador, datos_ram, datos_discos, datos_gpu, datos_programas, datos_procesos) 
    
    return render_template('index.html', tabla_general=tabla_general, tabla_procesador = tabla_procesador, tabla_ram = tabla_ram, tabla_discos = tabla_discos, tabla_gpu = tabla_gpu, tabla_programas = tabla_programas, tabla_procesos = tabla_procesos)

if __name__ == '__main__':
    app.run(debug=True)

# Imprimir la información almacenada en las variables