
#importing pandas as pd
import pandas as pd
from io import StringIO
  
# Read and store content
# of an excel file 
read_file = pd.read_excel (r"C:\Users\Janhavi Kulkarni\Desktop\Oracle projects\Berkshire Hathway Energy\Python Project\Post Validation Tool\ReferralExternal_ValidationReport_ReferralExternal .xls")

# Write the dataframe object
# into csv file
read_file.to_csv ("Test.csv",index = None,header=True)
    
# read csv file and convert 
# into a dataframe object
df = pd.DataFrame(pd.read_csv(r"C:\Users\Janhavi Kulkarni\Desktop\Oracle projects\Berkshire Hathway Energy\Python Project\Post Validation Tool\Test.csv"))
  
# show the dataframe
#print(df)
df1=pd.DataFrame(pd.read_csv(r"C:\Users\Janhavi Kulkarni\Desktop\Oracle projects\Berkshire Hathway Energy\Python Project\Post Validation Tool\ref.dat", sep='|', delimiter=None, header='infer', names=None, index_col=None))
#print(df1)
keys_list = df.keys().values.tolist()
df_non_matching = pd.merge(df1,df,on=keys_list,how='outer',indicator=True,sort=True)
#print(df_non_matching)

index_list =df_non_matching.index.values.tolist()
print(index_list)
df_non_matching['Index'] = index_list
df_non_matching = df_non_matching[(df_non_matching._merge != 'both')]
print(df_non_matching)
index_list =df_non_matching.index.values.tolist()
df_right = df_non_matching[(df_non_matching._merge == 'right_only')]
df_left = df_non_matching[(df_non_matching._merge == 'left_only')]

keys_list.append("Index")
df_final_nonmatch = pd.merge(df_left[keys_list],df_right[keys_list],on="Index",how = "outer",suffixes=("_hdl","_data_val_report"))

keys_list_final = df_final_nonmatch.keys().values.tolist()
First_col = keys_list_final[0]
keys_list_final = keys_list_final[1:len(keys_list_final)]
keys_list_final.sort()
keys_list_final.insert(0,First_col)
#print(keys_list_final)
df_final_nonmatch=df_final_nonmatch.loc[:,keys_list_final]

print(df_final_nonmatch)
file_name = 'output.xlsx'
  
# saving the excel
df_final_nonmatch.to_excel(file_name)
