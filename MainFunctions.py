# -*- coding: utf-8 -*-
"""
Created on Mon Sep 21 17:50:19 2020
This file contains all relevant functions for impurity prediction and visualisation (Instructions for installation are provided under
setup steps)
@author: AADA01
"""
# Setup steps
#User preferred to install Anaconda and Spyder as IDE
#RDKit: conda install -c conda-forge rdkit (https://www.rdkit.org/docs/Install.html)
#On linux server: install miniconda (leaner than anaconda) bash Miniconda3-latest-Linux-x86_64.sh with installer in working directory
# Then $ conda create -c rdkit -n my-rdkit-env rdkit and $ conda activate my-rdkit-env to activate and conda deactivate to deactivate environment
#PyTorch (Windows, without nvidia GPU): pip install torch==1.6.0+cpu torchvision==0.7.0+cpu -f https://download.pytorch.org/whl/torch_stable.html) [https://pytorch.org/get-started/locally/]
#RXN Mapper: pip install rxnmapper
# Install Micosoft Visual C++ Redistributable: https://aka.ms/vs/16/release/vc_redist.x64.exe
# Install CIRpy (Convert IUPAC to SMILES and vice versa): pip install cirpy (https://github.com/mcs07/CIRpy, https://cirpy.readthedocs.io/en/latest/api.html )
#Install tic toc (pip install ttictoc) for measuring time
#Install chempy (pip install chempy pytest)
#Install pickle 5 (pip install pickle5)
#Install cairosvg (pip install cairosvg)
# Restart Spyder
#On linux server: pip freeze > requirements.txt then pip install -r requirements.txt to download
#all packages on new machine (https://itsfoss.com/python-setup-linux/)
#GIT setup: https://git-scm.com/book/en/v2/Git-Basics-Getting-a-Git-Repository
#Spyder shortcuts (ctrl alr r to clear namespace, alt shift w to clear plots)


# %matplotlib inline
from rdkit import Chem #Importing RDKit
from rdkit.Chem import AllChem #Overall support
from rdkit.Chem import FunctionalGroups
from rdkit.Chem import PeriodicTable, GetPeriodicTable
import cirpy
from rdkit.Chem import RDConfig
from rdkit.Chem import Draw #For drawing molecules/reactions
from rdkit.Chem import rdChemReactions #Reaction processing
from rdkit.Chem.Draw import rdMolDraw2D #Drawing 2D molecules/reactions
from rdkit.Chem.Draw import IPythonConsole
from IPython.display import display, Image
from IPython.display import SVG  #For SVG support
from PIL import Image #Working with images
import matplotlib.pyplot as plt
import io
import os #Working with the OS
from rxnmapper import RXNMapper #Importing RXNMapper for unsupervised atom mapping
from ttictoc import tic,toc
from rdkit.Chem import BRICS #For fragmenting
from chempy import balance_stoichiometry
import json
# import pickle #Default
<<<<<<< HEAD
import pickle5 as pickle #Only if pickle doesn't work
=======
try:
    import pickle5 as pickle #Only if pickle doesn't work
except Exception:
    import pickle
>>>>>>> 399f3f1bd0be1bca56fcdd4ec17494105853144c
import cairosvg
import copy, itertools,shutil
from collections import Counter
from helpCompound import hc_smilesDict, hc_molDict
from FindFunctionalGroups import identify_functional_groups as IFG


#%% Reaction Mapping
def maprxn(rxns):
    """
    For a given list of reactions, rxns, returns mapped reactions with confidence scores.
    Uses IBM transformer model.

    Parameters
    ----------
    rxns : list
       List of reaction SMILES (no reactant/reagent split)

    Returns
    -------
    Mapped reactions with confidence scores: list
        mapped_rxn
             Mapped reaction SMARTS
        confidence
            Model confidence in the mapping rxn

    """

    rxn_mapper=RXNMapper()
    return rxn_mapper.get_attention_guided_atom_maps(rxns)


#%% Generating mol files
def molfromsmiles(SMILES):
    '''
    Converts a smiles string into a mol object for RDKit use. Also graphically
    represents molecule using matplotlib.

    Parameters
    ----------
    SMILES : String
        Smiles string of molecule

    Returns
    -------
    mol object for RDKit use
    figure of molecule

    '''

    mol=Chem.MolFromSmiles(SMILES)


    return mol

#%% Drawing reactions/mols


def mol_with_atom_index(mol):
    '''
    Draw a molecule with atom index numbers (set by RDKit)

    Parameters
    ----------
    mol : RDKit mole
        RDKit mole plain

    Returns
    -------
    mol : RDkit mol
        RDKit mol with atom indices

    '''
    for atom in mol.GetAtoms():
        atom.SetAtomMapNum(atom.GetIdx())
    return mol


def moveAtomMapsToNotes(m):
    '''
    Make note of the atom mapping

    Parameters
    ----------
    m : mole structure
        RDKit mole structure

    Returns
    -------
    None.

    '''
    for at in m.GetAtoms():
        if at.GetAtomMapNum():
            at.SetProp("atomNote",str(at.GetAtomMapNum()))
            #at.SetAtomMapNum(0)

def drawReaction(rxn):
    '''
    Produces an SVG of a mapped reaction

    Parameters
    ----------
    rxn : String
       Reaction SMARTS string
    filetype: String
        File type; specify svg if svg is desired. Other inputs will default
        to png


    Returns
    -------
    None.

    '''
    trxn = rdChemReactions.ChemicalReaction(rxn)
    for m in trxn.GetReactants():
        moveAtomMapsToNotes(m)
    for m in trxn.GetProducts():
        moveAtomMapsToNotes(m)
    # if filetype=='svg':
    d2d = rdMolDraw2D.MolDraw2DSVG(4000,500)
    # else:
    #     d2d=rdMolDraw2D.MolDraw2DCairo(4000,500)

    d2d.DrawReaction(trxn,highlightByReactant=True)
    d2d.FinishDrawing()
    img=d2d.GetDrawingText()

    # if filetype=='svg':

    return SVG(img)
    # else:
    #     im=Image.open(io.BytesIO(img))
    #     return im
        # d2d.WriteDrawingText('text.png') #Only works with cairo, plus atom notes not included

