from flask import Flask, request, send_file
import pandas as pd
import os

###
# Description: AthenaHealth to BlueCross BlueShield (BCBS) A1C report conversion for the Value Based Care (VBC) team.
###

# TODO List
# - add error handling
# - check report before conversion


app = Flask(__name__)

@app.route('/')
def index():
        return '''
        <html>
        <head>
            <style>
                h3 {
                    font-family: Arial, sans-serif;
                    color: #5b5b5b;
                }
                #instructional {
                    width: 500px;
                    height: 150px;
                    border: 2px solid #ccc;
                    border-radius: 5px;
                    background-color: #abedbc;
                    margin: 20 auto;
                    text-align: center;
                    padding: 20px;
                }
                #drop-area {
                    width: 300px;
                    height: 200px;
                    border: 2px dashed #ccc;
                    border-radius: 5px;
                    text-align: center;
                    padding: 20px;
                    margin: 0 auto;
                    font-family: Arial, sans-serif;
                }
                #drop-area.highlight {
                    border-color: #5c9ce6;
                }
                p {
                    font-size: 16px;
                    color: #5b5b5b;
                    font-family: Arial, sans-serif;
                }
            </style>
            <title>BCBS A1C Utility</title>
        </head>
        <body>
            <div id="instructional">
                <h3>BCBS A1C Utility</h3>
                <p><b>Instructions</b></p>
                <p>Download the BCBS A1C report from Athena and drop it onto the box below. This utility will make all the neccessary changes and provide a download for you once complete.
            </div>
            <div id="drop-area" ondrop="handleDrop(event)" ondragover="handleDragOver(event)" ondragenter="handleDragEnter(event)" ondragleave="handleDragLeave(event)">
                <p>Drag and drop a CSV file here</p>
                <input type="file" id="file-input" style="display: none;" onchange="handleFiles(event.target.files)">
                <button onclick="document.getElementById('file-input').click()">Select File</button>
            </div>
            <script>
                function handleFiles(files) {
                    if (files.length > 0) {
                        var formData = new FormData();
                        formData.append('file', files[0]);
                        fetch('/convert', {
                            method: 'POST',
                            body: formData
                        })
                        .then(response => response.text())
                        .then(result => {
                            document.getElementById('drop-area').innerHTML = result;
                        });
                    }
                }
                function handleDrop(event) {
                    event.preventDefault();
                    var files = event.dataTransfer.files;
                    handleFiles(files);
                    document.getElementById('drop-area').classList.remove('highlight');
                }
                function handleDragOver(event) {
                    event.preventDefault();
                }
                function handleDragEnter(event) {
                    event.preventDefault();
                    document.getElementById('drop-area').classList.add('highlight');
                }
                function handleDragLeave(event) {
                    event.preventDefault();
                    document.getElementById('drop-area').classList.remove('highlight');
                }
            </script>
        </body>
        </html>
    '''

# '''
#         <html>
#         <body>
#             <form action="/convert" method="post" enctype="multipart/form-data">
#                 <input type="file" name="file">
#                 <input type="submit" value="Convert">
#             </form>
#         </body>
#         </html>
#     '''

@app.route('/convert', methods=['POST'])
def convert():
    file = request.files['file']
    filename = file.filename
    file.save(filename)

    # Perform CSV conversion using pandas or any other library
    converted_data = pd.read_csv(filename).to_excel('converted_file.xlsx', index=False)

    # Remove the temporary CSV file
    os.remove(filename)

    # Provide a download link for the converted file
    return f'<a href="/download">Download Converted File</a>'

@app.route('/download')
def download():
    converted_file = 'converted_file.xlsx'
    return send_file(converted_file, as_attachment=True)

if __name__ == '__main__':
    app.run()
