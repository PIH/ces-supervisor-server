#!/usr/bin/python3

import subprocess as sp, shlex
from time import sleep
import getpass
import os
from tempfile import mkdtemp

import tkinter as tk
from tkinter import filedialog

from dotenv import load_dotenv
load_dotenv()

LAST_IMPORT_DIR = "/media/sup"
LAST_IMPORT_DIR = "~/Documentos"
SITES = ["capitan", "honduras", "laguna", "letrero", "matazano",
        "monterrey", "plan", "reforma", "salvador", "soledad"]
PASSWORD = os.getenv("PASSWORD")

def port_for_site(site):
    return 8000 + SITES.index(site)


def is_up(site):
    command = "ps aux | grep " + site + " | grep -v grep"
    ps = sp.Popen(command, shell=True, stdout=sp.DEVNULL)
    ps.communicate()
    return ps.returncode == 0


def main_loop():
    try:
        while True:
            main_menu()
    except Exception as e:
        print(e)
        input("\n\nLa programa ha fallado. Por favor revisa el información arriba "
                "para determinar que pasó.\n\n"
                "Presiona Enter para cerrar la ventana.")


def main_menu():
    show_running()
    print()
    options = ["Correr un EMR", "Parar un EMR", "Importar datos", "Exportar usuarios", "Importar usuarios"]
    selection = _get_selection("Que quieres hacer?", options)
    if selection == options[0]:
        run_emr()
    elif selection == options[1]:
        stop_server()
    elif selection == options[2]:
        import_data()
    elif selection == options[3]:
        export_users()
    elif selection == options[4]:
        import_users()


def show_running():
    running_sites = [s for s in SITES if is_up(s)]
    if running_sites:
        print("Ya corriendo:\n"
                + "\n".join(
                    ["{}\t({})".format(s, port_for_site(s)) for s in running_sites]
                ) + "\n")


def run_emr():
    sites_with_running_info = [
            s + (" (activo)" if is_up(s) else "")
            for s in SITES]
    site = _get_selection(
            "Elegir un EMR de correr, o (0) para regresar.",
            sites_with_running_info).split(' ')[0].strip()

    if not is_up(site):
        start_server(site)

    launch_browser(site)


def start_server(site):
    print("Ok, corriendo " + site + "...")

    command = "mvn openmrs-sdk:run -e --offline -DserverId=" + site

    process = sp.Popen(command, stdout=sp.PIPE, shell=True)

    output = ""
    while True:
        line = process.stdout.readline()
        output += "\n" + str(line)
        print('.', end='', flush=True)
        if process.poll() is not None or line is None:
            print("\nAlgo no esta bien. Por favor enviar esto a IT:")
            print(output)
            break
        if "Starting ProtocolHandler" in str(line):
            print("\nEl EMR ha iniciado. Corriendo el navegador.")
            break
        elif "is already in use. Would you like to use" in str(line):
            print("\nEMR para " + site + " ya esta corriendo pue!")
            break


def stop_server():
    running_sites = [s for s in SITES if is_up(s)]
    site = _get_selection("Elegir un EMR de parar.", running_sites)
    process = sp.Popen(
            "kill $(ps -ef | grep "
            + site
            + " | grep -v grep | awk '{print $2}')",
            shell=True)
    process.wait()
    sleep(3)
    print("Ok, lo maté!")


def import_data():
    global LAST_IMPORT_DIR
    print("Por favor eliges el .sql archivo que quieres importar.")
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(initialdir=LAST_IMPORT_DIR)
    LAST_IMPORT_DIR = os.path.dirname(file_path)
    site = _get_selection("A cual EMR quieres importar el archivo {}?".format(file_path), SITES)
    tmp_dir = mkdtemp()
    print("\n\n=== DECOMPRESSANDO ===\n")
    unzip_process = sp.Popen(["7za", "e", file_path,
            "-p" + PASSWORD,
            "-o" + tmp_dir])
    unzip_process.communicate()
    _check_return_code(unzip_process)
    file_path = tmp_dir + "/pihemr-archivo.sql"
    print("\n\n=== PREPARANDO PARA IMPORTAR ===\n")
    print("...")
    fix_process = sp.Popen(
            "sed -i -E 's/DEFINER=[^]+@[^]+/DEFINER=`openmrs`/g' " + file_path,
            shell=True)
    fix_process.communicate()
    _check_return_code(fix_process)
    print("\n\n=== CARGANDO AL BASE DE DATOS ===\n")
    print("This may take a while...")
    _run_in_docker("mysql -u openmrs " +
            "--password=" + PASSWORD +
            " -D " + site +
            " <" + file_path, "-i")