def drawMol(m,filetype):
    '''


    Parameters
    ----------
    m : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    '''
    if filetype=='svg':
        d=rdMolDraw2D.MolDraw2DSVG(400,300)
    else:
        d=rdMolDraw2D.MolDraw2DCairo(400,300)

    Draw.PrepareAndDrawMolecule(d,m)
    d.FinishDrawing()
    img=d.GetDrawingText()

    if filetype=='svg':
        return SVG(img)
    else:
        im=Image.open(io.BytesIO(img))
        return im

# Tkinter window
# Draw.ShowMol(p3)

#Save image to file
# fig=Draw.MolToFile(p4,'example.png',size=(500,500))

#Plotting in plot pane (matlab canvas)
# AllChem.Compute2DCoords(mol)
# fig=Draw.MolToMPL(mol)

#Rxn image (quite small)
# fig=Draw.ReactionToImage(rxn,subImgSize=(1000,1000))



#%% Utility Functions

def openpickle(filename):
    '''
    Takes a pickled file and loads it

    Parameters
    ----------
    filename : TYPE
        DESCRIPTION.

    Returns
    -------
    loadfile : TYPE
        DESCRIPTION.

    '''
    infile=open(filename,'rb')
    infile.seek(0)
    loadfile=pickle.load(infile)
    infile.close()
    return loadfile
    # with open('filename', 'rb') as handle: #Faster way
    # return pickle.load(handle)

def writepickle(pkl,filename):
    '''


    Parameters
    ----------
    pkl : Pickle file
        Destination file type
    filename : Str
        Directory to save in (exclude extension)

    Returns
    -------
    None.

    '''
    with open(filename+'.pickle', 'wb') as handle:
        pickle.dump(pkl, handle, protocol=pickle.HIGHEST_PROTOCOL)


def getlist(refdict,key):
    '''
    Gets list from a reference dictionary. Assumes refdict is a dictionary within a dictionary.
    given a key

    Parameters
    ----------
    refdict : Dictionary
        Reference dictionary with keys as Reaxys ID
    key : String
        The reaction property that need to be retrieved

    Returns
    -------
    list
        DESCRIPTION.

    '''
    return [rxn[key] for rxn in refdict.values() if key in rxn.keys()]


def writetofile(rxnimg,directory):
    '''
    Takes a reaction image and saves it to a specified directory (usually after calling drawReaction)

    Parameters
    ----------
    rxnimg : TYPE
        DESCRIPTION.
    directory : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    '''
    open(directory,'w').write(rxnimg.data)

def delcontents(directory):
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))



def convSVGtoPNG(filename, filenameout):
    '''
    Converts SVG images to PNG images for easier copy pasting (eg./ to Word)

    Parameters
    ----------
    filename : TYPE
        DESCRIPTION.
    filenameout : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    '''
    cairosvg.svg2png(url=filename+".svg", write_to=filenameout+".png")


def getMols(IDs):
    '''
    Retrieves smiles strings from a set of Reaxys IDs using the cambridge server
    Connect via VPN

    Parameters
    ----------
    IDs : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    '''
    # relies on Jana's files
    str_cwd = os.getcwd()
    os.chdir('/home/projects/graph/data/')
    folderNames = [_ for _ in os.listdir('.') if os.path.isdir(_)] #folder name and IDslist file name with .dat are same
    IDslen = len(IDs)
    mols = [None]*IDslen
    for i in range(IDslen):
        for folderName in folderNames:
            try:
                os.chdir('/home/projects/graph/data/' + folderName)
                mols[i] = Chem.MolFromMolFile(IDs[i])
                break    # if get mol
            except:
                continue
    os.chdir(str_cwd)
    return mols #Can streamline into the main code


def getfragments(chemlist,refdict,helpc=False):
    '''
    Builds reaction smiles string for each chemical (with reaxys ID) in a list given a reference
    dictionary with reaxys ID as keys.

    Parameters
    ----------
    chemlist : TYPE
        DESCRIPTION.
    refdict : TYPE
        DESCRIPTION.

    Returns
    -------
    frag : TYPE
        DESCRIPTION.

    '''
    frag=''
    if chemlist==[]:
        print('ERROR: NO CHEMICALS IN LIST PROVIDED')
    for idx,chem in enumerate(chemlist):
        if not refdict.get(chem):
            print('component not in dictionary. Skipping..')
            if idx==len(chemlist)-1:
                frag=frag[:-1]
            continue
        if helpc:
            frag+=refdict[chem]
        else:
            frag+=refdict[chem]['Smiles']
        if idx !=len(chemlist)-1:
            frag+='.'
    return frag

# def gethelpfragments(helplist,helpdict):
#     '''
#     Builds reaction smiles string for each chemical (with reaxys ID) in a list given a reference
#     help compound dictionary with reaxys ID as keys.

#     Parameters
#     ----------
#     helplist : TYPE
#         DESCRIPTION.
#     helpdict : TYPE
#         DESCRIPTION.

#     Returns
#     -------
#     frag : TYPE
#         DESCRIPTION.

#     '''
#     frag=''
#     if helplist==[]:
#         print('ERROR: NO CHEMICALS IN LIST PROVIDED')
#     for idx,hc in enumerate(helplist):
#         if not helpdict[hc]:
#             print('component not in dictionary. Skipping..')
#             continue
#         frag+=helpdict[hc]
#         if idx !=len(helplist)-1:
#             frag+='.'
#     return frag

