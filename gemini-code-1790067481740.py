import base64
from flask import Flask, request, jsonify
from vision_model import analyze_leaf
from rag_engine import get_farming_advice
from language_engine import transcribe_audio, text_to_speech_base64

app = Flask(__name__)

@app.route('/api/v2/farm_agent', methods=['POST'])
def multimodal_farm_agent():
    image_file = request.files.get('image')
    audio_file = request.files.get('audio')
    node_qr = request.form.get('node_qr')
    iot_telemetry = request.form.get('iot_telemetry') # Serialized JSON string
    language = request.form.get('language', 'Pidgin')
    
    diagnostic_context = []
    
    # 1. Ingest Hardware & IoT Context
    if node_qr:
        diagnostic_context.append(f"Linked IoT Node: {node_qr}")
    if iot_telemetry:
        diagnostic_context.append(f"Sensor Readings: {iot_telemetry}")

    # 2. Ingest Optical Inspection
    if image_file:
        diagnosis = analyze_leaf(image_file)
        diagnostic_context.append(
            f"Visual Diagnosis: {diagnosis['disease']} (Confidence: {diagnosis['confidence']:.2f})"
        )

    # 3. Transcribe Voice Ingestion
    user_query = ""
    if audio_file:
        user_query = transcribe_audio(audio_file, language=language)
        diagnostic_context.append(f"Farmer Query: {user_query}")

    # 4. Synthesize Advice & Produce Speaker Output
    combined_prompt = " | ".join(diagnostic_context)
    advice_text = get_farming_advice(combined_prompt, language=language)
    audio_response_b64 = text_to_speech_base64(advice_text, language=language)

    return jsonify({
        "status": "success",
        "advisory_text": advice_text,
        "audio_speaker_payload": audio_response_b64
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)