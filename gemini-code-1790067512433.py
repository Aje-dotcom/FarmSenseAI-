import os
from flask import Flask, request, jsonify
# Assuming custom modules for your specific models
from vision_model import analyze_leaf 
from rag_engine import get_farming_advice
from language_engine import translate_and_speak, transcribe_audio

app = Flask(__name__)

def agent_orchestrator(user_input, language="English", image_file=None):
    context = ""
    
    # Step 1: Tool Execution - Vision
    if image_file:
        diagnosis = analyze_leaf(image_file) # Returns e.g., {"disease": "Cassava Mosaic", "confidence": 0.92}
        context += f"The crop has been diagnosed with {diagnosis['disease']}. "
    
    # Step 2: Tool Execution - Knowledge Retrieval
    if user_input:
        advice = get_farming_advice(user_input + " " + context)
        context += f"Recommended action: {advice}. "
        
    # Step 3: LLM Generation (Formatting the final response)
    # This represents a call to a lightweight local LLM (e.g., Llama 3 8B quantized)
    final_response = generate_llm_response(
        prompt=f"Based on this context: {context}, advise the farmer safely and simply."
    )
    
    # Step 4: Translation & TTS
    if language != "English":
        final_response = translate_and_speak(final_response, target_lang=language)
        
    return final_response

@app.route('/api/chat', methods=['POST'])
def chat_endpoint():
    user_audio = request.files.get('audio')
    image_file = request.files.get('image')
    language = request.form.get('language', 'Pidgin')
    
    user_text = ""
    if user_audio:
        user_text = transcribe_audio(user_audio, language)
        
    response = agent_orchestrator(user_text, language, image_file)
    
    return jsonify({"response": response})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)