#%% Reaction Center Identification

def bond_to_label(bond):
    '''
    This function takes an RDKit bond and creates a label describing
    the most important attributes

    Parameters
    ----------
    bond : TYPE
        DESCRIPTION.

    Returns
    -------
    TYPE
        DESCRIPTION.

    '''
    a1_label = str(bond.GetBeginAtom().GetAtomicNum())
    a2_label = str(bond.GetEndAtom().GetAtomicNum())
    if bond.GetBeginAtom().HasProp('molAtomMapNumber'):
        a1_label += bond.GetBeginAtom().GetProp('molAtomMapNumber')
    if bond.GetEndAtom().HasProp('molAtomMapNumber'):
        a2_label += bond.GetEndAtom().GetProp('molAtomMapNumber')
    atoms = sorted([a1_label, a2_label])

    # return '{}{}{}'.format(atoms[0], bond.GetSmarts(), atoms[1])
    return '{}{}'.format(atoms[0], atoms[1])



def atoms_are_different(atom1, atom2, level = 1,usesmarts=True):
    '''
    Compares two RDKit atoms based on common properties (Smarts, number of
    bonded hydrogens, charge, degree, radical electrons, neighbors etc.)

    Parameters
    ----------
    atom1 : RDKit atom
        DESCRIPTION.
    atom2 : RDKit atom
        DESCRIPTION.
    level : Optional
        DESCRIPTION. The default is 1.

    Returns
    -------
    True if the two atoms are different and false if they are similar.

    '''
    # import pdb; pdb.set_trace()
    if usesmarts:
        if atom1.GetSmarts() != atom2.GetSmarts(): return True # should be very general
    if atom1.GetAtomicNum() != atom2.GetAtomicNum(): return True # must be true for atom mapping
    if atom1.GetTotalNumHs() != atom2.GetTotalNumHs(): return True
    if atom1.GetFormalCharge() != atom2.GetFormalCharge(): return True
    if atom1.GetDegree() != atom2.GetDegree(): return True
    if atom1.GetIsAromatic() != atom2.GetIsAromatic(): return True
    #if atom1.IsInRing() != atom2.IsInRing(): return True
    if atom1.GetNumRadicalElectrons() != atom2.GetNumRadicalElectrons(): return True
    # TODO: add # pi electrons like ICSynth? Account for chirality
    # Check bonds and nearest neighbor identity
    if level >= 1:
        bonds1 = sorted([bond_to_label(bond) for bond in atom1.GetBonds()])
        bonds2 = sorted([bond_to_label(bond) for bond in atom2.GetBonds()])
        if bonds1 != bonds2: return True

        # # Check neighbors too (already taken care of with previous lines)
        # neighbors1 = sorted([atom.GetAtomicNum() for atom in atom1.GetNeighbors()])
        # neighbors2 = sorted([atom.GetAtomicNum() for atom in atom2.GetNeighbors()])
        # if neighbors1 != neighbors2: return True

    else: return False

def parsemap(rxn):
    '''
    Takes in a reaction SMARTS string with mapping and returns a dictionary
    of mapped atoms between reactants and products (res). Provides warnings if
    all atoms are not mapped or the reaction is not balanced.

    Parameters
    ----------
    rxn : String
        Reaction SMARTS

    Returns
    -------
    res : Dict
        Dictionary with the keys being common mapped indices between reactants
        and products. The values are tuples (ptempl,rtempl, idxp, idxr) where
        ptempl corresponds to the product molecule, r templ corresponds to the
        reactant molecule, idxp is the product atom index and idxr is the
        reactant atom index (different from mapped index)

    reactantMap : Dict
        Dictionary with keys being mapped indices of reactants only.
        Values are tuples (rtempl, idx), with definitions similar to above

    '''
    res = {}
    reactantMap = {}
    totratoms=0
    totpatoms=0
    rm=False
    pm=False
    for rtempl in rxn.GetReactants():
        Chem.SanitizeMol(rtempl)
        rtempl.UpdatePropertyCache(strict=False) #This and above makes sure the molecule is properly stored in RDKit
        for atom in rtempl.GetAtoms():
            totratoms+=1
            mnum = atom.GetAtomMapNum()
            if not mnum:
                rm=True
                continue
            reactantMap[mnum] = (rtempl,atom.GetIdx())
    for ptempl in rxn.GetProducts():
        Chem.SanitizeMol(ptempl)
        ptempl.UpdatePropertyCache(strict=False)
        for atom in ptempl.GetAtoms():
            totpatoms+=1
            mnum = atom.GetAtomMapNum()
            if not mnum:
                pm=True
                continue
            if mnum in reactantMap:
                rtempl,idxr = reactantMap[mnum]
                res[mnum] = (ptempl,rtempl,atom.GetIdx(),idxr)
    if rm or pm:
        print("warning: not all atoms are mapped")
    elif totpatoms != totratoms:
        print("warning: reaction is not balanced")

    return res,reactantMap



def get_changed_atoms(mapdict):
    '''
    Takes res output from parsemap() and for each atom mapped, determines if
    equivalent atoms in reactant and product are different using
    atoms_are_different(). This function therefore identifies the reaction
    center of the reaction.

    Parameters
    ----------
    mapdict : Dict
              Dictionary with the keys being common mapped indices between reactants
              and products. The values are tuples (ptempl,rtempl, idxp, idxr) where
              ptempl corresponds to the product molecule, r templ corresponds to the
              reactant molecule, idxp is the product atom index and idxr is the
              reactant atom index (different from mapped index)
    Returns
    -------
    None.

    '''
    changed_atoms=[]
    changed_mapidx=[]

    for mapidx,val in mapdict.items():
        prod=val[0]
        react=val[1]
        idxp=val[2]
        idxr=val[3]
        ratom=react.GetAtomWithIdx(idxr)
        patom=prod.GetAtomWithIdx(idxp)
        if mapidx not in changed_mapidx:
            if atoms_are_different(patom,ratom):
                changed_atoms.append(ratom)
                changed_mapidx.append(mapidx)
    return changed_atoms, changed_mapidx




