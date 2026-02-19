//import React, { useState } from 'react';
//import ReactDOM from 'react-dom';
import * as React from 'react';
import * as ReactDOM from 'react-dom';

import { DefaultPluginUISpec, PluginUISpec } from 'molstar/lib/mol-plugin-ui/spec';
import { createPluginUI } from 'molstar/lib/mol-plugin-ui/index';
import { PluginConfig } from 'molstar/lib/mol-plugin/config';
import { InteractivityManager } from 'molstar/lib/mol-plugin-state/manager/interactivity';
import { MolScriptBuilder as MS } from 'molstar/lib/mol-script/language/builder';
import { Expression } from 'molstar/lib/mol-script/language/expression';
import { PluginStateObject as SO } from 'molstar/lib/mol-plugin-state/objects';
import { StateObjectRef } from 'molstar/lib/mol-state';

import {
    Structure,
    StructureProperties,
} from "molstar/lib/mol-model/structure";
import { Representation } from 'molstar/lib/mol-repr/representation';
import { PluginUIContext } from 'molstar/lib/mol-plugin-ui/context';
import { Color } from 'molstar/lib/mol-util/color';
import { StateObjectSelector } from 'molstar/lib/mol-state/object';
//import { ShapeRepresentation3D } from 'molstar/lib/mol-plugin-state/transforms/representation';
//import { StructureQueryHelper } from 'molstar/lib/mol-plugin-state/helpers/structure-query';
import { createStructureRepresentationParams } from 'molstar/lib/mol-plugin-state/helpers/structure-representation-params';

type Pocket = {
    rank: number;
    seq: {
	chain: string;
	subSeq: number[];
    }[];
};

const MySpec: PluginUISpec = {
    //ref: https://github.com/molstar/molstar/blob/master/src/apps/docking-viewer/index.ts#L80
    ...DefaultPluginUISpec(),
    config: [
        [PluginConfig.VolumeStreaming.Enabled, false],
        [PluginConfig.Viewport.ShowControls, false],
        [PluginConfig.Viewport.ShowSelectionMode, false],
        [PluginConfig.Viewport.ShowExpand, true],
        [PluginConfig.Viewport.ShowSettings, false],
        [PluginConfig.Viewport.ShowTrajectoryControls, false]
    ],
    layout: {
	initial: { //more in viewer/app.ts
	    isExpanded: false,
	    regionState: {
		top: "hidden",
		left: "hidden",
		right: "hidden",
		bottom: "hidden",
	    },
	},
    },
}

let loadReceptor;
    
