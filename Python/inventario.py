import os
import sys
import socket
import platform
import psutil
import uuid
import logging
import requests
import tempfile
import mysql.connector
from cpuinfo import get_cpu_info
from pathlib import Path
from datetime import datetime

# Configuração de log
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.FileHandler("inventario.log"), logging.StreamHandler()]
)

def obter_dados_maquina():
    try:
        machine_id = hex(uuid.getnode())  # ID único baseado no MAC
        username = os.getlogin()
        hostname = socket.gethostname()
        os_info = platform.platform()
        ip_local = socket.gethostbyname(hostname)

        try:
            ip_public = requests.get('https://api.ipify.org').text
        except Exception:
            ip_public = 'Desconhecido'

        cpu = get_cpu_info().get('brand_raw', 'Desconhecido')
        ram = f"{round(psutil.virtual_memory().total / (1024**3), 2)} GB"
        disk = f"{round(psutil.disk_usage('/').total / (1024**3), 2)} GB"

        return {
            'machine_id': machine_id,
            'username': username,
            'hostname': hostname,
            'os': os_info,
            'ip_local': ip_local,
            'ip_public': ip_public,
            'cpu': cpu,
            'ram': ram,
            'disk': disk
        }
    except Exception as e:
        logging.error(f"Erro ao obter dados da máquina: {e}")
        return None

def inserir_no_banco(data):
    try:
        conn = mysql.connector.connect(
            host="10.200.9.66",
            user="jadiran",
            password="123",
            database="sistema_auth"
        )
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO computers (machine_id, username, hostname, os, ip_local, ip_public, cpu, ram, disk)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                username=VALUES(username),
                hostname=VALUES(hostname),
                os=VALUES(os),
                ip_local=VALUES(ip_local),
                ip_public=VALUES(ip_public),
                cpu=VALUES(cpu),
                ram=VALUES(ram),
                disk=VALUES(disk),
                created_at=CURRENT_TIMESTAMP
        """, (
            data['machine_id'], data['username'], data['hostname'],
            data['os'], data['ip_local'], data['ip_public'],
            data['cpu'], data['ram'], data['disk']
        ))

        conn.commit()
        cursor.close()
        conn.close()
        logging.info("✅ Dados inseridos ou atualizados com sucesso!")

    except mysql.connector.Error as err:
        logging.error(f"❌ Erro ao conectar/inserir no banco: {err}")
    except Exception as e:
        logging.error(f"❌ Erro inesperado: {e}")

def criar_atalho_startup():
    try:
        startup_path = os.path.join(os.getenv('APPDATA'), r"Microsoft\Windows\Start Menu\Programs\Startup")
        atalho_path = os.path.join(startup_path, "inventario.lnk")
        exe_path = sys.executable

        if not os.path.exists(atalho_path):
            import pythoncom
            from win32com.client import Dispatch
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(atalho_path)
            shortcut.Targetpath = exe_path
            shortcut.WorkingDirectory = os.path.dirname(exe_path)
            shortcut.save()
            logging.info("✅ Atalho criado na pasta Startup.")
        else:
            logging.info("ℹ️ Atalho já existe na pasta Startup.")
    except Exception as e:
        logging.error(f"❌ Erro ao criar atalho de inicialização: {e}")

def is_another_instance_running(lock_file_path):
    if lock_file_path.exists():
        try:
            with lock_file_path.open("r") as f:
                pid = int(f.read())
            if pid != os.getpid() and psutil.pid_exists(pid):
                return True
        except Exception:
            pass
    try:
        with lock_file_path.open("w") as f:
            f.write(str(os.getpid()))
    except Exception as e:
        logging.error(f"Erro ao criar lock file: {e}")
    return False

def main():
    lock_file = Path(tempfile.gettempdir()) / "inventario.lock"
    if is_another_instance_running(lock_file):
        logging.warning("⚠️ Outra instância já está rodando. Abortando.")
        return

    dados = obter_dados_maquina()
    if dados:
        inserir_no_banco(dados)
        criar_atalho_startup()

if __name__ == "__main__":
    main()
    try:
        if sys.stdout.isatty():
            input("Pressione ENTER para sair...")
    except Exception:
        pass
