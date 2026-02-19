# -*- coding: utf-8 -*-
from django import forms
from .models import Protein, Ligand


class ProteinForm(forms.ModelForm):
    class Meta:
        model = Protein
        fields = ('protein_name', 'protein_file')


class LigandForm(forms.ModelForm):
    class Meta:
        model = Ligand
        fields = ('ligand_name', 'ligand_file')


class DockingForm(forms.Form):
    pform = ProteinForm()
    lform = LigandForm()
