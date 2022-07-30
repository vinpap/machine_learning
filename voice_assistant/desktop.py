"""This file contains all the intent slots that are exclusively relevant in a
desktop version of this voice assistant. As such, it includes classes that offer
some basic functions available on a desktop environment such as
copying/cutting/deleting files and directories or running programs, among others."""


import logging
import subprocess
import psutil
import os
import pathlib
import random

from Levenshtein import distance as levenshtein_distance
import send2trash

from interfaces import IIntent_slot
from environment import Environment


common_files_explorers = ("nautilus",
                            "thunar",
                            "pcmanfm",
                            "konqueror",
                            "dolphin",
                            "krusader",
                            "nemo",
                            "caja",
                            "files")

################################################################################

# Below are some functions common to several intent slots

def get_longest_string(lst):
    """Takes a list of full paths, and returns the element from that list whose
    name is the longest (not taking into account the path)"""
    folders_list = []
    for i in lst:
        if i=="/": folders_list.append("/")
        else: folders_list.append(i.split("/")[-1])
    return max(folders_list, key=len) if folders_list else None

def simplify_string(str):
    """Removes all accents and letters such as ç, replacing them with the same
    letter without accents. Also  lemmatize all the  words in the string and
    set everything to lowercase"""

    str = str.replace("_", " ")
    str = str.lower()
    str = str.strip()
    nlp = Environment.get_instance().language_model
    doc = nlp(str)
    str = " ".join([token.lemma_ for token in doc])

    translation_table = {
                        "é" : "e",
                        "è" : "e",
                        "ê" : "e",
                        "ë" : "e",
                        "à" : "a",
                        "â" : "a",
                        "ä" : "a",
                        "î" : "i",
                        "ï" : "i",
                        "û" : "u",
                        "ù" : "u",
                        "ü" : "u",
                        "ô" : "o",
                        "ö" : "o",
                        "ç" : "c"
    }

    for c in translation_table:
        str = str.replace(c, translation_table[c])

    return str

def find_element(input, current_directory, check_folders=True, distance_threshold=1):

    """This is the function used by several intent slots to identify the
    target of the action in the input (such as the name of the file to open, the
    name of the directory that should be opened...) in the context of a directory.

    In order to identify the target element in current_directory, we go over
    each word in the string input and compare it to each element in the current
    folder by calculating their Levenshtein distance. The Levenshtein distance of
    two strings is the minimal number of changes to turn one into the other (in
    other words the smaller the distance, the more similar two strings are).

    This function creates a dictionary named 'candidates'. All potential matches,
    i.e. matches that yield a Levenshtein distance lower than or equal to
    distance_threshold, are added to that dictionary. Afterwards, the longest string
    among the candidates having the lowest distance is deemed to be the target.

    In the case where no target was identified that way (which necessarily happens
    when the target we are looking for is made up of several words), we look for
    an element in the current directory whose name is wholly contained in the input.

    distance_threshold is the maximum Levenshtein distance that two strings can
    have in order to be considered as potential matches. Setting it to 0 means
    that the target element's name must be identical to a word in the input.
    If check_folders is set to False, then the function will ignore all folders
    in current_directory and will only compare the input with the files."""


    candidates = {}
    doc = Environment.get_instance().language_model(input)

    dir_content = []
    for file in os.listdir(current_directory):
        if (not check_folders) and (os.path.isdir(os.path.join(current_directory, file))):
            continue # folders are ignored if check_folders is set to False
        dir_content.append(file)

    for word in doc:
        if word.text.find(".") != -1:
            for file in dir_content:
                d = levenshtein_distance(word.text.lower(), file.lower().replace("_", " "))
                if d <= distance_threshold: candidates[os.path.join(current_directory, file)] = d

    if candidates == {}:
        for word in doc:
            if word.text.find(".") != -1:
                word_without_extension = word.text.lower.split(".")[-2]
            else: word_without_extension = word.text.lower()
            for file in dir_content:
                if file.find(".") != -1:
                    file_without_extension = file.split(".")[-2]
                else: file_without_extension = file
                d = levenshtein_distance(word_without_extension, file_without_extension.lower().replace("_", " "))
                if d <= distance_threshold: candidates[os.path.join(current_directory, file)] = d

    chosen_candidate = None


    for distance in range(0, distance_threshold+1):
        best_candidates = []
        for c in candidates:
            if candidates[c] == distance: best_candidates.append(c)
        chosen_candidate = get_longest_string(best_candidates)
        if chosen_candidate:
            for i in candidates:
                if i.lower().endswith("/" + chosen_candidate.lower()):
                    chosen_candidate = i
                    return chosen_candidate

    if not chosen_candidate:
        # As a last resort, we try to find out if there is an element whose
        # name is wholly contained in the sentence
        for file in dir_content:
            processed_filename = file.split(".")[0]
            processed_filename = simplify_string(processed_filename)
            if processed_filename in simplify_string(input) and len(processed_filename) >= 4:
                chosen_candidate = os.path.join(current_directory, file)
                return chosen_candidate

    return False


