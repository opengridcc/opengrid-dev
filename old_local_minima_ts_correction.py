#  def local_minima_ts_correction(result_list):
#     start=time.time()
#     loop_index=0 #Loops throu"gh the resultslist, as long as its size
#     current_saves=0 #Current amount of variables saved
#     some_list=[]
#     df_result=pd.DataFrame(some_list)
#     ts=(list_view[0][2]-list_view[0][1])/10
#     threshold_value=(ts / np.timedelta64(1, 'm')).astype(int)
#     #SAVING ONLY RELEVANT VALUES       
#     while loop_index < len(result_list):
#         if(loop_index==0):
#             [value,start_time_stamp,stop_time_stamp] = [result_list[loop_index][0], result_list[loop_index][1], result_list[loop_index][2]]
#             df_result=df_result.append(pd.DataFrame([[value, start_time_stamp,stop_time_stamp]], index=[current_saves], columns=['Manhattan','startTimeStamp','stopTimeStamp']))
#             current_saves=current_saves+1
#         if(result_list[loop_index-1][0] < result_list[loop_index-2][0]) and (result_list[loop_index-1][0] < result_list[loop_index][0]) and result_list[loop_index-1][0] < df_result.max()['Manhattan']:
#             #print "Value", resultList[loopIndex-1][0],",Index:",loopIndex-1,"has a lower value than value left and right to it.(",resultList[loopIndex-2][0],",",resultList[loopIndex][0],") nIt will now replace", dfResult['Euclidean'].max(),"in the dataset."
#             [value,start_time_stamp,stop_time_stamp] = [result_list[loop_index-1][0], result_list[loop_index-1][1], result_list[loop_index-1][2]]
#             list_with_values=[]
#             i=0
#             max_value=0
#             #!!!Timestamps are important. If timestamp is within the range of another timestamp already present,
#             #they will overwrite eachother instead of adding a new unique value
            
#             #Loop until at start
#             for i in range(0, df_result.index.size):
#                 if(start_time_stamp >= df_result['startTimeStamp'][i]) and (start_time_stamp <= df_result['stopTimeStamp'][i]-pd.Timedelta(minutes=threshold_value)):
#                     #INSIDE BOUNDARIES
#                     if(df_result.loc[i][0] >= max_value): #Store the maximum value, of the range between start and stoptimestamp.
#                         max_value=df_result.loc[i][0]
#                         ts=df_result.loc[i][1]
#             if(max_value==0): 
#                 #OUTSIDE BOUNDARIES
#                     df_result=df_result.append(pd.DataFrame([[value, start_time_stamp,stop_time_stamp]], index=[current_saves], columns=['Manhattan','startTimeStamp','stopTimeStamp']))
#                     current_saves=current_saves+1
#                 #INSIDE BOUNDARIES - 
#             elif(value < max_value): #Check if the current value is smaller than the Maximum value encountered. Replace if it is.
#                     df_result.loc[df_result['Manhattan']== max_value] = [value, start_time_stamp, stop_time_stamp]
#         loop_index=loop_index+1
#     df_result=df_result.sort_values(['Manhattan'])
#     print time.time()-start
#     return df_result
        