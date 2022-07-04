# %load ./AnalgRxns.py 

from decimal import Decimal, ROUND_HALF_UP
import math
import copy
from MainFunctions import getcompdict,CustomError
import os
import sqlite3
import pandas as pd
import ray
import modin.pandas as mpd
from ReaxysAPIv2 import main__,initray

def getanaloguerxns(rxnsource,combinedpool,combinedpoolex=None, workflow='strict',returnall=True,
                    reaxys_update=True,refanaloguerxns=None,ncpus=16,restart=True): #Done
    '''
    Retrieves analogue reactions containing analogue reactants and, optionally, reagents given a reaction database (rxnsource), 
    and an analogue species pool (combinedpool). Returns a dictionary containing analogue reaction lists and analogue reactions
    for each indicated workflow (refer below)
    
    combinedpoolex refers to an extended list of species, including combinedpool, 
    that includes species exempted from the search (eg. catalysts, misclassified reagents etc.)

    workflow can be either 'strict' (Reactants and reagents need to be analogue, considering combinedpoolex);
    'strictest' (Reactants and reagents need to be analogue, considering only combinedpool);
    'loose' (Reactants need to be analogue but if any reagent is analogue this is accepted; 
            considering combinedpoolex);
    'loosest' (Only reactants need to be analogue)
    Specify returnall as true if all above workflows are executed and returned, although only user-specified workflow will
    be used to retrieve analogue reactions
    reaxys_update determines if cross-validation with Reaxys (using API) is required
    refanaloguerxns refers to a reference pandas dataframe of updated analogue reactions to bypass reaxys API updates (as this is slow).
    Leave this as None if the most up-to-date information is required
    ncpus indicates how many CPUs or cores for parallel execution
    
    '''
    if ncpus>1:
        if restart:
            initray(num_cpus=ncpus)
    if type(rxnsource)==str:
        rxndat=pd.read_pickle(rxnsource)
    elif type(rxnsource)==pd.core.frame.DataFrame:
        rxndat=rxnsource
    if ncpus>1:
        if not rxndat.index.name and not rxndat.index.names:
            rxndat.set_index('ReactionID',inplace=True)
        rxndatdis=mpd.DataFrame(rxndat)
    else:
        rxndatdis=rxndat
    if workflow not in ['loosest','loose','strict','strictest']:
        raise CustomError('Please supply an acceptable workflow (loosest/loose/strict/strictest)') 
    if returnall:
        workflows=['loosest','loose','strict','strictest']
    else:
        workflows=[workflow]
    analgrxnsdict={}
    analgidsdict={}
    analoguerxnsraw=pd.DataFrame()
    errorlist=[]
    for i,workflow_ in enumerate(workflows):
        relevance_s=workflow_
        if reaxys_update: #Reaxys update splits reaction conditions into separate rows
            relevance_m='loosest'
        else:
            relevance_m=workflow_

        workflowlist=rxndatdis.apply(checkanaloguerxns,combinedpool=combinedpool,combinedpoolex=combinedpoolex,
                                    relevance_s=workflow_,relevance_m=workflow_,axis=1,result_type='reduce')
        workflowlist=pd.Series(data=workflowlist.values,index=workflowlist.index)
        workflowlist=workflowlist[workflowlist.values==True].index
        analoguerxns=rxndat[rxndat.index.isin(workflowlist)].copy()
        if reaxys_update:
            analoguerxns=updateanaloguerxns(analoguerxns,refanaloguerxns=refanaloguerxns) #Updates using Reaxys API
            if i==0:
                analoguerxnsraw=analoguerxns
