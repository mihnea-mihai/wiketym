from flask import Flask, request, render_template, send_file
from word import Word
import networkx as nx
from werkzeug.utils import secure_filename
from wiktionary import Language
from etygraph import EtyGraph

app = Flask(__name__)


@app.route('/')
def my_form():
    return render_template(
        'request.html',
        languages=[
            {'code': lang_code, 'name': lang_object['name']}
            for lang_code, lang_object in Language.lang_data.items()
            if len(lang_code) < 3
        ])


@app.route('/generate', methods=['GET'])
def my_form_post():
    G = EtyGraph()
    lemma = request.args['lemma']
    lang_code = request.args['lang_code']
    G.build({Word.get(lemma, lang_code)})
    filename = secure_filename(f'{lemma}_{lang_code}.pdf') or 'file.pdf'
    reduced: nx.DiGraph = nx.algorithms.transitive_reduction(G)
    reduced.add_nodes_from(G.nodes(data=True))
    reduced.add_edges_from(
        (u, v, G.edges[u, v]) for u, v in reduced.edges
    )
    nx.nx_pydot.to_pydot(reduced).write_pdf(filename)

    return send_file(filename, as_attachment=False)


if __name__ == '__main__':
    app.run(port=5000)
