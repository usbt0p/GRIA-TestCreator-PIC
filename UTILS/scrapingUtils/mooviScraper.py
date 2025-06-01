from bs4 import BeautifulSoup
import re
from joinJsons import join_jsons
import json


def get_moovi_data(use_file=None, assume_correct=False):
    with open(use_file, encoding="utf-8") as html_file:
        content = html_file.read()
        page = BeautifulSoup(content, "html.parser")

    preguntas = []
    opciones = []
    correctas = []
    feedbacks = []

    # Colle as preguntas e opcións do div parent
    formulation = page.find_all("div", class_="formulation clearfix")
    # print(formulation)

    for item in formulation:
        pregunta = item.find("div", class_="qtext").text

        opcion = item.find_all("div", class_="flex-fill ml-1")
        opcion = [elem.text for elem in opcion]

        correct_n = []
        if assume_correct:  # We will assume the checked options are correct
            correct = []
            inputs = item.find_all("input", attrs={"checked": "checked"})
            for inp in inputs:
                # Find the corresponding label or option text
                label_id = inp.get("aria-labelledby")
                if label_id:
                    label_elem = item.find(id=label_id)
                if label_elem:
                    correct.append(
                        label_elem.find(  # to remove answernumber
                            "div", class_="flex-fill ml-1"
                        ).text
                    )
            correct_n = [opcion.index(elem) for elem in correct]

        # Colle a sección coa pregunta e feedback, e inclúe o feedback se a pregunta o ten
        feedback = item.find_all("div", class_="feedback")

        if feedback:
            # FIXME legacy, might not work for all cases
            generalfeedback = feedback.find("div", class_="generalfeedback")
            correcta = feedback.find("div", class_="rightanswer")
            feedbacks.append(generalfeedback.text)

        preguntas.append(pregunta)
        opciones.append(opcion)
        correctas.append(correct_n)

    return preguntas, opciones, correctas, feedbacks


def format_into_json(questions, answers, type, correct, filepath=None) -> dict:
    """Format the data into a json file for the quiz app.
    For format of the json file, refer to the README.

    Parameters
    ----------
    questions : list
            The list of questions.
    answers : list
            The list of answers.
    type : list
            The list of question types.
    filepath : str, optional
            The filepath to save the json file. Default is None.

    Returns
    -------
    dict_qs : dict
            The dictionary of questions.
    """

    dict_qs = {"questions": []}

    for q, a, t, c in zip(questions, answers, type, correct):
        if t == 2:
            try:
                correct_option = c[0] if isinstance(c, list) else c
            except IndexError as e:
                print(f"Error getting correct option")
                correct_option = -1
            type = "singleChoice"
            dict_q = {
                "question": q,
                "options": a,
                "correct_option": correct_option,
                "questionType": type,
            }
        elif t == 4:
            type = "multipleChoice"
            dict_q = {
                "question": q,
                "options": a,
                "correct_options": c,
                "questionType": type,
            }
        dict_qs["questions"].append(dict_q)

    if filepath:
        with open(filepath, "w", encoding="utf-8") as file:
            json.dump(dict_qs, file, indent=2, ensure_ascii=False)

    return dict_qs


if __name__ == "__main__":
    """Coloca aquí o path do teu ficheiro de html
    A poder ser, non descargues nen lle deas a 'guardar como' para evitar problemas de formateado.
    No seu lugar, unha vez no exame escribe na barra de busca 'view-source' ao principio da query:
        view-source:https://moovi.uvigo.gal/mod/quiz/review.php...
    Dalle a Ctrl+A para seleccionalo todo, cópiao e pégao nun arquivo html no directorio no que o vaias ler.
    En firefox está comprobado que funciona.

    Después de ejecutar, revisad el JSON. Modificad a mano los -1 que encontréis en correct_option.
    """

    path = "./moovi.html"
    newfile_name = "./new.json"
    data = get_moovi_data(use_file=path)

    # Example usage
    assert newfile_name[-5:] == ".json"

    q, a, c, _ = get_moovi_data(use_file=path)  # questions, answers, question type
    t = [2] * len(q)  # FIXME hardcoded for single choice questions
    json_output = format_into_json(q, a, t, c, filepath=newfile_name)

    # Example usage
    join_jsons("SIRE/UnitAda3.json", "new.json", filepath="SIRE/UnitAda3.json")
