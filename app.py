import io
from flask import Flask, render_template_string, request, send_file
from rembg import remove
from PIL import Image

# Initialize the Flask application
app = Flask(__name__)

# HTML template for the user interface, styled with Tailwind CSS
# All logic is contained in this single file for simplicity.
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Background Remover</title>
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
            border: 5px solid rgba(209, 213, 219, 0.3);
            border-top-color: #3b82f6;
            animation: spin 1s ease-in-out infinite;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    </style>
</head>
<body class="bg-gray-100 text-gray-800 flex items-center justify-center min-h-screen">
    <div class="container mx-auto p-4 md:p-8 max-w-2xl">
        <div class="bg-white rounded-2xl shadow-lg p-8 md:p-12">
            <header class="text-center mb-8">
                <h1 class="text-4xl md:text-5xl font-bold text-gray-900">AI Background Remover</h1>
                <p class="text-gray-600 mt-3 text-lg">Upload an image and let our AI remove the background for you.</p>
            </header>
            
            <form id="upload-form" class="space-y-6">
                <div id="image-preview-container" class="w-full h-64 border-2 border-dashed border-gray-300 rounded-lg flex items-center justify-center bg-gray-50 hidden">
                    <img id="image-preview" src="#" alt="Image Preview" class="max-h-full max-w-full rounded-md"/>
                </div>
                
                <div id="upload-box" class="w-full p-8 border-2 border-dashed border-gray-300 rounded-lg flex flex-col items-center justify-center text-center cursor-pointer hover:bg-gray-50 transition-colors">
                    <svg class="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path></svg>
                    <p class="mt-2 text-gray-500"><span class="font-semibold text-blue-600">Click to upload</span> or drag and drop</p>
                    <p class="text-xs text-gray-500">PNG, JPG, or WEBP</p>
                    <input id="file-input" type="file" name="file" class="hidden" accept="image/png, image/jpeg, image/webp">
                </div>
                
                <button type="submit" id="submit-button" class="w-full bg-blue-600 text-white font-bold py-3 px-4 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-4 focus:ring-blue-300 transition-all disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center space-x-2">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L3 10.25l1.5-1.5L9.75 14l9.75-9.75L21 5.75z"></path></svg>
                    <span>Remove Background</span>
                </button>
            </form>
            
            <div id="result-section" class="mt-8 text-center hidden">
                <h2 class="text-2xl font-semibold mb-4">Your Image is Ready!</h2>
                <div class="flex justify-center p-4 bg-gray-100 rounded-lg">
                    <img id="result-image" src="" alt="Result Image" class="max-w-full max-h-80 rounded-md shadow-md"/>
                </div>
                <a id="download-button" href="#" download="background-removed.png" class="mt-6 inline-block w-full md:w-auto bg-green-500 text-white font-bold py-3 px-6 rounded-lg hover:bg-green-600 focus:outline-none focus:ring-4 focus:ring-green-300 transition-all">
                    Download Image
                </a>
            </div>

            <!-- Loading Spinner -->
            <div id="loader" class="mt-8 hidden items-center justify-center flex-col">
                <div class="custom-loader"></div>
                <p class="text-gray-600 mt-4">Processing your image, please wait...</p>
            </div>
            
            <!-- Error Message -->
            <div id="error-message" class="mt-6 hidden text-center bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg relative" role="alert">
                <strong class="font-bold">Oops!</strong>
                <span class="block sm:inline" id="error-text">Something went wrong.</span>
            </div>
        </div>
    </div>

    <script>
        const form = document.getElementById('upload-form');
        const fileInput = document.getElementById('file-input');
        const uploadBox = document.getElementById('upload-box');
        const submitButton = document.getElementById('submit-button');
        const loader = document.getElementById('loader');
        const resultSection = document.getElementById('result-section');
        const resultImage = document.getElementById('result-image');
        const downloadButton = document.getElementById('download-button');
        const errorMessage = document.getElementById('error-message');
        const errorText = document.getElementById('error-text');
        const imagePreviewContainer = document.getElementById('image-preview-container');
        const imagePreview = document.getElementById('image-preview');

        // Function to handle file selection
        const handleFileSelect = () => {
            const file = fileInput.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    imagePreview.src = e.target.result;
                    imagePreviewContainer.classList.remove('hidden');
                    uploadBox.classList.add('hidden');
                }
                reader.readAsDataURL(file);
                submitButton.disabled = false;
            }
        };

        // Trigger file input click
        uploadBox.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', handleFileSelect);
        
        // Handle drag and drop
        uploadBox.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadBox.classList.add('border-blue-500', 'bg-blue-50');
        });
        uploadBox.addEventListener('dragleave', () => {
            uploadBox.classList.remove('border-blue-500', 'bg-blue-50');
        });
        uploadBox.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadBox.classList.remove('border-blue-500', 'bg-blue-50');
            fileInput.files = e.dataTransfer.files;
            handleFileSelect();
        });

        // Initially disable the button
        submitButton.disabled = true;

        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            if (!fileInput.files || fileInput.files.length === 0) {
                showError("Please select a file first.");
                return;
            }

            const formData = new FormData();
            formData.append('file', fileInput.files[0]);

            // Reset UI
            hideError();
            resultSection.classList.add('hidden');
            loader.classList.remove('hidden');
            loader.classList.add('flex');
            submitButton.disabled = true;

            try {
                const response = await fetch('/remove_background', {
                    method: 'POST',
                    body: formData,
                });

                if (!response.ok) {
                    throw new Error(`Server error: ${response.statusText}`);
                }

                const blob = await response.blob();
                const url = URL.createObjectURL(blob);

                resultImage.src = url;
                downloadButton.href = url;
                resultSection.classList.remove('hidden');

            } catch (error) {
                console.error('Error:', error);
                showError("Failed to process the image. Please try again.");
            } finally {
                loader.classList.add('hidden');
                loader.classList.remove('flex');
                submitButton.disabled = false;
            }
        });
        
        function showError(message) {
            errorText.textContent = message;
            errorMessage.classList.remove('hidden');
        }

        function hideError() {
            errorMessage.classList.add('hidden');
        }
    </script>
</body>
</html>
"""

# Route for the main page
@app.route('/')
def index():
    """Renders the main upload page."""
    return render_template_string(HTML_TEMPLATE)

# Route to handle the background removal process
@app.route('/remove_background', methods=['POST'])
def remove_background():
    """Handles file upload, removes background, and returns the processed image."""
    if 'file' not in request.files:
        return 'No file part', 400
    
    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400

    if file:
        try:
            # Read the image file from the request
            input_image_bytes = file.read()
            
            # Use rembg to remove the background
            output_image_bytes = remove(input_image_bytes)
            
            # Return the processed image as a file attachment
            return send_file(
                io.BytesIO(output_image_bytes),
                mimetype='image/png',
                as_attachment=True,
                download_name='background-removed.png'
            )
        except Exception as e:
            # Log the error for debugging
            print(f"Error processing image: {e}")
            return "Error processing image", 500
            
    return "Invalid file", 400

# Main entry point for the application
if __name__ == '__main__':
    # Using port 8080 as it's a common choice for web services
    app.run(host='0.0.0.0', port=8080)
