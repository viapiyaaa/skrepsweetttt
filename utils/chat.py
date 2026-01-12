# from flask import session
# from openai import OpenAI
# from config import OPENAI_API_KEY

# client = OpenAI(api_key=OPENAI_API_KEY)

# def get_chat_response(user_message, detection_result=None):
#     """Get response from ChatGPT with conversation history"""
#     try:
#         # Initialize or get conversation history from session
#         if 'conversation_history' not in session:
#             session['conversation_history'] = []
        
#         # Initialize or get detection history from session
#         if 'detection_history' not in session:
#             session['detection_history'] = []
        
#         # If there's a new detection result, add it to detection history
#         if detection_result and isinstance(detection_result, dict):
#             session['detection_history'].append(detection_result)
#             session.modified = True
            
#             # Get detailed information about the detected condition
#             label = detection_result.get('label', 'Tidak diketahui')
#             confidence = detection_result.get('confidence', 0)
#             validation_status = detection_result.get('validation_status', 'unknown')
            
#             # Create detailed detection message
#             detection_message = f"""
#             The latest detection result using our AI model shows:
#             - Type: {label}
#             - Confidence level: {confidence * 100:.1f}%
#             - Validation status: {validation_status}

#             Additional information:
#             - Supported classifications: Basal Cell Carcinoma, Squamous Cell Carcinoma, Melanoma, and Nevus
#             - This result is an initial prediction and should be confirmed by a dermatologist

#             """
            
#             session['conversation_history'].append({
#                 "role": "system",
#                 "content": detection_message
#             })
        
#         # Prepare messages for API call
#         messages = [
#             {
#                 "role": "system", 
#                 "content": """
#                 Role: You are an expert agricultural assistant specializing in rice leaf conditions, 
#                 including healthy leaves and diseases such as Bacterial Blight, Blast, Brown Spot, and Tungro.

#                 Guidelines:
#                 - Provide clear, evidence-based information about rice leaf conditions, including symptoms, causes, risk factors, prevention, early detection, and initial management for diseased leaves.
#                 - If the leaf is healthy, confirm that no visible disease is detected and provide guidance on crop monitoring and good agricultural practices.
#                 - Always mention that detection results come from an AI model and must be confirmed by direct field observation or a qualified agricultural expert.
#                 - Politely decline to answer questions unrelated to rice leaf health.
#                 - Keep responses concise, clear, and easy to understand.    
# """
#             }
#         ]
        
#         # Add information about all previous detections if any
#         if session.get('detection_history') and len(session['detection_history']) > 0:
#             detection_summary = "Ringkasan hasil deteksi sebelumnya:\n"
#             for idx, detection in enumerate(session['detection_history'], 1):
#                 label = detection.get('label', 'Tidak diketahui')
#                 confidence = detection.get('confidence', 0)
#                 validation_status = detection.get('validation_status', 'unknown')
#                 detection_summary += f"{idx}. Jenis: {label}, Kepercayaan: {confidence * 100:.1f}%, Status: {validation_status}\n"
            
#             messages.append({
#                 "role": "system",
#                 "content": detection_summary
#             })
        
#         # Add conversation history
#         messages.extend(session['conversation_history'])
        
#         # Add current user message
#         messages.append({
#             "role": "user",
#             "content": user_message
#         })
        
#         # Get response from GPT-4o
#         try:
#             response = client.chat.completions.create(
#                 model="gpt-4o",
#                 messages=messages,
#                 max_tokens=1000,
#                 temperature=0.5
#             )
            
#             if not response or not response.choices or not response.choices[0].message:
#                 raise Exception("Invalid response from GPT-4o")
                
#             # Get assistant's response
#             assistant_response = response.choices[0].message.content.strip()
            
#             if not assistant_response:
#                 raise Exception("Empty response from GPT-4o")
            
#             # Update conversation history
#             session['conversation_history'].append({
#                 "role": "user",
#                 "content": user_message
#             })
#             session['conversation_history'].append({
#                 "role": "assistant",
#                 "content": assistant_response
#             })
            
#             # Keep only last 10 messages to prevent session from getting too large
#             if len(session['conversation_history']) > 10:
#                 session['conversation_history'] = session['conversation_history'][-10:]
            
#             # Ensure session changes are saved
#             session.modified = True
            
#             return assistant_response
            
#         except Exception as api_error:
#             print(f"API Error: {str(api_error)}")
#             # Return a fallback response if API call fails
#             return "Maaf, saya mengalami kesalahan dalam memproses permintaan Anda. Silakan coba lagi nanti."
        
#     except Exception as e:
#         print(f"Error in get_chat_response: {str(e)}")
#         return "Maaf, terjadi kesalahan dalam sistem. Silakan coba lagi nanti." 

from flask import session
from openai import OpenAI
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

