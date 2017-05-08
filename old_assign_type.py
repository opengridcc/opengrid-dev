def assign_type(df, blocks_list):
    #types of blocks
    type_block = 0
    #contains the list with the types from the original dataframe (type_ori)
    list_types_ori = []
    #new dataframe created with types for each similar block (type_block)
    df_types_block =[]
    df_types_block = pd.DataFrame(df_types_block)
    for i in range(0, df.index.size):
        start_ts = df.iloc[i]['start']
        stop_ts = df.iloc[i]['stop']
        #Storing type_ori - used for searching
        type_in_df_ori = df.iloc[i]['original']
        #Finding your type in the list with saved types_ori
        find_type = [row[0] for row in list_types_ori]   
            
        if(type_in_df_ori not in find_type):
            current_type_block = type_block
            #Find the start and stop timestamps of the block in the blocklist
            ind = blocks_list.loc[blocks_list['Type']==type_in_df_ori].index[0]
            start_ts_ori = pd.Timestamp(blocks_list.iloc[ind]['start'])
            stop_ts_ori = pd.Timestamp(blocks_list.iloc[ind]['stop'])
            #add type_ori to list_types_ori so that it cannot be assigned again
            #assign type_new to this type_ori
            list_types_ori.append([type_in_df_ori, type_block, start_ts, stop_ts])
            #Store the data
            data = [[start_ts, stop_ts, current_type_block], [start_ts_ori, stop_ts_ori, current_type_block]]
            #augment type_block
            type_block = type_block +1
        else:
            #Type is already present: find the type_blocks associated with it!
            index = find_type.index(type_in_df_ori)
            #Find current_type, look in the list, dependent on the index of the ori value
            current_type_block = list_types_ori[index][1]
            #New data will not contain the ori now since it is already present
            data = [[start_ts, stop_ts, current_type_block]]
        df_types_block = df_types_block.append(pd.DataFrame(data, columns=('start','stop','type')))
    return df_types_block