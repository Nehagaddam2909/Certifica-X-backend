import os
from PyPDF2 import PdfReader, PdfWriter


def rename_pdf(input_path, output_path, new_name):
    # Load the input PDF file
    input_pdf = PdfReader(open(input_path, 'rb'))

    # Create a new PDF writer object
    output_pdf = PdfWriter()

    # Copy each page from the input PDF to the output PDF
    for page in input_pdf.pages:
        output_pdf.add_page(page)

    # Set the new name for the PDF
    output_pdf.add_metadata({'/Title': new_name})

    # Save the output PDF to the specified path
    with open(output_path, 'wb') as output_file:
        output_pdf.write(output_file)

    print(f"PDF renamed and generated successfully as {new_name}.pdf!")


# Specify the input PDF file path
str = input("Enter filename: ")
input_path = 'C:/Users/USER/Desktop/Mails/'+str

# Specify the output directory where the renamed PDF will be saved
output_directory = 'C:/Users/USER/Desktop/Mails/Output'

# Specify the new name for the PDF (without the .pdf extension)

new_name = input("Enter new name: ")

# Create the output path by combining the output directory and new name
output_path = os.path.join(output_directory, new_name + '.pdf')

# Call the rename_pdf function to rename and generate the PDF
rename_pdf(input_path, output_path, new_name)
