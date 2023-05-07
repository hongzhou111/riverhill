#import tabula
# readinf the PDF file that contain Table Data
# you can find find the pdf file with complete code in below
# read_pdf will save the pdf table into Pandas Dataframe
#df = tabula.read_pdf("C:/Users/3203142/OneDrive/PharmDLive/Acension Health ST Lois 4695_ProfileExport_20200110060114 (2).pdf")
# in order to print first 5 lines of Table
#df.head()

import pdftables_api

c = pdftables_api.Client('1jwmh83jhdyj')
#c.xlsx("C:/Users/3203142/OneDrive/PharmDLive/Acension Health ST Lois 4695_ProfileExport_20200110060114 (2).pdf", "C:/Users/3203142/OneDrive/PharmDLive/Acension.xlsx")
c.xlsx("C:/Users/3203142/OneDrive/PharmDLive/Kaiser Info.pdf", "C:/Users/3203142/OneDrive/PharmDLive/Kaiser.xlsx")

#replace c.xlsx with c.csv to convert to CSV
#replace c.xlsx with c.xml to convert to XML
#replace c.xlsx with c.html to convert to HTML