# -*- coding: utf-8 -*-
"""
	
    <author>
    <Date>
    Directory, and functions  to list default and proposed units for transformation and visualisation    e.g. Flukso units, plotting units and SI units
	
	Format of directory: 
	UNITS
	[utility= 'water', 'gas', 'electricity']
	[ref = 'base','int','cost']
	[usage= 'fl','SI','pl']
	[what= 'str','cf']
# 'cf' returns conversion factor, to go TO this unit from SI base units.
# 'str' returns a string with units of this combination utility/ref/usage. 

# See demo notebook for more examples)
    
"""


def main(self,**kwargs ):
    """
    if call withouth options => empty?
    """

def __init__(self,**kwargs ):
    """
    Parameters
    ----------
    * utility : String of either 'electricity', 'gas', 'water'
    * chosen_type : Number 0 to 2
    
    """
    # Creation of dictionary of units and conversion factors, for units 
    import numpy

#  base SI units, FL units, and plotting units  for water. SI units always based per second.
wsib  = {'str':'m³_w/s' ,'cf':1./(1. ),None:'Unknown'}
wflb = {'str':'l_w/day ' ,'cf':1/(1000.*24.*3600.),None:'Unknown' }
wplb  = {'str':'l_w/min' ,'cf':1/(1000.*60. ),None:'Unknown'}

#  base SI units, FL units, and plotting units  for gas
gsib  = {'str':'m³_g/s' ,'cf':1 ,None:'Unknown'}
gflb = {'str':'l_g/day' ,'cf':1/(1*1000.*24.*3600.) ,None:'Unknown'}
gplb  = {'str':'kW_aver_g(/min)(@11kWh/m³)' ,'cf':1/(11*60.) ,None:'Unknown'}

#  base SI units, FL units,and plotting units  for electricity
esib  = {'str':'J_e/s' ,'cf':1 ,None:'Unknown'}
eflb = {'str':'W_aver_e (/s)' ,'cf':1/(1.) ,'info':'base flukso unit. CF to SI units',None:'Unknown'}
eplb  = {'str':'kW_aver_e(/s)' ,'cf':1/(1000.),None:'Unknown'}

#  Base costs of unit quantities for water, gas, elec
wsic = {'str':'€/m³_w','cf':35.,'info':'cost estimate of integrated utility',None:'Unknown'}
gsic = {'str':'€/m³_g ','cf':0.05,None:'Unknown'}
esic = {'str':'€/J','cf':0.15/3600.,None:'Unknown'}
#  integrated SI units (cf for integration per second)
wsii = {'str':'m³_w','cf':(1),'info':'Integrated per second; against base SI units (per seconds) integrated over time',None:'Unknown'}
gsii = {'str':'m³_g','cf':(1),None:'Unknown'} # integrated SI Base units per SEC = consumption per sec * cf
esii = {'str':'kWh_e','cf':(1/3600.),None:'Unknown'} # integrated  SI Base units per SEC = average per  * cf

#constructors of nested dictionary
#Note: cost and int based solely on SI units! Thus, for integrated CF, first convert to SI factors!!

wfl = {'base': wflb,'int':wsii,'cost': wsic} 
wsi ={'base': wsib ,'int':wsii,'cost': wsic}
wpl = {'base':wplb,'int':wsii,'cost': wsic}

gfl = {'base': gflb,'int':gsii,'cost': gsic}
gsi ={'base': gsib ,'int':gsii,'cost': gsic}
gpl = {'base':gplb,'int':gsii,'cost': gsic}

efl = {'base': eflb,'int':esii,'cost': esic}
esi ={'base': esib ,'int':esii,'cost': esic}
epl = {'base':eplb,'int':esii,'cost': esic}

#Optional totos:
#add [der: for e.g temperature sensors (°Caverage/min),
#add other [timebase ='s','min', 'hr', '']

wdict ={'fl':wfl,'SI':wsi,'pl':wpl}
gdict ={'fl':gfl,'SI':gsi,'pl':gpl}
edict ={'fl':efl,'SI':esi,'pl':epl}

UNITS = {'water':wdict, 'gas':gdict,'electricity':edict}

#some simpler /shorter lists:
UtilityTypes = UNITS.keys() # {'water','gas','electricity', ...} 
chosen_types = [0,1,2] # arange(0,len(UtilityTypes)) #len 3 atm, can become more options

utilitytypes_dict = dict(zip(UtilityTypes,chosen_types))
utilitytypebynr_dict = dict(zip(chosen_types,UtilityTypes))

def get_unitdict(**kwargs ):
    return UNITS


#Some helper functions for dict calls:

def query_utility(util = ' '):
    '''
    Syntax:
    get_units(self,util,usage = 'fl',ref='base', what= 'str'):
    
    Purpose:
     Find (full) name of utility, either from number or from (partial) name (possible enhancement).
    
    Input: 
    * util: input string, or a number (0 to 2) 

    Output:
    Utility type string.
    If util unknown, returns valueerror
'''
    #utilitytypebynr_dict = {0:'water',1: 'gas',2:'electricity'} 
 
    for utility in utilitytypes_dict:
        chosen_type = utilitytypes_dict[utility]
        if utility == util:
            return utility
        elif chosen_type == util:
            return utility  
    #if all else fails: (no match)
    return ValueError(" ".join([util,'unknown. Please specify a valid Utility string,e.g. ''water'' or an integer, e.g. 2']))

