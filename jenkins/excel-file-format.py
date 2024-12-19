import pandas as pd
import xlsxwriter
from datetime import datetime


entry=  ['SBL_SPI_INIT',
    'SBL_FCONFIG_LOAD',
    'SBL_CRYPTO_INIT',
    'SBL_CRITICAL_BOOT_LOAD',
    'SBL_UFH_LOAD_AND_VERIFY',
    'SBL_DIGEST_COMPUTE',
    'SBL_LOAD_TBL_IMAGE',
    'SBL_RIOT',
    'SBL_TOTAL',
    'TBL_SPI_INIT',
    'TBL_FCONFIG_LOAD',
    'TBL_PCIE_INIT',
    'TBL_LOAD_PBL_IMAGE',
    'TBL_RIOT',
    'TBL_PRETOTAL',
    'TBL_TOTAL',
    'PBL_SPI_INIT',
    'PBL_PARSE_FCONFIG',
    'PBL_PMIC_INIT',
    'PBL_DRAM_INIT',
    'PBL_SCRUB_MAINFW_DRAM',
    'PBL_CRYPTO_INIT',
    'PBL_NAND_INIT',
    'PBL_LOAD_MAIN_FW',
    'PBL_RIOT',
    'PBL_WAKE_CORES_JUMP',
    'PBL_TOTAL',
    'BOOTLOADERS_TOTAL',
    'MAINFW_PRE_TIMER_INIT',
    'MAINFW_PRE_PMU_INIT',
    'MAINFW_PRE_KERNEL_ENTER_SCHEDULER',
    'OVERALL_TOTAL']

# Get today's date
today = datetime.now().date()

# Print today's date in YYYY-MM-DD format
print(today)

# Create workbook and worksheet
# workbook = xlsxwriter.Workbook('/home/remlab/chewy20-8TB-SPI-{}.csv'.format(today))
workbook = xlsxwriter.Workbook('C:/Users/ozeabala/OneDrive - NANDPS/Desktop/seyon.csv'.format(today))
worksheet = workbook.add_worksheet()

# Expected strings to check
exp_str = [' =================== Selected device 1 =====================', 'boot', 'start', 'time', 'Iteration']

# Read CSV file into DataFrame
# df = pd.read_csv('/home/remlab/chewy20-raw-8TB-SPI-{}.csv'.format(today), header=None, sep=';')
df = pd.read_csv('C:/Users/ozeabala/OneDrive - NANDPS/Desktop/chewy20-raw-8TB-EB0-{}.csv'.format(today), header=None, sep=';', quotechar='"')
val = df.iloc()
res = 1
ignore = True
count = 0  # Initialize count variable
entry_count = 0
entry_position = 1
bold_format = workbook.add_format({'bold': True})

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
        if 'Iteration' in val.obj[i][j]:
            count = 0
        if 'Iteration' in val.obj[i][j] and not ignore:
            res += 1
        if 'Selected device 1' in str(val.obj[i][j]):
            continue
        if res == 1 and str(val.obj[i][j]).startswith('boot'):
            print (entry[entry_count])
            worksheet.write(entry_position, 0, entry[entry_count])
            entry_count += 1
            entry_position += 4
        elif res == 1 and entry_position > 1 and str(val.obj[i][j]).startswith('start') or str(val.obj[i][j]).startswith('time') :
            worksheet.write(count, 0, "        ")
            print ("entry_position: {}".format(entry_position))
            worksheet.write(entry_position - 1 , 0, "        ")
        
        worksheet.write(count, res, val.obj[i][j])
        
        if str(val.obj[i][j]).startswith('time elapsed in ss.ms.us'):
            count += 1
            worksheet.write(count, res, "                                         ")
        if ignore:
            ignore = False
        count += 1

worksheet.write(0, 0, "Boot Entry")
# worksheet.write(2, 0, "        ")
worksheet.freeze_panes(0, 1)  # Freeze from the second column (B) onwards

# Close workbook
workbook.close()
