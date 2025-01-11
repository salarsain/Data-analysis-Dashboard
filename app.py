from flask import Flask, request, render_template, jsonify, send_file
import pandas as pd
import matplotlib.pyplot as plt
import os
import io
import base64

app = Flask(__name__)
UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route('/')
def project():
    return render_template('project.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)
    return jsonify({"message": "File uploaded successfully", "file_path": file_path})


@app.route('/create-chart', methods=['POST'])
def create_chart():
    data = request.get_json()
    file_path = data.get('file_path')
    chart_type = data.get('chart_type')
    chart_title = data.get('chart_title', 'Chart')
    x_label = data.get('x_label', '')
    y_label = data.get('y_label', '')
    color = data.get('color', '#3498db')

    if not file_path or not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 400

    # Read the uploaded file
    try:
        df = pd.read_excel(file_path) if file_path.endswith('.xlsx') else pd.read_csv(file_path)
    except Exception as e:
        return jsonify({"error": f"Error reading file: {str(e)}"}), 400

    # Ensure the data is suitable for plotting
    if df.empty or len(df.columns) < 2:
        return jsonify({"error": "Insufficient data for plotting"}), 400

    # Create the chart
    plt.figure(figsize=(10, 6))
    try:
        if chart_type == 'line':
            df.plot(kind='line', color=color, title=chart_title)
        elif chart_type == 'bar':
            df.plot(kind='bar', color=color, title=chart_title)
        elif chart_type == 'scatter':
            # Scatter requires two numeric columns
            if len(df.columns) >= 2:
                x_col, y_col = df.columns[:2]
                # Ensure that the data in the columns is numeric
                df[x_col] = pd.to_numeric(df[x_col], errors='coerce')
                df[y_col] = pd.to_numeric(df[y_col], errors='coerce')

                # Drop rows with invalid data (NaN values)
                df = df.dropna(subset=[x_col, y_col])

                plt.scatter(df[x_col], df[y_col], c=color)
                plt.title(chart_title)
                plt.xlabel(x_label or x_col)
                plt.ylabel(y_label or y_col)
            else:
                return jsonify({"error": "Not enough columns for scatter plot."}), 400
        elif chart_type == 'histogram':
            df.hist(color=color, bins=10)
            plt.title(chart_title)
        elif chart_type == 'area':
            df.plot(kind='area', alpha=0.5, color=color, title=chart_title)
        else:
            return jsonify({"error": f"Unsupported chart type: {chart_type}"}), 400
    except Exception as e:
        return jsonify({"error": f"Error creating chart: {str(e)}"}), 400

    # Save the chart to a buffer
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    chart_base64 = base64.b64encode(img.read()).decode('utf-8')
    plt.close()

    return jsonify({"message": "Chart created successfully", "chart": chart_base64})


@app.route('/download', methods=['POST'])
def download_report():
    data = request.get_json()
    file_path = data.get('file_path')

    if not file_path or not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 400

    return send_file(file_path, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)
