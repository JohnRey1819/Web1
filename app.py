import os
from flask import Flask, request, render_template_string, send_file, jsonify
from rembg import remove
from PIL import Image
import io

# Create a 'templates' directory if it doesn't exist
if not os.path.exists('templates'):
    os.makedirs('templates')

# The HTML content will be written to this file
# This is done to keep the Flask app structure standard
html_file_path = os.path.join('templates', 'index.html')

# Define the HTML template content
# We will write this string to the templates/index.html file
html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Background Remover</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Inter', sans-serif;
        }
        .custom-loader {
            width: 50px;
            height: 50px;
            border-radius: 50%;
            border: 5px solid #f3f3f3;
            border-top: 5px solid #3498db;
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body class="bg-gray-100 text-gray-800 flex items-center justify-center min-h-screen">
    <div class="container mx-auto p-4 md:p-8 max-w-2xl">
        <div class="bg-white rounded-2xl shadow-xl p-6 md:p-10">
            <div class="text-center mb-8">
                <h1 class="text-3xl md:text-4xl font-bold text-gray-900">AI Background Remover</h1>
                <p class="text-gray-500 mt-2">Upload your image and we'll remove the background for free!</p>
            </div>
            
            <!-- Upload Form -->
            <form id="upload-form" class="space-y-6">
                <div>
                    <label for="file-upload" class="cursor-pointer block w-full border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-500 hover:bg-gray-50 transition-colors">
                        <svg class="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48" aria-hidden="true">
                            <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                        </svg>
                        <span id="file-name" class="mt-2 block text-sm font-medium text-gray-600">Click to upload an image</span>
                        <p class="text-xs text-gray-500">PNG, JPG, WEBP up to 10MB</p>
                    </label>
                    <input id="file-upload" name="file" type="file" class="sr-only" accept="image/png, image/jpeg, image/webp">
                </div>
                <button type="submit" id="submit-button" class="w-full bg-blue-600 text-white font-semibold py-3 px-4 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed">
                    Remove Background
                </button>
            </form>

            <!-- Loading Indicator -->
            <div id="loading" class="text-center py-8" style="display: none;">
                <div class="custom-loader mx-auto"></div>
                <p class="mt-4 text-gray-600 font-medium">Processing your image...</p>
            </div>

            <!-- Error Message -->
            <div id="error-message" class="text-center p-4 my-4 bg-red-100 text-red-700 rounded-lg" style="display: none;">
                <!-- Error content goes here -->
            </div>

            <!-- Result Display -->
            <div id="result" class="mt-8" style="display: none;">
                <h2 class="text-2xl font-bold text-center mb-6">Your Image is Ready!</h2>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div class="text-center">
                        <h3 class="font-semibold mb-2">Original</h3>
                        <img id="original-image" class="rounded-lg shadow-md w-full h-auto object-contain max-h-80" alt="Original Image">
                    </div>
                    <div class="text-center">
                        <h3 class="font-semibold mb-2">Background Removed</h3>
                        <img id="processed-image" class="rounded-lg shadow-md w-full h-auto object-contain max-h-80" alt="Processed Image with background removed">
                    </div>
                </div>
                <div class="mt-8 text-center">
                    <a id="download-button" href="#" download="background-removed.png" class="inline-block bg-green-600 text-white font-semibold py-3 px-8 rounded-lg hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 transition-all">
                        Download Image
                    </a>
                </div>
            </div>

        </div>
        <footer class="text-center mt-6 text-sm text-gray-500">
            <p>Powered by Python, Flask & Rembg. Deployed on Render.</p>
        </footer>
    </div>

    <script>
        const form = document.getElementById('upload-form');
        const fileInput = document.getElementById('file-upload');
        const submitButton = document.getElementById('submit-button');
        const fileNameDisplay = document.getElementById('file-name');
        const loading = document.getElementById('loading');
        const resultDiv = document.getElementById('result');
        const errorDiv = document.getElementById('error-message');
        
        const originalImage = document.getElementById('original-image');
        const processedImage = document.getElementById('processed-image');
        const downloadButton = document.getElementById('download-button');

        fileInput.addEventListener('change', () => {
            if (fileInput.files.length > 0) {
                const fileName = fileInput.files[0].name;
                fileNameDisplay.textContent = fileName.length > 30 ? fileName.substring(0, 27) + '...' : fileName;
            } else {
                fileNameDisplay.textContent = 'Click to upload an image';
            }
        });

        form.addEventListener('submit', async (event) => {
            event.preventDefault();

            if (!fileInput.files || fileInput.files.length === 0) {
                showError('Please select a file to upload.');
                return;
            }

            const file = fileInput.files[0];
            const formData = new FormData();
            formData.append('file', file);

            // Hide previous results/errors and show loader
            resultDiv.style.display = 'none';
            errorDiv.style.display = 'none';
            form.style.display = 'none';
            loading.style.display = 'block';
            submitButton.disabled = true;

            try {
                const response = await fetch('/remove-bg', {
                    method: 'POST',
                    body: formData,
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || `Server responded with status: ${response.status}`);
                }

                const blob = await response.blob();
                const processedImageUrl = URL.createObjectURL(blob);
                const originalImageUrl = URL.createObjectURL(file);
                
                originalImage.src = originalImageUrl;
                processedImage.src = processedImageUrl;
                downloadButton.href = processedImageUrl;

                resultDiv.style.display = 'block';
            } catch (error) {
                console.error('Error:', error);
                showError(`An error occurred: ${error.message}`);
            } finally {
                // Hide loader and show form again
                loading.style.display = 'none';
                form.style.display = 'block';
                submitButton.disabled = false;
                form.reset(); // Clear the file input
                fileNameDisplay.textContent = 'Click to upload another image';
            }
        });

        function showError(message) {
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
        }
    </script>
</body>
</html>
"""

# Write the HTML content to the file
with open(html_file_path, 'w') as f:
    f.write(html_template)

# --- Flask App ---
app = Flask(__name__)

# Set a higher body limit, e.g., 16 MB
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

@app.route('/')
def index():
    """Renders the main upload page."""
    return render_template_string(html_template)

@app.route('/remove-bg', methods=['POST'])
def remove_background():
    """Handles the file upload and background removal process."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No file selected for uploading'}), 400

    if file:
        try:
            input_bytes = file.read()
            
            # --- Image Processing with rembg ---
            # Using Pillow to ensure the image is in a compatible format (RGBA)
            # This improves reliability with different image types.
            input_image = Image.open(io.BytesIO(input_bytes))
            
            # rembg returns bytes of a PNG image
            output_bytes = remove(input_image)
            
            # Send the result back as a file
            return send_file(
                io.BytesIO(output_bytes),
                mimetype='image/png',
                as_attachment=True,
                download_name='background-removed.png'
            )
        except Exception as e:
            # This will catch errors from rembg if the image format is unsupported
            print(f"Error processing image: {e}")
            return jsonify({'error': 'Failed to process image. It might be corrupted or in an unsupported format.'}), 500
    
    return jsonify({'error': 'An unknown error occurred.'}), 500

if __name__ == '__main__':
    # This is for local development.
    # Render will use a Gunicorn server instead.
    app.run(debug=True)