def pick_random_sentence(options):
    """Randomly picks and returns a sentence among the options list. Enables to
    randomize a bit what the AI says"""
    return random.choice(options)


################################################################################


class Open_program(IIntent_slot):

    """The open_program intent runs a program mentioned by the user.
    It can be the name of the program itself, or a default program, e.g. 'text editor'
    or 'spreadsheet'. See the Environment class for a better understanting of how the
    information concerning the available programs on the machine are retrieved"""

    def __init__(self):
        self._environment = Environment.get_instance()
        self.intent_id = "open_program"
        logging.debug("Creating intent slot '" + self.intent_id + "'")

    def run(self, input):

        """If a default program matching the user's sentence is found, it is opened.
        If not, then we go through the list of all available programs on the system
        and look for one matching the sentence."""

        logging.debug("Running intent slot '" + self.intent_id + "' with input '" + input + "'")

        for a in self._environment.default_apps:
            if a.lower() in input.lower():
                logging.info("Running program " + a)
                logging.debug("Command: " + self._environment.default_apps[a])
                subprocess.Popen(self._environment.default_apps[a], shell=True)
                return ("", True)


        doc = self._environment.language_model(input)

        for a in self._environment.all_apps:
            for b in a: # Here we browse the different aliases for each app
                if b.lower() in input.lower():
                    alias = self._environment.language_model(b)
                    if len(alias) == 1:
                        for token in doc:
                            if alias[0].text.lower() == token.text.lower():
                                logging.info("Running program " + b)
                                logging.debug("Command: " + self._environment.all_apps[a])
                                subprocess.Popen(self._environment.all_apps[a], shell=True)
                                return ("", True)
                    else:
                        logging.info("Running program " + b)
                        logging.debug("Command: " + self._environment.all_apps[a])
                        subprocess.Popen(self._environment.all_apps[a], shell=True)
                        return ("", True)


        # If we didn't find any program to open, we check the current directory
        # to find out if a file or a folder matches the request

        if self._check_current_directory(input): return ("", True)
        else:
            logging.debug("Program not found")
            if self._environment.language == "en":
                potential_lines = ["Sorry , I don't understand what you want to open",
                                "I didn't get it, what application should I open?"]

            elif self._environment.language == "fr":
                potential_lines = ["Désolé, je ne comprends pas quelle application je dois ouvrir",
                                "Je ne trouve pas quelle application ouvrir."]
            msg = pick_random_sentence(potential_lines)
            return (msg, True)

    def _check_current_directory(self, input):

        """Looks for the action target in the current directory. This function is
        called if no program matching the user's request was found, as the intent
        slots for open_program and open_file are sometimes 'overlapping':
        open_program is sometimes called instead of open_file, even though the user
        actually wanted to open a file or folder in the current directory. This
        function allows us to handle that situation."""

        file_to_open = find_element(input, self._environment.working_dir, check_folders=True)
        if file_to_open:
            if os.path.isdir(file_to_open):
                for explorer in common_files_explorers:
                    for process in (process for process in psutil.process_iter() if process.name().lower() == explorer.lower()):
                        process.kill()
                        logging.info("killed process " + process.name().lower())
                self._environment.working_dir = file_to_open
                subprocess.Popen(["xdg-open", file_to_open])
                logging.info("Moving to directory " + file_to_open)
            else:
                logging.info("Opening file " + file_to_open)
                os.system(f"xdg-open '{file_to_open}'")

            return ("", True)
        else:
            return False