# Fragmenting functional groups (BRICS probably better)
# fName = os.path.join(RDConfig.RDDataDir, 'FunctionalGroups.txt')
# from rdkit.Chem import FragmentCatalog

# fparams=FragmentCatalog.FragCatParams(1,6,fName)
# fcat=FragmentCatalog.FragCatalog(fparams)
# fcgen=FragmentCatalog.FragCatGenerator()

#Detailed fragmentation (functional groups)
# fcgen.AddFragsFromMol(mol,fcat) #Gives fragments from a mol
# fcat.GetEntryDescription()
# list(fcat.GetEntryFuncGroupIds(num)) #Num depends on how many entries
# fparams.GetFuncGroup(num2) #Output from previous line to check
# list(fcat.GetEntryDownIds(num3)) # Retrieves what larger fragments the small fragment is part of
# To visualize functional groups
# catparams =FunctionalGroups.BuildFuncGroupHierarchy(fileNm=fName)
# for param in catparams:
#     print(param.name)
#     param.pattern.UpdatePropertyCache(strict=False)
#     Chem.FastFindRings(param.pattern)
#     Chem.SetHybridization(param.pattern)
#     display(param.pattern)



def get_special_groups(mol):
    '''
    This retrieves special groups from input molecules that should be part of
    the final template fragments. Only for specific templates. If general templates are
    preferred, then don't call this function'

    Parameters
    ----------
    mol : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    '''

# Define templates
    group_templates = [
        'C(=O)Cl', # acid chloride
        'C(=O)[O;H,-]', # carboxylic acid
        '[$(S-!@[#6])](=O)(=O)(Cl)', # sulfonyl chloride
        '[$(B-!@[#6])](O)(O)', # boronic acid
        '[$(N-!@[#6])](=!@C=!@O)', # isocyanate
        '[N;H0;$(N-[#6]);D2]=[N;D2]=[N;D1]', # azide
        'O=C1N(Br)C(=O)CC1', # NBS brominating agent
        'C=O', # carbonyl
        'ClS(Cl)=O', # thionyl chloride
        '[Mg][Br,Cl]', # grinard (non-disassociated)
        '[#6]S(=O)(=O)[O]', # RSO3 leaving group
        '[O]S(=O)(=O)[O]', # SO4 group
        '[N-]=[N+]=[C]', # diazo-alkyl
        ]
    # Build list
    groups = []
    for template in group_templates:
        matches = mol.GetSubstructMatches(Chem.MolFromSmarts(template))
        groups.extend(list(matches))
    return groups

    # group_templates = [
    #     (range(3), '[OH0,SH0]=C[O,Cl,I,Br,F]',), # carboxylic acid / halogen
    #     (range(3), '[OH0,SH0]=CN',), # amide/sulfamide
    #     (range(4), 'S(O)(O)[Cl]',), # sulfonyl chloride
    #     (range(3), 'B(O)O',), # boronic acid/ester
    #     ((0,), '[Si](C)(C)C'), # trialkyl silane
    #     ((0,), '[Si](OC)(OC)(OC)'), # trialkoxy silane, default to methyl
    #     (range(3), '[N;H0;$(N-[#6]);D2]-,=[N;D2]-,=[N;D1]',), # azide
    #     (range(8), 'O=C1N([Br,I,F,Cl])C(=O)CC1',), # NBS brominating agent
    #     (range(11), 'Cc1ccc(S(=O)(=O)O)cc1'), # Tosyl
    #     ((7,), 'CC(C)(C)OC(=O)[N]'), # N(boc)
    #     ((4,), '[CH3][CH0]([CH3])([CH3])O'), #
    #     (range(2), '[C,N]=[C,N]',), # alkene/imine
    #     (range(2), '[C,N]#[C,N]',), # alkyne/nitrile
    #     ((2,), 'C=C-[*]',), # adj to alkene
    #     ((2,), 'C#C-[*]',), # adj to alkyne
    #     ((2,), 'O=C-[*]',), # adj to carbonyl
    #     ((3,), 'O=C([CH3])-[*]'), # adj to methyl ketone
    #     ((3,), 'O=C([O,N])-[*]',), # adj to carboxylic acid/amide/ester
    #     (range(4), 'ClS(Cl)=O',), # thionyl chloride
    #     (range(2), '[Mg,Li,Zn,Sn][Br,Cl,I,F]',), # grinard/metal (non-disassociated)
    #     (range(3), 'S(O)(O)',), # SO2 group
    #     (range(2), 'N~N',), # diazo
    #     ((1,), '[!#6;R]@[#6;R]',), # adjacency to heteroatom in ring
    #     ((2,), '[a!c]:a:a',), # two-steps away from heteroatom in aromatic ring
    #     #((1,), 'c(-,=[*]):c([Cl,I,Br,F])',), # ortho to halogen on ring - too specific?
    #     #((1,), 'c(-,=[*]):c:c([Cl,I,Br,F])',), # meta to halogen on ring - too specific?
    #     ((0,), '[B,C](F)(F)F'), # CF3, BF3 should have the F3 included
    # ]
    # # Build list
    # groups = []
    # for (add_if_match, template) in group_templates:
    #     matches = mol.GetSubstructMatches(Chem.MolFromSmarts(template), useChirality=False)
    #     for match in matches:
    #         add_if = []
    #         for pattern_idx, atom_idx in enumerate(match):
    #             if pattern_idx in add_if_match:
    #                 add_if.append(atom_idx)
    #         groups.append((add_if, match))
    # return groups



