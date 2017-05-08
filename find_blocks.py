# def find_blocks(df_parent, row_parent, blocks, df_original, first_time = True):
#     min_lvl = 0
#     start = False
    
#     block_start = 0
#     block_end = 0
    
#     nr_of_blocks_start = blocks.size
    
#     nested = row_parent
    
#     if first_time:
#         start = True
#         min_lvl = df_parent['repeatedValues'].min()
        
#     #append last value again
#     post_index = df_parent.index[-1] + pd.Timedelta(minutes=1)

#     temp = pd.DataFrame(data=[df_parent.iloc[-1]], index=[post_index], columns=['repeatedValues'])
#     df_parent = df_parent.append(temp)

#     df_parent.sort_index(inplace=True)

#     for i in range(1, df_parent.size - 1):
#         if start == False and df_parent['repeatedValues'].iloc[i - 1] - df_parent['repeatedValues'].iloc[i] == 0:
#             min_lvl = df_parent['repeatedValues'].iloc[i]
#             start = True
        
#         if start == True and df_parent['repeatedValues'].iloc[i] > min_lvl and df_parent['repeatedValues'].iloc[i - 1] == min_lvl:
#             block_start = df_parent.index[i - 1]
            
#         if start == True and block_start != 0 and df_parent['repeatedValues'].iloc[i] <= min_lvl:
#             block_end = df_parent.index[i]
            
#             #Match if the length is more than 10% less than the parent
#             temp = pd.DataFrame(data=[[str(block_start), str(block_end), nested]], columns=['start', 'stop', 'nested_in'])
            
#             if float(df_parent.index.size - df_parent.ix[block_start : block_end].index.size) / float(df_parent.index.size) > 0.10:
#                 if(block_end - block_start > pd.Timedelta(minutes=15)):
#                     #print [block_start, block_end]
#                     blocks = blocks.append(temp)
            
#             df_parent2 = df_original.ix[block_start : block_end]
#             row_parent = blocks.index.size - 1
#             blocks = find_blocks(df_parent2, row_parent, blocks, df_original, False)
#             blocks =  blocks.drop_duplicates(subset=['start', 'stop'], keep= 'first')
#             block_start = 0
#             block_end = 0
            
#         if start == True and block_start == 0 and df_parent['repeatedValues'].iloc[i] < min_lvl:
#             #Lvl dropped below min value so the min value was not assigned properly
#             if df_parent['repeatedValues'].iloc[i+1] > df_parent['repeatedValues'].iloc[i]:
                
#                 #Match if the length is more than 10% less than the parent
#                 temp = pd.DataFrame(data=[[str(df_parent.index[0]), str(df_parent.index[i]), nested]], columns=['start', 'stop', 'nested_in'])
            
#                 if float(df_parent.index.size - df_parent.ix[df_parent.index[0] : df_parent.index[i]].index.size) / float(df_parent.index.size) > 0.10:
#                     if(df_parent.index[i]-df_parent.index[0] > pd.Timedelta(minutes=15)):
#                         #print [df_parent.index[i]-df_parent.index[0]]
#                         blocks = blocks.append(temp)
                
#                 min_lvl = df_parent['repeatedValues'].iloc[i]
                
    
#     return blocks