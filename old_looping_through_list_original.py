# def looping_through_list_original(df_list_blocks):
#     start_time = time.time()
#     time_now = time.time()
#     #Create list of costs
#     cost_list = []
#     #Creating variable 'j'. This will make sure we don't check the same frames twice.
#     j=0
#     #Other variable
#     k=0
#     for i in range(0, df_list_blocks.index.size):
#         start = df_list_blocks.iloc[i][0]
#         stop = df_list_blocks.iloc[i][1]
#         #This will create a dataframe with all the values between the start and stop timestamp.
#         #This is used for comparing these values using a similarity algorithm with the others
#         df_original = df_el.ix[pd.Timestamp(start):pd.Timestamp(stop)]
#         type_original = df_list_blocks.iloc[i][3]
#         print type_original
#         if(k==1):
#             print "After type: ", j, "we will raise 'j' so that the next type ", j+1, "won't be compared again with type ", j
#             j=j+1
#         for i in range(j, df_list_blocks.index.size):
#             df_new = df_el.ix[pd.Timestamp(df_list_blocks.iloc[i][0]):pd.Timestamp(df_list_blocks.iloc[i][1])]
#             if(df_new.index.size > df_original.index.size):
# #                 print "looping"
#                 result = looping_through_list(df_new, df_original)
#                 if(min(result)[0] not in [row[0][0] for row in cost_list]):
#                     cost_list.append((min(result), ('Original: Type', type_original, 'against type', df_list_blocks.iloc[i][3])))
#             elif(df_new.index.size < df_original.index.size):
# #                 print "looping"
#                 result = looping_through_list(df_original, df_new)
#                 if(min(result)[0] not in [row[0][0] for row in cost_list]):
#                     cost_list.append((min(result), ('Substitute: Type', df_list_blocks.iloc[i][3], 'against original type', type_original)))
#             k=1
#     print  "Time to complete: ", time.time() - start_time
#     return cost_list