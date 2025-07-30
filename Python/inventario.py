import os
import sys
import uuid
import socket
import psutil
import cpuinfo
import logging
import getpass
import win32com.client
from datetime import datetime
import mysql.connector
from mysql.connector import Error
import wmi
import netifaces

LOCKFILE = os.path.join(os.getenv("TEMP"), "inventario.lock")

# Caminho do arquivo de log (na mesma pasta do executável ou script)
if getattr(sys, 'frozen', False):
    log_path = os.path.join(os.path.dirname(sys.executable), "inventario.log")
else:
    log_path = os.path.join(os.path.dirname(__file__), "inventario.log")

# Configuração de log
file_handler = logging.FileHandler(log_path, encoding='utf-8')
console_handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)
logging.basicConfig(level=logging.INFO, handlers=[file_handler, console_handler])

def ja_esta_rodando():
    if os.path.exists(LOCKFILE):
        logging.warning("Outra instância já está rodando. Abortando.")
        return True
    with open(LOCKFILE, 'w') as f:
        f.write(str(os.getpid()))
    return False

def remover_lock():
    if os.path.exists(LOCKFILE):
        os.remove(LOCKFILE)

def tipo_maquina():
    c = wmi.WMI()
    for system in c.Win32_SystemEnclosure():
        if system.ChassisTypes:
            tipo = system.ChassisTypes[0]
            if tipo in [8, 9, 10, 14]:
                return "Notebook"
            elif tipo in [3, 4, 5, 6, 7, 15]:
                return "Desktop"
    return "Desconhecido"

def fabricante_modelo_serial():
    c = wmi.WMI()
    system = c.Win32_ComputerSystem()[0]
    bios = c.Win32_BIOS()[0]
    return system.Manufacturer.strip(), system.Model.strip(), bios.SerialNumber.strip()

def obter_ips():
    ip_wifi = None
    ip_ethernet = None
    interfaces = netifaces.interfaces()
    for iface in interfaces:
        addrs = netifaces.ifaddresses(iface)
        if netifaces.AF_INET in addrs:
            ip = addrs[netifaces.AF_INET][0]['addr']
            desc = iface.lower()
            if "wi-fi" in desc or "wlan" in desc:
                ip_wifi = ip
            elif "ethernet" in desc or "eth" in desc:
                ip_ethernet = ip
    return ip_wifi, ip_ethernet

def coletar_dados():
    fabricante, modelo, serial = fabricante_modelo_serial()
    ip_wifi, ip_ethernet = obter_ips()
    info = {
        "usuario": getpass.getuser(),
        "ip": socket.gethostbyname(socket.gethostname()),
        "ram": round(psutil.virtual_memory().total / (1024 ** 3), 2),
        "armazenamento": round(psutil.disk_usage('/').total / (1024 ** 3), 2),
        "processador": cpuinfo.get_cpu_info()['brand_raw'],
        "id_unico": str(uuid.getnode()),
        "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "tipo_maquina": tipo_maquina(),
        "fabricante": fabricante,
        "modelo": modelo,
        "numero_serie": serial,
        "ip_wifi": ip_wifi,
        "ip_ethernet": ip_ethernet
    }
    return info

def inserir_no_banco(dados):
    try:
        conn = mysql.connector.connect(
            host='SEU_HOST',
            user='SEU_USUARIO',
            password='SUA_SENHA',
            database='sistema_auth'
        )
        cursor = conn.cursor()

        query = '''
        INSERT INTO computadores (
            id_unico, usuario, ip, ram, armazenamento, processador, created_at,
            tipo_maquina, fabricante, modelo, numero_serie, ip_wifi, ip_ethernet
        )
        VALUES (
            %(id_unico)s, %(usuario)s, %(ip)s, %(ram)s, %(armazenamento)s, %(processador)s, %(created_at)s,
            %(tipo_maquina)s, %(fabricante)s, %(modelo)s, %(numero_serie)s, %(ip_wifi)s, %(ip_ethernet)s
        )
        ON DUPLICATE KEY UPDATE
            usuario=VALUES(usuario),
            ip=VALUES(ip),
            ram=VALUES(ram),
            armazenamento=VALUES(armazenamento),
            processador=VALUES(processador),
            created_at=VALUES(created_at),
            tipo_maquina=VALUES(tipo_maquina),
            fabricante=VALUES(fabricante),
            modelo=VALUES(modelo),
            numero_serie=VALUES(numero_serie),
            ip_wifi=VALUES(ip_wifi),
            ip_ethernet=VALUES(ip_ethernet)
        '''
        cursor.execute(query, dados)
        conn.commit()
        logging.info("Dados inseridos ou atualizados com sucesso!")
    except Error as e:
        logging.error(f"Erro ao conectar/inserir no banco: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

def criar_atalho_startup():
    nome_atalho = "Inventario.lnk"
    caminho_startup = os.path.join(os.getenv("APPDATA"), r"Microsoft\Windows\Start Menu\Programs\Startup")
    caminho_atalho = os.path.join(caminho_startup, nome_atalho)

    if os.path.exists(caminho_atalho):
        logging.info("Atalho já existe na pasta Startup.")
        return

    shell = win32com.client.Dispatch("WScript.Shell")
    atalho = shell.CreateShortCut(caminho_atalho)
    atalho.Targetpath = sys.executable
    atalho.WorkingDirectory = os.path.dirname(os.path.abspath(__file__))
    atalho.IconLocation = sys.executable
    atalho.save()
    logging.info("Atalho criado na pasta Startup.")

def main():
    if ja_esta_rodando():
        return

    try:
        dados = coletar_dados()
        inserir_no_banco(dados)
        criar_atalho_startup()
    finally:
        remover_lock()

if __name__ == "__main__":
    main()
