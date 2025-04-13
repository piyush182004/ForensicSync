from ultralytics import YOLO
import ollama
import cv2
import numpy as np

try:
    yolo_model = YOLO('yolov8n.pt')
except Exception as e:
    yolo_model = None
    print(f"Warning: Could not load YOLO model: {str(e)}")

def analyze_crime_scene(crime_scene_file, form_data):
    """Analyze crime scene image and generate a structured forensic report."""
    
    # Initialize detected objects list
    detected_objects = []

    if yolo_model is None:
        detected_objects.append("None detected (YOLO model unavailable)")
    else:
        try:
            # Make sure we're at the start of the file
            crime_scene_file.seek(0)
            img_bytes = crime_scene_file.read()
            img = cv2.imdecode(np.frombuffer(img_bytes, np.uint8), cv2.IMREAD_COLOR)
            
            if img is None:
                detected_objects.append("Invalid image")
            else:
                results = yolo_model(img)
                if results and len(results) > 0 and hasattr(results[0], 'boxes') and len(results[0].boxes) > 0:
                    detected_objects = [yolo_model.names[int(box.cls)] for box in results[0].boxes]
                else:
                    detected_objects.append("No objects detected")
        except Exception as e:
            detected_objects.append(f"Error detecting objects: {str(e)}")

    try:
        # Check if Ollama is running
        try:
            # Try to use llava model
            model_to_use = 'llava-phi3:3.8b'
            # Fall back to a simpler model if llava isn't available
            fallback_model = 'llama2'
            
            response = None
            try:
                response = ollama.chat(
                    model=model_to_use, 
                    messages=[{
                        'role': 'user',
                        'content': f"""Generate a full professional 1000 words atleast forensic crime report based on the following details and it must contains suggestions to help police and officials to trace out criminal ,suggest loopholes and etc:
**Crime Scene Details:**
- Date/Time: {form_data['incident_datetime']}
- Evidence Found: {form_data['evidence_found']}
- Forced Entry: {form_data['forced_entry']}
- Eyewitness Accounts: {form_data['eyewitness']}
- Motives: {form_data['motives']}
- Unusual Items: {form_data['unusual_items']}
- Time of Death: {form_data['time_of_death']}
- Tracks/Prints: {form_data['tracks']}
- Notes: {form_data['notes']}
- Additional Details: {form_data['additional_details']}

**Objects Detected:** {', '.join(detected_objects)}

Please provide a detailed forensic analysis."""
                    }],
                    options={
                        'temperature': 0.7,
                        'num_predict': 1024,
                        'top_k': 40
                    }
                )
            except Exception as e:
                print(f"Error with primary model: {str(e)}, trying fallback")
                # Try fallback model
                response = ollama.chat(
                    model=fallback_model, 
                    messages=[{
                        'role': 'user',
                        'content': f"""Generate a forensic crime report based on the following details:

**Crime Scene Details:**
- Date/Time: {form_data['incident_datetime']}
- Evidence Found: {form_data['evidence_found']}
- Forced Entry: {form_data['forced_entry']}
- Eyewitness Accounts: {form_data['eyewitness']}
- Motives: {form_data['motives']}
- Unusual Items: {form_data['unusual_items']}
- Time of Death: {form_data['time_of_death']}
- Tracks/Prints: {form_data['tracks']}
- Notes: {form_data['notes']}
- Additional Details: {form_data['additional_details']}

**Objects Detected:** {', '.join(detected_objects)}

Please provide a detailed forensic analysis."""
                    }],
                    options={
                        'temperature': 0.7
                    }
                )
            
            if response and 'message' in response and 'content' in response['message']:
                return response['message']['content']
            else:
                return "Error: Received invalid response from the AI model."
                
        except Exception as main_error:
            return f"""
**Crime Scene Analysis Report**

**Note: AI-powered analysis unavailable**
Error connecting to Ollama service: {str(main_error)}

**Manual Analysis Required**

**Evidence Summary:**
- Date/Time of Incident: {form_data['incident_datetime']}
- Evidence Found: {form_data['evidence_found']}
- Signs of Forced Entry: {form_data['forced_entry']}
- Eyewitness Accounts: {form_data['eyewitness']}
- Potential Motives: {form_data['motives']}
- Unusual Items Present: {form_data['unusual_items']}
- Estimated Time of Death: {form_data['time_of_death']}
- Tracks/Prints Found: {form_data['tracks']}
- Additional Notes: {form_data['notes']}
- Additional Details: {form_data['additional_details']}

**Objects Detected in Scene:** {', '.join(detected_objects)}

This case requires manual forensic analysis. Please ensure Ollama service is running and try again.
"""
    except Exception as e:
        return f"Error generating crime report: {str(e)}"
