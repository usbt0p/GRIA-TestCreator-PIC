from bs4 import BeautifulSoup as soup
from urllib.request import urlopen
import json


def get_form_data(url: str = None, use_file: str = "") -> tuple[list, list, list]:
    """Extract questions, answers and question types from a google form URL.
    The "structured" data in forms is buried in a script at the bottom of the HTML, so
    we need to work around it.

    Parameters
    ----------
    url : str
            The url of the page to scrape.
    use_file : str, optional
            The file to use for testing. Default is "".

    Returns
    -------
    questions : list
            The list of questions.
    answers : list
            The list of answers.
    question_type : list
            The list of question types.
    """

    if use_file:
        with open(use_file, "r") as file:
            url_content = file.read()
    else:
        url_client = urlopen(url)
        url_content = url_client.read()  # getting the content of the url.
        url_client.close()

    # beautiful soup parser to parse the files in html and get all scripts
    parser = soup(url_content, "html.parser")
    content = parser.find_all("script")

    # filter to get the one with 'var FB_PUBLIC_LOAD_DATA_' in it.
    content = [item for item in content if "var FB_PUBLIC_LOAD_DATA_" in str(item)][0]

    # now, split the content to get the data. Extract the json in the var and remove the semicolon.
    content = content.text.split("var FB_PUBLIC_LOAD_DATA_ = ")[1][:-1]

    # use the json format to turn the string into list.
    content = json.loads(content)

    data = content[1][1]  # get the data. dump stupid aah lists
    questions = []
    answers = []
    question_type = []

    for pair in data:
        question = pair[1]
        questions.append(question)

        answer = pair[4][0][1]  # stupid list indentation, 'thanks' google
        answer = [ans[0] for ans in answer]
        answers.append(answer)

        question_type.append(pair[3])

    # the code is the default one for correct div
    correct_answers = get_correct_answers(parser, "D42QGf")

    assert len(questions) == len(answers)

    return questions, answers, question_type, correct_answers


def format_into_json(questions, answers, type, corrects, filepath=None) -> dict:
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

    for q, a, t in zip(questions, answers, type):
        q = q.replace("\n", "")
        if t == 2:
            type = "singleChoice"
            dict_q = {
                "question": q,
                "options": a,
                "correct_option": None,
                "questionType": type,
            }
        elif t == 4:
            type = "multipleChoice"
            dict_q = {
                "question": q,
                "options": a,
                "correct_options": None,
                "questionType": type,
            }
        dict_qs["questions"].append(dict_q)

    # add the correct answers to the dict
    for i, q in enumerate(dict_qs["questions"]):
        if q["question"] in corrects:
            content = corrects[q["question"]]
            if q["questionType"] == "singleChoice":
                # go from the strings to their index
                if content[0] is not None:
                    dict_qs["questions"][i]["correct_option"] = [
                        q["options"].index(content[0])
                    ]
                else:
                    dict_qs["questions"][i]["correct_option"] = None

            elif q["questionType"] == "multipleChoice":
                dict_qs["questions"][i]["correct_options"] = [
                    q["options"].index(i) for i in content
                ]
        else:
            print("WARNING::Question mismatch!")
            print(
                "This means answer key and question key are not equivalent due to something. Fill it manually"
            )

    if filepath:
        with open(filepath, "w") as file:
            json.dump(dict_qs, file, indent=4, ensure_ascii=False)

    return dict_qs


def get_correct_answers(parser, class_id):
    """Get the correct answers from the google form.
    The correct answers are in a div with the class 'D42QGf' and the question name
    is in a span with the class 'M7eMe'.

    This only works for the questions you answered WRONG.
    Must implement a way to get the ones that are right!!!

    Parameters
    ----------
    parser : BeautifulSoup
            The parser to use.
    class_id : str
            The class id of the div containing the correct answers.
    Returns
    -------
    dict
            The dictionary of correct answers.
    """

    correct_answers_divs = {}
    divs = parser.find_all(
        "div", class_="OxAavc"
    )  # hardcoded code for the question divs
    for div in divs:
        # search for this specific class_id in the div, in order
        # if we find it, it means the question is answered wrong and has the correction
        qname = div.find(
            "span", class_="M7eMe"
        )  # name of the question to associate it with the answer
        div = div.find(
            "div", class_=class_id
        )  # D42QGf is the class of the div containing the correct answers
        if div:
            answerbox = div.find_all("span", dir="auto")
            to_add = [" ".join(span.text.split()) for span in answerbox]
            correct_answers_divs[" ".join(qname.text.split())] = to_add
        else:
            # if we don't find it, it means the question is not answered wrong
            # and you must fill it in manually
            # FIXME extend on here to get the correct ones...
            correct_answers_divs[" ".join(qname.text.split())] = [None]
            print(
                "WARNING!::One question was not answered wrong, so the correct answer is not available."
            )
            print("Please fill it in manually, the correct_options field will be null.")

    return correct_answers_divs


if __name__ == "__main__":

    # Example usage
    # url = input("Enter the url: ")
    # name = input("Enter complete file name: ")
    name = "PIC2/Unit8Teacher.json"
    file = "UTILS/scrapingUtils/test.html"
    assert name.endswith(".json")

    # q, a, t = get_data(url=url, use_file='test_answers.html')
    q, a, t, c = get_form_data(
        use_file=file
    )  # questions, answers, question type, correct answers
    json_output = format_into_json(q, a, t, c, filepath=name)

    # Example usage of get_correct_answers
    # with open(file, 'r') as file:
    #     html_content = file.read()
    # parser = soup(html_content, "html.parser")
    # correct_answers = get_correct_answers(parser, 'D42QGf')
