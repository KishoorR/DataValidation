
#importing pandas as pd
import pandas as pd
from io import StringIO
  
# Read and store content
# of an excel file 
read_file = pd.read_excel (r"C:\Users\Janhavi Kulkarni\Oracle Content - Accounts\Oracle Content\Post Validation Tool(Python)\DataValidation\ReferralExternal_ValidationReport_ReferralExternal .xls")

# Write the dataframe object
# into csv file
read_file.to_csv ("Test.csv",index = None,header=True)
    
# read csv file and convert 
# into a dataframe object
df = pd.DataFrame(pd.read_csv(r"C:\Users\Janhavi Kulkarni\Oracle Content - Accounts\Oracle Content\Post Validation Tool(Python)\DataValidation\Test.csv"))
  
# show the dataframe
#print(df)
df1=pd.DataFrame(pd.read_csv(r"C:\Users\Janhavi Kulkarni\Oracle Content - Accounts\Oracle Content\Post Validation Tool(Python)\DataValidation\ref.dat", sep='|', delimiter=None, header='infer', names=None, index_col=None))
#print(df1)
keys_list = df.keys().values.tolist()
df_non_matching = pd.merge(df1,df,on=keys_list,how='outer',indicator=True,sort=True)
#print(df_non_matching)

index_list =df_non_matching.index.values.tolist()
#print(index_list)
#df_non_matching['Index'] = index_list
df_non_matching = df_non_matching[(df_non_matching._merge != 'both')]
#print(df_non_matching)
index_list =df_non_matching.index.values.tolist()
df_right = df_non_matching[(df_non_matching._merge == 'right_only')]
df_left = df_non_matching[(df_non_matching._merge == 'left_only')]

#index_keys_list = keys_list
#index_keys_list.append("Index")
df_right.reset_index(inplace = True, drop = True)
df_left.reset_index(inplace = True, drop = True)
#df_final_nonmatch = pd.merge(df_left[keys_list],df_right[keys_list],on="Index",how = "right",suffixes=("_hdl","_data_val_report"))
print(df_left)

df_final_nonmatch=df_left.compare(df_right,keep_shape= True,keep_equal = True,align_axis=1).rename(columns={'self': 'HDL', 'other': 'Data_Val'}, level=-1)

print(df_final_nonmatch[keys_list])

df_final_nonmatch=df_final_nonmatch[keys_list]

#print(df_final_nonmatch)
file_name = 'output.xlsx'
  
# saving the excel
df_final_nonmatch.to_excel(file_name)
