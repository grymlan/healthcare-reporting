from flask import Flask, request, send_file
import pandas as pd
import os
from datetime import datetime

###
# Description: AthenaHealth to BlueCross BlueShield (BCBS) report conversion (A1C, BP, BMP, BMI. uACR) for the Value Based Care (VBC) team.
###

# TODO List
# - add error handling
# - add SFTP upload
# - get away from saving the file to disk during conversion
# - add support for BMI reporting
# - add logic to add columns that are missing
# - modulerize column renaming

###
# Change Log - ./CHANGELOG.md
### 


# Structured Order & the master column listing
COLUMN_ORDER = ['FileExtractDate','Patient_MRN','BCBSPolicyId','Patient_Fname','Patient_Mname','Patient_Lname','Patient_SSN','Patient_DOB','Patient_Gender','Patient_Addr_Line1','Patient_Addr_Line2','Patient_Addr_City','Patient_Addr_State','Patient_Addr_Zip','EncounterId','EncounterType_Code','EncounterType_CodeType','EncounterType_CodeDesc','ServiceDate','AdmitDate','DischargeDate','Provider_NPI','Provider_BCBSTID','Provider_Fname','Provider_Mname','Provider_Lname','Provider_OrgNPI','Provider_OrgTaxId','Provider_OrgLegalName','Procedure_Code','Procedure_CodeType','Procedure_Desc','Procedure_Status','Procedure_BeginDate','Procedure_EndDate','Problem_Code','Problem_CodeType','Problem_Desc','Problem_Status','Problem_BeginDate','Problem_EndDate','LabOrder_Code','LabOrder_CodeType','LabOrder_Desc','LabOrder_Date','LabResult_Code','LabResult_CodeType','LabResult_Desc','LabResult_Value','LabResult_ValueUOM','LabResult_Range','LabResult_Status','LabResult_ReportDate','VitalSign_Code','VitalSign_CodeType','VitalSign_CodeDesc','VitalSign_Value','VitalSign_ValueUOM','VitalSign_ReportDate','MedicationDrug_Code','MedicationDrug_CodeType','MedicationDrug_CodeDesc','Medication_Status','Medication_BeginDate','Medication_EndDate','VaccineDrug_Code','VaccineDrug_CodeType','VaccineDrug_CodeDesc','Vaccine_Status','Vaccine_AdminDate','AllergyCat_Code','AllergyCat_CodeType','AllergyCat_CodeDesc','Allergen_Code','Allergen_CodeType','Allergen_CodeDesc','Allergy_Status','Allergy_BeginDate','Allergy_EndDate']

app = Flask(__name__)

