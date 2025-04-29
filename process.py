import zipfile
import os
import shutil
import uuid
from PyPDF2 import PdfReader
import re
import ssl
import nltk
from nltk.corpus import stopwords
ssl._create_default_https_context = ssl._create_unverified_context
try:
    nltk.data.find("tokenizers/punkt")
    nltk.data.find("corpora/stopwords")
except LookupError:
    nltk.download("punkt")
    nltk.download("stopwords")

def extract_zip(zip_path, extract_to):
    try:
        if not os.path.exists(extract_to):
            os.makedirs(extract_to)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print(f"Extracted files to: {extract_to}")
    except PermissionError as e:
        print(f"Permission denied: {e}")
        raise
    except Exception as e:
        print(f"Error extracting ZIP file: {e}")
        raise

def extract_words_from_pdf(pdf_path, extra_stopwords=None):
    try:
        if not os.access(pdf_path, os.R_OK):
            print(f"Access Denied: Cannot read the PDF file {pdf_path}")
            return set()
        reader = PdfReader(pdf_path)
        text = "".join([page.extract_text() for page in reader.pages if page.extract_text()])
        words = re.findall(r'\w+', text.lower())

        stop_words = set(stopwords.words("english"))
        if extra_stopwords:
            stop_words.update([word.lower() for word in extra_stopwords])
        filtered_words = [word for word in words if word not in stop_words]
        return set(filtered_words)

    except Exception as e:
        print(f"Error extracting words from PDF {pdf_path}: {e}")
        return set()

def compare_pdfs(pdf1_path, pdf2_path, extra_stopwords=None):
    try:
        words1 = extract_words_from_pdf(pdf1_path,extra_stopwords)
        words2 = extract_words_from_pdf(pdf2_path,extra_stopwords)
        common_words=words1 & words2
        matching_words=len(common_words)
        total_distinct_words=len(words1 | words2)
        if total_distinct_words==0:
            return 0.0
        ratio=(matching_words/total_distinct_words)*100
        return ratio
    except Exception as e:
        print(f"Error comparing PDFs: {e}")
        return 0.0

def main():
    zip_path = input("Enter the ZIP file path: ").strip()
    extract_to = "extracted_files"
    user_input = input("Enter any additional stopwords separated by commas (or press Enter to skip): ")
    extra_stopwords = [word.strip() for word in user_input.split(",")] if user_input else []
    try:
        extract_zip(zip_path, extract_to)
        pdf_files = [os.path.join(extract_to, f) for f in os.listdir(extract_to) if f.endswith('.pdf')]

        if len(pdf_files) < 2:
            print("Not enough PDF files to compare.")
            shutil.rmtree(extract_to)
            return
        num_files_to_compare = min(len(pdf_files), 2 + (uuid.uuid4().int % (len(pdf_files) - 1)))
        selected_pdfs = list(pdf_files)[:num_files_to_compare]
        print(f"\nSelected {num_files_to_compare} files for comparison:\n{selected_pdfs}\n")

        total_matching_ratio = 0.0
        total_comparisons = 0

        file_names = [os.path.basename(f) for f in selected_pdfs]
        matrix_data = {name: {name2: "" for name2 in file_names} for name in file_names}

        for i in range(len(selected_pdfs)):
            for j in range(len(selected_pdfs)):
                if i == j:
                    matrix_data[file_names[i]][file_names[j]] = ""
                    continue
                pdf1 = selected_pdfs[i]
                pdf2 = selected_pdfs[j]
                print(f"Comparing {os.path.basename(pdf1)} and {os.path.basename(pdf2)}...")
                ratio = compare_pdfs(pdf1, pdf2, extra_stopwords)
                print(f"Matching words ratio: {ratio:.4f}")

                total_matching_ratio += ratio
                total_comparisons += 1

                matrix_data[file_names[i]][file_names[j]] = "1" if ratio > 0 else ""

        if total_comparisons > 0:
            average_matching_ratio = total_matching_ratio / total_comparisons
            print(f"\nTotal matching ratio between the files: {average_matching_ratio:.4f}")
        else:
            print("\nNo comparisons were made.")

    except PermissionError as e:
        print(f"Permission denied: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(extract_to):
            shutil.rmtree(extract_to)
        print("Temporary files cleaned up.")
if __name__ == "__main__":
    main()