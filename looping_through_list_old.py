 def looping_through_list(df_with_values, array_to_compare):
    start=time.time()
    #Create list where values on which the different methods will act will be saved temporarily
    #This list will be cleared every time
    values_list=[]
    #Create list with results of the methods
    result_list=[]
    compare_to_array=np.array(array_to_compare)
    i=0 #Loops through list arrayToCompare.size times
    j=0 #Amount of values considered, and calculated.
    array_with_values=np.array(df_with_values)
    #start and stop timestamp
    starting_time_stamp=df_with_values.index[0]
    stop_time_stamp=df_with_values.index[array_to_compare.size-1]
    
    #Threshold
    threshold_value=array_to_compare.size/10
    #LOOPING THROUGH LIST
    while i < array_to_compare.size+j: #i is dependent on j, i updates as j updates.
        #Save x amount of values where x is the size of the array to compare.
        values_list.append(([array_with_values[i][0]]))
        i=i+1
        if(i==(array_to_compare.size+j)) and (i<(df_with_values.size)):
            #j = the minute at this moment. i = starting from the current minute, adding the size of the array to compare.
            #Stops running when the limit of values to be considered is reached, being the size the original array.
            if(j==0) or (manhattanDistance2(compare_to_array,values_list)!=result_list[len(result_list)-1][0]):
                #Create list with unique values. Save them in "resultList". Euclidean score, startTimestamp, stopTimestamp
                result_list.append([manhattanDistance2(compare_to_array,values_list), starting_time_stamp,stop_time_stamp]) 
            j=j+1
            starting_time_stamp=df_with_values.index[j] #startingTimeStamp: current minute considered
            stop_time_stamp=df_with_values.index[i] #stopTimeStamp: current minute considered + size of array to compare.
            i=j
            values_list=[]
    print time.time()-start
    return result_list