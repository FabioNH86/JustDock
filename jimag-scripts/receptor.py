import chimera
import os

from chimera import runCommand

inputfile = os.environ.get("IF")
outputfile = os.environ.get("OF")
chains = os.environ.get("CHAINS")

# MODULE

def prot_only(receptor):
    for r in receptor.residues:
        if r.isHet:
            receptor.deleteResidue(r)


def chain_only(receptor, chain_names):
    # chains = receptor.sequences(asDict=True)
    chains = set([n.chain for n in receptor.sequences()])
    for chain in chains:
        if chain not in chain_names:
            for r in receptor.sequence(chain).residues:
                if r is not None:
                    receptor.deleteResidue(r)


# MAIN

model = chimera.openModels.open(inputfile)
receptor = model[0]

if chains:
    chain_names = chains.split(",")
else:
    # chain_names = receptor.sequences(asDict=True)  # use all chains
    chain_names = set([n.chain for n in receptor.sequences()])

chain_only(receptor, chain_names)
prot_only(receptor)
write_output = "write format pdb 0 %s" % outputfile
runCommand(write_output)