@app.route('/') # landing page
def index():
        return '''
        <html>
        <head>
            <style>
                body {
                    background-color: #191919;
                }
                h3 {
                    font-family: Arial, sans-serif;
                    color: #b2b2b2;
                }
                #instructional {
                    width: 500px;
                    height: 150px;
                    border: 2px solid #ccc;
                    border-radius: 5px;
                    background-color: #696969;
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
                    color: #b2b2b2;
                    font-family: Arial, sans-serif;
                }
            </style>
            <title>BCBS Reporting Utility</title>
        </head>
        <body>
            <div id="instructional">
                <h3>BCBS Reporting Utility</h3>
                <p><b>Instructions</b></p>
                <p>Download the BCBS reports in (CSV format) from Athena and drop it onto the box below. This utility will make all the neccessary changes and provide a download for you once complete.
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

def determineReportType(filename):
    ''' checks the first line of the document for the report name '''
    with open (filename, 'r') as file:
        reportName = file.readline()
        remainingFile = file.readlines()[0:]

    with open (filename, 'w') as outputFile:
        outputFile.writelines(remainingFile)

    df = pd.read_csv(filename)

    if 'Microalbumin-HS' in reportName:
        return 'uacr', df
    
    elif 'A1c' in reportName:
        return 'a1c', df
    
    elif 'BP' in reportName:
        return 'bp', df
    
    elif 'BMP' in reportName:
        return 'egfr', df
    
    elif 'BMI' in reportName:
        return 'bmi', df
    else:
        raise('Report type not detected')

def get_percentile(gender: str, age: float, bmi: float):
    ''' 
    Find BMI percentile based on BMI charts from the CDC.

    Parameters
    ----------
    gender : str
        Specify ['male','Male','M','m'] or ['female','Female','F','f']
    age : int
        Specify age in months (24months-240months)
    bmi : float
        Specify BMI number (5 decimal places)
    
    '''

    df_male = pd.read_csv('BMI-chart-male.csv')
    df_female = pd.read_csv('BMI-chart-female.csv')
    
    try:
        if gender in ['male','Male','M','m']:
            closest_age_percentiles = df_male.loc[(df_male['Age (in months)']-age).abs().idxmin()]
            diffs = abs(closest_age_percentiles- bmi)
            closest_col = diffs.idxmin()
            percentile = closest_col.split()[0]
            return {'percentile': f'{percentile} percentile' }
        if gender in ['female','Female','F','f']:
            closest_age_percentiles = df_female.loc[(df_female['Age (in months)']-age).abs().idxmin()]
            diffs = abs(closest_age_percentiles- bmi)
            closest_col = diffs.idxmin()
            percentile = closest_col.split()[0]
            return {'percentile': f'{percentile} percentile' }
    except Exception as e:
        pass

def convert_A1C(reportData):

    df = reportData

    # modify all dates to MM-DD-YYYY format
    df['patientdob'] = df['patientdob'].str.replace(r'\/', '-', regex=True)
    df['labdate'] = df['labdate'].str.replace(r'\/', '-', regex=True)
    df['order chartdate'] = df['order chartdate'].str.replace(r'\/', '-', regex=True)

    # Remove percent sign from labvalue column
    df['labvalue'] = df['labvalue'].str.replace(r'\s*%\s*', '', regex=True)

    # Append '0' to each value in labvalue column
    df['labvalue'] = df['labvalue'].apply(lambda x: x + '0')

    # Rename columns
    df = df.rename(columns={'patientid': 'Patient_MRN'})
    df = df.rename(columns={'patient primary policyidnumber': 'BCBSPolicyId'})
    df = df.rename(columns={'patient firstname': 'Patient_Fname'})
    df = df.rename(columns={'patient middleinitial': 'Patient_Mname'})
    df = df.rename(columns={'patient lastname': 'Patient_Lname'})
    df = df.rename(columns={'patient ssn': 'Patient_SSN'})
    df = df.rename(columns={'patientdob': 'Patient_DOB'})
    df = df.rename(columns={'patientsex': 'Patient_Gender'})
    df = df.rename(columns={'patient address1': 'Patient_Addr_Line1'})
    df = df.rename(columns={'patient address2': 'Patient_Addr_Line2'})
    df = df.rename(columns={'patient city': 'Patient_Addr_City'})
    df = df.rename(columns={'patient state': 'Patient_Addr_State'})
    df = df.rename(columns={'patient zip': 'Patient_Addr_Zip'})
    df = df.rename(columns={'prim prvdr npi no': 'Provider_NPI'})
    df = df.rename(columns={'order name (single)': 'LabOrder_CodeDesc'})
    df = df.rename(columns={'order chartdate': 'LabOrder_Date'})
    df = df.rename(columns={'labvalue': 'LabResult_Value'})
    df = df.rename(columns={'labstatus': 'LabResult_Status'})
    df = df.rename(columns={'labdate': 'LabResult_ReportDate'})

    # Get today's date
    today = datetime.today()

    # Format today's date as mm-dd-yyyy
    formatted_date = today.strftime('%m-%d-%Y')

    # Add date column at the beginning
    df.insert(0, 'FileExtractDate', formatted_date)

    # Define the new column names and their values
    new_columns = {
        'EncounterId': '',
        'EncounterType_Code': '',
        'EncounterType_CodeType': '',
        'EncounterType_CodeDesc': '',
        'ServiceDate': '',
        'AdmitDate': '',
        'DischargeDate': '',
        'Provider_NPI': '',
        'Provider_BCBSTID': '',
        'Provider_Fname': '',
        'Provider_Mname': '',
        'Provider_Lname': '',
        'Provider_OrgNPI': '',
        'Provider_OrgTaxId': '',
        'Provider_OrgLegalName': '',
        'Procedure_Code': '',
        'Procedure_CodeType': '',
        'Procedure_Desc': '',
        'Procedure_Status': '',
        'Procedure_BeginDate': '',
        'Procedure_EndDate': '',
        'Problem_Code': '',
        'Problem_CodeType': '',
        'Problem_Desc': '',
        'Problem_Status': '',
        'Problem_BeginDate': '',
        'Problem_EndDate': '',
        'LabOrder_Code': '83036',
        'LabOrder_CodeType': 'CPT',
        'LabOrder_Desc': 'HBA1C (HEMOGLOBIN A1C), BLOOD',
        'LabResult_Code': '4548-4',
        'LabResult_CodeType': 'LOINC',
        'LabResult_Desc': 'Hemoglobin A1c/Hemoglobin.total in Blood',
        'LabResult_ValueUOM': '% Hgb',
        'LabResult_Range': '',
        'LabResult_Status': 'Final',
        'VitalSign_Code': '',
        'VitalSign_CodeType': '',
        'VitalSign_CodeDesc': '',
        'VitalSign_Value': '',
        'VitalSign_ValueUOM': '',
        'VitalSign_ReportDate': '',
        'MedicationDrug_Code': '',
        'MedicationDrug_CodeType': '',
        'MedicationDrug_CodeDesc': '',
        'Medication_Status': '',
        'Medication_BeginDate': '',
        'Medication_EndDate': '',
        'VaccineDrug_Code': '',
        'VaccineDrug_CodeType': '',
        'VaccineDrug_CodeDesc': '',
        'Vaccine_Status': '',
        'Vaccine_AdminDate': '',
        'AllergyCat_Code': '',
        'AllergyCat_CodeType': '',
        'AllergyCat_CodeDesc': '',
        'Allergen_Code': '',
        'Allergen_CodeType': '',
        'Allergen_CodeDesc': '',
        'Allergy_Status': '',
        'Allergy_BeginDate': '',
        'Allergy_EndDate': ''
    }

    # Add the new columns to the DataFrame with the same value for each row
    for column, value in new_columns.items():
        df[column] = value

    # Remove a column by name
    column_to_remove = 'patient primary cstm ins grpng'
    df = df.drop(column_to_remove, axis=1)

    # Reorder the columns based on the desired order
    df = df[COLUMN_ORDER]

    # Write the modified DataFrame back to a CSV file
    csvFile = df.to_csv(f'BCBS_A1C_UPLOAD_{formatted_date}.txt', sep='|', index=False)

    return f'BCBS_A1C_UPLOAD_{formatted_date}.txt'

def convert_uacr(reportData):
    df = reportData

    raise ValueError('report type not implemented')

def convert_bp(reportData):
    raise ValueError('report type not implemented')

def convert_egfr(reportData):
    raise ValueError('report type not implemented')

def convert_bmi(reportData):
    # Documentation for BMI Formatting - https://docs.google.com/document/d/1DnOtM9fTy7ANS5U0oMk8yfqwzW1ga4t4E4CAEWqbdG0/edit
    df = reportData

        # modify all dates to MM-DD-YYYY format
    df['patientdob'] = df['patientdob'].str.replace(r'\/', '-', regex=True)

    # Rename columns
    df = df.rename(columns={'patientid': 'Patient_MRN'})
    df = df.rename(columns={'patient primary policyidnumber': 'BCBSPolicyId'})
    df = df.rename(columns={'patient firstname': 'Patient_Fname'})
    df = df.rename(columns={'patient middleinitial': 'Patient_Mname'})
    df = df.rename(columns={'patient lastname': 'Patient_Lname'})
    df = df.rename(columns={'patient ssn': 'Patient_SSN'})
    df = df.rename(columns={'patientdob': 'Patient_DOB'})
    df = df.rename(columns={'patientsex': 'Patient_Gender'})
    df = df.rename(columns={'patient address1': 'Patient_Addr_Line1'})
    df = df.rename(columns={'patient address2': 'Patient_Addr_Line2'})
    df = df.rename(columns={'patient city': 'Patient_Addr_City'})
    df = df.rename(columns={'patient state': 'Patient_Addr_State'})
    df = df.rename(columns={'patient zip': 'Patient_Addr_Zip'})
    df = df.rename(columns={'prim prvdr npi no': 'Provider_NPI'})
    df = df.rename(columns={'order name (single)': 'LabOrder_CodeDesc'})

    # Get today's date
    today = datetime.today()

    # Format today's date as mm-dd-yyyy
    formatted_date = today.strftime('%m-%d-%Y')

    # Add date column at the beginning
    df.insert(0, 'FileExtractDate', formatted_date)

    # Add missing columns
    existingColumns = df.columns.tolist()
    allColumns = existingColumns + COLUMN_ORDER
    # Remove duplicates
    uniqueColumns = list(set(allColumns))
    # Reindex the DataFrame with the updated column names
    df = df.reindex(columns=uniqueColumns)

    # Reorder the columns based on the desired order
    df = df[COLUMN_ORDER]

    # TODO Vital Sign Code

    # Write the modified DataFrame back to a CSV file
    csvFile = df.to_csv(f'BCBS_BMI_UPLOAD_{formatted_date}.txt', sep='|', index=False)

    return f'BCBS_BMI_UPLOAD_{formatted_date}.txt'

###
# Get/Post Methods
###

@app.route('/convert', methods=['POST'])
def convert():
    file = request.files['file']
    filename = file.filename
    file.save(filename)
    reportType, reportData = determineReportType(filename)
    match reportType:
        case 'a1c':
            modifiedReport = convert_A1C(reportData)
        case 'uacr':
            modifiedReport = convert_uacr(reportData)
        case 'bp':
            modifiedReport = convert_bp(reportData)
        case 'egfr':
            modifiedReport = convert_egfr(reportData)
        case 'bmi':
            modifiedReport = convert_bmi(reportData)

    # Remove the temporary CSV file
    os.remove(filename)

    # Provide a download link for the converted file
    return f'<a href="/download/{modifiedReport}">Download Converted File</a>'

@app.route('/download/<modifiedReport>')
def download(modifiedReport):
    converted_file = modifiedReport
    return send_file(converted_file, as_attachment=True)

if __name__ == '__main__':
    app.run()
