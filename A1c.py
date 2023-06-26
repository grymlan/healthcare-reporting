import pandas as pd
import time
import tkinter as tk
from tkinter import filedialog
from datetime import datetime

###
# Description: AthenaHealth to BlueCross BlueShield (BCBS) A1C report conversion for the Value Based Care (VBC) team.
###

# TODO List
# - convert to API/webpage so it's usable on Chromebooks
# - make a better drag/drop UI
# - add error handling
# - check report before conversion
# - create instructional guide for VBC team

filename = 'none'
COLUMN_ORDER = ['FileExtractDate','Patient_MRN','BCBSPolicyId','Patient_Fname','Patient_Mname','Patient_Lname','Patient_SSN','Patient_DOB','Patient_Gender','Patient_Addr_Line1','Patient_Addr_Line2','Patient_Addr_City','Patient_Addr_State','Patient_Addr_Zip','EncounterId','EncounterType_Code','EncounterType_CodeType','EncounterType_CodeDesc','ServiceDate','AdmitDate','DischargeDate','Provider_NPI','Provider_BCBSTID','Provider_Fname','Provider_Mname','Provider_Lname','Provider_OrgNPI','Provider_OrgTaxId','Provider_OrgLegalName','Procedure_Code','Procedure_CodeType','Procedure_Desc','Procedure_Status','Procedure_BeginDate','Procedure_EndDate','Problem_Code','Problem_CodeType','Problem_Desc','Problem_Status','Problem_BeginDate','Problem_EndDate','LabOrder_Code','LabOrder_CodeType','LabOrder_Desc','LabOrder_Date','LabResult_Code','LabResult_CodeType','LabResult_Desc','LabResult_Value','LabResult_ValueUOM','LabResult_Range','LabResult_Status','LabResult_ReportDate','VitalSign_Code','VitalSign_CodeType','VitalSign_CodeDesc','VitalSign_Value','VitalSign_ValueUOM','VitalSign_ReportDate','MedicationDrug_Code','MedicationDrug_CodeType','MedicationDrug_CodeDesc','Medication_Status','Medication_BeginDate','Medication_EndDate','VaccineDrug_Code','VaccineDrug_CodeType','VaccineDrug_CodeDesc','Vaccine_Status','Vaccine_AdminDate','AllergyCat_Code','AllergyCat_CodeType','AllergyCat_CodeDesc','Allergen_Code','Allergen_CodeType','Allergen_CodeDescAllergen_Code','Allergy_Status','Allergy_BeginDate','Allergy_EndDate']

def convert_file():
    # Read the CSV file into a DataFrame
    with open (filename, 'r') as file:
        df = pd.read_csv(filename)

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
        'Allergen_CodeDescAllergen_Code': '',
        'Allergy_Status': '',
        'Allergy_BeginDate': '',
        'Allergy_EndDate': ''
        # Add more columns as needed
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
    df.to_csv('BCBS A1C UPLOAD.txt', sep='|', index=False)

# Create the Tkinter window
window = tk.Tk()

# Function to handle the "Go" button click
def go_button_click():
    convert_file()

# Function to handle the file selection button click
def select_file():
    global filename
    filename = filedialog.askopenfilename()

# Create the "Select File" button
select_button = tk.Button(window, text="Select File", command=select_file)
select_button.pack()

# Create the "Go" button
go_button = tk.Button(window, text="Go", command=go_button_click)
go_button.pack()

# Set the window title
window.title("Athena > BCBS A1C Conversion ")

# Run the Tkinter event loop
window.mainloop()