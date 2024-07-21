import pandas as pd
import xlsxwriter
from datetime import datetime

# Get today's date
today = datetime.now().date()

# Print today's date in YYYY-MM-DD format
print(today)

# Create workbook and worksheet
workbook = xlsxwriter.Workbook('/home/remlab/chewy20-8TB-SPI-{}.csv'.format(today))
# workbook = xlsxwriter.Workbook('C:/Users/ozeabala/OneDrive - NANDPS/Desktop/seyon.csv'.format(today))
worksheet = workbook.add_worksheet()

# Expected strings to check
exp_str = [' =================== Selected device 1 =====================', 'boot', 'start', 'time', '******************* Iteration']

# Read CSV file into DataFrame
df = pd.read_csv('/home/remlab/chewy20-raw-8TB-SPI-{}.csv'.format(today), header=None, sep=';')
# df = pd.read_csv('C:/Users/ozeabala/OneDrive - NANDPS/Desktop/chewy20-raw-8TB-EB0-{}.csv'.format(today), header=None, sep=';')
val = df.iloc()
res = 0
ignore = True
count = 0  # Initialize count variable

def check_string(val):
    """Function to check if a value starts with any of the expected strings."""
    for i in exp_str:
        if str(val).startswith(i):
            return False
    return True

# Iterate through DataFrame to write to worksheet
for i in range(len(df.columns)):
    for j in range(len(val.obj)):
        print(val.obj[i][j])
        if str(val.obj[i][j]) == 'nan' or check_string(val.obj[i][j]):
            continue
        if '******************* Iteration' in val.obj[i][j]:
            count = 0
        if '******************* Iteration' in val.obj[i][j] and not ignore:
            res += 1
        if 'Selected device 1' in str(val.obj[i][j]):
            continue
        worksheet.write(count, res, val.obj[i][j])
        if str(val.obj[i][j]).startswith('time elapsed in ss.ms.us'):
            count += 1
            worksheet.write(count, res, "                                         ")
        if ignore:
            ignore = False
        count += 1

# Close workbook
workbook.close()