#                 if returnall or workflow_=='loosest':
#                     analoguerxnsraw=analoguerxns
#                 else:
#                     analoguerxnsraw=pd.DataFrame()
            if ncpus>1:
                initray(num_cpus=ncpus) #Not sure how to add more workers
                analoguerxnsdis=mpd.DataFrame(analoguerxns)
            else:
                analoguerxnsdis=analoguerxns
            relevance_m=workflow_
            workflowlist=analoguerxnsdis.apply(checkanaloguerxns,combinedpool=combinedpool,combinedpoolex=combinedpoolex,
                                                relevance_s=workflow_,relevance_m=workflow_,axis=1,result_type='reduce')
            workflowlist=pd.Series(data=workflowlist.values,index=workflowlist.index)
            workflowlist=workflowlist[workflowlist.values==True].index
            analoguerxns=analoguerxns[analoguerxns.index.isin(workflowlist)].copy()
            reaxys_update=False
        else:
            if not analoguerxns.index.name and not analoguerxns.index.names:
                analoguerxns.set_index('ReactionID',inplace=True)
        analgidsdict.update({workflow_:list(workflowlist)})
        analgrxnsdict.update({workflow_:analoguerxns})
        if returnall: #Every iteration is a subset of generated analogue reactions
            rxndat=analoguerxns
            if ncpus>1:
                rxndatdis=mpd.DataFrame(rxndat)
            else:
                rxndatdis=rxndat
    return analgidsdict,analgrxnsdict,analoguerxnsraw

def filteranaloguerxns(analoguerxns,unresolvedids,reaxys_update=False,exemptionlist=[],filltemp=True,ambienttemp=20,
                       ncpus=16,restart=True):
    '''
    Filters and cleans analogue reactions by removing entries without reactants, products, or invalid species. Also removes
    entries without any condition information. 
    
    unresolvedids are needed to remove invalid species
    If reaxys_update is True, then missing reactants/products/reagents (text) can be retrieved and reactions can be removed in these
    cases
    
    exemptionlist refers to a list of compounds that are exempted from filtering/cleaning (eg. catalysts)
    
    Specify filltemp as True and ambient temperature if records with ambient temperature (as notes) need to be translated
    
    '''
    if ncpus>1:
        if restart:
            initray(num_cpus=ncpus)
    originalen=len(analoguerxns.index)
# Removing entries with missing species information
    analoguerxns=analoguerxns.loc[(analoguerxns.ReactantID.astype(bool)) & (analoguerxns.ProductID.astype(bool))]
    if reaxys_update:
        analoguerxns=analoguerxns.loc[(~analoguerxns.MissingReactant.astype(bool)) & (~analoguerxns.MissingProduct.astype(bool)) & (~analoguerxns.MissingReagent.astype(bool))]
# Completing temperature information    
        if filltemp:
            analoguerxns=filltemps(analoguerxns,ambienttemp=ambienttemp)
# Removing entries with all conditions missing (reagents, solvents, temperature, pressure, residence time, catalyst))
    analoguerxns=analoguerxns.loc[(analoguerxns.ReagentID.astype(bool)) | (analoguerxns.SolventID.astype(bool)) | (analoguerxns.Temperature.astype(bool))| (analoguerxns.Pressure.astype(bool))| (analoguerxns.ReactionTime.astype(bool))| (analoguerxns.CatalystID.astype(bool)) | (analoguerxns.MissingSolvent.astype(bool)) | (analoguerxns.MissingCatalyst.astype(bool))]

# Removing all entries with unresolved smiles)
    if ncpus>1:
        analoguerxnsdis=mpd.DataFrame(analoguerxns)
    else:
        analoguerxnsdis=analoguerxns
    unresolvedlist=analoguerxnsdis.apply(checkunresolved,unresolvedids=unresolvedids,exemptionlist=exemptionlist,axis=1,
                                         result_type='reduce')
    unresolvedlist=pd.Series(data=unresolvedlist.values,index=unresolvedlist.index) #Remove this if want to use modin/distributed throughout
    keeplist=unresolvedlist[unresolvedlist.values==False].index
    analoguerxns=analoguerxns[analoguerxns.index.isin(keeplist)]
    percentremaining=round((len(analoguerxns.index)/originalen)*100,2)
    print(str(percentremaining)+'% reactions remaining after cleaning')
    return analoguerxns


