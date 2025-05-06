PDF Insight Tool is a Flask-based web application for analyzing and comparing the content of multiple PDF documents. It extracts text using PyPDF2, Tika, and Tesseract OCR, and computes document similarity using NLP techniques and TF-IDF.

     Features
Extract text from PDFs (supports scanned and native PDFs)
Calculate similarity using NLP and TF-IDF
Filter results by similarity range and remove custom keywords
Upload multiple PDFs via ZIP file
Export comparison results to Excel
Handles filename normalization and edge cases
Tech Stack

Backend: Python, Flask

Frontend: HTML, CSS (Jinja templates)

Python librarries used are:
1. PyPDF2
2. Nltk
3. flask 
4. flask-wtf 
5. openpyxl 
6. Natsort
7. PyPDF2 
8. tika 
9. pytesseract 


Output: Dynamic similarity matrix + Excel export
