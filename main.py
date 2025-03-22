import threading  # Importar threading para manejar hilos
import minecraft_launcher_lib
import os
import subprocess
import json
import customtkinter as ctk
from tkinter import messagebox, scrolledtext
import msal  # Biblioteca para la autenticación de Microsoft

# Archivo de configuración
CONFIG_FILE = "CRconfig.json"

def cargar_configuracion():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"username": "", "ram": "4"}

def guardar_configuracion():
    with open(CONFIG_FILE, "w") as f:
        json.dump({"username": entry_nombre.get().strip(), "ram": entry_ram.get().strip()}, f)

config = cargar_configuracion()

# Configuración de la aplicación de Azure
CLIENT_ID = "your_client_id"  # Reemplaza con tu Client ID
CLIENT_SECRET = "your_client_secret"  # Reemplaza con tu Client Secret
AUTHORITY = "https://login.microsoftonline.com/common"  # Autoridad para cuentas personales
SCOPE = ["XboxLive.signin", "XboxLive.offline_access"]  # Permisos necesarios

def iniciar_sesion_microsoft():
    global cuenta_microsoft
    try:
        # Crear una instancia de la aplicación MSAL
        app = msal.PublicClientApplication(
            CLIENT_ID,
            authority=AUTHORITY,
        )

        # Iniciar el flujo de autenticación interactivo
        result = app.acquire_token_interactive(
            scopes=SCOPE,
            prompt="select_account",  # Permite al usuario seleccionar una cuenta
        )

        if "access_token" in result:
            cuenta_microsoft = result
            messagebox.showinfo("Inicio de sesión", "Inicio de sesión exitoso")
        else:
            messagebox.showerror("Error", f"Error en la autenticación: {result.get('error_description')}")
    except Exception as e:
        messagebox.showerror("Error", f"Error en la autenticación: {str(e)}")

def ejecutar_minecraft():
    if not entry_nombre.get().strip():
        messagebox.showerror("Error", "Debes ingresar un nombre de usuario.")
        return

    version_seleccionada = menu_versiones.get()
    if not version_seleccionada:
        messagebox.showerror("Error", "Selecciona una versión de Minecraft.")
        return
    
    # Obtener la IP del servidor (si se ha ingresado)
    ip_servidor = entry_ip_servidor = None

    opciones = {
        "username": entry_nombre.get().strip(),
        "uuid": cuenta_microsoft["id_token_claims"]["sub"] if cuenta_microsoft else "",  # Usar el UUID de la cuenta
        "token": cuenta_microsoft["access_token"] if cuenta_microsoft else "",  # Usar el token de acceso
        "jvmArguments": [f"-Xmx{entry_ram.get() or '4'}G"]  # Usa 4GB por defecto
    }
    
    try:
        minecraft_command = minecraft_launcher_lib.command.get_minecraft_command(version_seleccionada, minecraft_directori, opciones)
        subprocess.Popen(minecraft_command)
        guardar_configuracion()

        # Mostrar mensaje si se ha ingresado una IP de servidor
        if ip_servidor:
            messagebox.showinfo("Multijugador", f"Conéctate manualmente al servidor: {ip_servidor}")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo iniciar Minecraft: {str(e)}")

def instalar_version():
    version_seleccionada = menu_instalar_versiones.get()
    if not version_seleccionada:
        messagebox.showerror("Error", "Selecciona una versión para instalar.")
        return
    
    try:
        # Crear una ventana de carga
        ventana_carga = ctk.CTkToplevel(ventana)
        ventana_carga.title("Instalando versión...")
        ventana_carga.geometry("400x150")
        ventana_carga.resizable(False, False)

        # Etiqueta para mostrar el estado
        label_estado = ctk.CTkLabel(ventana_carga, text="Iniciando instalación...", font=("Arial", 12))
        label_estado.pack(pady=10)

        # Barra de progreso
        progress_bar = ctk.CTkProgressBar(ventana_carga, width=300)
        progress_bar.pack(pady=10)
        progress_bar.set(0)  # Inicializar la barra de progreso en 0

        # Función para actualizar la pantalla de carga
        def actualizar_pantalla(progreso_actual, progreso_total):
            progress_bar.set(progreso_actual / progreso_total)  # Actualizar la barra de progreso
            label_estado.configure(text=f"Progreso: {int((progreso_actual / progreso_total) * 100)}%")
            ventana_carga.update_idletasks()  # Actualizar la ventana

        # Función para instalar la versión en un hilo secundario
        def instalar_en_hilo():
            try:
                # Instalar la versión seleccionada
                minecraft_launcher_lib.install.install_minecraft_version(
                    versionid=version_seleccionada,
                    minecraft_directory=minecraft_directori,
                    callback={
                        "setStatus": lambda text: label_estado.configure(text=text),  # Actualizar el estado
                        "setProgress": lambda value: actualizar_pantalla(value, 100),  # Actualizar el progreso
                        "setMax": lambda value: None  # No necesitamos este parámetro
                    }
                )

                # Cerrar la ventana de carga y mostrar mensaje de éxito
                ventana_carga.destroy()
                messagebox.showinfo("Éxito", "Versión instalada correctamente.")
                mostrar_versiones_instaladas()  # Actualizar la lista de versiones instaladas
                actualizar_menu_versiones()  # Actualizar el menú de versiones
            except Exception as e:
                ventana_carga.destroy()  # Cerrar la ventana de carga en caso de error
                messagebox.showerror("Error", f"No se pudo instalar la versión: {str(e)}")

        # Ejecutar la instalación en un hilo secundario
        threading.Thread(target=instalar_en_hilo, daemon=True).start()

    except Exception as e:
        messagebox.showerror("Error", f"No se pudo iniciar la instalación: {str(e)}")