def get_fragments_for_changed_atoms(mapdict,changed_mapidx, category, radius = 0):
    """


    Parameters
    ----------
    mapdict : TYPE
        DESCRIPTION.
    changed_mapidx : TYPE
        DESCRIPTION.
    category : Specify either reactant or product
        Category to generate fragments for template smarts
    radius : TYPE, optional
        DESCRIPTION. The default is 0.

    Returns
    -------
    None.

    """
    fragments=''
    mol_done=[]
    atoms_to_use=[] #List for fragment construction
    symbols=[]

    for mapidx in changed_mapidx:
        val=mapdict[mapidx]
        prod=val[0]
        react=val[1]
        idxp=val[2]
        idxr=val[3]
        if category=='reactants':
            mol=react
            idx=idxr
        else:
            mol=prod
            idx=idxp

        atoms_to_use.append(idx) #Adding changed atom to atoms list for fragment construction

        if mol not in mol_done:
            for atom in mol.GetAtoms():
                symbol=atom.GetSmarts()
                if atom.GetTotalNumHs() == 0:
                # Be explicit when there are no hydrogens
                    if ':' in symbol: # stick H0 before label
                        symbol = symbol.replace(':', ';H0:')
                    else: # stick before end
                        symbol = symbol.replace(']', ';H0]')
                    # print('Being explicit about H0!!!!')
        if atom.GetFormalCharge() == 0:
                # Also be explicit when there is no charge
            if ':' in symbol:
                symbol = symbol.replace(':', ';+0:')
            else:
                symbol = symbol.replace(']', ';+0]')
        if symbol !=atom.GetSmarts():
                symbol_replacements.append()
                symbols=[atom.GetSmarts() for atom in mol.GetAtoms()]

        mol_done.append(mol)





            # CUSTOM SYMBOL CHANGES
        if atom.GetTotalNumHs() == 0:
                # Be explicit when there are no hydrogens
            if ':' in symbol: # stick H0 before label
                symbol = symbol.replace(':', ';H0:')
            else: # stick before end
                symbol = symbol.replace(']', ';H0]')
                    # print('Being explicit about H0!!!!')
        if atom.GetFormalCharge() == 0:
                # Also be explicit when there is no charge
            if ':' in symbol:
                symbol = symbol.replace(':', ';+0:')
            else:
                symbol = symbol.replace(']', ';+0]')
        if symbol !=atom.GetSmarts():
                symbol_replacements.append()


    #     # Initialize list of replacement symbols (updated during expansion)



#%% Screening and balancing reactions (First cut)

def atomtypes(mol):
    """
    Generates an atom type dictionary with counting for a given mol file. Also returns overall
    charge of the molecule. It may be possible to directly go from formula to atom type

    Parameters
    ----------
    mol : mol file
        Mol file of chemical

    Returns
    -------
    typedict : Dictionary
        Dictionary with keys as element and value as count
    charge : integer
        Overall charge of supplied molecule

    """

    typedict={}
    mol2=Chem.AddHs(mol) #Assumes hydrogens are added
    charge=0
    for atom in mol2.GetAtoms():
        elem=PeriodicTable.GetElementSymbol(GetPeriodicTable(),atom.GetAtomicNum())
        charge+=atom.GetFormalCharge()
        if elem not in typedict.keys():
            typedict[elem]=1
        else:
            typedict[elem]+=1
    return typedict, charge

# def balancerxn(rxnid,rxnlib,smles):



