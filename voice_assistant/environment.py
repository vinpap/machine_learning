import os
import logging
import configparser

import spacy
import platformdirs

"""This is a singleton used by all elements in the program. As its name implies,
it stores and keeps track of data related to the current working directory,
the applications available on the system, the clipboard, the history, as well
as the Spacy language model to use. It also retrieves and stores the settings
saved in settings.ini"""



# This is a list of aliases we use in order for the assistant to associate default
# applications with specific MIME types. You can get more information on MIME mime types
# here: https://wiki.debian.org/MIME
mime_types_en = { "spreadsheet": "application/excel",
    "text editor": "application/rtf",
    "drawing software": "application/vnd.sun.xml.draw",
    "drawing program": "application/vnd.sun.xml.draw",
    "math software": "application/mathml+xml",
    "math program": "application/mathml+xml",
    "presentation software": "application/mspowerpoint",
    "presentation program": "application/mspowerpoint",
    "media player": "video/mp4",
    "music player": "audio/x-mp3",
    "mp3 player": "audio/x-mp3",
    "music editor": "application/x-audacity-project",
    "video player": "video/mp4",
    "code editor": "application/javascript",
    "compression tool": "application/x-compress",
    "compression program": "application/x-compress",
    "compression software": "application/x-compress",
    "zip program": "application/x-zip-compressed",
    "zip tool": "application/x-zip-compressed",
    "zip software": "application/x-zip-compressed",
    "CD burning app": "x-content/blank-cd",
    "CD burning software": "x-content/blank-cd",
    "CD burning program": "x-content/blank-cd",
    "PDF viewer": "application/pdf",
    "image editor": "image/x-xcf",
    "image editing program": "image/x-xcf",
    "image editing software": "image/x-xcf",
    "image editing tool": "image/x-xcf",
    "image viewer": "image/jpg",
    "image visualizer": "image/jpg",
    "web browser": "x-scheme-handler/http",
    "internet browser": "x-scheme-handler/http",
    "internet navigator": "x-scheme-handler/http",
    "navigator": "x-scheme-handler/http",
    "email client": "x-scheme-handler/mailto",
    "email program": "x-scheme-handler/mailto",
    "email tool": "x-scheme-handler/mailto",
    "email software": "x-scheme-handler/mailto",
    "email program": "x-scheme-handler/mailto",
    "torrent client": "x-scheme-handler/magnet",
    "torrent program": "x-scheme-handler/magnet",
    "torrent software": "x-scheme-handler/magnet",
    "torrent tool": "x-scheme-handler/magnet"
}


#MIME types in French
mime_types_fr = { "tableur": "application/excel",
    "éditeur de texte": "application/rtf",
    "traitement de texte": "application/rtf",
    "logiciel de dessin": "application/vnd.sun.xml.draw",
    "programme de dessin": "application/vnd.sun.xml.draw",
    "logiciel de maths": "application/mathml+xml",
    "programme de maths": "application/mathml+xml",
    "logiciel de mathématiques": "application/mathml+xml",
    "programme de mathématiques": "application/mathml+xml",
    "logiciel de présentation": "application/mspowerpoint",
    "programme de présentation": "application/mspowerpoint",
    "logiciel de diapositives": "application/mspowerpoint",
    "programme de diapositives": "application/mspowerpoint",
    "lecteur média": "video/mp4",
    "lecteur multimédia": "video/mp4",
    "lecteur audio": "audio/x-mp3",
    "lecteur de musique": "audio/x-mp3",
    "lecteur mp3": "audio/x-mp3",
    "éditeur audio": "application/x-audacity-project",
    "éditeur de musique": "application/x-audacity-project",
    "traitement de son": "application/x-audacity-project",
    "lecteur vidéo": "video/mp4",
    "lecteur de vidéos": "video/mp4",
    "lecteur de films": "video/mp4",
    "éditeur de code": "application/javascript",
    "IDE": "application/javascript",
    "outil de compression": "application/x-compress",
    "programme de compression": "application/x-compress",
    "logiciel de compression": "application/x-compress",
    "programme zip": "application/x-zip-compressed",
    "outil zip": "application/x-zip-compressed",
    "logiciel zip": "application/x-zip-compressed",
    "application de gravure de CD": "x-content/blank-cd",
    "graveur CD": "x-content/blank-cd",
    "graveur de CD": "x-content/blank-cd",
    "graveur de disque": "x-content/blank-cd",
    "visionneur de PDF": "application/pdf",
    "lecteur PDF": "application/pdf",
    "éditeur d'image": "image/x-xcf",
    "programme d'édition d'image": "image/x-xcf",
    "logiciel d'édition d'image": "image/x-xcf",
    "outil d'édition d'image": "image/x-xcf",
    "visionneur d'image": "image/jpg",
    "navigateur web": "x-scheme-handler/http",
    "navigateur internet": "x-scheme-handler/http",
    "navigateur": "x-scheme-handler/http",
    "client e-mail": "x-scheme-handler/mailto",
    "programme d'e-mail": "x-scheme-handler/mailto",
    "lecteur d'e-mail": "x-scheme-handler/mailto",
    "client torrent": "x-scheme-handler/magnet",
    "programme torrent": "x-scheme-handler/magnet",
    "logiciel torrent": "x-scheme-handler/magnet",
    "outil torrent": "x-scheme-handler/magnet"

}