(function() {
    //let plugin = null; 
    let plugin: PluginUIContext; 

    const MyComponent: React.FC = () => {
	const [selected, setSelected] = React.useState([]);

	React.useEffect(() => {
	    async function initializePlugin() {
		const parent = document.getElementById('chainsviewer')
		if (!parent) return;

		plugin = await createPluginUI(parent, MySpec);

		//const receptor = 'https://files.rcsb.org/download/1a3n.pdb';
		//const data = await plugin.builders.data.download({ url: receptor }, { state: { isGhost: true } });
		//const trajectory = await plugin.builders.structure.parseTrajectory(data, 'pdb');
		//await plugin.builders.structure.hierarchy.applyPreset(trajectory, 'default');

		plugin.managers.interactivity.setProps({granularity: 'chain'});
		plugin.selectionMode=true;
		plugin.behaviors.interaction.click.subscribe(
		    (event: InteractivityManager.ClickEvent) => {
			const selections = Array.from(
			    plugin.managers.structure.selection.entries.values()
			);
			//console.log("selections: ", selections);
			// This bit can be customized to record any piece information you want
			const localSelected: any[] = [];
			for (const { structure } of selections) {
			    //console.log("structure: ", structure);
			    if (!structure) continue;
			    Structure.eachAtomicHierarchyElement(structure, {
				chain: (loc) => {
				    const chainid = StructureProperties.chain.auth_asym_id(loc);
				    localSelected.push({ chainid });
				},
			    });
			}
			setSelected(localSelected);
			const chainString = localSelected.map(item => item.chainid).join(',');
			console.log("chainString: ", chainString);
			const stringDiv = document.getElementById('chainstring');
			stringDiv.innerHTML = chainString;
		    }
		);
	    }

	    initializePlugin();
	    return () => {
		//TODO: cleanup
	    };
	}, []);

	return null;
    }

    let currentStructure: StateObjectRef<SO.Molecule.Structure>;

    //https://stackoverflow.com/questions/50176213/accessing-exported-functions-from-html-file
    window.loadReceptor = async (receptor) => {
	if (!plugin) {
	    const parent = document.getElementById('chainsviewer');
	    if (!parent) return;
	    plugin = await createPluginUI(parent, MySpec);
	     
	} else {
	    const stringDiv = document.getElementById('chainstring');
	    stringDiv.innerHTML = '';
	    plugin.clear();
	    //console.log(receptor);
	    //de la definición de loadStructureFromData	(viewer/app.ts)
	    const rawdata = await plugin.builders.data.rawData({ data: receptor });
	    const trajectory = await plugin.builders.structure.parseTrajectory(rawdata, 'pdbqt');
	    await plugin.builders.structure.hierarchy.applyPreset(trajectory, 'default');
	    const model = await plugin.builders.structure.createModel(trajectory);
	    currentStructure = await plugin.builders.structure.createStructure(model);
	}
    }

    function createSequenceIdExpression(
	chain: string,
	sequenceIds: number[],
    ): Expression {
	const query: any = {
	"residue-test": MS.core.set.has([
	    MS.set(...sequenceIds),
	    MS.ammp("auth_seq_id"),
	]),
	    "group-by": MS.struct.atomProperty.macromolecular.residueKey(), //what does this do?
	};
	query["chain-test"] = MS.core.rel.eq([
	    MS.struct.atomProperty.macromolecular.auth_asym_id(),
	    chain,
	]);

	return MS.struct.generator.atomGroups(query);
    }

    window.togglePocketRepr = async (pocket:Pocket, isChecked: boolean) => {
	if (isChecked) {
	    pocketReprOn(pocket);
	} else {
	    pocketReprOff(pocket);
	}
    }

    let loadedReprs = [];
    let components: {[key:string]: StateObjectSelector<SO.Molecule.Structure>}= {};

    const pocketReprOn = (pocket: Pocket) => {
	console.log(pocket.rank);
	console.log(loadedReprs);
	console.log(loadedReprs[pocket.rank]);
	if (loadedReprs[pocket.rank]) {
	    for (const repr of loadedReprs[pocket.rank]) {
		//repr.setState({ visible:true });	
		    plugin.build()
		    .to(repr)
		    .update(createStructureRepresentationParams(plugin, undefined, {
			type: 'molecular-surface',
			typeParams: { alpha: 0.5 },
			color: 'uniform',
			colorParams: { value: Color(0x86F1E9) }
		}))
		.commit();
	    }
	} else {
	    //loadedReprs[pocket.rank] = createPocketRepr(pocket);
	    createPocketRepr(pocket);
	    console.log(loadedReprs[pocket.rank]);
	}
    }

    const pocketReprOff = (pocket: Pocket) => {
	//console.log("pocket description: ", JSON.stringify(loadedReprs[pocket.rank], null, 2));
	//loadedReprs[pocket.rank].forEach(function(repr: Representation.Any) {
	//    console.log(repr);
	//    repr.setState({visible: false});
	//});
	console.log(pocket.rank);
	console.log(loadedReprs);
	console.log(loadedReprs[pocket.rank]);
	for (const repr of loadedReprs[pocket.rank]) {
	    plugin.build()
		.to(repr)
		.update(createStructureRepresentationParams(plugin, undefined, {
		    type: 'molecular-surface',
		    typeParams: { alpha: 0 },
		    color: 'uniform',
		    colorParams: { value: Color(0x86F1E9) }
	    }))
	    .commit();
	}
    }

    //return an array of representations, each corresponding to a subSeq of the pocket	
    async function createPocketRepr (pocket: Pocket) {
	//this is called assuming the Repr doesn't exist, so no need to check for existence
	loadedReprs[pocket.rank] = [];
	let copy = { ... loadedReprs[pocket.rank]}; //DEBUG
	//https://stackoverflow.com/questions/37576685/using-async-await-with-a-foreach-loop
	for (const item of pocket.seq) {
	    let chain = item.chain;
	    let subSeq = item.subSeq;
	    let key = `${pocket.rank}${chain}`; //components key
	    console.log("CURRENT CHAIN, SUBSEQ: ", chain, subSeq); //DEBUG
	    let query = createSequenceIdExpression(chain, subSeq);
	    components[key] = await plugin.builders.structure.tryCreateComponentFromExpression(currentStructure, query, 'pocket${pocket.rank}');
	    console.log("CURRENT STRUCTURE", currentStructure); //DEBUG
	    let compcopy = {... components}; //DEBUG
	    console.log("COMPONENTS", compcopy); //DEBUG
	    console.log(`COMPONENTS[${key}]:`, compcopy[key]); //DEBUG
	    copy = { ... loadedReprs[pocket.rank]}; //DEBUG
	    console.log(`loadedReprs[${pocket.rank}] BEFORE: `, copy); //DEBUG

	    const builder = plugin.builders.structure.representation;
	    const update = plugin.build();
	    let selector = await builder.addRepresentation(components[key], {
		type: 'molecular-surface',
		typeParams: { alpha: 0.5 },
		color: 'uniform',
		colorParams: { value: Color(0x86F1E9) }
	    });
	    await update.commit();

	    loadedReprs[pocket.rank].push(selector);
	    copy = { ... loadedReprs[pocket.rank]}; //DEBUG
	    console.log(`loadedReprs[${pocket.rank}] AFTER: `, copy); //DEBUG
	}
	//the following results in cyclic object value:
	//console.log("pocket description (createPocketRepr): ", JSON.stringify(loadedReprs[pocket.rank], null, 2));
    }

    ReactDOM.render(
	React.createElement(MyComponent),
	//<MyComponent />,
	document.getElementById('chainsviewer')
    );
})();
