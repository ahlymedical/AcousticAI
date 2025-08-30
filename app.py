import os
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import noisereduce as nr
from scipy.io import wavfile
from spleeter.separator import Separator
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# --- Configuration ---
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'flac', 'm4a'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER

# --- Create directories if they don't exist ---
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

# --- Initialize AI Models (do this once on startup) ---
# This is resource-intensive. It's better to load it once.
logging.info("Initializing Spleeter model...")
try:
    separator = Separator('spleeter:2stems')
    logging.info("Spleeter model initialized successfully.")
except Exception as e:
    logging.error(f"Failed to initialize Spleeter: {e}")
    separator = None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/separate', methods=['POST'])
def separate_audio():
    if separator is None:
        return jsonify({"error": "نموذج فصل الصوت غير متاح حاليًا."}), 500
        
    if 'audio_file' not in request.files:
        return jsonify({"error": "لم يتم إرسال أي ملف"}), 400
    
    file = request.files['audio_file']
    if file.filename == '':
        return jsonify({"error": "لم يتم اختيار أي ملف"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        logging.info(f"File saved to {filepath}")

        try:
            output_path = app.config['PROCESSED_FOLDER']
            logging.info(f"Starting separation for {filepath} into {output_path}")
            separator.separate_to_file(filepath, output_path)
            logging.info("Separation complete.")

            base_filename = os.path.splitext(filename)[0]
            vocals_path = os.path.join(output_path, base_filename, 'vocals.wav')
            accompaniment_path = os.path.join(output_path, base_filename, 'accompaniment.wav')
            
            # Check if files were created
            if not os.path.exists(vocals_path) or not os.path.exists(accompaniment_path):
                 raise Exception("Spleeter did not produce output files.")

            return jsonify({
                "files": {
                    "vocals": f"/processed/{base_filename}/vocals.wav",
                    "accompaniment": f"/processed/{base_filename}/accompaniment.wav"
                }
            })
        except Exception as e:
            logging.error(f"Error during separation: {e}")
            return jsonify({"error": f"حدث خطأ أثناء المعالجة: {str(e)}"}), 500

    return jsonify({"error": "نوع الملف غير مسموح به"}), 400


@app.route('/enhance', methods=['POST'])
def enhance_audio():
    if 'audio_file' not in request.files:
        return jsonify({"error": "لم يتم إرسال أي ملف"}), 400
    
    file = request.files['audio_file']
    if file.filename == '':
        return jsonify({"error": "لم يتم اختيار أي ملف"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        logging.info(f"File saved to {filepath}")
        
        try:
            # We must convert to WAV for processing with scipy
            # This requires ffmpeg to be installed in the Docker container
            import subprocess
            wav_filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_for_enhance.wav')
            subprocess.run(['ffmpeg', '-i', filepath, wav_filepath, '-y'], check=True)
            
            logging.info(f"Starting enhancement for {wav_filepath}")
            rate, data = wavfile.read(wav_filepath)
            
            # Perform noise reduction
            reduced_noise = nr.reduce_noise(y=data, sr=rate)
            
            output_filename = f"enhanced_{os.path.splitext(filename)[0]}.wav"
            output_filepath = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)
            wavfile.write(output_filepath, rate, reduced_noise)
            logging.info(f"Enhancement complete. File saved to {output_filepath}")

            return jsonify({
                "files": {
                    "enhanced": f"/processed/{output_filename}"
                }
            })
        except Exception as e:
            logging.error(f"Error during enhancement: {e}")
            return jsonify({"error": f"حدث خطأ أثناء المعالجة: {str(e)}"}), 500

    return jsonify({"error": "نوع الملف غير مسموح به"}), 400


@app.route('/processed/<path:filename>')
def processed_file(filename):
    return send_from_directory(app.config['PROCESSED_FOLDER'], filename, as_attachment=True)


if __name__ == '__main__':
    # Use 0.0.0.0 to be accessible from outside the container
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
