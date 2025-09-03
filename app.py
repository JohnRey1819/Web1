import os
import subprocess
import uuid
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from pdf2docx import Converter
import pandas as pd
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

# Use a temporary directory for file operations
UPLOAD_FOLDER = '/tmp/file_converter_uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'pptx', 'xlsx'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def handle_file_upload():
    """Checks for a valid file in the request and saves it securely."""
    if 'file' not in request.files:
        return None, (jsonify({"error": "No file part in the request"}), 400)
    
    file = request.files['file']
    if file.filename == '':
        return None, (jsonify({"error": "No file selected"}), 400)

    if file and allowed_file(file.filename):
        # Generate a unique directory for this conversion to avoid conflicts
        unique_dir = os.path.join(app.config['UPLOAD_FOLDER'], str(uuid.uuid4()))
        os.makedirs(unique_dir)
        
        filename = secure_filename(file.filename)
        input_path = os.path.join(unique_dir, filename)
        file.save(input_path)
        return input_path, None
    
    return None, (jsonify({"error": "File type not allowed"}), 400)

def run_libreoffice_conversion(input_path, output_dir):
    """Uses LibreOffice to convert documents to PDF."""
    try:
        # Command to execute for conversion
        command = [
            'libreoffice', '--headless', '--convert-to', 'pdf',
            '--outdir', output_dir, input_path
        ]
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        raise RuntimeError("LibreOffice is not installed or not in the system's PATH. This is required for conversion.")
    except subprocess.CalledProcessError as e:
        error_message = f"LibreOffice conversion failed. Error: {e.stderr.decode('utf-8')}"
        raise RuntimeError(error_message)

@app.route('/')
def index():
    return "File Converter Backend is running!"

@app.route('/convert-pdf-to-docx', methods=['POST'])
def convert_pdf_to_docx():
    input_path, error = handle_file_upload()
    if error:
        return error

    output_dir = os.path.dirname(input_path)
    base_filename = os.path.splitext(os.path.basename(input_path))[0]
    output_path = os.path.join(output_dir, f"{base_filename}.docx")
    
    try:
        cv = Converter(input_path)
        cv.convert(output_path)
        cv.close()
        return send_file(output_path, as_attachment=True)
    except Exception as e:
        return jsonify({"error": f"Conversion failed: {str(e)}"}), 500
    finally:
        # Clean up files and directory
        if os.path.exists(input_path): os.remove(input_path)
        if os.path.exists(output_path): os.remove(output_path)
        if os.path.exists(output_dir): os.rmdir(output_dir)

@app.route('/convert-pptx-to-pdf', methods=['POST'])
def convert_pptx_to_pdf():
    input_path, error = handle_file_upload()
    if error:
        return error
        
    output_dir = os.path.dirname(input_path)
    base_filename = os.path.splitext(os.path.basename(input_path))[0]
    output_path = os.path.join(output_dir, f"{base_filename}.pdf")

    try:
        run_libreoffice_conversion(input_path, output_dir)
        if not os.path.exists(output_path):
             raise RuntimeError("Conversion resulted in no output file.")
        return send_file(output_path, as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(input_path): os.remove(input_path)
        if os.path.exists(output_path): os.remove(output_path)
        if os.path.exists(output_dir): os.rmdir(output_dir)

@app.route('/convert-xlsx-to-pdf', methods=['POST'])
def convert_xlsx_to_pdf():
    input_path, error = handle_file_upload()
    if error:
        return error
        
    output_dir = os.path.dirname(input_path)
    base_filename = os.path.splitext(os.path.basename(input_path))[0]
    output_path = os.path.join(output_dir, f"{base_filename}.pdf")

    try:
        run_libreoffice_conversion(input_path, output_dir)
        if not os.path.exists(output_path):
             raise RuntimeError("Conversion resulted in no output file.")
        return send_file(output_path, as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(input_path): os.remove(input_path)
        if os.path.exists(output_path): os.remove(output_path)
        if os.path.exists(output_dir): os.rmdir(output_dir)

@app.route('/convert-xlsx-to-csv', methods=['POST'])
def convert_xlsx_to_csv():
    input_path, error = handle_file_upload()
    if error:
        return error
        
    output_dir = os.path.dirname(input_path)
    base_filename = os.path.splitext(os.path.basename(input_path))[0]
    output_path = os.path.join(output_dir, f"{base_filename}.csv")

    try:
        df = pd.read_excel(input_path)
        df.to_csv(output_path, index=False)
        return send_file(output_path, as_attachment=True)
    except Exception as e:
        return jsonify({"error": f"Conversion failed: {str(e)}"}), 500
    finally:
        if os.path.exists(input_path): os.remove(input_path)
        if os.path.exists(output_path): os.remove(output_path)
        if os.path.exists(output_dir): os.rmdir(output_dir)

if __name__ == '__main__':
    # Use 0.0.0.0 to be accessible on the network
    app.run(host='0.0.0.0', port=5000)
