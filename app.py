from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)

def criar_tabelas():
    conn = sqlite3.connect('banco.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            descricao TEXT,
            valor_compra REAL NOT NULL,
            valor_venda REAL NOT NULL,
            estoque INTEGER NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER,
            quantidade INTEGER,
            data TEXT,
            lucro REAL,
            FOREIGN KEY (produto_id) REFERENCES produtos(id)
        )
    ''')
    conn.commit()
    conn.close()

criar_tabelas()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    conn = sqlite3.connect('banco.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        nome = request.form['nome']
        descricao = request.form['descricao']
        valor_compra = float(request.form['valor_compra'])
        valor_venda = float(request.form['valor_venda'])
        estoque = int(request.form['estoque'])
        cursor.execute('INSERT INTO produtos (nome, descricao, valor_compra, valor_venda, estoque) VALUES (?, ?, ?, ?, ?)', 
                       (nome, descricao, valor_compra, valor_venda, estoque))
        conn.commit()
        return redirect(url_for('cadastro'))

    cursor.execute('SELECT * FROM produtos')
    produtos = cursor.fetchall()
    conn.close()

    return render_template('cadastro.html', produtos=produtos)

@app.route('/editar/<int:id>', methods=['POST'])
def editar(id):
    conn = sqlite3.connect('banco.db')
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE produtos SET nome=?, descricao=?, valor_compra=?, valor_venda=?, estoque=?
        WHERE id=?
    ''', (
        request.form['nome'],
        request.form['descricao'],
        float(request.form['valor_compra']),
        float(request.form['valor_venda']),
        int(request.form['estoque']),
        id
    ))
    conn.commit()
    conn.close()
    return redirect(url_for('cadastro'))

@app.route('/excluir/<int:id>')
def excluir(id):
    conn = sqlite3.connect('banco.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM produtos WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('cadastro'))

@app.route('/vendas', methods=['GET', 'POST'])
def vendas():
    conn = sqlite3.connect('banco.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        produto_id = int(request.form['produto_id'])
        quantidade = int(request.form['quantidade'])
        cursor.execute('SELECT valor_compra, valor_venda, estoque FROM produtos WHERE id=?', (produto_id,))
        produto = cursor.fetchone()

        if produto and produto[2] >= quantidade:
            valor_compra, valor_venda, estoque = produto
            lucro = (valor_venda - valor_compra) * quantidade
            cursor.execute('UPDATE produtos SET estoque=estoque-? WHERE id=?', (quantidade, produto_id))
            cursor.execute('INSERT INTO vendas (produto_id, quantidade, data, lucro) VALUES (?, ?, ?, ?)', 
                           (produto_id, quantidade, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), lucro))
            conn.commit()

    cursor.execute('SELECT id, nome FROM produtos')
    produtos = cursor.fetchall()
    conn.close()
    return render_template('vendas.html', produtos=produtos)

@app.route('/relatorios', methods=['GET'])
def relatorios():
    periodo = request.args.get('periodo', 'diario')
    conn = sqlite3.connect('banco.db')
    cursor = conn.cursor()

    hoje = datetime.now()
    if periodo == 'diario':
        data_inicio = hoje.strftime("%Y-%m-%d")
    elif periodo == 'semanal':
        data_inicio = (hoje - timedelta(days=7)).strftime("%Y-%m-%d")
    elif periodo == 'mensal':
        data_inicio = (hoje - timedelta(days=30)).strftime("%Y-%m-%d")
    else:
        data_inicio = '1900-01-01'

    cursor.execute('''
        SELECT v.id, p.nome, v.quantidade, v.data, v.lucro, 
               (v.quantidade * p.valor_compra) as despesas,
               (v.quantidade * p.valor_venda) as total_venda
        FROM vendas v
        JOIN produtos p ON v.produto_id = p.id
        WHERE date(v.data) >= ?
        ORDER BY v.data DESC
    ''', (data_inicio,))
    vendas = cursor.fetchall()

    total_vendas = sum([v[6] for v in vendas]) if vendas else 0
    total_despesas = sum([v[5] for v in vendas]) if vendas else 0
    total_lucros = sum([v[4] for v in vendas]) if vendas else 0

    conn.close()
    return render_template('relatorios.html', vendas=vendas,
                           total_vendas=total_vendas,
                           total_despesas=total_despesas,
                           total_lucros=total_lucros,
                           periodo=periodo)

if __name__ == '__main__':
    app.run(debug=True)

