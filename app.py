from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import PyPDF2
import os

app = Flask(__name__)
CORS(app)

openai.api_key = os.getenv("OPENAI_API_KEY")

def extract_text_from_pdf(pdf_file):
    reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

@app.route("/ask", methods=["POST"])
def ask_question():
    if 'file' not in request.files or 'question' not in request.form:
        return jsonify({'error': 'Missing file or question'}), 400

    pdf_file = request.files['file']
    question = request.form['question']
    context = extract_text_from_pdf(pdf_file)

    prompt = f"Answer the following question based on the PDF content:\n\n{context}\n\nQuestion: {question}"

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300
        )
        answer = response['choices'][0]['message']['content'].strip()
        return jsonify({'answer': answer})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