class Close_program(IIntent_slot):

    """The close_program intent closes a program explicitely mentioned by the user
    that is currently opened. Please note that unlike other intents such as
    open_program, this intent doesn't recognize default application designations
    such as "text editor" or "navigator". Therefore the user must explicitely
    give the name of the process he wants to close. There will probably be
    attempts at changing this in future updates."""

    def __init__(self):
        self.intent_id = "close_program"
        self._env = Environment.get_instance()
        logging.debug("Creating intent slot '" + self.intent_id + "'")

    def run(self, input):

        msg = ""
        found_process = False
        logging.debug("Running intent slot '" + self.intent_id + "' with input '" + input + "'")
        # Currently, the user has to explicitely spell out the name of the program he
        # wishes to close. This might change in a later update.
        for process in (process for process in psutil.process_iter() if process.name().lower() in input.lower()):
            process.kill()
            logging.info("killed process " + process.name().lower())
            found_process = True

        if not found_process:
            if self._environment.language == "en":
                potential_lines = ["Sorry , I didn't find this process",
                                "I couldn't find that process"]
            elif self._environment.language == "fr":
                potential_lines = ["Désolé, je n'ai pas pu trouver ce processus",
                                "Je ne comprends pas, quel processus je dois fermer ?"]
            msg = pick_random_sentence(potential_lines)
        return (msg, True)




class New_working_dir(IIntent_slot):

    """This class allows the user to change the current working directory. All
    subsequent operations such as copying, cutting etc will be performed on the
    elements in this directory.
    Moreover, moving to a new directory causes the files manager to open a window
    in that directory. Only one window at max can be opened by the voice assistant:
    moving to a new directory will close any window previously opened by the assistant
    and open a single window in the new directory."""

    def __init__(self):
        self._environment = Environment.get_instance()
        self.intent_id = "new_working_dir"
        logging.debug("Creating intent slot '" + self.intent_id + "'")
        self._lang = self._environment.language

        self._nlp = self._environment.language_model

        # By default, this intent slot already knows of some very common locations
        # such as the root folder, the home folder, etc...
        self._home = str(pathlib.Path.home())
        self._common_folders_en = {"root": "/",
                        "root folder": "/",
                        "home": self._home,
                        "personal directory": self._home,
                        "home directory": self._home,
                        "personal folder": self._home,
                        "my folder": self._home}

        self._common_folders_fr = {"root": "/",
                        "dossier root": "/",
                        "dossier racine": "/",
                        "home": self._home,
                        "dossier personnel": self._home,
                        "dossier home": self._home,
                        "répertoire personnel": self._home,
                        "mon dossier personnel": self._home}

    def run(self, input):


        logging.debug("Running intent slot '" + self.intent_id + "' with input '" + input + "'")
        return self._find_folder(input.replace("_", " "))

    def _change_working_directory(self, new_dir):

        """This is executed in three times:
        - killing the files manager processes. This is based on a list of common
        files explorers on Linux (defined at the top of that file), which means
        that rare or "exotic" files managers won't be found in the process list.
        In that situation, if will fall to the user to close himself the windows
        he doesn't need anymore.
        - changing the working directory in the Environment object
        - opening a window in the new directory."""

        for explorer in common_files_explorers:
            for process in (process for process in psutil.process_iter() if process.name().lower() == explorer.lower()):
                process.kill()
                logging.info("killed process " + process.name().lower())
        self._environment.working_dir = new_dir
        subprocess.Popen(["xdg-open", new_dir])
        logging.info("Moving to directory " + new_dir)


    def _find_folder(self, input):

        """Works kinda like the find_element function, but only on folders.
        Furthermore, if no matching folder is find in the current directory,
        this function will look for a match among the common locations (home, root,
        etc..) defined in __init__."""

        current_dir = self._environment.working_dir
        current_subfolders = []
        user_folders = []
        candidates = {}
        doc = self._nlp(input)
        distance_threshold = 1


        for file in os.listdir(current_dir):
            d = os.path.join(current_dir, file)
            if os.path.isdir(d):
                current_subfolders.append(d)

        user_folders.append(self._home)
        for file in os.listdir(self._home):
            d = os.path.join(self._home, file)
            if os.path.isdir(d):
                user_folders.append(d)

        for word in doc:
            for f in current_subfolders:
                folder_name = f.split("/")[-1]
                d = levenshtein_distance(word.text, folder_name.lower().replace("_", " "))
                if d <= distance_threshold: candidates[f] = d

        if candidates == {}:
            for word in doc:
                for f in user_folders:
                    folder_name = f.split("/")[-1]
                    d = levenshtein_distance(word.text, folder_name.lower().replace("_", " "))
                    if d <= distance_threshold: candidates[f] = d

        if candidates != {}:

            chosen_candidate = None

            for distance in range(0, distance_threshold+1):
                best_candidates = []
                for c in candidates:
                    if candidates[c] == distance: best_candidates.append(c)
                chosen_candidate = get_longest_string(best_candidates)
                if chosen_candidate:
                    for i in candidates:
                        if i.lower().endswith("/" + chosen_candidate.lower()):
                            new_directory = i
                    self._change_working_directory(new_directory)
                    return ("", True)


        if candidates == {}:
            if self._environment.language == "en":
                for f in self._common_folders_en:
                    if f.lower() in input.lower():
                        folder = self._common_folders_en[f]
                        self._change_working_directory(folder)
                        return ("", True)

            elif self._environment.language == "fr":
                for f in self._common_folders_fr:
                    if f.lower() in input.lower():
                        folder = self._common_folders_fr[f]
                        self._change_working_directory(folder)
                        return ("", True)

        if candidates == {}:
            # As a last resort, we try to find out if there is an element whose
            # name is wholly contained in the sentence
            for file in os.listdir(current_dir):
                if simplify_string(file) in simplify_string(input) and len(file) >= 4:
                    chosen_candidate = os.path.join(current_dir, file)
                    self._change_working_directory(chosen_candidate)
                    return ("", True)

        if candidates == {}:
            if self._environment.language == "en":
                potential_lines = ["Sorry , I didn't find this folder",
                                "I couldn't find that folder",
                                "I didn't understand what folder you're'looking for"]
            elif self._environment.language == "fr":
                potential_lines = ["Désolé, je n'ai pas trouvé ce dossier",
                                "Je ne comprends pas quel dossier vous cherchez, désolé !",
                                "Je n'ai pas réussi à trouver ce dossier, j'ai dû mal comprendre"]
            msg = pick_random_sentence(potential_lines)
            return (msg, True)