def get_chat_response(user_message, detection_result=None):
    try:
        # Inisialisasi session
        if 'conversation_history' not in session:
            session['conversation_history'] = []
        if 'detection_history' not in session:
            session['detection_history'] = []

        # Simpan deteksi terbaru sebagai dict (tanpa summary)
        if detection_result and isinstance(detection_result, dict):
            session['detection_history'].append(detection_result)
            # Batasi max 5 deteksi terakhir
            session['detection_history'] = session['detection_history'][-5:]
            session.modified = True

        # Batasi conversation history max 10
        session['conversation_history'] = session['conversation_history'][-10:]

        # System prompt
        system_prompt = """
        Role: You are an expert agricultural assistant specializing in rice leaf conditions.

        Guidelines:
        - Focus only on rice leaf conditions: healthy leaves or diseases including Bacterial Blight, Blast, Brown Spot, and Tungro.
        - Explain the detected condition:
          - If disease → describe symptoms, causes, prevention, early detection, and initial management.
          - If healthy → confirm no visible disease and provide monitoring tips and good practices.
        - Always mention AI detection is preliminary and must be confirmed by a qualified agricultural expert.
        - Do not answer questions unrelated to rice leaf health.
        - Keep responses concise, clear, and easy to understand.
        """

        messages = [{"role": "system", "content": system_prompt}]

        # Masukkan setiap deteksi sebagai sistem message
        for det in session['detection_history']:
            # konversi dict ke string langsung di sini
            det_message = f"Detection result: Type={det.get('label', 'Unknown')}, Confidence={det.get('confidence', 0)*100:.1f}%, Status={det.get('validation_status', 'unknown')}"
            messages.append({"role": "system", "content": det_message})

        # Tambahkan conversation history
        messages.extend(session['conversation_history'])

        # Tambahkan pesan user
        messages.append({"role": "user", "content": user_message})

        # Panggil GPT
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=500,  # lebih aman
            temperature=0.5
        )

        assistant_response = response.choices[0].message.content.strip()

        # Update conversation history
        session['conversation_history'].append({"role": "user", "content": user_message})
        session['conversation_history'].append({"role": "assistant", "content": assistant_response})
        session.modified = True

        return assistant_response

    except Exception as e:
        print(f"Error in get_chat_response: {str(e)}")
        return "Maaf, terjadi kesalahan dalam sistem. Silakan coba lagi nanti."






# from pyexpat.errors import messages
# from flask import session
# from openai import OpenAI
# from config import OPENAI_API_KEY

# client = OpenAI(api_key=OPENAI_API_KEY)

# def get_chat_response(user_message, detection_result=None):
#     """Get response from ChatGPT with conversation history"""
#     try:
#         # Initialize or get conversation history from session
#         if 'conversation_history' not in session:
#             session['conversation_history'] = []
        
#         # # Initialize or get detection history from session
#         # if 'detection_history' not in session:
#         #     session['detection_history'] = []
        
#         # # If there's a new detection result, add it to detection history
#         # if detection_result and isinstance(detection_result, dict):
#         #     session['detection_history'].append(detection_result)
#         #     session.modified = True
        
#         # Simpan SATU hasil deteksi terakhir saja
#         if detection_result and isinstance(detection_result, dict):
#             session['last_detection'] = detection_result
#             session.modified = True
       
            
#             # Get detailed information about the detected condition
#             label = detection_result.get('label', 'Tidak diketahui')
#             confidence = detection_result.get('confidence', 0)
#             validation_status = detection_result.get('validation_status', 'unknown')
            
#             # # Create detailed detection message
#             # detection_message = f"""
#             # The latest detection result using our AI model shows:
#             # - Type: {label}
#             # - Confidence level: {confidence * 100:.1f}%
#             # - Validation status: {validation_status}

#             # Additional information:
#             # - Supported classifications: Bacterial blight, Blast, Brown spot, Tungro, Healthy
#             # - This result is an initial prediction and should be confirmed by a plant pathology expert.
#             # - If the model’s predicted  {label} is Bacterial blight or Tungro, please provide additional information, specifically:
#             # Whether the plant shows stunting (yes/no)

#             # """
           
#             # Create detailed detection message
#             extra_instructions = ""
#             if label == "Tungro":
#                 extra_instructions = (
#                     "\n- Catatan Penting: Penyakit ini sering mirip dengan Bacterial Blight. "
#                     "WAJIB tanyakan apakah tanaman terlihat KERDIL untuk memastikannya."
#                     )
#             elif label == "Bacterialblight":
#                 extra_instructions = (
#                     "\n- Catatan Penting: Penyakit ini sering mirip dengan Tungro. "
#                     "WAJIB tanyakan apakah ada garis bergelombang/basah di pinggir daun atau cairan kuning."
#                     )
                
