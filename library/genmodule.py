# -*- coding: utf-8 -*-
"""
	
    <author>
    <Date>
    Directory, and functions  to list default and proposed units for transformation and visualisation    e.g. Flukso units, plotting units and SI units
	
	Format of directory: 
	UNITS
	[utility= 'water', 'gas', 'electricity']
	[ref = 'base','int','diff']
	[usage= 'fl','si','pl', 'tm','cost']
	[what= 'str','cf']
# 'cf' returns conversion factor, to go TO this unit from SI base units.
# 'str' returns a string with units of this combination utility/ref/usage. 

# See demo notebook for more examples!
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
wflb = {'str':'l_w/day ' ,'cf':(1000.*24.*3600.),None:'Unknown' }
wtmb = {'str':'l_w/h' ,'cf':(1000.*3600.),None:'Unknown' }
wplb  = {'str':'l_w/min' ,'cf':(1000.*60. ),None:'Unknown'}

#  base SI units, FL units, and plotting units  for gas
gsib  = {'str':'m³_g/s' ,'cf':1./1. ,None:'Unknown'}
gflb = {'str':'l_g/day' ,'cf':(1000.*24.*3600.) ,None:'Unknown'}
gtmb = {'str':'l_g/h' ,'cf':(1000.*3600.),None:'Unknown' }
gplb  = {'str':'kW_aver_g(/min)(@11kWh/m³)' ,'cf':(11*60./1000.) ,None:'Unknown'}

#  base SI units, FL units,and plotting units for electricity
esib  = {'str':'J_e/s' ,'cf':1./1. ,None:'Unknown'}
eflb = {'str':'W_aver_e (/s)' ,'cf':1./(1.) ,'info':'base flukso unit. CF to SI units',None:'Unknown'}
etmb = {'str':'Wh_aver_e/min' ,'cf':60./(3600.) ,'info':'tmpo=dash flukso unit (to check). CF to SI units',None:'Unknown'}
eplb  = {'str':'kW_aver_e(/s)' ,'cf':1/1000.,None:'Unknown'}

int_timebase = 's'
#  integrated SI units (cf for integration per second)
wsii = {'str':'m³_w','cf':(1),'info':'Integrated per second; against base SI units (m³/s) integrated over time',None:'Unknown'}
gsii = {'str':'m³_g','cf':(1),None:'Unknown'} # integrated SI Base units per SEC = consumption per sec * cf
esii = {'str':'J_e','cf':(1),None:'Unknown'} # integrated  SI Base units per SEC = average per  * cf

#  differentiated SI units (not really usefull for base sensors)
wsid = {'str':'m³_w*s','cf':(1),'info':'Differentated water usage per second; against base SI units (m³/s) (not really usefull for base sensors)',None:'Unknown'}
gsid = {'str':'m³_g*s','cf':(1),'info':'Differentated gas usage per second; against base SI units (m³/s) (not really usefull for base sensors)',None:'Unknown'} # integrated SI Base units per SEC = consumption per sec * cf
esid = {'str':'J*s','cf':(1),'info':'Differentated electricity  per second; against base SI units (m³/s) (not really usefull for base sensors)',None:'Unknown'} # integrated  SI Base units per SEC = average per  * cf

#  Base cost for unit quantities for water, gas, elec
wcob = {'str':'€/s','cf':35.,'info':'cost estimate of integrated utility in SI units (€/m³ *m³/s',None:'Unknown'}
gcob = {'str':'€/s','cf':0.05,None:'Unknown'}
ecob = {'str':'€/s','cf':0.15/3600./1000.,None:'Unknown'}


#integrated and diff costs derived from base si costs (*sic)




#constructors of nested dictionary
#Note: diff and int based solely on SI units! 
#Thus, if unavailable, first convert to SI factors, and convert to other base
def dict_add_int_diff(basedict=None,si_dict=None):
    """output: gfl dictionary, based on base and si int/diff conversion. """
    return {'base':basedict,'int':{'cf': basedict['cf']*si_dict['int']['cf'] , 'str':"".join([basedict['str'],'*s'])},'diff':{'cf': basedict['cf']*si_dict['diff']['cf'] , 'str':"".join([basedict['str'],'/s'])}}

wsi ={'base': wsib ,'int':wsii,'diff': wsid}
wfl = dict_add_int_diff(wflb,wsi)
wpl = dict_add_int_diff(wplb,wsi)
wtm = dict_add_int_diff(wtmb,wsi)
wco =  dict_add_int_diff(wcob,wsi)

gsi ={'base': gsib ,'int':gsii,'diff': gsid}
gfl = dict_add_int_diff(gflb,gsi)
gpl = dict_add_int_diff(gplb,gsi)
gtm = dict_add_int_diff(gtmb,gsi)
gco = dict_add_int_diff(gcob,gsi)

esi ={'base': esib ,'int':esii,'diff': esid}
efl = dict_add_int_diff(eflb,esi)
epl = dict_add_int_diff(eplb,esi)
etm = dict_add_int_diff(etmb,esi)
eco =  dict_add_int_diff(ecob,esi) 

#Optional totos:
#add [der: for e.g temperature sensors (°Caverage/min),
#add other [timebase ='s','min', 'hr', '']

wdict ={'fl':wfl,'si':wsi,'pl':wpl,'tm':wtm,'cost':wco}
gdict ={'fl':gfl,'si':gsi,'pl':gpl,'tm':gtm,'cost':gco}
edict ={'fl':efl,'si':esi,'pl':epl,'tm':etm,'cost':eco}

UNITS = {'water':wdict, 'gas':gdict,'electricity':edict}

#some simpler /shorter lists:
UtilityTypes = UNITS.keys() # {'water','gas','electricity', ...} 
chosen_types = [0,1,2] # arange(0,len(UtilityTypes)) #len 3 atm, can become more options

utilitytypes_dict = dict(zip(UtilityTypes,chosen_types))
utilitytypebynr_dict = dict(zip(chosen_types,UtilityTypes))

def get_unitdict(**kwargs ):
    return UNITS

def query_utility(util = ' '): #get_units(self,util,usage = 'fl',ref='base', what= 'str'):
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



def get_units(util,usage = 'fl',ref='base', what= 'str'): #get_units(util,usage = 'fl',ref='base', what= 'str',qty = 1)
    '''
    Purpose:
    Return units and conversion factors (TO a unit) for Opengrid.
    
    Input options: 
    [utility= 'water', 'gas', 'electricity']. Obligatory input.
    [ref = 'base','int','diff'] . Default: 'base'
    [usage= 'fl','si','pl','tm','cost']. Default: 'fl'
    [what= 'str','cf']; Default: 'str'
	qty = default 1. Multiplier to units
	
    
    Outputs: 
    If what= 'str' (default), then string of default units
    If what= 'cv', then conversion factor from base SI units TO this unit    
    '''
    utility=  query_utility(util)
    return UNITS[utility][usage][ref][what]

#Some examples:
#print  get_units('electricity',ref='base',usage='si', what= 'str')
#print get_units('water',ref='cost', what= 'cf') , get_units('water',ref='cost', what= 'str')
#print get_units(2)


def get_conversionfactor(util,fromusage = 'fl',fromref='base',tousage = None,toref=None,what='cf',str_incl_units =False,qty=1): # get_conversionfactor(util,fromusage = 'fl',fromref='base',tousage = None,toref=None,what='cf',str_incl_units =False,qty=1)
    '''    
	Syntax:
    get_conversionfactor(util,fromusage = 'fl',fromref='base',tousage = None,toref=None,what='cf',str_incl_units =False,qty=1):
    
    Purpose:
    Return conversion factors and/or units from one unitbase to another for Opengrid.
    
    Input options: 
    utility= ['water', 'gas', 'electricity']. Obligatory input.
    fromref = ['base','int','diff'] . Default: 'base'
    toref = ['base','int','diff'] . Default: fromref
    fromusage= ['fl','SI','pl','cost','tm']. Default: 'fl'
    tousage= '[fl','SI','pl','cost', 'tm']. Default:fromusage
    what=['cf','str',info']. Default= 'cf'
    str_incl_units. [True, False] If true, ouput is (human readable) string with CF and units. Default False
    qty = 1 multiplication factor
        
    Outputs: 
    If str_incl_units = false (default), output is conversion factor FROM unit (utility fromref, fromsage) 1 
    TO unit 2, defined by (utility toref, tousage) .
    
    If str_incl_units = true, output is converion factor, and FROM and TO units, in str format.
    '''
    utility= query_utility(util)
    if what=='str':
        unitsa = get_units(utility, usage = fromusage,ref=fromref, what='str')   
        unitsb = get_units(utility, usage = tousage,ref=toref,what='str')
        return "".join([unitsb, ' ',unitsa])
    if tousage == None:
        tousage = fromusage
    if toref == None:
        toref = fromref
    if ((fromref =='base') & (toref == 'base')):
        cftoA = get_units(utility, usage = fromusage,ref=fromref, what='cf')   
        cftoB = get_units(utility, usage = tousage,ref=toref,what='cf')
        CF =  cftoB / cftoA
		
    else: # at least one diff or int => go trhough SI units
         # since unitcost and int are based on SI units: convert to usage: SI and ref:base between A and B first
        SI_int = 1
        A_to_SI_CF =  get_units(utility, usage = 'si',ref='base',what='cf')/get_units(utility, usage = fromusage,ref=fromref,what='cf')
        SI_to_B_CF =  get_units(utility, usage = tousage,ref=toref,what='cf')/get_units(utility, usage = 'si',ref='base',what='cf')
        if not(toref == 'base'):
            SI_int = SI_int*get_units(utility,usage ='si',ref=toref,what='cf')
        if not (fromref == 'base'): #int or diff
            SI_int = SI_int/ get_units(utility,usage ='si',ref=fromref,what='cf')
        CF =  A_to_SI_CF *SI_to_B_CF *SI_int

    if str_incl_units  == False:
        return CF*qty
    else:
        unitsa = get_units(utility, usage = fromusage,ref=fromref, what='str')   
        unitsb = get_units(utility, usage = tousage,ref=toref,what='str')
        if toref == 'int': 
            timebase = '(integrated over time)'
        elif toref == 'diff':
            timebase = '(differentiated over time)'
        else:
            timebase = '' #base
        return " ".join([str(qty), unitsa,'corresponds to', str(CF*qty),unitsb,timebase])
#some tests
#print get_conversionfactor(2), 'convert to itself  (should be 1)'
#print get_conversionfactor(1,fromusage = 'si', fromref='base',toref='cost') , get_units(1,ref='cost'), ' (Should return 0.15€/kWhe)'

#examples
#print get_conversionfactor(1,fromusage ='fl', tousage='si',toref='int',str_incl_units =True)

#print 'A gas consumption of 1000*24*60*60',get_units(2,usage='fl'), 'during one second equals ',
#print 1000*24*60*60*get_conversionfactor(2,fromusage ='fl',toref='int'),get_units(2,usage='fl',ref='int')

#print 'A water consumption of 60',get_units(0,usage='pl'), 'during equals a cost of ',
#print get_conversionfactor(0,fromusage ='pl',toref='cost', str_incl_units=False)*60, '€'