class Copy(IIntent_slot):

    """That intent copies a file or a folder located in the current directory to the
    clipboard.
    IMPORTANT: the clipboard used by this assistant and the one used by your files
    manager are not the same. Thus you can't copy a file to the clipboard from the
    assistant and paste it on your files explorer, for example"""

    def __init__(self):
        self._environment = Environment.get_instance()
        self.intent_id = "copy"
        logging.debug("Creating intent slot '" + self.intent_id + "'")
        self._lang = self._environment.language

        self._nlp = self._environment.language_model

    def run(self, input):

        logging.debug("Running intent slot '" + self.intent_id + "' with input '" + input + "'")
        return self._find_element(input.replace("_", " "))

    def _find_element(self, input):

        element_to_copy = find_element(input, self._environment.working_dir)
        if element_to_copy:
            self._environment.clear_clipboard()
            self._environment.clipboard[element_to_copy] = False
            logging.info("Copying " + element_to_copy)
            return ("", True)
        else:
            if self._environment.language == "en":
                potential_lines = ["Sorry , I didn't find this element",
                                "I don't understand what I should copy",
                                "I didn' understand what you want to copy, sorry"]
            elif self._environment.language == "fr":
                potential_lines = ["Désolé, je n'ai pas compris quoi copier",
                                "Je ne comprends pas ce que vous voulez copier, désolé !",
                                "J'ai mal compris ce que je dois copier, vous pouvez répéter ?"]
            msg = pick_random_sentence(potential_lines)
            return (msg, True)