#             detection_message = f"""
#             The latest detection result using our AI model shows:
#             - Type: {label}
#             - Confidence level: {confidence * 100:.1f}%
#             - Validation status: {validation_status}
#             - Current Detection Result: {label}.{extra_instructions}
                
#             Additional information:
#             - {extra_instructions if extra_instructions else "Provide general education and treatment for " + label + "."}
#             - Always remind the user that this is an AI prediction and needs expert confirmation.
#             """

            
#             session['conversation_history'].append({
#                 "role": "system",
#                 "content": detection_message
#             })
        
#         # Prepare messages for API call
#         messages = [
#             {
#                 "role": "system", 
#                 "content": """
#                 Role: You are an expert plant pathology assistant specializing in the early detection of rice leaf diseases, 
#                 particularly bacterial leaf blight, blast, brown spot, and tungro.
#                 Current Detection Result: {label}.{extra_instructions}

#                 Operational Guidelines:
#                 1. DISEASE INFORMATION: Provide clear, evidence-based information regarding symptoms, causes (fungal/bacterial/viral), risk factors, prevention, and integrated pest management (IPM) for: Bacterial Leaf Blight (HDB), Blast, Brown Spot, and Tungro.
                
#                 2. THE "DETECTIVE" PROTOCOL (Crucial):
#                 - If the CNN model detects 'Tungro' or 'Bacterial blight', you are STRICTLY PROHIBITED from giving immediate chemical solutions.
#                 - You must act as a detective to resolve visual ambiguity:
#                     a. For Tungro: Mandatorily ask if the plant shows significant STUNTING (abnormally short height).
#                     b. For Bacterial Blight: Mandatorily ask if there are wavy, water-soaked streaks along the leaf margins or yellowish bacterial ooze.
#                 - Use the user's confirmation to refine the final diagnosis.

#                 3. HIGH-CONFIDENCE PATHOLOGY (Blast & Brown Spot):
#                 - For 'Blast' or 'Brown Spot', you may proceed directly to technical control measures and management steps, as the model's visual accuracy for these categories is significantly higher.

#                 4. SAFETY & LIMITATIONS:
#                 - Always state that these results are initial AI predictions and MUST be confirmed by a local Plant Pathology Expert or Agricultural Extension Officer (PPL).
#                 - Offer initial cultural or biological guidance (e.g., water management, field sanitation) without replacing professional expertise.
#                 - Politely decline any questions unrelated to rice leaf diseases.

#                 5. CONTEXT AWARENESS:
#                 - Always refer to the latest CNN detection results and the conversation history to ensure consistency. Do not give generalized advice if a specific disease has already been detected.

#                 Goal: To educate farmers, ensure accurate early detection, and prevent the misuse of pesticides by confirming symptoms before recommendation.
#                 """
#             }
#         ]
        
#         # Add information about all previous detections if any
#         if session.get('detection_history') and len(session['detection_history']) > 0:
#             detection_summary = "Ringkasan hasil deteksi sebelumnya:\n"
#             for idx, detection in enumerate(session['detection_history'], 1):
#                 label = detection.get('label', 'Tidak diketahui')
#                 confidence = detection.get('confidence', 0)
#                 validation_status = detection.get('validation_status', 'unknown')
#                 detection_summary += f"{idx}. Jenis: {label}, Kepercayaan: {confidence * 100:.1f}%, Status: {validation_status}\n"
            
#             messages.append({
#                 "role": "system",
#                 "content": detection_summary
#             })
        
#         # Add conversation history
#         messages.extend(session['conversation_history'])
        
#         # NEW BLOCK (fokus penyakit)
        
#         if session.get('detection_history'):
#             last_detection = session['detection_history'][-1]
#             last_label = last_detection.get('label', 'Tidak diketahui')
#         else:
#             last_label = None
            
#         if last_label:
#             messages.append({
#                 "role": "system",
#                 "content": (
#                     f"Penyakit terakhir yang terdeteksi oleh model adalah: {last_label}. "
#                     f"Jika pengguna menanyakan gejala, penyebab, pencegahan, atau pengendalian, "
#                     f"jawablah SECARA SPESIFIK hanya untuk penyakit {last_label}. "
#                     f"Jangan memberikan pencegahan umum untuk semua penyakit padi."
#                     )
#                 })
        
#         # Add current user message
#         messages.append({
#             "role": "user",
#             "content": user_message
#         })
        
#         # Get response from GPT-4o
#         try:
#             response = client.chat.completions.create(
#             model="gpt-4o",
#             messages=messages,
#             max_tokens=700,   # 🔒 AMAN
#             temperature=0.5
#         )        
#             if not response or not response.choices or not response.choices[0].message:
#                 raise Exception("Invalid response from GPT-4o")
                
#             # Get assistant's response
#             assistant_response = response.choices[0].message.content.strip()
            
