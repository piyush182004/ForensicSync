from flask import Flask, render_template, request, send_file, redirect, url_for
from fingerprint import analyze_fingerprint
from crime_scene import analyze_crime_scene
import json
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from io import BytesIO
import random
import shutil

app = Flask(__name__)

# Ensure upload directory exists
UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure persons.json exists
if not os.path.exists('persons.json'):
    default_persons = [{"name": "Unknown Suspect", "age": 0, "address": "N/A"}]
    with open('persons.json', 'w') as f:
        json.dump(default_persons, f)

with open('persons.json', 'r') as f:
    persons = json.load(f)

@app.route('/')
def front():
    """Render the front page."""
    return render_template('front.html')

@app.route('/analyze_page', methods=['GET', 'POST'])
def index():
    """Render the analysis input page with image preview."""
    if request.method == 'POST':
        # Validate file uploads
        if 'crimeScene' not in request.files or 'fingerprint' not in request.files:
            return redirect(url_for('index', error="Missing file uploads"))

        crime_scene = request.files['crimeScene']
        fingerprint = request.files['fingerprint']

        if not crime_scene.filename or not fingerprint.filename:
            return redirect(url_for('index', error="No files selected"))

        # Save files temporarily
        crime_scene_path = os.path.join(app.config['UPLOAD_FOLDER'], 'crime_scene.jpg')
        fingerprint_path = os.path.join(app.config['UPLOAD_FOLDER'], 'fingerprint.jpg')
        crime_scene.save(crime_scene_path)
        fingerprint.save(fingerprint_path)

        # Redirect to index with image paths
        return redirect(url_for('index', crime_scene='uploads/crime_scene.jpg', fingerprint='uploads/fingerprint.jpg'))

    # GET request: Display form with optional image previews
    crime_scene = request.args.get('crime_scene')
    fingerprint = request.args.get('fingerprint')
    error = request.args.get('error')
    return render_template('index.html', crime_scene=crime_scene, fingerprint=fingerprint, error=error)

@app.route('/analyze', methods=['POST'])
def analyze():
    """Process evidence and generate a detailed report."""
    try:
        # Check if we have file paths from previously uploaded images
        if 'crime_scene_path' in request.form and 'fingerprint_path' in request.form:
            crime_scene_path = request.form.get('crime_scene_path')
            fingerprint_path = request.form.get('fingerprint_path')
            
            # Open the files for analysis
            crime_scene_file_path = os.path.join('static', crime_scene_path)
            fingerprint_file_path = os.path.join('static', fingerprint_path)
            
            if not os.path.exists(crime_scene_file_path) or not os.path.exists(fingerprint_file_path):
                return render_template('report.html', report={
                    'error': "Image files not found. Please upload again.",
                    'date_generated': datetime.now().strftime('%d-%m-%Y %H:%M:%S')
                })
            
            # Use the files for analysis
            crime_scene_file = open(crime_scene_file_path, 'rb')
            fingerprint_file = open(fingerprint_file_path, 'rb')
        else:
            # Otherwise, use newly uploaded files
            if 'crimeScene' not in request.files or 'fingerprint' not in request.files:
                return render_template('report.html', report={
                    'error': "Missing required files. Please upload both crime scene and fingerprint images.",
                    'date_generated': datetime.now().strftime('%d-%m-%Y %H:%M:%S')
                })
            
            crime_scene_file = request.files['crimeScene']
            fingerprint_file = request.files['fingerprint']
            
            # Save the uploaded files
            crime_scene_path = 'uploads/crime_scene.jpg'
            fingerprint_path = 'uploads/fingerprint.jpg'
            os.makedirs(os.path.join('static', 'uploads'), exist_ok=True)
            crime_scene_file.save(os.path.join('static', crime_scene_path))
            fingerprint_file.save(os.path.join('static', fingerprint_path))
            
            # Re-open the saved files for analysis
            crime_scene_file = open(os.path.join('static', crime_scene_path), 'rb')
            fingerprint_file = open(os.path.join('static', fingerprint_path), 'rb')

        # Collect form data with defaults
        form_data = {
            'incident_datetime': request.form.get('incident_datetime', 'Unknown'),
            'evidence_found': request.form.get('evidence_found', 'None provided'),
            'forced_entry': request.form.get('forced_entry', 'Unknown'),
            'eyewitness': request.form.get('eyewitness', 'None'),
            'motives': request.form.get('motives', 'Unknown'),
            'unusual_items': request.form.get('unusual_items', 'None'),
            'time_of_death': request.form.get('time_of_death', 'Unknown'),
            'tracks': request.form.get('tracks', 'None'),
            'notes': request.form.get('notes', 'None'),
            'additional_details': request.form.get('additional_details', 'None')
        }

        # Analyze fingerprint and crime scene
        blood_group = analyze_fingerprint(fingerprint_file)
        suspect = random.choice(persons)
        crime_analysis = analyze_crime_scene(crime_scene_file, form_data)
        
        # Close the file objects after analysis
        crime_scene_file.close()
        fingerprint_file.close()

        report_data = {
            'blood_group': blood_group,
            'suspect': suspect,
            'crime_analysis': crime_analysis,
            'form_data': form_data,
            'date_generated': datetime.now().strftime('%d-%m-%Y %H:%M:%S'),
            'crime_scene_img': crime_scene_path,
            'fingerprint_img': fingerprint_path
        }

        return render_template('report.html', report=report_data)
    except Exception as e:
        return render_template('report.html', report={
            'error': f"An error occurred during analysis: {str(e)}",
            'date_generated': datetime.now().strftime('%d-%m-%Y %H:%M:%S')
        })

