# -*- coding: utf-8 -*-
"""
Date de création: Wed Aug  4 08:42:54 2021
Auteur: antonietti

"""
import os

import math

import numpy as np
import pandas as pd

import unicodedata


def remove_accents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])


def find_directories(root_dir):
    """Recherche l'ensemble des répertoire à partir de la racine root_dir

    Parameters
    root_dir: répertoire racine pour la recherche
    
    Returns:
    n_cycle: liste avec les numéroas de cycles (a priori, [1, 2, 3, ...])
    MGI: liste des valeurs des MGI pour chaque cycle
    MGM: liste des valeurs des MGM pour chaque cycle
    MGS: liste des valeurs des MGS pour chaque cycle
    M05: liste des valeurs des M05 pour chaque cycle
    sucess: bolean indiquant si le VB c'est passé correctement (critère très basique sur le nombre de cycles)
    
    Remarque:
    La procédure reste mécanique et donc sujette à des erreurs en cas de fichier tronqué
    """
    directories = os.walk(root_dir)
    return [directory[0] for directory in directories]

def pidoux_parser(x, mesure_bride, mesure_cycle):
    """Analyse d'une ligne du fichier Pidoux
    
    Parameters:
    x: ligne du fichier (chaîne de caractères)
    
    Returns:
    Information sur la ligne
    """
    
    value = dict()
    
    if "mesure bride glissante" in x:
        mesure_bride = True
        mesure_cycle = False

    elif "vieillissement Bride cycle : " in x:
        value["Cycle="] = int(x.split("vieillissement Bride cycle : ")[1].split('"\n')[0])
        mesure_cycle = True
        mesure_bride = False

    elif "Energie restituée=" in x:
        value["Energie restituee="] = float(x.split("Energie restituée=")[1].split("[J]")[0])

    elif "Rendement=" in x:
        value["Rendement="] = float(x.split("Rendement=")[1].split("[%]")[0])

    elif "M48h" in x:
        tags = ["M0.5=", "M50%=", "M24h=", "M48h="]
        unit = "[mNm]"
        x_splits = x.split(unit)[:-1]
        value = dict()
        
        for tag, x_split in zip(tags, x_splits):
            xs = x_split.split(tag)
            value[tag] = float(xs[1])

    elif "Perte" in x:
        tags = ["PerteM50%=", "PerteM24h="]
        unit = "[%]"
        x_splits = x.split(unit)[:-1]
        value = dict()
        
        for tag, x_split in zip(tags, x_splits):
            xs = x_split.split(tag)
            value[tag] = float(xs[1])
    
    elif "Pas de données" in x:
        value["MGI="] = np.nan
        value["MGM="] = np.nan
        value["MGS="] = np.nan
                
    elif "MGS" in x:
        tags = ["MGI:", "MGM:", "MGS:"]
        unit = " "
        x_splits = x.split('"')[1].split(unit)
        value = dict()
        
        for tag, x_split in zip(tags, x_splits):
            xs = x_split.split(tag)
            value[tag.replace(":", "=")] = float(xs[1])

    elif "M0.5=" in x:
        value["M05="] = float(x.split("M0.5=")[1].split("[mNm]")[0])
            
    else:
        value = dict()
        
    return value, mesure_bride, mesure_cycle