class Copy_all(IIntent_slot):

    """That intent copies all elements located in the current directory to the
    clipboard.
    IMPORTANT: the clipboard used by this assistant and the one used by your files
    manager are not the same. Thus you can't copy a file to the clipboard from the
    assistant and paste it on your files explorer, for example"""

    def __init__(self):
        self._environment = Environment.get_instance()
        self.intent_id = "copy_all"
        logging.debug("Creating intent slot '" + self.intent_id + "'")
        self._lang = self._environment.language


    def run(self, input):

        logging.debug("Running intent slot '" + self.intent_id + "' with input '" + input + "'")
        current_elements = []

        for i in os.listdir(self._environment.working_dir):
            current_elements.append(os.path.join(self._environment.working_dir, i))

        if current_elements == []:
            if self._environment.language == "en":
                potential_lines = ["Sorry, this folder is empty",
                                "There is nothing to copy here"]

            elif self._environment.language == "fr":
                potential_lines = ["Désolé, ce dossier est vide",
                                "Il n'y a rien à copier ici"]

            else: raise ValueError("Wrong language code")
            msg = pick_random_sentence(potential_lines)
            return (msg, True)


        self._environment.clear_clipboard()
        for j in current_elements:
            self._environment.clipboard[j] = False

        return ("", True)


class Cut(IIntent_slot):

    """That intent CUTS a file or a folder located in the current directory to the
    clipboard.
    IMPORTANT: the clipboard used by this assistant and the one used by your files
    manager are not the same. Thus you can't copy a file to the clipboard from the
    assistant and paste it on your files explorer, for example"""

    def __init__(self):
        self._environment = Environment.get_instance()
        self.intent_id = "cut"
        logging.debug("Creating intent slot '" + self.intent_id + "'")
        self._lang = self._environment.language

        self._nlp = self._environment.language_model

    def run(self, input):

        logging.debug("Running intent slot '" + self.intent_id + "' with input '" + input + "'")
        return self._find_element(input.replace("_", " "))

    def _find_element(self, input):

        element_to_cut = find_element(input, self._environment.working_dir)
        if element_to_cut:
            self._environment.clear_clipboard()
            self._environment.clipboard[element_to_cut] = True
            logging.info("Cutting " + element_to_cut)
            return ("", True)
        else:
            if self._environment.language == "en":
                potential_lines = ["Sorry, I didn't get it. Can you tell me again the element you want to cut?",
                                "Sorry, could you repeat the name of the element you want to cut?"]

            elif self._environment.language == "fr":
                potential_lines = ["Désolé, j'ai mal compris. Pouvez-vous répéter le nom de l'élément à couper ?",
                                "Je n'ai pas bien compris. Pourriez-vous répéter le nom de l'élément que je dois couper ?"]

            else: raise ValueError("Wrong language code")
            msg = pick_random_sentence(potential_lines)
            return (msg, False)



class Cut_all(IIntent_slot):

    """That intent CUTS all elements located in the current directory to the
    clipboard.
    IMPORTANT: the clipboard used by this assistant and the one used by your files
    manager are not the same. Thus you can't copy a file to the clipboard from the
    assistant and paste it on your files explorer, for example"""

    def __init__(self):
        self._environment = Environment.get_instance()
        self.intent_id = "cut_all"
        logging.debug("Creating intent slot '" + self.intent_id + "'")
        self._lang = self._environment.language


    def run(self, input):

        logging.debug("Running intent slot '" + self.intent_id + "' with input '" + input + "'")
        current_elements = []
        for i in os.listdir(self._environment.working_dir):
            current_elements.append(os.path.join(self._environment.working_dir, i))

        if current_elements == []:
            if self._environment.language == "en":
                potential_lines = ["Sorry, this folder is empty",
                                "There is nothing to cut here"]

            elif self._environment.language == "fr":
                potential_lines = ["Désolé, ce dossier est vide",
                                "Il n'y a rien à couper ici"]

            else: raise ValueError("Wrong language code")
            msg = pick_random_sentence(potential_lines)
            return (msg, True)

        self._environment.clear_clipboard()
        for j in current_elements:
            self._environment.clipboard[j] = True
        logging.info("Cutting all elements in " + self._environment.working_dir)

        return ("", True)


