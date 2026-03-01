import os
import json
import google.generativeai as genai
import requests
from flask import Flask, request, render_template, redirect, url_for
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)

# --- CONFIGURATION ---
API_KEY = 'AIzaSyA_ShNXMcHUak8l9QDs7aeEEqkyn7uK9E4' # <--- Your Key
genai.configure(api_key=API_KEY)

MODEL_NAME = 'gemini-flash-latest'
CONFIG_FILE = 'config.json'

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {"esp32_ip": "0.0.0.0"}

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)

def draw_bounding_boxes(image_path, boxes_data):
    try:
        img = Image.open(image_path)
        draw = ImageDraw.Draw(img)
        width, height = img.size
        detected_items = []

        for item in boxes_data:
            box_ymin = (item["ymin"] / 1000) * height
            box_xmin = (item["xmin"] / 1000) * width
            box_ymax = (item["ymax"] / 1000) * height
            box_xmax = (item["xmax"] / 1000) * width
            label = item["label"]

            draw.rectangle([box_xmin, box_ymin, box_xmax, box_ymax], outline="red", width=5)
            
            try:
                font = ImageFont.truetype("arial.ttf", 20)
            except:
                font = ImageFont.load_default()
            
            draw.rectangle([box_xmin, box_ymin - 25, box_xmin + 150, box_ymin], fill="red")
            draw.text((box_xmin + 5, box_ymin - 25), label, fill="white", font=font)
            
            detected_items.append(label)

        result_path = image_path.replace(".", "_detected.")
        img.save(result_path)
        return result_path, detected_items

    except Exception as e:
        return None, f"Drawing Error: {str(e)}"

def analyze_and_detect(image_path):
    model = genai.GenerativeModel(
        MODEL_NAME,
        generation_config={"response_mime_type": "application/json"}
    )
    img = Image.open(image_path)
    
    prompt = """
    Analyze this image of microplastics. Perform two tasks and return a JSON object.

    1. "report": Write a scientific analysis text (no markdown). 
       - Identify the morphology (shape).
       - Classify it as Fiber, Film, Fragment, Foam, or Pellet.
       - Describe characteristics (color, texture).
       - Predict the likely source.
    
    2. "boxes": Detect all plastic items. Return a list of bounding boxes.
       - Keys: ymin, xmin, ymax, xmax, label.
       - Scale: 0 to 1000.

    Output JSON Format:
    { "report": "...", "boxes": [...] }
    """
    
    try:
        response = model.generate_content([prompt, img])
        return json.loads(response.text)
    except Exception as e:
        return {"error": str(e)}

@app.route('/', methods=['GET', 'POST'])
def index():
    original_img = None
    processed_img = None
    item_list = []
    analysis_report = None
    error_msg = None
    
    if request.method == 'POST':
        if 'file' not in request.files: return "No file"
        file = request.files['file']
        if file.filename == '': return "No file"

        if not os.path.exists('static'): os.makedirs('static')
        filepath = os.path.join('static', file.filename)
        file.save(filepath)
        original_img = filepath

        ai_result = analyze_and_detect(filepath)
        
        if "error" in ai_result:
            error_msg = ai_result["error"]
        else:
            analysis_report = ai_result.get("report", "No report generated.")
            boxes = ai_result.get("boxes", [])
            
            if boxes:
                processed_path, items = draw_bounding_boxes(filepath, boxes)
                if processed_path:
                    processed_img = processed_path
                    item_list = items
            else:
                error_msg = "No microplastics detected in the image."

    return render_template('home.html', 
                           original_img=original_img, 
                           processed_img=processed_img, 
                           item_list=item_list, 
                           analysis_report=analysis_report, 
                           error_msg=error_msg)

@app.route('/setup', methods=['GET', 'POST'])
def setup():
    config = load_config()
    message = None
    if request.method == 'POST':
        new_ip = request.form.get('esp32_ip')
        config['esp32_ip'] = new_ip
        save_config(config)
        message = "Configuration saved successfully!"
    return render_template('setup.html', esp32_ip=config.get('esp32_ip'), message=message)

@app.route('/detect-live')
def detect_live():
    config = load_config()
    esp_ip = config.get('esp32_ip')
    snap_url = f"http://{esp_ip}/capture"
    
    try:
        response = requests.get(snap_url, timeout=10)
        if response.status_code == 200:
            if not os.path.exists('static'): os.makedirs('static')
            filename = f"live_snap_{os.urandom(4).hex()}.jpg"
            filepath = os.path.join('static', filename)
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            ai_result = analyze_and_detect(filepath)
            
            error_msg = None
            analysis_report = None
            processed_img = None
            item_list = []
            
            if "error" in ai_result:
                error_msg = ai_result["error"]
            else:
                analysis_report = ai_result.get("report", "No report generated.")
                boxes = ai_result.get("boxes", [])
                
                if boxes:
                    processed_path, items = draw_bounding_boxes(filepath, boxes)
                    if processed_path:
                        processed_img = processed_path
                        item_list = items
                else:
                    error_msg = "No microplastics detected in the image."
            
            return render_template('home.html', 
                                   original_img=filepath, 
                                   processed_img=processed_img, 
                                   item_list=item_list, 
                                   analysis_report=analysis_report, 
                                   error_msg=error_msg)
        else:
            return render_template('home.html', error_msg=f"Failed to fetch image from ESP32. Status: {response.status_code}")
    except Exception as e:
        return render_template('home.html', error_msg=f"ESP32 Connection Error: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True)