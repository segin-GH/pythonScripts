# import pandas as pd

# pd.options.display.max_rows = 999
# # Read two CSV files into Pandas DataFrames
# df1 = pd.read_csv('bom.csv') # not sync bom
# df2 = pd.read_csv('bom2.csv') #sync bom

# print(df1.iloc[:, 0] + "                    " + df2.iloc[:, 0])


import pandas as pd

pd.options.display.max_rows = 999
# Read two CSV files into Pandas DataFrames
df1 = pd.read_csv('bom.csv') # not sync bom
df2 = pd.read_csv('bom2.csv') # sync bom

# Compare the two dataframes to find the values that are not present in df1
not_in_df1 = df1[~df1.iloc[:, 0].isin(df2.iloc[:, 0])]

# Print the result
print(not_in_df1.iloc[:, 0])