def isbalanced(rxnid,rxnlib,smles):
    '''
    Outputs whether reaction is balanced. If not balanced, attempts to balance
    with a series of help compounds. If successful, stoichiometry coefficients
    are outputted as well. Assumes help compounds are not analogue compounds.

    Parameters
    ----------
    rxnid : TYPE
        DESCRIPTION.
    rxnlib : TYPE
        DESCRIPTION.
    smles : TYPE
        DESCRIPTION.

    Raises
    ------
    Exception
        DESCRIPTION.

    Returns
    -------
    TYPE
        DESCRIPTION.

    '''
    # import pdb; pdb.set_trace()
    Rcount=Counter({}) #Used to cumulatively add atom count across reactants
    Pcount=Counter({}) #Used to cumulatively add atom count across products
    Rcharge=0 #Used to cumulatively add formal charge across reactants
    Pcharge=0 #Used to cumulatively add formal charge across products
    Rdata={} #Stores atom count and type for each reactant
    Pdata={} #Stores atom count and type for each product

    def tryhelp(hc_atomtype,chempyr,chempyp,rxnid,keep=False):
        reac={}
        prod={}
        hc=''
        lim=len(hc_atomtype)
        if type(hc_atomtype)==dict:
            keylist=list(hc_atomtype.keys())
        elif type(hc_atomtype)==list:
            keylist=hc_atomtype
        counter=0
        while any([idx>=5 for tup in zip(reac.values(),prod.values()) for idx in tup]) or not reac:
            if counter>lim-1:
                if keep:
                    print('Help compounds did not help. '+'Reaction '+rxnid+' will still be kept, but there are extra reactant atoms')
                    return True,'Warning'
                else:
                    errormsg='Reaction could not be balanced with help compounds.'
                    print('Reaction '+rxnid+' could not be balanced. Help compounds did not help. '+' Reaction '+rxnid+' will be screened out')
                    return False,errormsg
            if hc:
                chempyp.remove(hc)
            hc=keylist[counter]
            chempyp.add(hc)
            try:
                reac, prod = balance_stoichiometry(chempyr, chempyp,underdetermined=None,allow_duplicates=True)
                if any(idx<0 for idx in reac.values()) or any(idx<0 for idx in prod.values()): #Don't want negative stoich coefficients
                    raise Exception
                else:
                    counter+=1
                    continue
            except Exception:
                counter+=1
                continue
        print('Reaction '+rxnid+' successfully balanced')
        return True,reac,prod

    def checksimilar(Rdata,Pdata):
        similarspecies=set()
        for product,patomtype in Pdata.items():
            psettype=set(patomtype)
            for rspecies,ratomtype in Rdata.items():
                rsettype=set(ratomtype)
                inters=psettype.intersection(rsettype)
                uni=psettype.union(rsettype)
                if (len(inters)/len(uni))>0.75 and psettype.issubset(rsettype): #Similar to Jaccard Index (intersection over union) and ensures that that reactant only takes part
                    mult={atom: patomtype[atom]/ratomtype[atom] for atom in inters} # Finding stoichiometric multiplier
                    multcount=dict(sorted(Counter(mult.values()).items(), key=lambda item:item[1],reverse=True))
                    if len(multcount)<=2 and not [key for key in list(multcount.keys()) if key>list(multcount.keys())[0]] :
                        similarspecies.add(rspecies)
        return similarspecies


    rspecieslist=[rspecies for rspecies in itertools.chain(rxnlib[rxnid]['Reactants'],rxnlib[rxnid]['Reagents']) if rspecies]
    if not rspecieslist:
        errormsg='No LHS species in reaction.'
        print('No LHS species in reaction. '+ 'Reaction '+rxnid+ ' will be screened out')
        return False,errormsg
    #Reaction parsing
    for rspecies in rspecieslist:
        #Error handling
        if rspecies not in smles.keys():
            errormsg='LHS species not in substance dictionary.'
            detmsg='Missing LHS species '+rspecies
            print('LHS species '+rspecies+' not in substance dictionary. '+ 'Reaction '+rxnid+ ' will be screened out')
            return False,errormsg,detmsg
        elif ('Carrier Fragment' not in smles[rspecies].keys()): #Or if not smles[reactant].get('Carrier Fragment):
            errormsg='LHS species is not an analogue compound'
            detmsg='LHS species '+rspecies+ ' is not analogue'
            print('LHS species '+rspecies+' is not an analogue compound. '+ 'Reaction '+rxnid+ ' will be screened out')
            return False,errormsg,detmsg

        #Main code

        rmol=smles[rspecies]['Mol']
        Rdata[rspecies]=atomtypes(rmol)[0]
        Rcount+=Counter(Rdata[rspecies])
        Rcharge+=atomtypes(rmol)[1]

    MainProd=False
    #Product parsing
    for product in rxnlib[rxnid]['Products']:
        #Error handling
        if product=='':
            errormsg='No products in reaction.'
            print('No products in reaction. ' + 'Reaction '+rxnid+ ' will be screened out')
            return False,errormsg
        elif product not in smles.keys():
            errormsg='Products not in substance dictionary'
            detmsg='Missing product '+product
            print('Product '+product+' not in substance dictionary. ' + 'Reaction '+rxnid+ ' will be screened out')
            return False,errormsg,detmsg

        #Main code

        pmol=smles[product]['Mol']
        Pdata[product]=atomtypes(pmol)[0]
        if sum(Pdata[product].values())>=(0.5*sum(Rcount.values())): #Check if any product is the main product
            MainProd=True
        Pcount+=Counter(Pdata[product])
        Pcharge+=atomtypes(pmol)[1]

    if not MainProd:
        errormsg='More than 50 % of reactant atoms missing.'
        print('Main product is not present. More than 50 % of reactant atoms are missing. '+'Reaction '+rxnid+ ' will be screened out')
        return False,errormsg

    if Rcount==Pcount and Rcharge==Pcharge:
        print('Reaction '+rxnid+ ' is fully balanced')
        return [True]  #Same number and type of atoms reactant and product side and same charge ie. perfectly balanced reaction. Pretty much impossible.
    elif Rcharge!=Pcharge: #Does not deal with charge imbalance yet. Reaction is screened out
        errormsg='Charge imbalanced.'
        print('Charge is not balanced. ' + 'Reaction '+rxnid+ ' will be screened out')
        return False,errormsg
    elif len(Rcount.keys())<len(Pcount.keys()): #Screen out reactions where new atom types are in the product that weren't in reactants. This means solvent is needed, which is not an analogue compound
        errormsg='New atom types in products.'
        print('New atom types introduced in products. Other non-analogue species required. ' + 'Reaction '+rxnid+ ' will be screened out')
        return False,errormsg
    else: #Charge balance is met but not mol balance.Can use new function
        print('Reaction '+rxnid+' needs to be balanced. Initializing...')
        chempyr={smles[rspecies]['Formula'] for rspecies in rspecieslist}
        chempyp={smles[product]['Formula'] for product in rxnlib[rxnid]['Products']}
        try:
            reac, prod = balance_stoichiometry(chempyr, chempyp,underdetermined=None,allow_duplicates=True) #Try balancing once without adding compounds
            if any(idx<0 for idx in reac.values()) or any(idx<0 for idx in prod.values()) or any([idx>=5 for tup in zip(reac.values(),prod.values()) for idx in tup]): #Don't want negative stoich coefficients
                raise Exception
            else:
                print('Reaction '+rxnid+' successfully balanced')
                return True,reac,prod
        except Exception: # Fails if missing compounds either on reactant or product side
            print('Help compounds may need to be added to balance reaction '+rxnid+'. Proceeding...')
            rem=Counter() # Rem contains difference between product and reactant counters
            rem.update(Pcount)  #If atoms not balanced and same charge, attempt to balance. Can try if different charge but more tricky
            rem.subtract(Rcount) #Subtracting reactant atom type index from product atom type index
            poskey=[key for key in rem.keys() if rem[key]>0] #Finding only positive keys. Note that if counter is positive this means extra molecules need to be added to the reactant side.
            negkey=[key for key in rem.keys() if rem[key]<0] #Finding only negative keys. This means that extra molecules need to be added to the product side

        # 3 conditions: rem is all negative. In this case, match atom type dictionary of rem with that of a help compound. Better than testing each one
        # iteratively using chempy. If rem is positive and negative or just positive, no choice but to test one by one. This code will not
        # consider more than 1 help compound at a time, so there will be limitations (ie. reactions that require 2 or more help compounds will be screened out).
        # There is also an assumption that no help compound is an analogue compound. This is why nothing is added to the reactant side as if this is the case,
        # the reaction has to be screened out anyway. Consider putting similar species check outside

            postype={}
            negtype={}
            hc_atomtype={hc: atomtypes(hc_molDict[hc])[0] for hc in hc_molDict if atomtypes(hc_molDict[hc])[1]==0} #Atom type for help compounds

            if poskey:
                postype={key: rem[key] for key in poskey}
            if negkey:
                negtype={key: abs(rem[key]) for key in negkey}
                
            similarspecies=checksimilar(Rdata,Pdata)
            if similarspecies and len(similarspecies)!=len(chempyr):
                print('Extra reagent/reactant may not be needed')
                chempyrs={smles[rspecies]['Formula'] for rspecies in similarspecies}
                try:
                    reac, prod = balance_stoichiometry(chempyrs, chempyp,underdetermined=None,allow_duplicates=True)
                    if any(idx<0 for idx in reac.values()) or any(idx<0 for idx in prod.values()) or any([idx>=5 for tup in zip(reac.values(),prod.values()) for idx in tup]): #Don't want negative stoich coefficients
                        raise Exception
                    else:
                        print('Reaction '+rxnid+' successfully balanced')
                        return True,reac,prod
                except Exception:
                    return tryhelp(hc_atomtype,chempyrs,chempyp,rxnid)
            elif negtype and not postype:
                hc_list=[hc for hc in hc_atomtype if hc_atomtype[hc].keys()==negtype.keys()] #Narrow down list of help compounds
                if hc_list:
                    hc_list2=[hc for hc in hc_list if hc_atomtype[hc]==negtype]
                    if hc_list2:
                        return tryhelp(hc_list2,chempyr,chempyp,rxnid,keep=True)
                    return tryhelp(hc_list,chempyr,chempyp,rxnid,keep=True)
                else:
                    errormsg='LHS species has new atom type not present in any help compound.'
                    print('No help atom type match. Reactant complex likely to have other atom types. ' + 'Reaction '+rxnid+ ' will be screened out')
                    return False,errormsg
                  
            

            # if postype:
            #     similarspecies=checksimilar(Rdata,Pdata)
            #     if similarspecies and len(similarspecies)!=len(chempyr):
            #         chempyrs={smles[rspecies]['Formula'] for rspecies in similarspecies}
            #         try:
            #             reac, prod = balance_stoichiometry(chempyrs, chempyp,underdetermined=None,allow_duplicates=True)
            #             if any(idx<0 for idx in reac.values()) or any(idx<0 for idx in prod.values()) or any([idx>=5 for tup in zip(reac.values(),prod.values()) for idx in tup]): #Don't want negative stoich coefficients
            #                 raise Exception
            #             else:
            #                 print('Reaction '+rxnid+' successfully balanced')
            #                 return True,reac,prod
            #         except Exception:
            #             return tryhelp(hc_atomtype,chempyrs,chempyp,rxnid)
            #     else:
            #         return tryhelp(hc_atomtype,chempyr,chempyp,rxnid)

                # elif negtype:
                #     chempyp.add(''.join([key if val==1 else key+str(val) for key,val in negtype.items() if val>1]))
                #     try:
                #         reac, prod = balance_stoichiometry(chempyr, chempyp,underdetermined=None,allow_duplicates=True)
                #         if any(idx<0 for idx in reac.values()) or any(idx<0 for idx in prod.values()) or any([idx>=5 for tup in zip(reac.values(),prod.values()) for idx in tup]) : #Don't want negative stoich coefficients
                #             raise Exception
                #         else:
                #             print('Reaction '+rxnid+' successfully balanced')
                #             return True,reac,prod
                #     except Exception:
                #         return tryhelp(hc_atomtype,chempyr,chempyp,rxnid)
                # else:
                #     return tryhelp(hc_atomtype,chempyr,chempyp,rxnid)

            else: #This means excess molecules only on reactant side. Attempt to add help compounds to product side(one only not combinations)
                return tryhelp(hc_atomtype,chempyr,chempyp,rxnid) 