#examples        
#print sensortype(0) , sensortype('electricity')
#sensortype('somethingelse')



def get_units(util,usage = 'fl',ref='base', what= 'str'):
    '''
    Purpose:
    Return units and conversion factors (TO a unit) for Opengrid.
    
    Input options: 
    [utility= 'water', 'gas', 'electricity']. Obligatory input.
    [ref = 'base','int','cost'] . Default: 'base'
    [usage= 'fl','SI','pl']. Default: 'fl'
    [what= 'str','cf']; Default: 'str'
    Utility is obligatory  
    
    Outputs: 
    If what= 'str' (default), then string of default units
    If what= 'cv', then conversion factor from base SI units TO this unit    
    '''
    utility=  query_utility(util)
    return UNITS[utility][usage][ref][what]

#Some examples:
#print  get_units('electricity',ref='base',usage='SI', what= 'str')
#print get_units('water',ref='cost', what= 'cf') , get_units('water',ref='cost', what= 'str')
#print get_units(2)


def get_conversionfactor(util,fromusage = 'fl',fromref='base',tousage = None,toref=None,str_incl_units =False):
    '''
    Purpose:
    Return conversion factors from one unitbase to another for Opengrid.
    
    Input options: 
    [utility= 'water', 'gas', 'electricity']. Obligatory input.
    [fromref = 'base','int','cost'] . Default: 'base'
    [toref = 'base','int','cost'] . Default: fromref
    [fromusage= 'fl','SI','pl']. Default: 'fl'
    [tousage= 'fl','SI','pl']. Default:fromusage
    str_incl_units. If true, ouput is string Default False
        
    Outputs: 
    If str_incl_units = false (default), output is conversion factor FROM unit (utility fromref, fromsage) 1 
    TO unit 2, defined by (utility toref, tousage) .
    
    If str_incl_units = true, output is converion factor, and FROM and TO units, in str format.
    '''
    utility= query_utility(util)
    if tousage == None:
        tousage = fromusage
    if toref == None:
        toref = fromref
    if (toref == 'int') | (fromref == 'int') | (toref == 'cost') |(fromref == 'cost') :
        SI_cost = get_units(utility,usage ='SI',ref='cost',what='cf')
        SI_int = get_units(utility,usage ='SI',ref='cost',what='cf')
         # since unitcost or int based on SI units: convert to base SI between A and B first
        A_to_SI_CF =  get_units(utility, usage = 'SI',ref=fromref,what='cf')/ get_units(utility, usage = fromusage,ref=fromref,what='cf')
        SI_to_B_CF =  get_units(utility, usage = 'SI',ref=toref,what='cf')/get_units(utility, usage = tousage,ref=toref,what='cf')
        if (toref == 'int'):
            SI_int = 1/get_units(utility,usage ='SI',ref='int',what='cf')
        if (fromref == 'int'):
            SI_int = get_units(utility,usage ='SI',ref='int',what='cf')
        if (toref == 'cost'):
            SI_cost = 1/get_units(utility,usage ='SI',ref='cost',what='cf')
        if (fromref == 'cost'):
            SI_cost = get_units(utility,usage ='SI',ref='cost',what='cf')

        CF =  A_to_SI_CF *SI_to_B_CF* SI_cost *SI_int
    else: # direct one step convers
        cftoA = get_units(utility, usage = fromusage,ref=fromref, what='cf')   
        cftoB = get_units(utility, usage = tousage,ref=toref,what='cf')
        CF =  cftoB / cftoA
    
    if str_incl_units  == False:
        return CF
    else:
        unitsa = get_units(utility, usage = fromusage,ref=fromref, what='str')   
        unitsb = get_units(utility, usage = tousage,ref=toref,what='str')
        if toref == 'int': 
            persec = '(integrated)'
        else:
            persec = ''
        return " ".join([str(CF), unitsa,'corresponds to 1',unitsb,persec])
#some tests
#print get_conversionfactor(2), 'convert to itself  (should be 1)'
#print get_conversionfactor(1,fromusage = 'SI', fromref='base',toref='cost') , get_units(1,ref='cost'), ' (Should return 0.15€/kWhe)'

#examples
#print get_conversionfactor(1,fromusage ='fl', tousage='SI',toref='int',str_incl_units =True)

#print 'A gas consumption of 1000*24*60*60',get_units(2,usage='fl'), 'during one second equals ',
#print 1000*24*60*60*get_conversionfactor(2,fromusage ='fl',toref='int'),get_units(2,usage='fl',ref='int')

#print 'A water consumption of 60',get_units(0,usage='pl'), 'during equals a cost of ',
#print get_conversionfactor(0,fromusage ='pl',toref='cost', str_incl_units=False)*60, '€'


def sensortype(var = []):
    '''
    Used to find (full) name of sensortype, either from number or from partial name.
    Input:
    * var: input string, or a number (0 to 2) 
    OUTPUT:
    * utility: returns string of utility type.
    If unknown, returns valueerror or keyerror
    '''
    for utility in utilitytypes_dict:
        if utility == var:
            #self.utility = utility
            chosen_type = utilitytypes_dict[utility]
            return utility
        elif chosen_type == var:
            #self.utility = utility
            return utility  
    #if all else fails: (no match)
    return KeyError(" ".join([var, 'unknown']))

#examples        
#print sensortype(0) , sensortype('electricity')
#sensortype('somethingelse')
