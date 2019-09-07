#!/usr/bin/python3

import subprocess as sp, shlex
from time import sleep
import getpass

import tkinter as tk
from tkinter import filedialog


SITES = ["capitan", "honduras", "laguna", "letrero", "matazano",
        "monterrey", "plan", "reforma", "salvador", "soledad"]

def port_for_site(site):
    return 8000 + SITES.index(site)


def is_up(site):
    command = "ps aux | grep " + site + " | grep -v grep"
    ps = sp.Popen(command, shell=True, stdout=sp.DEVNULL)
    ps.communicate()
    return ps.returncode == 0


def main_loop():
    while True:
        main_menu()


def main_menu():
    show_running()
    print()
    options = ["Lanzar un EMR", "Parar un EMR", "Importar datos", "Exportar usuarios", "Importar usuarios"]
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
    print("Ya corriendo:\n"
            + "\n".join(
                ["{}\t({})".format(s, port_for_site(s)) for s in running_sites]
            ) + "\n")


def run_emr():
    sites_with_running_info = [
            s + (" (activo)" if is_up(s) else "")
            for s in SITES]
    site = _get_selection("Elegir un EMR de correr.", sites_with_running_info).split(' ')[0].strip()

    if not is_up(site):
        start_server(site)

    launch_browser(site)


def start_server(site):
    print("Ok, lanzando " + site + "...")

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
            print("\nEl EMR ha iniciado. Lanzando navegador.")
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
    sleep(1)
    print("Ok, lo maté!")


def import_data():
    print("Por favor eliges el .sql archivo que quieres importar.")
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(initialdir="/media/sup")
    site = _get_selection("A cual EMR quieres importar el archivo {}?".format(file_path), SITES)
    _run_in_docker("mysql -uopenmrs --password=***REMOVED*** " + site + " <" + file_path)


def export_users():
    site = _get_selection("De cual EMR quieres exportar las cuentas?", SITES)

    insert_users = _run_in_docker("mysqldump -uopenmrs -p***REMOVED*** --databases " + site +
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
    print(file_path)
    #for site in SITES:
    for site in ['laguna']:
        _run_sql(site, "DELETE FROM user_role WHERE user_id NOT IN (1,2)")
        _run_sql(site, "DELETE FROM user_property WHERE user_id NOT IN (1,2)")
        _run_sql(site, "UPDATE users SET changed_by = 1 WHERE user_id NOT IN (1,2)")
        _run_sql(site, "UPDATE visit SET creator=1, changed_by=1, voided_by=1 WHERE creator NOT IN (1,2) OR changed_by NOT IN (1,2) OR voided_by NOT IN (1,2)")
        _run_sql(site, "UPDATE person_attribute SET creator=1, changed_by=1, voided_by=1 WHERE creator NOT IN (1,2) OR changed_by NOT IN (1,2) OR voided_by NOT IN (1,2)")
        _run_sql(site, "UPDATE person SET creator=1, changed_by=1, voided_by=1 WHERE creator NOT IN (1,2) OR changed_by NOT IN (1,2) OR voided_by NOT IN (1,2)")
        _run_sql(site, "UPDATE patient SET creator=1, changed_by=1, voided_by=1 WHERE creator NOT IN (1,2) OR changed_by NOT IN (1,2) OR voided_by NOT IN (1,2)")
        _run_sql(site, "UPDATE encounter SET creator=1, changed_by=1, voided_by=1 WHERE creator NOT IN (1,2) OR changed_by NOT IN (1,2) OR voided_by NOT IN (1,2)")
        _run_sql(site, "UPDATE encounter_provider SET creator=1, changed_by=1, voided_by=1 WHERE creator NOT IN (1,2) OR changed_by NOT IN (1,2) OR voided_by NOT IN (1,2)")
        _run_sql(site, "UPDATE patient_identifier SET creator=1, changed_by=1, voided_by=1 WHERE creator NOT IN (1,2) OR changed_by NOT IN (1,2) OR voided_by NOT IN (1,2)")
        _run_sql(site, "UPDATE person_address SET creator=1, changed_by=1, voided_by=1 WHERE creator NOT IN (1,2) OR changed_by NOT IN (1,2) OR voided_by NOT IN (1,2)")
        _run_sql(site, "UPDATE obs SET creator=1, voided_by=1 WHERE creator NOT IN (1,2) OR voided_by NOT IN (1,2)")
        _run_sql(site, "UPDATE idgen_log_entry SET generated_by=1 WHERE generated_by NOT IN (1,2);")
        _run_sql(site, "UPDATE htmlformentry_html_form SET creator=1, changed_by=1, retired_by=1 WHERE creator NOT IN (1,2) OR changed_by NOT IN (1,2) OR retired_by NOT IN (1,2)")
        _run_sql(site, "UPDATE encounter_provider SET provider_id=1 WHERE provider_id NOT IN (1,2);")
        _run_sql(site, "DELETE FROM notification_alert_recipient")
        _run_sql(site, "DELETE FROM notification_alert")
        _run_sql(site, "DELETE FROM provider WHERE provider_id <> 1")
        _run_sql(site, "DELETE FROM users WHERE user_id NOT IN (1,2)")
        import_cmd = ("docker exec -i $(docker ps | grep openmrs-sdk-mysql | cut -f1 -d' ') " +
                "mysql -uopenmrs --password=***REMOVED*** " + site + " <" + file_path)
        sp.check_output(import_cmd, shell=True)
        _run_sql(site, "INSERT INTO user_role (user_id, role) SELECT u.user_id, r.role FROM users u CROSS JOIN role r WHERE u.user_id NOT IN (1,2)")


def launch_browser(site):
    command = "firefox -new-tab http://localhost:" + str(port_for_site(site)) + "/openmrs"
    process = sp.Popen(command, shell=True, stdout=sp.DEVNULL, stderr=sp.PIPE)


def _get_selection(prompt, options):
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
            result = options[selection - 1]
            return result
        except (ValueError, IndexError) as e:
            print("Oups! Eso no es input valido. Intenta otra vez.")


def _run_in_docker(command):
    docker_cmd = "docker exec $(docker ps | grep openmrs-sdk-mysql | cut -f1 -d' ') " + command
    # print(docker_cmd)
    result = sp.check_output(docker_cmd, shell=True)
    # print(result)
    return result


def _run_sql(database, command):
    mysql_cmd = "mysql -uopenmrs --password=***REMOVED*** -e '" + command + "' " + database
    return _run_in_docker(mysql_cmd)


if __name__ == "__main__":
    main_loop()


