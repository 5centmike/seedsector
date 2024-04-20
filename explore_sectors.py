import pandas as pd

# Set the maximum number of columns to None to display all columns
pd.set_option("display.max_columns", None)

relevant_stats = ['Planet Features','hazard_rating','ore','rare_ore','volatiles','organics','food']

index_cols = ['Save Directory', 'System Name', 'Planet Name','Planet Type']






df = pd.read_csv("C:\Program Files (x86)\Fractal Softworks\Starsector\saves\parsed_saves.csv")
#print(df.columns)
#print(df.sort_values('food',ascending=False)[index_cols+relevant_stats])
trifectas = df.loc[df['Hypershunt In Range'] & df['Cryosleeper In Range'] & df['Relay']].sort_values('hazard_rating',ascending=True)

print(trifectas['System Name'].unique())
print(len(trifectas))
#print(trifectas)

#print(df.loc[df['Hypershunt In Range'] & df['Cryosleeper In Range']])

#bool = (df['Save Directory']=='save_auto230251086812_7677681501776336526') & (df['System Name']=='Haddu')
#print(bool)
#print(df.loc[bool])