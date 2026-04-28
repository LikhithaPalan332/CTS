from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector

app = Flask(__name__)
app.secret_key = 'supersecretkey'

def connect_db():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='#######',  
        database='courier_system'
    )

@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        mobile = request.form['mobile'].strip()

        if not username or not password or not mobile:
            flash("All fields are required!")
            return redirect(url_for('register'))

        try:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
            if cursor.fetchone():
                flash("Username already exists!")
                return redirect(url_for('register'))

            cursor.execute("INSERT INTO users (username, password, mobile) VALUES (%s, %s, %s)",
                           (username, password, mobile))
            conn.commit()
            flash("Registered successfully! Please login.")
            return redirect(url_for('login'))

        except Exception as e:
            flash(f"Registration failed: {str(e)}")
            return redirect(url_for('register'))

        finally:
            cursor.close()
            conn.close()

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            session['username'] = username
            flash("Login successful!")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid username or password!")
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'username' not in session:
        flash("Please login first!")
        return redirect(url_for('login'))

    conn = connect_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        # Add new courier
        courier_id = request.form['courier_id'].strip()
        sender = request.form['sender'].strip()
        receiver = request.form['receiver'].strip()
        status = request.form['status'].strip()

        if not courier_id or not sender or not receiver or not status:
            flash("All courier fields are required!")
        else:
            try:
                cursor.execute("INSERT INTO couriers (courier_id, sender_name, receiver_name, status) VALUES (%s, %s, %s, %s)",
                               (courier_id, sender, receiver, status))
                conn.commit()
                flash("Courier added successfully!")
            except Exception as e:
                flash(f"Failed to add courier: {str(e)}")

    # Handle search/filter query param
    search = request.args.get('search', '').strip()
    if search:
        query = """
            SELECT * FROM couriers 
            WHERE courier_id LIKE %s OR sender_name LIKE %s OR receiver_name LIKE %s OR status LIKE %s
            ORDER BY id DESC
        """
        like_search = f"%{search}%"
        cursor.execute(query, (like_search, like_search, like_search, like_search))
    else:
        cursor.execute("SELECT * FROM couriers ORDER BY id DESC")

    couriers = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('dashboard.html', couriers=couriers, search=search)


@app.route('/update_status/<int:courier_id>', methods=['POST'])
def update_status(courier_id):
    if 'username' not in session:
        flash("Please login first!")
        return redirect(url_for('login'))

    new_status = request.form.get('new_status', '').strip()
    if not new_status:
        flash("New status cannot be empty!")
        return redirect(url_for('dashboard'))

    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE couriers SET status=%s WHERE id=%s", (new_status, courier_id))
        conn.commit()
        flash("Courier status updated!")
    except Exception as e:
        flash(f"Failed to update status: {str(e)}")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('dashboard'))


@app.route('/delete/<int:courier_id>')
def delete_courier(courier_id):
    if 'username' not in session:
        flash("Please login first!")
        return redirect(url_for('login'))

    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM couriers WHERE id=%s", (courier_id,))
        conn.commit()
        flash("Courier deleted successfully!")
    except Exception as e:
        flash(f"Failed to delete courier: {str(e)}")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('dashboard'))


@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("Logged out successfully!")
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