@app.route('/download_pdf', methods=['POST'])
def download_pdf():
    """Generate and download the report as a PDF."""
    try:
        report_data = {
            'blood_group': request.form.get('blood_group', 'N/A'),
            'suspect': {
                'name': request.form.get('suspect_name', 'Unknown'),
                'age': int(request.form.get('suspect_age', 0)),
                'address': request.form.get('suspect_address', 'N/A')
            },
            'crime_analysis': request.form.get('crime_analysis', 'No analysis available'),
            'form_data': {
                'incident_datetime': request.form.get('incident_datetime', 'Unknown'),
                'evidence_found': request.form.get('evidence_found', 'None provided'),
                'forced_entry': request.form.get('forced_entry', 'Unknown'),
                'eyewitness': request.form.get('eyewitness', 'None'),
                'motives': request.form.get('motives', 'Unknown'),
                'unusual_items': request.form.get('unusual_items', 'None'),
                'time_of_death': request.form.get('time_of_death', 'Unknown'),
                'tracks': request.form.get('tracks', 'None'),
                'notes': request.form.get('notes', 'None')
            },
            'date_generated': request.form.get('date_generated', 'Unknown')
        }

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle('Title', fontSize=24, textColor=colors.red, alignment=1, spaceAfter=20)
        heading_style = ParagraphStyle('Heading', fontSize=16, textColor=colors.black, spaceAfter=10)
        body_style = ParagraphStyle('Body', fontSize=12, textColor=colors.black, spaceAfter=8, leading=14)

        story = []
        story.append(Paragraph("ForensicSync Crime Report", title_style))
        story.append(Paragraph(f"Generated on: {report_data['date_generated']}", styles['Normal']))
        story.append(Spacer(1, 20))

        story.append(Paragraph("Fingerprint Analysis", heading_style))
        story.append(Paragraph(f"<b>Blood Group:</b> {report_data['blood_group']}", body_style))
        story.append(Paragraph(f"<b>Suspect:</b> {report_data['suspect']['name']}, Age: {report_data['suspect']['age']}, Address: {report_data['suspect']['address']}", body_style))
        story.append(Spacer(1, 20))

        story.append(Paragraph("Crime Scene Analysis", heading_style))
        story.append(Paragraph(report_data['crime_analysis'].replace('\n', '<br/>'), body_style))
        story.append(Spacer(1, 20))

        story.append(Paragraph("Investigation Details", heading_style))
        details = [
            f"<b>Incident Date & Time:</b> {report_data['form_data']['incident_datetime']}",
            f"<b>Evidence Found:</b> {report_data['form_data']['evidence_found']}",
            f"<b>Signs of Forced Entry:</b> {report_data['form_data']['forced_entry']}",
            f"<b>Eyewitness Accounts:</b> {report_data['form_data']['eyewitness']}",
            f"<b>Potential Motives:</b> {report_data['form_data']['motives']}",
            f"<b>Unusual Items or Messages:</b> {report_data['form_data']['unusual_items']}",
            f"<b>Estimated Time of Death:</b> {report_data['form_data']['time_of_death']}",
            f"<b>Tracks or Prints:</b> {report_data['form_data']['tracks']}",
            f"<b>Additional Notes:</b> {report_data['form_data']['notes']}"
        ]
        for detail in details:
            story.append(Paragraph(detail, body_style))
        
        doc.build(story)
        buffer.seek(0)
        return send_file(buffer, as_attachment=True, download_name='ForensicSync_Crime_Report.pdf', mimetype='application/pdf')
    except Exception as e:
        return f"Error generating PDF: {str(e)}", 500