def instalar_forge():
    try:
        # Obtener la versión seleccionada
        version_seleccionada = menu_instalar_versiones.get()
        if not version_seleccionada:
            messagebox.showerror("Error", "Selecciona una versión de Minecraft.")
            return

        # Crear una ventana de carga
        ventana_carga = ctk.CTkToplevel(ventana)
        ventana_carga.title("Instalando Forge...")
        ventana_carga.geometry("400x150")
        ventana_carga.resizable(False, False)

        # Etiqueta para mostrar el estado
        label_estado = ctk.CTkLabel(ventana_carga, text="Iniciando instalación de Forge...", font=("Arial", 12))
        label_estado.pack(pady=10)

        # Barra de progreso
        progress_bar = ctk.CTkProgressBar(ventana_carga, width=300)
        progress_bar.pack(pady=10)
        progress_bar.set(0)  # Inicializar la barra de progreso en 0

        # Función para actualizar la pantalla de carga
        def actualizar_pantalla(progreso_actual, progreso_total):
            progress_bar.set(progreso_actual / progreso_total)  # Actualizar la barra de progreso
            label_estado.configure(text=f"Progreso: {int((progreso_actual / progreso_total) * 100)}%")
            ventana_carga.update_idletasks()  # Actualizar la ventana

        # Función para instalar Forge en un hilo secundario
        def instalar_forge_en_hilo():
            try:
                # Instalar Forge para la versión seleccionada
                minecraft_launcher_lib.forge.install_forge_version(
                    version_seleccionada,  # Solo se pasa la versión
                    callback={
                        "setStatus": lambda text: label_estado.configure(text=text),  # Actualizar el estado
                        "setProgress": lambda value: actualizar_pantalla(value, 100),  # Actualizar el progreso
                        "setMax": lambda value: None  # No necesitamos este parámetro
                    }
                )

                # Cerrar la ventana de carga y mostrar mensaje de éxito
                ventana_carga.destroy()
                messagebox.showinfo("Éxito", "Forge instalado correctamente.")
                mostrar_versiones_instaladas()  # Actualizar la lista de versiones instaladas
                actualizar_menu_versiones()  # Actualizar el menú de versiones
            except Exception as e:
                ventana_carga.destroy()  # Cerrar la ventana de carga en caso de error
                messagebox.showerror("Error", f"No se pudo instalar Forge: {str(e)}")

        # Ejecutar la instalación en un hilo secundario
        threading.Thread(target=instalar_forge_en_hilo, daemon=True).start()

    except Exception as e:
        messagebox.showerror("Error", f"No se pudo iniciar la instalación de Forge: {str(e)}")