class Paste(IIntent_slot):

    """That intent pastes the content of the clipboard in the current directory.
    IMPORTANT: the clipboard used by this assistant and the one used by your files
    manager are not the same. Thus you can't copy a file to the clipboard from the
    assistant and paste it on your files explorer, for example"""

    def __init__(self):
        self._environment = Environment.get_instance()
        self.intent_id = "paste"
        logging.debug("Creating intent slot '" + self.intent_id + "'")

    def run(self, input):

        logging.debug("Running intent slot '" + self.intent_id + "' with input '" + input + "'")
        for f in self._environment.clipboard:
            if self._environment.clipboard[f] == True: #e.g. if the file must be cut
                cmd = f"mv '{f}' '{self._environment.working_dir}'"
            else: # copy-only
                cmd = f"cp -r '{f}' '{self._environment.working_dir}/'"
            os.system(cmd)
        logging.info("Pasting clipboard's content in " + self._environment.working_dir)

        self._environment.clear_clipboard()
        return ("", True)



class Trash(IIntent_slot):

    """That intent sends a file or folder in the current directory to the trash can"""

    def __init__(self):
        self._environment = Environment.get_instance()
        self.intent_id = "trash"
        logging.debug("Creating intent slot '" + self.intent_id + "'")
        self._lang = self._environment.language

        self._nlp = self._environment.language_model

    def run(self, input):

        logging.debug("Running intent slot '" + self.intent_id + "' with input '" + input + "'")
        return self._find_element(input.replace("_", " "))

    def _find_element(self, input):

        element_to_delete = find_element(input, self._environment.working_dir)
        if element_to_delete:
            send2trash.send2trash(element_to_delete)
            logging.info("Sending to trash " + element_to_delete)
            return ("", True)

        else:
            if self._environment.language == "en":
                potential_lines = ["Sorry, I didn' understand well. What is the name of the element to delete?",
                                "Could you repeat the name of the element to delete?"]

            elif self._environment.language == "fr":
                potential_lines = ["Désolé, Je n'ai pas bien compris. Quel est le nom de l'élément à supprimer ?",
                                "Pouvez-vous répéter le nom de l'élément à supprimer ?"]

            else: raise ValueError("Wrong language code")
            msg = pick_random_sentence(potential_lines)
            return (msg, False)


class Trash_all(IIntent_slot):

    """That intent copies sends all the elements in the current directory to the
    trash can."""

    def __init__(self):
        self._environment = Environment.get_instance()
        self.intent_id = "trash_all"
        logging.debug("Creating intent slot '" + self.intent_id + "'")
        self._lang = self._environment.language


    def run(self, input):

        logging.debug("Running intent slot '" + self.intent_id + "' with input '" + input + "'")
        current_elements = []

        for i in os.listdir(self._environment.working_dir):
            current_elements.append(os.path.join(self._environment.working_dir, i))

        if current_elements == []:
            if self._environment.language == "en":
                potential_lines = ["Sorry, this folder is already empty",
                                "There is nothing to delete here"]

            elif self._environment.language == "fr":
                potential_lines = ["Ce dossier est déjà vide",
                                "Il n'y a rien à supprimer ici"]

            else: raise ValueError("Wrong language code")
            msg = pick_random_sentence(potential_lines)
            return (msg, True)

        for j in current_elements:
            send2trash.send2trash(j)

        logging.info("Sending to trash can all content in " + self._environment.working_dir)

        return ("", True)




class Rename(IIntent_slot):

    """That intent renames a file or folder in the current directory."""

    def __init__(self):
        self._environment = Environment.get_instance()
        self.intent_id = "rename"
        logging.debug("Creating intent slot '" + self.intent_id + "'")
        self._lang = self._environment.language
        self._element_to_rename = ""

        self._nlp = self._environment.language_model


    def run(self, input):

        logging.debug("Running intent slot '" + self.intent_id + "' with input '" + input + "'")
        if self.task_is_ongoing and self._element_to_rename != "":
            new_path = os.path.join(self._environment.working_dir, input)
            cmd = "mv '" + self._element_to_rename + "' '" + new_path + "'"
            os.system(cmd)
            self.task_is_ongoing = False
            return ("", True)

        return self._find_element(input.replace("_", " "))

    def _find_element(self, input):

        element_to_rename = find_element(input, self._environment.working_dir)
        if element_to_rename:
            self._element_to_rename = element_to_rename
            element_name = element_to_rename.split("/")[-1]
            self.task_is_ongoing = True
            logging.info("Renaming " + element_name)
            if self._lang == "en": return (f"How do you want to rename {element_name}?", False)
            elif self._lang == "fr": return (f"Comment voulez-vous renommer {element_name} ?", False)
            else: raise ValueError("Unvalid language code")

        else:
            if self._environment.language == "en":
                potential_lines = ["Sorry, I didn' understand well. What is the name of the element to rename?",
                                "Could you repeat the name of the element you want to rename?"]

            elif self._environment.language == "fr":
                potential_lines = ["Désolé, Je n'ai pas bien compris. Quel est le nom de l'élément à renommer ?",
                                "Pourriez-vous répéter le nom de l'élément à renommer, s'il vous plaît ?"]

            else: raise ValueError("Wrong language code")
            msg = pick_random_sentence(potential_lines)
            return (msg, False)


