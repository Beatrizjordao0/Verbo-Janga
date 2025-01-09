from flask import Flask, render_template, request, redirect, url_for
import mysql.connector

app = Flask(__name__)

# Conexão com o banco de dados
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="Bia",
        password="2233287774449999",
        database="igreja"
    )

@app.route('/')
def login_page():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = "SELECT * FROM obreiros WHERE email = %s AND senha = %s"
    cursor.execute(query, (email, password))
    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if user:
        return redirect(url_for('schedule_page'))
    else:
        return "<h1>Login inválido. <a href='/'>Tente novamente</a></h1>"

@app.route('/register', methods=['GET', 'POST'])
def register_page():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        name = request.form['name']
        department = request.form['department']

        conn = get_db_connection()
        cursor = conn.cursor()

        query = "INSERT INTO obreiros (email, senha, nome, departamentos) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (email, password, name, department))
        conn.commit()

        cursor.close()
        conn.close()

        return redirect(url_for('department_page'))

    return render_template('cadastro.html')

@app.route('/department', methods=['GET', 'POST'])
def department_page():
    if request.method == 'POST':
        days_off = request.form['days_off']
        email = request.form['email']

        conn = get_db_connection()
        cursor = conn.cursor()

        query = "UPDATE obreiros SET dias_nao_pode = %s WHERE email = %s"
        cursor.execute(query, (days_off, email))
        conn.commit()

        cursor.close()
        conn.close()

        return redirect(url_for('schedule_page'))

    return render_template('department.html')

@app.route('/schedule')
def schedule_page():
    return render_template('schedule.html')


if __name__ == '__main__':
    app.run(debug=True)