#             if not assistant_response:
#                 raise Exception("Empty response from GPT-4o")
            
#             # Update conversation history
#             session['conversation_history'].append({
#                 "role": "user",
#                 "content": user_message
#             })
#             session['conversation_history'].append({
#                 "role": "assistant",
#                 "content": assistant_response
#             })
            
#             # Keep only last 10 messages to prevent session from getting too large
#             if len(session['conversation_history']) > 10:
#                 session['conversation_history'] = session['conversation_history'][-10:]
            
#             # Ensure session changes are saved
#             session.modified = True
            
#             return assistant_response
            
#         except Exception as api_error:
#             print(f"API Error: {str(api_error)}")
#             # Return a fallback response if API call fails
#             return "Maaf, saya mengalami kesalahan dalam memproses permintaan Anda. Silakan coba lagi nanti."
        
#     except Exception as e:
#         print(f"Error in get_chat_response: {str(e)}")
#         return "Maaf, terjadi kesalahan dalam sistem. Silakan coba lagi nanti." 



# from flask import session
# from openai import OpenAI
# from config import OPENAI_API_KEY

# client = OpenAI(api_key=OPENAI_API_KEY)

# def get_chat_response(user_message, detection_result=None):
#     try:
#         # === INIT HISTORY ===
#         if 'chat_history' not in session:
#             session['chat_history'] = []

#         # === SIMPAN DETEKSI TERAKHIR ===
#         if detection_result:
#             session['last_detection'] = detection_result
#             session.modified = True

#         last_detection = session.get('last_detection', {})
#         label = last_detection.get('label', 'Tidak diketahui')
#         confidence = last_detection.get('confidence', 0)

#        # === MENYUSUN EXTRA INSTRUCTION SPESIFIK ===
#         # Hanya untuk Tungro dan Bacterial Blight
#         validation_needed = ["Tungro", "Bacterial Blight"]
        
#         extra_instruction = ""
#         if label in validation_needed:
#             extra_instruction = (
#                 "WAJIB: Karena hasil deteksi adalah {label}, Anda DILARANG memberi solusi dulu. "
#                 "Sebutkan label dan confidence, lalu tanyakan: 'Apakah tanaman padi Anda terlihat kerdil "
#                 "secara signifikan dibanding tanaman sehat sekitarnya?'"
#             )
#         else:
#             # Untuk Blast dan Brown Spot
#             extra_instruction = "Anda boleh langsung menjelaskan detail penyakit dan cara penanganannya."
            
            
#         # === SYSTEM PROMPT ===
#         system_prompt = f"""
#         Role: You are an expert plant pathology assistant specializing in rice leaf diseases (Bacterial Leaf Blight, Blast, Brown Spot, and Tungro).
#         Current Detection Result: {label} ({confidence*100:.1f}%).

#         OPERATIONAL GUIDELINES:
#         1. VALIDATION RULE:
#            {extra_instruction}
        
#         2. LOGIKA KROSCEK (Hanya jika label Tungro/Bacterial Blight):
#            - Jika user menjawab 'Ya' (Kerdil) -> Prioritaskan diagnosa sebagai Tungro.
#            - Jika user menjawab 'Tidak' (Tidak Kerdil) -> Prioritaskan diagnosa sebagai Bacterial Blight (HDB).
#         3. DISEASE INFORMATION: Provide clear, evidence-based info on symptoms, causes, and IPM.
        
       

#         4. HIGH-CONFIDENCE PATHOLOGY:
#         - For 'Blast' or 'Brown Spot', you may proceed directly to technical control measures.

#         5. SAFETY & LIMITATIONS:
#         - Always state this is an AI prediction and MUST be confirmed by a local Agricultural Extension Officer (PPL).
#         - Politely decline non-rice disease questions.
#         - Answer in Indonesian.

#         6. CONTEXT AWARENESS:
#         - Refer to the latest CNN result: {label}. Use history to ensure consistency.
#         """

#         messages = [{"role": "system", "content": system_prompt}]

#         # === HISTORY TERBATAS ===
#         messages.extend(session['chat_history'][-4:])

#         # === USER INPUT ===
#         messages.append({"role": "user", "content": user_message})

#         response = client.chat.completions.create(
#             model="gpt-4o",
#             messages=messages,
#             max_tokens=700,
#             temperature=0.3 # Diturunkan ke 0.3 agar lebih patuh pada protokol
#         )

#         reply = response.choices[0].message.content.strip()

#         # === UPDATE HISTORY ===
#         session['chat_history'].append({"role": "user", "content": user_message})
#         session['chat_history'].append({"role": "assistant", "content": reply})
#         session['chat_history'] = session['chat_history'][-6:]
#         session.modified = True

#         return reply

#     except Exception as e:
#         print("Chat error:", e)
#         return "Terjadi kesalahan dalam sistem. Silakan coba kembali."