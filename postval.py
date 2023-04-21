
#importing pandas as pd
import pandas as pd
  
# Read and store content
# of an excel file 
read_file = pd.read_excel ("c:/Users/Rishika Kalappa/Desktop/Post Validation Python/ReferralExternal_ValidationReport_ReferralExternal .xls")
  
# Write the dataframe object
# into csv file
read_file.to_csv ("Test.csv", 
                  index = None,
                  header=True)
    
# read csv file and convert 
# into a dataframe object
df = pd.DataFrame(pd.read_csv("c:/Users/Rishika Kalappa/Desktop/Post Validation Python/Test.csv"))
  
# show the dataframe
print(df)