@app.route('/dashboard')
def dashboard():
    """Render the dashboard page with statistics and visualizations."""
    # Sample statistics data
    stats = {
        'total_cases': 158,
        'solved_cases': 103,
        'pending_cases': 42,
        'critical_cases': 13
    }
    
    # Sample recent cases
    recent_cases = [
        {'id': 'CS-2023-089', 'date': '2023-10-15', 'type': 'Homicide', 'status': 'Active', 'status_class': 'status-active'},
        {'id': 'CS-2023-088', 'date': '2023-10-14', 'type': 'Burglary', 'status': 'Solved', 'status_class': 'status-solved'},
        {'id': 'CS-2023-087', 'date': '2023-10-12', 'type': 'Assault', 'status': 'Active', 'status_class': 'status-active'},
        {'id': 'CS-2023-086', 'date': '2023-10-10', 'type': 'Theft', 'status': 'Solved', 'status_class': 'status-solved'},
        {'id': 'CS-2023-085', 'date': '2023-10-08', 'type': 'Fraud', 'status': 'Pending', 'status_class': 'status-pending'}
    ]
    
    return render_template('dashboard.html', stats=stats, recent_cases=recent_cases)

@app.route('/map')
def crime_map():
    """Render the crime map page with location data."""
    # Sample incident data
    incidents = [
        {'date': '2023-10-15', 'location': 'Connaught Place, New Delhi', 'type': 'Theft', 'status': 'Active', 'status_class': 'status-active'},
        {'date': '2023-10-14', 'location': 'Saket, New Delhi', 'type': 'Assault', 'status': 'Solved', 'status_class': 'status-solved'},
        {'date': '2023-10-13', 'location': 'Dwarka, New Delhi', 'type': 'Burglary', 'status': 'Active', 'status_class': 'status-active'},
        {'date': '2023-10-12', 'location': 'Rohini, New Delhi', 'type': 'Fraud', 'status': 'Pending', 'status_class': 'status-pending'},
        {'date': '2023-10-11', 'location': 'Lajpat Nagar, New Delhi', 'type': 'Theft', 'status': 'Solved', 'status_class': 'status-solved'}
    ]
    
    return render_template('map.html', incidents=incidents)

@app.route('/cases')
def cases():
    """Show the cases page with all case files."""
    # Sample statistics data 
    stats = {
        'total_cases': 158,
        'solved_cases': 103, 
        'pending_cases': 42,
        'critical_cases': 13
    }
    
    # Sample cases data
    sample_cases = [
        {'id': 'CS-2023-089', 'date': '2023-10-15', 'type': 'Homicide', 'status': 'Active', 'status_class': 'status-active'},
        {'id': 'CS-2023-088', 'date': '2023-10-14', 'type': 'Burglary', 'status': 'Solved', 'status_class': 'status-solved'},
        {'id': 'CS-2023-087', 'date': '2023-10-12', 'type': 'Assault', 'status': 'Active', 'status_class': 'status-active'},
        {'id': 'CS-2023-086', 'date': '2023-10-10', 'type': 'Theft', 'status': 'Solved', 'status_class': 'status-solved'},
        {'id': 'CS-2023-085', 'date': '2023-10-08', 'type': 'Fraud', 'status': 'Pending', 'status_class': 'status-pending'},
        {'id': 'CS-2023-084', 'date': '2023-10-07', 'type': 'Robbery', 'status': 'Active', 'status_class': 'status-active'},
        {'id': 'CS-2023-083', 'date': '2023-10-05', 'type': 'Fraud', 'status': 'Solved', 'status_class': 'status-solved'},
        {'id': 'CS-2023-082', 'date': '2023-10-03', 'type': 'Assault', 'status': 'Pending', 'status_class': 'status-pending'}
    ]
    
    # Use the dedicated cases.html template instead of dashboard.html
    return render_template('cases.html', stats=stats, recent_cases=sample_cases)

@app.route('/locations')
def locations():
    """Show detailed crime locations page."""
    return render_template('locations.html')

