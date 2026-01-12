import os
from flask import Blueprint, request, jsonify, current_app, session
from tensorflow.keras.models import load_model
from utils.image_processing import allowed_file, prepare_image
from utils.validation import validate_leaf_rice_image
from utils.validation import validate_image
from utils.chat import get_chat_response
from config import LABELS
import numpy as np

# CONFIDENCE_THRESHOLD = 0.60 

api = Blueprint('api', __name__)

# Load TF model
try:
    model = load_model('./model/model_ini.keras')
    print("Model loaded successfully")
except Exception as e:
    print(f"Error loading model: {e}")
    model = None


@api.route('/detect', methods=['POST'])
def detect():

    if model is None:
        return jsonify({'error': 'Model tidak tersedia'}), 500

    if 'image' not in request.files:
        return jsonify({'error': 'Tidak ada gambar yang diunggah'}), 400

    file = request.files['image']
    if not file or not allowed_file(file.filename):
        return jsonify({'error': 'Format file tidak didukung'}), 400

    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename)

    try:
        file.save(filepath)

        # GPT Vision validation
        validation_result = validate_leaf_rice_image(filepath)
        validation_result = validation_result.strip().upper()
        print(f"[VALIDATION] {validation_result}")

        if validation_result == 'INVALID':
            return jsonify({
                'status': 'INVALID',
                'message': 'Gambar berada di luar ruang lingkup sistem deteksi penyakit padi'
            }), 400

        # if validation_result == 'UNCERTAIN':
        #     return jsonify({
        #         'status': 'UNCERTAIN',
        #         'message': 'Daun padi terdeteksi, namun gejala tidak cukup jelas'
        #     }), 422

        # Preprocess
        img_array = prepare_image(filepath)
        if img_array is None:
            raise ValueError("Gagal memproses gambar")

        # Prediction
        predictions = model.predict(img_array)
        confidence = float(np.max(predictions))           # CAST WAJIB
        predicted_class = str(LABELS[np.argmax(predictions)])  # CAST WAJIB

        print(f"[PREDICT] {predicted_class} ({confidence:.4f})")
        
        # final_label = validate_image(predicted_class, is_rice_leaf=True)
        # print(f"[FINAL LABEL] {final_label}")

        # Confidence threshold
        # if confidence < CONFIDENCE_THRESHOLD:
        #     return jsonify({
        #         'status': 'OUT_OF_SCOPE',
        #         'message': 'Penyakit tidak termasuk dalam kelas yang dikenali sistem',
        #         'confidence': confidence
        #     }), 422

        # Final detection (SESSION SAFE)
        detection = {
            'status': 'VALID',
            'label': predicted_class,
            'confidence': confidence
        }

        # SESSION AMAN
        history = session.get('detection_history', [])
        history.append(detection)
        session['detection_history'] = history
        session.modified = True

        return jsonify({'detections': [detection]}), 200

    except Exception as e:
        print("[ERROR DETECT]", repr(e))
        return jsonify({
            'status': 'ERROR',
            'message': 'Terjadi kesalahan saat memproses gambar',
            'detail': str(e)
        }), 500

    finally:
        if os.path.exists(filepath):
            os.remove(filepath)


@api.route('/get_response', methods=['POST'])
def get_response():
    """Handle chat response request"""
    try:
        data = request.json
        if not data:
            return jsonify({"reply": "Permintaan tidak valid"}), 400
            
        user_message = data.get('message')
        if not user_message:
            return jsonify({"reply": "Pesan tidak boleh kosong"}), 400
            
        detection_result = data.get('detection_result')
        
        # If detection_result is provided, store it as a single detection object
        if detection_result and isinstance(detection_result, dict) and 'detections' in detection_result:
            detection_obj = detection_result['detections'][0] if detection_result['detections'] else None
        else:
            detection_obj = None
        
        chat_response = get_chat_response(user_message, detection_obj)
        
        if not chat_response:
            return jsonify({"reply": "Maaf, tidak dapat memproses permintaan Anda saat ini"}), 500

        return jsonify({"reply": chat_response})

    except Exception as e:
        print(f"Error in get_response: {str(e)}")
        return jsonify({"reply": "Maaf, terjadi kesalahan dalam memproses permintaan Anda. Silakan coba lagi nanti."}), 500
# import os
# from flask import Blueprint, request, jsonify, current_app, session
# from tensorflow.keras.models import load_model
# from utils.image_processing import allowed_file, prepare_image

# # ⛔ NONAKTIF SEMENTARA (pakai GPT / OpenAI → biaya)
# # from utils.validation import validate_leaf_rice_image

# from utils.chat import get_chat_response
# from config import LABELS
# import numpy as np

