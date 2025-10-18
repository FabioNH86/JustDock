//import React, { useState } from 'react';
//import ReactDOM from 'react-dom';
import * as React from 'react';
import * as ReactDOM from 'react-dom';

import { DefaultPluginUISpec, PluginUISpec } from 'molstar/lib/mol-plugin-ui/spec';
import { createPluginUI } from 'molstar/lib/mol-plugin-ui/index';
import { PluginConfig } from 'molstar/lib/mol-plugin/config';
import { InteractivityManager } from 'molstar/lib/mol-plugin-state/manager/interactivity';

import {
  Structure,
  StructureProperties,
} from "molstar/lib/mol-model/structure"

const MySpec: PluginUISpec = {
    //ref: https://github.com/molstar/molstar/blob/master/src/apps/docking-viewer/index.ts#L80
    ...DefaultPluginUISpec(),
    config: [
        [PluginConfig.VolumeStreaming.Enabled, false],
        [PluginConfig.Viewport.ShowControls, false],
        [PluginConfig.Viewport.ShowSelectionMode, false],
        [PluginConfig.Viewport.ShowExpand, false],
        [PluginConfig.Viewport.ShowSettings, false],
        [PluginConfig.Viewport.ShowTrajectoryControls, false]
    ],
    layout: {
	initial: {
	    regionState: {
	      bottom: "hidden",
	      top: "hidden",
	      left: "hidden",
	      right: "hidden",
	    },
	},
    },
}

const MyComponent = () => {
  const [selected, setSelected] = React.useState<{ chainid: string }[]>([]);

  React.useEffect(() => {
    async function initializePlugin() {
      const parent = document.getElementById('app2')
      if (!parent) return;

      const plugin = await createPluginUI({
        target: parent,
        render: (component: any, container: Element) => ReactDOM.render(component, container),
        spec: MySpec
      });

      const data = await plugin.builders.data.download({ url: 'https://files.rcsb.org/download/1a3n.pdb' }, { state: { isGhost: true } });
      const trajectory = await plugin.builders.structure.parseTrajectory(data, 'pdb');
      await plugin.builders.structure.hierarchy.applyPreset(trajectory, 'default');

      plugin.managers.interactivity.setProps({granularity: 'chain'});
      plugin.selectionMode=true;

      plugin.behaviors.interaction.click.subscribe(
	(event: InteractivityManager.ClickEvent) => {
	  const selections = Array.from(
	    plugin.managers.structure.selection.entries.values()
	  );
	  //console.log("selections: ", selections);
    // This bit can be customized to record any piece information you want
    const localSelected: { chainid: string }[] = [];
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
    console.log(chainString);
    const stringDiv = document.getElementById('chainstring');
    if (stringDiv instanceof HTMLElement) {
      stringDiv.textContent = chainString;
    }
  }
      );
    }

    initializePlugin();
    return () => {
      //cleanup
    };
  }, []);

  return null;
}

ReactDOM.render(
  React.createElement(MyComponent),
  document.getElementById('chainsviewer')
);