# views.py
import base64
from builtins import Exception, all, len, open, print, range
import csv
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from django.http import JsonResponse
import smtplib
from django.views.decorators.csrf import csrf_exempt
import PyPDF2
from django.templatetags.static import static
from django.contrib.staticfiles.storage import staticfiles_storage
import os
from django.http import HttpResponse
import qrcode
from cryptography.fernet import Fernet
import requests
from pdf2image import convert_from_path
from PIL import Image, ImageDraw, ImageFont  
from datetime import date
from fpdf import FPDF
@csrf_exempt 
def decrypt_qr_code(request):
    # Get the encrypted string from the request parameters
    encrypted_string = request.GET.get('encrypted_string', '')
    key = request.GET.get('key', '')
    print(encrypted_string)
    # Decrypt the payload
    try:
        print("1")
        key = Fernet.generate_key()  # You should use a secure method to store and retrieve the key
        print("2")
        cipher_suite = Fernet(key)
        print("3")
        decrypted_payload = cipher_suite.decrypt(encrypted_string.encode('utf-8')).decode('utf-8')
        print("4")

        # Process the decrypted payload as needed
        # For example, you can split it into individual fields
        certificate_details, issuer_name, subject_name, date_of_issue = decrypted_payload.split(',')
        print("5")

        # Perform actions with the decrypted data or return it in the response
        response_data = {
            'certificate_details': certificate_details,
            'issuer_name': issuer_name,
            'subject_name': subject_name,
            'date_of_issue': date_of_issue,
        }

        # You can return the data as JSON or use it to render a template
        return HttpResponse(response_data)
    except Exception as e:
        # Handle decryption errors
        return HttpResponse(f"Error: {str(e)}", status=400)

@csrf_exempt
def get_key():
    # Make a request to the key retrieval endpoint
    response = requests.get("http://localhost:5000/utility/getKey")
    
    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON response and extract the key
        key = response.json().get('key', '')
        key = key.encode('utf-8')
        key = base64.urlsafe_b64encode(key.ljust(32)[:32])

        return key
    else:
        # Handle the case where the request to fetch the key failed
        return None
    
@csrf_exempt
def get_org_name():
    # Make a request to the key retrieval endpoint
    response = requests.get("http://localhost:5000/utility/getOrgName")
    
    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON response and extract the key
        org_name = response.json().get('org_name', '')
        return org_name
    else:
        # Handle the case where the request to fetch the key failed
        return None

def generate_qr_code(key,hash,payload,output_path):

    # Check if the key is available
    if key is None:
        # Handle the case where the key retrieval failed
        return HttpResponse("Failed to retrieve the key from the remote server")

    # extract fields from the payload dictionary
    certificate_key = payload.get('certificate_key', '')
    issuer_name = payload.get('issuer_name', '')
    subject_name = payload.get('subject_name', '')
    date_of_issue = payload.get('date_of_issue', '')

    
    # Combine payload
    payload = f"{certificate_key},{issuer_name},{subject_name},{date_of_issue}"

    # Encrypt payload with the fetched key

    cipher_suite = Fernet(key)
    encrypted_payload = cipher_suite.encrypt(payload.encode('utf-8'))

    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    # use this url http://localhost:8000/api/decryptQR/?hash=yeh_hai_hash&key=yeh_hai_key, replay key with encrypted_payload and hash with hash
    qr.add_data("http://localhost:5000/verify/qrcode/?hash="+hash+"&key="+encrypted_payload.decode('utf-8'))

    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # You can save the image or return it as an HTTP response
    img.save(output_path + ".png")

    # Return the image as an HTTP response
    # response = HttpResponse(content_type="image/png")
    # img.save(response, "PNG")
    return img

def replace_text(input_path, output_path, new_text,key):
    img = Image.open(input_path)  
    d = ImageDraw.Draw(img)  
    fnt = ImageFont.truetype("comicbd.ttf", 75)  
    d.text((750, 600),new_text, font=fnt, fill=(0, 0, 0))

    payload = {
        'certificate_key': key,
        'issuer_name': get_org_name(),
        'subject_name': new_text,
        'date_of_issue': date.today(),
    }
    hash = "yeh_hai_hash"
    qr_code = generate_qr_code(key,hash,payload,output_path.replace(".pdf",""))
    qr_code =  Image.open(output_path.replace(".pdf",".png"))
    qr_code = qr_code.resize((200, 200))
    img.paste(qr_code, (1700, 100))
    img.save(output_path)