def instalar_fabric():
    try:
        # Obtener la versión seleccionada
        version_seleccionada = menu_instalar_versiones.get()
        if not version_seleccionada:
            messagebox.showerror("Error", "Selecciona una versión de Minecraft.")
            return

        # Crear una ventana de carga
        ventana_carga = ctk.CTkToplevel(ventana)
        ventana_carga.title("Instalando Fabric...")
        ventana_carga.geometry("400x150")
        ventana_carga.resizable(False, False)

        # Etiqueta para mostrar el estado
        label_estado = ctk.CTkLabel(ventana_carga, text="Iniciando instalación de Fabric...", font=("Arial", 12))
        label_estado.pack(pady=10)

        # Barra de progreso
        progress_bar = ctk.CTkProgressBar(ventana_carga, width=300)
        progress_bar.pack(pady=10)
        progress_bar.set(0)  # Inicializar la barra de progreso en 0

        # Función para actualizar la pantalla de carga
        def actualizar_pantalla(progreso_actual, progreso_total):
            progress_bar.set(progreso_actual / progreso_total)  # Actualizar la barra de progreso
            label_estado.configure(text=f"Progreso: {int((progreso_actual / progreso_total) * 100)}%")
            ventana_carga.update_idletasks()  # Actualizar la ventana

        # Función para instalar Fabric en un hilo secundario
        def instalar_fabric_en_hilo():
            try:
                # Instalar Fabric para la versión seleccionada
                minecraft_launcher_lib.fabric.install_fabric(
                    version_seleccionada,
                    minecraft_directory=minecraft_directori,
                    callback={
                        "setStatus": lambda text: label_estado.configure(text=text),  # Actualizar el estado
                        "setProgress": lambda value: actualizar_pantalla(value, 100),  # Actualizar el progreso
                        "setMax": lambda value: None  # No necesitamos este parámetro
                    }
                )

                # Cerrar la ventana de carga y mostrar mensaje de éxito
                ventana_carga.destroy()
                messagebox.showinfo("Éxito", "Fabric instalado correctamente.")
                mostrar_versiones_instaladas()  # Actualizar la lista de versiones instaladas
                actualizar_menu_versiones()  # Actualizar el menú de versiones
            except Exception as e:
                ventana_carga.destroy()  # Cerrar la ventana de carga en caso de error
                messagebox.showerror("Error", f"No se pudo instalar Fabric: {str(e)}")

        # Ejecutar la instalación en un hilo secundario
        threading.Thread(target=instalar_fabric_en_hilo, daemon=True).start()

    except Exception as e:
        messagebox.showerror("Error", f"No se pudo iniciar la instalación de Fabric: {str(e)}")

def mostrar_versiones_instaladas():
    versiones_instaladas = minecraft_launcher_lib.utils.get_installed_versions(minecraft_directori)
    if versiones_instaladas:
        lista_versiones = "\n".join([v['id'] for v in versiones_instaladas])
        textbox_versiones_instaladas.delete("1.0", "end")  # Limpiar el contenido anterior
        textbox_versiones_instaladas.insert("1.0", lista_versiones)  # Insertar la nueva lista
    else:
        textbox_versiones_instaladas.delete("1.0", "end")
        textbox_versiones_instaladas.insert("1.0", "No hay versiones instaladas.")

def obtener_version_mas_reciente(versiones):
    # Ordenar las versiones por fecha de lanzamiento (la más reciente primero)
    versiones_ordenadas = sorted(versiones, key=lambda v: v.get("releaseTime", "0"), reverse=True)
    if versiones_ordenadas:
        return versiones_ordenadas[0]["id"]
    return None

def actualizar_menu_versiones():
    versiones_instaladas = minecraft_launcher_lib.utils.get_installed_versions(minecraft_directori)
    if versiones_instaladas:
        version_mas_reciente = obtener_version_mas_reciente(versiones_instaladas)
        menu_versiones.configure(values=[v['id'] for v in versiones_instaladas])
        if version_mas_reciente:
            menu_versiones.set(version_mas_reciente)  # Establecer la versión más reciente como predeterminada

# Configuración de estilos
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Configuración de la ventana principal
ventana = ctk.CTk()
ventana.geometry('800x600')  # Tamaño inicial de la ventana
ventana.title('Crimson Launcher')
ventana.resizable(True, True)  # Permitir que el usuario cambie el tamaño de la ventana
ventana.minsize(700, 500)  # Establecer un tamaño mínimo para la ventana

# Ruta de la carpeta .minecraft
user_window = os.environ["USERNAME"]
minecraft_directori = os.path.join("C:", "Users", user_window, "AppData", "Roaming", ".minecraft")

cuenta_microsoft = None

# Barra de progreso (definida antes de usarla)
progress_bar = ctk.CTkProgressBar(ventana)
progress_bar.set(0)  # Inicializar la barra de progreso en 0

# Crear un frame para la sección "Launch Game"
frame_launch = ctk.CTkFrame(ventana)
frame_launch.pack(pady=10, padx=10, fill="x")

label_launch = ctk.CTkLabel(frame_launch, text="LAUNCH GAME", font=("Arial", 16, "bold"))
label_launch.pack(pady=5)

