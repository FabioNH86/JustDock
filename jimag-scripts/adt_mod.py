#hay que ejecutar la siguiente linea en IDLE
#execfile('/home/aldo/pro/falcon/script2/adt_mod.py')

#load ligand
self.AD41analyze_readVinaResult('./coarse.pdbqt', 'conformations', log=0)
#load receptor
self.AD41analyze_readMacromolecule('./receptor.pdbqt', log=0)
self.displayLines("receptor;", negate=True, log=0)
#initialize objects
rec = self.Mols[1]
chain = rec.children
residues = chain.children

def loadPocket():
    from MolKit.protein import Protein, ProteinSet, Chain, Residue, ResidueSet
    #process geometries
    self.computeMSMS("receptor:::;", log=0, display=True)
    self.displayCPK("receptor,", log=0, quality=0)
    self.ribbon("receptor,", log=0)

    #load residue list
    pocket = ResidueSet([])
    with open('./resfile') as f:
        indices = f.read().splitlines()
    for index in indices:
        #TODO: the way to compute the offset needs to be revised!
        i = int(index)
        residues[i].name
        adtpdbindex = int(residues[i].name[3:])
        offset = adtpdbindex - i
        pocket.append(residues[int(i) - offset])
    #highlight pocket
    self.color(pocket, [[0.5176470588235295, 1.0, 1.0]], ['all'], log=0)

    #leave only the default geometry
    #self.displayMSMS("receptor:::;", negate=True)
    self.displayCPK("receptor,", log=0, negate=True)
    self.ribbon("receptor,", negate=True, log=0)
    return pocket

def pocketOnly():
    #regenerate geometries
    self.displayMSMS("receptor:::;", log=0)
    self.displayCPK("receptor,", log=0)
    self.ribbon("receptor,", log=0)

    self.select(pocket)
    self.invertSelection('molecule', redraw=0, log=1)
    self.displayMSMS(self.selection, negate=True, log=0)
    self.displayCPK(self.selection, negate=True, log=0)
    self.ribbon(self.selection, negate=True, log=0)
    self.select(self.selection, negate=True)

def setBox():
    with open('./box.txt') as f:
        lines = f.read().splitlines()
        gc, size = parseBox(lines) #gc refers to gridCenter
        self.ADgpf_setGpo(gridcenterAuto=0, gridcenter=gc, spacing=1.0, log=0, npts=size)

def setCoarseBox():
    with open('./coarse_box.txt') as f:
        lines = f.read().splitlines()
        gc, size = parseBox(lines) 
        self.ADgpf_setGpo(gridcenterAuto=0, gridcenter=gc, spacing=1.0, log=0, npts=size)

def parseBox(lines):
    gridcenter, size = [], []
    for i in range(0,3): #lines for gc = 0,2,4; lines for size = 1,3,5
        gridcenter.append(float(getNrInLine(lines[i*2])))
        size.append(float(getNrInLine(lines[i*2 + 1])))
    return gridcenter, size

def getNrInLine(line):
    return line.split()[2]

pocket = loadPocket()