def export_users():
    site = _get_selection("De cual EMR quieres exportar las cuentas?", SITES)

    insert_users = _run_in_docker("mysqldump -uopenmrs -p" + PASSWORD + " --databases " + site +
            " --tables users --where 'user_id NOT IN (1,2)' --no-create-info | " +
            "grep 'INSERT INTO' | " +
            "perl -pe 's/(\(.*?,.*?,.*?,.*?,.*?,.*?,.*?),.*?,/\\1,1,/g' | " +  # fix creator
            "perl -pe 's/(\(.*?,.*?,.*?,.*?,.*?,.*?,.*?,.*?,.*?),.*?,/\\1,1,/g' | " +  # fix changed_by
            "perl -pe 's/(\(.*?,.*?,.*?,.*?,.*?,.*?,.*?,.*?,.*?,.*?,.*?),.*?,/\\1,1,/g' | " +  # fix person_id
            "perl -pe 's/\(.*?,/(/g' | " +  # remove primary key
            "sed 's/VALUES/(system_id,username,password,salt,secret_question,secret_answer  ,creator,date_created   ,changed_by     ,date_changed   ,person_id      ,retired        ,retired_by     ,date_retired   ,retire_reason  ,uuid           ,activation_key ,email) VALUES/' ")

    with open('/home/sup/Descargas/users.sql', 'wb') as f:
        f.write(insert_users)


def import_users():
    print("Por favor eliges el archivo 'users.sql' que quieres importar.")
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(initialdir="/home/sup/Descargas")
    if file_path == "":
        print("Oups, eso no parece bien. Vamos al inicio.")
        return
    site_options = SITES + ["Todos"]
    site = _get_selection("A cual EMR quieres importar usuarios? (0 para regresar)", site_options)
    if site == None:
        return
    elif site == "Todos":
        sites = SITES
    else:
        sites = [site]
    for site in sites:
        # Import the users
        _run_in_docker(
                "mysql -uopenmrs --password=" + PASSWORD + " " + site + " <" + file_path,
                "-i")
        # Just update the password for the users that already existed
        _run_sql(site, "UPDATE users INNER JOIN users u ON users.username = u.username AND u.person_id = 1 " +
                "SET users.password=u.password, users.salt=u.salt")
        _run_sql(site, "DELETE u1 FROM users u1 JOIN users u2 " +
                "WHERE u1.username = u2.username " +
                "AND u1.person_id = 1 " +
                "AND u1.user_id NOT IN (1,2) " +
                "AND u1.user_id <> u2.user_id")
        # Give everyone all the roles
        _run_sql(site, "INSERT INTO user_role (user_id, role) " +
                "SELECT u.user_id, r.role FROM users u CROSS JOIN role r " +
                "WHERE u.user_id NOT IN (1,2) " +
                "AND (SELECT COUNT(*) FROM user_role WHERE user_id = u.user_id AND role = r.role) = 0")


def launch_browser(site):
    command = "firefox -new-tab http://localhost:" + str(port_for_site(site)) + "/openmrs"
    process = sp.Popen(command, shell=True, stdout=sp.DEVNULL, stderr=sp.PIPE)


def _get_selection(prompt, options):
    """Prompts the user to select one of the provided options.

    Returns either the selected option, or None if the user enters "0".
    """
    if not options:
        print("Oups. Disculpa.")
        main_loop()
    selection_prompt = (prompt
            + "\n"
            + "\n".join(
                ["{}) {}".format(i + 1, val) for i, val in enumerate(options)]
            ) + "\n")
    result = None
    while result is None:
        try:
            selection = int(input(selection_prompt))
            if selection == 0:
                return None
            result = options[selection - 1]
            return result
        except (ValueError, IndexError) as e:
            print("Oups! Eso no es input valido. Intenta otra vez.")


def _check_return_code(process):
    if process.returncode != 0:
        raise Exception("Program exited with return code {}".format(process.returncode))


def _run_in_docker(command, exec_flags=""):
    docker_cmd = "docker exec " + exec_flags + " $(docker ps | grep openmrs-sdk-mysql | cut -f1 -d' ') " + command
    # print(docker_cmd)
    result = sp.check_output(docker_cmd, shell=True)
    # print(result)
    return result


def _run_sql(database, command):
    mysql_cmd = "mysql -uopenmrs --password=" + PASSWORD + " -e '" + command + "' " + database
    return _run_in_docker(mysql_cmd)


if __name__ == "__main__":
    main_loop()


