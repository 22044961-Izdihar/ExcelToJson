from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import json
import io

app = Flask(__name__)

@app.route('/')
def upload_file():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file and (file.filename.endswith('.xlsx') or file.filename.endswith('.xls')):
        # Load the Excel file and strip extra spaces
        df = pd.read_excel(file)
        df.columns = df.columns.str.strip()

        # 1. Filter out columns with date values and change format to yyyymmdd
        columns_with_date = [
            'Enrolment Date', 'Year of birth of Applicant', 'Year of birth of the child',
            'FM Start Date of enrolment', 'CCFA Start Date', 'CCFA End Date'
        ]
        datecolumns_df = df[columns_with_date]

        # Change date format
        for col in datecolumns_df:
            df[col] = pd.to_datetime(df[col], format='%d/%m/%Y', errors='coerce').dt.strftime('%Y%m%d')

        # 2. Update working status
        def map_working_status(status):
            if status == "Salaried Employee":
                return "WEP"
            elif status == "Self Employed":
                return "WSP"
            elif status == "Salaried Employee & Self Employed":
                return "WEPWSP"
            else:
                return "NW"

        df['Main Applicant working status'] = df['Main Applicant working status'].apply(map_working_status)

        # Replace missing values with blanks
        df = df.fillna("")

        # Build the JSON data
        json_data = []
        for num, (_, row) in enumerate(df.iterrows(), start=1):
            row_json = {
                f"Row {num} TC00{num}  ChildInfo": {
                    "Gender": row.get("Gender", ""),
                    "DateOfBirth": row.get("Year of birth of the child", ""),
                    "IdentityNumber": row.get("Child ID", ""),
                    "IdentityType": row.get("Child ID Type", ""),
                    "Name": row.get("Child Name", ""),
                    "Race": row.get("Child Race", ""),
                    "RelationshipToChild": "Child",
                    "TypeOfCitizenship": row.get("Child Citizenship", ""),
                },
                "EnrolmentApplicantInfo": {
                    "RelationshipToChild": row.get("Main Applicant Relationship to Child", ""),
                    "SpecificRelationship": row.get("LG Specific Relationship", ""),
                    "Name": row.get("Main Applicant Name", ""),
                    "Gender": row.get("Main Applicant Gender", ""),
                    "DateOfBirth": row.get("Year of birth of Applicant", ""),
                    "TypeOfCitizenship": row.get("Main Applicant Type of Citizenship", ""),
                    "IdentityNumber": row.get("Applicant ID", ""),
                    "IdentityType": row.get("Main Applicant ID Type", ""),
                    "MaritalStatus": row.get("Main Applicant", ""),
                    "IsJointCustody": row.get("Is Joint Custody", ""),
                    "PostalCode": row.get("Postal Code", ""),
                    "BlockNumber": row.get("Block Number", ""),
                    "StreetName": row.get("Street Name", ""),
                    "BuildingName": row.get("Building Name", ""),
                    "FloorNo": row.get("Floor No", ""),
                    "UnitNo": row.get("Unit No", ""),
                    "WorkingStatus": [{"Value": row.get("Main Applicant working status", "")}],
                    "NWReason": row.get("Main Applicant Not working reason", ""),
                    "ApplicantWSG": row.get("Applicant WSG", ""),
                    "EDD": row.get("EDD", ""),
                    "EmploymentWithInPast2Months": row.get("Within last 2 months", ""),
                    "DateOfEmployment": row.get("Main Applicant Emp start Date", ""),
                    "ReceivingCPF": row.get("Main Applicant - Receiving CPF ?", ""),
                    "MainApplicantWEPGrossMonthlyIncome": row.get("Main Applicant Gross Monthly Income 1", ""),
                    "HasLatestNOA": row.get("Main Applicant has NOA ?", ""),
                    "MainApplicantWSPGrossMonthlyIncome": row.get("Main Applicant Gross Monthly Income 2", ""),
                    "MobileNoSG": row.get("Mobile No", ""),
                    "TelephoneNo": row.get("Telephone No", ""),
                    "EmailAddress": row.get("Email Address", ""),
                    "Consent": {
                        "IsNoValidAuthority": "N",
                        "ConsentScope": "AS",
                        "ConsentType": "NCO",
                        "ConsentSigningDate": "20240930",
                    }
                },
                "EnrolmentInfo": {
                    "DateOfEnrolment": row.get("Enrolment Date", ""),
                    "EnlmMthProgFeeWOGST": row.get("Enlm Mth Prog Fee WOGST", ""),
                    "EnlmMthProration": row.get("Enlm Mth Proration", ""),
                    "AppliedForPCI": row.get("Applied For PCI", ""),
                    "CCFAInfo": {
                        "CCFARequired": row.get("CCFA Required", ""),
                        "TypeOfReferral": row.get("Type Of Referral", ""),
                        "CCFANonWorkingReasons": row.get("CCFA Non Working Reasons", ""),
                        "OtherDescription": row.get("Other Description", ""),
                        "ReferralBy": row.get("Referral By", ""),
                        "NameOfAgency": row.get("Name Of Agency", ""),
                        "SocialWorkerName": row.get("Social Worker Name", ""),
                        "SocialWorkerEmail": row.get("Social Worker Email", ""),
                        "RecommendedCopayment": row.get("Recommended Copayment", ""),
                        "StartDate": row.get("Start Date", ""),
                        "MonthsRequired": row.get("Months Required", ""),
                        "EndDate": row.get("End Date", "")
                    },
                    "CCFASUG": {
                        "CCSUGRequired": row.get("CCSUG Required", ""),
                    },
                    "IsDeclarationSelected": row.get("Is Declaration Selected", ""),
                    "Declaration": [
                        {
                            "Display": "Exact declaration pending ECDA confirmation."
                        }
                    ]
                },
                "FamilyMemberList": [
                    {
                        "Name": row.get("Family Member Name 1", ""),
                        "RelationshipToChild": row.get("Family Member Relationship 1", ""),
                        "IdentityNumber": row.get("Family Member ID 1", ""),
                        "DateOfBirth": row.get("Family Member DOB 1", ""),
                        "WorkingStatus": row.get("Family Member Working Status 1", ""),
                        "GrossMonthlyIncome": row.get("Family Member Gross Monthly Income 1", ""),
                        "EmploymentWithInPast2Months": row.get("Family Member Employment Within Past 2 Months 1", ""),
                        "DateOfEmployment": row.get("Family Member Employment Date 1", ""),
                        "Consent": {
                            "IsNoValidAuthority": "N",
                            "ConsentScope": "AS",
                            "ConsentType": "NCO",
                            "ConsentSigningDate": "20240930",
                        }
                    }
                ],
                "SpouseInfo": {
                    "RelationshipToChild": row.get("Spouse Relationship to Child", ""),
                    "SpecificRelationship": row.get("Spouse Specific Relationship", ""),
                    "Name": row.get("Spouse Name", ""),
                    "DateOfBirth": row.get("Spouse DOB", ""),
                    "Gender": row.get("Spouse Gender", ""),
                    "TypeOfCitizenship": row.get("Spouse Type of Citizenship", ""),
                    "IdentityNumber": row.get("Spouse ID", ""),
                    "IdentityType": row.get("Spouse ID Type", ""),
                    "IsIncarcerated": row.get("Spouse Is Incarcerated", ""),
                    "IsMentallyIncapacitated": row.get("Spouse Is Mentally Incapacitated", ""),
                    "WorkingStatus": row.get("Spouse Working Status", ""),
                    "DateOfEmployment": row.get("Spouse Employment Date", ""),
                    "EmploymentWithInPast2Months": row.get("Spouse Employment Within Past 2 Months", ""),
                    "SpouseReceivingCPF": row.get("Spouse Receiving CPF", ""),
                    "SpouseWEPGrossMonthlyIncome": row.get("Spouse WEP Gross Monthly Income", ""),
                    "SpouseHasLatestNOA": row.get("Spouse Has Latest NOA", ""),
                    "SpouseWSPGrossMonthlyIncome": row.get("Spouse WSP Gross Monthly Income", ""),
                    "MobileNoSG": row.get("Spouse Mobile No", ""),
                    "TelephoneNo": row.get("Spouse Telephone No", ""),
                    "EmailAddress": row.get("Spouse Email Address", ""),
                    "Consent": {
                        "IsNoValidAuthority": "N",
                        "ConsentScope": "AS",
                        "ConsentType": "NCO",
                        "ConsentSigningDate": "20240930",
                    }
                },
                "ApplicationStatus": {
                    "StatusCode": "00",
                    "RejectionCode": "",
                    "RejectionDescription": ""
                },
                "DocumentCategoryList": [
                    {
                        "Code": "SPDNW",
                        "FileName": "SPDNW.doc"
                    },
                    {
                        "Code": "",
                        "FileName": ""
                    }
                ]
            }
            json_data.append(row_json)

        # Create an in-memory file and save the JSON data
        json_file = io.BytesIO()
        json_file.write(json.dumps(json_data, indent=4).encode('utf-8'))
        json_file.seek(0)

        return send_file(
            json_file,
            as_attachment=True,
            download_name='converted_output.json',  # Change the output file name here
            mimetype='application/json'
        )

    return jsonify({"error": "Invalid file format"}), 400

if __name__ == '__main__':
    app.run(debug=True)