class Open_file(IIntent_slot):

    """That intent opens a file in the current directory using its default application."""

    def __init__(self):
        self._environment = Environment.get_instance()
        self.intent_id = "open_file"
        logging.debug("Creating intent slot '" + self.intent_id + "'")
        self._lang = self._environment.language

        self._nlp = self._environment.language_model

    def run(self, input):

        logging.debug("Running intent slot '" + self.intent_id + "' with input '" + input + "'")
        return self._find_element(input.replace("_", " "))

    def _find_element(self, input):

        file_to_open = find_element(input, self._environment.working_dir, check_folders=False)
        if file_to_open:
            logging.info("Opening " + file_to_open)
            os.system(f"xdg-open '{file_to_open}'")
            return ("", True)

        else:
            if self._environment.language == "en":
                potential_lines = ["Sorry, I didn' understand well. What do you want to open?",
                                "Could you repeat the name of the element I should open?"]

            elif self._environment.language == "fr":
                potential_lines = ["Désolé, Je n'ai pas bien compris. Que voulez-vous ouvrir ?",
                                "Pouvez-vous répéter le nom de l'élément à ouvrir ?"]

            else: raise ValueError("Wrong language code")
            msg = pick_random_sentence(potential_lines)
            return (msg, False)



class Previous(IIntent_slot):

    """Goes back to the last directory visited by the user.
    Please note: this does not behave like a history such as the one you have in
    a web browser or a files manager. Going back to the previous directory also
    add it at the end of the history as the last visited folder, meaning that
    repeatedly going back would only take you back and forth between two directories.
    Might be changed in a future update"""

    def __init__(self):
        self._environment = Environment.get_instance()
        self.intent_id = "previous"
        logging.debug("Creating intent slot '" + self.intent_id + "'")


    def run(self, input):

        logging.debug("Running intent slot '" + self.intent_id + "' with input '" + input + "'")
        if len(self._environment.history) != 1:
            new_dir = self._environment.history[-2]
            for explorer in common_files_explorers:
                for process in (process for process in psutil.process_iter() if process.name().lower() == explorer.lower()):
                    process.kill()
                    logging.info("killed process " + process.name().lower())
                    self._environment.working_dir = new_dir
                    subprocess.Popen(["xdg-open", new_dir])
                    logging.info("Moving to directory " + new_dir)

        return ("", True)


class Go_to_parent_dir(IIntent_slot):

    """Goes to the parent of the current directory"""

    def __init__(self):
        self._environment = Environment.get_instance()
        self.intent_id = "go_to_parent_dir"
        logging.debug("Creating intent slot '" + self.intent_id + "'")


    def run(self, input):

        logging.debug("Running intent slot '" + self.intent_id + "' with input '" + input + "'")
        if self._environment.working_dir == "/":
            if self._environment.language == "en":
                potential_lines = ["This is already the root folder",
                                "You are already at the root directory"]

            elif self._environment.language == "fr":
                potential_lines = ["Vous êtes déjà dans le dossier racine",
                                "Vous êtes dans le répertoire root, impossible d'aller plus haut"]

            else: raise ValueError("Wrong language code")
            msg = pick_random_sentence(potential_lines)
            return (msg, True)

        new_folder = os.path.dirname(self._environment.working_dir)
        self._environment.working_dir = new_folder
        for explorer in common_files_explorers:
            for process in (process for process in psutil.process_iter() if process.name().lower() == explorer.lower()):
                process.kill()
                logging.info("killed process " + process.name().lower())
        subprocess.Popen(["xdg-open", new_folder])
        logging.info("Moving to directory " + new_folder)

        return ("", True)