@app.route('/reports')
def reports():
    """Show the reports page."""
    # Sample statistics data (needed by dashboard.html template)
    stats = {
        'total_cases': 158,
        'solved_cases': 103,
        'pending_cases': 42,
        'critical_cases': 13
    }
    
    # Sample cases data
    sample_cases = [
        {'id': 'CS-2023-089', 'date': '2023-10-15', 'type': 'Homicide', 'status': 'Active', 'status_class': 'status-active'},
        {'id': 'CS-2023-088', 'date': '2023-10-14', 'type': 'Burglary', 'status': 'Solved', 'status_class': 'status-solved'},
        {'id': 'CS-2023-087', 'date': '2023-10-12', 'type': 'Assault', 'status': 'Active', 'status_class': 'status-active'}
    ]
    
    message = "Report Generation System"
    return render_template('dashboard.html', stats=stats, recent_cases=sample_cases, message=message)

@app.route('/settings')
def settings():
    """Show the settings page."""
    # Sample statistics data (needed by dashboard.html template)
    stats = {
        'total_cases': 158,
        'solved_cases': 103,
        'pending_cases': 42,
        'critical_cases': 13
    }
    
    sample_cases = [
        {'id': 'CS-2023-089', 'date': '2023-10-15', 'type': 'Homicide', 'status': 'Active', 'status_class': 'status-active'},
        {'id': 'CS-2023-088', 'date': '2023-10-14', 'type': 'Burglary', 'status': 'Solved', 'status_class': 'status-solved'}
    ]
    
    message = "Settings and Configuration"
    return render_template('dashboard.html', stats=stats, recent_cases=sample_cases, message=message)

@app.route('/add_case', methods=['GET', 'POST'])
def add_case():
    """Allow users to manually add case information."""
    if request.method == 'POST':
        try:
            # Process the form data
            case_id = request.form.get('case_id')
            case_type = request.form.get('case_type')
            case_date = request.form.get('case_date')
            case_status = request.form.get('case_status')
            
            # Handle file uploads if any
            if 'crime_scene_photo' in request.files:
                photo = request.files['crime_scene_photo']
                if photo.filename:
                    # Save the file
                    photo_path = os.path.join(app.config['UPLOAD_FOLDER'], f'case_{case_id}_photo.jpg')
                    photo.save(os.path.join('static', photo_path))
            
            if 'report_file' in request.files:
                report = request.files['report_file']
                if report.filename:
                    # Save the file
                    report_path = os.path.join(app.config['UPLOAD_FOLDER'], f'case_{case_id}_report.pdf')
                    report.save(os.path.join('static', report_path))
            
            # In a real application, you would save this data to a database
            # For now, we'll just return a success message
            return render_template('add_case.html', message=f"Case {case_id} added successfully!")
            
        except Exception as e:
            return render_template('add_case.html', error=f"Error adding case: {str(e)}")
    
    # GET request: Display the form
    return render_template('add_case.html')

@app.route('/case/<case_id>', methods=['GET'])
def view_case(case_id):
    """View a specific case."""
    # Sample statistics data (needed by dashboard.html template)
    stats = {
        'total_cases': 158,
        'solved_cases': 103,
        'pending_cases': 42,
        'critical_cases': 13
    }
    
    sample_cases = [
        {'id': case_id, 'date': '2023-10-15', 'type': 'Homicide', 'status': 'Active', 'status_class': 'status-active'}
    ]
    
    message = f"Viewing Case {case_id}"
    return render_template('dashboard.html', stats=stats, recent_cases=sample_cases, message=message)

@app.route('/case/<case_id>/pdf', methods=['GET'])
def case_pdf(case_id):
    """Download PDF report for a specific case."""
    # In a real app, you would generate or fetch the PDF
    # For now, return a simple PDF
    try:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        
        story = []
        story.append(Paragraph(f"Case Report: {case_id}", styles['Title']))
        story.append(Paragraph("This is a placeholder for a real case report.", styles['Normal']))
        
        doc.build(story)
        buffer.seek(0)
        return send_file(buffer, as_attachment=True, download_name=f'Case_{case_id}_Report.pdf', mimetype='application/pdf')
    except Exception as e:
        return f"Error generating PDF: {str(e)}", 500

if __name__ == '__main__':
    # Set a more conservative timeout value 
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload
    app.run(debug=True, host='127.0.0.1', port=5000, threaded=True)