@csrf_exempt
def send_pdf_to_emails(request):
    if request.method == 'POST':
        # Get data from the POST request body
        sender_email = request.POST.get('sender_email')
        sender_password = request.POST.get('sender_password')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        # get current key for encryption
        key = get_key()

        # # call generate_qr_code function to generate qr code
        # hash = "yeh_hai_hash"
        # payload = {
        #     'certificate_key': '123456789',
        #     'issuer_name': 'John Doe',
        #     'subject_name': 'Jane Doe',
        #     'date_of_issue': '2020-01-01',
        # }
        # qr_code = generate_qr_code(key,hash,payload)

        # return qr_code
        
        # The file will be in request.FILES
        pdf_file = request.FILES.get('template')
        email_recipients_csv = request.FILES.get('email_recipients')

        if not all([sender_email, sender_password, subject, message, pdf_file, email_recipients_csv]):
            return JsonResponse({'error': 'Missing required parameters'}, status=400)

        # Save the uploaded PDF file with the same name
        pdf_file_path = os.path.join(
            'D:\\Sem 4\\MP\\Certifica-X-backend\\MegaProject\\CertificaX\\static', pdf_file.name)
        pdf_output_path = os.path.join(
            'D:\\Sem 4\\MP\\Certifica-X-backend\\MegaProject\\CertificaX\\static\\modified', pdf_file.name)
        
        with open(pdf_file_path, 'wb') as destination:
            for chunk in pdf_file.chunks():
                destination.write(chunk)

        # Replace the placeholder text in the PDF file

                
        # Read email recipients and names from the CSV file
        recipients_with_names = []
        try:
            csv_data = email_recipients_csv.read().decode('utf-8').splitlines()
            csv_reader = csv.DictReader(csv_data)
            recipients_with_names = [(row['email'], row['names'])
                                     for row in csv_reader if 'email' in row and 'names' in row]
        except Exception as e:
            return JsonResponse({'error': f'Error reading CSV file: {str(e)}'}, status=500)

        # Configure the SMTP server
        smtp_server = 'smtp.gmail.com'  # Replace with your SMTP server

        # Create a secure connection to the SMTP server
        server = smtplib.SMTP(smtp_server, 587)
        server.starttls()

        # Login to the email account
        server.login(sender_email, sender_password)

        for recipient_email, recipient_name in recipients_with_names:
            # Create a new email message for each recipient
            email_message = MIMEMultipart()
            email_message['From'] = sender_email
            email_message['To'] = recipient_email 
            email_message['Subject'] = subject +  " " + recipient_name

            # Add the message body
            email_message.attach(MIMEText(message, 'plain'))

            # Attach the PDF file with a customized file name
            try:
                # Create a PDF reader object

                # Assuming the username is unique for each recipient, use it as the file name
                file_name = os.path.join(
                    'D:\\Sem 4\\MP\\Certifica-X-backend\\MegaProject\\CertificaX\\static', f"{pdf_file.name}")
                individual_output_path = os.path.join(
                    'D:\\Sem 4\\MP\\Certifica-X-backend\\MegaProject\\CertificaX\\static\\modified', f"{recipient_name}.pdf")
                print('1')
                replace_text(file_name, individual_output_path, recipient_name,key)
                # # Create a PDF writer object
                # pdf_writer = PyPDF2.PdfWriter()

                # # Add the pages from the original PDF to the new PDF
                # for page_num in range(len(pdf_reader.pages)):
                #     pdf_writer.add_page(pdf_reader.pages[page_num])

                # # Save the new PDF with the customized file name
                # with open(file_name, 'wb') as new_pdf:
                #     pdf_writer.write(new_pdf)

                # Attach the new PDF to the email
                with open(individual_output_path, 'rb') as attachment:
                    pdf_attachment = MIMEApplication(
                        attachment.read(), _subtype="pdf")
                    pdf_attachment.add_header(
                        'Content-Disposition', f'attachment; filename={recipient_name}')
                    email_message.attach(pdf_attachment)

                # Send the email
                # server.sendmail(sender_email, recipient_email,
                #                 email_message.as_string())
                # os.remove(individual_output_path)
                print(
                    f'Email sent to {recipient_email} with customized file name for {recipient_name}')

            except Exception as e:
                print(f'Error processing PDF for {recipient_email}: {str(e)}')

            # finally:
                # Clean up: delete the temporary PDF file
        
        # os.remove(file_name)

        print('Emails sent successfully!')
        # Close the connection
        server.quit()
        return JsonResponse({'message': 'Emails sent successfully!'}, status=200)

    return JsonResponse({'error': 'Invalid request method'}, status=400)
