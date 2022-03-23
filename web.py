from flask import Flask, request, render_template, send_file
from word import Word
import networkx as nx
from werkzeug.utils import secure_filename
from wiktionary.language import Language

app = Flask(__name__)


@app.route('/')
def my_form():
    return render_template(
        'request.html',
        languages=[
            {'code': lang_code, 'name': lang_object['name']}
            for lang_code, lang_object in Language._langs.items()
            if len(lang_code) < 3
        ])


@app.route('/', methods=['POST'])
def my_form_post():
    lemma = request.form['lemma']
    lang_code = request.form['lang_code']
    Word.get(lemma, lang_code)
    filename = secure_filename(f'{lemma}_{lang_code}.pdf') or 'file.pdf'
    nx.nx_pydot.to_pydot(Word.g).write_pdf(filename)

    Word.g = nx.DiGraph()
    Word._words = {}
    return send_file(filename, as_attachment=False)


if __name__ == '__main__':
    app.run(port=5000, debug=True)