# Campo de entrada para el nombre de usuario
label_nombre = ctk.CTkLabel(frame_launch, text="Nombre de usuario:", font=("Arial", 12))
label_nombre.pack(pady=5)
entry_nombre = ctk.CTkEntry(frame_launch, placeholder_text="Introduce tu nombre")
entry_nombre.pack(pady=5)
entry_nombre.insert(0, config["username"])  # Cargar nombre guardado

# Campo de entrada para la RAM
label_ram = ctk.CTkLabel(frame_launch, text="RAM a usar (GB):", font=("Arial", 12))
label_ram.pack(pady=5)
entry_ram = ctk.CTkEntry(frame_launch, placeholder_text="Introduce la RAM")
entry_ram.pack(pady=5)
entry_ram.insert(0, config["ram"])  # Cargar RAM guardada

# Menú de versiones para lanzar el juego
menu_versiones = ctk.CTkComboBox(frame_launch, values=[])
menu_versiones.pack(pady=5)

# Botón para lanzar Minecraft
bt_ejecutar_minecraft = ctk.CTkButton(frame_launch, text="Launch", command=ejecutar_minecraft)
bt_ejecutar_minecraft.pack(pady=10)

# Crear un frame para la sección "Install & Manage Versions"
frame_install = ctk.CTkFrame(ventana)
frame_install.pack(pady=10, padx=10, fill="x")

label_install = ctk.CTkLabel(frame_install, text="INSTALL & MANAGE VERSIONS", font=("Arial", 16, "bold"))
label_install.pack(pady=5)

# Menú de versiones para instalar
menu_instalar_versiones = ctk.CTkComboBox(frame_install, values=["1.19.4", "1.18.2", "1.17.1"])  # Ejemplo de versiones
menu_instalar_versiones.pack(pady=5)

# Botón para instalar versiones de Minecraft
bt_instalar_versiones = ctk.CTkButton(frame_install, text="Install Version", command=instalar_version)
bt_instalar_versiones.pack(pady=5)

# Botón para instalar Forge
bt_instalar_forge = ctk.CTkButton(frame_install, text="Install Forge", command=instalar_forge)
bt_instalar_forge.pack(pady=5)

# Botón para instalar Fabric
bt_instalar_fabric = ctk.CTkButton(frame_install, text="Install Fabric", command=instalar_fabric)
bt_instalar_fabric.pack(pady=5)

# Botón para mostrar versiones instaladas
bt_mostrar_versiones = ctk.CTkButton(frame_install, text="Show Installed Versions", command=mostrar_versiones_instaladas)
bt_mostrar_versiones.pack(pady=5)

# Textbox para mostrar versiones instaladas
textbox_versiones_instaladas = ctk.CTkTextbox(frame_install, width=400, height=150)
textbox_versiones_instaladas.pack(pady=10)

# Crear un frame para la sección "Friends"
frame_friends = ctk.CTkFrame(ventana)
frame_friends.pack(pady=10, padx=10, fill="x")

label_friends = ctk.CTkLabel(frame_friends, text="FRIENDS", font=("Arial", 16, "bold"))
label_friends.pack(pady=5)

label_friends_info = ctk.CTkLabel(frame_friends, text="Chat with friends, send game invites, and more!")
label_friends_info.pack(pady=5)

bt_add_friend = ctk.CTkButton(frame_friends, text="Add your first friend")
bt_add_friend.pack(pady=5)

# Crear un frame para la sección "Latest News"
frame_news = ctk.CTkFrame(ventana)
frame_news.pack(pady=10, padx=10, fill="x")

label_news = ctk.CTkLabel(frame_news, text="LATEST NEWS", font=("Arial", 16, "bold"))
label_news.pack(pady=5)

label_news1 = ctk.CTkLabel(frame_news, text="GREATORS BEWARE", font=("Arial", 14))
label_news1.pack(pady=2)

label_news2 = ctk.CTkLabel(frame_news, text="IS KICKING IN", font=("Arial", 14))
label_news2.pack(pady=2)

label_news3 = ctk.CTkLabel(frame_news, text="LUNAR CLIENT", font=("Arial", 14))
label_news3.pack(pady=2)

label_news4 = ctk.CTkLabel(frame_news, text="BADLION", font=("Arial", 14))
label_news4.pack(pady=2)

label_news5 = ctk.CTkLabel(frame_news, text="MONTHLY RECAP", font=("Arial", 14))
label_news5.pack(pady=2)

# Botón para iniciar sesión con Microsoft
bt_login_microsoft = ctk.CTkButton(ventana, text="Iniciar sesión con Microsoft", command=iniciar_sesion_microsoft)
bt_login_microsoft.pack(pady=10)

# Actualizar el menú de versiones al iniciar la aplicación
actualizar_menu_versiones()

ventana.mainloop()