def addspeciesdata(analoguerxns,substancesource,includesolv=False,ncpus=16,restart=True,SQL=False,
                   reaxys_update=True,hc_Dict=None,hc_rct=None,refanaloguerxns=None): #Done
    '''
    Adds species data to each reaction (dictionary containing SMILES, formula, count, and atom types/count) given a substance
    source (substancesource) --MEMORY INTENSIVE
    
    Specify includesolve as True if solvent data is required
    ncpus indicates how many CPUs or cores for parallel execution
    Pass in an SQL connection under substancesource and put SQL as true if memory is low (NOT IMPLEMENTED YET)
    reaxys_update determines if cross-validation with Reaxys (using API) has been done before already
    hc_Dict is optional and contains a dictionary of product help compounds (small compounds) that will help in balancing later
    hc_rct is optional and contains a dictionary of reactant help compounds (small compounds) that will help in balancing later
    
    '''
    if ncpus>1:
        if restart:
            initray(num_cpus=ncpus)
    if not analoguerxns.index.name and not analoguerxns.index.names:
        idxreset=True
    else:
        idxreset=False
    idxcol=[]
    if reaxys_update:
        idxcol=['ReactionID','Instance']
    else:
        idxcol=['ReactionID']
    if refanaloguerxns is not None:
        analoguerxns,commondf=userefrxns(analoguerxns,idxcol=idxcol,refanaloguerxns=refanaloguerxns)
        import gc
        gc.collect()
        idxreset=False
    if not analoguerxns.empty:
        if type(substancesource)==str:
            if not SQL:
                DB=pd.read_pickle(substancesource)
            else:
                DB=sqlite3.connect(substancesource)
        elif type(substancesource)==pd.core.frame.DataFrame:
            DB=substancesource
        elif type(DBsource)==sqlite3.Connection:
            DB=substancesource
        if reaxys_update:
            if includesolv:
                cols=['ReactantID','ProductID','NumRefs','NumSteps','NumStages','ReagentID','SolventID']
            else:
                cols=['ReactantID','ProductID','NumRefs','NumSteps','NumStages','ReagentID']
        else:
            if includesolv:
                cols=['ReactantID','ProductID','NumRefs','NumSteps','ReagentID','SolventID']
            else:
                cols=['ReactantID','ProductID','NumRefs','NumSteps','ReagentID']
        analoguerxns_=copy.deepcopy(analoguerxns[cols])
        if ncpus>1:
            if not idxreset:
                analoguerxns_.reset_index(inplace=True)
                idxreset=True
            analoguerxnsdis_=mpd.DataFrame(analoguerxns_)
        else:
            analoguerxnsdis_=analoguerxns_
        Rdata=analoguerxnsdis_.apply(getspecdat,DB=DB,SQL=SQL,Rdata=True,Pdata=False,Rgtdata=False,Solvdata=False,axis=1,result_type='reduce')
        Pdata=analoguerxnsdis_.apply(getspecdat,DB=DB,SQL=SQL,Rdata=False,Pdata=True,Rgtdata=False,Solvdata=False,axis=1,result_type='reduce')
        Rgtdata=analoguerxnsdis_.apply(getspecdat,DB=DB,SQL=SQL,Rdata=False,Pdata=False,Rgtdata=True,Solvdata=False,axis=1,result_type='reduce')
        analoguerxns_['Rdata']=pd.DataFrame(data=Rdata.values,index=Rdata.index,columns=['Rdata'])
        analoguerxns_['Pdata']=pd.DataFrame(data=Pdata.values,index=Pdata.index,columns=['Pdata'])
        analoguerxns_['Rgtdata']=pd.DataFrame(data=Rgtdata.values,index=Rgtdata.index,columns=['Rgtdata'])
        if includesolv:
            Solvdata=analoguerxnsdis_.apply(getspecdat,DB=DB,SQL=SQL,Rdata=False,Pdata=False,Rgtdata=False,Solvdata=True,axis=1,result_type='reduce')
            analoguerxns_['Solvdata']=pd.DataFrame(data=Solvdata.values,index=Solvdata.index,columns=['Solvdata'])
        if hc_Dict is not None:
            analoguerxns_['hc_prod']=[hc_Dict]*len(analoguerxns_)
        if hc_rct is not None:
            analoguerxns_['hc_react']=[hc_rct]*len(analoguerxns_)
        if idxreset:
            analoguerxns_.set_index(idxcol,inplace=True)
        if refanaloguerxns is not None and not commondf.empty:
            analoguerxns_=pd.concat([analoguerxns_,commondf])
    else:
        analoguerxns_=commondf
    analoguerxns_=analoguerxns_.loc[(analoguerxns_.Rdata.astype(bool)) & (analoguerxns_.Pdata.astype(bool))] #For missing/invalid product ids
    return analoguerxns_

    