def import_BRT(filename):
    """Extraction des valeurs des fichiers Pidoux de vieilliseemnt bride
    
    Parameters:
    filename: nom du fichier (p.ex. "00000026.TXT")
    basic_detector: 
    
    Returns:
    df_vieillissement: numéro du cycle et valuers des moments (1 ligne par cycle)
    df_avant_apres: valeurs mesurées avant et après vieillissement
    
    Remarque:
    La procédure reste mécanique et donc sujette à des erreurs en cas de fichier tronqué
    """
    VERBOSE = False # Déboggage
    
    df_vieillissement = pd.DataFrame(columns=["Cycle", "MGI", "MGM", "MGS", "M05"])
    df_avant_apres = pd.DataFrame(columns=["Etat", "Energie [J]", "Rendement [%]", "MGI", "MGM", "MGS", 
                                           "M05", "M50%", "M24h", "M48h", 
                                           "PerteM50% [%]", "PerteM24h [%]"])
    
    mesure_bride = False
    mesure_cycle = False
    
    with open(filename, "r") as f:
        state="Avant"
        for x in f:
            value, mesure_bride, mesure_cycle = pidoux_parser(x, mesure_bride, mesure_cycle)

            if mesure_cycle:
                if value.get("Cycle="):
                    data_dict = dict()
                    data_dict["Cycle"] = [value.get("Cycle=")]
                elif value.get("MGI="):
                    data_dict["MGI"] = [value.get("MGI=")]
                    data_dict["MGM"] = [value.get("MGM=")]
                    data_dict["MGS"] = [value.get("MGS=")]
                elif value.get("M05="):
                    data_dict["M05"] = [value.get("M05=")]
                    df = pd.DataFrame(data=data_dict, columns=["Cycle", "MGI", "MGM", "MGS", "M05"])
                    df_vieillissement = df_vieillissement.append(df)
                else:
                    if VERBOSE:
                        print("Pas de valeurs à extraire de la ligne: ", x)
            
            elif mesure_bride:
                if state == "Avant":
                    if value.get("MGI="):
                        avant_apres_dict = dict()
                        avant_apres_dict["Etat"] = state
                        avant_apres_dict["MGI"] = [value.get("MGI=")]
                        avant_apres_dict["MGM"] = [value.get("MGM=")]
                        avant_apres_dict["MGS"] = [value.get("MGS=")]
                    elif value.get("M48h="):
                        avant_apres_dict["M05"] = [value.get("M0.5=")]
                        avant_apres_dict["M50%"] = [value.get("M50%=")]
                        avant_apres_dict["M24h"] = [value.get("M24h=")]
                        avant_apres_dict["M48h"] = [value.get("M48h=")]
                    elif value.get("PerteM50%="):
                        avant_apres_dict["PerteM50% [%]"] = [value.get("PerteM50%=")]
                        avant_apres_dict["PerteM24h [%]"] = [value.get("PerteM24h=")]
                    elif value.get("Energie restituee="):
                        avant_apres_dict["Energie [J]"] = [value.get("Energie restituee=")]
                    elif value.get("Rendement="):
                        avant_apres_dict["Rendement [%]"] = [value.get("Rendement=")]
                        state = "Apres"
                        df = pd.DataFrame(data=avant_apres_dict)
                        df_avant_apres = df_avant_apres.append(df)
                    else:
                        if VERBOSE:
                            print("Pas de valeurs à extraire de la ligne: ", x)
                
                elif state == "Apres":

                    if value.get("MGI="):
                        avant_apres_dict["Etat"] = state
                        avant_apres_dict["MGI"] = [value.get("MGI=")]
                        avant_apres_dict["MGM"] = [value.get("MGM=")]
                        avant_apres_dict["MGS"] = [value.get("MGS=")]
                    elif value.get("M48h="):
                        avant_apres_dict["M05"] = [value.get("M0.5=")]
                        avant_apres_dict["M50%"] = [value.get("M50%=")]
                        avant_apres_dict["M24h"] = [value.get("M24h=")]
                        avant_apres_dict["M48h"] = [value.get("M48h=")]
                    elif value.get("PerteM50%="):
                        avant_apres_dict["PerteM50% [%]"] = [value.get("PerteM50%=")]
                        avant_apres_dict["PerteM24h [%]"] = [value.get("PerteM24h=")]
                    elif value.get("Energie restituee="):
                        avant_apres_dict["Energie [J]"] = [value.get("Energie restituee=")]
                    elif value.get("Rendement="):
                        avant_apres_dict["Rendement [%]"] = [value.get("Rendement=")]
                        state = "Avant"
                        df = pd.DataFrame(data=avant_apres_dict)
                        df_avant_apres = df_avant_apres.append(df)
                    else:
                        if VERBOSE:
                            print("Pas de valeurs à extraire de la ligne: ", x)
                
                else:
                    if VERBOSE:
                        print("ERREUR: state") # Sécurité, ne devrait jamais survenir
    
    return df_avant_apres, df_vieillissement

