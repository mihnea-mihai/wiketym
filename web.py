from flask import Flask, request, render_template, send_file
from src.wiketym.wiktionary.language import Language
from src.wiketym.query import Query
from src.wiketym.word import Word

app = Flask(__name__)

PREF_LANGS = ["en", "ro", "de", "la", "fr", "es"]


@app.route("/")
def my_form():
    return render_template(
        "request.html",
        languages=[
            {"code": lang_code, "name": lang_object.name}
            for lang_code, lang_object in {
                code: Language(code) for code in PREF_LANGS
            }.items()
        ]
        + [
            {"code": lang_code, "name": lang_object["name"]}
            for lang_code, lang_object in Language.lang_data.items()
            if len(lang_code) < 3 and lang_code not in PREF_LANGS
        ],
    )


@app.route("/generate", methods=["GET"])
def generate():

    lemmas = [v for k, v in request.args.items() if k.startswith("lemma")]
    lang_codes = [v for k, v in request.args.items() if k.startswith("lang_code")]

    word_list = [
        Word(lemmas[i], lang_codes[i]) for i in range(len(lemmas)) if lemmas[i]
    ]
    q = Query(
        word_list,
        allow_invalid=request.args.get("show_invalid"),
        max_level=int(request.args["max_level"]),
        max_count=int(request.args["max_count"]),
        reduce=request.args.get("reduce"),
        ignore_affixes=request.args.get("ignore_affixes"),
    )
    return send_file(f"outputs/{q.filename}.pdf", as_attachment=False)


if __name__ == "__main__":
    app.run(port=5000)