def filltemps(analoguerxns,ambienttemp=20): #Done
    '''
    Conditions notes entries might have temperature information (ambient temperature) that has not been transferred
    to the Temperature entry (specific to Reaxys). This function does this. 
    
    '''
    analoguerxns.loc[(analoguerxns.ConditionNotes.str.contains('ambient temperature',case=False)) \
                      & (~analoguerxns.Temperature.astype(bool)),'Temperature']=[[ambienttemp]] \
                        *len(analoguerxns.loc[(analoguerxns.ConditionNotes.str.contains('ambient temperature',case=False))\
                        & (~analoguerxns.Temperature.astype(bool))])
    return analoguerxns

     
def checkanaloguerxns(row,combinedpool,combinedpoolex=None,relevance_s='loose',relevance_m='loose'): #Done
    '''
    Given a row, checks if either rcts, or rcts and reagents are analogue based on an analogue pool (combinedpool);
    Include additional exemptions (eg. misclassified catalysts) under combinedpoolex.
    relevance_s is for single reference records, relevance_m is for multiple reference records
    For either option, specify relevance as:
    
    'loosest': Only reactants need to be analogue (combinedpool);
    'loose': Reactants need to be analogue but if any reagent is analogue this is accepted, 
             taking into account exemption list (combinedpoolex);
    'strict': Reactants and reagents need to be analogue, taking into account exemption list (combinedpoolex);
    'strictest': Reactants and reagents need to be analogue, not taking into account exemption list (combinedpool);
    
    ''' 
    if combinedpoolex is None:
        combinedpoolex=combinedpool
    rct=set()
    rct=set(row['ReactantID'])
    numrefs=row['NumRefs']
    if numrefs==1: #Single reference record
        relevance=relevance_s
    else: #Multiple reference record
        relevance=relevance_m
    if relevance=='loose':
        if row['ReagentID']!='NaN' and row['ReagentID']:
            matches=[val in combinedpoolex for val in set(row['ReagentID'])]
            if any(matches) and rct.issubset(combinedpool):
                return True
            else:
                return False
    if relevance=='strict':
        if row['ReagentID']!='NaN' and row['ReagentID']:
            matches=[val in combinedpoolex for val in set(row['ReagentID'])]
            if all(matches) and rct.issubset(combinedpool):
                return True
            else:
                return False
    if relevance=='strictest':
        if row['ReagentID']!='NaN' and row['ReagentID']:
            matches=[val in combinedpool for val in set(row['ReagentID'])]
            if all(matches) and rct.issubset(combinedpool):
                return True
            else:
                return False 
    if rct.issubset(combinedpool):
        return True
    else:
        return False