#%% Screening based on reaction center (Second cut)

def get_matches(mol,patt,checkresults=True):
    import pdb; pdb.set_trace()
    matches=mol.GetSubstructMatches(patt)
    if not matches:
        return False,False
    elif checkresults:
        funcgroupmol=IFG(mol) #Functional groups of RDKit reactant
        funcgrouppatt=IFG(patt) #Functional groups of carrier fragment
        funcids=set() #Store functional groups that are of the same type as the carrier fragment
        for funcgroup in funcgrouppatt:
            matchtype=[molgroup for molgroup in funcgroupmol if molgroup.atoms==funcgroup.atoms]
            for molgroup in matchtype:
                if not any([atoms_are_different(mol.GetAtomWithIdx(atomid),patt.GetAtomWithIdx(pattid),usesmarts=False) for atomid,pattid in zip(molgroup.atomIds,funcgroup.atomIds)]): #BUGGY
                    funcids.update({atomid for atomid in molgroup.atomIds})

        corr_matches={match for match in matches if set(match).intersection(funcids)}
        # funcgroupids={atomid for match in corr_matches for atomid in set(match).intersection(funcids)}
        funcgroupids=[set(match).intersection(funcids) for match in corr_matches]
        return corr_matches,funcgroupids
    else:
        return matches



