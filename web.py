from crypt import methods
from flask import Flask, request, render_template, send_file
from word import Word
import pygraphviz as pgv

app = Flask(__name__)

# @app.route("/")
# def hello_world():
#     return "<p>Hello, World!</p>"

@app.route('/')
def my_form():
    return render_template('request.html')

@app.route('/', methods=['POST'])
def my_form_post():
    lemma = request.form['lemma']
    lang_code = request.form['lang_code']
    Word.get(lemma, lang_code)
    filename = f'{lemma}_{lang_code}.pdf'
    Word.g.draw(filename, prog='dot')
    Word.g = pgv.AGraph(directed=True)
    Word._words = {}
    return send_file(f'{filename}', as_attachment=False)


if __name__ == '__main__':
    app.run(port=5000, debug=True)