# Some extra common programs, not covered in the MIME types
common_programs = { "terminal": "x-terminal-emulator",
    "shell": "x-terminal-emulator"

}

class Environment:

    """SINGLETON!"""

    __instance = None

    __working_dir = None
    __default_apps = None
    __all_apps = None
    __config = None
    __language_model = None

    # This clipboard can only contain files and folders (no text)
    clipboard = {}
    # This list stores the last directories visited
    history = []



    def clear_clipboard(self): Environment.clipboard = {}

    @property
    def working_dir(self): return Environment.__working_dir
    @working_dir.setter
    def working_dir(self, new_directory):
        if Environment.__working_dir == new_directory: return
        else:
            Environment.__working_dir = new_directory
            Environment.history.append(new_directory)

    @property
    def default_apps(self): return Environment.__default_apps
    @default_apps.setter
    def default_apps(self, new_value): raise Exception("You cannot change the environment's application lists from outside the class!")

    @property
    def all_apps(self): return Environment.__all_apps
    @all_apps.setter
    def all_apps(self, new_value): raise Exception("You cannot change the environment's application lists from outside the class!")

    @property
    def language(self): return Environment.__config['DEFAULT']["language"]
    @language.setter
    def language(self, new_value): raise Exception("You cannot change the environment's language attribute from outside the class!")

    @property
    def language_model(self): return Environment.__language_model
    @language_model.setter
    def language_model(self, new_value): raise Exception("You cannot change the environment's language model from outside the class!")

    @property
    def config(self): return Environment.__config
    @config.setter
    def config(self, new_value): raise Exception("You cannot change the environment's config data from outside the class!")

    @staticmethod
    def get_instance():
        """ Static access method. """
        if Environment.__instance == None:
            Environment()
        return Environment.__instance

    def __init__(self):

        logging.debug("Creating environment object")
        if Environment.__instance != None:
            raise Exception("This class is a singleton! Use Environment.get_instance() to instantiate it")
        else:
            Environment.__instance = self
            Environment.__load_config()
            logging.info("Base working directory: " + Environment.__working_dir)
            Environment.history.append(Environment.__working_dir)

            Environment.__get_default_apps()
            log_msg = "Built list of default apps:\n"
            for a in Environment.__default_apps:
                log_msg = log_msg + a + " - " + Environment.__default_apps[a] + "\n"
            logging.debug(log_msg)

            Environment.__get_all_aps()
            log_msg = "Built list of all apps:\n"
            for a in Environment.__all_apps:
                log_msg = log_msg + str(a) + " - " + Environment.__all_apps[a] + "\n"
            logging.debug(log_msg)


    def __get_default_apps():

        """In order to get the full list of available apps on Linux, we check the
        files defaults.list and mimeinfo.cache, both located in /usr/share/applications."""


        Environment.__default_apps = {}
        with open("/usr/share/applications/defaults.list") as defaults_list:
            lines = defaults_list.readlines()
            Environment.__parse_mime_file(lines)

        with open("/usr/share/applications/mimeinfo.cache") as defaults_list:
            lines = defaults_list.readlines()
            Environment.__parse_mime_file(lines)

        for p in common_programs:
            Environment.__default_apps[p] = common_programs[p]

    def __parse_mime_file(mime_content):

        """MIME files have a specific structure that includes the application name
        as well as some aliases, comments and - obviously - the command associated
        with the application. That's what we retrieve here"""

        if Environment.__config['DEFAULT']['language'] == "en": mime_types = mime_types_en
        elif Environment.__config['DEFAULT']['language'] == "fr": mime_types = mime_types_fr
        else: raise ValueError("Unknown language code")
        for l in mime_content:
            for a in mime_types:
                if l.find(mime_types[a]) != -1:
                    substrings = l.split("=")
                    desktop_file = substrings[-1].rstrip("\n\r;")

                    try:
                        with open("/usr/share/applications/" + desktop_file) as file:
                            desktop_lines = file.readlines()
                            command = ""
                            for m in desktop_lines:
                                if m.startswith("Exec="):
                                    command = m.removeprefix("Exec=")
                                    command = command.rstrip("\n\r;")
                                    command = command.removesuffix(" %U")
                                    command = command.removesuffix(" %u")
                                    command = command.removesuffix(" %F")
                                    command = command.removesuffix(" %f")
                                    command = command.removesuffix(" %U")
                                    command = command.removesuffix(" %u")

                                    break

                            if command:
                                Environment.__default_apps[a] = command

                    except FileNotFoundError: continue


    def __get_all_aps():

        """In order to get the full list of applications, we read all the
        .desktop files located in the /usr/share/applications folder.
        Unlike the default applications, which are stored in a dictionary whose
        keys are generic default program names such as "text editor", "media
        player", etc... here we store all applications under multiple names, as
        an application can define several alternative names in its MIME file."""

        Environment.__all_apps = {}
        path = "/usr/share/applications/"
        files_list = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
        for f in files_list:
            if f.endswith(".desktop"):
                with open(os.path.join(path, f)) as file:
                    desktop_lines = file.readlines()
                    app_name = ""
                    app_aliases = []
                    command = ""
                    for l in desktop_lines:

                        if Environment.__config['DEFAULT']['language'] == "fr" and l.startswith("Name[fr]="):
                            app_name = l.removeprefix("Name[fr]=")
                            app_name = app_name.strip("\n\r;")
                            app_aliases.append(app_name)
                        if Environment.__config['DEFAULT']['language'] == "fr" and l.startswith("GenericName[fr]="):
                            app_name = l.removeprefix("GenericName[fr]=")
                            app_name = app_name.strip("\n\r;")
                            app_aliases.append(app_name)

                        if l.startswith("Name="):
                            app_name = l.removeprefix("Name=")
                            app_name = app_name.strip("\n\r;")
                            app_aliases.append(app_name)
                        if l.startswith("GenericName="):
                            app_name = l.removeprefix("GenericName=")
                            app_name = app_name.strip("\n\r;")
                            app_aliases.append(app_name)

                        if l.startswith("Exec=") and command == "":
                            command = l.removeprefix("Exec=")
                            command = command.rstrip("\n\r;")
                            command = command.removesuffix(" %U")
                            command = command.removesuffix(" %u")
                            command = command.removesuffix(" %F")
                            command = command.removesuffix(" %f")
                            command = command.removesuffix(" %U")
                            command = command.removesuffix(" %u")


                    if command and app_name:
                        Environment.__all_apps[tuple(app_aliases)] = command

    def __load_config():

        """Loads the configuration data from the settings file.
        Just a quick note: Spacy language models are VERY memory-heavy. That's
        why we load them here so that they're created only once, and accessed
        through the language_model decorator when needed.
        NOTE: in the long run, settings.ini will be moved to the default config
        folder for the OS. For now it is kept in the project's folder for
        conveniency's sake"""

        Environment.__config = configparser.ConfigParser()
        Environment.__config.read("settings.ini")
        Environment.__working_dir = Environment.__config['DEFAULT']['default_directory']

        if Environment.__config['DEFAULT']["language"] == "en":
            Environment.__language_model = spacy.load("en_core_web_md")
        elif Environment.__config['DEFAULT']["language"] == "fr":
            Environment.__language_model = spacy.load("fr_core_news_md")
        else: raise ValueError("Language code not recognized")
