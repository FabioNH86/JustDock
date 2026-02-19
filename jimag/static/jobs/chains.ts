//import React, { useState } from 'react';
//import ReactDOM from 'react-dom';
import { renderReact18 } from 'molstar/lib/mol-plugin-ui/react18';
import * as React from 'react';
import * as ReactDOM from 'react-dom';

import { DefaultPluginUISpec, PluginUISpec } from 'molstar/lib/mol-plugin-ui/spec';
import { createPluginUI } from 'molstar/lib/mol-plugin-ui/index';
import { ColorNames } from 'molstar/lib/mol-util/color/names';
import { PluginCommands } from 'molstar/lib/mol-plugin/commands';
import { PluginConfig } from 'molstar/lib/mol-plugin/config';
import { InteractivityManager } from 'molstar/lib/mol-plugin-state/manager/interactivity';
import { MolScriptBuilder as MS } from 'molstar/lib/mol-script/language/builder';
import { Expression } from 'molstar/lib/mol-script/language/expression';
import { PluginStateObject as SO } from 'molstar/lib/mol-plugin-state/objects';
import { StateObjectRef } from 'molstar/lib/mol-state';
import { setSubtreeVisibility } from 'molstar/lib/mol-plugin/behavior/static/state';

import {
    Structure,
    StructureProperties,
} from "molstar/lib/mol-model/structure";
import { PluginUIContext } from 'molstar/lib/mol-plugin-ui/context';
import { Color } from 'molstar/lib/mol-util/color';

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

//let plugin = null; 
let plugin: PluginUIContext; 

const MyComponent: React.FC = () => {
    const [selected, setSelected] = React.useState([]);

    React.useEffect(() => {
	async function createPlugin() {
	    const parent = document.getElementById('chainsviewer')
	    if (!parent) return;

	    plugin = await createPluginUI({
		target: parent, 
		spec: MySpec,
		render: renderReact18
	    });

	    const renderer = plugin.canvas3d!.props.renderer;
	    PluginCommands.Canvas3D.SetSettings(plugin, { settings: { renderer: { ...renderer, backgroundColor: ColorNames.white /* or: 0xff0000 as Color */ } } });

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
		    //console.log("chainString: ", chainString);
		    const stringDiv = document.getElementById('chainstring');
		    stringDiv.innerHTML = chainString;
		}
	    );
	}

	createPlugin();
	return () => {
	    //TODO: cleanup
	};
    }, []);

    return null;
}

let currentStructure: StateObjectRef<SO.Molecule.Structure>;
let loadedReprs = [];
let components = {};

window.deletePockets = async () => {
    //const updates = plugin.build();
    const updates = plugin.state.data.build();
    //console.log(components);
    for (const key in components) {
	const component = components[key];
	updates.delete(component.ref);
    }
    await updates.commit();

    //clean pocket variables
    loadedReprs = [];
    components = {};
}

//https://stackoverflow.com/questions/50176213/accessing-exported-functions-from-html-file
window.loadReceptor = async (receptor) => {
    loadedReprs = [];
    components = {};
    window.clearChainString();
    window.clearPocketsTable();
    plugin.clear();
    //console.log(receptor);
    //de la definición de loadStructureFromData	(viewer/app.ts)
    const rawdata = await plugin.builders.data.rawData({ data: receptor });
    const trajectory = await plugin.builders.structure.parseTrajectory(rawdata, 'pdbqt');
    await plugin.builders.structure.hierarchy.applyPreset(trajectory, 'default');
    const model = await plugin.builders.structure.createModel(trajectory);
    currentStructure = await plugin.builders.structure.createStructure(model);
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
    if (loadedReprs[pocket.rank]) {
	for (const item of pocket.seq) {
	    let key = `${pocket.rank}${item.chain}`;
	    setSubtreeVisibility(plugin.state.data, components[key].ref, !isChecked); // true means hide, ¯\_(ツ)_/¯
	}
    } else {
	createPocketRepr(pocket);
    }
}

//return an array of representations, each corresponding to a subSeq of the pocket	
async function createPocketRepr (pocket: Pocket) {
    //this is called assuming the Repr doesn't exist, so no need to check for existence
    loadedReprs[pocket.rank] = [];
    for (const item of pocket.seq) {
	let chain = item.chain;
	let subSeq = item.subSeq;
	let key = `${pocket.rank}${chain}`; //components key, like 1A, 1B
	let query = createSequenceIdExpression(chain, subSeq);
	//console.log(`DEBUG: query `, JSON.stringify(query));
	let err;
	components[key] = await plugin.builders.structure.tryCreateComponentFromExpression(currentStructure, query, `pocket${key}`).catch((err) => {
	    console.log("E: ", err);	
	});
	//console.log(`DEBUG: components[${key}]: `, components[key]);

	let selector = await plugin.builders.structure.representation.addRepresentation(components[key], {
	    type: 'molecular-surface',
	    typeParams: { alpha: 0.5 },
	    color: 'uniform',
	    colorParams: { value: Color(0x86F1E9) }
	});

	loadedReprs[pocket.rank].push(selector);
    }
}

//BEGIN debug functions
async function pause(ms) {
    return new Promise(resolve => {
    setTimeout(resolve, ms);
    });
}

async function pauseTilEnter(comment: string) {
    console.log("pause: ", comment);
    return new Promise(resolve => {
	const handleKeyPress = event => {
	    if (event.key === 'Enter') {
		window.removeEventListener('keydown', handleKeyPress);
		resolve();
	    } 
	};
	window.addEventListener('keydown', handleKeyPress);
    });
}
//END debug functions

/*
ReactDOM.render(
    React.createElement(MyComponent),
    //<MyComponent />,
    document.getElementById('chainsviewer')
);
*/

renderReact18(React.createElement(MyComponent),document.getElementById('chainsviewer'));
