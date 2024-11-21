# Flatten the column into new columns
def flatten_column_to_columns(df, col_name):
    # Extract the list of dictionaries from the column
    lists_of_dicts = df[col_name]

    # Flatten the dictionaries and create new columns for each key
    for i, row in enumerate(lists_of_dicts):
        for j, dictionary in enumerate(row):
            for key, value in dictionary.items():
                column_name = f"{col_name}_{key}_{j}"  # Create unique column names
                df.at[i, column_name] = value

    return df.drop(columns=[col_name])  # Optionally remove the original column


flattened_df = flatten_column_to_columns(df, 'location')
print(flattened_df)
