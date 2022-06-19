from flask import Flask, request, render_template, send_file
# from werkzeug.utils import secure_filename

from src.wiketym.wiktionary.language import Language
from src.wiketym.query import Query
from src.wiketym.word import Word

app = Flask(__name__)


@app.route("/")
def my_form():
    return render_template(
        "request.html",
        languages=[
            {"code": lang_code, "name": lang_object["name"]}
            for lang_code, lang_object in Language.lang_data.items()
            if len(lang_code) < 3
        ],
    )


@app.route("/generate", methods=["GET"])
def my_form_post():
    Query([Word(request.args['lemma'], request.args['lang_code'])])
    return send_file('outputs/test.pdf', as_attachment=False)


if __name__ == "__main__":
    app.run(port=5000)