def userefrxns(analoguerxns,idxcol=['ReactionID'],refanaloguerxns=[pd.DataFrame()]): #Done
#     breakpoint()
    if type(refanaloguerxns)!=list:
        refanaloguerxns=[refanaloguerxns]
    refanaloguerxnslist=[]
    for refanaloguerxns_ in refanaloguerxns:
        if type(refanaloguerxns_)==str:
            refanaloguerxns_=pd.read_pickle(refanaloguerxns_)
        refanaloguerxnslist+=[refanaloguerxns_]
    refanaloguerxns=pd.concat(refanaloguerxnslist)
    refanaloguerxns = refanaloguerxns[~refanaloguerxns.index.duplicated(keep='first')]   
    if len(idxcol)==1:
        analogueidx=analoguerxns.index.name
        refidx=refanaloguerxns.index.name
        if not analogueidx:
            analogueidx=analoguerxns.index.names
        if not refidx:
            refidx=refanaloguerxns.index.names
        if analogueidx and analogueidx!=idxcol[0]:
            analoguerxns.reset_index(inplace=True)
            analoguerxns.set_index(idxcol,inplace=True)
        elif not analogueidx:
            analoguerxns.set_index(idxcol,inplace=True)
#         breakpoint()
        if not refanaloguerxns.empty:
            if refidx and refidx!=idxcol[0]:
                refanaloguerxns.reset_index(inplace=True)
                refanaloguerxns.set_index(idxcol,inplace=True)
            elif not refidx:
                refanaloguerxns.set_index(idxcol,inplace=True)
    elif len(idxcol)>1:
        analogueidx=analoguerxns.index.names
        if not analogueidx:
            analogueidx=analoguerxns.index.name
        refidx=refanaloguerxns.index.names
        if not refidx:
            refidx=refanaloguerxns.index.name
        if analogueidx and analogueidx!=idxcol:
            analoguerxns.reset_index(inplace=True)
            analoguerxns.set_index(idxcol,inplace=True)
        elif not analogueidx:
            analoguerxns.set_index(idxcol,inplace=True)
        if not refanaloguerxns.empty:
            if refidx and refidx!=idxcol:
                refanaloguerxns.reset_index(inplace=True)
                refanaloguerxns.set_index(idxcol,inplace=True)
            elif not refidx:
                refanaloguerxns.set_index(idxcol,inplace=True)
    commonids=set(refanaloguerxns.index).intersection(set(analoguerxns.index))
    commondf=refanaloguerxns[refanaloguerxns.index.isin(commonids)].copy()
    analoguerxns=analoguerxns[~analoguerxns.index.isin(commonids)].copy()
    return analoguerxns,commondf

def updateanaloguerxns(analoguerxns,formatting=True,refanaloguerxns=None,idxcol=['ReactionID']): #Done
    '''
    Calls the reaxys API to update analogue reactions (ReactionID should be the index)
    Specify formatting as true if formatting data types for columns is required
    Optionally include a reference UPDATED reaction dataframe (with no index)
    
    '''
    if refanaloguerxns is not None:
        analoguerxns,commondf=userefrxns(analoguerxns,idxcol=idxcol,refanaloguerxns=refanaloguerxns)
    if not analoguerxns.empty:
        rxn_ids=[str(ID) for ID in list(analoguerxns.index)]
        reaxys_final=[]
        while rxn_ids:
            if len(rxn_ids)>=5:
                nsessions=5
            else:
                nsessions=len(rxn_ids)    
            finalres=main__(nsessions,reaxys_ids=rxn_ids) #Calls API with 5 concurrent sessions, 100 IDs selected and retrieved at once
            reaxys_dat=[record for batch in finalres for record in batch[0]]
            errorlst=[errorid for batch in finalres for errorid in batch[1]]
            if not reaxys_dat:
                break
            if not errorlst or len(errorlst)==1:
                reaxys_final+=reaxys_dat
                break
            reaxys_final+=reaxys_dat
            rxn_ids=errorlst
        analoguerxns_updated=pd.DataFrame(reaxys_final)
        if formatting:
            for colname in ['ReactionID','NumRefs','NumSteps','NumStages']:
                analoguerxns_updated[colname]=analoguerxns_updated[colname].apply(pd.to_numeric)
            for colname in ['ReactantID','ProductID','ReagentID','SolventID','CatalystID','YearPublished']:
                analoguerxns_updated[colname]=analoguerxns_updated[colname].apply(lambda x: [int(ID) for ID in x])
            analoguerxns_updated['NameDict']=analoguerxns_updated['NameDict'].apply(lambda x: {int(key):val for key,val in x.items()})
            analoguerxns_updated['Yield']=analoguerxns_updated['Yield'].apply(lambda x: {int(key):float(val) for key,val in x.items()})
            analoguerxns_updated['Instance']=analoguerxns_updated.groupby('ReactionID').cumcount()
        analoguerxns_updated.set_index(idxcol,inplace=True)
        if refanaloguerxns is not None and not commondf.empty:
            analoguerxns_updated=pd.concat([analoguerxns_updated,commondf])
    else:
        analoguerxns_updated=commondf
    if idxcol!=['ReactionID','Instance']:
        analoguerxns_updated.reset_index(inplace=True)
        analoguerxns_updated.set_index(['ReactionID','Instance'],inplace=True) 
    return analoguerxns_updated