# api = Blueprint('api', __name__)

# # Load TF model
# try:
#     model = load_model('./model/mbNetV3Dataset2NoBlur.keras')
#     print("Model loaded successfully")
# except Exception as e:
#     print(f"Error loading model: {e}")
#     model = None


# @api.route('/detect', methods=['POST'])
# def detect():
#     """Handle image detection request"""
#     if model is None:
#         return jsonify({'error': 'Model tidak tersedia'}), 500

#     if 'image' not in request.files:
#         return jsonify({'error': 'Tidak ada gambar yang diunggah'}), 400

#     file = request.files['image']

#     # Process valid image file
#     if file and allowed_file(file.filename):
#         try:
#             # Save uploaded file temporarily
#             filepath = os.path.join(
#                 current_app.config['UPLOAD_FOLDER'],
#                 file.filename
#             )
#             file.save(filepath)

#             # =====================================================
#             # ⛔ VALIDATION GPT / OPENAI (DINONAKTIFKAN SEMENTARA)
#             # =====================================================
#             # validation_result = validate_leaf_rice_image(filepath)
#             # print(f"Validation result: {validation_result}")

#             # =====================================================
#             # LANGSUNG PROSES GAMBAR TANPA VALIDASI GPT
#             # =====================================================

#             # Prepare image for prediction
#             img_array = prepare_image(filepath)
#             if img_array is None:
#                 raise ValueError("Gagal memproses gambar")

#             # Make prediction
#             predictions = model.predict(img_array)
#             confidence = float(np.max(predictions))
#             predicted_class = LABELS[np.argmax(predictions)]

#             # Create detection result
#             detection = {
#                 'label': predicted_class,
#                 'confidence': confidence
#                 # 'validation_status': validation_result  # ⛔ nonaktif
#             }

#             # Store detection result in session
#             if 'detection_history' not in session:
#                 session['detection_history'] = []
#             session['detection_history'].append(detection)
#             session.modified = True

#             result = {
#                 'detections': [detection]
#             }

#             # Clean up - remove temporary file
#             os.remove(filepath)

#             return jsonify(result)

#         except Exception as e:
#             if os.path.exists(filepath):
#                 os.remove(filepath)
#             return jsonify({
#                 'error': f'Error saat memproses gambar: {str(e)}'
#             }), 500

#     else:
#         return jsonify({'error': 'Format file tidak didukung'}), 400


# @api.route('/get_response', methods=['POST'])
# def get_response():
#     """Handle chat response request"""
#     try:
#         data = request.json
#         if not data:
#             return jsonify({"reply": "Permintaan tidak valid"}), 400

#         user_message = data.get('message')
#         if not user_message:
#             return jsonify({"reply": "Pesan tidak boleh kosong"}), 400

#         detection_result = data.get('detection_result')

#         # If detection_result is provided, store it as a single detection object
#         if (
#             detection_result
#             and isinstance(detection_result, dict)
#             and 'detections' in detection_result
#         ):
#             detection_obj = (
#                 detection_result['detections'][0]
#                 if detection_result['detections']
#                 else None
#             )
#         else:
#             detection_obj = None

#         chat_response = get_chat_response(user_message, detection_obj)

#         if not chat_response:
#             return jsonify({
#                 "reply": "Maaf, tidak dapat memproses permintaan Anda saat ini"
#             }), 500

#         return jsonify({"reply": chat_response})

#     except Exception as e:
#         print(f"Error in get_response: {str(e)}")
#         return jsonify({
#             "reply": (
#                 "Maaf, terjadi kesalahan dalam memproses permintaan Anda. "
#                 "Silakan coba lagi nanti."
#             )
#         }), 500

# @api.route('/detect', methods=['POST'])
# def detect():
#     """Handle image validation only: show valid, invalid, uncertain"""
#     if 'image' not in request.files:
#         return jsonify({'error': 'Tidak ada gambar yang diunggah'}), 400

#     file = request.files['image']

#     if file and allowed_file(file.filename):
#         filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename)
#         try:
#             # Save file sementara
#             file.save(filepath)

#             # VALIDASI INPUT
#             validation_status = validate_leaf_rice_image(filepath)
#             print(f"Validation status: {validation_status}")

#             # Return hanya status validasi
#             result = {
#                 'validation_status': validation_status
#             }

#             return jsonify(result)

#         except Exception as e:
#             return jsonify({'error': f'Error saat memproses gambar: {str(e)}'}), 500

#         finally:
#             if os.path.exists(filepath):
#                 os.remove(filepath)
#     else:
#         return jsonify({'error': 'Format file tidak didukung'}), 400