def valid_rxn_center(rxnid,analoguerxns,smles):
    # import pdb; pdb.set_trace()
    rxn=analoguerxns[rxnid]
    if 'Balanced Reaction Center' in rxn.keys():
        RC=set(copy.copy(rxn['Balanced Reaction Center']))
        rdrxn=rxn['Balanced RDKit Rxn']
        rspecieslist=rxn['Balanced Reactants']
    else:
        RC=set(copy.copy(rxn['Reaction Center2']))
        rdrxn=rxn['RDKit Rxn2']
        rspecieslist=[rspecies for rspecies in itertools.chain(rxn['Reactants'],rxn['Reagents']) if rspecies]
    
    if not RC:
        errormsg='No atoms change in the reaction'
        print('No atoms change in the reaction. Reaction '+rxnid+' will be screened out.')
        return False,errormsg
    clean_rxn=copy.copy(rdrxn)
    rdChemReactions.RemoveMappingNumbersFromReactions(clean_rxn)
    reacfragloc={} #This stores mapping numbers and atom indices of carrier fragment atoms within all reactants

    for idx,reactant in enumerate(clean_rxn.GetReactants()):
        matched=False
        fragloc={} #This stores mapping numbers and atom indices of carrier fragment atoms for each reactant
        rdreactant=Chem.RemoveAllHs(rdrxn.GetReactants()[idx])
        for reacid in rspecieslist:
            if smles[reacid]['Smiles']==Chem.MolToSmiles(reactant):
                break

        for carrier_frag in set(getlist(smles,'Carrier Fragment')):
            fin_matches=[] #Stores mapping numbers of carrier fragment atoms involved in the reaction
            carriermol=Chem.RemoveAllHs(Chem.MolFromSmarts(carrier_frag))
            Chem.SanitizeMol(carriermol)
            carriermol.UpdatePropertyCache(strict=False)
            corr_matches,funcgroupids=get_matches(reactant,carriermol)
            if not corr_matches:
                continue
            matched=True
            funcgroupmap=[{rdreactant.GetAtomWithIdx(atomidx).GetAtomMapNum() for atomidx in funcgroup} for funcgroup in funcgroupids]
            for funcgroupmapnum,corr_match in zip(funcgroupmap,corr_matches):
                funcgroupreac=RC.intersection(funcgroupmapnum) #Checks if any atoms in RC are in functional group of matched carrier fragment
                if funcgroupreac:
                    RC-=funcgroupreac
                    fin_matches.extend([corr_match])
                    
            if not fin_matches:
                continue #Reaction center is not in any of functional groups of carrier fragments of a reactant
                
            fragloccarr=[[{rdreactant.GetAtomWithIdx(atomidx).GetAtomMapNum() for atomidx in match} for match in fin_matches],[{atomidx for atomidx in match} for match in fin_matches]]
            fragloc.update({carrier_frag: fragloccarr})
        if not fragloc:
            if not matched:
                errormsg='No carrier fragment found within LHS species.'
                detmsg='No carrier fragment in LHS species '+reacid #Need to change this
                print('LHS species '+reacid+' does not have any carrier fragment and is not analogue. Reaction '+rxnid+' will be screened out.')
            else:
                errormsg='Carrier fragment found but invalid reaction center.'
                detmsg='LHS species '+reacid+' does not react at functional groups within carrier fragments.'
                print('LHS species '+reacid+' does not react at functional groups within carrier fragments. Reaction '+rxnid+' will be screened out.')
            return False,errormsg,detmsg
        elif reacfragloc.get(reacid):
            reacfragloc[reacid].extend([fragloc])
        else:
            reacfragloc.update({reacid:[fragloc]})
                    
    if RC:
        errormsg='Reaction center still outside carrier fragment.'
        print(errormsg)
        return False,errormsg
    else:
        return True,reacfragloc,clean_rxn

        # corr_matches={match for match in matches if set(match).intersection(funcids)}
        # fraglocmap={rdreactant.GetAtomWithIdx(atomidx).GetAtomMapNum() for match in corr_matches for atomidx in match}
        # fraglocidx={atomidx for match in corr_matches for atomidx in match}
        # if reacfragloc.get(reacid):
        #     reacfragloc[reacid][0].extend([fraglocmap])
        #     reacfragloc[reacid][1].extend([fraglocidx])
        # else:
        #     reacfragloc.update({reacid:([fraglocmap],[fraglocidx])})

        # valid_RC.update({rdreactant.GetAtomWithIdx(atomidx).GetAtomMapNum() for atomidx in funcgroupids})
    # if RC and set(RC).issubset(valid_RC):
    #     return True,reacfragloc,clean_rxn
    # else:
    #     return False
    #     if mapset and funcgroupset:
    #         mapset=mapset.union(fraglocmap)
    #         funcgroupset=funcgroupset.union({rdreactant.GetAtomWithIdx(atomidx).GetAtomMapNum() for match in funcgroupmatches for atomidx in match.atomIds})    #Atom indices, atoms and type of functional group within carrier fragment
    #     else:
    #         mapset=fraglocmap
    #         funcgroupset={rdreactant.GetAtomWithIdx(atomidx).GetAtomMapNum() for match in funcgroupmatches for atomidx in match.atomIds}
    # if RC and set(RC).issubset(mapset) and set(RC).issubset(funcgroupset): #Check if reaction center exists, it is part of the carrier fragment and it is at a functional group
    #     return True,reacfragloc,clean_rxn
    # else:
    #     return False




#%% Template generation

def gen_template(reactant_fragments,product_fragments):
    rxn_string = '{}>>{}'.format(reactant_fragments, product_fragments)
    return rxn_string





