def save_features(features, path_name, var_name, write_mode="w"):
    string = "{"
    
    for feature in features:
        feature_value = features[feature]
        if type(feature_value) is str:
            string = string + f"{feature}: " + "\"" + f"{features[feature]}" + "\", "
        else:
            string = string + f"{feature}: {features[feature]}, "

    string = string + "}"
    string = string.replace(", }", "}")

    with open(path_name, write_mode) as f:
        f.write(f"const {var_name} = ")
        f.write(string)
        f.write("\n")

def save_to_json(df, path_name, var_name, write_mode="w"):
    data_formated = df.to_json(orient="records")

    with open(path_name, write_mode, encoding='utf-8') as f:
        f.write(f"var {var_name} = ")
        f.write(data_formated)
        f.write("\n")

def scan_and_calculate(path_to_scan, trials, file_caract, mgx_to_save=["MGI", "MGM", "MGS", "M05"], save_n_cycles=1,
                       save_path=""):

    if save_path == "":
        save_path = os.getcwd()
        print(f"Répertoire de sauvegarde modifié: {save_path}")
        
    directories = find_directories(path_to_scan)

    for directory in directories: # Boucle sur chaque répertoire (=1 essai de N barillets)
        if "Vieillissement ressort" in directory:
            continue

        # Le nom du répertoire fait office de nom de l'essai
        norm_directory = os.path.normpath(directory) # Correction des / en \ pour que le folder_name soit correct
        folder_name = norm_directory.split("\\")[-2] + "_" + norm_directory.split("\\")[-1]
        folder_name = remove_accents(folder_name) # Correction orthographique pour ne pas perturber VegaLite (é --> e)
        print("\nfolder_name: ", folder_name)

        print("="*(len("folder_name: " + folder_name) + 1))

        data_files = []

        for (dirpath, dirnames, filenames) in os.walk(directory):
            data_files.extend(filenames)
            break # Eviter la récursion sur les sous-dossiers, car la liste de ceux-ci est déjà disponible dans "directory"

        files = [fi for fi in data_files if fi.endswith(".TXT") ]

        if files: # S'il y a des fichiers de données à analyser
            df_vb_trial = pd.DataFrame() # Dataframe consacré à un seul essai, à "remettre à zéro" pour chaque nouvel essai (=directory)
            df_ab_trial = pd.DataFrame() # Dataframe consacré à un seul essai, à "remettre à zéro" pour chaque nouvel essai (=directory)
            success = False

            for fl in files: # Boucle sur chaque barillet de l'essai
                print(f"\nFichier: {directory + ' --> ' + fl}")
                brt = fl.split(".")[0]
                df_ab, df_vb = import_BRT(directory + "/" + fl)
                
                if df_ab.empty or df_vb.empty:
                    print("Pas de données récupérées")
                    continue
                else:
                    success = True # On a réussi à lire au moins un fichier, et on pourra faire la post-analyse
    
                # Conversion du nombre de cycle en année [1, ..., 10]
                # 365.25 pour éviter d'avoir la dernière valeur comptée dans l'année 11
                df_vb["Annee"] = df_vb["Cycle"].apply(lambda x: math.ceil((x + 1)/365.25))
                df_vb["Essai"] = folder_name
                df_vb["Barillet"] = brt

                # Suppression des cycles contenant des valeurs NaN
                # Remarque: on passe à df_temp uniquement pour ne pas avoir à modifier tout le code initial ensuite
                df_vb = df_vb.dropna(axis=0, how="any")

                # Définition officielle de la dérive pour 1 barillet: différence entre les valeurs du dernier cycle et 
                # du premier cycle, divisée par la valeur du premier cycle
                # ATTENTION: si le test n'a pas tourné jusqu'à 10 ans, on fausse le résultat
                dMGS_first_last = 100*((df_vb["MGS"].iloc[-1])/(df_vb["MGS"].iloc[0]) - 1)

                df_vb_trial= df_vb_trial.append(df_vb)

                df_ab["Essai"] = folder_name
                df_ab["Barillet"] = brt
                df_ab["Derive MGS BRT"] = dMGS_first_last
                df_ab_trial = df_ab_trial.append(df_ab)

            if success:
                trials.append(folder_name) # On ajoute le nom du dossier uniquement en cas de succès
                    
                df_vb_trial_mean = df_vb_trial.groupby(by="Cycle", axis=0).mean()
                dMGS_mean_first_last = round(100*((df_vb_trial_mean["MGS"].iloc[-1])/(df_vb_trial_mean["MGS"].iloc[0]) - 1), 2)
                
    
                df_mean_MGS = round(df_ab_trial["Derive MGS BRT"].mean(), 2)
                df_std_MGS = round(df_ab_trial["Derive MGS BRT"].std(), 2)
                df_ab_trial_sumup = df_ab_trial.groupby("Essai").mean()
        
                # Ajout des informations sur les sous-couches, couche d'or (bain et épaisseur mesurée) et l'épaisseur de bride
                filename = file_caract
                df_caract = pd.read_excel(filename)
                df_caract.drop(columns=["Remarque"], inplace=True)
        
                df_caract = df_caract.merge(df_ab_trial_sumup, on="Essai", how="right")
                
                df_caract["Full Description"] = "SC: " + df_caract["Sous-couche"] + "-" + df_caract["Epaisseur SC"].astype(str) + \
                     " mum // Flash: " + df_caract["Or"] + "-" + df_caract["Epaisseur Au mesuree"].astype(str) + " mum // Bride: " + df_caract["Bride"].astype(str) + \
                     " mm"
            
                df_caract["Derive Moy"] = f"Derive de la moyenne du MGS: {dMGS_mean_first_last}%"
                df_caract["Moy Derive"] = f"Moyenne de la derive du MGS: {df_mean_MGS}% ± {df_std_MGS}%"
        
                # =============================================================================
                # SAUVEGARDE DES DONNÉES POUR CHAQUE ESSAI
                # Afin d'éviter d'avoir des fichiers de données de grande taille, diverses stratégies d'élaguage
                # des données être mises en oeuvre
                # =============================================================================
        
                # 1. On se base sur mgx_to_save pour choisir ce que l'on sauve=["MGI", "MGM", "MGS", "M05"]
                mgx_to_drop = ["MGI", "MGM", "MGS", "M05"]
                for mgx in mgx_to_save:
                    mgx_to_drop.remove(mgx)
            
                if mgx_to_drop:
                    df_vb_trial.drop(columns=mgx_to_drop, inplace=True)
            
                # 2. Seul 1 point sur n_save est conservé (attention: on ne fait pas la moyenne sur le n_save point)
                # save_n_cycles = 1 correspond à l'enregistrement de tous les points
                if save_n_cycles > 0: 
                    df_tmp = df_vb_trial[(df_vb_trial.Cycle - 1) % save_n_cycles == 0]
                    df_vb_trial = df_tmp
    
                if not os.path.isdir(os.path.join(save_path, folder_name)):
                    os.mkdir(os.path.join(save_path, folder_name))
                
                df_vb_trial.to_excel(os.path.join(save_path, folder_name, "data_vb.xlsx"), index=False)
                df_caract.to_excel(os.path.join(save_path, folder_name, "data_caract.xlsx"), index=False)
                df_ab_trial.to_excel(os.path.join(save_path, folder_name, "data_trial.xlsx"), index=False)
    
    return True, trials
