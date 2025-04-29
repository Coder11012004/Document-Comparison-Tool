from flask import Flask, render_template, request, send_file, redirect, url_for, flash, session
from flask_wtf import FlaskForm
from wtforms import FileField, StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, DataRequired
import os
from openpyxl import Workbook
from natsort import natsorted
from process import compare_pdfs, extract_zip
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

class UploadForm(FlaskForm):
    zipfile = FileField("Upload ZIP", validators=[InputRequired()])
    submit = SubmitField("Upload and Process")
class LoginForm(FlaskForm):
    username = StringField("Username:", validators=[DataRequired()])
    password = PasswordField("Password:", validators=[DataRequired()])
    submit = SubmitField("Login")

USER_CREDENTIALS={"Mahir":"123"}

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    error = None
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
            session['user'] = username
            flash('Login successful!','success')
            return redirect(url_for('upload_and_compare'))
        else:
            error = 'Invalid username or password. Please try again.'
    return render_template('login.html', form=form, error=error)

@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

@app.route("/", methods=["GET", "POST"])
def upload_and_compare():
    if "user" not in session:
        flash("Please log in first!", "warning")
        return redirect(url_for("login"))
    form = UploadForm()
    if request.method == "POST" and form.validate_on_submit():
        zip_file = request.files["zipfile"]
        extract_to = "extracted_files"
        if zip_file:
            zip_path = os.path.join(extract_to, "uploaded.zip")
            os.makedirs(extract_to, exist_ok=True)
            zip_file.save(zip_path)
            extract_zip(zip_path, extract_to)
            pdf_files=natsorted([f for f in os.listdir(extract_to) if f.endswith('.pdf')])
            if len(pdf_files) < 2:
                flash("Not enough PDF files to compare.", "danger")
                return render_template("index.html", form=form, user=session["user"])
            matrix={pdf: {pdf: 100.0 for pdf in pdf_files} for pdf in pdf_files}
            for i in range(len(pdf_files)):
                for j in range(i + 1, len(pdf_files)):
                    pdf1, pdf2 = pdf_files[i], pdf_files[j]
                    ratio = compare_pdfs(os.path.join(extract_to, pdf1), os.path.join(extract_to, pdf2))
                    matrix[pdf1][pdf2] = round(ratio, 2)
                    matrix[pdf2][pdf1] = round(ratio, 2)
            app.config["MATRIX"] = matrix
            app.config["FILES"] = pdf_files
            excel_path = "comparison_results.xlsx"
            wb = Workbook()
            ws = wb.active
            ws.title = "Comparison Matrix"
            headers = ["File Name"] + pdf_files
            ws.append(headers)
            for pdf in pdf_files:
                ws.append([pdf] + [matrix[pdf][other_pdf] for other_pdf in pdf_files])
            wb.save(excel_path)
            flash("Comparison results saved successfully!", "success")
            return redirect(url_for("filter_results", min_similarity=0))
    return render_template("index.html", form=form, user=session.get("user"))

@app.route('/filter_results', methods=['GET'])
def filter_results():
    if "user" not in session:
        flash("Please log in first!", "warning")
        return redirect(url_for("login"))

    matrix = app.config.get("MATRIX", {})
    files = app.config.get("FILES", [])
    min_similarity = request.args.get("min_similarity", type=int, default=0)
    max_similarity = request.args.get("max_similarity", type=int, default=100)
    remove_words = request.args.get("remove_words", default="").strip()
    if not files:
        flash("No comparison data available. Please upload files first.", "danger")
        return redirect(url_for("upload_and_compare"))
    custom_stopwords=set(word.strip().lower() for word in remove_words.split(",") if word.strip())
    normalized_files={f.strip().lower().replace(" ", ""): f for f in files}
    filtered_matrix={
        normalized_files.get(file1.strip().lower().replace(" ", ""), file1): {
            normalized_files.get(file2.strip().lower().replace(" ", ""), file2):
            similarity if min_similarity <= similarity <= max_similarity else ""
            for file2, similarity in row.items()
        }
        for file1, row in matrix.items()
    }
    valid_rows={
        file: row for file, row in filtered_matrix.items()
        if any(val != "" for other_file, val in row.items() if other_file != file)
    }
    valid_cols=set(
        key for row in valid_rows.values() for key, value in row.items()
        if value != "" or key in valid_rows
    )
    cleaned_matrix={
        file: {other_file: value for other_file, value in row.items() if other_file in valid_cols}
        for file, row in valid_rows.items()
        if file in valid_cols
    }
    return render_template(
        "result.html",
        matrix=cleaned_matrix,
        files=sorted(cleaned_matrix.keys()),
        min_similarity=min_similarity,
        max_similarity=max_similarity,
        remove_words=remove_words,
        user=session["user"],
    )

@app.route("/download")
def download_file():
    if "user" not in session:
        flash("Please log in first!", "warning")
        return redirect(url_for("login"))

    matrix = app.config.get("MATRIX", {})
    files = app.config.get("FILES", [])
    min_similarity = request.args.get("min_similarity", type=int, default=0)
    max_similarity = request.args.get("max_similarity", type=int, default=100)
    remove_words = request.args.get("remove_words", default="").strip()

    if not files:
        flash("No comparison data available. Please upload files first.", "danger")
        return redirect(url_for("upload_and_compare"))
    normalized_files = {f.strip().lower().replace(" ", ""): f for f in files}
    filtered_matrix = {
        normalized_files.get(file1.strip().lower().replace(" ", ""), file1): {
            normalized_files.get(file2.strip().lower().replace(" ", ""), file2):
            similarity if min_similarity <= similarity <= max_similarity else ""
            for file2, similarity in row.items()
        }
        for file1, row in matrix.items()
    }

    valid_rows = {
        file: row for file, row in filtered_matrix.items()
        if any(val != "" for other_file, val in row.items() if other_file != file)
    }
    valid_cols = set(
        key for row in valid_rows.values() for key, value in row.items()
        if value != "" or key in valid_rows
    )
    cleaned_matrix = {
        file: {other_file: value for other_file, value in row.items() if other_file in valid_cols}
        for file, row in valid_rows.items()
        if file in valid_cols
    }
    filtered_excel_path="comparison_results.xlsx"
    wb=Workbook()
    ws=wb.active
    ws.title="Comparison Matrix"
    headers=["File Name"]+list(cleaned_matrix.keys())
    ws.append(headers)
    for file1, row in cleaned_matrix.items():
        row_data = [file1] + [
            "" if file1 == file2 else row.get(file2, "")
            for file2 in cleaned_matrix.keys()]
        ws.append(row_data)
    wb.save(filtered_excel_path)
    return send_file(filtered_excel_path, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)