def checkunresolved(row,unresolvedids,exemptionlist=[]):
    '''
    Given a row, checks if reactants, reagents and products have valid/representable smiles
    based on a set of unresolved IDs
    
    If an exemption list is given (misclassified catalysts as reagents) it will be omitted from checking for reagents,
    as many catalysts have invalid SMILES or can't be represented.
    
    '''
    
    rct=set(row['ReactantID'])
    rgt=set(row['ReagentID'])
    prod=set(row['ProductID'])
    rctmatches=[val in unresolvedids for val in rct]
    prodmatches=[val in unresolvedids for val in prod]
    if exemptionlist:
        rgtmatches=[val in unresolvedids and val not in exemptionlist for val in rgt]
    else:
        rgtmatches=[val in unresolvedids for val in rgt]
    if any(rgtmatches) or any(rgtmatches) or any(prodmatches):
        return True
    else:
        return False

def getspecdat(row,DB,Rdata=True,Pdata=False,Rgtdata=False,Solvdata=False,SQL=False):
    '''
    Retrieves reaxys species data in the form of a dictionary for a row given a reference database or SQL connection
    (DB). Specify only one of Rdata (reactants), Pdata (products), Rgtdata (reagents) and Solvdata (solvents) as True.
    
    Pass in an SQL connection under DB and put SQL as true if memory is low
    
    '''
    
    if Rdata:
        col='ReactantID'
    elif Pdata:
        col='ProductID'
    elif Rgtdata:
        col='ReagentID'
    elif Solvdata:
        col='SolventID'
    dat={}
    if row[col]=='NaN' or row[col] is None or not row[col]:
        return {}
    for ID in set(copy.copy(row[col])):
        try:
            if not SQL:
                smiles=DB.loc[ID].Smiles
            else:
                smiles=pd.read_sql_query('''SELECT Smiles from SubstanceDB Where SubstanceID=  "'''+ str(ID) + '''"''',DB).Smiles[0]
            dat.update(getcompdict(ID=ID,smiles=smiles))  
        except Exception:
            continue
    return dat

def getspecdat_rxn(rxnsmiles):
    '''
    A more general function of getspecdat that retrieves species data from a given reaction SMILES
    
    '''
    if not type(rxnsmiles)==str:
        raise CustomError("Please input a reaction smiles string. Include '>>' even if no products are inputted")
    splitrxn=rxnsmiles.split('>>')
    LHS={}
    RHS={}
    LHSspec=set()
    RHSspec=set()
    if splitrxn[0]:
        LHSspec=set(splitrxn[0].split('.'))
    if splitrxn[1]:
        RHSspec=set(splitrxn[1].split('.'))
    for i,spec in enumerate(LHSspec):
        LHS.update(getcompdict(ID=i,smiles=spec))
    for j,spec in enumerate(RHSspec):
        RHS.update(getcompdict(ID=j,smiles=spec))
    return LHS,RHS
    
  
